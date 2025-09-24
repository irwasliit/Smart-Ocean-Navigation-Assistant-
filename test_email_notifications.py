#!/usr/bin/env python3
"""
Test script for weather email notifications
Run this to test the email functionality
"""

import asyncio
import os
from dotenv import load_dotenv
from services.email_service import EmailService
from services.notification_scheduler import WeatherNotificationScheduler

load_dotenv()

async def test_email_service():
    """Test the email service with sample data"""
    print("Testing Email Service...")
    
    email_service = EmailService()
    
    # Sample weather data
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
    
    # Sample forecast data
    test_forecast_data = [
        {
            'timestamp': '2024-01-15',
            'temperature': 24.0,
            'wind_speed': 12.0,
            'precipitation_probability': 10
        },
        {
            'timestamp': '2024-01-16',
            'temperature': 23.5,
            'wind_speed': 18.0,
            'precipitation_probability': 20
        }
    ]
    
    # Test email (replace with your email)
    test_email = os.getenv("TEST_EMAIL", "test@example.com")
    
    print(f"Sending test email to {test_email}...")
    
    success = await email_service.send_weather_notification(
        to_email=test_email,
        location_name="Test Location - Pacific Ocean",
        weather_data=test_weather_data,
        forecast_data=test_forecast_data
    )
    
    if success:
        print("✅ Test email sent successfully!")
    else:
        print("❌ Failed to send test email")
    
    return success

async def test_scheduler():
    """Test the notification scheduler"""
    print("\nTesting Notification Scheduler...")
    
    scheduler = WeatherNotificationScheduler()
    
    # Test email (replace with your email)
    test_email = os.getenv("TEST_EMAIL", "test@example.com")
    
    print(f"Sending test notification to {test_email}...")
    
    success = await scheduler.test_notification(test_email, "Test Location")
    
    if success:
        print("✅ Test notification sent successfully!")
    else:
        print("❌ Failed to send test notification")
    
    return success

async def main():
    """Main test function"""
    print("🌊 Marine Weather Email Notification Test")
    print("=" * 50)
    
    # Check if email configuration is set
    if not os.getenv("SMTP_USERNAME") or not os.getenv("SMTP_PASSWORD"):
        print("❌ Email configuration not found!")
        print("Please set SMTP_USERNAME and SMTP_PASSWORD in your .env file")
        return
    
    if not os.getenv("TEST_EMAIL"):
        print("⚠️  TEST_EMAIL not set in .env file")
        print("Set TEST_EMAIL=your_email@example.com to test email sending")
        return
    
    try:
        # Test email service
        email_success = await test_email_service()
        
        # Test scheduler
        scheduler_success = await test_scheduler()
        
        print("\n" + "=" * 50)
        if email_success and scheduler_success:
            print("🎉 All tests passed! Email notifications are working.")
        else:
            print("⚠️  Some tests failed. Check your email configuration.")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())


