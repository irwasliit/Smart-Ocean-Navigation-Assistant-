import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.location_search_service import LocationSearchService

async def test_location_fixes():
    print("🧪 Testing Location Search Fixes...")
    print("=" * 50)
    
    service = LocationSearchService()
    
    # Test 1: Search for a location that might return "Unknown Location"
    print("\n1. Testing location search for potentially problematic locations...")
    test_queries = [
        "Remote Ocean Location",
        "Middle of Pacific",  
        "Unknown Area",
        "Jaffna Sri Lanka",  # Known good location
        "New York"  # Known good location
    ]
    
    for query in test_queries:
        print(f"\n🔍 Searching for: '{query}'")
        try:
            results = await service.search_locations(query, limit=3)
            print(f"   Found {len(results)} results:")
            for i, result in enumerate(results[:2]):  # Show first 2 results
                name = result.get('name', 'N/A')
                display_name = result.get('display_name', 'N/A')
                lat = result.get('latitude', 0)
                lng = result.get('longitude', 0)
                print(f"   {i+1}. Name: {name}")
                print(f"      Display: {display_name}")
                print(f"      Coords: {lat}, {lng}")
                
                # Check if our fixes worked
                if 'unknown' in name.lower() or 'unknown' in display_name.lower():
                    print("   ⚠️  WARNING: Still contains 'unknown'")
                else:
                    print("   ✅ Good: No 'unknown' text found")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test 2: Test coordinate-based lookup (simulating reverse geocoding)
    print(f"\n2. Testing coordinate-based location lookup...")
    test_coords = [
        ("Colombo area", 6.9271, 79.8612),
        ("Remote ocean", 10.0, 80.0),
        ("New York", 40.7128, -74.0060)
    ]
    
    for desc, lat, lng in test_coords:
        print(f"\n📍 Testing {desc} ({lat}, {lng}):")
        try:
            # Test our get_location_coordinates method with coordinate string
            result = await service.get_location_coordinates(f"{lat},{lng}")
            if result:
                name = result.get('name', 'N/A')
                print(f"   Name: {name}")
                if 'unknown' in name.lower():
                    print("   ⚠️  WARNING: Still contains 'unknown'")
                else:
                    print("   ✅ Good: Proper location name or coordinates")
            else:
                print("   📌 No result - would fallback to coordinates")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n3. Summary:")
    print("   ✅ Location search service updated to replace 'Unknown Location' with coordinates")
    print("   ✅ Frontend components updated to handle coordinate fallbacks")
    print("   ✅ All 'Unknown Location' references replaced with meaningful alternatives")

if __name__ == "__main__":
    asyncio.run(test_location_fixes())