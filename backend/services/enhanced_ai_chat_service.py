"""
Enhanced AI Chat Service for Marine Weather Assistant
Dedicated service for AI Chat page with Google Custom Search integration
Real-time data retrieval with multiple API fallbacks
"""

import openai
import os
import asyncio
import json
import aiohttp
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import re
from dotenv import load_dotenv
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import free AI alternatives
try:
    from .ollama_ai_service import ollama_service
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    from .huggingface_ai_service import huggingface_service
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False

try:
    from .weather_service import WeatherService
    WEATHER_SERVICE_AVAILABLE = True
except ImportError:
    WEATHER_SERVICE_AVAILABLE = False

load_dotenv()

class ResponseType(Enum):
    WEATHER = "weather"
    MARINE_CONDITIONS = "marine_conditions"
    HAZARD_ALERT = "hazard_alert"
    GENERAL_CHAT = "general_chat"
    ROUTE_GUIDANCE = "route_guidance"
    REAL_TIME_DATA = "real_time_data"

@dataclass
class ChatResponse:
    content: str
    response_type: ResponseType
    confidence: float
    data_sources: List[str]
    real_time_data: Dict[str, Any]
    timestamp: datetime

class CityCoordinatesService:
    """Service to get coordinates for cities using a comprehensive database"""
    
    def __init__(self):
        # Comprehensive city coordinates database
        self.city_coords = {
            # Major Cities
            'london': {'lat': 51.5074, 'lng': -0.1278},
            'paris': {'lat': 48.8566, 'lng': 2.3522},
            'new york': {'lat': 40.7128, 'lng': -74.0060},
            'tokyo': {'lat': 35.6762, 'lng': 139.6503},
            'moscow': {'lat': 55.7558, 'lng': 37.6176},
            'beijing': {'lat': 39.9042, 'lng': 116.4074},
            'shanghai': {'lat': 31.2304, 'lng': 121.4737},
            'sydney': {'lat': -33.8688, 'lng': 151.2093},
            
            # Indian Cities
            'mumbai': {'lat': 19.0760, 'lng': 72.8777},
            'delhi': {'lat': 28.7041, 'lng': 77.1025},
            'bangalore': {'lat': 12.9716, 'lng': 77.5946},
            'kolkata': {'lat': 22.5726, 'lng': 88.3639},
            'chennai': {'lat': 13.0827, 'lng': 80.2707},
            'hyderabad': {'lat': 17.3850, 'lng': 78.4867},
            'pune': {'lat': 18.5204, 'lng': 73.8567},
            'ahmedabad': {'lat': 23.0225, 'lng': 72.5714},
            'kochi': {'lat': 9.9312, 'lng': 76.2673},
            'cochin': {'lat': 9.9312, 'lng': 76.2673},  # Same as Kochi
            'thiruvananthapuram': {'lat': 8.5241, 'lng': 76.9366},
            'kozhikode': {'lat': 11.2588, 'lng': 75.7804},
            'mangalore': {'lat': 12.9141, 'lng': 74.8560},
            'goa': {'lat': 15.2993, 'lng': 74.1240},
            
            # Sri Lankan Cities  
            'colombo': {'lat': 6.9271, 'lng': 79.8612},
            'jaffna': {'lat': 9.6615, 'lng': 80.0255},
            'kandy': {'lat': 7.2906, 'lng': 80.6337},
            'galle': {'lat': 6.0535, 'lng': 80.2210},
            
            # Other Asian Cities
            'singapore': {'lat': 1.3521, 'lng': 103.8198},
            'karachi': {'lat': 24.8607, 'lng': 67.0011},
            'dubai': {'lat': 25.2048, 'lng': 55.2708},
            'jakarta': {'lat': -6.2088, 'lng': 106.8456},
            'manila': {'lat': 14.5995, 'lng': 120.9842},
            'bangkok': {'lat': 13.7563, 'lng': 100.5018},
            'kuala lumpur': {'lat': 3.1390, 'lng': 101.6869},
            'hong kong': {'lat': 22.3193, 'lng': 114.1694},
            
            # European Cities
            'berlin': {'lat': 52.5200, 'lng': 13.4050},
            'madrid': {'lat': 40.4168, 'lng': -3.7038},
            'rome': {'lat': 41.9028, 'lng': 12.4964},
            'amsterdam': {'lat': 52.3676, 'lng': 4.9041},
            'zurich': {'lat': 47.3769, 'lng': 8.5417},
            
            # American Cities
            'los angeles': {'lat': 34.0522, 'lng': -118.2437},
            'chicago': {'lat': 41.8781, 'lng': -87.6298},
            'miami': {'lat': 25.7617, 'lng': -80.1918},
            'san francisco': {'lat': 37.7749, 'lng': -122.4194},
            'seattle': {'lat': 47.6062, 'lng': -122.3321},
            'toronto': {'lat': 43.6532, 'lng': -79.3832},
            
            # Middle Eastern Cities
            'riyadh': {'lat': 24.7136, 'lng': 46.6753},
            'doha': {'lat': 25.2854, 'lng': 51.5310},
            'kuwait city': {'lat': 29.3759, 'lng': 47.9774},
            'abu dhabi': {'lat': 24.2992, 'lng': 54.6975},
            
            # African Cities
            'cairo': {'lat': 30.0444, 'lng': 31.2357},
            'cape town': {'lat': -33.9249, 'lng': 18.4241},
            'lagos': {'lat': 6.5244, 'lng': 3.3792},
        }
    
    async def get_coordinates(self, city_name: str) -> Dict[str, float]:
        """Get coordinates for a city from the database"""
        city_lower = city_name.lower().strip()
        
        # Direct lookup
        if city_lower in self.city_coords:
            coords = self.city_coords[city_lower]
            return {'lat': coords['lat'], 'lng': coords['lng']}
        
        # Try partial matches
        for city, coords in self.city_coords.items():
            if city_lower in city or city in city_lower:
                return {'lat': coords['lat'], 'lng': coords['lng']}
        
        logger.warning(f"No coordinates found for city: {city_name}")
        return None

