import requests
import json
import os
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
import math
from dotenv import load_dotenv

load_dotenv()

class HarborService:
    def __init__(self):
        self.nominatim_base_url = "https://nominatim.openstreetmap.org"
        self.headers = {"User-Agent": "MarineApp/1.0"}
        
        # Manual harbor database with major ports worldwide
        self.harbor_database = self._load_harbor_database()
        # Load optional static dataset (user-provided ~1000 harbors)
        self.static_harbors = self._load_static_harbors()
        
        # Overpass API for OpenStreetMap data (disabled by default to avoid timeouts)
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.enable_overpass = False
    
    def _load_harbor_database(self) -> List[Dict]:
        """Load a comprehensive harbor/port database"""
        return [
            # Major International Ports
            {"name": "Port of Singapore", "country": "Singapore", "lat": 1.2966, "lon": 103.7764, "type": "container"},
            {"name": "Port of Shanghai", "country": "China", "lat": 31.2304, "lon": 121.4737, "type": "container"},
            {"name": "Port of Los Angeles", "country": "USA", "lat": 33.7175, "lon": -118.2728, "type": "container"},
            {"name": "Port of Rotterdam", "country": "Netherlands", "lat": 51.9225, "lon": 4.4792, "type": "container"},
            {"name": "Port of Hamburg", "country": "Germany", "lat": 53.5511, "lon": 9.9937, "type": "container"},
            {"name": "Port of Antwerp", "country": "Belgium", "lat": 51.2194, "lon": 4.4025, "type": "container"},
            {"name": "Port of Busan", "country": "South Korea", "lat": 35.1796, "lon": 129.0756, "type": "container"},
            {"name": "Port of Hong Kong", "country": "Hong Kong", "lat": 22.3193, "lon": 114.1694, "type": "container"},
            {"name": "Port of Dubai", "country": "UAE", "lat": 25.2048, "lon": 55.2708, "type": "container"},
            {"name": "Port of New York", "country": "USA", "lat": 40.6892, "lon": -74.0445, "type": "container"},
            
            # European Ports
            {"name": "Port of London", "country": "UK", "lat": 51.5074, "lon": -0.1278, "type": "commercial"},
            {"name": "Port of Marseille", "country": "France", "lat": 43.2965, "lon": 5.3698, "type": "commercial"},
            {"name": "Port of Barcelona", "country": "Spain", "lat": 41.3851, "lon": 2.1734, "type": "commercial"},
            {"name": "Port of Genoa", "country": "Italy", "lat": 44.4056, "lon": 8.9463, "type": "commercial"},
            {"name": "Port of Piraeus", "country": "Greece", "lat": 37.9755, "lon": 23.7348, "type": "commercial"},
            {"name": "Port of Amsterdam", "country": "Netherlands", "lat": 52.3676, "lon": 4.9041, "type": "commercial"},
            {"name": "Port of Gothenburg", "country": "Sweden", "lat": 57.7089, "lon": 11.9746, "type": "commercial"},
            {"name": "Port of Oslo", "country": "Norway", "lat": 59.9139, "lon": 10.7522, "type": "commercial"},
            {"name": "Port of Copenhagen", "country": "Denmark", "lat": 55.6761, "lon": 12.5683, "type": "commercial"},
            {"name": "Port of Helsinki", "country": "Finland", "lat": 60.1699, "lon": 24.9384, "type": "commercial"},
            
            # Asian Ports
            {"name": "Port of Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "type": "commercial"},
            {"name": "Port of Yokohama", "country": "Japan", "lat": 35.4437, "lon": 139.6380, "type": "commercial"},
            {"name": "Port of Kobe", "country": "Japan", "lat": 34.6901, "lon": 135.1956, "type": "commercial"},
            {"name": "Port of Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777, "type": "commercial"},
            {"name": "Port of Chennai", "country": "India", "lat": 13.0827, "lon": 80.2707, "type": "commercial"},
            {"name": "Port of Kolkata", "country": "India", "lat": 22.5726, "lon": 88.3639, "type": "commercial"},
            {"name": "Port of Colombo", "country": "Sri Lanka", "lat": 6.9271, "lon": 79.8612, "type": "commercial"},
            {"name": "Port of Karachi", "country": "Pakistan", "lat": 24.8607, "lon": 67.0011, "type": "commercial"},
            {"name": "Port of Chittagong", "country": "Bangladesh", "lat": 22.3569, "lon": 91.7832, "type": "commercial"},
            {"name": "Port of Bangkok", "country": "Thailand", "lat": 13.7563, "lon": 100.5018, "type": "commercial"},
            
            # American Ports
            {"name": "Port of Long Beach", "country": "USA", "lat": 33.7701, "lon": -118.1937, "type": "container"},
            {"name": "Port of Oakland", "country": "USA", "lat": 37.8044, "lon": -122.2712, "type": "container"},
            {"name": "Port of Seattle", "country": "USA", "lat": 47.6062, "lon": -122.3321, "type": "commercial"},
            {"name": "Port of Vancouver", "country": "Canada", "lat": 49.2827, "lon": -123.1207, "type": "commercial"},
            {"name": "Port of Montreal", "country": "Canada", "lat": 45.5017, "lon": -73.5673, "type": "commercial"},
            {"name": "Port of Halifax", "country": "Canada", "lat": 44.6488, "lon": -63.5752, "type": "commercial"},
            {"name": "Port of Santos", "country": "Brazil", "lat": -23.9618, "lon": -46.3322, "type": "commercial"},
            {"name": "Port of Buenos Aires", "country": "Argentina", "lat": -34.6118, "lon": -58.3960, "type": "commercial"},
            {"name": "Port of Valparaiso", "country": "Chile", "lat": -33.0458, "lon": -71.6197, "type": "commercial"},
            {"name": "Port of Callao", "country": "Peru", "lat": -12.0464, "lon": -77.0428, "type": "commercial"},
            
            # African Ports
            {"name": "Port of Cape Town", "country": "South Africa", "lat": -33.9249, "lon": 18.4241, "type": "commercial"},
            {"name": "Port of Durban", "country": "South Africa", "lat": -29.8587, "lon": 31.0218, "type": "commercial"},
            {"name": "Port of Lagos", "country": "Nigeria", "lat": 6.5244, "lon": 3.3792, "type": "commercial"},
            {"name": "Port of Alexandria", "country": "Egypt", "lat": 31.2001, "lon": 29.9187, "type": "commercial"},
            {"name": "Port of Casablanca", "country": "Morocco", "lat": 33.5731, "lon": -7.5898, "type": "commercial"},
            {"name": "Port of Mombasa", "country": "Kenya", "lat": -4.0437, "lon": 39.6682, "type": "commercial"},
            {"name": "Port of Dar es Salaam", "country": "Tanzania", "lat": -6.7924, "lon": 39.2083, "type": "commercial"},
            {"name": "Port of Abidjan", "country": "Ivory Coast", "lat": 5.3600, "lon": -4.0083, "type": "commercial"},
            
            # Australian Ports
            {"name": "Port of Sydney", "country": "Australia", "lat": -33.8688, "lon": 151.2093, "type": "commercial"},
            {"name": "Port of Melbourne", "country": "Australia", "lat": -37.8136, "lon": 144.9631, "type": "commercial"},
            {"name": "Port of Brisbane", "country": "Australia", "lat": -27.4698, "lon": 153.0251, "type": "commercial"},
            {"name": "Port of Perth", "country": "Australia", "lat": -31.9505, "lon": 115.8605, "type": "commercial"},
            {"name": "Port of Adelaide", "country": "Australia", "lat": -34.9285, "lon": 138.6007, "type": "commercial"},
            {"name": "Port of Auckland", "country": "New Zealand", "lat": -36.8485, "lon": 174.7633, "type": "commercial"},
            {"name": "Port of Wellington", "country": "New Zealand", "lat": -41.2924, "lon": 174.7787, "type": "commercial"},
            
            # Middle East Ports
            {"name": "Port of Jeddah", "country": "Saudi Arabia", "lat": 21.4858, "lon": 39.1925, "type": "commercial"},
            {"name": "Port of Dammam", "country": "Saudi Arabia", "lat": 26.4207, "lon": 50.0888, "type": "commercial"},
            {"name": "Port of Kuwait", "country": "Kuwait", "lat": 29.3759, "lon": 47.9774, "type": "commercial"},
            {"name": "Port of Doha", "country": "Qatar", "lat": 25.2854, "lon": 51.5310, "type": "commercial"},
            {"name": "Port of Manama", "country": "Bahrain", "lat": 26.0667, "lon": 50.5577, "type": "commercial"},
            {"name": "Port of Muscat", "country": "Oman", "lat": 23.5880, "lon": 58.3829, "type": "commercial"},
            
            # Fishing Ports
            {"name": "Port of Bergen", "country": "Norway", "lat": 60.3913, "lon": 5.3221, "type": "fishing"},
            {"name": "Port of Reykjavik", "country": "Iceland", "lat": 64.1466, "lon": -21.9426, "type": "fishing"},
            {"name": "Port of Halifax", "country": "Canada", "lat": 44.6488, "lon": -63.5752, "type": "fishing"},
            {"name": "Port of Gloucester", "country": "USA", "lat": 42.6159, "lon": -70.6620, "type": "fishing"},
            {"name": "Port of New Bedford", "country": "USA", "lat": 41.6362, "lon": -70.9342, "type": "fishing"},
            {"name": "Port of Grimsby", "country": "UK", "lat": 53.5678, "lon": -0.0754, "type": "fishing"},
            {"name": "Port of Peterhead", "country": "UK", "lat": 57.5089, "lon": -1.7842, "type": "fishing"},
            {"name": "Port of Fraserburgh", "country": "UK", "lat": 57.6922, "lon": -2.0056, "type": "fishing"},
        ]
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers using Haversine formula"""
        R = 6371  # Earth's radius in kilometers
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def _load_static_harbors(self) -> List[Dict]:
        """Load static harbor list from JSON if available."""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            static_path = os.path.join(base_dir, "data", "harbors_static.json")
            if os.path.exists(static_path):
                with open(static_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Normalize keys
                    normalized: List[Dict] = []
                    for item in data:
                        if not ("lat" in item and "lon" in item and "name" in item):
                            continue
                        normalized.append({
                            "name": item.get("name"),
                            "country": item.get("country", "Unknown"),
                            "type": item.get("type", "port"),
                            "lat": float(item.get("lat")),
                            "lon": float(item.get("lon")),
                            "display_name": item.get("display_name") or f"{item.get('name')}, {item.get('country', 'Unknown')}"
                        })
                    return normalized
        except Exception as e:
            print(f"Error loading static harbors: {e}")
        return []

    def _is_land_location(self, lat: float, lon: float) -> bool:
        """Cheap land/water heuristic removed to avoid slow reverse geocoding.
        We'll validate by proximity to a known harbor instead."""
        # Not used in new fast-path validation
        return False
    
    async def search_harbors(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for harbors by name or location"""
        if not query or len(query.strip()) < 2:
            return []
        
        query = query.strip().lower()
        results = []
        
        # Search in manual database
        for harbor in self.harbor_database:
            if (query in harbor['name'].lower() or 
                query in harbor['country'].lower() or
                query in harbor['type'].lower()):
                
                results.append({
                    'name': harbor['name'],
                    'country': harbor['country'],
                    'type': harbor['type'],
                    'lat': harbor['lat'],
                    'lon': harbor['lon'],
                    'display_name': f"{harbor['name']}, {harbor['country']}",
                    'source': 'database'
                })
        
        # Search in static dataset
        for harbor in self.static_harbors:
            if (query in harbor['name'].lower() or 
                query in harbor.get('country', '').lower() or
                query in harbor.get('type', '').lower()):
                results.append({
                    'name': harbor['name'],
                    'country': harbor.get('country', 'Unknown'),
                    'type': harbor.get('type', 'port'),
                    'lat': harbor['lat'],
                    'lon': harbor['lon'],
                    'display_name': harbor.get('display_name') or f"{harbor['name']}, {harbor.get('country', 'Unknown')}",
                    'source': 'static'
                })
        
        # Remove duplicates and sort by relevance
        unique_results = {}
        for result in results:
            key = f"{result['lat']},{result['lon']}"
            if key not in unique_results:
                unique_results[key] = result
        
        return list(unique_results.values())[:limit]
    
    async def find_nearest_harbor(self, lat: float, lon: float, max_distance_km: float = 200) -> Optional[Dict]:
        """Find the nearest harbor to a given location"""
        if not lat or not lon:
            return None
        
        nearest_harbor = None
        min_distance = float('inf')
        
        # Check manual database
        for harbor in self.harbor_database:
            distance = self._calculate_distance(lat, lon, harbor['lat'], harbor['lon'])
            if distance < min_distance and distance <= max_distance_km:
                min_distance = distance
                nearest_harbor = {
                    'name': harbor['name'],
                    'country': harbor['country'],
                    'type': harbor['type'],
                    'lat': harbor['lat'],
                    'lon': harbor['lon'],
                    'display_name': f"{harbor['name']}, {harbor['country']}",
                    'distance_km': distance,
                    'source': 'database'
                }
        
        # Check static dataset
        for harbor in self.static_harbors:
            distance = self._calculate_distance(lat, lon, harbor['lat'], harbor['lon'])
            if distance < min_distance and distance <= max_distance_km:
                min_distance = distance
                nearest_harbor = {
                    'name': harbor['name'],
                    'country': harbor.get('country', 'Unknown'),
                    'type': harbor.get('type', 'port'),
                    'lat': harbor['lat'],
                    'lon': harbor['lon'],
                    'display_name': harbor.get('display_name') or f"{harbor['name']}, {harbor.get('country', 'Unknown')}",
                    'distance_km': distance,
                    'source': 'static'
                }
        
        return nearest_harbor
    
    async def validate_harbor_location(self, lat: float, lon: float) -> Dict:
        """Validate if a location is suitable for ocean navigation (harbor/port)"""
        result = {
            'is_valid': False,
            'is_land': False,
            'nearest_harbor': None,
            'message': ''
        }
        
        # Fast validation: consider valid if within 5 km of a known harbor
        nearest_harbor = await self.find_nearest_harbor(lat, lon, max_distance_km=50)
        result['nearest_harbor'] = nearest_harbor
        if nearest_harbor and nearest_harbor['distance_km'] <= 5:
            result['is_valid'] = True
            result['message'] = f"Valid harbor location near {nearest_harbor['name']}"
        elif nearest_harbor:
            result['is_valid'] = False
            result['message'] = f"Not a harbor location. Nearest harbor: {nearest_harbor['name']} ({nearest_harbor['distance_km']:.1f} km away)"
        else:
            result['is_valid'] = False
            result['message'] = "No nearby harbors found within 50 km."
        
        return result

# Global instance
harbor_service = HarborService()
