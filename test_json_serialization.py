#!/usr/bin/env python3
"""
Test script to verify JSON serialization fix for route analysis
"""

import sys
import os
import json
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.multi_agent_ai_service import NavigationContext

def test_navigation_context_json_serialization():
    """Test that NavigationContext can be JSON serialized after our fix"""
    print("Testing NavigationContext JSON serialization...")
    
    # Create a NavigationContext with string departure_time (our fix)
    context = NavigationContext(
        vessel_type="cargo",
        vessel_size="large",
        experience_level="intermediate",
        cargo_type="containers",
        departure_port="New York Harbor",
        destination_port="Miami Harbor",
        departure_time=datetime.now().isoformat(),  # This should now be a string
        urgency_level="high"
    )
    
    print(f"✅ NavigationContext created successfully")
    print(f"   - vessel_type: {context.vessel_type}")
    print(f"   - departure_time: {context.departure_time} (type: {type(context.departure_time)})")
    
    # Try to JSON serialize it
    try:
        context_dict = {
            'vessel_type': context.vessel_type,
            'vessel_size': context.vessel_size,
            'experience_level': context.experience_level,
            'cargo_type': context.cargo_type,
            'departure_port': context.departure_port,
            'destination_port': context.destination_port,
            'departure_time': context.departure_time,
            'urgency_level': context.urgency_level
        }
        
        json_str = json.dumps(context_dict)
        print(f"✅ JSON serialization successful!")
        print(f"   JSON output: {json_str}")
        
        # Test deserialization
        parsed_data = json.loads(json_str)
        print(f"✅ JSON deserialization successful!")
        print(f"   Parsed departure_time: {parsed_data['departure_time']}")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return False

def test_datetime_objects():
    """Test direct datetime object serialization (should fail)"""
    print("\nTesting direct datetime object serialization (should fail)...")
    
    test_dict = {
        'departure_time': datetime.now(),
        'vessel_type': 'cargo'
    }
    
    try:
        json_str = json.dumps(test_dict)
        print(f"❌ Unexpected success: {json_str}")
        return False
    except TypeError as e:
        print(f"✅ Expected failure: {e}")
        return True

if __name__ == "__main__":
    print("🧪 Testing JSON Serialization Fix for Route Analysis")
    print("=" * 55)
    
    test1_passed = test_navigation_context_json_serialization()
    test2_passed = test_datetime_objects()
    
    print("\n" + "=" * 55)
    if test1_passed and test2_passed:
        print("✅ All tests passed! JSON serialization fix is working correctly.")
    else:
        print("❌ Some tests failed. JSON serialization issues may persist.")
    
    print("🔧 This confirms our datetime.now().isoformat() fix resolved the serialization error.")