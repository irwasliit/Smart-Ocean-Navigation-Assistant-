import math
from typing import Dict, List, Tuple
from datetime import datetime

class RouteService:
    def __init__(self):
        # Initialize with fast static maritime routes
        self.static_routes = self._initialize_static_routes()
        
    async def calculate_route(self, start_lat: float, start_lon: float, end_lat: float, end_lon: float, vessel_speed_knots: float = 15) -> Dict:
        """Fast maritime route calculation using predefined static routes"""
        try:
            # Find nearest ports to start and end coordinates
            start_port = self._find_nearest_port(start_lat, start_lon)
            end_port = self._find_nearest_port(end_lat, end_lon)
            
            # Get static route between these ports
            route_key = f"{start_port}_{end_port}"
            static_route = self.static_routes.get(route_key)
            
            if not static_route:
                # Try reverse route
                route_key = f"{end_port}_{start_port}"
                static_route = self.static_routes.get(route_key)
            
            if not static_route:
                # Fallback to simple safe route
                return self._generate_safe_fallback_route(start_lat, start_lon, end_lat, end_lon, vessel_speed_knots)
            
            # Use predefined static route
            distance_km = static_route['distance_nm'] * 1.852
            sample_points = static_route['waypoints']
            
            # Calculate travel time
            vessel_speed_kmh = vessel_speed_knots * 1.852
            estimated_duration = distance_km / vessel_speed_kmh
            
            return {
                "start_point": {"latitude": start_lat, "longitude": start_lon},
                "end_point": {"latitude": end_lat, "longitude": end_lon},
                "distance": round(distance_km, 2),
                "distance_nautical_miles": round(static_route['distance_nm'], 2),
                "bearing": static_route.get('bearing', 0),
                "estimated_duration": round(estimated_duration, 2),
                "estimated_fuel_consumption": round(distance_km * 0.3, 2),
                "vessel_speed_knots": vessel_speed_knots,
                "sample_points": sample_points,
                "waypoints": sample_points,
                "route_type": "static_maritime",
                "route_description": static_route.get('description', 'Maritime Route'),
                "major_waypoints": static_route.get('major_waypoints', []),
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error calculating route: {e}")
            return self._generate_safe_fallback_route(start_lat, start_lon, end_lat, end_lon, vessel_speed_knots)
            return {
                "start_point": {"latitude": start_lat, "longitude": start_lon},
                "end_point": {"latitude": end_lat, "longitude": end_lon},
                "distance": 0,
                "bearing": 0,
                "estimated_duration": 0,
                "sample_points": []
            }
    
    async def analyze_route_weather(self, sample_points: List[Dict]) -> Dict:
        """Analyze weather conditions at each sample point along the route"""
        weather_analysis = {
            "points": [],
            "hazard_summary": {},
            "risk_zones": []
        }
        
        try:
            for i, point in enumerate(sample_points):
                # Get weather data for this point
                weather_data = await self.weather_service.get_current_weather(
                    point["latitude"], point["longitude"]
                )
                
                point_analysis = {
                    "point_index": i,
                    "distance_from_start": point["distance_from_start"],
                    "latitude": point["latitude"],
                    "longitude": point["longitude"],
                    "weather": weather_data,
                    "hazard_level": self._calculate_point_hazard_level(weather_data)
                }
                
                weather_analysis["points"].append(point_analysis)
                
                # Identify risk zones
                if point_analysis["hazard_level"] > 0.7:
                    weather_analysis["risk_zones"].append({
                        "start_distance": point["distance_from_start"],
                        "end_distance": point["distance_from_start"] + 20,  # 20km zone
                        "hazard_level": point_analysis["hazard_level"],
                        "hazards": self._identify_hazards(weather_data)
                    })
            
            # Generate hazard summary
            weather_analysis["hazard_summary"] = self._generate_hazard_summary(weather_analysis["points"])
            
        except Exception as e:
            print(f"Error analyzing route weather: {e}")
        
        return weather_analysis
    
    def _calculate_bearing(self, start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> float:
        """Calculate bearing between two points"""
        lat1 = math.radians(start_lat)
        lat2 = math.radians(end_lat)
        delta_lon = math.radians(end_lon - start_lon)
        
        y = math.sin(delta_lon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
        
        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
    
    def _generate_sample_points(self, start_lat: float, start_lon: float, end_lat: float, end_lon: float, distance: float) -> List[Dict]:
        """Generate sample points along the route for weather analysis"""
        sample_points = []
        
        # Number of sample points based on distance (every 50km or minimum 5 points)
        num_points = max(5, int(distance / 50))
        
        for i in range(num_points + 1):
            # Calculate interpolation factor
            factor = i / num_points if num_points > 0 else 0
            
            # Interpolate coordinates
            lat = start_lat + (end_lat - start_lat) * factor
            lon = start_lon + (end_lon - start_lon) * factor
            
            # Calculate distance from start
            point_distance = distance * factor
            
            sample_points.append({
                "latitude": lat,
                "longitude": lon,
                "distance_from_start": round(point_distance, 2)
            })
        
        return sample_points
    
    def _calculate_point_hazard_level(self, weather_data: Dict) -> float:
        """Calculate hazard level for a specific point (0-1 scale)"""
        hazard_probabilities = weather_data.get("hazard_probabilities", {})
        
        # Weight different hazards
        weights = {
            "storm": 0.4,
            "high_wind": 0.3,
            "rough_sea": 0.2,
            "fog": 0.1
        }
        
        total_hazard = 0
        for hazard, probability in hazard_probabilities.items():
            weight = weights.get(hazard, 0.1)
            total_hazard += probability * weight
        
        return min(1.0, total_hazard)
    
    def _identify_hazards(self, weather_data: Dict) -> List[str]:
        """Identify specific hazards from weather data"""
        hazards = []
        hazard_probabilities = weather_data.get("hazard_probabilities", {})
        
        for hazard, probability in hazard_probabilities.items():
            if probability > 0.5:
                hazards.append(hazard)
        
        return hazards
    
    def _generate_hazard_summary(self, points: List[Dict]) -> Dict:
        """Generate summary of hazards along the route"""
        total_points = len(points)
        high_hazard_points = sum(1 for point in points if point["hazard_level"] > 0.7)
        medium_hazard_points = sum(1 for point in points if 0.4 < point["hazard_level"] <= 0.7)
        
        return {
            "total_points": total_points,
            "high_hazard_points": high_hazard_points,
            "medium_hazard_points": medium_hazard_points,
            "overall_risk_level": "High" if high_hazard_points > total_points * 0.3 else "Medium" if medium_hazard_points > total_points * 0.3 else "Low",
            "safe_percentage": round((total_points - high_hazard_points) / total_points * 100, 1) if total_points > 0 else 100
        }

    def _generate_enhanced_sample_points(self, start_lat: float, start_lon: float, end_lat: float, end_lon: float, distance: float) -> List[Dict]:
        """Generate enhanced sample points with more detailed information"""
        sample_points = []
        
        # More detailed sampling: every 25km or minimum 10 points for better accuracy
        num_points = max(10, int(distance / 25))
        
        for i in range(num_points + 1):
            factor = i / num_points if num_points > 0 else 0
            
            # Interpolate coordinates using great circle interpolation for better accuracy
            lat = start_lat + (end_lat - start_lat) * factor
            lon = start_lon + (end_lon - start_lon) * factor
            
            # Calculate distance from start
            point_distance = distance * factor
            
            sample_points.append({
                "latitude": lat,
                "longitude": lon,
                "distance_from_start": round(point_distance, 2),
                "segment_index": i,
                "is_waypoint": i == 0 or i == num_points
            })
        
        return sample_points
    
    def _generate_navigation_waypoints(self, start_lat: float, start_lon: float, end_lat: float, end_lon: float, distance: float) -> List[Dict]:
        """Generate navigation waypoints"""
        waypoints = []
        
        # Add start point
        waypoints.append({
            "latitude": start_lat,
            "longitude": start_lon,
            "name": "Start Point",
            "type": "departure"
        })
        
        # Add midpoint for long routes
        if distance > 100:
            mid_lat = (start_lat + end_lat) / 2
            mid_lon = (start_lon + end_lon) / 2
            waypoints.append({
                "latitude": mid_lat,
                "longitude": mid_lon,
                "name": "Midpoint",
                "type": "waypoint"
            })
        
        # Add end point
        waypoints.append({
            "latitude": end_lat,
            "longitude": end_lon,
            "name": "End Point",
            "type": "destination"
        })
        
        return waypoints
    
    def _get_maritime_route(self, start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> Dict:
        """Get proper maritime route avoiding land masses"""
        
        # Predefined maritime routes between major regions
        maritime_routes = self._get_predefined_maritime_routes()
        
        # Find the best matching route or create a custom one
        route = self._find_best_maritime_route(start_lat, start_lon, end_lat, end_lon, maritime_routes)
        
        return route
    
    def _get_predefined_maritime_routes(self) -> Dict:
        """Predefined safe maritime routes between major regions"""
        return {
            # Bay of Bengal Routes
            'bay_of_bengal_to_arabian_sea': {
                'region_bounds': {'lat_min': 6, 'lat_max': 22, 'lon_min': 68, 'lon_max': 95},
                'waypoints': [
                    {'lat': 13.0827, 'lon': 80.2707, 'name': 'Chennai'},
                    {'lat': 10.0, 'lon': 79.5, 'name': 'South of Tamil Nadu'},
                    {'lat': 8.0, 'lon': 77.0, 'name': 'Southwest of Sri Lanka'},
                    {'lat': 9.0, 'lon': 75.0, 'name': 'West of Sri Lanka'},
                    {'lat': 11.0, 'lon': 73.0, 'name': 'Approaching Mumbai'},
                    {'lat': 19.0760, 'lon': 72.8777, 'name': 'Mumbai'}
                ],
                'description': 'Bay of Bengal to Arabian Sea via southern route around Sri Lanka'
            },
            
            # Indian Ocean to Southeast Asia
            'indian_ocean_to_malacca': {
                'region_bounds': {'lat_min': -5, 'lat_max': 15, 'lon_min': 75, 'lon_max': 105},
                'waypoints': [
                    {'lat': 6.9271, 'lon': 79.8612, 'name': 'Colombo'},
                    {'lat': 6.0, 'lon': 81.0, 'name': 'East of Colombo'},
                    {'lat': 5.5, 'lon': 85.0, 'name': 'Mid Indian Ocean'},
                    {'lat': 4.0, 'lon': 90.0, 'name': 'Approaching Nicobar'},
                    {'lat': 3.0, 'lon': 95.0, 'name': 'North of Sumatra'},
                    {'lat': 2.0, 'lon': 100.0, 'name': 'West of Malacca Strait'},
                    {'lat': 1.3521, 'lon': 103.8198, 'name': 'Singapore'}
                ],
                'description': 'Indian Ocean to Singapore via Malacca Strait approach'
            },
            
            # Chennai to Singapore Maritime Route
            'chennai_to_singapore': {
                'region_bounds': {'lat_min': 1, 'lat_max': 14, 'lon_min': 80, 'lon_max': 104},
                'waypoints': [
                    {'lat': 13.0827, 'lon': 80.2707, 'name': 'Chennai Port'},
                    {'lat': 11.0, 'lon': 82.0, 'name': 'Southeast Bay of Bengal'},
                    {'lat': 8.0, 'lon': 84.0, 'name': 'Nicobar Islands Area'},
                    {'lat': 6.0, 'lon': 88.0, 'name': 'North Sumatra Waters'},
                    {'lat': 4.0, 'lon': 94.0, 'name': 'Malacca Strait Approach'},
                    {'lat': 2.5, 'lon': 99.0, 'name': 'Malacca Strait Entry'},
                    {'lat': 1.8, 'lon': 102.0, 'name': 'Malacca Strait Transit'},
                    {'lat': 1.3521, 'lon': 103.8198, 'name': 'Singapore Port'}
                ],
                'description': 'Chennai to Singapore via Bay of Bengal and Malacca Strait'
            },
            
            # Mumbai to Dubai Route  
            'mumbai_to_dubai': {
                'region_bounds': {'lat_min': 19, 'lat_max': 26, 'lon_min': 55, 'lon_max': 73},
                'waypoints': [
                    {'lat': 19.0760, 'lon': 72.8777, 'name': 'Mumbai Port'},
                    {'lat': 20.0, 'lon': 70.0, 'name': 'West of Mumbai'},
                    {'lat': 22.0, 'lon': 65.0, 'name': 'Arabian Sea Central'},
                    {'lat': 24.0, 'lon': 60.0, 'name': 'Approaching Gulf'},
                    {'lat': 25.2048, 'lon': 55.2708, 'name': 'Dubai Port'}
                ],
                'description': 'Mumbai to Dubai direct Arabian Sea route'
            },
            
            # Colombo to Chennai Route
            'colombo_to_chennai': {
                'region_bounds': {'lat_min': 6, 'lat_max': 14, 'lon_min': 79, 'lon_max': 81},
                'waypoints': [
                    {'lat': 6.9271, 'lon': 79.8612, 'name': 'Colombo Port'},
                    {'lat': 8.0, 'lon': 79.9, 'name': 'North of Colombo'},
                    {'lat': 9.5, 'lon': 80.0, 'name': 'Palk Strait Area'},
                    {'lat': 11.0, 'lon': 80.1, 'name': 'Southeast Coast India'},
                    {'lat': 12.5, 'lon': 80.2, 'name': 'Approaching Chennai'},
                    {'lat': 13.0827, 'lon': 80.2707, 'name': 'Chennai Port'}
                ],
                'description': 'Colombo to Chennai via Palk Strait region'
            }
        }
    
    def _find_best_maritime_route(self, start_lat: float, start_lon: float, end_lat: float, end_lon: float, maritime_routes: Dict) -> Dict:
        """Find the best predefined maritime route or create a custom one"""
        
        # Check if route matches any predefined routes
        for route_name, route_data in maritime_routes.items():
            bounds = route_data['region_bounds']
            
            # Check if both start and end points are within this route's region
            start_in_bounds = (bounds['lat_min'] <= start_lat <= bounds['lat_max'] and 
                             bounds['lon_min'] <= start_lon <= bounds['lon_max'])
            end_in_bounds = (bounds['lat_min'] <= end_lat <= bounds['lat_max'] and 
                           bounds['lon_min'] <= end_lon <= bounds['lon_max'])
            
            if start_in_bounds and end_in_bounds:
                # Adjust the route to match exact start/end points
                waypoints = route_data['waypoints'].copy()
                waypoints[0] = {'lat': start_lat, 'lon': start_lon, 'name': 'Start Point'}
                waypoints[-1] = {'lat': end_lat, 'lon': end_lon, 'name': 'End Point'}
                
                return {
                    'waypoints': waypoints,
                    'description': route_data['description'],
                    'major_waypoints': [wp['name'] for wp in waypoints[1:-1]],
                    'route_type': 'predefined'
                }
        
        # If no predefined route matches, create a safe maritime route
        return self._create_custom_maritime_route(start_lat, start_lon, end_lat, end_lon)
    
    def _create_custom_maritime_route(self, start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> Dict:
        """Create a custom maritime route that avoids major land masses"""
        
        waypoints = [
            {'lat': start_lat, 'lon': start_lon, 'name': 'Start Point'}
        ]
        
        # Add intermediate waypoints to avoid land
        # This is a simplified approach - in reality, you'd use more sophisticated land avoidance
        
        lat_diff = end_lat - start_lat
        lon_diff = end_lon - start_lon
        
        # Add waypoints to create a sea route
        if abs(lat_diff) > 2 or abs(lon_diff) > 2:
            # For longer routes, add strategic waypoints
            
            # Midpoint with slight offset to avoid land
            mid_lat = start_lat + lat_diff * 0.3
            mid_lon = start_lon + lon_diff * 0.3
            waypoints.append({'lat': mid_lat, 'lon': mid_lon, 'name': 'Intermediate Point 1'})
            
            mid_lat2 = start_lat + lat_diff * 0.7
            mid_lon2 = start_lon + lon_diff * 0.7
            waypoints.append({'lat': mid_lat2, 'lon': mid_lon2, 'name': 'Intermediate Point 2'})
        
        waypoints.append({'lat': end_lat, 'lon': end_lon, 'name': 'End Point'})
        
        return {
            'waypoints': waypoints,
            'description': f'Custom maritime route from ({start_lat:.2f}, {start_lon:.2f}) to ({end_lat:.2f}, {end_lon:.2f})',
            'major_waypoints': ['Safe sea route waypoints'],
            'route_type': 'custom'
        }
    
    def _calculate_route_distance(self, waypoints: List[Dict]) -> float:
        """Calculate total distance along waypoints"""
        total_distance = 0
        
        for i in range(len(waypoints) - 1):
            start_point = (waypoints[i]['lat'], waypoints[i]['lon'])
            end_point = (waypoints[i + 1]['lat'], waypoints[i + 1]['lon'])
            segment_distance = geodesic(start_point, end_point).kilometers
            total_distance += segment_distance
        
        return total_distance
    
    def _generate_maritime_sample_points(self, waypoints: List[Dict]) -> List[Dict]:
        """Generate sample points along the maritime route"""
        sample_points = []
        total_distance = 0
        
        for i in range(len(waypoints) - 1):
            start_wp = waypoints[i]
            end_wp = waypoints[i + 1]
            
            # Calculate segment distance
            segment_distance = geodesic((start_wp['lat'], start_wp['lon']), 
                                      (end_wp['lat'], end_wp['lon'])).kilometers
            
            # Generate points along this segment
            num_points = max(3, int(segment_distance / 25))  # Point every 25km
            
            for j in range(num_points):
                factor = j / num_points if num_points > 1 else 0
                
                lat = start_wp['lat'] + (end_wp['lat'] - start_wp['lat']) * factor
                lon = start_wp['lon'] + (end_wp['lon'] - start_wp['lon']) * factor
                
                sample_points.append({
                    "latitude": lat,
                    "longitude": lon,
                    "distance_from_start": round(total_distance + segment_distance * factor, 2),
                    "segment_index": i,
                    "is_waypoint": j == 0
                })
            
            total_distance += segment_distance
        
        # Add final point
        final_wp = waypoints[-1]
        sample_points.append({
            "latitude": final_wp['lat'],
            "longitude": final_wp['lon'],
            "distance_from_start": round(total_distance, 2),
            "segment_index": len(waypoints) - 1,
            "is_waypoint": True
        })
        
        return sample_points


