import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
import os
from datetime import datetime
from dotenv import load_dotenv
from services.weather_service import WeatherService

load_dotenv()

class AlertService:
    def __init__(self):
        self.weather_service = WeatherService()
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("SMTP_USERNAME")
        self.email_password = os.getenv("SMTP_PASSWORD")
        
    async def check_alerts_for_location(self, location, alert_preference, db):
        """Check if alerts should be triggered for a location"""
        try:
            # Get current weather for the location
            weather_data = await self.weather_service.get_current_weather(
                location.latitude, location.longitude
            )
            
            triggered_alerts = []
            
            # Check each alert type
            for alert_type in alert_preference.alert_types:
                threshold = alert_preference.threshold_values.get(alert_type, 0)
                
                if self._should_trigger_alert(alert_type, weather_data, threshold):
                    alert_message = self._generate_alert_message(
                        alert_type, weather_data, location.name
                    )
                    
                    triggered_alerts.append({
                        "alert_type": alert_type,
                        "message": alert_message,
                        "severity": self._determine_severity(alert_type, weather_data),
                        "weather_data": weather_data
                    })
            
            return triggered_alerts
            
        except Exception as e:
            print(f"Error checking alerts for location {location.name}: {e}")
            return []
    
    async def send_alert_email(self, user_email: str, location_name: str, alert_data: Dict):
        """Send alert email to user"""
        try:
            if not self.email_user or not self.email_password:
                print("Email credentials not configured")
                return False
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = user_email
            msg['Subject'] = f"🌊 Marine Weather Alert - {location_name}"
            
            # Create both HTML and text versions
            html_body = self._generate_alert_email_html(location_name, alert_data)
            text_body = self._generate_alert_email_text(location_name, alert_data)
            
            # Create MIME parts
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Error sending alert email: {e}")
            return False
    
    async def test_alert(self, location, alert_preference, user_email=None):
        """Send a test alert for a location"""
        try:
            # Create test alert data
            test_alert = {
                "alert_type": "test",
                "message": f"Test alert for {location.name}. This is a system test to verify alert functionality.",
                "severity": "low",
                "weather_data": {
                    "wind_speed": 15.0,
                    "wave_height": 1.5,
                    "visibility": 10000,
                    "temperature": 22.0
                }
            }
            
            # Send test email if user email is provided
            if user_email and self.email_user and self.email_password:
                email_sent = await self.send_alert_email(user_email, location.name, test_alert)
                if email_sent:
                    return {"status": "success", "message": "Test alert sent via email"}
                else:
                    return {"status": "error", "message": "Failed to send test email"}
            else:
                return {"status": "success", "message": "Test alert prepared (email not configured)"}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _generate_alert_email_html(self, location_name: str, alert_data: Dict) -> str:
        """Generate professional HTML email content for alerts"""
        severity = alert_data.get('severity', 'low').lower()
        alert_type = alert_data.get('alert_type', 'unknown').replace('_', ' ').title()
        
        # Determine colors based on severity
        if severity in ['critical', 'high']:
            header_color = "#dc2626"  # Red
            accent_color = "#fef2f2"
            severity_color = "#dc2626"
            icon = "🚨"
        elif severity == 'medium':
            header_color = "#d97706"  # Orange
            accent_color = "#fef3e2"
            severity_color = "#d97706"
            icon = "⚠️"
        else:
            header_color = "#059669"  # Green
            accent_color = "#f0fdf4"
            severity_color = "#059669"
            icon = "ℹ️"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marine Weather Alert</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #e0f2fe 0%, #b3e5fc 100%);
            min-height: 100vh;
        }}
        .container {{ 
            max-width: 650px; 
            margin: 0 auto; 
            background-color: white; 
            border-radius: 16px; 
            overflow: hidden; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            border: 1px solid #e2e8f0;
        }}
        .header {{ 
            background: linear-gradient(135deg, {header_color}, {header_color}dd); 
            color: white; 
            padding: 40px 30px; 
            text-align: center;
            position: relative;
        }}
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="waves" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse"><path d="M0 50c25-25 75 25 100 0v50H0z" fill="rgba(255,255,255,0.1)"/></pattern></defs><rect width="100" height="100" fill="url(%23waves)"/></svg>');
            opacity: 0.3;
        }}
        .header-content {{
            position: relative;
            z-index: 1;
        }}
        .header h1 {{ 
            margin: 0; 
            font-size: 28px; 
            font-weight: 700;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        .header .location {{ 
            margin: 10px 0 0 0; 
            opacity: 0.95; 
            font-size: 18px;
            font-weight: 500;
        }}
        .header .timestamp {{ 
            margin: 5px 0 0 0; 
            opacity: 0.85; 
            font-size: 14px;
        }}
        .alert-banner {{
            background: {accent_color};
            border-left: 6px solid {severity_color};
            padding: 25px 30px;
            margin: 0;
        }}
        .alert-type {{
            display: flex;
            align-items: center;
            font-size: 20px;
            font-weight: 700;
            color: {severity_color};
            margin-bottom: 10px;
        }}
        .alert-type .icon {{
            font-size: 24px;
            margin-right: 10px;
        }}
        .severity-badge {{
            display: inline-block;
            padding: 8px 16px;
            background: {severity_color};
            color: white;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-left: 10px;
        }}
        .content {{ 
            padding: 30px; 
        }}
        .message-box {{
            background: #f8fafc;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
            border-left: 4px solid #3b82f6;
        }}
        .message-box h3 {{
            color: #1e40af;
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 18px;
        }}
        .message-text {{
            color: #374151;
            line-height: 1.6;
            font-size: 16px;
        }}
        .weather-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); 
            gap: 15px; 
            margin-bottom: 30px; 
        }}
        .weather-item {{ 
            text-align: center; 
            padding: 20px 15px; 
            background: linear-gradient(135deg, #f8fafc, #e2e8f0);
            border-radius: 12px; 
            border: 1px solid #e2e8f0;
            transition: transform 0.2s ease;
        }}
        .weather-item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .weather-value {{ 
            font-size: 24px; 
            font-weight: 700; 
            color: #1e40af; 
            margin-bottom: 8px; 
        }}
        .weather-label {{ 
            font-size: 12px; 
            color: #64748b; 
            text-transform: uppercase; 
            letter-spacing: 0.5px;
            font-weight: 600;
        }}
        .weather-icon {{
            font-size: 20px;
            margin-bottom: 8px;
        }}
        .safety-notice {{
            background: linear-gradient(135deg, #fef3e2, #fed7aa);
            border-radius: 12px;
            padding: 25px;
            margin-top: 30px;
            border-left: 4px solid #d97706;
        }}
        .safety-notice h3 {{
            color: #92400e;
            margin-top: 0;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .safety-notice h3::before {{
            content: '⚠️';
            margin-right: 10px;
            font-size: 20px;
        }}
        .footer {{ 
            background: linear-gradient(135deg, #1e40af, #3b82f6);
            padding: 25px 30px; 
            text-align: center; 
            color: white;
        }}
        .footer p {{
            margin: 5px 0;
            opacity: 0.9;
        }}
        .footer .app-name {{
            font-weight: 700;
            font-size: 16px;
        }}
        .divider {{
            height: 1px;
            background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
            margin: 30px 0;
        }}
        @media (max-width: 600px) {{
            .container {{ margin: 10px; border-radius: 12px; }}
            .header {{ padding: 30px 20px; }}
            .content {{ padding: 20px; }}
            .weather-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <h1>{icon} Marine Weather Alert</h1>
                <div class="location">📍 {location_name}</div>
                <div class="timestamp">🕐 {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}</div>
            </div>
        </div>
        
        <div class="alert-banner">
            <div class="alert-type">
                <span class="icon">{icon}</span>
                {alert_type}
                <span class="severity-badge">{severity.upper()}</span>
            </div>
        </div>
        
        <div class="content">
            <div class="message-box">
                <h3>🚨 Alert Details</h3>
                <div class="message-text">{alert_data['message']}</div>
            </div>
            
            <div class="divider"></div>
            
            <h3 style="color: #1e40af; margin-bottom: 20px; display: flex; align-items: center;">
                <span style="margin-right: 10px;">🌊</span>
                Current Marine Conditions
            </h3>
            <div class="weather-grid">
                <div class="weather-item">
                    <div class="weather-icon">💨</div>
                    <div class="weather-value">{alert_data['weather_data'].get('wind_speed', 'N/A')} km/h</div>
                    <div class="weather-label">Wind Speed</div>
                </div>
                <div class="weather-item">
                    <div class="weather-icon">🌊</div>
                    <div class="weather-value">{alert_data['weather_data'].get('wave_height', 'N/A')} m</div>
                    <div class="weather-label">Wave Height</div>
                </div>
                <div class="weather-item">
                    <div class="weather-icon">👁️</div>
                    <div class="weather-value">{alert_data['weather_data'].get('visibility', 'N/A')} m</div>
                    <div class="weather-label">Visibility</div>
                </div>
                <div class="weather-item">
                    <div class="weather-icon">🌡️</div>
                    <div class="weather-value">{alert_data['weather_data'].get('temperature', 'N/A')}°C</div>
                    <div class="weather-label">Temperature</div>
                </div>
            </div>
            
            <div class="safety-notice">
                <h3>Maritime Safety Reminder</h3>
                <p>Always check current weather conditions before departing. Monitor marine radio channels and consider postponing your trip if conditions deteriorate. Your safety is our top priority.</p>
            </div>
        </div>
        
        <div class="footer">
            <p class="app-name">🌊 Smart Ocean Navigation Assistant</p>
            <p>Advanced Marine Weather & AI Hazard Detection System</p>
            <p style="font-size: 12px; opacity: 0.8;">This is an automated alert. Stay safe on the water! ⚓</p>
        </div>
    </div>
</body>
</html>"""
        return html
    
    def _generate_alert_email_text(self, location_name: str, alert_data: Dict) -> str:
        """Generate plain text email content for alerts"""
        severity = alert_data.get('severity', 'low').upper()
        alert_type = alert_data.get('alert_type', 'unknown').replace('_', ' ').title()
        
        text = f"""
🌊 MARINE WEATHER ALERT 🌊
{'='*50}

LOCATION: {location_name}
ALERT TYPE: {alert_type}
SEVERITY: {severity}
TIME: {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}

ALERT DETAILS:
{'-'*20}
{alert_data['message']}

CURRENT MARINE CONDITIONS:
{'-'*30}
💨 Wind Speed: {alert_data['weather_data'].get('wind_speed', 'N/A')} km/h
🌊 Wave Height: {alert_data['weather_data'].get('wave_height', 'N/A')} m
👁️ Visibility: {alert_data['weather_data'].get('visibility', 'N/A')} m
🌡️ Temperature: {alert_data['weather_data'].get('temperature', 'N/A')}°C

⚠️ MARITIME SAFETY REMINDER:
Always check current weather conditions before departing.
Monitor marine radio channels and consider postponing your trip 
if conditions deteriorate. Your safety is our top priority.

{'='*50}
🌊 Smart Ocean Navigation Assistant
Advanced Marine Weather & AI Hazard Detection System
This is an automated alert. Stay safe on the water! ⚓
"""
        return text
    
    def _should_trigger_alert(self, alert_type: str, weather_data: Dict, threshold: float) -> bool:
        """Determine if an alert should be triggered based on weather data and threshold"""
        hazard_probabilities = weather_data.get("hazard_probabilities", {})
        
        if alert_type == "storm":
            return hazard_probabilities.get("storm", 0) > threshold
        elif alert_type == "high_wind":
            wind_speed = weather_data.get("wind_speed", 0)
            return wind_speed > threshold
        elif alert_type == "fog":
            visibility = weather_data.get("visibility", 10000)
            return visibility < threshold
        elif alert_type == "rough_sea":
            wave_height = weather_data.get("wave_height", 0)
            return wave_height > threshold
        elif alert_type == "tsunami":
            return hazard_probabilities.get("tsunami", 0) > threshold
        
        return False
    
    def _generate_alert_message(self, alert_type: str, weather_data: Dict, location_name: str) -> str:
        """Generate human-readable alert message"""
        if alert_type == "storm":
            return f"Storm conditions detected near {location_name}. Avoid travel and seek shelter."
        elif alert_type == "high_wind":
            wind_speed = weather_data.get("wind_speed", 0)
            return f"High wind warning: {wind_speed} km/h winds detected near {location_name}. Small vessels should avoid travel."
        elif alert_type == "fog":
            visibility = weather_data.get("visibility", 10000)
            return f"Fog warning: Visibility reduced to {visibility}m near {location_name}. Navigate with extreme caution."
        elif alert_type == "rough_sea":
            wave_height = weather_data.get("wave_height", 0)
            return f"Rough sea conditions: {wave_height}m waves detected near {location_name}. Exercise caution."
        elif alert_type == "tsunami":
            return f"Tsunami alert for {location_name}. Move to higher ground immediately."
        else:
            return f"Weather alert for {location_name}. Check current conditions before travel."
    
    def _determine_severity(self, alert_type: str, weather_data: Dict) -> str:
        """Determine alert severity level"""
        hazard_probabilities = weather_data.get("hazard_probabilities", {})
        
        if alert_type == "tsunami":
            return "critical"
        elif alert_type == "storm":
            storm_prob = hazard_probabilities.get("storm", 0)
            if storm_prob > 0.8:
                return "high"
            elif storm_prob > 0.5:
                return "medium"
            else:
                return "low"
        elif alert_type == "high_wind":
            wind_speed = weather_data.get("wind_speed", 0)
            if wind_speed > 50:
                return "high"
            elif wind_speed > 30:
                return "medium"
            else:
                return "low"
        else:
            return "medium"
