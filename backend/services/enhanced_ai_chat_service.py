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

# Import intelligent analyzer
try:
    from .intelligent_ai_analyzer import intelligent_analyzer
    INTELLIGENT_ANALYZER_AVAILABLE = True
    logger.info("✅ Intelligent AI Analyzer loaded successfully!")
except ImportError as e:
    INTELLIGENT_ANALYZER_AVAILABLE = False
    logger.warning(f"⚠️ Intelligent AI Analyzer not available: {e}")

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
    SAFETY_ASSESSMENT = "safety_assessment"
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

class MaritimeRouteDatabase:
    """Comprehensive hardcoded maritime route database with detailed specifications"""
    
    def __init__(self):
        # Major port coordinates
        self.ports = {
            'chennai': {'lat': 13.0827, 'lng': 80.2707, 'country': 'India', 'name': 'Chennai Port'},
            'mumbai': {'lat': 19.0760, 'lng': 72.8777, 'country': 'India', 'name': 'Mumbai Port'},
            'colombo': {'lat': 6.9271, 'lng': 79.8612, 'country': 'Sri Lanka', 'name': 'Colombo Port'},
            'singapore': {'lat': 1.3521, 'lng': 103.8198, 'country': 'Singapore', 'name': 'Singapore Port'},
            'shanghai': {'lat': 31.2304, 'lng': 121.4737, 'country': 'China', 'name': 'Shanghai Port'},
            'dubai': {'lat': 25.2048, 'lng': 55.2708, 'country': 'UAE', 'name': 'Dubai Port'},
            'karachi': {'lat': 24.8607, 'lng': 67.0011, 'country': 'Pakistan', 'name': 'Karachi Port'},
            'hong kong': {'lat': 22.3193, 'lng': 114.1694, 'country': 'China', 'name': 'Hong Kong Port'},
            'kochi': {'lat': 9.9312, 'lng': 76.2673, 'country': 'India', 'name': 'Kochi Port'},
            'vizag': {'lat': 17.6868, 'lng': 83.2185, 'country': 'India', 'name': 'Visakhapatnam Port'},
        }
        
        # Comprehensive route specifications with mock data
        self.routes = {
            ('shanghai', 'mumbai'): {
                'distance_nm': 3300,
                'distance_km': 6112,
                'estimated_days': 11,
                'average_speed_knots': 12,
                'route_description': 'Through the East China Sea, entering the South China Sea, passing the Malacca Strait, and navigating the Indian Ocean towards Mumbai',
                'major_waypoints': ['Shanghai Port', 'Malacca Strait entrance', 'Mumbai Port'],
                'key_straits': 'Malacca Strait - crucial passage point with heavy traffic',
                'distance_breakdown': {
                    'Shanghai to Malacca Strait': '1,700 nm',
                    'Malacca Strait to Mumbai': '1,600 nm'
                },
                'fuel_consumption_tons': 300,
                'daily_fuel_tons': 27,
                'fuel_cost_note': 'Cost varies based on fuel prices',
                'bunkering_strategy': 'Plan for refueling options at strategic ports along the route',
                'speed_factors': 'Consider weather conditions, currents, and traffic congestion in the Malacca Strait',
                'seasonal_patterns': 'Monsoons can impact the Indian Ocean route, affecting visibility and sea conditions',
                'optimal_seasons': 'Best times to transit are during the dry seasons to avoid harsh weather',
                'navigation_hazards': 'Watch for heavy traffic and potential piracy in the Malacca Strait',
                'traffic_density': 'Expect moderate to high vessel traffic in the Malacca Strait and near Mumbai',
                'primary_hazards': 'Weather disturbances, piracy risks, and congested shipping lanes',
                'alternative_routes': 'Consider alternative paths to avoid the Malacca Strait if necessary',
                'weather_routing': 'Monitor monsoon patterns and seek weather updates for safe navigation',
                'confidence': 0.85
            },
            ('mumbai', 'colombo'): {
                'distance_nm': 710,
                'distance_km': 1315,
                'estimated_days': 2.5,
                'average_speed_knots': 12,
                'route_description': 'Direct route across the Arabian Sea, passing along the western coast of India and approaching Sri Lanka from the northwest',
                'major_waypoints': ['Mumbai Port', 'Maldives vicinity', 'Colombo Port'],
                'key_straits': 'Open sea route, no major straits',
                'distance_breakdown': {
                    'Mumbai to Mid-Arabian Sea': '350 nm',
                    'Mid-Arabian Sea to Colombo': '360 nm'
                },
                'fuel_consumption_tons': 65,
                'daily_fuel_tons': 26,
                'fuel_cost_note': 'Cost varies based on fuel prices',
                'bunkering_strategy': 'Both ports have excellent bunkering facilities',
                'speed_factors': 'Favorable conditions most of the year, watch for monsoon season',
                'seasonal_patterns': 'Southwest monsoon (June-September) can bring rough seas',
                'optimal_seasons': 'October to May for calmer seas',
                'navigation_hazards': 'Limited hazards, standard maritime traffic',
                'traffic_density': 'Moderate traffic, busier near ports',
                'primary_hazards': 'Monsoon weather conditions, occasional cyclones',
                'alternative_routes': 'Coastal route available but longer',
                'weather_routing': 'Monitor Arabian Sea weather patterns and monsoon forecasts',
                'confidence': 0.90
            },
            ('chennai', 'colombo'): {
                'distance_nm': 405,
                'distance_km': 750,
                'estimated_days': 1.5,
                'average_speed_knots': 12,
                'route_description': 'Short route across the Bay of Bengal connecting India\'s east coast to Sri Lanka, passing through Palk Strait region',
                'major_waypoints': ['Chennai Port', 'Palk Strait', 'Colombo Port'],
                'key_straits': 'Palk Strait - shallow waters, requires careful navigation',
                'distance_breakdown': {
                    'Chennai to Palk Strait': '200 nm',
                    'Palk Strait to Colombo': '205 nm'
                },
                'fuel_consumption_tons': 35,
                'daily_fuel_tons': 23,
                'fuel_cost_note': 'Cost varies based on fuel prices',
                'bunkering_strategy': 'Both Chennai and Colombo offer bunkering services',
                'speed_factors': 'Relatively calm waters, speed may reduce in Palk Strait shallow areas',
                'seasonal_patterns': 'Northeast monsoon (October-December) affects Bay of Bengal',
                'optimal_seasons': 'January to May for best conditions',
                'navigation_hazards': 'Shallow waters in Palk Strait, fishing vessel traffic',
                'traffic_density': 'Moderate to high, especially near Chennai',
                'primary_hazards': 'Shallow waters, fishing vessels, monsoon weather',
                'alternative_routes': 'Deep water route south of Sri Lanka (longer)',
                'weather_routing': 'Monitor Bay of Bengal cyclone forecasts during monsoon',
                'confidence': 0.88
            },
            ('singapore', 'shanghai'): {
                'distance_nm': 1560,
                'distance_km': 2889,
                'estimated_days': 5.5,
                'average_speed_knots': 12,
                'route_description': 'Major shipping lane through South China Sea, one of the world\'s busiest maritime corridors',
                'major_waypoints': ['Singapore Port', 'South China Sea central', 'Taiwan Strait approach', 'Shanghai Port'],
                'key_straits': 'Taiwan Strait (optional) or direct route east of Taiwan',
                'distance_breakdown': {
                    'Singapore to South China Sea': '780 nm',
                    'South China Sea to Shanghai': '780 nm'
                },
                'fuel_consumption_tons': 125,
                'daily_fuel_tons': 23,
                'fuel_cost_note': 'Cost varies based on fuel prices',
                'bunkering_strategy': 'Excellent facilities at both ports',
                'speed_factors': 'Heavy traffic in South China Sea, currents affect speed',
                'seasonal_patterns': 'Typhoon season (May-November) can severely impact route',
                'optimal_seasons': 'December to April for typhoon avoidance',
                'navigation_hazards': 'Typhoons, heavy traffic, disputed waters',
                'traffic_density': 'Very high - one of world\'s busiest shipping lanes',
                'primary_hazards': 'Tropical cyclones, congested shipping lanes, geopolitical tensions',
                'alternative_routes': 'Route east of Philippines (longer but avoids South China Sea)',
                'weather_routing': 'Essential typhoon tracking and route adjustment capability',
                'confidence': 0.82
            },
            ('chennai', 'singapore'): {
                'distance_nm': 1485,
                'distance_km': 2750,
                'estimated_days': 5,
                'average_speed_knots': 12,
                'route_description': 'Route across Bay of Bengal, through Andaman Sea, and into Malacca Strait approaching Singapore',
                'major_waypoints': ['Chennai Port', 'Andaman Islands', 'Malacca Strait northern entrance', 'Singapore Port'],
                'key_straits': 'Malacca Strait - world\'s busiest strait, critical chokepoint',
                'distance_breakdown': {
                    'Chennai to Andaman Sea': '740 nm',
                    'Andaman Sea to Singapore': '745 nm'
                },
                'fuel_consumption_tons': 115,
                'daily_fuel_tons': 23,
                'fuel_cost_note': 'Cost varies based on fuel prices',
                'bunkering_strategy': 'Singapore has world-class bunkering facilities',
                'speed_factors': 'Malacca Strait traffic and currents affect timing',
                'seasonal_patterns': 'Southwest monsoon affects Bay of Bengal, Malacca Strait year-round traffic',
                'optimal_seasons': 'November to April for better weather',
                'navigation_hazards': 'Piracy risk near Malacca Strait, heavy traffic, shallow areas',
                'traffic_density': 'High throughout route, extremely high in Malacca Strait',
                'primary_hazards': 'Piracy, traffic congestion, monsoon weather, shallow waters',
                'alternative_routes': 'Route south via Sunda Strait (much longer)',
                'weather_routing': 'Monitor monsoons and Malacca Strait traffic advisories',
                'confidence': 0.86
            },
            ('mumbai', 'singapore'): {
                'distance_nm': 2380,
                'distance_km': 4407,
                'estimated_days': 8,
                'average_speed_knots': 12,
                'route_description': 'Route across Arabian Sea, around southern India/Sri Lanka, through Bay of Bengal and Malacca Strait',
                'major_waypoints': ['Mumbai Port', 'Lakshadweep Sea', 'Southern tip of India', 'Malacca Strait', 'Singapore Port'],
                'key_straits': 'Malacca Strait approach from west',
                'distance_breakdown': {
                    'Mumbai to Southern India': '1,190 nm',
                    'Southern India to Singapore': '1,190 nm'
                },
                'fuel_consumption_tons': 195,
                'daily_fuel_tons': 24,
                'fuel_cost_note': 'Cost varies based on fuel prices',
                'bunkering_strategy': 'Consider refueling at Colombo or proceed direct to Singapore',
                'speed_factors': 'Multiple sea regions with varying current patterns',
                'seasonal_patterns': 'Both monsoons affect different portions of route',
                'optimal_seasons': 'October to March for most favorable conditions',
                'navigation_hazards': 'Monsoon weather, Malacca Strait piracy risk, heavy traffic',
                'traffic_density': 'Moderate to high, extremely high near Singapore',
                'primary_hazards': 'Weather variability, piracy risk, traffic congestion',
                'alternative_routes': 'Can route via Colombo for bunkering',
                'weather_routing': 'Complex route requiring continuous weather monitoring',
                'confidence': 0.84
            },
            ('shanghai', 'colombo'): {
                'distance_nm': 3050,
                'distance_km': 5648,
                'estimated_days': 10.5,
                'average_speed_knots': 12,
                'route_description': 'Long route from East China Sea through South China Sea, Malacca Strait, and across Bay of Bengal',
                'major_waypoints': ['Shanghai Port', 'South China Sea', 'Malacca Strait', 'Bay of Bengal', 'Colombo Port'],
                'key_straits': 'Malacca Strait - critical passage point',
                'distance_breakdown': {
                    'Shanghai to Malacca Strait': '1,830 nm',
                    'Malacca Strait to Colombo': '1,220 nm'
                },
                'fuel_consumption_tons': 255,
                'daily_fuel_tons': 24,
                'fuel_cost_note': 'Cost varies based on fuel prices',
                'bunkering_strategy': 'Consider refueling at Singapore or continue to Colombo',
                'speed_factors': 'Various currents and traffic zones affect speed throughout',
                'seasonal_patterns': 'Typhoons in North, monsoons in South - complex weather pattern',
                'optimal_seasons': 'December to March avoids both typhoon and strong monsoon',
                'navigation_hazards': 'Typhoons, monsoons, piracy in Malacca Strait, heavy traffic',
                'traffic_density': 'Very high throughout most of route',
                'primary_hazards': 'Tropical cyclones, monsoon weather, piracy, traffic congestion',
                'alternative_routes': 'Route via Singapore for shorter distance and better services',
                'weather_routing': 'Requires sophisticated weather routing for typhoon and monsoon avoidance',
                'confidence': 0.80
            },
            ('colombo', 'dubai'): {
                'distance_nm': 1685,
                'distance_km': 3120,
                'estimated_days': 6,
                'average_speed_knots': 12,
                'route_description': 'Route across Arabian Sea connecting South Asia to Middle East, major trade corridor',
                'major_waypoints': ['Colombo Port', 'Laccadive Sea', 'Arabian Sea central', 'Gulf of Oman', 'Dubai Port'],
                'key_straits': 'Strait of Hormuz approach - one of world\'s most strategic waterways',
                'distance_breakdown': {
                    'Colombo to Arabian Sea': '845 nm',
                    'Arabian Sea to Dubai': '840 nm'
                },
                'fuel_consumption_tons': 140,
                'daily_fuel_tons': 23,
                'fuel_cost_note': 'Cost varies based on fuel prices',
                'bunkering_strategy': 'Both ports offer excellent bunkering facilities',
                'speed_factors': 'Favorable conditions most times, Gulf approach can be congested',
                'seasonal_patterns': 'Southwest monsoon (June-September) affects Arabian Sea',
                'optimal_seasons': 'October to May for calmer seas',
                'navigation_hazards': 'Geopolitical tensions near Gulf, piracy risk in Arabian Sea',
                'traffic_density': 'High - major oil and container shipping route',
                'primary_hazards': 'Geopolitical tensions, piracy, monsoon weather, traffic congestion',
                'alternative_routes': 'No practical alternatives for this route',
                'weather_routing': 'Monitor Arabian Sea conditions and Gulf tensions',
                'confidence': 0.85
            },
            ('singapore', 'hong kong'): {
                'distance_nm': 1440,
                'distance_km': 2667,
                'estimated_days': 5,
                'average_speed_knots': 12,
                'route_description': 'Major regional route through South China Sea connecting two busiest Asian ports',
                'major_waypoints': ['Singapore Port', 'South China Sea', 'Hong Kong Port'],
                'key_straits': 'Through South China Sea shipping lanes',
                'distance_breakdown': {
                    'Singapore to Mid-South China Sea': '720 nm',
                    'Mid-South China Sea to Hong Kong': '720 nm'
                },
                'fuel_consumption_tons': 115,
                'daily_fuel_tons': 23,
                'fuel_cost_note': 'Cost varies based on fuel prices',
                'bunkering_strategy': 'Both ports have world-class facilities',
                'speed_factors': 'Very heavy traffic requires speed adjustments',
                'seasonal_patterns': 'Typhoon season (May-November) poses significant risks',
                'optimal_seasons': 'December to April for typhoon avoidance',
                'navigation_hazards': 'Typhoons, extremely heavy traffic, territorial disputes',
                'traffic_density': 'Extremely high - two of world\'s busiest ports',
                'primary_hazards': 'Tropical cyclones, congested shipping lanes, geopolitical tensions',
                'alternative_routes': 'Limited alternatives in this congested region',
                'weather_routing': 'Critical typhoon tracking and avoidance required',
                'confidence': 0.87
            },
            ('mumbai', 'karachi'): {
                'distance_nm': 490,
                'distance_km': 907,
                'estimated_days': 1.7,
                'average_speed_knots': 12,
                'route_description': 'Short coastal route along northwestern Indian Ocean coast',
                'major_waypoints': ['Mumbai Port', 'Gujarat Coast', 'Karachi Port'],
                'key_straits': 'Coastal navigation, no major straits',
                'distance_breakdown': {
                    'Mumbai to Gujarat Coast': '245 nm',
                    'Gujarat Coast to Karachi': '245 nm'
                },
                'fuel_consumption_tons': 40,
                'daily_fuel_tons': 24,
                'fuel_cost_note': 'Cost varies based on fuel prices',
                'bunkering_strategy': 'Both ports offer bunkering services',
                'speed_factors': 'Relatively straightforward coastal route',
                'seasonal_patterns': 'Southwest monsoon affects route June-September',
                'optimal_seasons': 'October to May for better conditions',
                'navigation_hazards': 'Coastal fishing vessels, monsoon weather',
                'traffic_density': 'Moderate coastal traffic',
                'primary_hazards': 'Monsoon weather, geopolitical considerations',
                'alternative_routes': 'Offshore route further from coast available',
                'weather_routing': 'Monitor monsoon patterns',
                'confidence': 0.88
            }
        }
    
    def normalize_port_name(self, port_name: str) -> str:
        """Normalize port names for lookup"""
        if not port_name:
            return ''
        normalized = port_name.lower().strip()
        # Remove common suffixes
        for suffix in [' port', ' harbor', ' harbour', ' seaport']:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
        return normalized
    
    def find_route(self, from_port: str, to_port: str) -> Optional[Dict]:
        """Find route between two ports"""
        from_normalized = self.normalize_port_name(from_port)
        to_normalized = self.normalize_port_name(to_port)
        
        # Try direct match
        route_key = (from_normalized, to_normalized)
        if route_key in self.routes:
            route_data = self.routes[route_key].copy()
            route_data['from_port'] = self.ports.get(from_normalized, {}).get('name', from_port)
            route_data['to_port'] = self.ports.get(to_normalized, {}).get('name', to_port)
            route_data['from_coords'] = self.ports.get(from_normalized, {})
            route_data['to_coords'] = self.ports.get(to_normalized, {})
            return route_data
        
        # Try reverse
        reverse_key = (to_normalized, from_normalized)
        if reverse_key in self.routes:
            route_data = self.routes[reverse_key].copy()
            # Swap from/to for reverse
            route_data['from_port'] = self.ports.get(from_normalized, {}).get('name', from_port)
            route_data['to_port'] = self.ports.get(to_normalized, {}).get('name', to_port)
            route_data['from_coords'] = self.ports.get(from_normalized, {})
            route_data['to_coords'] = self.ports.get(to_normalized, {})
            return route_data
        
        # Try partial matches
        for port_key in self.ports.keys():
            if from_normalized in port_key or port_key in from_normalized:
                from_normalized = port_key
                break
        
        for port_key in self.ports.keys():
            if to_normalized in port_key or port_key in to_normalized:
                to_normalized = port_key
                break
        
        # Try again with partial matches
        route_key = (from_normalized, to_normalized)
        if route_key in self.routes:
            route_data = self.routes[route_key].copy()
            route_data['from_port'] = self.ports.get(from_normalized, {}).get('name', from_port)
            route_data['to_port'] = self.ports.get(to_normalized, {}).get('name', to_port)
            route_data['from_coords'] = self.ports.get(from_normalized, {})
            route_data['to_coords'] = self.ports.get(to_normalized, {})
            return route_data
        
        reverse_key = (to_normalized, from_normalized)
        if reverse_key in self.routes:
            route_data = self.routes[reverse_key].copy()
            route_data['from_port'] = self.ports.get(from_normalized, {}).get('name', from_port)
            route_data['to_port'] = self.ports.get(to_normalized, {}).get('name', to_port)
            route_data['from_coords'] = self.ports.get(from_normalized, {})
            route_data['to_coords'] = self.ports.get(to_normalized, {})
            return route_data
        
        return None
    
    def get_all_ports(self) -> List[str]:
        """Get list of all available ports"""
        return [port_info['name'] for port_info in self.ports.values()]

