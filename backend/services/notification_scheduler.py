import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from database import get_db
from models import User, SavedLocation, WeatherData
from services.weather_service import WeatherService
from services.email_service import EmailService
from services.multi_agent_ai_service import multi_agent_service
import logging

# Use WARNING level to reduce noise, only show important issues
logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WeatherNotificationScheduler:
    def __init__(self):
        self.weather_service = WeatherService()
        self.email_service = EmailService()
        # Use global multi-agent service
        self.is_running = False
        # Predefined ocean/coastal locations for hourly hazard scanning (name, lat, lon)
        self.monitor_locations = [
            ("North Atlantic (Azores)", 38.7223, -28.2449),
            ("Bay of Biscay", 45.0000, -5.0000),
            ("English Channel", 50.0000, -2.0000),
            ("Arabian Sea", 18.0000, 66.0000),
            ("Bay of Bengal", 15.0000, 88.0000),
            ("South China Sea", 14.0000, 114.0000),
            ("Gulf of Mexico", 25.0000, -90.0000),
            ("Coral Sea", -18.0000, 152.0000),
        ]
        # In-memory rate limiter: { (name): last_sent_datetime }
        self.last_hazard_email_sent = {}
        
    async def start_scheduler(self):
        """Start the daily weather notification scheduler"""
        self.is_running = True
        print("Background scheduler started - checking alerts every 10 minutes")
        
        while self.is_running:
            try:
                # Check if it's time to send daily notifications (e.g., 6 AM)
                current_time = datetime.now()
                if current_time.hour == 6 and current_time.minute < 5:  # Send between 6:00-6:05 AM
                    await self.send_daily_notifications()
                    # Wait for the next day
                    await asyncio.sleep(3600)  # Wait 1 hour to avoid multiple sends
                # Hourly hazard scan on the hour
                elif current_time.minute == 0:
                    await self.run_hourly_hazard_scan()
                    await asyncio.sleep(120)  # Cooldown 2 minutes to avoid duplicate firing
                else:
                    # Check every 5 minutes
                    await asyncio.sleep(300)
                    
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    async def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        logger.info("Weather notification scheduler stopped")
    
    async def send_daily_notifications(self):
        """Send daily weather notifications to all users with saved locations"""
        logger.info("Starting daily weather notifications")
        
        try:
            # Get database session
            db = next(get_db())
            
            # Get all users with saved locations
            users_with_locations = db.query(User).join(SavedLocation).filter(
                User.is_active == True
            ).distinct().all()
            
            notifications_sent = 0
            
            for user in users_with_locations:
                try:
                    # Get user's saved locations
                    saved_locations = db.query(SavedLocation).filter(
                        SavedLocation.user_id == user.id
                    ).all()
                    
                    if not saved_locations:
                        continue
                    
                    # Prepare notifications for this user
                    user_notifications = []
                    
                    for location in saved_locations:
                        try:
                            # Get current weather data
                            weather_data = await self.weather_service.get_current_weather(
                                location.latitude, location.longitude
                            )
                            
                            # Get 7-day forecast
                            forecast_data = await self.weather_service.get_forecast(
                                location.latitude, location.longitude, 7
                            )
                            
                            # Generate AI weather summary using multi-agent system
                            weather_summary = await multi_agent_service.analyze_weather_conditions({
                                "current_weather": weather_data,
                                "forecast": forecast_data.get('forecast', []),
                                "location": {"latitude": location.latitude, "longitude": location.longitude}
                            })
                            
                            # Add AI summary to weather data
                            weather_data['ai_summary'] = weather_summary
                            
                            user_notifications.append({
                                'email': user.email,
                                'location_name': location.name,
                                'weather_data': weather_data,
                                'forecast_data': forecast_data.get('forecast', [])
                            })
                            
                        except Exception as e:
                            logger.error(f"Error getting weather for location {location.name}: {e}")
                            continue
                    
                    # Send notifications for this user
                    if user_notifications:
                        results = await self.email_service.send_bulk_weather_notifications(user_notifications)
                        notifications_sent += len([r for r in results.values() if r])
                        
                        # Log results
                        for notification in user_notifications:
                            email = notification['email']
                            success = results.get(email, False)
                            logger.info(f"Notification sent to {email} for {notification['location_name']}: {success}")
                
                except Exception as e:
                    logger.error(f"Error processing user {user.email}: {e}")
                    continue
            
            logger.info(f"Daily weather notifications completed. Sent: {notifications_sent}")
            
        except Exception as e:
            logger.error(f"Error in send_daily_notifications: {e}")
        finally:
            if 'db' in locals():
                db.close()

    async def run_hourly_hazard_scan(self):
        """Multi-agent hourly scan across predefined and user-saved locations using free data sources.
        Pipeline: Collector (weather + IR) -> Analyzer (AI hazard analysis) -> Notifier (email).
        Sends to active users when max hazard probability > 0.7.
        Rate limit: one email per location per 2 hours.
        """
        logger.info("Starting hourly hazard scan")
        try:
            db = next(get_db())
            active_users = db.query(User).filter(User.is_active == True).all()
            if not active_users:
                logger.info("No active users to notify")
                return

            notifications = []

            # Scan user-saved locations (notify only the owner)
            user_saved_locations = db.query(SavedLocation).join(User, SavedLocation.user_id == User.id).filter(User.is_active == True).all()
            for loc in user_saved_locations:
                try:
                    name = loc.name
                    lat = loc.latitude
                    lon = loc.longitude

                    last_sent = self.last_hazard_email_sent.get(name)
                    if last_sent and (datetime.now() - last_sent).total_seconds() < 7200:
                        continue

                    current_weather = await self.weather_service.get_current_weather(lat, lon)
                    forecast_data = await self.weather_service.get_forecast(lat, lon, 3)

                    probs = current_weather.get('hazard_probabilities') or {}
                    max_prob = max(probs.values()) if probs else 0.0
                    if max_prob < 0.7:
                        continue

                    ir_content = await self.weather_service.fetch_ir_content(lat, lon)
                    analysis = await multi_agent_service.analyze_hazards({
                        "current_weather": current_weather,
                        "forecast": forecast_data,
                        "ir_content": ir_content,
                        "location": {"latitude": lat, "longitude": lon}
                    })
                    current_weather['ai_hazard_analysis'] = analysis

                    owner = db.query(User).filter(User.id == loc.user_id, User.is_active == True).first()
                    if owner:
                        notifications.append({
                            'email': owner.email,
                            'location_name': name,
                            'weather_data': current_weather,
                            'forecast_data': forecast_data.get('forecast', [])
                        })
                        self.last_hazard_email_sent[name] = datetime.now()
                except Exception as e:
                    logger.error(f"Hourly scan user location error {loc.id}:{loc.name}: {e}")
                    continue

            # Scan global monitor locations (notify all active users)
            for name, lat, lon in self.monitor_locations:
                try:
                    # Rate limit per location
                    last_sent = self.last_hazard_email_sent.get(name)
                    if last_sent and (datetime.now() - last_sent).total_seconds() < 7200:
                        continue

                    # Collector: fetch current weather and forecast
                    current_weather = await self.weather_service.get_current_weather(lat, lon)
                    forecast_data = await self.weather_service.get_forecast(lat, lon, 3)

                    # Determine hazard level from probabilities
                    probs = current_weather.get('hazard_probabilities') or {}
                    max_prob = max(probs.values()) if probs else 0.0
                    if max_prob < 0.7:
                        continue

                    # Analyzer: AI JSON analysis using multi-agent system
                    ir_content = await self.weather_service.fetch_ir_content(lat, lon)
                    analysis = await multi_agent_service.analyze_hazards({
                        "current_weather": current_weather,
                        "forecast": forecast_data,
                        "ir_content": ir_content,
                        "location": {"latitude": lat, "longitude": lon}
                    })
                    current_weather['ai_hazard_analysis'] = analysis

                    # Build notifications for all active users
                    for user in active_users:
                        notifications.append({
                            'email': user.email,
                            'location_name': name,
                            'weather_data': current_weather,
                            'forecast_data': forecast_data.get('forecast', [])
                        })

                    # Mark rate limit for this location
                    self.last_hazard_email_sent[name] = datetime.now()
                except Exception as e:
                    logger.error(f"Hourly scan error at {name}: {e}")
                    continue

            if notifications:
                results = await self.email_service.send_bulk_weather_notifications(notifications)
                sent_count = len([r for r in results.values() if r])
                logger.info(f"Hourly hazard emails sent: {sent_count}")
            else:
                logger.info("No high hazards detected this hour")

        except Exception as e:
            logger.error(f"Error in hourly hazard scan: {e}")
        finally:
            if 'db' in locals():
                db.close()
    
    async def send_immediate_notification(
        self, 
        user_email: str, 
        location_id: int, 
        alert_type: str = "weather_update"
    ):
        """Send immediate weather notification for a specific location"""
        try:
            db = next(get_db())
            
            # Get location details
            location = db.query(SavedLocation).filter(SavedLocation.id == location_id).first()
            if not location:
                logger.error(f"Location {location_id} not found")
                return False
            
            # Get current weather
            weather_data = await self.weather_service.get_current_weather(
                location.latitude, location.longitude
            )
            
            # Send notification
            success = await self.email_service.send_weather_notification(
                to_email=user_email,
                location_name=location.name,
                weather_data=weather_data
            )
            
            logger.info(f"Immediate notification sent to {user_email} for {location.name}: {success}")
            return success
            
        except Exception as e:
            logger.error(f"Error sending immediate notification: {e}")
            return False
        finally:
            if 'db' in locals():
                db.close()
    
    async def test_notification(self, email: str, location_name: str = "Test Location"):
        """Send a test notification"""
        test_weather_data = {
            'temperature': 22.5,
            'wind_speed': 15.3,
            'wave_height': 1.2,
            'visibility': 8500,
            'weather_condition': 'Clear',
            'hazard_probabilities': {
                'storm': 0.1,
                'fog': 0.0,
                'tsunami': 0.0,
                'high_wind': 0.2,
                'rough_sea': 0.1
            }
        }
        
        success = await self.email_service.send_weather_notification(
            to_email=email,
            location_name=location_name,
            weather_data=test_weather_data
        )
        
        logger.info(f"Test notification sent to {email}: {success}")
        return success

# Global scheduler instance
scheduler = WeatherNotificationScheduler()


