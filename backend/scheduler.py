from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from database import SessionLocal
from models import AlertPreference, SavedLocation, AlertHistory, User
from services.alert_service import AlertService
from datetime import datetime, timedelta
import asyncio

alert_service = AlertService()

async def check_and_send_alerts():
    """Background task to check for alerts and send emails every 10 minutes"""
    db = SessionLocal()
    try:
        # Get all active alert preferences
        alert_preferences = db.query(AlertPreference).filter(
            AlertPreference.is_active == True
        ).all()
        
        for preference in alert_preferences:
            try:
                # Get the location
                location = db.query(SavedLocation).filter(
                    SavedLocation.id == preference.location_id
                ).first()
                
                if not location:
                    continue
                
                # Get the user
                user = db.query(User).filter(User.id == preference.user_id).first()
                
                if not user:
                    continue
                
                # Check for alerts
                triggered_alerts = await alert_service.check_alerts_for_location(
                    location, preference, db
                )
                
                # Send alerts and log them
                for alert_data in triggered_alerts:
                    # Check if we already sent this alert recently (within last hour)
                    recent_alert = db.query(AlertHistory).filter(
                        AlertHistory.user_id == user.id,
                        AlertHistory.location_id == location.id,
                        AlertHistory.alert_type == alert_data["alert_type"],
                        AlertHistory.sent_at >= datetime.utcnow() - timedelta(hours=1)
                    ).first()
                    
                    if recent_alert:
                        continue  # Skip if already sent recently
                    
                    # Send email alert
                    email_sent = await alert_service.send_alert_email(
                        user.email, location.name, alert_data
                    )
                    
                    # Log the alert
                    alert_history = AlertHistory(
                        user_id=user.id,
                        location_id=location.id,
                        alert_type=alert_data["alert_type"],
                        severity=alert_data["severity"],
                        message=alert_data["message"],
                        weather_data=alert_data["weather_data"]
                    )
                    db.add(alert_history)
                    
                    print(f"Alert sent to {user.email} for {location.name}: {alert_data['alert_type']}")
                
                db.commit()
                
            except Exception as e:
                print(f"Error processing alerts for preference {preference.id}: {e}")
                db.rollback()
                continue
        
    except Exception as e:
        print(f"Error in alert checking task: {e}")
        db.rollback()
    finally:
        db.close()

def start_scheduler():
    """Start the background scheduler"""
    scheduler = AsyncIOScheduler()
    
    # Schedule alert checking every 10 minutes
    scheduler.add_job(
        check_and_send_alerts,
        trigger=IntervalTrigger(minutes=10),
        id='alert_checker',
        name='Check and send marine weather alerts',
        replace_existing=True
    )
    
    scheduler.start()
    print("Background scheduler started - checking alerts every 10 minutes")
    
    return scheduler
