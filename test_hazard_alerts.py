#!/usr/bin/env python3
"""
Test script for the new Hazard Alerts API
"""
import requests
import json
import asyncio
import sys

BASE_URL = "http://localhost:8000"

def test_hazard_alerts_api():
    print("🧪 Testing Hazard Alerts API...")
    print("=" * 50)
    
    # Test locations
    test_locations = [
        {"name": "New York", "lat": 40.7128, "lon": -74.0060},
        {"name": "Miami", "lat": 25.7617, "lon": -80.1918},
        {"name": "London", "lat": 51.5074, "lon": -0.1278},
        {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
        {"name": "Colombo", "lat": 6.9271, "lon": 79.8612},
    ]
    
    # Test different endpoints
    endpoints = [
        "/api/hazards/alerts/status",
        "/api/hazards/alerts/quick",
        "/api/hazards/alerts/comprehensive",
        "/api/hazards/alerts/marine",
        "/api/hazards/alerts/earthquake"
    ]
    
    # Test status endpoint first
    try:
        print("📊 Testing service status...")
        response = requests.get(f"{BASE_URL}/api/hazards/alerts/status", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Service operational")
            print(f"📡 Data sources: {len(data.get('data_sources', {}))}")
            print(f"🚨 Alert types: {', '.join(data.get('alert_types', []))}")
        else:
            print(f"❌ Status check failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Status check error: {e}")
        return
    
    print("\n" + "=" * 50)
    
    # Test with one location
    test_location = test_locations[0]  # New York
    print(f"🌍 Testing with {test_location['name']} ({test_location['lat']}, {test_location['lon']})")
    
    for endpoint in endpoints[1:]:  # Skip status endpoint
        print(f"\n🔍 Testing {endpoint}...")
        try:
            params = {
                'latitude': test_location['lat'],
                'longitude': test_location['lon'],
                'city': test_location['name']
            }
            
            response = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Show key information
                if 'alerts' in data:
                    alert_count = len(data['alerts'])
                    print(f"   ✅ {alert_count} alerts found")
                    
                    if alert_count > 0:
                        for i, alert in enumerate(data['alerts'][:2]):  # Show first 2
                            print(f"      Alert {i+1}: {alert.get('event', 'Unknown')} ({alert.get('severity', 'unknown')})")
                
                if 'safety_status' in data:
                    status = data['safety_status']
                    print(f"   🛡️  Safety: {status.get('status', 'unknown')} (Level {status.get('level', 0)})")
                
                if 'current_weather' in data and data['current_weather']:
                    weather = data['current_weather'].get('current', {})
                    if weather.get('temperature'):
                        print(f"   🌤️  Weather: {weather.get('temperature')}°C, Wind: {weather.get('wind_speed', 'N/A')} km/h")
                
                if 'marine_conditions' in data and data['marine_conditions']:
                    marine = data['marine_conditions']
                    if marine.get('wave_height'):
                        print(f"   🌊 Marine: Wave height {marine.get('wave_height')}m")
                
            else:
                print(f"   ❌ Failed: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Hazard Alerts API test completed!")
    print("\n📋 Usage Examples:")
    print(f"🔗 Quick alerts: {BASE_URL}/api/hazards/alerts/quick?latitude=40.7128&longitude=-74.0060")
    print(f"🔗 Comprehensive: {BASE_URL}/api/hazards/alerts/comprehensive?latitude=40.7128&longitude=-74.0060")
    print(f"🔗 Marine only: {BASE_URL}/api/hazards/alerts/marine?latitude=40.7128&longitude=-74.0060")
    print(f"🔗 Service status: {BASE_URL}/api/hazards/alerts/status")

if __name__ == "__main__":
    test_hazard_alerts_api()