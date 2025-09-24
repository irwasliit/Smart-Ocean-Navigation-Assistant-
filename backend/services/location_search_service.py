import requests
import json
import os
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
import re
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

class LocationSearchService:
    def __init__(self):
        self.nominatim_base_url = "https://nominatim.openstreetmap.org"
        self.headers = {"User-Agent": "WeatherApp/1.0"}
        
        # Common location names database
        self.location_database = self._load_location_database()
        
        # Spelling correction patterns
        self.spelling_patterns = {
            'sri': ['sri lanka', 'srilanka'],
            'united states': ['usa', 'us', 'america'],
            'united kingdom': ['uk', 'britain', 'england'],
            'new york': ['ny', 'nyc'],
            'california': ['cali', 'ca'],
            'florida': ['fl'],
            'texas': ['tx'],
            'london': ['london uk'],
            'paris': ['paris france'],
            'tokyo': ['tokyo japan'],
            'mumbai': ['bombay'],
            'delhi': ['new delhi'],
            'bangalore': ['bengaluru'],
            'chennai': ['madras'],
            'kolkata': ['calcutta'],
            'hyderabad': ['hyderabad india'],
            'pune': ['pune india'],
            'ahmedabad': ['ahmedabad india'],
            'surat': ['surat india'],
            'jaipur': ['jaipur india'],
            'lucknow': ['lucknow india'],
            'kanpur': ['kanpur india'],
            'nagpur': ['nagpur india'],
            'indore': ['indore india'],
            'thane': ['thane india'],
            'bhopal': ['bhopal india'],
            'visakhapatnam': ['vizag', 'visakhapatnam india'],
            'pimpri': ['pimpri india'],
            'patna': ['patna india'],
            'vadodara': ['baroda', 'vadodara india'],
            'ludhiana': ['ludhiana india'],
            'agra': ['agra india'],
            'nashik': ['nashik india'],
            'faridabad': ['faridabad india'],
            'meerut': ['meerut india'],
            'rajkot': ['rajkot india'],
            'kalyan': ['kalyan india'],
            'vasai': ['vasai india'],
            'varanasi': ['banaras', 'varanasi india'],
            'srinagar': ['srinagar india'],
            'aurangabad': ['aurangabad india'],
            'noida': ['noida india'],
            'solapur': ['solapur india'],
            'hubli': ['hubli india'],
            'mysore': ['mysuru', 'mysore india'],
            'gulbarga': ['kalaburagi', 'gulbarga india'],
            'bhubaneswar': ['bhubaneswar india'],
            'cochin': ['kochi', 'cochin india'],
            'bhavnagar': ['bhavnagar india'],
            'amravati': ['amravati india'],
            'nanded': ['nanded india'],
            'kolhapur': ['kolhapur india'],
            'sangli': ['sangli india'],
            'malegaon': ['malegaon india'],
            'ulhasnagar': ['ulhasnagar india'],
            'jalgaon': ['jalgaon india'],
            'akola': ['akola india'],
            'latur': ['latur india'],
            'ahmadnagar': ['ahmadnagar india'],
            'ichalkaranji': ['ichalkaranji india'],
            'parbhani': ['parbhani india'],
            'jalna': ['jalna india'],
            'bhusawal': ['bhusawal india'],
            'amalner': ['amalner india'],
            'dhule': ['dhule india'],
            'chalisgaon': ['chalisgaon india'],
            'bhiwandi': ['bhiwandi india'],
            'panvel': ['panvel india'],
            'ulhasnagar': ['ulhasnagar india'],
            'badlapur': ['badlapur india'],
            'ambarnath': ['ambarnath india'],
            'bhiwani': ['bhiwani india'],
            'karnal': ['karnal india'],
            'hisar': ['hisar india'],
            'rohtak': ['rohtak india'],
            'panipat': ['panipat india'],
            'kurukshetra': ['kurukshetra india'],
            'sonipat': ['sonipat india'],
            'gurgaon': ['gurugram', 'gurgaon india'],
            'rewari': ['rewari india'],
            'palwal': ['palwal india'],
            'mahendragarh': ['mahendragarh india'],
            'jind': ['jind india'],
            'kaithal': ['kaithal india'],
            'fatehabad': ['fatehabad india'],
            'sirsa': ['sirsa india'],
            'bhiwani': ['bhiwani india'],
            'chandigarh': ['chandigarh india'],
            'shimla': ['shimla india'],
            'dharamshala': ['dharamshala india'],
            'solan': ['solan india'],
            'mandi': ['mandi india'],
            'kullu': ['kullu india'],
            'manali': ['manali india'],
            'palampur': ['palampur india'],
            'kangra': ['kangra india'],
            'una': ['una india'],
            'hamirpur': ['hamirpur india'],
            'bilaspur': ['bilaspur india'],
            'chamba': ['chamba india'],
            'lahul': ['lahul india'],
            'spiti': ['spiti india'],
            'kinnaur': ['kinnaur india'],
            'sirmour': ['sirmour india'],
            'shimla': ['shimla india'],
            'kangra': ['kangra india'],
            'una': ['una india'],
            'hamirpur': ['hamirpur india'],
            'bilaspur': ['bilaspur india'],
            'chamba': ['chamba india'],
            'lahul': ['lahul india'],
            'spiti': ['spiti india'],
            'kinnaur': ['kinnaur india'],
            'sirmour': ['sirmour india']
        }
    
    def _load_location_database(self) -> Dict[str, List[str]]:
        """Load a comprehensive location database"""
        return {
            'countries': [
                'afghanistan', 'albania', 'algeria', 'argentina', 'armenia', 'australia',
                'austria', 'azerbaijan', 'bangladesh', 'belarus', 'belgium', 'bolivia',
                'brazil', 'bulgaria', 'cambodia', 'canada', 'chile', 'china', 'colombia',
                'croatia', 'cuba', 'cyprus', 'czech republic', 'denmark', 'ecuador',
                'egypt', 'estonia', 'finland', 'france', 'georgia', 'germany', 'ghana',
                'greece', 'guatemala', 'haiti', 'hungary', 'iceland', 'india', 'indonesia',
                'iran', 'iraq', 'ireland', 'israel', 'italy', 'jamaica', 'japan', 'jordan',
                'kazakhstan', 'kenya', 'kuwait', 'kyrgyzstan', 'laos', 'latvia', 'lebanon',
                'libya', 'lithuania', 'luxembourg', 'madagascar', 'malaysia', 'maldives',
                'mali', 'malta', 'mauritius', 'mexico', 'moldova', 'mongolia', 'montenegro',
                'morocco', 'myanmar', 'nepal', 'netherlands', 'new zealand', 'nicaragua',
                'nigeria', 'north korea', 'norway', 'oman', 'pakistan', 'panama', 'paraguay',
                'peru', 'philippines', 'poland', 'portugal', 'qatar', 'romania', 'russia',
                'saudi arabia', 'senegal', 'serbia', 'singapore', 'slovakia', 'slovenia',
                'south africa', 'south korea', 'spain', 'sri lanka', 'sudan', 'sweden',
                'switzerland', 'syria', 'taiwan', 'tajikistan', 'thailand', 'tunisia',
                'turkey', 'turkmenistan', 'ukraine', 'united arab emirates', 'united kingdom',
                'united states', 'uruguay', 'uzbekistan', 'venezuela', 'vietnam', 'yemen',
                'zambia', 'zimbabwe'
            ],
            'major_cities': [
                'new york', 'london', 'paris', 'tokyo', 'mumbai', 'delhi', 'bangalore',
                'chennai', 'kolkata', 'hyderabad', 'pune', 'ahmedabad', 'surat', 'jaipur',
                'lucknow', 'kanpur', 'nagpur', 'indore', 'thane', 'bhopal', 'visakhapatnam',
                'pimpri', 'patna', 'vadodara', 'ludhiana', 'agra', 'nashik', 'faridabad',
                'meerut', 'rajkot', 'kalyan', 'vasai', 'varanasi', 'srinagar', 'aurangabad',
                'noida', 'solapur', 'hubli', 'mysore', 'gulbarga', 'bhubaneswar', 'cochin',
                'bhavnagar', 'amravati', 'nanded', 'kolhapur', 'sangli', 'malegaon',
                'ulhasnagar', 'jalgaon', 'akola', 'latur', 'ahmadnagar', 'ichalkaranji',
                'parbhani', 'jalna', 'bhusawal', 'amalner', 'dhule', 'chalisgaon',
                'bhiwandi', 'panvel', 'badlapur', 'ambarnath', 'bhiwani', 'karnal',
                'hisar', 'rohtak', 'panipat', 'kurukshetra', 'sonipat', 'gurgaon',
                'rewari', 'palwal', 'mahendragarh', 'jind', 'kaithal', 'fatehabad',
                'sirsa', 'chandigarh', 'shimla', 'dharamshala', 'solan', 'mandi',
                'kullu', 'manali', 'palampur', 'kangra', 'una', 'hamirpur', 'bilaspur',
                'chamba', 'lahul', 'spiti', 'kinnaur', 'sirmour', 'los angeles',
                'chicago', 'houston', 'phoenix', 'philadelphia', 'san antonio',
                'san diego', 'dallas', 'san jose', 'austin', 'jacksonville', 'fort worth',
                'columbus', 'charlotte', 'san francisco', 'indianapolis', 'seattle',
                'denver', 'washington', 'boston', 'el paso', 'nashville', 'detroit',
                'oklahoma city', 'portland', 'las vegas', 'memphis', 'louisville',
                'baltimore', 'milwaukee', 'albuquerque', 'tucson', 'fresno', 'mesa',
                'sacramento', 'atlanta', 'kansas city', 'colorado springs', 'raleigh',
                'omaha', 'miami', 'long beach', 'virginia beach', 'oakland', 'minneapolis',
                'tulsa', 'arlington', 'tampa', 'new orleans', 'wichita', 'cleveland',
                'bakersfield', 'aurora', 'anaheim', 'honolulu', 'santa ana', 'corpus christi',
                'riverside', 'lexington', 'stockton', 'henderson', 'saint paul', 'st louis',
                'milwaukee', 'baltimore', 'boston', 'seattle', 'denver', 'las vegas',
                'nashville', 'portland', 'oklahoma city', 'albuquerque', 'tucson',
                'fresno', 'mesa', 'sacramento', 'atlanta', 'kansas city', 'colorado springs',
                'raleigh', 'omaha', 'miami', 'long beach', 'virginia beach', 'oakland',
                'minneapolis', 'tulsa', 'arlington', 'tampa', 'new orleans', 'wichita',
                'cleveland', 'bakersfield', 'aurora', 'anaheim', 'honolulu', 'santa ana',
                'corpus christi', 'riverside', 'lexington', 'stockton', 'henderson',
                'saint paul', 'st louis', 'madrid', 'barcelona', 'valencia', 'seville',
                'zaragoza', 'malaga', 'murcia', 'palma', 'las palmas', 'bilbao',
                'alicante', 'cordoba', 'valladolid', 'vigo', 'gijon', 'hospitalet',
                'coruna', 'granada', 'vitoria', 'elche', 'santa cruz', 'oviedo',
                'mostoles', 'cartagena', 'terrassa', 'alcala', 'pamplona', 'fuenlabrada',
                'almeria', 'leganes', 'santander', 'castellon', 'burgos', 'alcorcon',
                'getafe', 'salamanca', 'huelva', 'marbella', 'leon', 'tarragona',
                'cadiz', 'lugo', 'linares', 'caceres', 'lorca', 'coslada', 'talavera',
                'el ejido', 'majadahonda', 'reus', 'fuengirola', 'pontevedra', 'ciudad real',
                'elche', 'santa cruz', 'oviedo', 'mostoles', 'cartagena', 'terrassa',
                'alcala', 'pamplona', 'fuenlabrada', 'almeria', 'leganes', 'santander',
                'castellon', 'burgos', 'alcorcon', 'getafe', 'salamanca', 'huelva',
                'marbella', 'leon', 'tarragona', 'cadiz', 'lugo', 'linares', 'caceres',
                'lorca', 'coslada', 'talavera', 'el ejido', 'majadahonda', 'reus',
                'fuengirola', 'pontevedra', 'ciudad real'
            ]
        }
    
    def _calculate_similarity(self, a: str, b: str) -> float:
        """Calculate similarity between two strings"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def _fuzzy_match(self, query: str, candidates: List[str], threshold: float = 0.6) -> List[Tuple[str, float]]:
        """Find fuzzy matches for a query"""
        matches = []
        query_lower = query.lower()
        
        for candidate in candidates:
            similarity = self._calculate_similarity(query_lower, candidate.lower())
            if similarity >= threshold:
                matches.append((candidate, similarity))
        
        return sorted(matches, key=lambda x: x[1], reverse=True)
    
    def _apply_spelling_correction(self, query: str) -> List[str]:
        """Apply spelling correction patterns"""
        corrected_queries = [query]
        query_lower = query.lower()
        
        # Check for common spelling patterns
        for pattern, corrections in self.spelling_patterns.items():
            if pattern in query_lower:
                for correction in corrections:
                    corrected_query = query_lower.replace(pattern, correction)
                    corrected_queries.append(corrected_query)
        
        return corrected_queries
    
    async def search_locations(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for locations with spelling correction and fuzzy matching"""
        if not query or len(query.strip()) < 2:
            return []
        
        query = query.strip()
        corrected_queries = self._apply_spelling_correction(query)
        
        all_results = []
        
        # Search using Nominatim API first (with coordinates)
        try:
            for corrected_query in corrected_queries[:3]:  # Try more variations
                nominatim_results = await self._search_nominatim(corrected_query, limit=8)
                all_results.extend(nominatim_results)
        except Exception as e:
            print(f"Error searching Nominatim: {e}")
        
        # If no good results from API, try local database but get coordinates
        if not all_results or len(all_results) < 3:
            for corrected_query in corrected_queries:
                # Search countries and get coordinates
                country_matches = self._fuzzy_match(corrected_query, self.location_database['countries'])
                for country, score in country_matches[:2]:
                    coords = await self.get_location_coordinates(country)
                    if coords:
                        all_results.append({
                            'name': country.title(),
                            'display_name': f"{country.title()}, Country",
                            'type': 'country',
                            'score': score,
                            'query': corrected_query,
                            'latitude': coords.get('lat', 0),
                            'longitude': coords.get('lon', 0)
                        })
                
                # Search cities and get coordinates
                city_matches = self._fuzzy_match(corrected_query, self.location_database['major_cities'])
                for city, score in city_matches[:3]:
                    coords = await self.get_location_coordinates(city)
                    if coords:
                        all_results.append({
                            'name': city.title(),
                            'display_name': f"{city.title()}, City",
                            'type': 'city',
                            'score': score,
                            'query': corrected_query,
                            'latitude': coords.get('lat', 0),
                            'longitude': coords.get('lon', 0)
                        })
        
        # Remove duplicates and sort by score - prioritize results with coordinates
        unique_results = {}
        for result in all_results:
            key = result['name'].lower()
            has_coords = result.get('latitude', 0) != 0 or result.get('longitude', 0) != 0
            
            if key not in unique_results:
                unique_results[key] = result
            elif has_coords and (unique_results[key].get('latitude', 0) == 0 and unique_results[key].get('longitude', 0) == 0):
                # Replace if new result has coordinates and old doesn't
                unique_results[key] = result
            elif result['score'] > unique_results[key]['score']:
                unique_results[key] = result
        
        # Filter out results without coordinates and sort by score
        valid_results = []
        for result in unique_results.values():
            has_coords = result.get('latitude', 0) != 0 or result.get('longitude', 0) != 0
            if has_coords:
                # Ensure coordinates are properly set
                result['lat'] = result.get('latitude', 0)  # Add lat field for compatibility
                result['lon'] = result.get('longitude', 0)  # Add lon field for compatibility
                valid_results.append(result)
        
        # Sort by score - all results now have coordinates
        sorted_results = sorted(valid_results, key=lambda x: x['score'], reverse=True)
        return sorted_results[:limit]
    
    async def _search_nominatim(self, query: str, limit: int = 5) -> List[Dict]:
        """Search using Nominatim API"""
        try:
            url = f"{self.nominatim_base_url}/search"
            params = {
                'q': query,
                'format': 'json',
                'limit': limit,
                'addressdetails': 1,
                'extratags': 1,
                'namedetails': 1
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data:
                display_name = item.get('display_name', '')
                name = item.get('name', '')
                lat = float(item.get('lat', 0))
                lon = float(item.get('lon', 0))
                
                # Handle cases where name is "Unknown Location" or contains "unknown"
                if not name or name.lower().strip() in ['unknown location', 'unknown'] or 'unknown' in name.lower():
                    # Try to extract a meaningful name from display_name or use coordinates
                    if display_name:
                        # Split display_name and find the first meaningful part
                        parts = display_name.split(',')
                        meaningful_parts = [part.strip() for part in parts if part.strip() and 
                                         not part.strip().lower().startswith('unknown') and
                                         not part.strip().lower() == 'unknown location']
                        if meaningful_parts:
                            name = meaningful_parts[0]
                        else:
                            name = f"Location {lat:.4f}, {lon:.4f}"
                    else:
                        name = f"Location {lat:.4f}, {lon:.4f}"
                
                # Clean up display_name to remove unknown parts
                if display_name:
                    clean_parts = display_name.split(',')
                    clean_parts = [part.strip() for part in clean_parts if part.strip() and 
                                 not part.strip().lower().startswith('unknown') and
                                 not part.strip().lower() == 'unknown location']
                    display_name = ', '.join(clean_parts) if clean_parts else f"Coordinates: {lat:.6f}, {lon:.6f}"
                else:
                    display_name = f"Coordinates: {lat:.6f}, {lon:.6f}"
                
                # Extract location type
                location_type = 'place'
                if 'country' in item.get('type', ''):
                    location_type = 'country'
                elif 'city' in item.get('type', '') or 'town' in item.get('type', ''):
                    location_type = 'city'
                elif 'state' in item.get('type', ''):
                    location_type = 'state'
                
                # Calculate relevance score
                score = self._calculate_similarity(query.lower(), name.lower())
                
                # Only include results with valid coordinates
                if lat != 0 and lon != 0:
                    results.append({
                        'name': name,
                        'display_name': display_name,
                        'type': location_type,
                        'score': score,
                        'query': query,
                        'latitude': lat,
                        'longitude': lon,
                        'lat': lat,  # Add for compatibility
                        'lon': lon,  # Add for compatibility
                        'osm_id': item.get('osm_id'),
                        'osm_type': item.get('osm_type')
                    })
            
            return results
            
        except Exception as e:
            print(f"Error in Nominatim search: {e}")
            return []
    
    async def get_location_coordinates(self, location_name: str) -> Optional[Dict]:
        """Get coordinates for a specific location"""
        try:
            url = f"{self.nominatim_base_url}/search"
            params = {
                'q': location_name,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data:
                item = data[0]
                lat = float(item.get('lat', 0))
                lon = float(item.get('lon', 0))
                display_name = item.get('display_name', location_name)
                
                # Handle unknown locations by cleaning display_name or using coordinates
                if not display_name or 'unknown' in display_name.lower():
                    if display_name:
                        # Clean up the display name
                        parts = display_name.split(',')
                        clean_parts = [part.strip() for part in parts if part.strip() and 
                                     not part.strip().lower().startswith('unknown') and
                                     not part.strip().lower() == 'unknown location']
                        display_name = ', '.join(clean_parts) if clean_parts else f"Location {lat:.4f}, {lon:.4f}"
                    else:
                        display_name = f"Location {lat:.4f}, {lon:.4f}"
                
                return {
                    'name': display_name,
                    'lat': lat,
                    'lon': lon,
                    'address': item.get('address', {}),
                    'osm_id': item.get('osm_id')
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting coordinates: {e}")
            return None

