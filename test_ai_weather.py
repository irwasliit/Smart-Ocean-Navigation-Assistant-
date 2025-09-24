import sys
import os
sys.path.append('backend')
sys.path.append('backend/services')

import asyncio
from services.multi_agent_ai_service import MultiAgentAIService

async def test_ai_weather():
    print("Testing AI Weather Integration...")
    
    # Initialize the AI service
    ai_service = MultiAgentAIService()
    
    # Test weather query
    query = "current weather of jaffna sri lanka"
    print(f"\n🤖 Testing query: '{query}'")
    
    try:
        result = await ai_service.process_message(query)
        
        print(f"\n✅ AI Response:")
        print(f"Confidence: {result.get('confidence', 'N/A')}")
        print(f"Response: {result.get('response', 'No response')}")
        
        # Check if response contains real weather data
        response_text = result.get('response', '').lower()
        has_temp = any(word in response_text for word in ['temperature', '°c', 'degrees', 'celsius'])
        has_wind = any(word in response_text for word in ['wind', 'km/h', 'knots'])
        has_humidity = 'humidity' in response_text
        
        print(f"\n📊 Analysis:")
        print(f"Contains temperature: {has_temp}")
        print(f"Contains wind data: {has_wind}")
        print(f"Contains humidity: {has_humidity}")
        
        if has_temp or has_wind or has_humidity:
            print("✅ AI successfully integrated real weather data!")
        else:
            print("❌ AI response appears to be generic, not using real data")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_ai_weather())