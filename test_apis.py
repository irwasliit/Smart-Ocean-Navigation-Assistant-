#!/usr/bin/env python3
"""
Test script to check API key configurations
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_api():
    """Test OpenAI API"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your-openai-api-key":
        print("❌ OpenAI API key not configured")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            },
            timeout=10
        )
        if response.status_code == 200:
            print("✅ OpenAI API key is working")
            return True
        else:
            print(f"❌ OpenAI API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return False

def test_stormglass_api():
    """Test StormGlass API"""
    api_key = os.getenv("STORMGLASS_API_KEY")
    if not api_key or api_key == "your-stormglass-api-key":
        print("❌ StormGlass API key not configured")
        return False
    
    try:
        headers = {"Authorization": api_key}
        response = requests.get(
            "https://api.stormglass.io/v2/weather/point",
            headers=headers,
            params={
                "lat": 6.9271,
                "lng": 79.8612,
                "params": "waveHeight,windSpeed"
            },
            timeout=10
        )
        if response.status_code == 200:
            print("✅ StormGlass API key is working")
            return True
        else:
            print(f"❌ StormGlass API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ StormGlass API test failed: {e}")
        return False

def test_open_meteo_api():
    """Test Open-Meteo API (free, no key needed)"""
    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": 6.9271,
                "longitude": 79.8612,
                "current": "temperature_2m,wind_speed_10m"
            },
            timeout=10
        )
        if response.status_code == 200:
            print("✅ Open-Meteo API is working (free)")
            return True
        else:
            print(f"❌ Open-Meteo API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Open-Meteo API test failed: {e}")
        return False

def test_email_config():
    """Test email configuration"""
    smtp_server = os.getenv("SMTP_SERVER")
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    if not smtp_server or smtp_server == "smtp.gmail.com":
        print("⚠️  Email configuration not set up")
        return False
    
    if not email_user or email_user == "your-email@gmail.com":
        print("⚠️  Email user not configured")
        return False
    
    if not email_password or email_password == "your-app-password":
        print("⚠️  Email password not configured")
        return False
    
    print("✅ Email configuration appears to be set up")
    return True

def main():
    """Main test function"""
    print("🌊 Marine Weather & AI Hazard Assistant - API Test")
    print("=" * 60)
    
    print("\n🔍 Testing API configurations...")
    
    # Test APIs
    openai_working = test_openai_api()
    stormglass_working = test_stormglass_api()
    openmeteo_working = test_open_meteo_api()
    email_configured = test_email_config()
    
    print("\n📊 Summary:")
    print(f"OpenAI API: {'✅ Working' if openai_working else '❌ Not configured'}")
    print(f"StormGlass API: {'✅ Working' if stormglass_working else '❌ Not configured'}")
    print(f"Open-Meteo API: {'✅ Working' if openmeteo_working else '❌ Not working'}")
    print(f"Email Config: {'✅ Configured' if email_configured else '⚠️  Not configured'}")
    
    print("\n💡 Recommendations:")
    if not openai_working:
        print("- Get OpenAI API key from: https://platform.openai.com/")
    if not stormglass_working:
        print("- Get StormGlass API key from: https://stormglass.io/")
    if not email_configured:
        print("- Set up Gmail SMTP credentials for email alerts")
    
    if openmeteo_working:
        print("- ✅ Basic weather functionality will work with Open-Meteo")
    
    print("\n🎯 The application will work with basic features even without all API keys!")

if __name__ == "__main__":
    main()
