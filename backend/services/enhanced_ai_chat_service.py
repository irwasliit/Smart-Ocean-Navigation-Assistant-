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
                f"{query} current news today 2025",
                f"{query} latest updates current situation",
                f"{query} recent developments news"
            ])
        
        if "safety_info" in search_types:
            search_queries.extend([
                f"{query} safety travel advisory current",
                f"{query} security situation latest",
                f"{query} safe travel conditions now"
            ])
            
        if "real_time_conditions" in search_types:
            search_queries.extend([
                f"{query} current conditions today weather",
                f"{query} real time status updates",
                f"{query} live information current"
            ])

        # Execute multiple searches in parallel to maximize API usage
        search_tasks = []
        for search_query in search_queries[:6]:  # Limit to 6 searches to avoid rate limits
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
        self.google_search = GoogleSearchService()
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
        """Gather comprehensive real-time data from multiple sources with maximum Google API usage"""
        
        data = {"sources": []}
        tasks = []
        
        # 🔍 MAXIMIZE GOOGLE SEARCH API USAGE - Always search for current information
        search_types = []
        
        # Determine search types based on message content
        if any(word in message.lower() for word in ['safe', 'safety', 'travel', 'go', 'visit', 'danger', 'risk']):
            search_types.extend(["current_events", "safety_info"])
        
        if any(word in message.lower() for word in ['weather', 'condition', 'climate', 'temperature', 'storm']):
            search_types.append("real_time_conditions")
        
        if any(word in message.lower() for word in ['news', 'update', 'current', 'latest', 'now', 'today']):
            search_types.extend(["current_events", "real_time_conditions"])
        
        # Default to comprehensive search if no specific type detected
        if not search_types:
            search_types = ["current_events", "safety_info", "real_time_conditions"]
        
        # 🚀 ALWAYS perform comprehensive Google searches to maximize API usage
        logger.info(f"🔍 Performing comprehensive Google search with types: {search_types}")
        tasks.append(self.google_search.search_comprehensive_data(message, search_types))
        
        # Always get marine alerts for safety
        tasks.append(self.real_time_data.get_noaa_marine_alerts())
        
        # Get earthquake data for hazard queries
        if any(word in message for word in ['hazard', 'danger', 'earthquake', 'tsunami', 'disaster', 'natural disaster', 'affected', 'countries']):
            tasks.append(self.real_time_data.get_earthquake_data())
            # Also get enhanced disaster information
            tasks.append(self.real_time_data.get_global_disaster_info())
        
        # Get weather data for weather/marine queries
        if any(word in message for word in ['weather', 'marine', 'wind', 'wave', 'storm']):
            location = context_data.get('location') if context_data else None
            lat = location.get('latitude') if location else None
            lon = location.get('longitude') if location else None
            tasks.append(self.real_time_data.get_weather_conditions(lat, lon))
        
        # Execute all data gathering tasks in parallel
        logger.info(f"🔄 Executing {len(tasks)} data gathering tasks in parallel")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Data gathering task {i} failed: {result}")
                continue
                
            if isinstance(result, dict) and result.get("success"):
                if "combined_data" in result:  # Comprehensive Google search results
                    data["comprehensive_search"] = result
                    data["sources"].extend([f"google_search_{j+1}" for j in range(len(result.get("searches", {})))])
                    logger.info(f"✅ Google comprehensive search returned {len(result.get('combined_data', []))} results")
                elif "alerts" in result:
                    data["marine_alerts"] = result
                    data["sources"].append(result.get("source", "unknown"))
                elif "earthquakes" in result:
                    data["earthquake_data"] = result
                    data["sources"].append(result.get("source", "unknown"))
                elif "disasters" in result:  # Global disaster information
                    data["disaster_data"] = result
                    data["sources"].append(result.get("source", "unknown"))
                elif "weather" in result:
                    data["weather_data"] = result
                    data["sources"].append(result.get("source", "unknown"))
        
        # Get route data for route queries
        if any(word in message for word in ['route', 'distance', 'port', 'from', 'to', 'between']):
            route_data = await self._calculate_marine_route(message)
            if route_data:
                data["route_data"] = route_data
                data["sources"].append("marine_route_calculator")
        
        logger.info(f"📊 Gathered data from {len(data['sources'])} sources: {data['sources']}")
        return data
    
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
        
        system_prompt = f"""You are an INTELLIGENT assistant with access to COMPREHENSIVE REAL-TIME DATA from Google Search and multiple live sources.
        
        KEY CAPABILITIES:
        - Real-time Google search analysis with current information
        - Live data from multiple authoritative sources
        - Current events, safety, and conditions analysis
        - Comprehensive situational assessment
        
        PERSONALITY: Expert analyst providing data-driven insights. ALWAYS use REAL CURRENT DATA from searches.
        
        RESPONSE REQUIREMENTS:
        - Use SPECIFIC information from Google search results
        - Include EXACT data, numbers, dates, and current conditions
        - Reference CURRENT NEWS and recent developments
        - Provide FACTUAL analysis based on real-time sources
        - Give PRACTICAL, actionable advice based on current situation
        
        COMPREHENSIVE REAL-TIME DATA FROM MULTIPLE SOURCES:
        {context_info}
        
        CRITICAL INSTRUCTIONS:
        1. Analyze the Google search results for CURRENT information
        2. Use SPECIFIC details, numbers, and recent developments
        3. Reference ACTUAL news, conditions, and current events
        4. Provide EVIDENCE-BASED assessment from real data
        5. Never give generic responses - use the REAL information above
        
        ALWAYS base your response on the ACTUAL DATA provided above, especially the Google search results.
        """
        
        user_prompt = f"""User Query: "{message}"
        
        Response Type: {response_type.value}
        
        Task: Analyze the COMPREHENSIVE REAL-TIME DATA above (especially Google search results) to provide an accurate, current response.
        
        MANDATORY REQUIREMENTS:
        1. Use SPECIFIC information from the Google search results above
        2. Include EXACT data, dates, numbers, and current conditions found in searches
        3. Reference CURRENT NEWS, recent developments, and latest information
        4. Provide EVIDENCE-BASED analysis using the real search data
        5. Give PRACTICAL advice based on the actual current situation
        6. Quote or reference specific sources when relevant
        
        FOCUS ON: The Google search results contain the most current information - USE THEM EXTENSIVELY!
        
        Provide a comprehensive response using the ACTUAL REAL-TIME DATA above, not generic information.
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
        
        if "weather_data" in real_time_data:
            weather_data = real_time_data["weather_data"]
            if weather_data.get("success"):
                weather = weather_data.get('weather', {})
                if weather:
                    context_parts.append(f"🌤️ CURRENT WEATHER DATA:")
                    context_parts.append(f"Temperature: {weather.get('temperature', 'N/A')}°C")
                    context_parts.append(f"Condition: {weather.get('weather_condition', 'N/A')}")
                    context_parts.append(f"Wind: {weather.get('wind_speed', 'N/A')} km/h from {weather.get('wind_direction', 'N/A')}°")
                    context_parts.append(f"Humidity: {weather.get('humidity', 'N/A')}%")
                    context_parts.append(f"Pressure: {weather.get('pressure', 'N/A')} hPa")
                    context_parts.append(f"Visibility: {weather.get('visibility', 'N/A')} m")
                    if 'wave_height' in weather:
                        context_parts.append(f"Wave Height: {weather.get('wave_height', 'N/A')} m")
                    if 'hazard_probabilities' in weather:
                        hazards = weather['hazard_probabilities']
                        storm_risk = hazards.get('storm', 0) * 100
                        if storm_risk > 5:
                            context_parts.append(f"⚠️ Storm Risk: {storm_risk:.1f}%")
        
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
                context_parts.append(f"🚢 MARINE ROUTE INFORMATION:")
                context_parts.append(f"Route: {route_data['from_port']['name']} → {route_data['to_port']['name']}")
                context_parts.append(f"Distance: {route_data['distance_nm']} nautical miles ({route_data['distance_km']} km)")
                context_parts.append(f"Estimated sailing time: {route_data['estimated_sailing_time']['days']} days")
                context_parts.append(f"Key waypoints: {', '.join(route_data['route_info']['key_waypoints'])}")
                context_parts.append(f"Weather considerations: {', '.join(route_data['route_info']['weather_considerations'])}")
        
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