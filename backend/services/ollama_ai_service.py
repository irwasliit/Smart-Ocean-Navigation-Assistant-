"""
Free Local AI Service using Ollama
No API keys required - runs AI models locally
"""

import requests
import json
from typing import Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

class AgentType(Enum):
    COMMUNICATION_MANAGER = "communication_manager"
    WEATHER_ANALYST = "weather_analyst"
    ROUTE_OPTIMIZER = "route_optimizer"
    HAZARD_DETECTOR = "hazard_detector"

@dataclass
class AgentResponse:
    agent_type: AgentType
    content: str
    confidence: float
    metadata: Dict[str, Any]
    timestamp: datetime

class OllamaAIService:
    """Free local AI service using Ollama"""
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = "llama3.2:1b"  # Lightweight model
        self.available = self._check_ollama_availability()
        
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(self.model in model.get('name', '') for model in models)
            return False
        except:
            return False
    
    async def process_message(self, message: str, context: Dict = None) -> Dict[str, str]:
        """Process message using local AI or fallback"""
        
        if not self.available:
            return self._get_fallback_response(message)
        
        try:
            # Use Ollama for AI response
            prompt = self._build_marine_prompt(message, context)
            response = self._call_ollama(prompt)
            
            return {
                "response": response,
                "context_data": {"ai_provider": "ollama_local", "model": self.model}
            }
            
        except Exception as e:
            print(f"Ollama error: {e}")
            return self._get_fallback_response(message)
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "max_tokens": 200
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get('response', 'No response generated.')
        else:
            raise Exception(f"Ollama API error: {response.status_code}")
    
    def _build_marine_prompt(self, message: str, context: Dict = None) -> str:
        """Build marine navigation specific prompt"""
        system_prompt = """You are a Smart Ocean Navigation Assistant. Provide helpful, safety-focused advice about marine weather, navigation, and maritime safety. Keep responses concise and practical.

Key areas of expertise:
- Marine weather analysis and forecasting
- Route planning and optimization
- Maritime safety and hazard detection
- Navigation best practices

Always prioritize safety and refer to official marine resources when appropriate."""

        user_context = ""
        if context and context.get('location'):
            user_context = f"Location context: {context.get('location')}\n"
        
        return f"{system_prompt}\n\n{user_context}User question: {message}\n\nResponse:"
    
    def _get_fallback_response(self, message: str) -> Dict[str, str]:
        """Fallback responses when AI is unavailable"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['weather', 'wind', 'wave', 'storm', 'forecast']):
            content = "For current marine weather information, please check NOAA Marine Weather Services at weather.gov/marine or your local maritime weather broadcasts on VHF radio. You can also use marine weather apps like PredictWind or Windy."
        elif any(word in message_lower for word in ['route', 'navigation', 'course', 'path', 'optimize']):
            content = "For navigation assistance, please consult your marine charts, check current weather conditions from official sources, and consider using navigation apps like Navionics, ActiveCaptain, or OpenCPN."
        elif any(word in message_lower for word in ['hazard', 'danger', 'safety', 'warning', 'alert']):
            content = "For maritime safety information, please monitor official marine safety broadcasts, NAVTEX transmissions, and check the Coast Guard's Notice to Mariners. Always monitor VHF Channel 16 for emergency communications."
        elif any(word in message_lower for word in ['hello', 'hi', 'help', 'what', 'how']):
            content = "Hello! I'm the Smart Ocean Navigation Assistant. For marine weather, check NOAA Marine Weather. For navigation, use your marine charts and GPS. For safety alerts, monitor VHF radio and Coast Guard broadcasts. How can I help you with your marine navigation needs?"
        else:
            content = "For comprehensive marine information: Weather (weather.gov/marine), Navigation (use marine charts), Safety (monitor VHF radio). How can I assist with your specific marine navigation question?"
        
        return {
            "response": content,
            "context_data": {"fallback_mode": True, "service_status": "local_guidance"}
        }

# Create singleton instance
ollama_service = OllamaAIService()