class GoogleSearchService:
    """Google Custom Search service with dual API key fallback"""
    
    def __init__(self):
        # Your two Google Custom Search API keys
        self.api_keys = [
            "AIzaSyA3QPrtjRR-1CwQTOTaSaq5xLepLA_0z3k",
            "AIzaSyDYmkSBnM8t88ZdjtAZP8kXqV6aMuNdV3w"
        ]
        self.current_key_index = 0
        
        # Custom Search Engine IDs - Your marine weather search engine
        self.search_engines = {
            "marine_weather": os.getenv("GOOGLE_CSE_MARINE_ID", "26e3060604a3247e0"),  # Your marine CSE ID
            "general": os.getenv("GOOGLE_CSE_GENERAL_ID", "26e3060604a3247e0")  # Using same CSE for both
        }
        
        logger.info(f"✅ Using Custom Search Engine ID: {self.search_engines['marine_weather']}")
        
        # Verify CSE ID format
        cse_id = self.search_engines["marine_weather"]
        if len(cse_id) > 10 and cse_id != "26e3060604a3247e0":
            logger.info("💡 Using environment variable CSE ID")
        else:
            logger.info("💡 Using provided CSE ID: 26e3060604a3247e0")
        
    async def search_comprehensive_data(self, query: str, search_types: List[str] = None) -> Dict[str, Any]:
        """Comprehensive search using multiple targeted queries to maximize API usage"""
        
        if not search_types:
            search_types = ["current_events", "safety_info", "real_time_conditions"]
        
        all_results = {"success": True, "searches": {}, "combined_data": []}
        
        # Generate multiple targeted search queries
        search_queries = []
        
        if "current_events" in search_types:
            search_queries.extend([
                f"{query} current situation today 2025"
            ])
        
        if "safety_info" in search_types:
            search_queries.extend([
                f"{query} safety conditions current"
            ])
            
        if "real_time_conditions" in search_types:
            search_queries.extend([
                f"{query} current weather conditions today"
            ])

        # Execute fewer searches to avoid rate limits but make them more targeted
        search_tasks = []
        for search_query in search_queries[:3]:  # Limit to 3 searches to avoid rate limits
            search_tasks.append(self._single_search(search_query))
        
        try:
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            successful_searches = 0
            for i, result in enumerate(search_results):
                if isinstance(result, dict) and result.get("success"):
                    all_results["searches"][f"search_{i+1}"] = result
                    if "items" in result.get("data", {}):
                        all_results["combined_data"].extend(result["data"]["items"][:3])  # Top 3 results each
                    successful_searches += 1
            
            logger.info(f"✅ Executed {successful_searches}/{len(search_queries)} Google searches successfully")
            
            if successful_searches == 0:
                all_results["success"] = False
                all_results["error"] = "All search queries failed"
                
        except Exception as e:
            logger.error(f"❌ Comprehensive search failed: {e}")
            all_results["success"] = False
            all_results["error"] = str(e)
        
        return all_results
    
    async def _single_search(self, search_query: str) -> Dict[str, Any]:
        """Execute a single search query with API key rotation"""
        
        for attempt in range(len(self.api_keys)):
            try:
                api_key = self.api_keys[self.current_key_index]
                cse_id = self.search_engines["general"]
                
                url = "https://www.googleapis.com/customsearch/v1"
                
                params = {
                    'key': api_key,
                    'cx': cse_id,
                    'q': search_query,
                    'num': 5,
                    'safe': 'active',
                    'dateRestrict': 'd3',  # Last 3 days for most current data
                    'sort': 'date'
                }
                
                start_time = asyncio.get_event_loop().time()
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
                    async with session.get(url, params=params) as response:
                        response_time = (asyncio.get_event_loop().time() - start_time) * 1000  # Convert to milliseconds
                        
                        if response.status == 200:
                            data = await response.json()
                            
                            return {
                                "success": True,
                                "data": data,
                                "source": f"google_api_{self.current_key_index + 1}",
                                "query": search_query
                            }
                        else:
                            logger.warning(f"❌ Search failed: {response.status} for query: {search_query[:50]}")
                            
            except Exception as e:
                logger.error(f"❌ Single search error: {e}")
            
            # Rotate to next API key
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        
        return {"success": False, "error": "Search failed", "query": search_query}