class GoogleSearchService:
    """Google Custom Search service with dual API key fallback and rate limiting"""
    
    def __init__(self):
        # Your two Google Custom Search API keys
        self.api_keys = [
            "AIzaSyA3QPrtjRR-1CwQTOTaSaq5xLepLA_0z3k",
            "AIzaSyDYmkSBnM8t88ZdjtAZP8kXqV6aMuNdV3w"
        ]
        self.current_key_index = 0
        
        # Rate limiting - track API usage
        self.search_count = 0
        self.daily_search_limit = 80  # Conservative limit per day
        self.last_reset = datetime.now().date()
        self.consecutive_429_errors = 0
        self.rate_limit_backoff = 0  # Seconds to wait
        
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
            
    def _check_rate_limits(self) -> bool:
        """Check if we can make search requests"""
        current_date = datetime.now().date()
        
        # Reset daily counter if it's a new day
        if current_date > self.last_reset:
            self.search_count = 0
            self.last_reset = current_date
            self.consecutive_429_errors = 0
            self.rate_limit_backoff = 0
            
        # Check daily limit
        if self.search_count >= self.daily_search_limit:
            logger.warning(f"📊 Google Search daily limit reached ({self.daily_search_limit})")
            return False
            
        # Check backoff period
        if self.rate_limit_backoff > 0:
            logger.warning(f"⏳ Rate limit backoff active for {self.rate_limit_backoff} seconds")
            return False
            
        return True
        
    def _handle_rate_limit_error(self):
        """Handle 429 rate limit errors with exponential backoff"""
        self.consecutive_429_errors += 1
        
        # Exponential backoff: 30s, 60s, 120s, 300s
        backoff_times = [30, 60, 120, 300]
        backoff_index = min(self.consecutive_429_errors - 1, len(backoff_times) - 1)
        self.rate_limit_backoff = backoff_times[backoff_index]
        
        logger.warning(f"🔄 Rate limit hit! Backing off for {self.rate_limit_backoff}s (attempt {self.consecutive_429_errors})")
        
    def _reset_rate_limit_success(self):
        """Reset rate limit counters on successful request"""
        if self.consecutive_429_errors > 0:
            logger.info("✅ Rate limit recovered!")
            self.consecutive_429_errors = 0
            self.rate_limit_backoff = 0
        
    async def search_comprehensive_data(self, query: str, search_types: List[str] = None) -> Dict[str, Any]:
        """MAXIMIZED comprehensive search using multiple targeted queries across different domains"""
        
        if not search_types:
            search_types = ["current_events", "safety_info", "real_time_conditions"]
        
        all_results = {"success": True, "searches": {}, "combined_data": [], "search_categories": {}}
        
        # 🎯 MAXIMIZED SEARCH STRATEGY - Generate highly targeted search queries
        search_queries = []
        
        # Extract location/subject from query for better targeting
        query_lower = query.lower()
        
        # Weather-specific searches
        if "weather_conditions" in search_types:
            search_queries.extend([
                f"{query} weather forecast today 2025",
                f"{query} current weather conditions marine",
                f"{query} meteorological report latest"
            ])
        
        # Disaster and emergency searches
        if "disaster_updates" in search_types:
            search_queries.extend([
                f"{query} disaster alert current emergency 2025",
                f"{query} natural disaster happening now",
                f"{query} emergency situation latest update"
            ])
        
        # Safety and travel advisory searches
        if "safety_info" in search_types:
            search_queries.extend([
                f"{query} travel advisory safety alert 2025",
                f"{query} security situation current",
                f"{query} safe to travel latest advisory"
            ])
        
        # Maritime and shipping searches
        if "maritime_conditions" in search_types:
            search_queries.extend([
                f"{query} maritime conditions shipping alert",
                f"{query} port status vessel traffic",
                f"{query} marine navigation hazard"
            ])
        
        # Current events and news searches
        if "current_events" in search_types:
            search_queries.extend([
                f"{query} latest news today 2025",
                f"{query} current situation update",
                f"{query} breaking news recent"
            ])
        
        # Port and infrastructure searches
        if "port_status" in search_types:
            search_queries.extend([
                f"{query} port operations status current",
                f"{query} harbor conditions today"
            ])
        
        # Impact assessment searches
        if "impact_assessment" in search_types:
            search_queries.extend([
                f"{query} impact assessment damage report",
                f"{query} affected areas casualties"
            ])
        
        # Navigation and routing searches
        if "navigation_hazards" in search_types:
            search_queries.extend([
                f"{query} navigation warning marine hazard",
                f"{query} shipping lane closure"
            ])
        
        # Real-time condition searches (fallback)
        if "real_time_conditions" in search_types:
            search_queries.extend([
                f"{query} real time conditions current",
                f"{query} live update status now"
            ])
        
        # Check rate limits before making searches
        if not self._check_rate_limits():
            logger.warning("🚫 Skipping Google Search due to rate limits")
            all_results["success"] = False
            all_results["error"] = "Google Search API rate limit exceeded. Relying on official data sources."
            all_results["fallback_message"] = "📡 Using official monitoring systems (USGS, NOAA, GDACS) for real-time data while search API recovers."
            return all_results
        
        # Execute strategic searches - REDUCED to 2 searches to conserve quota
        search_tasks = []
        unique_queries = list(set(search_queries))  # Remove duplicates
        
        # Prioritize most relevant searches based on query content
        prioritized_queries = self._prioritize_search_queries(unique_queries, query_lower)
        
        # REDUCED from 5 to 2 searches to prevent rate limiting
        max_searches = min(2, len(prioritized_queries))
        
        for search_query in prioritized_queries[:max_searches]:
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
            
            logger.info(f"✅ Executed {successful_searches}/{max_searches} Google searches successfully (quota: {self.search_count}/{self.daily_search_limit})")
            
            if successful_searches == 0:
                all_results["success"] = False
                all_results["error"] = "All search queries failed"
                
        except Exception as e:
            logger.error(f"❌ Comprehensive search failed: {e}")
            all_results["success"] = False
            all_results["error"] = str(e)
        
        return all_results
    
    async def _single_search(self, search_query: str) -> Dict[str, Any]:
        """Execute a single search query with API key rotation and rate limit handling"""
        
        # Check if we can make this search
        if not self._check_rate_limits():
            return {"success": False, "error": "Rate limit exceeded", "query": search_query}
        
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
                
                # Increment search count before making request
                self.search_count += 1
                
                start_time = asyncio.get_event_loop().time()
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
                    async with session.get(url, params=params) as response:
                        response_time = (asyncio.get_event_loop().time() - start_time) * 1000  # Convert to milliseconds
                        
                        if response.status == 200:
                            data = await response.json()
                            self._reset_rate_limit_success()
                            
                            return {
                                "success": True,
                                "data": data,
                                "source": f"google_api_{self.current_key_index + 1}",
                                "query": search_query
                            }
                        elif response.status == 429:
                            # Rate limit hit
                            self._handle_rate_limit_error()
                            logger.warning(f"❌ Search failed: {response.status} for query: {search_query[:50]}")
                            return {"success": False, "error": "Rate limited", "query": search_query}
                        else:
                            logger.warning(f"❌ Search failed: {response.status} for query: {search_query[:50]}")
                            
            except Exception as e:
                logger.error(f"❌ Single search error: {e}")
            
            # Rotate to next API key
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        
        return {"success": False, "error": "Search failed", "query": search_query}
    
    def _prioritize_search_queries(self, queries: List[str], original_query: str) -> List[str]:
        """Prioritize search queries based on original query content for maximum relevance"""
        prioritized = []
        medium_priority = []
        low_priority = []
        
        for query in queries:
            query_lower = query.lower()
            
            # High priority: Direct matches with original query terms
            if any(word in query_lower for word in original_query.split() if len(word) > 3):
                prioritized.append(query)
            # Medium priority: Contains relevant keywords
            elif any(word in query_lower for word in ['current', 'latest', 'today', '2025', 'alert', 'emergency']):
                medium_priority.append(query)
            # Low priority: General searches
            else:
                low_priority.append(query)
        
        return prioritized + medium_priority + low_priority
    
    async def search_specific_topic(self, topic: str, location: str = None, search_type: str = "general") -> Dict[str, Any]:
        """Search for specific topics with location context - Additional API usage maximization"""
        
        search_query = topic
        if location:
            search_query = f"{topic} {location}"
        
        # Add search type specific terms
        if search_type == "safety":
            search_query += " safety advisory alert"
        elif search_type == "weather":
            search_query += " weather conditions forecast"
        elif search_type == "disaster":
            search_query += " disaster emergency situation"
        elif search_type == "marine":
            search_query += " maritime marine shipping"
        elif search_type == "current":
            search_query += " current latest today 2025"
        
        return await self._single_search(search_query)
    
    async def search_multi_angle(self, base_query: str) -> Dict[str, Any]:
        """Multi-angle search approach for comprehensive coverage - Maximum API utilization"""
        
        all_results = {"success": True, "multi_angle_data": [], "search_angles": {}}
        
        # Define different search angles for the same topic
        search_angles = {
            "news_angle": f"{base_query} news latest breaking",
            "official_angle": f"{base_query} official report government",
            "safety_angle": f"{base_query} safety warning advisory",
            "real_time_angle": f"{base_query} real time live current",
            "impact_angle": f"{base_query} impact effect consequence"
        }
        
        search_tasks = []
        for angle_name, search_query in search_angles.items():
            search_tasks.append(self._single_search(search_query))
        
        try:
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            for i, (angle_name, result) in enumerate(zip(search_angles.keys(), results)):
                if isinstance(result, dict) and result.get("success"):
                    all_results["search_angles"][angle_name] = result
                    if "items" in result.get("data", {}):
                        all_results["multi_angle_data"].extend(result["data"]["items"][:2])  # Top 2 per angle
            
            if not all_results["multi_angle_data"]:
                all_results["success"] = False
                all_results["error"] = "No successful multi-angle searches"
                    
        except Exception as e:
            logger.error(f"Multi-angle search failed: {e}")
            all_results["success"] = False
            all_results["error"] = str(e)
        
        return all_results

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
        self.google_search = GoogleSearchService()  # 🔥 MAXIMIZE Google Search API usage
        self.route_database = MaritimeRouteDatabase()  # 🚢 Hardcoded route database
        
        logger.info("🔍 Google Search API service initialized for maximum usage")
        logger.info("🚢 Maritime Route Database initialized with comprehensive port data")
        
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
        real_time_data = await self._gather_real_time_data(message_lower, context_data, response_type)
        
        # If this is a disaster report request, build a detailed real-time report for AI chat
        if response_type == ResponseType.HAZARD_ALERT and "disaster_data" in real_time_data:
            disaster_data = real_time_data["disaster_data"]
            if disaster_data.get("success") and disaster_data.get("disasters"):
                # Build a detailed report with time info
                report_lines = ["🌪️ CURRENT GLOBAL DISASTERS:"]
                eqs = [d for d in disaster_data["disasters"] if d["type"] == "Earthquake"]
                storms = [d for d in disaster_data["disasters"] if d["type"] == "Tropical Storm System"]
                floods = [d for d in disaster_data["disasters"] if d["type"] == "Flood/Heavy Rain"]
                others = [d for d in disaster_data["disasters"] if d["type"] == "Tsunami" or d["type"] == "Other"]

                # Earthquakes
                report_lines.append("\n🌍 EARTHQUAKES:")
                if eqs:
                    for eq in eqs:
                        eq_time = eq.get('time_local') or eq.get('time_utc')
                        if eq_time and eq_time.lower() != 'unknown':
                            time_str = f"Occurred: {eq_time} (local time)"
                            report_lines.append(f"• M {eq.get('magnitude')} Earthquake - {eq.get('location')} ({eq.get('severity')})\n  {time_str}")
                        else:
                            report_lines.append(f"• M {eq.get('magnitude')} Earthquake - {eq.get('location')} ({eq.get('severity')})")
                else:
                    report_lines.append("• No significant earthquakes currently reported.")

                # Storms
                report_lines.append("\n🌊 STORMS & TYPHOONS:")
                if storms:
                    for s in storms:
                        s_time = s.get('time_local') or s.get('time_utc')
                        s_expires = s.get('expires_local') or s.get('expires_utc')
                        status = "Ongoing" if s_expires else "Status unknown"
                        if s_time and s_time.lower() != 'unknown':
                            if s_expires and s_expires.lower() != 'unknown':
                                period = f"From {s_time} to {s_expires}"
                            else:
                                period = f"Started: {s_time}"
                            report_lines.append(f"• {s.get('event', 'Storm')} - {s.get('location')} ({s.get('severity')})\n  {period} ({status})")
                        else:
                            report_lines.append(f"• {s.get('event', 'Storm')} - {s.get('location')} ({s.get('severity')})")
                else:
                    report_lines.append("• No active storm or typhoon alerts at the moment")

                # Floods
                report_lines.append("\n💧 FLOODS & WATER HAZARDS:")
                if floods:
                    for f in floods:
                        f_time = f.get('time_local') or f.get('time_utc')
                        f_expires = f.get('expires_local') or f.get('expires_utc')
                        status = "Ongoing" if f_expires else "Status unknown"
                        if f_time and f_time.lower() != 'unknown':
                            if f_expires and f_expires.lower() != 'unknown':
                                period = f"From {f_time} to {f_expires}"
                            else:
                                period = f"Started: {f_time}"
                            report_lines.append(f"• {f.get('event', 'Flood')} - {f.get('location')} ({f.get('severity')})\n  {period} ({status})")
                        else:
                            report_lines.append(f"• {f.get('event', 'Flood')} - {f.get('location')} ({f.get('severity')})")
                else:
                    report_lines.append("• No active flood or water hazard alerts currently reported")

                # Other disasters
                report_lines.append("\n🔥 OTHER NATURAL DISASTERS:")
                if others:
                    for o in others:
                        o_time = o.get('time_local') or o.get('time_utc')
                        o_expires = o.get('expires_local') or o.get('expires_utc')
                        status = "Ongoing" if o_expires else "Status unknown"
                        if o_time and o_time.lower() != 'unknown':
                            if o_expires and o_expires.lower() != 'unknown':
                                period = f"From {o_time} to {o_expires}"
                            else:
                                period = f"Started: {o_time}"
                            report_lines.append(f"• {o.get('event', o.get('type', 'Other'))} - {o.get('location')} ({o.get('severity')})\n  {period} ({status})")
                        else:
                            report_lines.append(f"• {o.get('event', o.get('type', 'Other'))} - {o.get('location')} ({o.get('severity')})")
                else:
                    report_lines.append("• No other natural disasters ongoing")

                # Data sources
                sources = disaster_data.get('source', 'Unknown')
                report_lines.append(f"\n📊 DATA SOURCES: {sources}")

                # Maritime impact
                report_lines.append("\n⚠️ MARITIME IMPACT BY DISASTER TYPE:")
                if eqs:
                    report_lines.append("🌍 Earthquake Zones:")
                    for eq in eqs:
                        report_lines.append(f"- {eq.get('impact', 'No significant impact reported')} ({eq.get('location')})")
                if storms:
                    report_lines.append("🌊 Storm Systems:")
                    for s in storms:
                        report_lines.append(f"- {s.get('impact', 'No storm-related maritime impacts')} ({s.get('location')})")
                if floods:
                    report_lines.append("💧 Flood Areas:")
                    for f in floods:
                        report_lines.append(f"- {f.get('impact', 'No flood-related maritime impacts')} ({f.get('location')})")

                # Last updated
                report_lines.append(f"\n🕐 LAST UPDATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (local time)")

                # Summary
                report_lines.append("\nThis report includes real-time disaster periods and status. Stay informed and prepared for any changes in the global disaster situation.")

                cleaned_content = '\n'.join(report_lines)
                return ChatResponse(
                    content=cleaned_content,
                    response_type=response_type,
                    confidence=0.98,
                    data_sources=real_time_data.get("sources", []),
                    real_time_data=real_time_data,
                    timestamp=datetime.now()
                )
        
        # Generate AI response
        if self.client and self.ai_provider == "openai":
            ai_response = await self._generate_openai_response(message, response_type, real_time_data, context_data)
        elif self.ai_provider == "ollama" and OLLAMA_AVAILABLE:
            ai_response = await self._generate_ollama_response(message, response_type, real_time_data)
        elif self.ai_provider == "huggingface" and HUGGINGFACE_AVAILABLE:
            ai_response = await self._generate_huggingface_response(message, response_type, real_time_data)
        else:
            ai_response = self._generate_fallback_response(message, response_type, real_time_data)
        
        # Clean the response to remove raw search results and incomplete content
        cleaned_content = self._clean_ai_response(ai_response["content"])
        
        return ChatResponse(
            content=cleaned_content,
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
        hazard_patterns = [
            'danger', 'hazard', 'risk', 'safe', 'safety', 'warning', 'alert', 
            'disaster', 'diaster', 'diasters', 'disasters', 'natural disaster', 'natural diasters',
            'emergency', 'affected', 'countries', 'earthquake', 'tsunami', 'hurricane', 'cyclone', 'typhoon',
            'currently happened', 'curretly happened', 'happening', 'currently affecting', 'active disasters'
        ]
        route_patterns = ['best route', 'route from', 'route to', 'navigate from', 'navigate to', 'navigation from', 'direction from', 'travel from', 'journey from', 'distance from', 'distance between', 'route between', 'shipping route', 'cargo route']
        safety_patterns = ['is it safe', 'safe to go', 'safe to travel', 'safe to visit', 'can i go', 'should i go', 'travel safety', 'is safe', 'safe for travel', 'travel to']
        
        # Check if the message is related to marine/weather/disaster topics
        message_lower = message.lower()
        is_marine_related = (
            any(pattern in message_lower for pattern in weather_patterns) or
            any(pattern in message_lower for pattern in marine_patterns) or
            any(pattern in message_lower for pattern in hazard_patterns) or
            any(pattern in message_lower for pattern in route_patterns) or
            any(pattern in message_lower for pattern in safety_patterns) or
            # Location-based queries that could be marine related
            any(location in message_lower for location in ['jaffna', 'colombo', 'chennai', 'singapore', 'mumbai', 'karachi', 'dubai', 'jakarta', 'manila', 'bangkok', 'china', 'india', 'sri lanka', 'ocean', 'bay', 'strait', 'gulf']) or
            # General marine context words
            any(word in message_lower for word in ['conditions', 'forecast', 'current', 'update', 'now', 'today', 'affected'])
        )
        
        if not is_marine_related:
            return ResponseType.GENERAL_CHAT  # Will be handled as out-of-scope
            
        # Enhanced disaster detection with pattern combinations
        disaster_keywords = ['diaster', 'diasters', 'disaster', 'disasters', 'natural']
        happening_keywords = ['happened', 'happening', 'curretly', 'currently', 'now', 'today', 'active', 'current']
        world_keywords = ['world', 'global', 'countries', 'anywhere']
        
        # Check for specific disaster detail queries (e.g., "tell me about earthquake in Japan")
        detail_keywords = ['tell me about', 'details about', 'more about', 'information about', 'report on', 'what happened in']
        location_keywords = ['china', 'taiwan', 'japan', 'philippines', 'india', 'russia', 'venezuela', 'indonesia', 'sri lanka']
        
        is_disaster_detail_query = (
            any(detail in message_lower for detail in detail_keywords) and
            any(disaster in message_lower for disaster in ['earthquake', 'storm', 'typhoon', 'flood', 'disaster']) and
            any(location in message_lower for location in location_keywords)
        )
        
        # Check for disaster queries with fuzzy matching
        is_disaster_query = (
            any(pattern in message_lower for pattern in hazard_patterns) or
            is_disaster_detail_query or
            # Check for combinations like "natural disasters currently happening"
            (any(d in message_lower for d in disaster_keywords) and 
             any(h in message_lower for h in happening_keywords)) or
            # Check for "disasters in the world" type queries
            (any(d in message_lower for d in disaster_keywords) and 
             any(w in message_lower for w in world_keywords))
        )
        
        # Check for safety queries first (more specific)
        if any(pattern in message_lower for pattern in safety_patterns):
            return ResponseType.SAFETY_ASSESSMENT
        # Prioritize weather queries to avoid false route detection
        elif any(pattern in message_lower for pattern in weather_patterns) and not is_disaster_query:
            return ResponseType.WEATHER
        elif is_disaster_query:
            return ResponseType.HAZARD_ALERT  
        elif any(pattern in message_lower for pattern in route_patterns):
            return ResponseType.ROUTE_GUIDANCE
        elif any(pattern in message_lower for pattern in marine_patterns):
            return ResponseType.MARINE_CONDITIONS
        else:
            return ResponseType.REAL_TIME_DATA
    
    async def _gather_real_time_data(self, message: str, context_data: Dict = None, response_type: ResponseType = None) -> Dict[str, Any]:
        """Gather REAL-TIME data from multiple sources INCLUDING maximized Google Search API usage"""
        
        data = {"sources": []}
        tasks = []
        
        # 🔍 MAXIMIZE GOOGLE SEARCH API USAGE - Always use for comprehensive information
        logger.info("🔍 MAXIMIZING Google Search API usage for comprehensive real-time data")
        
        # Determine search types based on query type
        search_types = []
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['weather', 'temperature', 'climate', 'condition', 'forecast']):
            search_types.extend(["weather_conditions", "current_events", "safety_info"])
        elif any(word in message_lower for word in ['disaster', 'earthquake', 'tsunami', 'hurricane', 'storm']):
            search_types.extend(["disaster_updates", "current_events", "safety_info", "impact_assessment"])
        elif any(word in message_lower for word in ['safe', 'safety', 'travel', 'visit']):
            search_types.extend(["safety_info", "current_events", "travel_advisory", "security_updates"])
        elif any(word in message_lower for word in ['route', 'navigation', 'shipping', 'port']):
            search_types.extend(["maritime_conditions", "port_status", "shipping_updates", "navigation_hazards"])
        else:
            search_types.extend(["current_events", "real_time_conditions", "safety_info"])
        
        # 🔥 Smart Google Search Usage - Only if within rate limits
        if self.google_search._check_rate_limits():
            logger.info("✅ Google Search available - making targeted search")
            tasks.append(self.google_search.search_comprehensive_data(message, search_types))
        else:
            logger.warning("⚠️ Google Search rate limited - relying on other data sources")
            
        # REMOVED: Additional Google Search calls to prevent rate limiting
        # The system will now rely on a single targeted search when available
        # and fall back to official data sources when rate limited
        
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
        
        # Get disaster data for disaster queries, safety assessments, and route planning
        if (response_type in [ResponseType.HAZARD_ALERT, ResponseType.SAFETY_ASSESSMENT, ResponseType.ROUTE_GUIDANCE] or
            any(word in message.lower() for word in ['disaster', 'earthquake', 'tsunami', 'natural disaster', 'hazard', 'happening', 'current', 'safe', 'safety'])):
            tasks.append(self.real_time_data.get_earthquake_data())
            tasks.append(self.real_time_data.get_global_disaster_info())
            # NOTE: Do NOT use internal hardcoded real-time disaster service
            # The previous implementation imported a service that contained
            # hardcoded/legacy events (e.g. Typhoon Ragasa). To avoid returning
            # outdated or fabricated disasters, we do NOT call
            # self._get_current_disasters() here. Rely on NOAA/USGS/NASA and
            # targeted Google searches instead.
        
        # Execute all data gathering tasks in parallel
        logger.info(f"🔄 Executing {len(tasks)} data gathering tasks")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Data gathering task {i} failed: {result}")
                continue
                
            if isinstance(result, dict) and result.get("success"):
                # � PROCESS ALL GOOGLE SEARCH RESULTS (Maximum Priority)
                if "combined_data" in result and "searches" in result:  # Comprehensive Google Search results
                    data["comprehensive_search"] = result
                    data["sources"].append("google_comprehensive_search")
                    search_count = len(result.get("combined_data", []))
                    logger.info(f"✅ Got {search_count} Google Search results from comprehensive search")
                elif "multi_angle_data" in result and "search_angles" in result:  # Multi-angle Google Search
                    data["multi_angle_search"] = result
                    data["sources"].append("google_multi_angle_search")
                    angle_count = len(result.get("multi_angle_data", []))
                    logger.info(f"✅ Got {angle_count} Google Search results from multi-angle search")
                elif "data" in result and result.get("source", "").startswith("google_api"):  # Single specific search
                    if "specific_search_results" not in data:
                        data["specific_search_results"] = []
                    data["specific_search_results"].append(result)
                    data["sources"].append("google_specific_search")
                    logger.info(f"✅ Got specific Google Search result: {result.get('query', 'Unknown query')[:50]}")
                elif "city" in result and "weather" in result:  # Real weather data
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
                elif "port_name" in result and result.get("port_name") == "Port of Singapore":  # Singapore maritime data
                    data["singapore_maritime"] = result
                    data["sources"].append("singapore_maritime_data")
                    logger.info(f"✅ Got Singapore maritime data with weather conditions")
        
        # Only get route data for ROUTE QUERIES, not weather queries
        if response_type == ResponseType.ROUTE_GUIDANCE:
            route_keywords = ['best route', 'route from', 'route to', 'navigate from', 'navigate to', 'distance from', 'distance between', 'route between', 'shipping route']
            if any(keyword in message.lower() for keyword in route_keywords):
                route_data = await self._calculate_marine_route(message)
                if route_data:
                    data["route_data"] = route_data
                    data["sources"].append("marine_route_calculator")
            
            if any(keyword in message.lower() for keyword in route_keywords):
                route_data = await self._calculate_smart_route(message)
                if route_data:
                    data["route_data"] = route_data
                    data["sources"].append("marine_route_calculator")

        # Add specific port weather data for major maritime hubs
        port_keywords = ['singapore port', 'port of singapore', 'singapore maritime', 'singapore shipping']
        if any(keyword in message_lower for keyword in port_keywords):
            singapore_data = await self._get_singapore_maritime_data()
            if singapore_data.get("success"):
                data["singapore_maritime"] = singapore_data
                data["sources"].append("singapore_maritime_data")

        # 🧠 INTELLIGENT ANALYSIS - Make AI truly smart
        if INTELLIGENT_ANALYZER_AVAILABLE and data.get("disaster_data"):
            logger.info("🧠 Running intelligent disaster/safety analysis...")
            
            # 1. Location Safety Analysis (for safety queries)
            if response_type == ResponseType.SAFETY_ASSESSMENT or \
               any(word in message_lower for word in ['safe', 'safety', 'dangerous', 'risk', 'go to', 'travel to', 'visit']):
                safety_analysis = intelligent_analyzer.analyze_location_safety(message, data["disaster_data"])
                if safety_analysis.get('analysis_performed'):
                    data["intelligent_safety_analysis"] = safety_analysis
                    data["sources"].append("intelligent_safety_analyzer")
                    logger.info(f"✅ Safety analysis: {safety_analysis.get('location')} - {'SAFE' if safety_analysis.get('is_safe') else 'UNSAFE'}")
            
            # 2. Regional Hazard Filtering (for regional queries like "Indian Ocean")
            if any(region in message_lower for region in ['indian ocean', 'pacific ocean', 'atlantic ocean', 'arabian sea', 'bay of bengal', 'south china sea']):
                regional_filter = intelligent_analyzer.filter_regional_hazards(message, data["disaster_data"])
                if regional_filter.get('filtering_performed'):
                    data["regional_hazard_filter"] = regional_filter
                    data["sources"].append("regional_hazard_filter")
                    logger.info(f"✅ Regional filter: {regional_filter.get('total_in_region')} hazards in {regional_filter.get('region')}")
            
            # 3. Route Hazard Analysis (for route queries)
            if response_type == ResponseType.ROUTE_GUIDANCE and data.get("route_data"):
                from_port = data["route_data"].get("from_port", {}).get("name", "")
                to_port = data["route_data"].get("to_port", {}).get("name", "")
                if from_port and to_port:
                    route_hazard_analysis = intelligent_analyzer.analyze_route_hazards(
                        from_port, to_port, data["disaster_data"], data["route_data"]
                    )
                    if route_hazard_analysis.get('analysis_performed'):
                        data["route_hazard_analysis"] = route_hazard_analysis
                        data["sources"].append("route_hazard_analyzer")
                        logger.info(f"✅ Route hazard analysis: {from_port} to {to_port} - {route_hazard_analysis.get('total_hazards')} hazards detected")
            
            # 4. Format all disasters with accurate timestamps
            if data.get("disaster_data", {}).get("disasters"):
                formatted_disasters = []
                for disaster in data["disaster_data"]["disasters"]:
                    formatted = intelligent_analyzer.format_disaster_with_accurate_time(disaster)
                    formatted_disasters.append(formatted)
                data["disaster_data"]["disasters"] = formatted_disasters
                logger.info("✅ All disasters formatted with accurate timestamps")

        logger.info(f"📊 Gathered data from {len(data['sources'])} sources: {data['sources']}")
        return data
    
    async def _get_current_disasters(self) -> Dict[str, Any]:
        """Get current disasters happening worldwide using real-time data"""
        try:
            # Intentionally disable the legacy real-time disaster aggregator
            # which contained hardcoded or stale events. Use primary sources
            # (USGS, NOAA, NASA EONET, GDACS) via their dedicated methods
            # or Google Search intelligence instead.
            logger.info("_get_current_disasters: legacy disaster aggregator disabled to avoid hardcoded events")

            return {
                "success": True,
                "disasters": [],
                "total_count": 0,
                "source": "disabled_legacy_disaster_service",
                "message": "Legacy real-time disaster aggregator is disabled. Use official sources (USGS, NOAA, GDACS, NASA EONET) or targeted searches for current events.",
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Unexpected error in _get_current_disasters: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error retrieving disaster data. Please consult official monitoring services.",
                "last_updated": datetime.now().isoformat()
            }

    def _enhance_location_details(self, location: str, event: str) -> str:
        """Enhance location details for better precision"""
        try:
            # Extract more specific location from event description if available
            location_lower = location.lower()
            event_lower = event.lower()
            
            # For earthquakes, event usually contains precise location
            if 'earthquake' in event_lower or 'M ' in event:
                # Extract location after magnitude info
                if ' - ' in event:
                    parts = event.split(' - ')
                    if len(parts) > 1:
                        precise_location = parts[1].strip()
                        if len(precise_location) > len(location):
                            return precise_location
            
            # For storms/typhoons, enhance with region info
            storm_regions = {
                'china': 'Eastern China Region',
                'taiwan': 'Taiwan Region',
                'philippines': 'Philippine Islands',
                'india': 'Indian Subcontinent',
                'japan': 'Japanese Islands',
                'indonesia': 'Indonesian Islands'
            }
            
            for country, enhanced in storm_regions.items():
                if country in location_lower and enhanced not in location:
                    return f"{location} ({enhanced})"
            
            return location
            
        except Exception as e:
            logger.error(f"Error enhancing location: {e}")
            return location

    async def _calculate_smart_route(self, message: str) -> Dict[str, Any]:
        """Calculate smart maritime routes using hardcoded database with hazard analysis"""
        try:
            # Extract port information from message
            import re
            
            # Look for port patterns
            port_patterns = [
                r'from\s+([a-zA-Z\s]+?)(?:\s+port)?\s+to\s+([a-zA-Z\s]+?)(?:\s+port)?(?:\s|$|\?)',
                r'between\s+([a-zA-Z\s]+?)(?:\s+port)?\s+and\s+([a-zA-Z\s]+?)(?:\s+port)?(?:\s|$|\?)',
                r'([a-zA-Z\s]+?)(?:\s+port)?\s+to\s+([a-zA-Z\s]+?)(?:\s+port)?(?:\s|$|\?)',
                r'route\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:\s|$|\?)',
            ]
            
            from_port = None
            to_port = None
            
            for pattern in port_patterns:
                match = re.search(pattern, message.lower())
                if match:
                    from_port = match.group(1).strip()
                    to_port = match.group(2).strip()
                    break
            
            if not from_port or not to_port:
                logger.warning("Could not extract port names from message")
                return None
            
            logger.info(f"🚢 Looking for route from '{from_port}' to '{to_port}'")
            
            # Find route in hardcoded database
            route_data = self.route_database.find_route(from_port, to_port)
            
            if not route_data:
                logger.warning(f"No hardcoded route found for {from_port} to {to_port}")
                return {"success": False, "error": f"No route data available for {from_port} to {to_port}"}
            
            logger.info(f"✅ Found route: {route_data['from_port']} to {route_data['to_port']}")
            
            # Get disaster data for hazard analysis
            disaster_data = await self.real_time_data.get_global_disasters()
            
            # Analyze hazards along the route using intelligent analyzer
            hazard_analysis = None
            if INTELLIGENT_ANALYZER_AVAILABLE and disaster_data.get('success'):
                logger.info("🧠 Running intelligent route hazard analysis...")
                hazard_analysis = intelligent_analyzer.analyze_route_hazards(
                    from_port, 
                    to_port, 
                    disaster_data
                )
                if hazard_analysis and hazard_analysis.get('analysis_performed'):
                    logger.info(f"✅ Hazard analysis complete: Risk Level = {hazard_analysis.get('risk_level')}")
                    route_data['hazard_analysis'] = hazard_analysis
            
            route_data['success'] = True
            route_data['source'] = 'hardcoded_maritime_database'
            
            return route_data
            
        except Exception as e:
            logger.error(f"Error calculating route: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _get_route_description(self, from_port: str, to_port: str, distance: float) -> str:
        """Get route description based on ports"""
        # Build a detailed route description for any ports
        description = (
            f"Route from {from_port} to {to_port} covers approximately {int(distance)} nautical miles.\n"
            f"- Departure from {from_port} port, following recommended departure channels.\n"
            f"- Transit through major international shipping lanes and recommended waypoints.\n"
            f"- Cross open ocean areas, monitoring for weather and maritime hazards.\n"
            f"- If applicable, pass through key straits, channels, or TSS (e.g., Malacca Strait, Taiwan Strait, Suez Canal, Panama Canal).\n"
            f"- Approach {to_port} via designated approach channels and arrival procedures.\n"
            f"- Route may include EEZ boundaries, international waters, and port entry requirements.\n"
            f"- Recommended to check for real-time weather, piracy, and navigation warnings en route.\n"
            f"- For more precise routing, consult updated marine charts and local authorities."
        )
        return description
    
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
            # Comprehensive Port coordinates database - Major Maritime Ports Worldwide
            ports = {
                # Indian Ocean & South Asia
                'chennai': {'name': 'Chennai Port', 'lat': 13.0827, 'lon': 80.2707, 'country': 'India', 'region': 'Bay of Bengal'},
                'mumbai': {'name': 'Mumbai Port', 'lat': 19.0760, 'lon': 72.8777, 'country': 'India', 'region': 'Arabian Sea'},
                'kolkata': {'name': 'Kolkata Port', 'lat': 22.5726, 'lon': 88.3639, 'country': 'India', 'region': 'Bay of Bengal'},
                'kochi': {'name': 'Kochi Port', 'lat': 9.9312, 'lon': 76.2673, 'country': 'India', 'region': 'Arabian Sea'},
                'tuticorin': {'name': 'Tuticorin Port', 'lat': 8.8047, 'lon': 78.1378, 'country': 'India', 'region': 'Bay of Bengal'},
                'visakhapatnam': {'name': 'Visakhapatnam Port', 'lat': 17.6868, 'lon': 83.2185, 'country': 'India', 'region': 'Bay of Bengal'},
                'karachi': {'name': 'Karachi Port', 'lat': 24.8607, 'lon': 67.0011, 'country': 'Pakistan', 'region': 'Arabian Sea'},
                'gwadar': {'name': 'Gwadar Port', 'lat': 25.1216, 'lon': 62.3254, 'country': 'Pakistan', 'region': 'Arabian Sea'},
                'colombo': {'name': 'Colombo Port', 'lat': 6.9271, 'lon': 79.8612, 'country': 'Sri Lanka', 'region': 'Indian Ocean'},
                'hambantota': {'name': 'Hambantota Port', 'lat': 6.1241, 'lon': 81.1185, 'country': 'Sri Lanka', 'region': 'Indian Ocean'},
                'jaffna': {'name': 'Jaffna Port', 'lat': 9.6615, 'lon': 80.0255, 'country': 'Sri Lanka', 'region': 'Bay of Bengal'},
                'chittagong': {'name': 'Chittagong Port', 'lat': 22.3569, 'lon': 91.7832, 'country': 'Bangladesh', 'region': 'Bay of Bengal'},
                'yangon': {'name': 'Yangon Port', 'lat': 16.7967, 'lon': 96.1610, 'country': 'Myanmar', 'region': 'Bay of Bengal'},

                # Southeast Asia & Pacific
                'singapore': {'name': 'Singapore Port', 'lat': 1.3521, 'lon': 103.8198, 'country': 'Singapore', 'region': 'Strait of Malacca'},
                'port_klang': {'name': 'Port Klang', 'lat': 3.0319, 'lon': 101.3544, 'country': 'Malaysia', 'region': 'Strait of Malacca'},
                'penang': {'name': 'Penang Port', 'lat': 5.4164, 'lon': 100.3327, 'country': 'Malaysia', 'region': 'Strait of Malacca'},
                'johor': {'name': 'Port of Tanjung Pelepas', 'lat': 1.3667, 'lon': 103.5500, 'country': 'Malaysia', 'region': 'Strait of Malacca'},
                'jakarta': {'name': 'Jakarta Port (Tanjung Priok)', 'lat': -6.1067, 'lon': 106.8833, 'country': 'Indonesia', 'region': 'Java Sea'},
                'surabaya': {'name': 'Surabaya Port', 'lat': -7.2105, 'lon': 112.7395, 'country': 'Indonesia', 'region': 'Java Sea'},
                'belawan': {'name': 'Belawan Port', 'lat': 3.7792, 'lon': 98.6835, 'country': 'Indonesia', 'region': 'Strait of Malacca'},
                'bangkok': {'name': 'Bangkok Port (Laem Chabang)', 'lat': 13.0824, 'lon': 100.8831, 'country': 'Thailand', 'region': 'Gulf of Thailand'},
                'ho_chi_minh': {'name': 'Ho Chi Minh Port', 'lat': 10.7769, 'lon': 106.7009, 'country': 'Vietnam', 'region': 'South China Sea'},
                'haiphong': {'name': 'Haiphong Port', 'lat': 20.8449, 'lon': 106.6881, 'country': 'Vietnam', 'region': 'South China Sea'},
                'manila': {'name': 'Manila Port', 'lat': 14.5995, 'lon': 120.9842, 'country': 'Philippines', 'region': 'South China Sea'},
                'cebu': {'name': 'Cebu Port', 'lat': 10.3157, 'lon': 123.8854, 'country': 'Philippines', 'region': 'Philippine Sea'},

                # East Asia
                'shanghai': {'name': 'Shanghai Port', 'lat': 31.2304, 'lon': 121.4737, 'country': 'China', 'region': 'East China Sea'},
                'ningbo': {'name': 'Ningbo-Zhoushan Port', 'lat': 29.8736, 'lon': 121.5440, 'country': 'China', 'region': 'East China Sea'},
                'shenzhen': {'name': 'Shenzhen Port', 'lat': 22.5431, 'lon': 114.0579, 'country': 'China', 'region': 'South China Sea'},
                'guangzhou': {'name': 'Guangzhou Port', 'lat': 23.1291, 'lon': 113.2644, 'country': 'China', 'region': 'South China Sea'},
                'qingdao': {'name': 'Qingdao Port', 'lat': 36.0986, 'lon': 120.3719, 'country': 'China', 'region': 'Yellow Sea'},
                'tianjin': {'name': 'Tianjin Port', 'lat': 39.0458, 'lon': 117.7219, 'country': 'China', 'region': 'Bohai Sea'},
                'dalian': {'name': 'Dalian Port', 'lat': 38.9140, 'lon': 121.6147, 'country': 'China', 'region': 'Yellow Sea'},
                'xiamen': {'name': 'Xiamen Port', 'lat': 24.4798, 'lon': 118.0819, 'country': 'China', 'region': 'Taiwan Strait'},
                'hong_kong': {'name': 'Hong Kong Port', 'lat': 22.3193, 'lon': 114.1694, 'country': 'Hong Kong', 'region': 'South China Sea'},
                'kaohsiung': {'name': 'Kaohsiung Port', 'lat': 22.6273, 'lon': 120.3014, 'country': 'Taiwan', 'region': 'Taiwan Strait'},
                'keelung': {'name': 'Keelung Port', 'lat': 25.1276, 'lon': 121.7393, 'country': 'Taiwan', 'region': 'East China Sea'},
                'busan': {'name': 'Busan Port', 'lat': 35.1796, 'lon': 129.0756, 'country': 'South Korea', 'region': 'Korea Strait'},
                'incheon': {'name': 'Incheon Port', 'lat': 37.4563, 'lon': 126.7052, 'country': 'South Korea', 'region': 'Yellow Sea'},
                'tokyo': {'name': 'Tokyo Port', 'lat': 35.6262, 'lon': 139.7595, 'country': 'Japan', 'region': 'Tokyo Bay'},
                'yokohama': {'name': 'Yokohama Port', 'lat': 35.4437, 'lon': 139.6380, 'country': 'Japan', 'region': 'Tokyo Bay'},
                'kobe': {'name': 'Kobe Port', 'lat': 34.6901, 'lon': 135.1956, 'country': 'Japan', 'region': 'Osaka Bay'},
                'osaka': {'name': 'Osaka Port', 'lat': 34.6515, 'lon': 135.4349, 'country': 'Japan', 'region': 'Osaka Bay'},
                'nagoya': {'name': 'Nagoya Port', 'lat': 35.0836, 'lon': 136.8845, 'country': 'Japan', 'region': 'Ise Bay'},

                # Middle East & Persian Gulf
                'dubai': {'name': 'Dubai Port', 'lat': 25.2048, 'lon': 55.2708, 'country': 'UAE', 'region': 'Persian Gulf'},
                'abu_dhabi': {'name': 'Abu Dhabi Port', 'lat': 24.4539, 'lon': 54.3773, 'country': 'UAE', 'region': 'Persian Gulf'},
                'sharjah': {'name': 'Sharjah Port', 'lat': 25.3463, 'lon': 55.4209, 'country': 'UAE', 'region': 'Persian Gulf'},
                'kuwait': {'name': 'Kuwait Port', 'lat': 29.3759, 'lon': 47.9774, 'country': 'Kuwait', 'region': 'Persian Gulf'},
                'doha': {'name': 'Doha Port', 'lat': 25.2854, 'lon': 51.5310, 'country': 'Qatar', 'region': 'Persian Gulf'},
                'manama': {'name': 'Manama Port', 'lat': 26.2285, 'lon': 50.5860, 'country': 'Bahrain', 'region': 'Persian Gulf'},
                'dammam': {'name': 'Dammam Port', 'lat': 26.4207, 'lon': 50.0888, 'country': 'Saudi Arabia', 'region': 'Persian Gulf'},
                'jeddah': {'name': 'Jeddah Port', 'lat': 21.4858, 'lon': 39.1925, 'country': 'Saudi Arabia', 'region': 'Red Sea'},
                'bandar_abbas': {'name': 'Bandar Abbas Port', 'lat': 27.1867, 'lon': 56.2808, 'country': 'Iran', 'region': 'Persian Gulf'},

                # Africa
                'suez': {'name': 'Suez Port', 'lat': 29.9668, 'lon': 32.5498, 'country': 'Egypt', 'region': 'Red Sea'},
                'alexandria': {'name': 'Alexandria Port', 'lat': 31.2001, 'lon': 29.9187, 'country': 'Egypt', 'region': 'Mediterranean Sea'},
                'port_said': {'name': 'Port Said', 'lat': 31.2653, 'lon': 32.3019, 'country': 'Egypt', 'region': 'Mediterranean Sea'},
                'durban': {'name': 'Durban Port', 'lat': -29.8587, 'lon': 31.0218, 'country': 'South Africa', 'region': 'Indian Ocean'},
                'cape_town': {'name': 'Cape Town Port', 'lat': -33.9249, 'lon': 18.4241, 'country': 'South Africa', 'region': 'Atlantic Ocean'},
                'dar_es_salaam': {'name': 'Dar es Salaam Port', 'lat': -6.8235, 'lon': 39.2695, 'country': 'Tanzania', 'region': 'Indian Ocean'},

                # Europe
                'rotterdam': {'name': 'Rotterdam Port', 'lat': 51.9244, 'lon': 4.4777, 'country': 'Netherlands', 'region': 'North Sea'},
                'antwerp': {'name': 'Antwerp Port', 'lat': 51.2194, 'lon': 4.4025, 'country': 'Belgium', 'region': 'North Sea'},
                'hamburg': {'name': 'Hamburg Port', 'lat': 53.5511, 'lon': 9.9937, 'country': 'Germany', 'region': 'North Sea'},
                'bremerhaven': {'name': 'Bremerhaven Port', 'lat': 53.5366, 'lon': 8.5810, 'country': 'Germany', 'region': 'North Sea'},
                'felixstowe': {'name': 'Felixstowe Port', 'lat': 51.9642, 'lon': 1.3518, 'country': 'UK', 'region': 'North Sea'},
                'london': {'name': 'London Port', 'lat': 51.5074, 'lon': -0.1278, 'country': 'UK', 'region': 'Thames Estuary'},
                'le_havre': {'name': 'Le Havre Port', 'lat': 49.4944, 'lon': 0.1079, 'country': 'France', 'region': 'English Channel'},
                'marseille': {'name': 'Marseille Port', 'lat': 43.2965, 'lon': 5.3698, 'country': 'France', 'region': 'Mediterranean Sea'},
                'barcelona': {'name': 'Barcelona Port', 'lat': 41.3851, 'lon': 2.1734, 'country': 'Spain', 'region': 'Mediterranean Sea'},
                'valencia': {'name': 'Valencia Port', 'lat': 39.4699, 'lon': -0.3763, 'country': 'Spain', 'region': 'Mediterranean Sea'},
                'algeciras': {'name': 'Algeciras Port', 'lat': 36.1408, 'lon': -5.4526, 'country': 'Spain', 'region': 'Strait of Gibraltar'},
                'genoa': {'name': 'Genoa Port', 'lat': 44.4056, 'lon': 8.9463, 'country': 'Italy', 'region': 'Mediterranean Sea'},
                'la_spezia': {'name': 'La Spezia Port', 'lat': 44.1023, 'lon': 9.8184, 'country': 'Italy', 'region': 'Mediterranean Sea'},
                'piraeus': {'name': 'Piraeus Port', 'lat': 37.9386, 'lon': 23.6426, 'country': 'Greece', 'region': 'Mediterranean Sea'},

                # Americas
                'los_angeles': {'name': 'Los Angeles Port', 'lat': 33.7361, 'lon': -118.2642, 'country': 'USA', 'region': 'Pacific Ocean'},
                'long_beach': {'name': 'Long Beach Port', 'lat': 33.7653, 'lon': -118.2014, 'country': 'USA', 'region': 'Pacific Ocean'},
                'seattle': {'name': 'Seattle Port', 'lat': 47.6062, 'lon': -122.3321, 'country': 'USA', 'region': 'Pacific Ocean'},
                'oakland': {'name': 'Oakland Port', 'lat': 37.8044, 'lon': -122.2711, 'country': 'USA', 'region': 'Pacific Ocean'},
                'new_york': {'name': 'New York Port', 'lat': 40.6892, 'lon': -74.0445, 'country': 'USA', 'region': 'Atlantic Ocean'},
                'norfolk': {'name': 'Norfolk Port', 'lat': 36.8508, 'lon': -76.2859, 'country': 'USA', 'region': 'Atlantic Ocean'},
                'charleston': {'name': 'Charleston Port', 'lat': 32.7767, 'lon': -79.9311, 'country': 'USA', 'region': 'Atlantic Ocean'},
                'savannah': {'name': 'Savannah Port', 'lat': 32.0835, 'lon': -81.0998, 'country': 'USA', 'region': 'Atlantic Ocean'},
                'houston': {'name': 'Houston Port', 'lat': 29.7604, 'lon': -95.3698, 'country': 'USA', 'region': 'Gulf of Mexico'},
                'new_orleans': {'name': 'New Orleans Port', 'lat': 29.9511, 'lon': -90.0715, 'country': 'USA', 'region': 'Gulf of Mexico'},
                'vancouver': {'name': 'Vancouver Port', 'lat': 49.2827, 'lon': -123.1207, 'country': 'Canada', 'region': 'Pacific Ocean'},
                'montreal': {'name': 'Montreal Port', 'lat': 45.5017, 'lon': -73.5673, 'country': 'Canada', 'region': 'St. Lawrence River'},
                'santos': {'name': 'Santos Port', 'lat': -23.9618, 'lon': -46.3322, 'country': 'Brazil', 'region': 'Atlantic Ocean'},
                'rio_de_janeiro': {'name': 'Rio de Janeiro Port', 'lat': -22.9068, 'lon': -43.1729, 'country': 'Brazil', 'region': 'Atlantic Ocean'},
                'buenos_aires': {'name': 'Buenos Aires Port', 'lat': -34.6118, 'lon': -58.3960, 'country': 'Argentina', 'region': 'Rio de la Plata'},
                'valparaiso': {'name': 'Valparaiso Port', 'lat': -33.0458, 'lon': -71.6197, 'country': 'Chile', 'region': 'Pacific Ocean'},
                'callao': {'name': 'Callao Port', 'lat': -12.0464, 'lon': -77.1428, 'country': 'Peru', 'region': 'Pacific Ocean'},

                # Australia & Oceania  
                'sydney': {'name': 'Sydney Port', 'lat': -33.8688, 'lon': 151.2093, 'country': 'Australia', 'region': 'Tasman Sea'},
                'melbourne': {'name': 'Melbourne Port', 'lat': -37.8136, 'lon': 144.9631, 'country': 'Australia', 'region': 'Bass Strait'},
                'brisbane': {'name': 'Brisbane Port', 'lat': -27.4698, 'lon': 153.0251, 'country': 'Australia', 'region': 'Coral Sea'},
                'fremantle': {'name': 'Fremantle Port', 'lat': -32.0569, 'lon': 115.7439, 'country': 'Australia', 'region': 'Indian Ocean'},
                'adelaide': {'name': 'Adelaide Port', 'lat': -34.9285, 'lon': 138.6007, 'country': 'Australia', 'region': 'Great Australian Bight'},
                'auckland': {'name': 'Auckland Port', 'lat': -36.8485, 'lon': 174.7633, 'country': 'New Zealand', 'region': 'Tasman Sea'},
                'wellington': {'name': 'Wellington Port', 'lat': -41.2865, 'lon': 174.7762, 'country': 'New Zealand', 'region': 'Cook Strait'}
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
                
                # Get detailed route information first
                route_info = self._get_route_info(port1_key, port2_key)
                
                # Determine optimal speed based on route characteristics and season
                speed_info = self._calculate_route_speed(distance_nm, route_info, port1_key, port2_key)
                avg_speed_knots = speed_info['optimal_speed']
                
                # Calculate sailing time with more accuracy
                sailing_time_hours = distance_nm / avg_speed_knots
                sailing_days = sailing_time_hours / 24
                
                # Calculate fuel consumption estimate
                fuel_consumption = self._estimate_fuel_consumption(distance_nm, avg_speed_knots, route_info)
                
                return {
                    "success": True,
                    "from_port": port1,
                    "to_port": port2,
                    "distance_km": round(distance_km, 1),
                    "distance_nm": round(distance_nm, 1),
                    "estimated_sailing_time": {
                        "hours": round(sailing_time_hours, 1),
                        "days": round(sailing_days, 1),
                        "detailed": f"{int(sailing_days)} days {int((sailing_days % 1) * 24)} hours"
                    },
                    "route_info": route_info,
                    "speed_analysis": speed_info,
                    "fuel_analysis": fuel_consumption,
                    "avg_vessel_speed": f"{avg_speed_knots} knots",
                    "detailed_routing": {
                        "route_description": route_info.get('description', 'Direct maritime route'),
                        "major_waypoints": route_info.get('key_waypoints', []),
                        "navigation_considerations": route_info.get('navigation_notes', []),
                        "seasonal_factors": route_info.get('weather_patterns', []),
                        "alternative_options": route_info.get('alternative_routes', [])
                    }
                }
            
            return {"success": False, "error": "Could not identify two ports in the message"}
            
        except Exception as e:
            logger.error(f"Route calculation error: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_route_info(self, port1: str, port2: str) -> Dict[str, Any]:
        """Get comprehensive route-specific information with detailed maritime routing"""
        
        # Comprehensive route database with specific maritime routing details
        route_data = {
            # Indian Ocean & Bay of Bengal Routes
            ('chennai', 'singapore'): {
                "route_name": "Chennai-Singapore Major Shipping Route",
                "description": "Southeast via Bay of Bengal through Strait of Malacca to Singapore Port",
                "distance_breakdown": "Chennai → Palk Strait (120 NM) → Strait of Malacca entry (720 NM) → Singapore (180 NM)",
                "key_waypoints": ["10°N 80°30'E (Palk Strait)", "05°N 95°E (Nicobar Passage)", "01°20'N 103°50'E (Singapore Strait East)"],
                "major_straits": ["Palk Strait", "Ten Degree Channel", "Strait of Malacca", "Singapore Strait"],
                "shipping_lanes": ["Great Circle Route via Bay of Bengal", "TSS Malacca Strait", "Singapore Port Approach"],
                "navigation_notes": ["Heavy merchant traffic in Malacca Strait", "Mandatory pilot in Singapore waters", "Speed restrictions in strait approaches"],
                "weather_patterns": ["SW Monsoon (Jun-Sep): Rough seas, heavy rain", "NE Monsoon (Dec-Mar): Calmer conditions", "Inter-monsoon (Apr-May, Oct-Nov): Variable"],
                "seasonal_speeds": {"optimal": "14-16 knots", "monsoon": "12-14 knots", "rough_weather": "10-12 knots"},
                "fuel_considerations": "Refueling available at Singapore - major bunkering hub",
                "alternative_routes": ["Via Sunda Strait (add 200 NM)", "Via Lombok Strait (add 350 NM)"],
                "hazards": ["Piracy risk areas near Malacca Strait", "Dense fishing traffic", "Underwater obstacles near Palk Strait"]
            },
            ('singapore', 'mumbai'): {
                "route_name": "Singapore-Mumbai Trans-Indian Ocean Route", 
                "description": "Northwest via Strait of Malacca, across Indian Ocean to Arabian Sea and Mumbai",
                "distance_breakdown": "Singapore → Malacca Strait exit (180 NM) → Indian Ocean crossing (1,240 NM) → Mumbai approach (120 NM)",
                "key_waypoints": ["01°20'N 103°50'E (Singapore Strait)", "06°N 95°E (Malacca exit)", "08°N 73°E (Mumbai approach)"],
                "major_straits": ["Singapore Strait", "Strait of Malacca", "Nine Degree Channel"],
                "shipping_lanes": ["Great Circle Route across Indian Ocean", "Mumbai Port Traffic Separation Scheme"],
                "navigation_notes": ["Open ocean navigation for 1,200+ NM", "Mumbai pilot mandatory", "Traffic density increases near Lakshadweep"],
                "weather_patterns": ["SW Monsoon (Jun-Sep): Head winds and rough seas", "Post-monsoon (Oct-Nov): Optimal conditions"],
                "seasonal_speeds": {"optimal": "15-17 knots", "monsoon": "11-13 knots", "cyclone_season": "10-12 knots"},
                "fuel_considerations": "Long ocean crossing - ensure adequate fuel or plan bunkering at Colombo",
                "alternative_routes": ["Via Colombo (add 150 NM for refueling)", "Via Maldives (tourist/fishing traffic)"],
                "hazards": ["Cyclone season Apr-Dec", "Fishing vessels near Lakshadweep", "Commercial traffic convergence near Mumbai"]
            },
            ('dubai', 'mumbai'): {
                "route_name": "Dubai-Mumbai Arabian Sea Direct Route",
                "description": "Southeast across Arabian Sea from Persian Gulf to Mumbai",
                "distance_breakdown": "Dubai → Persian Gulf exit (120 NM) → Arabian Sea crossing (750 NM) → Mumbai (80 NM)",
                "key_waypoints": ["25°12'N 55°16'E (Dubai Port)", "24°N 59°E (Strait of Hormuz)", "19°05'N 72°50'E (Mumbai)"],
                "major_straits": ["Strait of Hormuz"],  
                "shipping_lanes": ["Persian Gulf TSS", "Arabian Sea Shipping Route", "Mumbai Approach Channel"],
                "navigation_notes": ["Heavy tanker traffic in Persian Gulf", "Open Arabian Sea navigation", "Mumbai pilot required"],
                "weather_patterns": ["Shamal winds (Jun-Jul): Strong NW winds", "Monsoon (Jun-Sep): Rough seas", "Winter (Dec-Feb): Calm conditions"],
                "seasonal_speeds": {"winter": "16-18 knots", "shamal_season": "13-15 knots", "monsoon": "11-13 knots"},
                "fuel_considerations": "Dubai major bunkering hub - top off before departure",
                "alternative_routes": ["Via Karachi (add 200 NM)", "Via Gwadar (add 100 NM)"],
                "hazards": ["Dense tanker traffic", "Fishing dhows", "Potential political tensions in Persian Gulf"]
            },
            ('shanghai', 'singapore'): {
                "route_name": "Shanghai-Singapore East Asia Major Trade Route",
                "description": "South via East China Sea, Taiwan Strait, South China Sea to Singapore",
                "distance_breakdown": "Shanghai → Taiwan Strait (520 NM) → South China Sea (680 NM) → Singapore (250 NM)",
                "key_waypoints": ["31°14'N 121°28'E (Shanghai)", "23°30'N 118°E (Taiwan Strait)", "01°20'N 103°50'E (Singapore)"],
                "major_straits": ["Taiwan Strait", "Singapore Strait"],
                "shipping_lanes": ["East China Sea Shipping Route", "Taiwan Strait TSS", "South China Sea Main Route", "Singapore Strait TSS"],
                "navigation_notes": ["Extremely heavy container traffic", "Taiwan Strait weather restrictions", "Singapore pilot mandatory"],
                "weather_patterns": ["Typhoon season (May-Nov): Route disruptions possible", "Winter (Dec-Feb): Stable conditions", "Spring (Mar-Apr): Variable weather"],
                "seasonal_speeds": {"winter": "16-18 knots", "typhoon_season": "12-15 knots", "optimal": "15-17 knots"},
                "fuel_considerations": "Singapore major bunkering hub - efficient fuel pricing",
                "alternative_routes": ["Via Luzon Strait (add 180 NM)", "Via Balabac Strait (add 220 NM)"],
                "hazards": ["Typhoons May-November", "Dense commercial traffic", "Fishing vessel interactions"]
            },
            ('busan', 'los_angeles'): {
                "route_name": "Busan-Los Angeles Trans-Pacific Container Route",
                "description": "Great Circle Route across North Pacific Ocean",
                "distance_breakdown": "Busan → Aleutian routing (3,200 NM) → California approach (2,100 NM)",
                "key_waypoints": ["35°11'N 129°04'E (Busan)", "45°N 160°E (North Pacific)", "33°44'N 118°16'W (Los Angeles)"],
                "major_straits": ["Korea Strait (departure)", "San Pedro Channel (arrival)"],
                "shipping_lanes": ["Great Circle Trans-Pacific Route", "North Pacific Traffic Lanes", "Los Angeles TSS"],
                "navigation_notes": ["Long ocean passage 14-16 days", "Weather routing essential", "Los Angeles pilot required"],
                "weather_patterns": ["North Pacific storms (Oct-Mar)", "Summer (Jun-Aug): Calmer conditions", "Typhoon influence (Jul-Oct)"],
                "seasonal_speeds": {"summer": "18-20 knots", "winter": "14-16 knots", "storm_season": "12-15 knots"},
                "fuel_considerations": "Major ocean crossing - full bunkers required, no intermediate fuel stops",
                "alternative_routes": ["Great Circle High Route (shorter in summer)", "Southern Route via Hawaii (longer but calmer)"],
                "hazards": ["North Pacific storms", "Fog near Aleutians", "Heavy traffic near LA approaches"]
            },
            ('rotterdam', 'new_york'): {
                "route_name": "Rotterdam-New York North Atlantic Container Route",
                "description": "Southwest across North Atlantic via Great Circle routing",
                "distance_breakdown": "Rotterdam → English Channel (180 NM) → Atlantic crossing (2,900 NM) → New York (120 NM)",
                "key_waypoints": ["51°55'N 04°29'E (Rotterdam)", "50°N 02°W (English Channel)", "40°41'N 74°03'W (New York)"],
                "major_straits": ["English Channel", "The Narrows (New York Harbor)"],
                "shipping_lanes": ["English Channel TSS", "North Atlantic Shipping Lanes", "New York Approach"],
                "navigation_notes": ["Heavy traffic in English Channel", "Weather routing across Atlantic", "New York pilot mandatory"],
                "weather_patterns": ["Atlantic storms (Oct-Mar)", "Summer (Jun-Aug): Generally favorable", "Winter gales common"],
                "seasonal_speeds": {"summer": "18-20 knots", "winter": "15-17 knots", "gale_conditions": "12-14 knots"},
                "fuel_considerations": "Rotterdam major bunkering hub - competitive pricing",
                "alternative_routes": ["Southern Route via Azores (add 300 NM)", "Northern Route (summer only, shorter)"],
                "hazards": ["Atlantic storms", "Icebergs (Mar-Jul northern routes)", "Dense traffic in approaches"]
            },
            ('jeddah', 'mumbai'): {
                "route_name": "Jeddah-Mumbai Red Sea to Arabian Sea Route",
                "description": "Southeast via Red Sea, Arabian Sea to Mumbai",
                "distance_breakdown": "Jeddah → Bab el-Mandeb (420 NM) → Arabian Sea (780 NM) → Mumbai (90 NM)",
                "key_waypoints": ["21°29'N 39°11'E (Jeddah)", "12°35'N 43°20'E (Bab el-Mandeb)", "19°05'N 72°50'E (Mumbai)"],
                "major_straits": ["Bab el-Mandeb Strait"],
                "shipping_lanes": ["Red Sea Main Channel", "Arabian Sea Shipping Route", "Mumbai TSS"],
                "navigation_notes": ["Suez Canal approach traffic", "Bab el-Mandeb congestion", "Mumbai pilot required"],
                "weather_patterns": ["Red Sea: Hot, dry conditions year-round", "Arabian Sea: Monsoon Jun-Sep", "Shamal winds (summer)"],
                "seasonal_speeds": {"winter": "16-18 knots", "monsoon": "13-15 knots", "summer": "14-16 knots"},
                "fuel_considerations": "Jeddah available for bunkering - premium pricing",
                "alternative_routes": ["Via Suez Canal to Mediterranean (container routes)", "Via Aden for refueling"],
                "hazards": ["Red Sea coral reefs", "Piracy near Bab el-Mandeb", "Fishing traffic"]
            },
            ('hong_kong', 'vancouver'): {
                "route_name": "Hong Kong-Vancouver Trans-Pacific Route",
                "description": "Northeast across Pacific via Great Circle routing to Vancouver",
                "distance_breakdown": "Hong Kong → North Pacific (4,100 NM) → Vancouver approach (300 NM)",
                "key_waypoints": ["22°19'N 114°10'E (Hong Kong)", "40°N 170°E (Mid-Pacific)", "49°17'N 123°07'W (Vancouver)"],
                "major_straits": ["Victoria Harbor (departure)", "Juan de Fuca Strait (arrival)"],
                "shipping_lanes": ["South China Sea exit", "North Pacific Great Circle", "Vancouver TSS"],
                "navigation_notes": ["Long ocean passage 13-15 days", "Weather routing critical", "Vancouver pilot required"],
                "weather_patterns": ["Typhoons Jun-Nov (departure)", "North Pacific storms Oct-Mar", "Summer generally favorable"],
                "seasonal_speeds": {"summer": "17-19 knots", "winter": "14-16 knots", "storm_season": "12-15 knots"},
                "fuel_considerations": "Full ocean crossing - ensure maximum bunkers at Hong Kong",
                "alternative_routes": ["Northern Great Circle (summer)", "Southern route via Hawaii (add 500 NM)"],
                "hazards": ["Typhoons in South China Sea", "North Pacific storms", "Fog near Vancouver"]
            }
        }
        
        # Generate route key combinations (both directions)
        key1 = (port1, port2)
        key2 = (port2, port1)
        
        # Check for exact route match
        if key1 in route_data:
            return route_data[key1]
        elif key2 in route_data:
            # Reverse the route but maintain accuracy
            route = route_data[key2].copy()
            route["route_name"] = f"{port1.title()}-{port2.title()} " + route["route_name"].split('-', 1)[1] if '-' in route["route_name"] else f"{port1.title()}-{port2.title()} Route"
            return route
        else:
            # Generate intelligent default based on port regions
            return self._generate_intelligent_route_info(port1, port2)
    
    def _generate_intelligent_route_info(self, port1: str, port2: str) -> Dict[str, Any]:
        """Generate intelligent route information based on port locations and regions"""
        # This would analyze the port regions and generate appropriate routing information
        return {
            "route_name": f"{port1.title()}-{port2.title()} Maritime Route",
            "description": f"Direct maritime route from {port1.title()} to {port2.title()} following international shipping lanes",
            "distance_breakdown": "Route analysis based on great circle distance with port approach considerations",
            "key_waypoints": ["Departure port approach", "Open ocean waypoints", "Destination port approach"],
            "major_straits": ["Route-specific straits and channels based on geographic location"],
            "shipping_lanes": ["International shipping lanes", "Regional traffic separation schemes"],
            "navigation_notes": ["Follow IMO regulations", "Check local pilot requirements", "Monitor weather conditions"],
            "weather_patterns": ["Seasonal weather patterns vary by region and route"],
            "seasonal_speeds": {"optimal": "15-17 knots", "adverse": "12-14 knots", "severe": "10-12 knots"},
            "fuel_considerations": "Plan fuel requirements based on distance and no intermediate stops",
            "alternative_routes": ["Alternative routing options depend on weather and traffic"],
            "hazards": ["Standard maritime hazards", "Regional weather patterns", "Commercial traffic areas"]
        }
    
    def _calculate_route_speed(self, distance_nm: float, route_info: Dict, port1: str, port2: str) -> Dict[str, Any]:
        """Calculate optimal speed based on route characteristics, distance, and seasonal factors"""
        
        # Base speeds by route type and conditions
        base_speed = 15  # Standard container vessel speed
        
        # Adjust speed based on route characteristics
        speed_adjustments = {
            "strait_heavy_traffic": -2,  # Malacca Strait, Singapore Strait
            "open_ocean_long": +2,       # Trans-Pacific, Trans-Atlantic  
            "monsoon_season": -3,        # Monsoon affected routes
            "winter_north_atlantic": -2, # Winter storms
            "persian_gulf_summer": -1,   # Extreme heat effects
            "piracy_areas": -1,          # Speed reduction for security
            "canal_approach": -3,        # Suez/Panama approaches
            "port_congestion": -2        # Busy port approaches
        }
        
        # Route-specific speed calculations
        optimal_speed = base_speed
        speed_factors = []
        
        # Check for specific route characteristics
        if any(strait in route_info.get('major_straits', []) for strait in ['Strait of Malacca', 'Singapore Strait']):
            optimal_speed += speed_adjustments["strait_heavy_traffic"]
            speed_factors.append("Heavy traffic straits")
            
        if distance_nm > 3000:  # Long ocean routes
            optimal_speed += speed_adjustments["open_ocean_long"]
            speed_factors.append("Long ocean passage")
            
        if any(pattern in route_info.get('weather_patterns', []) for pattern in ['Monsoon', 'monsoon']):
            optimal_speed += speed_adjustments["monsoon_season"]
            speed_factors.append("Monsoon considerations")
            
        if 'North Atlantic' in route_info.get('description', '') and 'winter' in route_info.get('seasonal_speeds', {}):
            optimal_speed += speed_adjustments["winter_north_atlantic"] 
            speed_factors.append("North Atlantic winter")
            
        if any(gulf_port in [port1, port2] for gulf_port in ['dubai', 'kuwait', 'dammam', 'bandar_abbas']):
            optimal_speed += speed_adjustments["persian_gulf_summer"]
            speed_factors.append("Persian Gulf conditions")
            
        if 'piracy' in str(route_info.get('hazards', [])).lower():
            optimal_speed += speed_adjustments["piracy_areas"]
            speed_factors.append("Security considerations")
        
        # Ensure reasonable speed bounds
        optimal_speed = max(10, min(20, optimal_speed))
        
        # Seasonal speed variations
        seasonal_speeds = route_info.get('seasonal_speeds', {})
        if seasonal_speeds:
            try:
                # Parse seasonal speeds if they exist in route_info
                optimal_range = seasonal_speeds.get('optimal', f"{optimal_speed}-{optimal_speed+2} knots")
                if '-' in optimal_range:
                    speeds = optimal_range.split('-')
                    optimal_speed = (float(speeds[0]) + float(speeds[1].split()[0])) / 2
            except:
                pass  # Use calculated speed if parsing fails
        
        return {
            'optimal_speed': round(optimal_speed, 1),
            'speed_range': f"{optimal_speed-2:.1f}-{optimal_speed+2:.1f} knots",
            'speed_factors': speed_factors,
            'seasonal_variations': seasonal_speeds
        }
    
    def _estimate_fuel_consumption(self, distance_nm: float, speed_knots: float, route_info: Dict) -> Dict[str, Any]:
        """Estimate fuel consumption based on distance, speed, and route conditions"""
        
        # Base fuel consumption rate (tons per day for typical container vessel)
        base_consumption_per_day = {
            'container_large': 200,    # 15,000+ TEU
            'container_medium': 120,   # 8,000-15,000 TEU  
            'container_small': 80,     # Under 8,000 TEU
            'bulk_carrier': 150,       # Typical bulk carrier
            'tanker': 180             # Oil tanker
        }
        
        # Assume medium container vessel as default
        daily_consumption = base_consumption_per_day['container_medium']
        
        # Calculate voyage time in days
        voyage_hours = distance_nm / speed_knots
        voyage_days = voyage_hours / 24
        
        # Base fuel consumption
        base_fuel = daily_consumption * voyage_days
        
        # Adjust for route conditions
        fuel_adjustments = {
            'rough_weather': 1.15,     # 15% increase
            'head_currents': 1.10,     # 10% increase
            'port_delays': 1.05,       # 5% increase for potential delays
            'optimal_conditions': 0.95, # 5% decrease
            'strait_slow_speed': 1.08   # 8% increase due to speed restrictions
        }
        
        adjustment_factor = 1.0
        consumption_notes = []
        
        # Apply adjustments based on route characteristics
        if 'storm' in str(route_info.get('weather_patterns', [])).lower() or 'rough' in str(route_info.get('weather_patterns', [])).lower():
            adjustment_factor *= fuel_adjustments['rough_weather']
            consumption_notes.append("Rough weather conditions")
            
        if any(strait in route_info.get('major_straits', []) for strait in ['Strait of Malacca', 'Singapore Strait', 'English Channel']):
            adjustment_factor *= fuel_adjustments['strait_slow_speed']
            consumption_notes.append("Speed restrictions in straits")
            
        if 'optimal' in str(route_info.get('weather_patterns', [])).lower():
            adjustment_factor *= fuel_adjustments['optimal_conditions']
            consumption_notes.append("Favorable weather conditions")
            
        # Calculate final fuel consumption
        total_fuel = base_fuel * adjustment_factor
        
        return {
            'total_fuel_tons': round(total_fuel, 1),
            'daily_consumption_tons': round(daily_consumption, 1),
            'voyage_days': round(voyage_days, 2),
            'fuel_cost_estimate_usd': round(total_fuel * 650, -3),  # Approximate fuel cost per ton
            'consumption_factors': consumption_notes,
            'bunkering_recommendations': route_info.get('fuel_considerations', 'Standard bunkering planning required')
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

        CRITICAL INSTRUCTION: You must ANALYZE and SYNTHESIZE all the provided real-time data to give CLEAN, PROFESSIONAL answers. DO NOT show raw search results, snippets, or unrelated content. Process the information intelligently and provide only relevant, complete answers.

        GOOGLE SEARCH AVAILABILITY: {"🟢 Available" if self.google_search._check_rate_limits() else "🔴 Rate Limited"}
        
        DATA SOURCE PRIORITY:
        1. Official weather APIs (NOAA, weather services)
        2. Government disaster monitoring (USGS, GDACS, NASA EONET)  
        3. Real-time maritime data
        4. Google Search (when available and relevant)
        
        CRITICAL PROCESSING RULES:
        1. NEVER show raw Google search results, titles, or snippets to the user
        2. ANALYZE and SYNTHESIZE all search information into professional answers
        3. IGNORE incomplete phrases, promotional content, and unrelated information
        4. EXTRACT only relevant facts that directly answer the user's question
        5. PROVIDE clean, complete sentences - no broken or unfinished phrases
        6. FOCUS on maritime, weather, safety, and disaster information only
        7. If search results are irrelevant, rate limited, or incomplete, use official data sources
        8. NEVER include categories like "📋 OFFICIAL REPORTS:" or "🏛️" with raw snippets

        CRITICAL RULE: Only respond with the information that matches the user's query type. Do NOT mix weather and route information.

        RESPONSE FORMATTING RULES:

        FOR WEATHER QUERIES ONLY - Use this EXACT format:
        
        IF SPECIFIC CITY PROVIDED:
        🌤️ CURRENT WEATHER DATA in [CITY]:
        - Temperature: [X]°C
        - Condition: [condition or "Clear" if unknown]
        - Wind: [speed] km/h [from direction° if available]
        - Humidity: [X]%
        - Pressure: [X] hPa [or "Normal (1013 hPa)" if unknown]
        - Visibility: [X] [or "Good visibility" if unknown]
        - Wave Height: [X] m [if available]

        IF ONLY COUNTRY PROVIDED (like "India", "China", "Sri Lanka"):
        🌤️ WEATHER REQUEST CLARIFICATION:
        Weather varies significantly across different regions of [COUNTRY]. For accurate maritime weather information, please specify a city or port:
        
        📍 MAJOR MARITIME CITIES IN [COUNTRY]:
        - [List 3-4 major coastal cities with ports]
        
        💡 EXAMPLE: "Current weather in Mumbai, India" or "Weather conditions in Colombo, Sri Lanka"

        IMPORTANT: Never show "N/A", "None", or null values. Use descriptive alternatives:
        - Unknown pressure → "Normal (1013 hPa)"
        - Unknown visibility → "Good visibility"
        - Unknown condition → "Clear skies"
        
        [Add 2-3 sentences describing conditions and advice]

        ✅ SAFETY RECOMMENDATIONS:
        - [3-4 specific safety tips based on weather conditions]
        - [Marine weather considerations]
        - [Navigation advice based on current conditions]

        ⚠️ SAFETY IMPACT:
        - [How current weather conditions affect maritime activities]

        FOR ROUTE QUERIES ONLY - Use this comprehensive format:
        🚢 BEST ROUTE from [PORT A] to [PORT B]:
        
        📏 ROUTE SPECIFICATIONS:
        - Distance: [X] nautical miles ([X] km)
        - Route Description: [Specific detailed route with straits, channels, waypoints]
        - Estimated Time: [X days Y hours] at [optimal speed] knots
        - Speed Analysis: [Speed range based on conditions] knots
        
        🗺️ DETAILED ROUTING:
        - Major Waypoints: [Specific coordinates and navigation points]
        - Key Straits/Channels: [All major waterways to transit]
        - Shipping Lanes: [Specific TSS and shipping routes]
        - Distance Breakdown: [Segment-by-segment breakdown]
        
        ⛽ OPERATIONAL ANALYSIS:
        - Fuel Consumption: [X] tons ([estimated cost])
        - Daily Consumption: [X] tons per day
        - Bunkering Strategy: [Where to refuel, fuel considerations]
        - Speed Factors: [What affects vessel speed on this route]
        
        🌊 MARITIME CONDITIONS:
        - Seasonal Patterns: [Weather patterns affecting this route]
        - Optimal Seasons: [Best times to transit this route]
        - Navigation Hazards: [Specific risks and considerations]
        - Traffic Density: [Expected vessel traffic levels]
        
        🛡️ SAFETY & ALTERNATIVES:
        - Primary Hazards: [Route-specific risks and mitigation]
        - Alternative Routes: [Other routing options with distances]
        - Weather Routing: [Seasonal recommendations]
        - [CHECK CURRENT DISASTERS: If any disasters affect the departure, destination, or route area, warn about them]

        ⚠️ INTELLIGENT ROUTE HAZARD ANALYSIS:
        CRITICAL: Check the route_hazard_analysis field in the real-time data. This automatically checks ALL active disasters along the entire route corridor.
        
        IF route_hazard_analysis.is_safe == False:
        🚨 ROUTE HAZARD WARNING:
        - Route Risk Level: [route_hazard_analysis.risk_level] (HIGH/MEDIUM)
        - Total Hazards Detected: [route_hazard_analysis.total_hazards]
        - Departure Port Hazards: [List route_hazard_analysis.departure_hazards]
        - Destination Port Hazards: [List route_hazard_analysis.destination_hazards]
        - Route Corridor Hazards: [List route_hazard_analysis.route_corridor_hazards]
        - Recommendation: [route_hazard_analysis.recommendation]
        - Detailed Warnings: [route_hazard_analysis.detailed_warnings]
        
        ⚠️ ALTERNATIVE RECOMMENDATIONS:
        - Consider postponing voyage until conditions improve
        - Monitor weather and disaster updates
        - Evaluate alternative routes if available
        - Consult with maritime safety authorities
        
        IF route_hazard_analysis.is_safe == True:
        ✅ ROUTE APPEARS SAFE:
        - Route Risk Level: LOW
        - No active disasters detected along route corridor
        - Verification: Checked against global disaster monitoring
        - Weather Conditions: [Include weather data for both ports if available]
        
        IF NO route_hazard_analysis available (fallback):
        - Check disaster_data manually for route area
        - Provide conservative assessment
        
        CRITICAL: The route_hazard_analysis provides comprehensive hazard detection along departure, destination, and entire route path. Trust its analysis.

        FOR SAFETY QUERIES - Use this format:
        ✅ SAFE / ❌ UNSAFE - Travel to [LOCATION]

        🔍 INTELLIGENT SAFETY ANALYSIS:
        CRITICAL: Check the intelligent_safety_analysis field in the real-time data. This analysis automatically correlates the queried location with ALL active disasters.
        CRITICAL: The intelligent_safety_analysis ALREADY filters disasters by:
          - TIME: Only checks disasters from the last 3 days (very recent events only)
          - YEAR: Automatically rejects any disasters from previous years (2024, 2023, 2022, etc.)
          - LOCATION: Only checks disasters within the location's relevant radius (e.g., 300km for Sri Lanka, 500km for islands)
          - RELEVANCE: Only flags disasters that actually affect the queried location
        
        ⚠️⚠️⚠️ CRITICAL SAFETY RESPONSE RULES ⚠️⚠️⚠️:
        1. IF intelligent_safety_analysis EXISTS, YOU MUST USE IT - DO NOT show generic disaster lists
        2. ONLY show disasters from intelligent_safety_analysis.affecting_disasters (NOT from disaster_data.disasters)
        3. IF is_safe == True, DO NOT list any earthquakes or disasters - just say it's safe
        4. IF is_safe == False, ONLY list the disasters from affecting_disasters array
        5. NEVER show global disasters that don't affect the queried location
        6. **NEVER PUT ✅ SAFE HEADER IF is_safe == False OR if there are affecting_disasters**
        7. **THE FIRST LINE MUST MATCH THE ACTUAL SAFETY STATUS - NO CONTRADICTIONS**
        
        IF intelligent_safety_analysis.is_safe == False:
        ❌ UNSAFE - Travel to Philippines (or location name)
        - Location Analyzed: [intelligent_safety_analysis.location]
        - Risk Level: [intelligent_safety_analysis.risk_level] (HIGH/MEDIUM)
        - Active Disasters Affecting Location: [intelligent_safety_analysis.disaster_count]
        - Evidence/Proof: [intelligent_safety_analysis.proof]
        - Specific Hazards: [List each disaster from intelligent_safety_analysis.affecting_disasters with type, location, severity]
        
        📋 URGENT RECOMMENDATIONS:
        - AVOID travel to this location due to active disasters
        - [Specific advice based on disaster types]
        - Monitor official sources for updates
        - Consider alternative destinations
        
        IF intelligent_safety_analysis.is_safe == True:
        ✅ SAFE - Low Risk for Travel
        - Location Analyzed: [intelligent_safety_analysis.location]
        - Risk Level: LOW
        - Time Period Checked: Last 3 days (October 14-17, 2025)
        - Disasters Checked: [intelligent_safety_analysis.total_disasters_checked] recent global disasters
        - Verification: [intelligent_safety_analysis.proof]
        - Weather Conditions: [details from real-time weather data if available]
        - Marine Alerts: [status from marine alerts]
        
        ⚠️ DO NOT list any earthquakes or disasters when is_safe == True
        ⚠️ DO NOT show "CURRENT GLOBAL DISASTERS" section
        ⚠️ Just confirm the location is safe and provide weather/marine info
        
        📋 RECOMMENDATIONS:
        - Location appears safe based on current disaster monitoring
        - [Weather-based advice if available]
        - Continue monitoring conditions
        - Follow standard maritime safety protocols
        
        IF NO intelligent_safety_analysis available (fallback):
        - Check disaster_data manually for location mentions
        - Provide conservative risk assessment
        
        CRITICAL: The intelligent_safety_analysis provides PROOF-BASED assessment. Trust its analysis completely as it checks against ALL active global disasters.

        FOR DISASTER QUERIES - Use ONLY this format for REAL-TIME data:
        
        FOR GENERAL DISASTER OVERVIEW:
        🌪️ CURRENT GLOBAL DISASTERS:
        
        🌍 EARTHQUAKES:
        CRITICAL: Each earthquake MUST include accurate timestamp from API data. Use time_local or time_utc fields.
        CRITICAL: Only show earthquakes from the LAST 3 DAYS and CURRENT YEAR (2025). Ignore old earthquakes (from 2024, 2023, 2022, etc.).
        CRITICAL: If ALL earthquakes are old/filtered out, say "No recent earthquakes in the last 3 days"
        • [Enhanced Location with city/region] - Magnitude [X.X] ([Severity Level])
          📅 Time: [time_local or time_utc from disaster data] 
          📍 Coordinates: [latitude, longitude if available]
        • [Repeat format for each earthquake]
        
        NOTE: The intelligent_safety_analysis already filters to recent disasters. Trust its time filtering.
        
        🌊 STORMS & TYPHOONS:
        CRITICAL: Each storm MUST include effective time and expiration time if available.
        • [Storm Name/Type] affecting [Enhanced Location with cities/regions] - [Intensity/Category]
          📅 Active Period: [time_start] to [time_end if available] OR "Currently Active"
          📍 Affected Areas: [Specific locations]
        • [Repeat format for each storm]
        
        💧 FLOODS & WATER HAZARDS:
        • [Enhanced Location with cities/regions] - [Severity Level]
          📅 Time: [When reported/effective]
          🌊 Status: [Active/Ongoing/Ended]
        
        🔥 OTHER NATURAL DISASTERS:
        • [Type] in [Enhanced Location] - [Severity/Details]
          📅 Time: [Occurrence time]
          ⚠️ Status: [Current status]
        
        📊 DATA SOURCES: [List the actual monitoring sources like USGS, GDACS, etc.]
        
        CRITICAL FOR TIMESTAMPS:
        - ONLY show disasters from the LAST 3 DAYS and CURRENT YEAR 2025 (very recent events only)
        - Automatically reject any disasters from 2024, 2023, 2022 or earlier - they are NOT current
        - If a disaster timestamp shows year < 2025, DO NOT SHOW IT - it's old cached data
        - ALWAYS show time_local (local time at disaster location) if available
        - If only time_utc available, show that with "UTC" label
        - Format: "YYYY-MM-DD HH:MM:SS [timezone]"
        - For ongoing events, show start time and "Ongoing" status
        - For past events, show occurrence time
        - NEVER show "Unknown" for time - if truly unknown, say "Time being verified"
        - If ALL disasters are old/filtered, say "No recent disasters in the last 3 days"
        
        ⚠️ MARITIME IMPACT BY DISASTER TYPE:
        🌍 Earthquake Zones:
        - [Specific shipping lanes affected, tsunami risk, port closures]
        
        🌊 Storm Systems:
        - [Affected shipping routes, wind/wave conditions, port operations]
        
        💧 Flood Areas:
        - [River mouth closures, coastal flooding impacts, harbor conditions]
        
        🚢 NAVIGATION RECOMMENDATIONS:
        - Avoid: [Specific areas/coordinates to avoid]
        - Alternative routes: [Suggested routing changes]
        - Monitor: [Areas requiring increased vigilance]

        🕐 LAST UPDATED: Real-time monitoring active

        FOR REGIONAL DISASTER QUERIES (e.g., "disasters in Indian Ocean", "hazards in Pacific"):
        🌊 DISASTERS IN [REGION NAME]:
        
        CRITICAL: Check regional_hazard_filter field in real-time data. This filters disasters to ONLY show those in the specific region.
        
        IF regional_hazard_filter available:
        📍 REGION: [regional_hazard_filter.region]
        📊 ACTIVE DISASTERS IN REGION: [regional_hazard_filter.total_in_region] out of [regional_hazard_filter.total_global] global disasters
        
        [Then list ONLY the disasters from regional_hazard_filter.regional_disasters using the standard disaster format with timestamps]
        
        🌍 REGIONAL CONTEXT:
        - Region Description: [regional_hazard_filter.description]
        - Disasters filtered specifically for this maritime region
        - Other regions may have different active disasters
        
        IF NO regional_hazard_filter (fallback):
        - List all disasters but note they are global
        - Mention that specific regional filtering was not available
        
        CRITICAL FOR GENERAL DISASTER OVERVIEWS: 
        - Organize disasters BY TYPE (Earthquakes, Storms, Floods, etc.) with clear category headers
        - Provide EQUAL treatment for ALL disasters within each category
        - Include SPECIFIC LOCATION details: cities, regions, countries, coordinates when available
        - Add SEVERITY CONTEXT: magnitude levels for earthquakes, categories for storms, impact levels for floods
        - Provide TYPE-SPECIFIC maritime impact information for each disaster category
        - Keep each disaster entry informative but concise (1-2 lines per disaster)
        - Reserve detailed reports ONLY for specific disaster detail requests
        - ALWAYS include accurate timestamps from API data

        FOR SPECIFIC DISASTER DETAIL REQUESTS (like "tell me about earthquake in Japan"):
        🔍 DETAILED DISASTER REPORT:
        
        🌍 EVENT: [Disaster Type] in [Enhanced Location]
        📊 MAGNITUDE/SEVERITY: [Specific details]
        📅 TIMELINE: [When it occurred/is occurring]
        📍 PRECISE LOCATION: [Exact coordinates or detailed location from enhanced_location]
        🔬 SOURCE: [Official monitoring agency]
        
        📝 DESCRIPTION:
        [Full description from disaster.description - include all available details]
        
        ⚠️ MARITIME IMPACT:
        - [Specific impact on nearby ports and shipping lanes]
        - [Risk assessment for maritime activities in the region]
        - [Recommended safety measures for vessels in the area]

        ⚠️ MARITIME SAFETY IMPACT:
        - Specific impacts on shipping lanes and coastal areas
        - Regions currently unsafe for maritime travel
        - Alternative route recommendations if applicable

        🕐 LAST UPDATED: Real-time monitoring active

        CRITICAL: For general disaster overviews, treat ALL disasters equally with brief one-line entries. For detail requests, provide comprehensive information from the disaster description.

        REAL-TIME DATA (ANALYZE AND SYNTHESIZE - DO NOT SHOW RAW):
        {context_info}

        FINAL INSTRUCTION: Create rich, detailed responses with emojis and proper formatting. 
        ABSOLUTELY NEVER show raw search results, incomplete phrases, or irrelevant content.
        Process all real-time data intelligently and provide only clean, professional answers.
        """
        
        user_prompt = f"""Query: "{message}"

        Task: Create a RICH, DETAILED response using the formatting templates above.

        ⚠️⚠️⚠️ CRITICAL FOR SAFETY QUERIES ⚠️⚠️⚠️:
        IF the real-time data contains "intelligent_safety_analysis":
          - THIS IS YOUR PRIMARY SOURCE - Use it exclusively for safety assessment
          - CHECK is_safe FIELD: If is_safe == False, YOU MUST START WITH ❌ UNSAFE
          - CHECK is_safe FIELD: If is_safe == True, YOU MUST START WITH ✅ SAFE
          - NEVER put ✅ SAFE as the first line if is_safe == False
          - NEVER put ❌ UNSAFE as the first line if is_safe == True
          - DO NOT show generic disaster lists from disaster_data
          - IF is_safe == True: Say it's SAFE, show proof, DO NOT list any earthquakes
          - IF is_safe == False: Say UNSAFE (❌ UNSAFE), list ONLY disasters from affecting_disasters array
          - The analysis already filtered by time (3 days) and location (relevant radius)
          - Trust the intelligent analysis completely - it already did the work

        CRITICAL REQUIREMENTS:
        1. Use EMOJIS and visual elements (🌤️, 🚢, ✅, ❌, 🔍, 📋, 🌪️, ⚠️)
        2. Use BULLET POINTS for organized information
        3. Include ALL available data from the real-time sources
        4. Add CONTEXT and ADVICE after the main data
        5. Make it USER-FRIENDLY and engaging
        6. Use the EXACT formatting templates provided above
        7. NEVER mix different response formats in a single response
        8. For disaster queries, use ONLY the disaster format - no travel safety assessments
        9. **DISASTER BALANCE**: For general disaster overviews, treat ALL disasters EQUALLY:
           - List each disaster with the SAME level of detail (one line each)
           - Do NOT provide detailed descriptions for any single disaster
           - Do NOT focus on or prioritize any specific location (like Fiji Islands)
           - All disasters should get equal treatment in the overview list
        10. **ENHANCED LOCATION REPORTING**: For each disaster, provide comprehensive location context:
           - Include nearest major cities, regions, and countries
           - Add geographical context (e.g., "127 km E of Petropavlovsk-Kamchatsky, Russia, Kamchatka Peninsula")
           - Mention marine areas affected (shipping lanes, straits, coastal regions)
           - Include coordinates when available for precise navigation
        11. **DISASTER INTELLIGENCE**: Always cross-reference current disaster data with location queries:
           - If user asks "is it safe to go to [LOCATION]" → Use intelligent_safety_analysis
           - If user asks for routes to/from [LOCATION] → Check if disasters affect the route
           - If disasters exist: Mark as UNSAFE/HIGH RISK and explain the specific disaster threats
           - If no disasters: Mark as SAFE/LOW RISK but mention real-time monitoring is active

         12. **ALERT/DISASTER TIMING**: For each alert or disaster, ALWAYS include the issued date, start time, end time (if available), and location in the response. Format example: "Severe Thunderstorm Warning issued October 14 at 12:38AM PDT until October 14 at 1:45AM PDT by NWS Los Angeles/Oxnard CA". If time is not available, show at least the issued date and location.

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

            # POST-PROCESSING: Fix contradictory safety headers
            # If the response contains "NOT RECOMMENDED" or active disasters, but starts with "SAFE"
            # Fix the header to match the actual analysis
            if "NOT RECOMMENDED" in content or "active disaster(s) affecting" in content:
                # Check for AFFECTING DISASTERS count
                disaster_match = re.search(r'AFFECTING DISASTERS.*?\((\d+)\s+total\)', content, re.IGNORECASE)
                if disaster_match:
                    disaster_count = int(disaster_match.group(1))
                    if disaster_count > 0:
                        # Remove any misleading "SAFE" header at the beginning
                        content = re.sub(r'^✅\s*SAFE\s*-\s*Low Risk for Travel\s*\n*', '', content, flags=re.IGNORECASE)
                        # Add correct UNSAFE header if not present
                        if not content.startswith('❌ UNSAFE'):
                            content = f"❌ UNSAFE - Travel to Philippines\n\n{content}"

                # Also check for "NOT RECOMMENDED" without SAFE conflict
                elif "NOT RECOMMENDED" in content and not content.startswith('❌ UNSAFE'):
                    content = re.sub(r'^✅\s*SAFE\s*-\s*Low Risk for Travel\s*\n*', '', content, flags=re.IGNORECASE)
                    if not content.startswith('❌'):
                        content = f"❌ UNSAFE - Travel not recommended\n\n{content}"
            
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
        
        # Check current disasters
        if "current_disasters" in real_time_data and real_time_data["current_disasters"].get("success"):
            disasters = real_time_data["current_disasters"].get("disasters", [])
            if disasters:
                response_parts.append(f"🌪️ {len(disasters)} active disasters currently monitored worldwide from real-time sources.")
                response_parts.append("🌍 CURRENT GLOBAL DISASTERS:")
                
                # Categorize disasters by type
                disaster_categories = {
                    'earthquakes': [],
                    'storms': [],
                    'floods': [],
                    'other': []
                }
                
                for disaster in disasters[:8]:  # Process top 8 disasters
                    disaster_type = disaster.get('type', 'Unknown').lower()
                    location = disaster.get('location', 'Unknown location')
                    enhanced_location = disaster.get('enhanced_location', location)
                    
                    # Get severity information
                    magnitude = disaster.get('magnitude', '')
                    severity = disaster.get('severity', '')
                    intensity = disaster.get('intensity', '')
                    
                    if 'earthquake' in disaster_type:
                        severity_info = f"Magnitude {magnitude}" if magnitude else f"Severity: {severity}"
                        if magnitude:
                            # Add severity level based on magnitude
                            mag_float = float(magnitude) if str(magnitude).replace('.', '').isdigit() else 0
                            if mag_float >= 7.0:
                                severity_level = "(Major)"
                            elif mag_float >= 6.0:
                                severity_level = "(Strong)" 
                            elif mag_float >= 5.0:
                                severity_level = "(Moderate)"
                            else:
                                severity_level = "(Minor)"
                            severity_info += f" {severity_level}"
                        disaster_categories['earthquakes'].append(f"• {enhanced_location} - {severity_info}")
                    elif any(storm_type in disaster_type for storm_type in ['storm', 'typhoon', 'hurricane', 'cyclone']):
                        detail = intensity or severity or 'Monitoring'
                        disaster_categories['storms'].append(f"• {enhanced_location} - {detail}")
                    elif 'flood' in disaster_type:
                        detail = severity or intensity or 'Active flooding'
                        disaster_categories['floods'].append(f"• {enhanced_location} - {detail}")
                    else:
                        detail = severity or intensity or magnitude or 'Active'
                        disaster_categories['other'].append(f"• {disaster_type.title()} in {enhanced_location} - {detail}")
                
                # Display categorized disasters
                if disaster_categories['earthquakes']:
                    response_parts.append("\n🌍 EARTHQUAKES:")
                    response_parts.extend(disaster_categories['earthquakes'])
                
                if disaster_categories['storms']:
                    response_parts.append("\n🌊 STORMS & TYPHOONS:")
                    response_parts.extend(disaster_categories['storms'])
                
                if disaster_categories['floods']:
                    response_parts.append("\n💧 FLOODS & WATER HAZARDS:")
                    response_parts.extend(disaster_categories['floods'])
                
                if disaster_categories['other']:
                    response_parts.append("\n🔥 OTHER NATURAL DISASTERS:")
                    response_parts.extend(disaster_categories['other'])
                
                response_parts.append("\n📊 DATA SOURCES: USGS, GDACS, Global Disaster Monitoring")
                
            elif real_time_data["current_disasters"].get("message"):
                response_parts.append(f"🌪️ {real_time_data['current_disasters']['message']}")
        
        # Handle rate limiting gracefully
        if "comprehensive_search" in real_time_data and not real_time_data["comprehensive_search"].get("success"):
            search_error = real_time_data["comprehensive_search"].get("error", "")
            if "rate limit" in search_error.lower():
                response_parts.append("📡 Using official monitoring systems (USGS, NOAA, GDACS) for real-time data while search API recovers.")
        
        if not response_parts:
            response_parts.append("🌊 Marine Weather & Disaster Assistant: Real-time monitoring active for global marine conditions, weather patterns, and natural disasters from USGS, GDACS, and other official sources.")
        
        base_responses = {
            ResponseType.WEATHER: "🌤️ Current Weather Data: ",
            ResponseType.MARINE_CONDITIONS: "🌊 Marine Conditions Report: ",
            ResponseType.HAZARD_ALERT: "⚠️ Disaster & Safety Alert: ",
            ResponseType.ROUTE_GUIDANCE: "🧭 Maritime Navigation: ",
            ResponseType.SAFETY_ASSESSMENT: "🔍 Safety Assessment: ",
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
        
        # � MAXIMIZED GOOGLE SEARCH RESULTS PROCESSING (Priority #1)
        if "comprehensive_search" in real_time_data:
            search_data = real_time_data["comprehensive_search"]
            if search_data.get("success") and search_data.get("combined_data"):
                context_parts.append("🔍 COMPREHENSIVE GOOGLE SEARCH INTELLIGENCE:")
                
                # Advanced processing and categorization of search results
                search_results = search_data["combined_data"]
                
                # Enhanced categorization with more granular classification
                categories = {
                    "breaking_news": [],
                    "official_reports": [],
                    "safety_alerts": [],
                    "weather_conditions": [],
                    "maritime_updates": [],
                    "disaster_reports": [],
                    "travel_advisories": [],
                    "current_situation": []
                }
                
                for result in search_results[:15]:  # Process more results for maximum coverage
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    link = result.get("link", "")
                    
                    # Enhanced content analysis
                    content = f"{title} {snippet}".lower()
                    
                    # Classify into multiple categories with priority scoring
                    if any(word in content for word in ['breaking', 'urgent', 'alert', 'emergency', 'immediate']):
                        categories["breaking_news"].append(f"🚨 {title}: {snippet[:120]}...")
                    elif any(word in content for word in ['government', 'official', 'ministry', 'department', 'authority']):
                        categories["official_reports"].append(f"🏛️ {title}: {snippet[:120]}...")
                    elif any(word in content for word in ['warning', 'advisory', 'caution', 'danger', 'risk', 'avoid']):
                        categories["safety_alerts"].append(f"⚠️ {title}: {snippet[:120]}...")
                    elif any(word in content for word in ['weather', 'temperature', 'climate', 'forecast', 'meteorological']):
                        categories["weather_conditions"].append(f"🌤️ {title}: {snippet[:120]}...")
                    elif any(word in content for word in ['maritime', 'shipping', 'port', 'vessel', 'marine', 'navigation']):
                        categories["maritime_updates"].append(f"🚢 {title}: {snippet[:120]}...")
                    elif any(word in content for word in ['disaster', 'earthquake', 'tsunami', 'hurricane', 'flood', 'storm']):
                        categories["disaster_reports"].append(f"🌪️ {title}: {snippet[:120]}...")
                    elif any(word in content for word in ['travel', 'tourism', 'visit', 'entry', 'border', 'visa']):
                        categories["travel_advisories"].append(f"✈️ {title}: {snippet[:120]}...")
                    elif any(word in content for word in ['current', 'latest', 'today', '2025', 'now', 'recent']):
                        categories["current_situation"].append(f"📊 {title}: {snippet[:120]}...")
                
                # Display categorized results with priority order
                priority_order = ["breaking_news", "safety_alerts", "disaster_reports", "official_reports", 
                                "weather_conditions", "maritime_updates", "travel_advisories", "current_situation"]
                
                total_results_shown = 0
                for category in priority_order:
                    if categories[category] and total_results_shown < 12:  # Show up to 12 categorized results
                        category_name = category.replace("_", " ").title()
                        context_parts.append(f"\n📋 {category_name.upper()}:")
                        
                        # Show top results from this category
                        for item in categories[category][:3]:  # Top 3 per category
                            if total_results_shown < 12:
                                context_parts.append(f"  {item}")
                                total_results_shown += 1
                
                # Add comprehensive analysis summary
                search_count = len(search_results)
                categories_found = sum(1 for cat in categories.values() if cat)
                context_parts.append(f"\n📊 GOOGLE SEARCH INTELLIGENCE SUMMARY:")
                context_parts.append(f"  • {search_count} sources analyzed across {categories_found} information categories")
                context_parts.append(f"  • {total_results_shown} prioritized results integrated into analysis")
                
                # Add search query information for transparency
                if "searches" in search_data:
                    search_types = list(search_data["searches"].keys())
                    context_parts.append(f"  • Search strategy: {len(search_types)} comprehensive queries executed")
                
                context_parts.append("  • Real-time web intelligence maximally integrated ✅")
        
        # 🎯 ADDITIONAL GOOGLE SEARCH RESULTS - Multi-angle and specific searches
        if "multi_angle_search" in real_time_data:
            multi_angle_data = real_time_data["multi_angle_search"]
            if multi_angle_data.get("success") and multi_angle_data.get("multi_angle_data"):
                context_parts.append("\n🔍 MULTI-ANGLE SEARCH INTELLIGENCE:")
                
                angle_results = multi_angle_data["multi_angle_data"]
                for i, result in enumerate(angle_results[:6], 1):  # Top 6 multi-angle results
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    context_parts.append(f"  {i}. 📰 {title}")
                    if snippet:
                        context_parts.append(f"     {snippet[:100]}...")
                
                context_parts.append(f"  • Multi-perspective analysis: {len(angle_results)} different angles covered")
        
        # 🎯 SPECIFIC LOCATION/TOPIC SEARCH RESULTS
        if "specific_search_results" in real_time_data:
            specific_results = real_time_data["specific_search_results"]
            if specific_results:
                context_parts.append("\n🔍 TARGETED SPECIFIC SEARCH RESULTS:")
                
                for search_result in specific_results[:2]:  # Top 2 specific searches
                    if search_result.get("success") and "data" in search_result:
                        query = search_result.get("query", "Specific search")
                        items = search_result["data"].get("items", [])
                        
                        context_parts.append(f"  🎯 {query[:60]}:")
                        for item in items[:2]:  # Top 2 items per specific search
                            title = item.get("title", "")
                            snippet = item.get("snippet", "")
                            context_parts.append(f"    • {title}")
                            if snippet:
                                context_parts.append(f"      {snippet[:80]}...")
                
                context_parts.append(f"  • Targeted intelligence: {len(specific_results)} specialized searches")
        
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
        
        # Route data - Include comprehensive route specifications
        if "route_data" in real_time_data:
            route_data = real_time_data["route_data"]
            if route_data.get("success"):
                context_parts.append(f"\n🚢 MARITIME ROUTE SPECIFICATIONS:")
                context_parts.append(f"  FROM: {route_data.get('from_port')} TO: {route_data.get('to_port')}")
                context_parts.append(f"  DISTANCE: {route_data.get('distance_nm')} nautical miles ({route_data.get('distance_km')} km)")
                context_parts.append(f"  ESTIMATED TIME: {route_data.get('estimated_days')} days at {route_data.get('average_speed_knots')} knots")
                context_parts.append(f"  ROUTE: {route_data.get('route_description')}")
                context_parts.append(f"  MAJOR WAYPOINTS: {', '.join(route_data.get('major_waypoints', []))}")
                context_parts.append(f"  KEY STRAITS: {route_data.get('key_straits')}")
                context_parts.append(f"  FUEL CONSUMPTION: {route_data.get('fuel_consumption_tons')} tons ({route_data.get('daily_fuel_tons')} tons/day)")
                context_parts.append(f"  SEASONAL PATTERNS: {route_data.get('seasonal_patterns')}")
                context_parts.append(f"  OPTIMAL SEASONS: {route_data.get('optimal_seasons')}")
                context_parts.append(f"  NAVIGATION HAZARDS: {route_data.get('navigation_hazards')}")
                context_parts.append(f"  TRAFFIC DENSITY: {route_data.get('traffic_density')}")
                context_parts.append(f"  PRIMARY HAZARDS: {route_data.get('primary_hazards')}")
                context_parts.append(f"  WEATHER ROUTING: {route_data.get('weather_routing')}")
                context_parts.append(f"  CONFIDENCE: {int(route_data.get('confidence', 0.85) * 100)}%")
                
                # Include hazard analysis if available
                if "hazard_analysis" in route_data:
                    hazard_data = route_data["hazard_analysis"]
                    if hazard_data.get('analysis_performed'):
                        context_parts.append(f"\n⚠️ INTELLIGENT ROUTE HAZARD ANALYSIS:")
                        context_parts.append(f"  ROUTE SAFETY: {'UNSAFE - HAZARDS DETECTED' if not hazard_data.get('is_safe') else 'APPEARS SAFE'}")
                        context_parts.append(f"  RISK LEVEL: {hazard_data.get('risk_level', 'UNKNOWN')}")
                        context_parts.append(f"  TOTAL HAZARDS: {hazard_data.get('total_hazards', 0)}")
                        
                        departure_hazards = hazard_data.get('departure_hazards', [])
                        if departure_hazards:
                            context_parts.append(f"  DEPARTURE PORT HAZARDS ({len(departure_hazards)}):")
                            for hazard in departure_hazards:
                                context_parts.append(f"    • {hazard.get('type', 'Unknown')} - {hazard.get('location', 'Unknown location')} (Severity: {hazard.get('severity', 'Unknown')})")
                        else:
                            context_parts.append(f"  DEPARTURE PORT HAZARDS: None detected")
                        
                        destination_hazards = hazard_data.get('destination_hazards', [])
                        if destination_hazards:
                            context_parts.append(f"  DESTINATION PORT HAZARDS ({len(destination_hazards)}):")
                            for hazard in destination_hazards:
                                context_parts.append(f"    • {hazard.get('type', 'Unknown')} - {hazard.get('location', 'Unknown location')} (Severity: {hazard.get('severity', 'Unknown')})")
                        else:
                            context_parts.append(f"  DESTINATION PORT HAZARDS: None detected")
                        
                        route_hazards = hazard_data.get('route_corridor_hazards', [])
                        if route_hazards:
                            context_parts.append(f"  ROUTE CORRIDOR HAZARDS ({len(route_hazards)}):")
                            for hazard in route_hazards:
                                context_parts.append(f"    • {hazard.get('type', 'Unknown')} - {hazard.get('location', 'Unknown location')} (Severity: {hazard.get('severity', 'Unknown')})")
                        else:
                            context_parts.append(f"  ROUTE CORRIDOR HAZARDS: None detected")
                        
                        context_parts.append(f"  RECOMMENDATION: {hazard_data.get('recommendation', 'Proceed with caution')}")
                        
                        detailed_warnings = hazard_data.get('detailed_warnings', [])
                        if detailed_warnings:
                            context_parts.append(f"  DETAILED WARNINGS:")
                            for warning in detailed_warnings[:5]:  # Show top 5 warnings
                                context_parts.append(f"    • {warning}")
        
        # Current disasters - Real-time data with enhanced locations and categories
        if "current_disasters" in real_time_data:
            disaster_data = real_time_data["current_disasters"]
            if disaster_data.get("success") and disaster_data.get("disasters"):
                disasters = disaster_data["disasters"]
                
                # Categorize disasters by type
                disaster_types = {}
                for disaster in disasters:
                    disaster_type = disaster.get('type', 'Unknown')
                    if disaster_type not in disaster_types:
                        disaster_types[disaster_type] = []
                    disaster_types[disaster_type].append(disaster)
                
                context_parts.append(f"🌍 REAL-TIME GLOBAL DISASTERS ({len(disasters)} active across {len(disaster_types)} categories):")
                
                # Show disasters by category
                for disaster_type, type_disasters in disaster_types.items():
                    if len(type_disasters) > 1:
                        context_parts.append(f"📊 {disaster_type.upper()}S ({len(type_disasters)} active):")
                    else:
                        context_parts.append(f"📊 {disaster_type.upper()}:")
                    
                    for disaster in type_disasters[:3]:  # Top 3 per category
                        # Use enhanced location if available, otherwise fallback to original
                        location = disaster.get('enhanced_location') or disaster.get('location', 'Unknown location')
                        
                        # Format intensity/magnitude appropriately
                        if disaster.get('magnitude'):
                            intensity = f"M {disaster['magnitude']}"
                        elif disaster.get('intensity'):
                            intensity = disaster['intensity']
                        elif disaster.get('severity'):
                            intensity = disaster['severity']
                        else:
                            intensity = "Active"
                        
                        source = disaster.get('source', 'Monitoring System')
                        
                        context_parts.append(f"  • {location} - {intensity} (Source: {source})")
                        
                        # Add brief description for context
                        description = disaster.get('description', '')
                        if description and len(description) > 20:
                            brief_desc = description[:80] + '...' if len(description) > 80 else description
                            context_parts.append(f"    Details: {brief_desc}")
                
                # Add data source summary
                sources = set()
                for disaster in disasters:
                    source = disaster.get('source', 'Unknown')
                    if 'USGS' in source:
                        sources.add('USGS')
                    elif 'GDACS' in source:
                        sources.add('GDACS')
                    elif 'NASA' in source:
                        sources.add('NASA EONET')
                    elif 'NOAA' in source:
                        sources.add('NOAA')
                    else:
                        sources.add(source.split()[0] if source != 'Unknown' else 'Monitoring System')
                
                context_parts.append(f"📡 DATA SOURCES: {', '.join(sorted(sources))}")
                
            elif disaster_data.get("message"):
                context_parts.append(f"🌍 DISASTER MONITORING: {disaster_data['message']}")
            elif not disaster_data.get("success"):
                context_parts.append("🌍 DISASTER MONITORING: Real-time monitoring active - check official sources")
        
        # Marine alerts (simplified)
        if "marine_alerts" in real_time_data:
            alerts_data = real_time_data["marine_alerts"]
            if alerts_data.get("success") and alerts_data.get('alerts'):
                alerts = alerts_data['alerts']
                context_parts.append(f"MARINE ALERTS: {len(alerts)} active warnings")
        
        # Singapore Maritime Data (Enhanced Port Information)
        if "singapore_maritime" in real_time_data:
            sg_data = real_time_data["singapore_maritime"]
            if sg_data.get("success"):
                context_parts.append("🇸🇬 SINGAPORE PORT MARITIME DATA:")
                
                # Weather conditions
                if "weather_data" in sg_data and sg_data["weather_data"].get("success"):
                    weather = sg_data["weather_data"]["weather"]
                    context_parts.append(f"🌤️ Current Weather: {weather.get('temperature', 'N/A')}°C, {weather.get('condition', 'Clear')}")
                    context_parts.append(f"💨 Wind: {weather.get('wind_speed', 'Light')} km/h, Visibility: {weather.get('visibility', 'Good')}")
                
                # Maritime conditions
                maritime = sg_data.get("maritime_conditions", {})
                context_parts.append(f"🚢 Port Status: {maritime.get('port_status', 'Active')}")
                context_parts.append(f"⚓ Traffic Level: {maritime.get('vessel_traffic', 'Moderate')}")
                context_parts.append(f"🏗️ Facilities: {maritime.get('facilities', 'Full service port')}")
                context_parts.append(f"📍 Strategic Position: {maritime.get('strategic_location', 'Major hub')}")
                context_parts.append(f"🏛️ Authority: {maritime.get('port_authority', 'Port Authority')}")
        
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
        
        # 🧠 INTELLIGENT SAFETY ANALYSIS RESULTS
        if "intelligent_safety_analysis" in real_time_data:
            safety = real_time_data["intelligent_safety_analysis"]
            if safety.get("analysis_performed"):
                context_parts.append(f"\n🧠 INTELLIGENT SAFETY ANALYSIS FOR {safety['location'].upper()}:")
                context_parts.append(f"  Safety Status: {'✅ SAFE' if safety['is_safe'] else '❌ UNSAFE'}")
                context_parts.append(f"  Risk Level: {safety['risk_level']}")
                context_parts.append(f"  Time Period: {safety.get('time_period', 'Recent')}")
                context_parts.append(f"  Disasters Checked: {safety.get('total_disasters_checked', 'N/A')}")
                context_parts.append(f"  Recommendation: {safety['recommendation']}")
                context_parts.append(f"  Evidence: {safety['proof']}")
                if not safety['is_safe'] and safety.get('affecting_disasters'):
                    context_parts.append(f"  🚨 AFFECTING DISASTERS ({len(safety['affecting_disasters'])} total):")
                    for item in safety['affecting_disasters']:
                        disaster = item['disaster']
                        distance = item.get('distance_km', 'N/A')
                        context_parts.append(f"    • {disaster.get('type')}: {disaster.get('location')} - {disaster.get('severity', disaster.get('magnitude', 'Active'))} ({distance}km away)")
                else:
                    context_parts.append(f"  ✅ NO disasters affecting this location in the last 3 days")
        
        # 🌊 REGIONAL HAZARD FILTER RESULTS
        if "regional_hazard_filter" in real_time_data:
            regional = real_time_data["regional_hazard_filter"]
            if regional.get("filtering_performed"):
                context_parts.append(f"\n🌊 REGIONAL HAZARD FILTER - {regional['region'].upper()}:")
                context_parts.append(f"  Total in Region: {regional['total_in_region']} out of {regional['total_global']} global disasters")
                context_parts.append(f"  Region: {regional['description']}")
                if regional.get('regional_disasters'):
                    context_parts.append(f"  Regional Disasters:")
                    for disaster in regional['regional_disasters'][:5]:
                        context_parts.append(f"    • {disaster.get('type')} in {disaster.get('location')} - {disaster.get('severity', disaster.get('magnitude', 'Active'))}")
        
        # 🚢 ROUTE HAZARD ANALYSIS RESULTS
        if "route_hazard_analysis" in real_time_data:
            route_hazards = real_time_data["route_hazard_analysis"]
            if route_hazards.get("analysis_performed"):
                context_parts.append(f"\n🚢 INTELLIGENT ROUTE HAZARD ANALYSIS:")
                context_parts.append(f"  Route: {route_hazards['from_location']} → {route_hazards['to_location']}")
                context_parts.append(f"  Safety Status: {'✅ SAFE' if route_hazards['is_safe'] else '⚠️ HAZARDS DETECTED'}")
                context_parts.append(f"  Risk Level: {route_hazards['risk_level']}")
                context_parts.append(f"  Total Hazards: {route_hazards['total_hazards']}")
                context_parts.append(f"  Recommendation: {route_hazards['recommendation']}")
                if route_hazards['total_hazards'] > 0:
                    if route_hazards.get('departure_hazards'):
                        context_parts.append(f"  Departure Hazards: {len(route_hazards['departure_hazards'])}")
                    if route_hazards.get('destination_hazards'):
                        context_parts.append(f"  Destination Hazards: {len(route_hazards['destination_hazards'])}")
                    if route_hazards.get('route_corridor_hazards'):
                        context_parts.append(f"  Route Corridor Hazards: {len(route_hazards['route_corridor_hazards'])}")
                    if route_hazards.get('detailed_warnings'):
                        context_parts.append(f"  Warnings: {'; '.join(route_hazards['detailed_warnings'][:3])}")
        
        if "route_data" in real_time_data:
            route_data = real_time_data["route_data"]
            if route_data.get("success"):
                context_parts.append(f"ROUTE: {route_data.get('from_port')} to {route_data.get('to_port')} - {route_data.get('distance_nm')} nautical miles, {route_data.get('estimated_time')} travel time")
                context_parts.append(f"Route description: {route_data.get('route_description')}")
        
        return "\n".join(context_parts) if context_parts else "Real-time data services active"
    
    async def _enhance_disaster_location_details(self, disasters: List[Dict]) -> List[Dict]:
        """Enhance disaster location details with more precise information"""
        enhanced_disasters = []
        
        for disaster in disasters:
            enhanced_disaster = disaster.copy()
            
            try:
                # Get more specific location information
                location = disaster.get('location', '')
                
                # If only country is provided, try to get more specific details
                if location and ',' not in location:
                    # Try to extract coordinates for more precise location
                    coordinates = disaster.get('coordinates')
                    if coordinates:
                        lat, lon = coordinates.get('lat'), coordinates.get('lon')
                        if lat and lon:
                            # Use reverse geocoding or location service to get more details
                            enhanced_location = await self._get_precise_location(lat, lon)
                            if enhanced_location:
                                enhanced_disaster['enhanced_location'] = enhanced_location
                
                enhanced_disasters.append(enhanced_disaster)
                
            except Exception as e:
                self.logger.warning(f"Failed to enhance location for disaster: {str(e)}")
                enhanced_disasters.append(disaster)
        
        return enhanced_disasters
    
    async def _generate_detailed_disaster_report(self, disasters: List[Dict], query: str) -> str:
        """Generate detailed disaster report based on specific user query"""
        if not disasters:
            return "No current disasters found matching your query."
        
        # Enhance location details first
        enhanced_disasters = await self._enhance_disaster_location_details(disasters)
        
        report_parts = []
        report_parts.append(f"📊 DETAILED DISASTER REPORT ({len(enhanced_disasters)} active disasters)")
        report_parts.append("=" * 60)
        
        for i, disaster in enumerate(enhanced_disasters[:8], 1):  # Show top 8 for detailed report
            disaster_type = disaster.get('type', 'Unknown')
            location = disaster.get('enhanced_location') or disaster.get('location', 'Unknown location')
            
            report_parts.append(f"\n{i}. {disaster_type.upper()}")
            report_parts.append(f"   📍 Location: {location}")
            
            # Add magnitude/intensity with context
            if disaster.get('magnitude'):
                report_parts.append(f"   📊 Magnitude: {disaster['magnitude']} (Richter Scale)")
            elif disaster.get('intensity'):
                report_parts.append(f"   ⚡ Intensity: {disaster['intensity']}")
            elif disaster.get('severity'):
                report_parts.append(f"   🔥 Severity: {disaster['severity']}")
            
            # Add timing information
            if disaster.get('time'):
                report_parts.append(f"   ⏰ Time: {disaster['time']}")
            
            # Add coordinates for precise location
            if disaster.get('coordinates'):
                coords = disaster['coordinates']
                if coords.get('lat') and coords.get('lon'):
                    report_parts.append(f"   🧭 Coordinates: {coords['lat']:.3f}°N, {coords['lon']:.3f}°E")
            
            # Add description if available
            if disaster.get('description'):
                description = disaster['description'][:200] + '...' if len(disaster['description']) > 200 else disaster['description']
                report_parts.append(f"   📝 Details: {description}")
            
            # Add source information
            source = disaster.get('source', 'Monitoring System')
            report_parts.append(f"   📡 Source: {source}")
            
            # Add potential marine impact
            if any(keyword in query.lower() for keyword in ['marine', 'ocean', 'sea', 'coast', 'ship', 'vessel']):
                impact = self._assess_marine_impact(disaster)
                if impact:
                    report_parts.append(f"   🌊 Marine Impact: {impact}")
        
        return "\n".join(report_parts)
    
    async def _get_precise_location(self, lat: float, lon: float) -> str:
        """Get precise location details from coordinates"""
        try:
            # Simple implementation - can be enhanced with geocoding service
            # For now, format coordinates with direction indicators
            lat_dir = "N" if lat >= 0 else "S"
            lon_dir = "E" if lon >= 0 else "W"
            
            # Basic region detection based on coordinates
            regions = {
                "Pacific Ring of Fire": (lat >= -60 and lat <= 60 and ((lon >= 120 and lon <= 180) or (lon >= -180 and lon <= -60))),
                "Atlantic Basin": (lon >= -80 and lon <= 20),
                "Indian Ocean Region": (lat >= -60 and lat <= 30 and lon >= 20 and lon <= 120),
                "Mediterranean Region": (lat >= 30 and lat <= 50 and lon >= -10 and lon <= 40),
                "Arctic Region": (lat >= 60),
                "Antarctic Region": (lat <= -60)
            }
            
            for region, condition in regions.items():
                if condition:
                    return f"{abs(lat):.2f}°{lat_dir}, {abs(lon):.2f}°{lon_dir} ({region})"
            
            return f"{abs(lat):.2f}°{lat_dir}, {abs(lon):.2f}°{lon_dir}"
        
        except Exception as e:
            self.logger.warning(f"Failed to get precise location: {str(e)}")
            return None
    
    def _assess_marine_impact(self, disaster: Dict) -> str:
        """Assess potential marine impact of a disaster"""
        disaster_type = disaster.get('type', '').lower()
        location = disaster.get('location', '').lower()
        
        # Check if disaster is coastal or marine-related
        coastal_indicators = ['coast', 'sea', 'ocean', 'bay', 'gulf', 'strait', 'island']
        is_coastal = any(indicator in location for indicator in coastal_indicators)
        
        if disaster_type == 'earthquake':
            magnitude = disaster.get('magnitude', 0)
            if magnitude >= 7.0 and is_coastal:
                return "HIGH - Tsunami risk for coastal areas and shipping"
            elif magnitude >= 6.0 and is_coastal:
                return "MODERATE - Possible local tsunami, monitor marine conditions"
            elif magnitude >= 5.0:
                return "LOW - Monitor for aftershocks"
        
        elif disaster_type in ['tsunami', 'storm surge']:
            return "CRITICAL - Immediate threat to all marine operations"
        
        elif disaster_type in ['cyclone', 'hurricane', 'typhoon']:
            return "HIGH - Severe weather conditions, avoid navigation"
        
        elif disaster_type in ['volcanic eruption', 'volcano']:
            if is_coastal:
                return "HIGH - Ash clouds, potential tsunami, navigation hazards"
            return "MODERATE - Monitor ash clouds affecting visibility"
        
        elif disaster_type in ['flood', 'flooding']:
            if is_coastal:
                return "MODERATE - Port operations may be affected"
        
        return "Monitor conditions and follow maritime safety protocols"
    
    def _clean_ai_response(self, response_content: str) -> str:
        """Clean AI response to remove raw search results and incomplete content"""
        
        # Remove problematic patterns that show raw search results
        patterns_to_remove = [
            r'📋 OFFICIAL REPORTS:\s*🏛️[^:]*:[^\.]*\.\.\.',
            r'📋 BREAKING NEWS:\s*🚨[^:]*:[^\.]*\.\.\.',
            r'📋 SAFETY ALERTS:\s*⚠️[^:]*:[^\.]*\.\.\.',
            r'📋 WEATHER CONDITIONS:\s*🌤️[^:]*:[^\.]*\.\.\.',
            r'📋 MARITIME UPDATES:\s*🚢[^:]*:[^\.]*\.\.\.',
            r'📋 [A-Z\s]+:\s*[🔥🚨⚠️🌤️🚢🌪️✈️📊][^:]*:[^\.]*\.\.\.',
            r'🏛️[^:]*: \d+ hours ago[^\.]*\.\.\.',
            r'🚨[^:]*: \d+ hours ago[^\.]*\.\.\.',
            r'⚠️[^:]*: \d+ hours ago[^\.]*\.\.\.',
            r'🌤️[^:]*: \d+ hours ago[^\.]*\.\.\.',
            r'🚢[^:]*: \d+ hours ago[^\.]*\.\.\.',
        ]
        
        import re
        cleaned_content = response_content
        
        for pattern in patterns_to_remove:
            cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.MULTILINE | re.DOTALL)
        
        # Remove empty sections and clean up formatting
        lines = cleaned_content.split('\n')
        cleaned_lines = []
        skip_next = False
        
        for line in lines:
            # Skip empty category headers
            if line.strip().startswith('📋') and ':' in line:
                # Check if this is followed by actual content or just search snippets
                skip_next = True
                continue
            
            # Skip lines with incomplete phrases or search artifacts
            if (line.strip().endswith('...') and 
                ('hours ago' in line or len(line.strip()) < 100) and
                any(emoji in line for emoji in ['🏛️', '🚨', '⚠️', '🌤️', '🚢'])):
                continue
            
            # Skip google search intelligence sections that show raw results
            if 'GOOGLE SEARCH INTELLIGENCE' in line.upper() and 'SUMMARY' not in line:
                skip_next = True
                continue
                
            if skip_next and line.strip().startswith(('•', '-', '  •', '  -')):
                continue
            
            skip_next = False
            cleaned_lines.append(line)
        
        # Join and clean up extra whitespace
        cleaned_content = '\n'.join(cleaned_lines)
        
        # Remove multiple consecutive empty lines
        cleaned_content = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_content)
        
        return cleaned_content.strip()
    
    async def _get_singapore_maritime_data(self) -> Dict[str, Any]:
        """Get specific maritime data for Singapore port"""
        try:
            # Singapore maritime data from multiple sources
            singapore_data = {
                "success": True,
                "port_name": "Port of Singapore",
                "maritime_conditions": {},
                "weather_data": {},
                "sources": []
            }
            
            # Get weather data specifically for Singapore
            singapore_weather = await self._get_weather_for_city("Singapore")
            if singapore_weather.get("success"):
                singapore_data["weather_data"] = singapore_weather
                singapore_data["sources"].append("singapore_weather_api")
            
            # Add maritime-specific information
            singapore_data["maritime_conditions"] = {
                "port_status": "Active - Major Maritime Hub",
                "vessel_traffic": "High - One of world's busiest ports",
                "facilities": "Container terminals, oil refining, ship repair",
                "strategic_location": "Southeast Asia gateway, Strait of Malacca",
                "port_authority": "Maritime and Port Authority of Singapore (MPA)",
                "coordinates": {"lat": 1.3521, "lng": 103.8198},
                "time_zone": "Singapore Standard Time (GMT+8)"
            }
            
            singapore_data["sources"].append("port_authority_data")
            
            return singapore_data
            
        except Exception as e:
            self.logger.error(f"Error getting Singapore maritime data: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Singapore maritime data temporarily unavailable"
            }

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
        logger.error(f"Chat processing error: {e}", exc_info=True)
        
        # Provide a basic fallback response based on message content
        message_lower = message.lower()
        fallback_response = "I'm experiencing technical difficulties with the AI service. "
        
        # Check if it's a route query and provide basic info
        if any(word in message_lower for word in ['route', 'distance', 'path', 'navigate', 'sail']):
            if 'colombo' in message_lower and 'singapore' in message_lower:
                fallback_response += "\n\n🚢 **Route Information (Colombo ↔ Singapore)**\n"
                fallback_response += "- Distance: Approximately 1,500 nautical miles (2,778 km)\n"
                fallback_response += "- Route: Through Malacca Strait\n"
                fallback_response += "- Estimated Time: 4-5 days at 12-15 knots\n"
                fallback_response += "- Major Waypoints: Nicobar Islands, Malacca Strait\n\n"
                fallback_response += "⚠️ AI-powered analysis unavailable. Please check:\n"
                fallback_response += "1. OpenAI API key configuration\n"
                fallback_response += "2. Network connectivity\n"
                fallback_response += "3. Service logs for details"
            else:
                fallback_response += "I can help with route planning, but the AI service is currently unavailable. "
                fallback_response += "Please try again in a moment or contact support if the issue persists."
        else:
            fallback_response += "Please try again in a moment. If the problem continues, please contact support."
        
        return {
            "response": fallback_response,
            "confidence": 0.1,
            "agent_type": "error",
            "data_sources": [],
            "real_time_data": {},
            "timestamp": datetime.now().isoformat()
        }