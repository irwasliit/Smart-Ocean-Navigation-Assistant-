import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from jinja2 import Template
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        
    async def send_weather_notification(
        self, 
        to_email: str, 
        location_name: str, 
        weather_data: Dict,
        forecast_data: List[Dict] = None
    ) -> bool:
        """Send daily weather notification email"""
        try:
            # Create email content
            subject = f"Daily Weather Report - {location_name}"
            html_content = self._generate_weather_email_html(
                location_name, weather_data, forecast_data
            )
            text_content = self._generate_weather_email_text(
                location_name, weather_data, forecast_data
            )
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def _generate_weather_email_html(
        self, 
        location_name: str, 
        weather_data: Dict, 
        forecast_data: List[Dict] = None
    ) -> str:
        """Generate HTML email content"""
        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Daily Weather Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #1e40af, #3b82f6); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 24px; }
        .header p { margin: 5px 0 0 0; opacity: 0.9; }
        .content { padding: 30px; }
        .weather-card { background-color: #f8fafc; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        .weather-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .weather-item { text-align: center; padding: 15px; background-color: white; border-radius: 6px; }
        .weather-value { font-size: 24px; font-weight: bold; color: #1e40af; margin-bottom: 5px; }
        .weather-label { font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
        .hazard-section { margin-top: 20px; }
        .hazard-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #e2e8f0; }
        .hazard-name { font-weight: 500; text-transform: capitalize; }
        .hazard-probability { font-weight: bold; }
        .hazard-low { color: #10b981; }
        .hazard-medium { color: #f59e0b; }
        .hazard-high { color: #ef4444; }
        .forecast-section { margin-top: 30px; }
        .forecast-item { display: flex; justify-content: space-between; align-items: center; padding: 15px 0; border-bottom: 1px solid #e2e8f0; }
        .forecast-date { font-weight: 500; }
        .forecast-temp { font-weight: bold; color: #1e40af; }
        .footer { background-color: #f8fafc; padding: 20px; text-align: center; color: #64748b; font-size: 12px; }
        .footer a { color: #1e40af; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌊 Daily Weather Report</h1>
            <p>{{ location_name }}</p>
            <p>{{ current_date }}</p>
        </div>
        
        <div class="content">
            <div class="weather-card">
                <h2 style="margin-top: 0; color: #1e40af;">Current Conditions</h2>
                <div class="weather-grid">
                    <div class="weather-item">
                        <div class="weather-value">{{ "%.1f"|format(weather_data.temperature) }}°C</div>
                        <div class="weather-label">Temperature</div>
                    </div>
                    <div class="weather-item">
                        <div class="weather-value">{{ "%.1f"|format(weather_data.wind_speed) }} km/h</div>
                        <div class="weather-label">Wind Speed</div>
                    </div>
                    <div class="weather-item">
                        <div class="weather-value">{{ "%.1f"|format(weather_data.wave_height) }} m</div>
                        <div class="weather-label">Wave Height</div>
                    </div>
                    <div class="weather-item">
                        <div class="weather-value">{{ "%.1f"|format(weather_data.visibility / 1000) }} km</div>
                        <div class="weather-label">Visibility</div>
                    </div>
                </div>
                
                <div class="hazard-section">
                    <h3 style="color: #1e40af; margin-bottom: 15px;">Hazard Assessment</h3>
                    {% for hazard, probability in weather_data.hazard_probabilities.items() %}
                    <div class="hazard-item">
                        <span class="hazard-name">{{ hazard.replace('_', ' ') }}</span>
                        <span class="hazard-probability hazard-{% if probability < 0.3 %}low{% elif probability < 0.7 %}medium{% else %}high{% endif %}">
                            {{ "%.0f"|format(probability * 100) }}%
                        </span>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            {% if forecast_data %}
            <div class="forecast-section">
                <h2 style="color: #1e40af;">7-Day Forecast</h2>
                {% for day in forecast_data[:7] %}
                <div class="forecast-item">
                    <span class="forecast-date">{{ day.timestamp.strftime('%A, %B %d') }}</span>
                    <span class="forecast-temp">{{ "%.1f"|format(day.temperature) }}°C</span>
                </div>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            <p>This is an automated weather report from your Marine Weather App.</p>
            <p>Stay safe and check conditions before heading out!</p>
        </div>
    </div>
</body>
</html>
        """)
        
        return template.render(
            location_name=location_name,
            current_date=datetime.now().strftime("%B %d, %Y"),
            weather_data=weather_data,
            forecast_data=forecast_data or []
        )
    
    def _generate_weather_email_text(
        self, 
        location_name: str, 
        weather_data: Dict, 
        forecast_data: List[Dict] = None
    ) -> str:
        """Generate plain text email content"""
        text = f"""
DAILY WEATHER REPORT - {location_name}
{datetime.now().strftime("%B %d, %Y")}

CURRENT CONDITIONS:
==================
Temperature: {weather_data.get('temperature', 'N/A'):.1f}°C
Wind Speed: {weather_data.get('wind_speed', 'N/A'):.1f} km/h
Wave Height: {weather_data.get('wave_height', 'N/A'):.1f} m
Visibility: {weather_data.get('visibility', 0) / 1000:.1f} km
Weather Condition: {weather_data.get('weather_condition', 'N/A')}

HAZARD ASSESSMENT:
==================
"""
        
        if weather_data.get('hazard_probabilities'):
            for hazard, probability in weather_data['hazard_probabilities'].items():
                text += f"{hazard.replace('_', ' ').title()}: {probability * 100:.0f}%\n"
        
        if forecast_data:
            text += "\n7-DAY FORECAST:\n================\n"
            for day in forecast_data[:7]:
                text += f"{day['timestamp'].strftime('%A, %B %d')}: {day['temperature']:.1f}°C\n"
        
        text += """
===============================================
This is an automated weather report from your Marine Weather App.
Stay safe and check conditions before heading out!
"""
        
        return text
    
    async def send_bulk_weather_notifications(
        self, 
        notifications: List[Dict]
    ) -> Dict[str, bool]:
        """Send bulk weather notifications"""
        results = {}
        
        for notification in notifications:
            success = await self.send_weather_notification(
                to_email=notification['email'],
                location_name=notification['location_name'],
                weather_data=notification['weather_data'],
                forecast_data=notification.get('forecast_data')
            )
            results[notification['email']] = success
        
        return results