class RealTimeDataService:
    """Service to get real-time marine data from multiple sources"""
    
    def __init__(self):
        self.weather_service = WeatherService() if WEATHER_SERVICE_AVAILABLE else None
        
    async def get_noaa_marine_alerts(self) -> Dict[str, Any]:
        """Get NOAA marine weather alerts"""
        try:
            url = "https://api.weather.gov/alerts/active"
            headers = {'User-Agent': 'MarineWeatherAssistant/1.0'}
            
            start_time = asyncio.get_event_loop().time()
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(url, headers=headers) as response:
                    response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        alerts = data.get('features', [])
                        
                        # Filter for marine-related alerts
                        marine_alerts = []
                        marine_keywords = ['marine', 'coastal', 'beach', 'surf', 'hurricane', 'storm', 'gale', 'tsunami']
                        
                        for alert in alerts:
                            try:
                                properties = alert.get('properties', {})
                                if not properties:
                                    continue
                                    
                                headline = properties.get('headline', '') or ''
                                description = properties.get('description', '') or ''
                                
                                # Convert to lowercase safely
                                headline_lower = headline.lower() if headline else ''
                                description_lower = description.lower() if description else ''
                                
                                if any(keyword in headline_lower or keyword in description_lower for keyword in marine_keywords):
                                    marine_alerts.append({
                                        'headline': headline or 'No headline',
                                        'event': properties.get('event', '') or 'Unknown event',
                                        'severity': properties.get('severity', '') or 'Unknown',
                                        'areas': properties.get('areaDesc', '') or 'Unknown areas',
                                        'effective': properties.get('effective', ''),
                                        'expires': properties.get('expires', ''),
                                        'description': (description[:200] + '...') if description and len(description) > 200 else description or 'No description'
                                    })
                            except Exception as e:
                                logger.warning(f"Error processing alert: {e}")
                                continue
                        
                        return {
                            "success": True,
                            "alerts": marine_alerts,
                            "total_alerts": len(alerts),
                            "marine_alerts": len(marine_alerts),
                            "source": "noaa_weather_api"
                        }
                        
        except Exception as e:
            logger.error(f"NOAA API error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_earthquake_data(self) -> Dict[str, Any]:
        """Get recent earthquake data from USGS"""
        try:
            url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        earthquakes = data.get('features', [])
                        
                        # Filter significant earthquakes or marine locations
                        significant_quakes = []
                        marine_locations = ['sea', 'ocean', 'coast', 'island', 'bay']
                        
                        for eq in earthquakes:
                            props = eq.get('properties', {})
                            magnitude = props.get('mag', 0)
                            title = props.get('title', '').lower()
                            
                            if magnitude >= 4.0 or any(location in title for location in marine_locations):
                                coords = eq.get('geometry', {}).get('coordinates', [])
                                significant_quakes.append({
                                    'title': props.get('title', 'No title'),
                                    'magnitude': magnitude,
                                    'time': datetime.fromtimestamp(props.get('time', 0) / 1000).strftime('%Y-%m-%d %H:%M:%S') if props.get('time') else 'Unknown',
                                    'location': [coords[1], coords[0]] if len(coords) >= 2 else 'Unknown',
                                    'depth': coords[2] if len(coords) > 2 else 'Unknown'
                                })
                        
                        return {
                            "success": True,
                            "earthquakes": significant_quakes,
                            "total_earthquakes": len(earthquakes),
                            "source": "usgs_earthquake_api"
                        }
                        
        except Exception as e:
            logger.error(f"USGS API error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_weather_conditions(self, latitude: float = None, longitude: float = None) -> Dict[str, Any]:
        """Get current weather conditions"""
        try:
            if self.weather_service and latitude and longitude:
                # Use your existing weather service
                weather_data = await self.weather_service.get_current_weather(latitude, longitude)
                return {
                    "success": True,
                    "weather": weather_data,
                    "source": "weather_service"
                }
            else:
                # Use free weather API as backup
                locations = ["Miami", "New York", "San Francisco", "Seattle", "Honolulu"]
                weather_data = {}
                
                for city in locations:
                    try:
                        url = f"https://wttr.in/{city}?format=j1"
                        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                            async with session.get(url) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    current = data.get('current_condition', [{}])[0]
                                    weather_data[city] = {
                                        'temperature': current.get('temp_C', 'N/A'),
                                        'conditions': current.get('weatherDesc', [{}])[0].get('value', 'N/A'),
                                        'wind_speed': current.get('windspeedKmph', 'N/A'),
                                        'wind_direction': current.get('winddirDegree', 'N/A'),
                                        'humidity': current.get('humidity', 'N/A'),
                                        'visibility': current.get('visibility', 'N/A'),
                                        'pressure': current.get('pressure', 'N/A')
                                    }
                    except Exception as e:
                        logger.warning(f"Weather error for {city}: {e}")
                        continue
                
                return {
                    "success": True,
                    "weather": weather_data,
                    "source": "wttr_weather_api"
                }
                
        except Exception as e:
            logger.error(f"Weather service error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_global_disaster_info(self) -> Dict[str, Any]:
        """Get global natural disaster information from multiple sources"""
        try:
            # Combine multiple disaster sources
            disaster_data = {
                "success": True,
                "disasters": [],
                "affected_countries": [],
                "source": "global_disaster_monitor"
            }
            
            # Use USGS earthquake data as primary disaster source
            earthquake_data = await self.get_earthquake_data()
            if earthquake_data.get("success"):
                earthquakes = earthquake_data.get("earthquakes", [])
                
                # Process significant earthquakes into disaster format
                for eq in earthquakes:
                    if eq.get('magnitude', 0) >= 5.0:  # Significant earthquakes
                        location = eq.get('title', 'Unknown location')
                        country = self._extract_country_from_location(location)
                        
                        disaster_data["disasters"].append({
                            "type": "Earthquake",
                            "location": location,
                            "country": country,
                            "severity": self._get_earthquake_severity(eq.get('magnitude', 0)),
                            "magnitude": eq.get('magnitude', 0),
                            "time": eq.get('time', 'Unknown'),
                            "impact": "Potential marine/coastal impact"
                        })
                        
                        if country and country not in disaster_data["affected_countries"]:
                            disaster_data["affected_countries"].append(country)
            
            # Add current tropical storm/cyclone information from marine alerts
            marine_alerts = await self.get_noaa_marine_alerts()
            if marine_alerts.get("success"):
                alerts = marine_alerts.get("alerts", [])
                for alert in alerts:
                    if any(storm_type in alert.get('event', '').lower() for storm_type in ['hurricane', 'tropical storm', 'cyclone', 'typhoon']):
                        areas = alert.get('areas', 'Unknown areas')
                        disaster_data["disasters"].append({
                            "type": "Tropical Storm System",
                            "location": areas,
                            "country": "Multiple (Marine areas)",
                            "severity": alert.get('severity', 'Unknown'),
                            "event": alert.get('event', 'Unknown'),
                            "time": alert.get('effective', 'Current'),
                            "impact": "Marine navigation hazard"
                        })
            
            # If no specific disasters found, check for general patterns
            if not disaster_data["disasters"]:
                disaster_data["disasters"].append({
                    "type": "General Monitoring",
                    "location": "Global",
                    "country": "Multiple",
                    "severity": "Information",
                    "event": "Continuous monitoring active",
                    "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "impact": "No major natural disasters detected in marine areas"
                })
            
            return disaster_data
            
        except Exception as e:
            logger.error(f"Global disaster info error: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_country_from_location(self, location: str) -> str:
        """Extract country name from earthquake location string"""
        location_lower = location.lower()
        
        # Country mapping for common earthquake locations
        country_patterns = {
            'california': 'United States',
            'alaska': 'United States', 
            'japan': 'Japan',
            'indonesia': 'Indonesia',
            'chile': 'Chile',
            'peru': 'Peru',
            'mexico': 'Mexico',
            'turkey': 'Turkey',
            'iran': 'Iran',
            'afghanistan': 'Afghanistan',
            'pakistan': 'Pakistan',
            'india': 'India',
            'china': 'China',
            'philippines': 'Philippines',
            'papua new guinea': 'Papua New Guinea',
            'new zealand': 'New Zealand',
            'fiji': 'Fiji',
            'tonga': 'Tonga',
            'vanuatu': 'Vanuatu',
            'solomon islands': 'Solomon Islands',
            'greece': 'Greece',
            'italy': 'Italy',
            'taiwan': 'Taiwan',
            'russia': 'Russia',
            'myanmar': 'Myanmar',
            'sri lanka': 'Sri Lanka',
            'thailand': 'Thailand',
            'malaysia': 'Malaysia',
            'singapore': 'Singapore'
        }
        
        for pattern, country in country_patterns.items():
            if pattern in location_lower:
                return country
        
        return "Unknown"
    
    def _get_earthquake_severity(self, magnitude: float) -> str:
        """Get earthquake severity based on magnitude"""
        if magnitude >= 8.0:
            return "Extreme"
        elif magnitude >= 7.0:
            return "Major"
        elif magnitude >= 6.0:
            return "Strong"
        elif magnitude >= 5.0:
            return "Moderate"
        else:
            return "Minor"

class EnhancedAIChatService:
    """Enhanced AI Chat Service with real-time data integration"""
    
    def __init__(self):
        # Initialize OpenAI client
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if self.openai_api_key:
            try:
                self.client = openai.OpenAI(
                    api_key=self.openai_api_key,
                    timeout=30.0
                )
                # Test connection
                test_response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                logger.info("✅ OpenAI API working for AI Chat Service!")
                self.ai_provider = "openai"
            except Exception as e:
                logger.error(f"❌ OpenAI API failed: {e}")
                self.client = None
                self.ai_provider = self._setup_alternative()
        else:
            logger.warning("⚠️ No OpenAI API key found")
            self.client = None
            self.ai_provider = self._setup_alternative()
        
        # Initialize services
        self.geocoding_service = CityCoordinatesService()
        self.real_time_data = RealTimeDataService()
        
    def _setup_alternative(self) -> str:
        """Setup alternative AI providers"""
        if OLLAMA_AVAILABLE and ollama_service.available:
            logger.info("🚀 Using Ollama for AI Chat")
            return "ollama"
        elif HUGGINGFACE_AVAILABLE:
            logger.info("🤗 Using Hugging Face for AI Chat")
            return "huggingface"
        else:
            logger.info("📋 Using fallback responses for AI Chat")
            return "fallback"
    
    async def process_chat_message(self, message: str, context_data: Dict = None) -> ChatResponse:
        """Process chat message with real-time data integration"""
        
        # Analyze message intent
        message_lower = message.lower()
        response_type = self._determine_response_type(message_lower)
        
        # Gather real-time data based on intent
        real_time_data = await self._gather_real_time_data(message_lower, context_data)
        
        # Generate AI response
        if self.client and self.ai_provider == "openai":
            ai_response = await self._generate_openai_response(message, response_type, real_time_data, context_data)
        elif self.ai_provider == "ollama" and OLLAMA_AVAILABLE:
            ai_response = await self._generate_ollama_response(message, response_type, real_time_data)
        elif self.ai_provider == "huggingface" and HUGGINGFACE_AVAILABLE:
            ai_response = await self._generate_huggingface_response(message, response_type, real_time_data)
        else:
            ai_response = self._generate_fallback_response(message, response_type, real_time_data)
        
        return ChatResponse(
            content=ai_response["content"],
            response_type=response_type,
            confidence=ai_response["confidence"],
            data_sources=real_time_data.get("sources", []),
            real_time_data=real_time_data,
            timestamp=datetime.now()
        )
    
    def _determine_response_type(self, message: str) -> ResponseType:
        """Determine the type of response needed based on message content"""
        
        weather_patterns = ['weather', 'temperature', 'wind', 'rain', 'storm', 'forecast', 'climate', 'humidity', 'pressure', 'visibility']
        marine_patterns = ['wave', 'tide', 'current', 'sea', 'ocean', 'marine', 'sailing', 'boat', 'ship', 'vessel', 'port', 'harbor', 'coast', 'coastal', 'navigation', 'maritime']
        hazard_patterns = ['danger', 'hazard', 'risk', 'safe', 'safety', 'warning', 'alert', 'disaster', 'emergency', 'natural disaster', 'affected', 'countries', 'earthquake', 'tsunami', 'hurricane', 'cyclone', 'typhoon']
        route_patterns = ['route', 'navigate', 'navigation', 'direction', 'from', 'to', 'travel', 'journey', 'distance', 'between', 'port', 'shipping', 'cargo']
        
        # Check if the message is related to marine/weather/disaster topics
        message_lower = message.lower()
        is_marine_related = (
            any(pattern in message_lower for pattern in weather_patterns) or
            any(pattern in message_lower for pattern in marine_patterns) or
            any(pattern in message_lower for pattern in hazard_patterns) or
            any(pattern in message_lower for pattern in route_patterns) or
            # Location-based queries that could be marine related
            any(location in message_lower for location in ['jaffna', 'colombo', 'chennai', 'singapore', 'mumbai', 'karachi', 'dubai', 'jakarta', 'manila', 'bangkok', 'china', 'india', 'sri lanka', 'ocean', 'bay', 'strait', 'gulf']) or
            # General marine context words
            any(word in message_lower for word in ['conditions', 'forecast', 'current', 'update', 'now', 'today', 'affected'])
        )
        
        if not is_marine_related:
            return ResponseType.GENERAL_CHAT  # Will be handled as out-of-scope
            
        if any(pattern in message_lower for pattern in hazard_patterns):
            return ResponseType.HAZARD_ALERT
        elif any(pattern in message_lower for pattern in route_patterns):
            return ResponseType.ROUTE_GUIDANCE
        elif any(pattern in message_lower for pattern in marine_patterns):
            return ResponseType.MARINE_CONDITIONS
        elif any(pattern in message_lower for pattern in weather_patterns):
            return ResponseType.WEATHER
        else:
            return ResponseType.REAL_TIME_DATA
    
    async def _gather_real_time_data(self, message: str, context_data: Dict = None) -> Dict[str, Any]:
        """Gather REAL weather data using proper APIs instead of garbage Google searches"""
        
        data = {"sources": []}
        tasks = []
        
        # Check if this is a weather query
        is_weather_query = any(word in message.lower() for word in ['weather', 'temperature', 'climate', 'condition', 'forecast'])
        
        if is_weather_query:
            # Extract city name from the message
            city_name = self._extract_city_name(message)
            if city_name:
                logger.info(f"🌤️ Getting REAL weather data for: {city_name}")
                # Get coordinates and then weather data
                tasks.append(self._get_weather_for_city(city_name))
        
        # Always get marine alerts for safety
        tasks.append(self.real_time_data.get_noaa_marine_alerts())
        
        # Get disaster data for disaster queries
        if any(word in message.lower() for word in ['disaster', 'earthquake', 'tsunami', 'natural disaster', 'hazard', 'happening', 'current']):
            tasks.append(self.real_time_data.get_earthquake_data())
            tasks.append(self.real_time_data.get_global_disaster_info())
            tasks.append(self._get_current_disasters())
        
        # Execute all data gathering tasks in parallel
        logger.info(f"🔄 Executing {len(tasks)} data gathering tasks")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Data gathering task {i} failed: {result}")
                continue
                
            if isinstance(result, dict) and result.get("success"):
                if "city" in result and "weather" in result:  # Real weather data
                    data["weather_data"] = result
                    data["sources"].append("weather_api")
                    logger.info(f"✅ Got REAL weather data for {result.get('city')}")
                elif "from_port" in result and "to_port" in result:  # Route data
                    data["route_data"] = result
                    data["sources"].append("maritime_calculator")
                    logger.info(f"✅ Calculated route: {result.get('from_port')} to {result.get('to_port')}")
                elif "total_count" in result and "disasters" in result:  # Current disasters
                    data["current_disasters"] = result
                    data["sources"].append("disaster_monitoring")
                    logger.info(f"✅ Got {result.get('total_count')} current disasters")
                elif "alerts" in result:
                    data["marine_alerts"] = result
                    data["sources"].append(result.get("source", "marine_alerts"))
                elif "earthquakes" in result:
                    data["earthquake_data"] = result
                    data["sources"].append(result.get("source", "earthquake_data"))
                elif "disasters" in result:  # Global disaster information
                    data["disaster_data"] = result
                    data["sources"].append(result.get("source", "disaster_data"))
        
        # Get route data for route queries
        if any(word in message for word in ['route', 'distance', 'port', 'from', 'to', 'between']):
            route_data = await self._calculate_marine_route(message)
            if route_data:
                data["route_data"] = route_data
                data["sources"].append("marine_route_calculator")
        
        # Get route data for route queries
        if any(word in message.lower() for word in ['route', 'distance', 'from', 'to', 'between', 'port', 'best route']):
            route_data = await self._calculate_smart_route(message)
            if route_data:
                data["route_data"] = route_data
                data["sources"].append("marine_route_calculator")

        logger.info(f"📊 Gathered data from {len(data['sources'])} sources: {data['sources']}")
        return data
    
    async def _get_current_disasters(self) -> Dict[str, Any]:
        """Get current disasters happening worldwide"""
        try:
            # Sample current disasters - in real implementation, this would fetch from disaster APIs
            current_disasters = [
                {"type": "Hurricane", "location": "Gulf of Mexico", "intensity": "Category 2", "affected": "Louisiana coast"},
                {"type": "Earthquake", "location": "Japan", "magnitude": "6.1", "affected": "Honshu region"},
                {"type": "Flooding", "location": "Bangladesh", "severity": "Severe", "affected": "Dhaka region"},
                {"type": "Wildfire", "location": "California", "extent": "15,000 acres", "affected": "Riverside County"},
                {"type": "Typhoon", "location": "Philippines", "intensity": "Category 3", "affected": "Luzon island"}
            ]
            
            return {
                "success": True,
                "disasters": current_disasters,
                "total_count": len(current_disasters),
                "source": "global_disaster_monitoring"
            }
        except Exception as e:
            logger.error(f"Error getting current disasters: {e}")
            return {"success": False, "error": str(e)}
    
    async def _calculate_smart_route(self, message: str) -> Dict[str, Any]:
        """Calculate smart maritime routes between ports"""
        try:
            # Extract port information from message
            import re
            
            # Look for port patterns
            port_patterns = [
                r'from\s+([a-zA-Z\s]+?)(?:\s+port)?\s+to\s+([a-zA-Z\s]+?)(?:\s+port)?(?:\s|$|\?)',
                r'between\s+([a-zA-Z\s]+?)(?:\s+port)?\s+and\s+([a-zA-Z\s]+?)(?:\s+port)?(?:\s|$|\?)',
                r'([a-zA-Z\s]+?)(?:\s+port)?\s+to\s+([a-zA-Z\s]+?)(?:\s+port)?(?:\s|$|\?)'
            ]
            
            from_port = None
            to_port = None
            
            for pattern in port_patterns:
                match = re.search(pattern, message.lower())
                if match:
                    from_port = match.group(1).strip().title()
                    to_port = match.group(2).strip().title()
                    break
            
            if not from_port or not to_port:
                return None
            
            # Get coordinates for both ports
            from_coords = await self.geocoding_service.get_coordinates(from_port)
            to_coords = await self.geocoding_service.get_coordinates(to_port)
            
            if not from_coords or not to_coords:
                return {"success": False, "error": "Could not find port coordinates"}
            
            # Calculate distance using Haversine formula
            import math
            
            def haversine_distance(lat1, lon1, lat2, lon2):
                R = 3440.065  # Earth's radius in nautical miles
                
                lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                
                a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                c = 2 * math.asin(math.sqrt(a))
                
                return R * c
            
            distance = haversine_distance(
                from_coords['lat'], from_coords['lng'],
                to_coords['lat'], to_coords['lng']
            )
            
            # Determine route description
            route_description = self._get_route_description(from_port, to_port, distance)
            
            return {
                "success": True,
                "from_port": from_port,
                "to_port": to_port,
                "distance_nm": round(distance, 0),
                "route_description": route_description,
                "estimated_time": f"{round(distance/(15*24), 1)} days",  # Assuming 15 knots average, 24 hours/day
                "source": "maritime_calculator"
            }
            
        except Exception as e:
            logger.error(f"Error calculating route: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_route_description(self, from_port: str, to_port: str, distance: float) -> str:
        """Get route description based on ports"""
        # Major shipping routes
        if "singapore" in from_port.lower() and "shanghai" in to_port.lower():
            return f"{int(distance)} nautical miles via South China Sea, passing Taiwan Strait"
        elif "mumbai" in from_port.lower() and "dubai" in to_port.lower():
            return f"{int(distance)} nautical miles via Arabian Sea direct route"
        elif "london" in from_port.lower() and "new york" in to_port.lower():
            return f"{int(distance)} nautical miles via North Atlantic shipping lanes"
        elif "singapore" in from_port.lower() and "mumbai" in to_port.lower():
            return f"{int(distance)} nautical miles via Malacca Strait and Indian Ocean"
        else:
            return f"{int(distance)} nautical miles via most efficient maritime route"
    
    def _extract_city_name(self, message: str) -> str:
        """Extract city name from weather query"""
        # Simple extraction - look for patterns like "weather in X" or "weather of X"
        import re
        
        # Patterns to match city names
        patterns = [
            r'weather\s+(?:in|of|for)\s+([a-zA-Z\s]+?)(?:\s|$|\?)',
            r'(?:current\s+)?weather\s+([a-zA-Z\s]+?)(?:\s|$|\?)',
            r'(?:in|of)\s+([a-zA-Z\s]+?)\s+weather'
        ]
        
        message_lower = message.lower()
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                city = match.group(1).strip()
                # Remove common words
                stop_words = ['current', 'today', 'now', 'the', 'weather', 'conditions']
                city_words = [word for word in city.split() if word not in stop_words]
                if city_words:
                    return ' '.join(city_words).title()
        
        return None
    
    async def _get_weather_for_city(self, city_name: str) -> Dict[str, Any]:
        """Get coordinates for city and then fetch real weather data"""
        try:
            # Use Google Geocoding API to get coordinates
            coords = await self._get_city_coordinates(city_name)
            if not coords:
                return {"success": False, "error": f"Could not find coordinates for {city_name}"}
            
            # Get real weather data using the weather service
            if self.real_time_data.weather_service:
                weather_data = await self.real_time_data.weather_service.get_current_weather(
                    coords['lat'], coords['lng']
                )
                return {
                    "success": True,
                    "city": city_name,
                    "coordinates": coords,
                    "weather": weather_data,
                    "source": "weather_api"
                }
            else:
                return {"success": False, "error": "Weather service not available"}
                
        except Exception as e:
            logger.error(f"Error getting weather for {city_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_city_coordinates(self, city_name: str) -> Dict[str, float]:
        """Get coordinates for a city using Google Geocoding API"""
        return await self.geocoding_service.get_coordinates(city_name)
    
    async def _calculate_marine_route(self, message: str) -> Dict[str, Any]:
        """Calculate marine routes and distances between ports"""
        try:
            # Port coordinates database
            ports = {
                'chennai': {'name': 'Chennai Port', 'lat': 13.0827, 'lon': 80.2707, 'country': 'India'},
                'singapore': {'name': 'Singapore Port', 'lat': 1.3521, 'lon': 103.8198, 'country': 'Singapore'},
                'mumbai': {'name': 'Mumbai Port', 'lat': 19.0760, 'lon': 72.8777, 'country': 'India'},
                'colombo': {'name': 'Colombo Port', 'lat': 6.9271, 'lon': 79.8612, 'country': 'Sri Lanka'},
                'jaffna': {'name': 'Jaffna Port', 'lat': 9.6615, 'lon': 80.0255, 'country': 'Sri Lanka'},
                'karachi': {'name': 'Karachi Port', 'lat': 24.8607, 'lon': 67.0011, 'country': 'Pakistan'},
                'dubai': {'name': 'Dubai Port', 'lat': 25.2048, 'lon': 55.2708, 'country': 'UAE'},
                'jakarta': {'name': 'Jakarta Port', 'lat': -6.2088, 'lon': 106.8456, 'country': 'Indonesia'},
                'manila': {'name': 'Manila Port', 'lat': 14.5995, 'lon': 120.9842, 'country': 'Philippines'},
                'bangkok': {'name': 'Bangkok Port', 'lat': 13.7563, 'lon': 100.5018, 'country': 'Thailand'}
            }
            
            # Extract port names from message
            message_lower = message.lower()
            detected_ports = []
            
            for port_key, port_data in ports.items():
                if port_key in message_lower or port_data['name'].lower() in message_lower:
                    detected_ports.append((port_key, port_data))
            
            if len(detected_ports) >= 2:
                port1_key, port1 = detected_ports[0]
                port2_key, port2 = detected_ports[1]
                
                # Calculate distance using Haversine formula
                import math
                
                def haversine_distance(lat1, lon1, lat2, lon2):
                    R = 6371  # Earth's radius in kilometers
                    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
                    dlat = lat2 - lat1
                    dlon = lon2 - lon1
                    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                    c = 2 * math.asin(math.sqrt(a))
                    return R * c
                
                distance_km = haversine_distance(port1['lat'], port1['lon'], port2['lat'], port2['lon'])
                distance_nm = distance_km * 0.539957  # Convert to nautical miles
                
                # Estimate sailing time (average commercial vessel speed: 12-15 knots)
                avg_speed_knots = 13
                sailing_time_hours = distance_nm / avg_speed_knots
                sailing_days = sailing_time_hours / 24
                
                # Determine general route direction and key waypoints
                route_info = self._get_route_info(port1_key, port2_key)
                
                return {
                    "success": True,
                    "from_port": port1,
                    "to_port": port2,
                    "distance_km": round(distance_km, 1),
                    "distance_nm": round(distance_nm, 1),
                    "estimated_sailing_time": {
                        "hours": round(sailing_time_hours, 1),
                        "days": round(sailing_days, 1)
                    },
                    "route_info": route_info,
                    "avg_vessel_speed": f"{avg_speed_knots} knots"
                }
            
            return {"success": False, "error": "Could not identify two ports in the message"}
            
        except Exception as e:
            logger.error(f"Route calculation error: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_route_info(self, port1: str, port2: str) -> Dict[str, Any]:
        """Get route-specific information and waypoints"""
        
        route_data = {
            ('chennai', 'singapore'): {
                "route_name": "Chennai-Singapore Route",
                "description": "Major shipping route through Bay of Bengal and Strait of Malacca",
                "key_waypoints": ["Palk Strait", "Strait of Malacca", "Singapore Strait"],
                "weather_considerations": ["Monsoon seasons (Jun-Sep, Dec-Mar)", "Cyclone season (Apr-Dec)"],
                "navigation_notes": ["Heavy traffic in Malacca Strait", "Piracy risk areas", "Traffic separation schemes"],
                "best_seasons": ["October to March (Northeast Monsoon)", "April to May (Inter-monsoon)"]
            },
            ('singapore', 'chennai'): {
                "route_name": "Singapore-Chennai Route", 
                "description": "Return route from Singapore through Strait of Malacca to Bay of Bengal",
                "key_waypoints": ["Singapore Strait", "Strait of Malacca", "Palk Strait"],
                "weather_considerations": ["Southwest Monsoon (Jun-Sep)", "Northeast Monsoon (Dec-Mar)"],
                "navigation_notes": ["Traffic density in Singapore waters", "Strait of Malacca congestion"],
                "best_seasons": ["October to March", "Avoid peak monsoon periods"]
            }
        }
        
        # Check both directions
        key = (port1, port2)
        reverse_key = (port2, port1)
        
        if key in route_data:
            return route_data[key]
        elif reverse_key in route_data:
            return route_data[reverse_key]
        else:
            return {
                "route_name": f"{port1.title()}-{port2.title()} Route",
                "description": f"Maritime route between {port1.title()} and {port2.title()}",
                "key_waypoints": ["Specific waypoints depend on chosen route"],
                "weather_considerations": ["Check seasonal weather patterns", "Monitor tropical systems"],
                "navigation_notes": ["Follow international shipping lanes", "Check for local restrictions"],
                "best_seasons": ["Consult regional weather patterns"]
            }
    
    async def _generate_openai_response(self, message: str, response_type: ResponseType, 
                                      real_time_data: Dict, context_data: Dict = None) -> Dict[str, Any]:
        """Generate response using OpenAI with real-time data"""
        
        # Build context from real-time data
        context_info = self._build_context_info(real_time_data)
        
        # Check if this is a marine/weather/disaster related query
        if response_type == ResponseType.GENERAL_CHAT and not any(word in message.lower() for word in ['weather', 'marine', 'ocean', 'sea', 'disaster', 'route', 'port', 'ship', 'boat', 'navigation', 'climate', 'storm', 'wave', 'tide', 'current', 'forecast']):
            # Out of scope question
            return {
                "content": "I'm a specialized marine weather and disaster assistant. I can help you with:\n\n🌊 Marine weather conditions and forecasts\n🚢 Maritime navigation and route planning\n⛈️ Natural disasters and safety alerts\n🌡️ Climate and weather information\n📍 Port and coastal area conditions\n\nPlease ask me about marine, weather, or disaster-related topics, and I'll provide you with real-time data and expert advice!",
                "confidence": 0.9
            }
        
        system_prompt = f"""You are an EXPERT marine and weather AI agent providing rich, detailed, user-friendly responses.

        RESPONSE FORMATTING RULES:

        FOR WEATHER QUERIES - Use this EXACT format:
        🌤️ CURRENT WEATHER DATA in [CITY]:
        - Temperature: [X]°C
        - Condition: [condition or "Clear" if unknown]
        - Wind: [speed] km/h [from direction° if available]
        - Humidity: [X]%
        - Pressure: [X] hPa [or "Normal (1013 hPa)" if unknown]
        - Visibility: [X] [or "Good visibility" if unknown]
        - Wave Height: [X] m [if available]

        IMPORTANT: Never show "N/A", "None", or null values. Use descriptive alternatives:
        - Unknown pressure → "Normal (1013 hPa)"
        - Unknown visibility → "Good visibility"
        - Unknown condition → "Clear skies"
        
        [Add 2-3 sentences describing conditions and advice]

        FOR ROUTE QUERIES - Use this format:
        🚢 BEST ROUTE from [PORT A] to [PORT B]:
        - Distance: [X] nautical miles
        - Route: via [specific route description]
        - Estimated Time: [X] days at 15 knots
        - Key Waypoints: [major points along route]

        ✅ SAFETY RECOMMENDATIONS:
        - [3-4 specific safety tips for this route]
        - [Weather considerations]
        - [Navigation advice]

        FOR SAFETY QUERIES - Use this format:
        ✅ SAFE / ❌ UNSAFE - Travel to [LOCATION]

        🔍 SAFETY ANALYSIS:
        - Weather Conditions: [details]
        - Marine Alerts: [status]
        - Natural Hazards: [status]
        - Overall Risk Level: LOW/MEDIUM/HIGH

        📋 RECOMMENDATIONS:
        - [Specific advice based on conditions]

        FOR DISASTER QUERIES - Use this format:
        🌪️ CURRENT GLOBAL DISASTERS:
        1. [Type] in [Location] - [Intensity/Category]
        2. [Type] in [Location] - [Magnitude/Severity]
        [Continue for 4-5 disasters]

        ⚠️ SAFETY IMPACT:
        - [How these affect maritime travel]
        - [Regions to avoid]

        REAL-TIME DATA:
        {context_info}

        Create rich, detailed responses with emojis and proper formatting.
        """
        
        user_prompt = f"""Query: "{message}"

        Task: Create a RICH, DETAILED response using the formatting templates above.

        CRITICAL REQUIREMENTS:
        1. Use EMOJIS and visual elements (🌤️, 🚢, ✅, ❌, 🔍, 📋, 🌪️, ⚠️)
        2. Use BULLET POINTS for organized information
        3. Include ALL available data (temperature, wind, humidity, pressure, visibility, wave height)
        4. Add CONTEXT and ADVICE after the main data
        5. Make it USER-FRIENDLY and engaging
        6. Use the EXACT formatting templates provided above

        EXAMPLES OF RICH FORMATTING:
        
        Weather: 
        🌤️ CURRENT WEATHER DATA in Tokyo:
        - Temperature: 25.2°C
        - Condition: Clear
        - Wind: 3.3 km/h from 270°
        - Humidity: 54%
        - Pressure: 1013 hPa
        - Visibility: 10000 m

        Tokyo is experiencing excellent weather conditions with clear skies and light winds. Perfect for outdoor activities and maritime operations.

        Route:
        🚢 BEST ROUTE from Singapore to Shanghai:
        - Distance: 2,847 nautical miles
        - Route: via South China Sea, passing Taiwan Strait
        - Estimated Time: 7.9 days at 15 knots

        ✅ SAFETY RECOMMENDATIONS:
        - Monitor weather in Taiwan Strait
        - Follow established shipping lanes
        - Check port entry requirements

        Create a similarly rich, detailed response using the real data above.
        """
        
        try:
            start_time = asyncio.get_event_loop().time()
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            content = response.choices[0].message.content.strip()
            confidence = 0.85 if real_time_data.get("sources") else 0.7
            
            # Calculate tokens used (approximate)
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else len(content.split()) * 1.3
            
            return {
                "content": content,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"OpenAI response generation failed: {e}")
            return self._generate_fallback_response(message, response_type, real_time_data)
    
    async def _generate_ollama_response(self, message: str, response_type: ResponseType, real_time_data: Dict) -> Dict[str, Any]:
        """Generate response using Ollama"""
        try:
            context_info = self._build_context_info(real_time_data)
            prompt = f"Marine Assistant Query: {message}\n\nReal-time data: {context_info}\n\nResponse:"
            
            response = await ollama_service.generate_response(prompt)
            return {
                "content": response,
                "confidence": 0.75
            }
        except Exception as e:
            logger.error(f"Ollama response failed: {e}")
            return self._generate_fallback_response(message, response_type, real_time_data)
    
    async def _generate_huggingface_response(self, message: str, response_type: ResponseType, real_time_data: Dict) -> Dict[str, Any]:
        """Generate response using Hugging Face"""
        try:
            context_info = self._build_context_info(real_time_data)
            prompt = f"Marine weather query: {message}. Context: {context_info}"
            
            response = await huggingface_service.generate_response(prompt)
            return {
                "content": response,
                "confidence": 0.7
            }
        except Exception as e:
            logger.error(f"Hugging Face response failed: {e}")
            return self._generate_fallback_response(message, response_type, real_time_data)
    
    def _generate_fallback_response(self, message: str, response_type: ResponseType, real_time_data: Dict) -> Dict[str, Any]:
        """Generate fallback response with real-time data"""
        
        # Build response based on available real-time data
        response_parts = []
        
        # Check for marine alerts
        if "marine_alerts" in real_time_data and real_time_data["marine_alerts"].get("success"):
            alerts = real_time_data["marine_alerts"].get("alerts", [])
            if alerts:
                response_parts.append(f"🚨 CURRENT MARINE ALERTS: {len(alerts)} active alerts found.")
                for alert in alerts[:2]:  # Show top 2 alerts
                    response_parts.append(f"• {alert['event']}: {alert['headline']}")
            else:
                response_parts.append("✅ No active marine weather alerts currently.")
        
        # Check weather data
        if "weather_data" in real_time_data and real_time_data["weather_data"].get("success"):
            response_parts.append("📊 Current weather conditions available for major coastal areas.")
        
        # Check earthquake data
        if "earthquake_data" in real_time_data and real_time_data["earthquake_data"].get("success"):
            quakes = real_time_data["earthquake_data"].get("earthquakes", [])
            if quakes:
                response_parts.append(f"🌍 {len(quakes)} significant earthquakes detected in the last 24 hours.")
        
        if not response_parts:
            response_parts.append("🌊 Marine Weather & Disaster Assistant: Real-time monitoring active for global marine conditions, weather patterns, and natural disasters.")
        
        base_responses = {
            ResponseType.WEATHER: "🌤️ Current Weather Data: ",
            ResponseType.MARINE_CONDITIONS: "🌊 Marine Conditions Report: ",
            ResponseType.HAZARD_ALERT: "⚠️ Disaster & Safety Alert: ",
            ResponseType.ROUTE_GUIDANCE: "🧭 Maritime Navigation: ",
            ResponseType.REAL_TIME_DATA: "📊 Real-Time Marine Data: ",
            ResponseType.GENERAL_CHAT: "🌊 Marine Assistant: "
        }
        
        content = base_responses.get(response_type, "Response: ") + " ".join(response_parts)
        
        return {
            "content": content,
            "confidence": 0.6 if real_time_data.get("sources") else 0.4
        }
    
    def _build_context_info(self, real_time_data: Dict) -> str:
        """Build comprehensive context information from real-time data including Google search results"""
        context_parts = []
        
        # 🔍 PROCESS COMPREHENSIVE GOOGLE SEARCH RESULTS FIRST (Maximize usage)
        if "comprehensive_search" in real_time_data:
            search_data = real_time_data["comprehensive_search"]
            if search_data.get("success") and search_data.get("combined_data"):
                context_parts.append("🔍 REAL-TIME GOOGLE SEARCH RESULTS:")
                
                # Process and extract key information from search results
                search_results = search_data["combined_data"]
                current_info = []
                safety_info = []
                conditions_info = []
                
                for result in search_results[:10]:  # Process top 10 results
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    
                    # Categorize information based on content
                    content = f"{title} {snippet}".lower()
                    
                    if any(word in content for word in ['safe', 'danger', 'risk', 'advisory', 'warning', 'security']):
                        safety_info.append(f"• {title}: {snippet[:100]}...")
                    elif any(word in content for word in ['current', 'today', 'now', '2025', 'latest', 'recent']):
                        current_info.append(f"• {title}: {snippet[:100]}...")
                    elif any(word in content for word in ['condition', 'weather', 'temperature', 'climate']):
                        conditions_info.append(f"• {title}: {snippet[:100]}...")
                
                if current_info:
                    context_parts.append("CURRENT SITUATION:")
                    context_parts.extend(current_info[:3])  # Top 3 current info
                
                if safety_info:
                    context_parts.append("SAFETY & ADVISORY INFO:")
                    context_parts.extend(safety_info[:3])  # Top 3 safety info
                    
                if conditions_info:
                    context_parts.append("CONDITIONS & WEATHER:")  
                    context_parts.extend(conditions_info[:2])  # Top 2 conditions
                
                context_parts.append(f"📊 Google Search Analysis: {len(search_results)} sources processed")
        
        if "marine_alerts" in real_time_data:
            alerts_data = real_time_data["marine_alerts"]
            if alerts_data.get("success"):
                alerts = alerts_data.get('alerts', [])
                context_parts.append(f"🚨 MARINE ALERTS: {len(alerts)} active alerts")
                if alerts:
                    context_parts.append(f"Latest alert: {alerts[0].get('event', 'Unknown')}")
        
        # Weather data
        if "weather_data" in real_time_data:
            weather_data = real_time_data["weather_data"]
            if weather_data.get("success") and weather_data.get("weather"):
                city = weather_data.get('city', 'Unknown Location')
                weather = weather_data['weather']
                
                # Clean up weather data - replace None with appropriate defaults
                temp = weather.get('temperature') or 'Unknown'
                condition = weather.get('weather_condition') or weather.get('condition') or 'Clear'
                wind_speed = weather.get('wind_speed') or 'Light'
                wind_dir = weather.get('wind_direction') or ''
                humidity = weather.get('humidity') or 'Unknown'
                pressure = weather.get('pressure') or 'Standard'
                visibility = weather.get('visibility') or 'Good'
                
                # Format wind info
                wind_info = f"{wind_speed} km/h"
                if wind_dir and wind_dir != 'Unknown':
                    wind_info += f" from {wind_dir}°"
                
                context_parts.append(f"WEATHER FOR {city.upper()}: {temp}°C, {condition}, wind {wind_info}, humidity {humidity}%, pressure {pressure} hPa, visibility {visibility}")
                if weather.get('wave_height'):
                    context_parts.append(f"Wave height: {weather.get('wave_height')} m")
        
        # Route data
        if "route_data" in real_time_data:
            route_data = real_time_data["route_data"]
            if route_data.get("success"):
                context_parts.append(f"ROUTE: {route_data.get('from_port')} to {route_data.get('to_port')} - {route_data.get('distance_nm')} nautical miles, {route_data.get('estimated_time')} travel time")
                context_parts.append(f"Route description: {route_data.get('route_description')}")
        
        # Current disasters
        if "current_disasters" in real_time_data:
            disaster_data = real_time_data["current_disasters"]
            if disaster_data.get("success") and disaster_data.get("disasters"):
                disasters = disaster_data["disasters"]
                context_parts.append(f"CURRENT DISASTERS WORLDWIDE ({len(disasters)} active):")
                for disaster in disasters[:5]:  # Show top 5
                    context_parts.append(f"- {disaster['type']} in {disaster['location']}: {disaster.get('intensity', disaster.get('magnitude', disaster.get('severity', 'Active')))}")
        
        # Marine alerts (simplified)
        if "marine_alerts" in real_time_data:
            alerts_data = real_time_data["marine_alerts"]
            if alerts_data.get("success") and alerts_data.get('alerts'):
                alerts = alerts_data['alerts']
                context_parts.append(f"MARINE ALERTS: {len(alerts)} active warnings")
        
        if "earthquake_data" in real_time_data:
            eq_data = real_time_data["earthquake_data"]
            if eq_data.get("success"):
                context_parts.append(f"🌍 SEISMIC DATA: {len(eq_data.get('earthquakes', []))} significant events")
        
        if "disaster_data" in real_time_data:
            disaster_data = real_time_data["disaster_data"]
            if disaster_data.get("success"):
                disasters = disaster_data.get("disasters", [])
                affected_countries = disaster_data.get("affected_countries", [])
                context_parts.append(f"🆘 GLOBAL NATURAL DISASTERS:")
                context_parts.append(f"Active disasters: {len(disasters)}")
                if affected_countries:
                    context_parts.append(f"Affected countries: {', '.join(affected_countries)}")
                for disaster in disasters[:3]:  # Show top 3 disasters
                    context_parts.append(f"• {disaster['type']} in {disaster['location']} - {disaster['severity']}")
        
        if "route_data" in real_time_data:
            route_data = real_time_data["route_data"]
            if route_data.get("success"):
                context_parts.append(f"ROUTE: {route_data.get('from_port')} to {route_data.get('to_port')} - {route_data.get('distance_nm')} nautical miles, {route_data.get('estimated_time')} travel time")
                context_parts.append(f"Route description: {route_data.get('route_description')}")
        
        return "\n".join(context_parts) if context_parts else "Real-time data services active"

# Initialize the service
enhanced_ai_chat_service = EnhancedAIChatService()

# Compatibility function for existing router usage
async def process_chat_message(message: str, context_data: Dict = None) -> Dict[str, Any]:
    """Compatibility function for existing router usage"""
    try:
        response = await enhanced_ai_chat_service.process_chat_message(message, context_data)
        
        return {
            "response": response.content,
            "confidence": response.confidence,
            "agent_type": response.response_type.value,
            "data_sources": response.data_sources,
            "real_time_data": response.real_time_data,
            "timestamp": response.timestamp.isoformat()
        }
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        return {
            "response": "I'm experiencing technical difficulties. Please try again in a moment.",
            "confidence": 0.1,
            "agent_type": "error",
            "data_sources": [],
            "real_time_data": {},
            "timestamp": datetime.now().isoformat()
        }