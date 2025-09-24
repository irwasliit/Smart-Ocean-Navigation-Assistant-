#!/usr/bin/env python3
"""
Test script for delete location functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_delete_location():
    print("🧪 Testing Delete Location API...")
    
    # Step 1: Register a test user or login
    register_data = {
        "email": "test_delete@test.com", 
        "password": "testpassword123",
        "full_name": "Test Delete User"
    }
    
    try:
        # Try to register first (might fail if user exists)
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        if register_response.status_code == 200:
            print("✅ User registered successfully")
        else:
            print(f"ℹ️  Registration response: {register_response.status_code}")
        
        # Now try to login
        login_data = {"email": "test_delete@test.com", "password": "testpassword123"}
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"✅ Login successful")
        
        # Step 2: Get existing locations
        locations_response = requests.get(f"{BASE_URL}/api/weather/locations", headers=headers)
        if locations_response.status_code != 200:
            print(f"❌ Failed to fetch locations: {locations_response.status_code}")
            return
        
        locations = locations_response.json()
        print(f"📍 Found {len(locations)} locations")
        
        if not locations:
            # Create a test location first
            print("🆕 Creating test location...")
            create_data = {
                "name": "Test Location for Delete",
                "latitude": 6.9271,
                "longitude": 79.8612,
                "location_type": "single"
            }
            create_response = requests.post(f"{BASE_URL}/api/weather/locations", 
                                          json=create_data, headers=headers)
            if create_response.status_code != 200:
                print(f"❌ Failed to create test location: {create_response.status_code}")
                return
            
            location_id = create_response.json()["id"]
            print(f"✅ Created test location with ID: {location_id}")
        else:
            location_id = locations[0]["id"]
            print(f"🎯 Testing delete with location ID: {location_id}")
        
        # Step 3: Test delete
        delete_response = requests.delete(f"{BASE_URL}/api/weather/locations/{location_id}", 
                                        headers=headers)
        print(f"🗑️  Delete response: {delete_response.status_code}")
        print(f"📝 Delete message: {delete_response.text}")
        
        if delete_response.status_code == 200:
            print("✅ Delete API is working correctly!")
            
            # Verify deletion
            verify_response = requests.get(f"{BASE_URL}/api/weather/locations", headers=headers)
            new_locations = verify_response.json()
            print(f"🔍 Locations after deletion: {len(new_locations)}")
        else:
            print(f"❌ Delete failed: {delete_response.status_code} - {delete_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_delete_location()