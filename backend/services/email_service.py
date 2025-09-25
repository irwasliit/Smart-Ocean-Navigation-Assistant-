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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Marine Weather Report</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #e0f2fe 0%, #b3e5fc 100%);
            min-height: 100vh;
        }
        .container { 
            max-width: 650px; 
            margin: 0 auto; 
            background-color: white; 
            border-radius: 16px; 
            overflow: hidden; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            border: 1px solid #e2e8f0;
        }
        .header { 
            background: linear-gradient(135deg, #0ea5e9, #0284c7); 
            color: white; 
            padding: 40px 30px; 
            text-align: center;
            position: relative;
        }
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="waves" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse"><path d="M0 50c25-25 75 25 100 0v50H0z" fill="rgba(255,255,255,0.1)"/></pattern></defs><rect width="100" height="100" fill="url(%23waves)"/></svg>');
            opacity: 0.3;
        }
        .header-content {
            position: relative;
            z-index: 1;
        }
        .header h1 { 
            margin: 0; 
            font-size: 28px; 
            font-weight: 700;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        .header .location { 
            margin: 10px 0 0 0; 
            opacity: 0.95; 
            font-size: 18px;
            font-weight: 500;
        }
        .header .date { 
            margin: 5px 0 0 0; 
            opacity: 0.85; 
            font-size: 14px;
        }
        .content { padding: 35px 30px; }
        .weather-card { 
            background: linear-gradient(135deg, #f8fafc, #e2e8f0);
            border-radius: 16px; 
            padding: 30px; 
            margin-bottom: 30px;
            border: 1px solid #e2e8f0;
        }
        .weather-card h2 {
            margin-top: 0; 
            color: #0ea5e9;
            display: flex;
            align-items: center;
            font-size: 22px;
        }
        .weather-card h2::before {
            content: '🌊';
            margin-right: 10px;
            font-size: 24px;
        }
        .weather-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); 
            gap: 20px; 
            margin-bottom: 25px; 
        }
        .weather-item { 
            text-align: center; 
            padding: 20px 15px; 
            background-color: white; 
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .weather-item:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        .weather-icon {
            font-size: 24px;
            margin-bottom: 10px;
        }
        .weather-value { 
            font-size: 24px; 
            font-weight: 700; 
            color: #0ea5e9; 
            margin-bottom: 8px; 
        }
        .weather-label { 
            font-size: 12px; 
            color: #64748b; 
            text-transform: uppercase; 
            letter-spacing: 0.5px;
            font-weight: 600;
        }
        .hazard-section { 
            margin-top: 25px;
            background: white;
            border-radius: 12px;
            padding: 25px;
            border-left: 4px solid #0ea5e9;
        }
        .hazard-section h3 {
            color: #0ea5e9;
            margin-top: 0;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
        }
        .hazard-section h3::before {
            content: '⚠️';
            margin-right: 10px;
            font-size: 20px;
        }
        .hazard-item { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            padding: 12px 0; 
            border-bottom: 1px solid #f1f5f9;
        }
        .hazard-item:last-child {
            border-bottom: none;
        }
        .hazard-name { 
            font-weight: 600; 
            text-transform: capitalize;
            color: #374151;
        }
        .hazard-probability { 
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
        }
        .hazard-low { 
            color: #065f46; 
            background: #d1fae5;
        }
        .hazard-medium { 
            color: #92400e; 
            background: #fef3e2;
        }
        .hazard-high { 
            color: #991b1b; 
            background: #fef2f2;
        }
        .forecast-section { 
            margin-top: 35px;
            background: white;
            border-radius: 12px;
            padding: 25px;
            border-left: 4px solid #10b981;
        }
        .forecast-section h2 {
            color: #059669;
            margin-top: 0;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
        }
        .forecast-section h2::before {
            content: '📅';
            margin-right: 10px;
            font-size: 20px;
        }
        .forecast-item { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            padding: 15px 0; 
            border-bottom: 1px solid #f1f5f9;
        }
        .forecast-item:last-child {
            border-bottom: none;
        }
        .forecast-date { 
            font-weight: 600;
            color: #374151;
        }
        .forecast-temp { 
            font-weight: 700; 
            color: #059669;
            background: #ecfdf5;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 14px;
        }
        .footer { 
            background: linear-gradient(135deg, #0ea5e9, #0284c7);
            padding: 30px; 
            text-align: center; 
            color: white;
        }
        .footer p {
            margin: 5px 0;
            opacity: 0.9;
        }
        .footer .app-name {
            font-weight: 700;
            font-size: 16px;
        }
        .safety-tip {
            background: linear-gradient(135deg, #fef3e2, #fed7aa);
            border-radius: 12px;
            padding: 25px;
            margin-top: 25px;
            border-left: 4px solid #d97706;
        }
        .safety-tip h3 {
            color: #92400e;
            margin-top: 0;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }
        .safety-tip h3::before {
            content: '⚓';
            margin-right: 10px;
            font-size: 20px;
        }
        @media (max-width: 600px) {
            .container { margin: 10px; border-radius: 12px; }
            .header { padding: 30px 20px; }
            .content { padding: 25px 20px; }
            .weather-grid { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <h1>🌊 Daily Marine Weather Report</h1>
                <div class="location">📍 {{ location_name }}</div>
                <div class="date">📅 {{ current_date }}</div>
            </div>
        </div>
        
        <div class="content">
            <div class="weather-card">
                <h2>Current Marine Conditions</h2>
                <div class="weather-grid">
                    <div class="weather-item">
                        <div class="weather-icon">🌡️</div>
                        <div class="weather-value">{{ "%.1f"|format(weather_data.temperature) }}°C</div>
                        <div class="weather-label">Temperature</div>
                    </div>
                    <div class="weather-item">
                        <div class="weather-icon">💨</div>
                        <div class="weather-value">{{ "%.1f"|format(weather_data.wind_speed) }} km/h</div>
                        <div class="weather-label">Wind Speed</div>
                    </div>
                    <div class="weather-item">
                        <div class="weather-icon">🌊</div>
                        <div class="weather-value">{{ "%.1f"|format(weather_data.wave_height) }} m</div>
                        <div class="weather-label">Wave Height</div>
                    </div>
                    <div class="weather-item">
                        <div class="weather-icon">👁️</div>
                        <div class="weather-value">{{ "%.1f"|format(weather_data.visibility / 1000) }} km</div>
                        <div class="weather-label">Visibility</div>
                    </div>
                </div>
                
                <div class="hazard-section">
                    <h3>Maritime Risk Assessment</h3>
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
                <h2>7-Day Marine Forecast</h2>
                {% for day in forecast_data[:7] %}
                <div class="forecast-item">
                    <span class="forecast-date">{{ day.timestamp.strftime('%A, %B %d') }}</span>
                    <span class="forecast-temp">{{ "%.1f"|format(day.temperature) }}°C</span>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <div class="safety-tip">
                <h3>Daily Maritime Safety Reminder</h3>
                <p style="margin: 0; color: #92400e; line-height: 1.6;">
                    Always file a float plan, check marine weather forecasts, carry proper safety equipment, 
                    and inform someone of your planned route and return time. Monitor VHF radio channels 
                    for weather updates while on the water.
                </p>
            </div>
        </div>
        
        <div class="footer">
            <p class="app-name">🌊 Smart Ocean Navigation Assistant</p>
            <p>Advanced Marine Weather & AI Hazard Detection System</p>
            <p style="font-size: 12px; opacity: 0.8;">
                This is an automated daily weather report. Stay safe on the water! ⚓
            </p>
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


