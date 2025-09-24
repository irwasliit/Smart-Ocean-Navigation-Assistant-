#!/usr/bin/env python3
"""
Test script to verify location coordinate fixes
"""
import asyncio
import sys
import os

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.location_search_service import LocationSearchService

async def test_location_coordinates():
    """Test location search and coordinate handling"""
    print("🧪 Testing Location Coordinate Fixes")
    print("=" * 50)
    
    location_service = LocationSearchService()
    
    # Test cases that might return "Unknown Location"
    test_queries = [
        "Toksun County, China",
        "Remote ocean location",
        "Pacific Ocean 35.0, -120.0",
        "London",
        "Sri Lanka",
        "Unknown test location"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")
        print("-" * 30)
        
        try:
            # Test location search
            results = await location_service.search_locations(query, limit=3)
            
            if results:
                for i, result in enumerate(results[:2]):  # Show top 2 results
                    name = result.get('name', 'N/A')
                    display_name = result.get('display_name', 'N/A')
                    lat = result.get('latitude', 0)
                    lon = result.get('longitude', 0)
                    
                    print(f"  Result {i+1}:")
                    print(f"    Name: {name}")
                    print(f"    Display: {display_name}")
                    print(f"    Coordinates: {lat}, {lon}")
                    print(f"    Has coords: {lat != 0 or lon != 0}")
                    
                    # Check if "Unknown Location" appears anywhere
                    if "Unknown Location" in name or "Unknown Location" in display_name:
                        print(f"    ⚠️  WARNING: 'Unknown Location' found!")
                    else:
                        print(f"    ✅ No 'Unknown Location' text")
            else:
                print("  No results found")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Location coordinate testing completed!")

if __name__ == "__main__":
    asyncio.run(test_location_coordinates())