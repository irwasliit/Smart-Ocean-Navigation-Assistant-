#!/usr/bin/env python3
"""
Simple test for route analysis API
"""
import requests
import json
import time

def test_route_analysis():
    """Test route analysis with simple data"""
    
    # API endpoint
    url = "http://localhost:8000/api/routes/analyze"
    
    # Simple test data
    test_data = {
        "origin": {
            "lat": 40.7128,
            "lng": -74.0060,
            "name": "New York Harbor"
        },
        "destination": {
            "lat": 51.5074,
            "lng": -0.1278,
            "name": "London"
        },
        "vessel_type": "cargo",
        "departure_date": "2024-01-15"
    }
    
    print("🧪 Testing Route Analysis API")
    print("=" * 50)
    print(f"📍 Origin: {test_data['origin']['name']}")
    print(f"📍 Destination: {test_data['destination']['name']}")
    print(f"⛵ Vessel Type: {test_data['vessel_type']}")
    print(f"📅 Departure: {test_data['departure_date']}")
    print()
    
    try:
        print("🔄 Sending request...")
        start_time = time.time()
        
        response = requests.post(
            url, 
            json=test_data,
            timeout=125  # 125 seconds timeout to test our 120s backend timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ Request took: {duration:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"📝 Analysis ID: {result.get('analysis_id', 'N/A')}")
            print(f"🎯 Risk Level: {result.get('risk_level', 'N/A')}")
            print(f"📊 Success: {result.get('success', False)}")
            
            # Print summary if available
            if 'summary' in result:
                print(f"📋 Summary: {result['summary'][:200]}...")
                
        else:
            print("❌ FAILED!")
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ REQUEST TIMED OUT after 125 seconds")
        print("This indicates the backend timeout (120s) may have been exceeded")
        
    except requests.exceptions.ConnectionError:
        print("🔌 CONNECTION ERROR")
        print("Backend server may not be running on http://localhost:8000")
        
    except Exception as e:
        print(f"💥 UNEXPECTED ERROR: {str(e)}")

if __name__ == "__main__":
    test_route_analysis()