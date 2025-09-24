import sys
import os
sys.path.append('backend')
sys.path.append('backend/services')

import asyncio
from services.location_search_service import LocationSearchService
from services.weather_service import WeatherService

async def test_weather_api():
    print("Testing Weather API Integration...")
    
    # Initialize services
    location_service = LocationSearchService()
    weather_service = WeatherService()
    
    # Test location search
    print("\n1. Testing location search for 'Jaffna Sri Lanka'...")
    try:
        locations = await location_service.search_locations("Jaffna Sri Lanka", 5)
        print(f"Found {len(locations)} locations:")
        for i, loc in enumerate(locations[:3]):
            print(f"  {i+1}. {loc.get('name', 'Unknown')} - Lat: {loc.get('latitude', 0)}, Lon: {loc.get('longitude', 0)}")
        
        if locations:
            # Test weather data for first location
            location = locations[0]
            lat = location.get('latitude')
            lon = location.get('longitude')
            
            print(f"\n2. Testing weather data for {location.get('name')} ({lat}, {lon})...")
            weather_data = await weather_service.get_current_weather(lat, lon)
            
            print("Current Weather Data:")
            print(f"  - Temperature: {weather_data.get('temperature', 'N/A')}°C")
            print(f"  - Humidity: {weather_data.get('humidity', 'N/A')}%")
            print(f"  - Wind Speed: {weather_data.get('wind_speed', 'N/A')} km/h")
            print(f"  - Wind Direction: {weather_data.get('wind_direction', 'N/A')}°")
            print(f"  - Pressure: {weather_data.get('pressure', 'N/A')} hPa")
            print(f"  - Visibility: {weather_data.get('visibility', 'N/A')} m")
            print(f"  - Wave Height: {weather_data.get('wave_height', 'N/A')} m")
            print(f"  - Weather Condition: {weather_data.get('weather_condition', 'N/A')}")
            
            return weather_data
        else:
            print("No locations found!")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_weather_api())
    if result:
        print("\n✅ Weather API test successful!")
    else:
        print("\n❌ Weather API test failed!")