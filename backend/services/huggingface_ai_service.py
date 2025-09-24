"""
Free AI Service using Hugging Face Inference API
No cost - uses free tier with rate limits
"""

import requests
import json
import aiohttp
import re
from typing import Dict, Any
from datetime import datetime

class HuggingFaceAIService:
    """Free AI service using Hugging Face Inference API"""
    
    def __init__(self):
        # No API key required for public models
        self.base_url = "https://api-inference.huggingface.co/models"
        self.model = "microsoft/DialoGPT-medium"  # Free conversation model
        
    async def process_message(self, message: str, context: Dict = None) -> Dict[str, str]:
        """Process message using Hugging Face free API with real weather data"""
        
        try:
            # Check if this is a weather-related question
            message_lower = message.lower()
            if any(word in message_lower for word in ['weather', 'wind', 'wave', 'storm', 'forecast']):
                # Try to get real weather data
                location = context.get('location', '') if context else ''
                lat = context.get('latitude') if context else None
                lon = context.get('longitude') if context else None
                
                # Extract location from message if not in context
                if not location and not (lat and lon):
                    location_match = re.search(r'(weather|forecast|conditions).*(in|at|for|near)\s+([a-zA-Z\s]+)', message, re.IGNORECASE)
                    if location_match:
                        location = location_match.group(3).strip()
                
                weather_data = await self._fetch_real_weather_data(location, lat, lon)
                if weather_data:
                    response = self._format_weather_response(weather_data, location)
                    return {
                        "response": response,
                        "context_data": {"ai_provider": "huggingface_with_weather", "location": location, "real_data": True}
                    }
            
            # Build marine-focused prompt
            prompt = self._build_marine_prompt(message, context)
            
            # Call Hugging Face API
            response = self._call_huggingface(prompt)
            
            return {
                "response": response,
                "context_data": {"ai_provider": "huggingface_free", "model": self.model}
            }
            
        except Exception as e:
            print(f"Hugging Face error: {e}")
            return await self._get_fallback_response(message, context)
    
    async def _fetch_real_weather_data(self, location: str = None, lat: float = None, lon: float = None) -> Dict[str, Any]:
        """Fetch real-time weather data from the backend API"""
        try:
            if lat is not None and lon is not None:
                # Use coordinates if provided
                url = f"http://localhost:8000/api/weather/current/{lat}/{lon}"
            elif location:
                # Try to get coordinates from location name first
                search_url = f"http://localhost:8000/api/weather/search-locations"
                async with aiohttp.ClientSession() as session:
                    async with session.get(search_url, params={"q": location}) as response:
                        if response.status == 200:
                            search_data = await response.json()
                            locations = search_data.get('results', [])
                            if locations:
                                # Use first match
                                first_location = locations[0]
                                lat = first_location.get('latitude')
                                lon = first_location.get('longitude')
                                url = f"http://localhost:8000/api/weather/current/{lat}/{lon}"
                            else:
                                return None
                        else:
                            return None
            else:
                return None
            
            # Fetch current weather data
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return None
                        
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return None

    def _format_weather_response(self, weather_data: Dict[str, Any], location: str = None) -> str:
        """Format weather data into a readable response"""
        if not weather_data:
            return "🌊 Unable to fetch current weather data. Please check NOAA Marine Weather or VHF broadcasts."
        
        location_str = f" for {location}" if location else ""
        response = f"🌊 **Real-Time Marine Weather{location_str}**\n\n"
        
        # Temperature
        if weather_data.get('temperature'):
            response += f"🌡️ **Temperature:** {weather_data['temperature']}°F\n"
        
        # Wind conditions
        if weather_data.get('wind_speed') and weather_data.get('wind_direction'):
            response += f"💨 **Wind:** {weather_data['wind_direction']} at {weather_data['wind_speed']} mph\n"
        elif weather_data.get('wind_speed'):
            response += f"💨 **Wind Speed:** {weather_data['wind_speed']} mph\n"
        
        # Wave conditions
        if weather_data.get('wave_height'):
            response += f"🌊 **Wave Height:** {weather_data['wave_height']} ft"
            if weather_data.get('wave_period'):
                response += f" (Period: {weather_data['wave_period']}s)"
            response += "\n"
        
        # Visibility
        if weather_data.get('visibility'):
            response += f"👁️ **Visibility:** {weather_data['visibility']} miles\n"
        
        # Pressure
        if weather_data.get('pressure'):
            response += f"📊 **Pressure:** {weather_data['pressure']} mb\n"
        
        # Weather condition
        if weather_data.get('weather_condition'):
            response += f"☁️ **Conditions:** {weather_data['weather_condition']}\n"
        
        # Hazard warnings
        if weather_data.get('hazard_probabilities'):
            hazards = weather_data['hazard_probabilities']
            high_risk_hazards = [hazard for hazard, prob in hazards.items() if prob > 0.6]
            if high_risk_hazards:
                response += f"\n⚠️ **High Risk Hazards:** {', '.join(high_risk_hazards)}\n"
        
        response += f"\n📅 **Updated:** {datetime.now().strftime('%H:%M UTC')}"
        response += "\n\n💡 **Powered by real-time weather data!**"
        
        return response
    
    def _call_huggingface(self, prompt: str) -> str:
        """Call Hugging Face Inference API"""
        
        # Try text generation model
        url = f"{self.base_url}/gpt2"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 150,
                "temperature": 0.7,
                "return_full_text": False
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', 'No response generated.')
            return 'No response generated.'
        else:
            raise Exception(f"Hugging Face API error: {response.status_code}")
    
    def _build_marine_prompt(self, message: str, context: Dict = None) -> str:
        """Build marine navigation specific prompt"""
        base_prompt = "Marine Navigation Assistant: "
        
        # Add context if available
        if context and context.get('location'):
            base_prompt += f"Location: {context.get('location')}. "
        
        # Add the user message
        base_prompt += f"Question: {message}. Helpful maritime advice: "
        
        return base_prompt
    
    async def _get_fallback_response(self, message: str, context: Dict = None) -> Dict[str, str]:
        """Fallback responses when AI is unavailable"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['weather', 'wind', 'wave', 'storm']):
            content = "🌊 For marine weather: Check NOAA Marine Weather (weather.gov/marine), PredictWind app, or VHF weather broadcasts. Always verify conditions before departure!"
        elif any(word in message_lower for word in ['route', 'navigation', 'course']):
            content = "🧭 For route planning: Use marine charts, Navionics app, or OpenCPN. Check tides, currents, and weather. File a float plan with someone ashore!"
        elif any(word in message_lower for word in ['safety', 'emergency', 'hazard']):
            content = "⚠️ For safety: Monitor VHF Channel 16, check Notice to Mariners, carry proper safety equipment. In emergency, call Coast Guard on VHF 16 or *CG (*24)!"
        else:
            content = "⚓ Welcome to Marine Navigation Assistant! I can help with weather, routes, and safety. For official info: NOAA Marine (weather.gov/marine), Coast Guard, and your marine charts."
        
        return {
            "response": content,
            "context_data": {"fallback_mode": True, "service_status": "free_guidance"}
        }

# Create singleton instance
huggingface_service = HuggingFaceAIService()