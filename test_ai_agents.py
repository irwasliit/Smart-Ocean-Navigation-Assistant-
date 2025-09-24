#!/usr/bin/env python3
"""
Simple test script for AI agents
"""

import requests
import json

def test_system_status():
    """Test the system status endpoint"""
    try:
        response = requests.get('http://localhost:8000/api/system-status')
        print(f"System Status Response: {response.status_code}")
        print(f"Content: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"Error testing system status: {e}")
        return None

def test_enhanced_ai_chat():
    """Test the enhanced AI chat endpoint"""
    try:
        data = {
            "message": "Hello, can you analyze current weather conditions?",
            "weather_data": {},
            "route_data": {},
            "location": {"latitude": 40.7128, "longitude": -74.0060}
        }
        
        response = requests.post(
            'http://localhost:8000/api/enhanced-ai/chat',
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Enhanced AI Chat Response: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
        return response
    except Exception as e:
        print(f"Error testing enhanced AI chat: {e}")
        return None

if __name__ == "__main__":
    print("🧪 Testing AI Agents...")
    print("=" * 50)
    
    # Test system status
    print("\n1. Testing System Status...")
    status = test_system_status()
    
    # Test enhanced AI chat
    print("\n2. Testing Enhanced AI Chat...")
    chat_response = test_enhanced_ai_chat()
    
    print("\n" + "=" * 50)
    print("✅ Tests completed!")