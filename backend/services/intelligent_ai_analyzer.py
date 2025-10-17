"""
Intelligent AI Analyzer for Smart Disaster and Safety Analysis
Makes the AI agent truly intelligent by correlating user queries with real hazards
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re
from geopy.distance import geodesic
import pytz

logger = logging.getLogger(__name__)

class IntelligentAIAnalyzer:
    """
    Intelligent analyzer that makes the AI agent smart by:
    1. Correlating location queries with active disasters
    2. Filtering regional hazards (e.g., Indian Ocean)
    3. Analyzing routes with hazard detection
    4. Providing evidence-based safety assessments
    """
    
    def __init__(self):
        # Define major regions with geographic boundaries
        self.regions = {
            'indian ocean': {
                'lat_range': (-40, 30),
                'lon_range': (20, 120),
                'description': 'Indian Ocean maritime region'
            },
            'pacific ocean': {
                'lat_range': (-60, 60),
                'lon_range': (120, -60),
                'description': 'Pacific Ocean maritime region'
            },
            'atlantic ocean': {
                'lat_range': (-60, 70),
                'lon_range': (-80, 20),
                'description': 'Atlantic Ocean maritime region'
            },
            'arabian sea': {
                'lat_range': (0, 30),
                'lon_range': (50, 80),
                'description': 'Arabian Sea region'
            },
            'bay of bengal': {
                'lat_range': (5, 22),
                'lon_range': (80, 100),
                'description': 'Bay of Bengal region'
            },
            'south china sea': {
                'lat_range': (0, 25),
                'lon_range': (100, 125),
                'description': 'South China Sea region'
            }
        }
        
        # Country/location coordinates for intelligent matching
        self.location_coords = {
            'japan': {'lat': 36.2048, 'lon': 138.2529, 'radius_km': 1500},
            'china': {'lat': 35.8617, 'lon': 104.1954, 'radius_km': 2500},
            'india': {'lat': 20.5937, 'lon': 78.9629, 'radius_km': 1500},
            'indonesia': {'lat': -0.7893, 'lon': 113.9213, 'radius_km': 2000},
            'philippines': {'lat': 12.8797, 'lon': 121.7740, 'radius_km': 1000},
            'sri lanka': {'lat': 7.8731, 'lon': 80.7718, 'radius_km': 300},
            'bangladesh': {'lat': 23.6850, 'lon': 90.3563, 'radius_km': 300},
            'myanmar': {'lat': 21.9162, 'lon': 95.9560, 'radius_km': 700},
            'thailand': {'lat': 15.8700, 'lon': 100.9925, 'radius_km': 700},
            'vietnam': {'lat': 14.0583, 'lon': 108.2772, 'radius_km': 700},
            'taiwan': {'lat': 23.6978, 'lon': 120.9605, 'radius_km': 300},
            'russia': {'lat': 61.5240, 'lon': 105.3188, 'radius_km': 3000},
            'fiji': {'lat': -17.7134, 'lon': 178.0650, 'radius_km': 500},
            'tonga': {'lat': -21.1789, 'lon': -175.1982, 'radius_km': 300},
            'samoa': {'lat': -13.7590, 'lon': -172.1046, 'radius_km': 200},
            'vanuatu': {'lat': -15.3767, 'lon': 166.9592, 'radius_km': 300},
            'papua new guinea': {'lat': -6.3150, 'lon': 143.9555, 'radius_km': 800},
            'new zealand': {'lat': -40.9006, 'lon': 174.8860, 'radius_km': 1000},
            'australia': {'lat': -25.2744, 'lon': 133.7751, 'radius_km': 2500},
            'mexico': {'lat': 23.6345, 'lon': -102.5528, 'radius_km': 1500},
            'chile': {'lat': -35.6751, 'lon': -71.5430, 'radius_km': 1800},
            'peru': {'lat': -9.1900, 'lon': -75.0152, 'radius_km': 1200},
            'ecuador': {'lat': -1.8312, 'lon': -78.1834, 'radius_km': 400},
            'usa': {'lat': 37.0902, 'lon': -95.7129, 'radius_km': 3000},
            'canada': {'lat': 56.1304, 'lon': -106.3468, 'radius_km': 3000},
            
            # Major cities/ports
            'colombo': {'lat': 6.9271, 'lon': 79.8612, 'radius_km': 100},
            'mumbai': {'lat': 19.0760, 'lon': 72.8777, 'radius_km': 150},
            'singapore': {'lat': 1.3521, 'lon': 103.8198, 'radius_km': 100},
            'chennai': {'lat': 13.0827, 'lon': 80.2707, 'radius_km': 100},
            'tokyo': {'lat': 35.6762, 'lon': 139.6503, 'radius_km': 150},
            'shanghai': {'lat': 31.2304, 'lon': 121.4737, 'radius_km': 150},
            'hong kong': {'lat': 22.3193, 'lon': 114.1694, 'radius_km': 100},
            'dubai': {'lat': 25.2048, 'lon': 55.2708, 'radius_km': 100},
            'karachi': {'lat': 24.8607, 'lon': 67.0011, 'radius_km': 100},
            'jakarta': {'lat': -6.2088, 'lon': 106.8456, 'radius_km': 150},
            'manila': {'lat': 14.5995, 'lon': 120.9842, 'radius_km': 100},
            'bangkok': {'lat': 13.7563, 'lon': 100.5018, 'radius_km': 100},
        }
    
    def analyze_location_safety(self, location_query: str, disaster_data: Dict) -> Dict[str, Any]:
        """
        Intelligently analyze if a location is safe by checking against ALL active disasters
        Returns detailed safety analysis with proof/evidence
        """
        location_lower = location_query.lower()
        
        # Extract location from query
        extracted_location = self._extract_location_from_query(location_lower)
        if not extracted_location:
            return {
                'analysis_performed': False,
                'reason': 'Could not identify specific location in query'
            }
        
        # Get disasters from data
        disasters = []
        if disaster_data.get('success'):
            disasters = disaster_data.get('disasters', [])
        
        # Filter to recent disasters only (last 3 days for more strict filtering)
        logger.info(f"Filtering {len(disasters)} disasters for recent events (last 3 days)")
        disasters = self._filter_recent_disasters(disasters, days=3)
        logger.info(f"After filtering: {len(disasters)} recent disasters remain")
        
        # Check if any disasters affect this location
        affecting_disasters = [] 
        # Use location-specific radius (smaller for islands, larger for countries)
        
        location_info = self.location_coords.get(extracted_location)
        if not location_info:
            # Try to match partial location names
            for loc_key, loc_val in self.location_coords.items():
                if loc_key in extracted_location or extracted_location in loc_key:
                    location_info = loc_val
                    extracted_location = loc_key
                    break
        
        if location_info:
            # Use the location's defined radius for relevance checking
            check_radius_km = location_info.get('radius_km', 300)
            
            for disaster in disasters:
                # Check if disaster location mentions the queried location
                disaster_location = disaster.get('location', '').lower()
                disaster_enhanced = disaster.get('enhanced_location', '').lower()
                
                # Direct location match (e.g., "Sri Lanka" in disaster location)
                if extracted_location in disaster_location or extracted_location in disaster_enhanced:
                    affecting_disasters.append({
                        'disaster': disaster,
                        'match_type': 'direct_location_match',
                        'distance_km': 0
                    })
                    continue
                
                # Geographic proximity check (if we have coordinates)
                if disaster.get('latitude') and disaster.get('longitude'):
                    disaster_coords = (disaster['latitude'], disaster['longitude'])
                    location_coords = (location_info['lat'], location_info['lon'])
                    
                    distance_km = geodesic(location_coords, disaster_coords).kilometers
                    
                    # Within affected radius? Use location-specific radius
                    # Only consider it affecting if it's within the location's radius
                    if distance_km <= check_radius_km:
                        affecting_disasters.append({
                            'disaster': disaster,
                            'match_type': 'geographic_proximity',
                            'distance_km': round(distance_km, 1)
                        })
        else:
            # Fallback: check for location name mentions in disaster data
            for disaster in disasters:
                disaster_location = disaster.get('location', '').lower()
                disaster_enhanced = disaster.get('enhanced_location', '').lower()
                
                if extracted_location in disaster_location or extracted_location in disaster_enhanced:
                    affecting_disasters.append({
                        'disaster': disaster,
                        'match_type': 'text_match',
                        'distance_km': None
                    })
        
        # Build safety analysis
        if affecting_disasters:
            # UNSAFE - disasters detected
            risk_level = self._calculate_risk_level(affecting_disasters)
            
            return {
                'analysis_performed': True,
                'location': extracted_location.title(),
                'is_safe': False,
                'risk_level': risk_level,
                'affecting_disasters': affecting_disasters,
                'disaster_count': len(affecting_disasters),
                'time_period': 'Last 3 days',
                'total_disasters_checked': len(disasters),
                'recommendation': f"⚠️ NOT RECOMMENDED: {len(affecting_disasters)} active disaster(s) affecting {extracted_location.title()}",
                'proof': self._build_proof_statement(affecting_disasters, extracted_location)
            }
        else:
            # SAFE - no disasters detected
            return {
                'analysis_performed': True,
                'location': extracted_location.title(),
                'is_safe': True,
                'risk_level': 'LOW',
                'affecting_disasters': [],
                'disaster_count': 0,
                'time_period': 'Last 3 days',
                'total_disasters_checked': len(disasters),
                'recommendation': f"✅ SAFE: No active disasters detected near {extracted_location.title()}",
                'proof': f"Checked {len(disasters)} recent global disasters (last 3 days) - none affecting {extracted_location.title()}"
            }
    
    def filter_regional_hazards(self, region_query: str, disaster_data: Dict) -> Dict[str, Any]:
        """
        Filter hazards to show only those in a specific region (e.g., "Indian Ocean")
        Returns disasters specific to that region only
        """
        region_lower = region_query.lower()
        
        # Identify the region
        identified_region = None
        for region_name, region_bounds in self.regions.items():
            if region_name in region_lower or region_lower in region_name:
                identified_region = region_name
                break
        
        if not identified_region:
            return {
                'filtering_performed': False,
                'reason': 'Could not identify specific region'
            }
        
        region_bounds = self.regions[identified_region]
        disasters = disaster_data.get('disasters', []) if disaster_data.get('success') else []
        
        # Filter disasters by region
        regional_disasters = []
        for disaster in disasters:
            # Check if disaster has coordinates
            if disaster.get('latitude') and disaster.get('longitude'):
                lat, lon = disaster['latitude'], disaster['longitude']
                
                # Check if within region bounds
                lat_range = region_bounds['lat_range']
                lon_range = region_bounds['lon_range']
                
                # Handle longitude wraparound for Pacific
                if identified_region == 'pacific ocean':
                    # Pacific spans across 180° meridian
                    if (lat_range[0] <= lat <= lat_range[1]) and \
                       (lon >= lon_range[0] or lon <= lon_range[1]):
                        regional_disasters.append(disaster)
                else:
                    if (lat_range[0] <= lat <= lat_range[1]) and \
                       (lon_range[0] <= lon <= lon_range[1]):
                        regional_disasters.append(disaster)
            else:
                # Fallback: check location text for region mentions
                location_text = f"{disaster.get('location', '')} {disaster.get('enhanced_location', '')}".lower()
                
                # Region-specific keywords
                region_keywords = {
                    'indian ocean': ['india', 'sri lanka', 'maldives', 'mauritius', 'seychelles', 'somalia', 'kenya', 'tanzania'],
                    'arabian sea': ['india', 'pakistan', 'oman', 'yemen', 'mumbai', 'karachi'],
                    'bay of bengal': ['india', 'bangladesh', 'myanmar', 'andaman', 'nicobar', 'chennai', 'kolkata'],
                    'south china sea': ['china', 'vietnam', 'philippines', 'malaysia', 'singapore', 'hong kong'],
                    'pacific ocean': ['japan', 'philippines', 'indonesia', 'fiji', 'tonga', 'samoa', 'vanuatu', 'pacific'],
                    'atlantic ocean': ['usa', 'canada', 'europe', 'africa', 'brazil', 'caribbean', 'atlantic']
                }
                
                keywords = region_keywords.get(identified_region, [])
                if any(keyword in location_text for keyword in keywords):
                    regional_disasters.append(disaster)
        
        return {
            'filtering_performed': True,
            'region': identified_region.title(),
            'regional_disasters': regional_disasters,
            'total_in_region': len(regional_disasters),
            'total_global': len(disasters),
            'description': region_bounds['description']
        }
    
    def analyze_route_hazards(self, from_location: str, to_location: str, disaster_data: Dict, 
                               route_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze hazards along a maritime route between two ports
        Returns comprehensive route safety analysis with hazard warnings
        """
        disasters = disaster_data.get('disasters', []) if disaster_data.get('success') else []
        
        # Filter to recent disasters only (last 3 days)
        disasters = self._filter_recent_disasters(disasters, days=3)
        
        # Get coordinates for both locations
        from_coords = self._get_location_coords(from_location.lower())
        to_coords = self._get_location_coords(to_location.lower())
        
        if not from_coords or not to_coords:
            return {
                'analysis_performed': False,
                'reason': 'Could not determine coordinates for one or both locations'
            }
        
        # Check hazards at departure point
        departure_hazards = self._check_location_hazards(from_location, from_coords, disasters)
        
        # Check hazards at destination
        destination_hazards = self._check_location_hazards(to_location, to_coords, disasters)
        
        # Check hazards along route path (simplified: check midpoint and corridor)
        route_hazards = self._check_route_corridor_hazards(from_coords, to_coords, disasters)
        
        # Calculate overall route risk
        all_hazards = departure_hazards + destination_hazards + route_hazards
        
        if all_hazards:
            risk_level = self._calculate_risk_level([{'disaster': h} for h in all_hazards])
            is_safe = False
            recommendation = f"⚠️ ROUTE NOT RECOMMENDED: {len(all_hazards)} hazard(s) detected along route"
        else:
            risk_level = 'LOW'
            is_safe = True
            recommendation = f"✅ ROUTE APPEARS SAFE: No active hazards detected along route corridor"
        
        return {
            'analysis_performed': True,
            'from_location': from_location.title(),
            'to_location': to_location.title(),
            'is_safe': is_safe,
            'risk_level': risk_level,
            'departure_hazards': departure_hazards,
            'destination_hazards': destination_hazards,
            'route_corridor_hazards': route_hazards,
            'total_hazards': len(all_hazards),
            'recommendation': recommendation,
            'detailed_warnings': self._build_route_warnings(all_hazards, from_location, to_location)
        }
    
    def format_disaster_with_accurate_time(self, disaster: Dict) -> Dict[str, Any]:
        """
        Format disaster information with accurate timestamps from API
        Converts to local time zones when possible
        """
        formatted = disaster.copy()
        
        # Handle earthquake time (usually in UTC milliseconds or ISO format)
        if 'time' in disaster:
            time_value = disaster['time']
            
            if isinstance(time_value, (int, float)):
                # Unix timestamp in milliseconds
                dt_utc = datetime.fromtimestamp(time_value / 1000, tz=pytz.UTC)
            elif isinstance(time_value, str):
                try:
                    # Try parsing ISO format
                    dt_utc = datetime.fromisoformat(time_value.replace('Z', '+00:00'))
                    if dt_utc.tzinfo is None:
                        dt_utc = pytz.UTC.localize(dt_utc)
                except:
                    dt_utc = None
            else:
                dt_utc = None
            
            if dt_utc:
                # Format UTC time
                formatted['time_utc'] = dt_utc.strftime('%Y-%m-%d %H:%M:%S UTC')
                
                # Try to get local time based on location
                if disaster.get('latitude') and disaster.get('longitude'):
                    try:
                        from timezonefinder import TimezoneFinder
                        tf = TimezoneFinder()
                        tz_name = tf.timezone_at(lat=disaster['latitude'], lng=disaster['longitude'])
                        if tz_name:
                            local_tz = pytz.timezone(tz_name)
                            dt_local = dt_utc.astimezone(local_tz)
                            formatted['time_local'] = dt_local.strftime('%Y-%m-%d %H:%M:%S %Z')
                            formatted['timezone'] = tz_name
                    except:
                        formatted['time_local'] = formatted['time_utc']
                else:
                    formatted['time_local'] = formatted['time_utc']
        
        # Handle storm/alert times (effective and expires)
        if 'effective' in disaster:
            formatted['time_start'] = disaster['effective']
        if 'expires' in disaster:
            formatted['time_end'] = disaster['expires']
        
        return formatted
    
    # Helper methods
    
    def _filter_recent_disasters(self, disasters: List[Dict], days: int = 7) -> List[Dict]:
        """
        Filter disasters to only include recent ones (within specified days)
        This prevents showing outdated disaster data
        """
        from datetime import datetime, timedelta
        
        recent_disasters = []
        cutoff_date = datetime.now() - timedelta(days=days)
        current_year = datetime.now().year
        
        logger.info(f"Filtering disasters - cutoff date: {cutoff_date.strftime('%Y-%m-%d')}, current year: {current_year}")
        
        for disaster in disasters:
            disaster_time = None
            
            # Try to parse disaster timestamp
            if 'time' in disaster:
                time_value = disaster['time']
                
                # Handle Unix timestamp (milliseconds)
                if isinstance(time_value, (int, float)):
                    try:
                        disaster_time = datetime.fromtimestamp(time_value / 1000)
                    except:
                        pass
                
                # Handle ISO format string
                elif isinstance(time_value, str):
                    try:
                        # Try parsing ISO format
                        disaster_time = datetime.fromisoformat(time_value.replace('Z', '+00:00'))
                        if disaster_time.tzinfo is not None:
                            disaster_time = disaster_time.replace(tzinfo=None)
                    except:
                        # Try parsing other common formats
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S']:
                            try:
                                disaster_time = datetime.strptime(time_value[:19], fmt)
                                break
                            except:
                                continue
            
            # Check if disaster is recent
            if disaster_time:
                # Extra check: Reject anything from previous years
                if disaster_time.year < current_year:
                    logger.warning(f"❌ FILTERED OUT OLD DISASTER from {disaster_time.year}: {disaster.get('type', 'Unknown')} - {disaster.get('location', 'Unknown')}")
                    continue
                
                if disaster_time >= cutoff_date:
                    recent_disasters.append(disaster)
                    logger.debug(f"✅ KEPT recent disaster from {disaster_time.strftime('%Y-%m-%d')}: {disaster.get('type', 'Unknown')}")
                else:
                    logger.warning(f"❌ FILTERED OUT disaster from {disaster_time.strftime('%Y-%m-%d')}: {disaster.get('type', 'Unknown')} - {disaster.get('location', 'Unknown')}")
            else:
                # If we can't determine time, include it (might be from weather alerts without timestamps)
                # But check if it has 'effective' or 'expires' fields
                if 'effective' in disaster or 'expires' in disaster:
                    recent_disasters.append(disaster)
                    logger.debug(f"✅ KEPT disaster with effective/expires: {disaster.get('type', 'Unknown')}")
                else:
                    # No time info at all - skip it to be safe
                    logger.warning(f"❌ FILTERED OUT disaster without timestamp: {disaster.get('type', 'Unknown')} - {disaster.get('location', 'Unknown')}")
        
        return recent_disasters
    
    def _extract_location_from_query(self, query: str) -> Optional[str]:
        """Extract location name from user query"""
        # Common patterns
        patterns = [
            r'(?:safe|go|travel|visit|to|in)\s+(?:to\s+)?([a-z\s]+?)(?:\s|$|\?)',
            r'(?:is|are)\s+([a-z\s]+?)\s+safe',
            r'safety\s+(?:of|in)\s+([a-z\s]+?)(?:\s|$|\?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                location = match.group(1).strip()
                # Check if it's a known location
                if location in self.location_coords or any(location in key or key in location for key in self.location_coords.keys()):
                    return location
        
        # Fallback: check if any known location is mentioned
        for location in self.location_coords.keys():
            if location in query:
                return location
        
        return None
    
    def _calculate_risk_level(self, affecting_disasters: List[Dict]) -> str:
        """Calculate overall risk level based on disasters"""
        if not affecting_disasters:
            return 'LOW'
        
        # Check severity of disasters
        high_severity_count = 0
        for item in affecting_disasters:
            disaster = item.get('disaster', item)
            severity = disaster.get('severity', '').lower()
            magnitude = disaster.get('magnitude', 0)
            
            # High severity indicators
            if severity in ['extreme', 'severe', 'major'] or magnitude >= 7.0:
                high_severity_count += 1
        
        if high_severity_count > 0:
            return 'HIGH'
        elif len(affecting_disasters) >= 3:
            return 'HIGH'
        elif len(affecting_disasters) >= 2:
            return 'MEDIUM'
        else:
            return 'MEDIUM'
    
    def _build_proof_statement(self, affecting_disasters: List[Dict], location: str) -> str:
        """Build evidence-based proof statement"""
        statements = []
        for item in affecting_disasters:
            disaster = item['disaster']
            match_type = item['match_type']
            distance = item.get('distance_km')
            
            disaster_type = disaster.get('type', 'Disaster')
            disaster_location = disaster.get('enhanced_location', disaster.get('location', 'Unknown'))
            severity = disaster.get('severity', '')
            magnitude = disaster.get('magnitude', '')
            
            if match_type == 'direct_location_match':
                proof = f"{disaster_type} directly affecting {disaster_location}"
            elif match_type == 'geographic_proximity' and distance is not None:
                proof = f"{disaster_type} {distance}km from {location.title()} ({disaster_location})"
            else:
                proof = f"{disaster_type} in {disaster_location}"
            
            if magnitude:
                proof += f" - Magnitude {magnitude}"
            elif severity:
                proof += f" - {severity}"
            
            statements.append(proof)
        
        return " | ".join(statements)
    
    def _get_location_coords(self, location: str) -> Optional[Tuple[float, float]]:
        """Get coordinates for a location"""
        if location in self.location_coords:
            info = self.location_coords[location]
            return (info['lat'], info['lon'])
        
        # Try partial match
        for key, info in self.location_coords.items():
            if key in location or location in key:
                return (info['lat'], info['lon'])
        
        return None
    
    def _check_location_hazards(self, location_name: str, coords: Tuple[float, float], 
                                 disasters: List[Dict]) -> List[Dict]:
        """Check hazards at a specific location"""
        hazards = []
        check_radius_km = 300  # Check within 300km of location
        
        for disaster in disasters:
            # Text match
            disaster_location = f"{disaster.get('location', '')} {disaster.get('enhanced_location', '')}".lower()
            if location_name.lower() in disaster_location:
                hazards.append(disaster)
                continue
            
            # Geographic match
            if disaster.get('latitude') and disaster.get('longitude'):
                disaster_coords = (disaster['latitude'], disaster['longitude'])
                distance = geodesic(coords, disaster_coords).kilometers
                if distance <= check_radius_km:
                    disaster_copy = disaster.copy()
                    disaster_copy['distance_km'] = round(distance, 1)
                    hazards.append(disaster_copy)
        
        return hazards
    
    def _check_route_corridor_hazards(self, from_coords: Tuple[float, float], 
                                       to_coords: Tuple[float, float], 
                                       disasters: List[Dict]) -> List[Dict]:
        """Check hazards along the route corridor"""
        hazards = []
        corridor_width_km = 500  # Check 500km on either side of direct route
        
        # Calculate midpoint
        mid_lat = (from_coords[0] + to_coords[0]) / 2
        mid_lon = (from_coords[1] + to_coords[1]) / 2
        midpoint = (mid_lat, mid_lon)
        
        # Calculate route distance
        route_distance = geodesic(from_coords, to_coords).kilometers
        
        for disaster in disasters:
            if disaster.get('latitude') and disaster.get('longitude'):
                disaster_coords = (disaster['latitude'], disaster['longitude'])
                
                # Distance from midpoint
                dist_from_midpoint = geodesic(midpoint, disaster_coords).kilometers
                
                # If within corridor
                if dist_from_midpoint <= (route_distance / 2 + corridor_width_km):
                    disaster_copy = disaster.copy()
                    disaster_copy['position'] = 'along route'
                    hazards.append(disaster_copy)
        
        return hazards
    
    def _build_route_warnings(self, hazards: List[Dict], from_loc: str, to_loc: str) -> List[str]:
        """Build detailed route warning messages"""
        warnings = []
        
        for hazard in hazards:
            hazard_type = hazard.get('type', 'Hazard')
            location = hazard.get('enhanced_location', hazard.get('location', 'Unknown'))
            severity = hazard.get('severity', '')
            magnitude = hazard.get('magnitude', '')
            position = hazard.get('position', '')
            
            warning = f"⚠️ {hazard_type}"
            if magnitude:
                warning += f" (M{magnitude})"
            elif severity:
                warning += f" ({severity})"
            warning += f" - {location}"
            if position:
                warning += f" [{position}]"
            
            warnings.append(warning)
        
        return warnings


# Global instance
intelligent_analyzer = IntelligentAIAnalyzer()
