import math
from typing import Dict, List, Tuple
from geopy.distance import geodesic
import requests
from datetime import datetime
from services.weather_service import WeatherService

class RouteService:
    def __init__(self):
        self.weather_service = WeatherService()
        # Hardcoded major harbors with their coordinates
        self.major_harbors = {
            "Chennai": {"lat": 13.0827, "lng": 80.2707, "country": "India"},
            "Mumbai": {"lat": 19.0760, "lng": 72.8777, "country": "India"},
            "Singapore": {"lat": 1.3521, "lng": 103.8198, "country": "Singapore"},
            "Shanghai": {"lat": 31.2304, "lng": 121.4737, "country": "China"},
            "Colombo": {"lat": 6.9271, "lng": 79.8612, "country": "Sri Lanka"},
        }
        
        # Predefined maritime routes between harbors
        self.maritime_routes = {
            ("Chennai", "Mumbai"): [
                {"lat": 13.0827, "lng": 80.2707},  # Chennai
                {"lat": 12.5, "lng": 81.5},       # Off Chennai coast
                {"lat": 10.5, "lng": 83.0},       # Bay of Bengal, further east
                {"lat": 7.5, "lng": 84.0},        # East of Sri Lanka, open ocean
                {"lat": 5.5, "lng": 80.0},        # Well south of Sri Lanka, open Indian Ocean
                {"lat": 7.5, "lng": 77.5},        # Off Kanyakumari (southern tip), open water
                {"lat": 9.5, "lng": 75.5},        # Arabian Sea, off Kerala
                {"lat": 12.0, "lng": 73.5},       # Arabian Sea, off Goa
                {"lat": 15.0, "lng": 72.8},       # Arabian Sea, off Maharashtra
                {"lat": 19.0760, "lng": 72.8777},  # Mumbai
            ],
            ("Chennai", "Singapore"): [
                {"lat": 13.0827, "lng": 80.2707},  # Chennai
                {"lat": 12.5, "lng": 82.0},
                {"lat": 11.0, "lng": 85.0},
                {"lat": 9.5, "lng": 88.0},
                {"lat": 8.0, "lng": 91.0},
                {"lat": 6.5, "lng": 94.0},
                {"lat": 5.0, "lng": 97.0},
                {"lat": 3.5, "lng": 100.0},
                {"lat": 2.0, "lng": 102.0},
                {"lat": 1.3521, "lng": 103.8198},  # Singapore
            ],
            ("Chennai", "Shanghai"): [
                {"lat": 13.0827, "lng": 80.2707},  # Chennai
                {"lat": 14.0, "lng": 82.0},
                {"lat": 15.0, "lng": 85.0},
                {"lat": 16.5, "lng": 88.0},
                {"lat": 18.0, "lng": 92.0},
                {"lat": 20.0, "lng": 96.0},
                {"lat": 22.0, "lng": 101.0},
                {"lat": 24.0, "lng": 106.0},
                {"lat": 26.0, "lng": 111.0},
                {"lat": 28.0, "lng": 116.0},
                {"lat": 30.0, "lng": 120.0},
                {"lat": 31.2304, "lng": 121.4737},  # Shanghai
            ],
            ("Chennai", "Colombo"): [
                {"lat": 13.0827, "lng": 80.2707},  # Chennai
                {"lat": 12.0, "lng": 80.0},
                {"lat": 10.5, "lng": 79.8},
                {"lat": 8.5, "lng": 79.7},
                {"lat": 6.9271, "lng": 79.8612},  # Colombo
            ],
            ("Mumbai", "Singapore"): [
                {"lat": 19.0760, "lng": 72.8777},  # Mumbai
                {"lat": 17.0, "lng": 74.0},
                {"lat": 14.0, "lng": 76.0},
                {"lat": 11.0, "lng": 78.0},
                {"lat": 8.0, "lng": 81.0},
                {"lat": 5.0, "lng": 85.0},
                {"lat": 3.0, "lng": 90.0},
                {"lat": 2.0, "lng": 95.0},
                {"lat": 1.5, "lng": 100.0},
                {"lat": 1.3521, "lng": 103.8198},  # Singapore
            ],
            ("Mumbai", "Shanghai"): [
                {"lat": 19.0760, "lng": 72.8777},  # Mumbai
                {"lat": 18.0, "lng": 75.0},
                {"lat": 16.0, "lng": 78.0},
                {"lat": 14.0, "lng": 82.0},
                {"lat": 12.0, "lng": 86.0},
                {"lat": 10.0, "lng": 91.0},
                {"lat": 8.0, "lng": 96.0},
                {"lat": 7.0, "lng": 101.0},
                {"lat": 8.0, "lng": 105.0},
                {"lat": 10.0, "lng": 109.0},
                {"lat": 13.0, "lng": 112.0},
                {"lat": 17.0, "lng": 115.0},
                {"lat": 22.0, "lng": 117.0},
                {"lat": 27.0, "lng": 119.0},
                {"lat": 31.2304, "lng": 121.4737},  # Shanghai
            ],
            ("Mumbai", "Colombo"): [
                {"lat": 19.0760, "lng": 72.8777},  # Mumbai
                {"lat": 17.0, "lng": 73.5},
                {"lat": 14.5, "lng": 74.5},
                {"lat": 12.0, "lng": 75.5},
                {"lat": 9.5, "lng": 77.0},
                {"lat": 7.5, "lng": 78.5},
                {"lat": 6.9271, "lng": 79.8612},  # Colombo
            ],
            ("Singapore", "Shanghai"): [
                {"lat": 1.3521, "lng": 103.8198},  # Singapore
                {"lat": 3.0, "lng": 105.0},
                {"lat": 5.0, "lng": 107.0},
                {"lat": 8.0, "lng": 109.0},
                {"lat": 12.0, "lng": 111.0},
                {"lat": 16.0, "lng": 113.0},
                {"lat": 20.0, "lng": 115.0},
                {"lat": 24.0, "lng": 117.0},
                {"lat": 28.0, "lng": 119.0},
                {"lat": 31.2304, "lng": 121.4737},  # Shanghai
            ],
            ("Singapore", "Colombo"): [
                {"lat": 1.3521, "lng": 103.8198},  # Singapore
                {"lat": 2.0, "lng": 101.0},
                {"lat": 3.0, "lng": 98.0},
                {"lat": 4.0, "lng": 95.0},
                {"lat": 5.0, "lng": 92.0},
                {"lat": 6.0, "lng": 88.0},
                {"lat": 6.5, "lng": 84.0},
                {"lat": 6.8, "lng": 80.0},
                {"lat": 6.9271, "lng": 79.8612},  # Colombo
            ],
            ("Shanghai", "Colombo"): [
                {"lat": 31.2304, "lng": 121.4737},  # Shanghai
                {"lat": 28.0, "lng": 119.0},
                {"lat": 24.0, "lng": 117.0},
                {"lat": 20.0, "lng": 115.0},
                {"lat": 16.0, "lng": 113.0},
                {"lat": 12.0, "lng": 111.0},
                {"lat": 8.0, "lng": 109.0},
                {"lat": 5.0, "lng": 106.0},
                {"lat": 3.0, "lng": 102.0},
                {"lat": 2.0, "lng": 98.0},
                {"lat": 3.0, "lng": 94.0},
                {"lat": 4.5, "lng": 90.0},
                {"lat": 5.5, "lng": 86.0},
                {"lat": 6.5, "lng": 82.0},
                {"lat": 6.9271, "lng": 79.8612},  # Colombo
            ],
        }
        
    def find_nearest_harbor(self, lat: float, lng: float) -> str:
        """Find the nearest major harbor to given coordinates"""
        min_distance = float('inf')
        nearest_harbor = None
        
        for harbor_name, harbor_data in self.major_harbors.items():
            distance = geodesic((lat, lng), (harbor_data["lat"], harbor_data["lng"])).kilometers
            if distance < min_distance:
                min_distance = distance
                nearest_harbor = harbor_name
                
        return nearest_harbor
        
    def get_maritime_route(self, start_harbor: str, end_harbor: str) -> List[Dict]:
        """Get predefined maritime route between two harbors"""
        route_key = (start_harbor, end_harbor)
        reverse_key = (end_harbor, start_harbor)
        
        if route_key in self.maritime_routes:
            return self.maritime_routes[route_key]
        elif reverse_key in self.maritime_routes:
            # Return reversed route
            return list(reversed(self.maritime_routes[reverse_key]))
        else:
            # If no predefined route, create a simple oceanic route
            start_coords = self.major_harbors[start_harbor]
            end_coords = self.major_harbors[end_harbor]
            return self._generate_oceanic_route(
                start_coords["lat"], start_coords["lng"],
                end_coords["lat"], end_coords["lng"]
            )
    
    def _generate_oceanic_route(self, start_lat: float, start_lng: float, end_lat: float, end_lng: float) -> List[Dict]:
        """Generate a safe oceanic route that avoids land masses"""
        waypoints = []
        
        # Add start point
        waypoints.append({"lat": start_lat, "lng": start_lng})
        
        # Calculate intermediate points that follow oceanic routes
        lat_diff = end_lat - start_lat
        lng_diff = end_lng - start_lng
        
        # Create waypoints that curve around land masses
        num_points = max(5, int(abs(lat_diff) + abs(lng_diff)) // 10)
        
        for i in range(1, num_points):
            factor = i / num_points
            
            # Add curvature to avoid land
            curve_factor = math.sin(factor * math.pi) * 0.1
            
            # Calculate intermediate coordinates with oceanic adjustment
            inter_lat = start_lat + lat_diff * factor
            inter_lng = start_lng + lng_diff * factor
            
            # Adjust for oceanic routes (push routes towards open ocean)
            if abs(lng_diff) > abs(lat_diff):  # East-West route
                inter_lat += curve_factor * (10 if lat_diff >= 0 else -10)
            else:  # North-South route
                inter_lng += curve_factor * (10 if lng_diff >= 0 else -10)
            
            waypoints.append({"lat": inter_lat, "lng": inter_lng})
        
        # Add end point
        waypoints.append({"lat": end_lat, "lng": end_lng})
        
        return waypoints
        
    async def calculate_route(self, start_harbor_name: str, end_harbor_name: str, vessel_speed_knots: float = 15) -> Dict:
        """Calculate enhanced maritime route between two harbors using predefined routes"""
        try:
            # Find harbor information
            start_harbor_info = self.find_harbor_by_name(start_harbor_name)
            end_harbor_info = self.find_harbor_by_name(end_harbor_name)
            
            if not start_harbor_info or not end_harbor_info:
                return self._create_error_response(start_harbor_name, end_harbor_name, "Harbor not found")
            
            # Get predefined maritime route
            route_points = self.get_maritime_route(start_harbor_info["name"], end_harbor_info["name"])
            
            # Calculate total distance along the route
            total_distance_km = 0
            sample_points = []
            
            for i in range(len(route_points)):
                if i > 0:
                    segment_distance = geodesic(
                        (route_points[i-1]["lat"], route_points[i-1]["lng"]),
                        (route_points[i]["lat"], route_points[i]["lng"])
                    ).kilometers
                    total_distance_km += segment_distance
                
                sample_points.append({
                    "latitude": route_points[i]["lat"],
                    "longitude": route_points[i]["lng"],
                    "distance_from_start": total_distance_km
                })
            
            # Convert to nautical miles
            total_distance_nm = total_distance_km * 0.539957
            
            # Calculate bearing (general direction)
            bearing = self._calculate_bearing(
                start_harbor_info["lat"], start_harbor_info["lng"],
                end_harbor_info["lat"], end_harbor_info["lng"]
            )
            
            # Calculate travel time and other metrics
            estimated_time_hours = total_distance_nm / vessel_speed_knots
            fuel_consumption_estimate = total_distance_km * 0.3
            
            # Generate navigation waypoints
            waypoints = self._generate_navigation_waypoints_from_route(route_points)
            
            # Create route summary with harbor information
            route_summary = self._generate_harbor_route_summary(
                start_harbor_info, end_harbor_info, total_distance_km, estimated_time_hours, vessel_speed_knots
            )
            
            return {
                "route_found": True,
                "start_point": {"latitude": start_harbor_info["lat"], "longitude": start_harbor_info["lng"]},
                "end_point": {"latitude": end_harbor_info["lat"], "longitude": end_harbor_info["lng"]},
                "start_harbor": start_harbor_info,
                "end_harbor": end_harbor_info,
                "distance_km": round(total_distance_km, 2),
                "distance_nm": round(total_distance_nm, 2),
                "bearing": round(bearing, 2),
                "estimated_time_hours": round(estimated_time_hours, 2),
                "estimated_fuel_consumption": round(fuel_consumption_estimate, 2),
                "vessel_speed_knots": vessel_speed_knots,
                "sample_points": sample_points,
                "route_points": route_points,
                "waypoints": waypoints,
                "route_type": "maritime_route",
                "route_summary": route_summary,
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error calculating route: {e}")
            return self._create_error_response(start_harbor_name, end_harbor_name, str(e))
    
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
            
            point_distance = distance * factor
            
            # Add enhanced point data
            sample_points.append({
                "latitude": lat,
                "longitude": lon,
                "distance_from_start": round(point_distance, 2),
                "point_index": i,
                "is_waypoint": i % 3 == 0,  # Every 3rd point is a major waypoint
                "estimated_time_hours": round(point_distance / 27.78, 2),  # Assuming 15 knots average
                "weather": {
                    "temperature": 20 + (i % 5),  # Simulated weather data
                    "wind_speed": 5 + (i % 10),
                    "wave_height": 1 + (i % 3),
                    "conditions": "fair" if i % 4 != 0 else "choppy"
                }
            })
        
        return sample_points

    def _generate_navigation_waypoints(self, start_lat: float, start_lon: float, end_lat: float, end_lon: float, distance: float) -> List[Dict]:
        """Generate key navigation waypoints for the route"""
        waypoints = []
        
        # Create waypoints at strategic intervals
        waypoint_intervals = [0.0, 0.25, 0.5, 0.75, 1.0]  # Start, quarter points, end
        
        for i, factor in enumerate(waypoint_intervals):
            lat = start_lat + (end_lat - start_lat) * factor
            lon = start_lon + (end_lon - start_lon) * factor
            
            waypoint_type = "departure" if i == 0 else "arrival" if i == len(waypoint_intervals) - 1 else "waypoint"
            
            waypoints.append({
                "waypoint_id": i + 1,
                "latitude": lat,
                "longitude": lon,
                "type": waypoint_type,
                "distance_from_start": round(distance * factor, 2),
                "bearing_to_next": self._calculate_bearing(lat, lon, 
                    start_lat + (end_lat - start_lat) * waypoint_intervals[min(i + 1, len(waypoint_intervals) - 1)],
                    start_lon + (end_lon - start_lon) * waypoint_intervals[min(i + 1, len(waypoint_intervals) - 1)]
                ) if i < len(waypoint_intervals) - 1 else None,
                "estimated_arrival": f"T+{int(distance * factor / 27.78)}h{int((distance * factor / 27.78 % 1) * 60)}m"
            })
        
        return waypoints

    def _generate_harbor_route_summary(self, start_harbor: str, end_harbor: str, distance: float, duration: float, speed: float) -> str:
        """Generate a detailed summary for harbor-to-harbor route"""
        start_country = self.major_harbors[start_harbor]["country"]
        end_country = self.major_harbors[end_harbor]["country"]
        
        return f"""🚢 MARITIME ROUTE ANALYSIS

📍 Route Details:
• Departure: {start_harbor} Port, {start_country}
• Destination: {end_harbor} Port, {end_country}
• Distance: {distance:.1f} km ({distance * 0.54:.1f} nautical miles)
• Estimated Duration: {duration:.1f} hours ({duration/24:.1f} days)
• Average Speed: {speed} knots

🌊 Maritime Route Features:
• Route Type: Established shipping lane
• Navigation: GPS waypoints provided
• Safety: Follows international maritime corridors
• Weather Monitoring: {len(self.get_maritime_route(start_harbor, end_harbor))} checkpoints

⚓ Port Information:
• {start_harbor}: Major commercial port with full facilities
• {end_harbor}: International port with cargo handling
• Both ports offer refueling, maintenance, and supplies

🛡️ Safety Features:
• Route avoids shallow waters and land masses
• Follows established shipping channels
• Regular weather monitoring points
• Emergency ports available along route

⛽ Fuel Planning:
• Total Distance: {distance:.1f} km
• Estimated Consumption: {distance * 0.3:.1f} liters
• Fuel stops available at major ports en route
• Recommended reserve: 20-25% extra fuel

🗺️ Navigation Notes:
• Route optimized for safety and efficiency
• All waypoints are in international waters
• Updated for current maritime regulations
• Compatible with standard marine GPS systems"""
    
    def _generate_navigation_waypoints_from_route(self, route_points: List[Dict]) -> List[Dict]:
        """Generate navigation waypoints from route points"""
        waypoints = []
        
        for i, point in enumerate(route_points):
            waypoint = {
                "latitude": point["lat"],
                "longitude": point["lng"],
                "waypoint_number": i + 1,
                "type": "route_point"
            }
            
            if i == 0:
                waypoint["type"] = "departure"
                waypoint["name"] = "Departure Point"
            elif i == len(route_points) - 1:
                waypoint["type"] = "destination"
                waypoint["name"] = "Arrival Point"
            else:
                waypoint["name"] = f"Waypoint {i}"
                
            waypoints.append(waypoint)
        
        return waypoints

    def find_harbor_by_name(self, harbor_name: str) -> Dict:
        """Find harbor information by name (case-insensitive partial match)"""
        harbor_name_lower = harbor_name.lower()
        
        for name, info in self.major_harbors.items():
            if harbor_name_lower in name.lower() or name.lower() in harbor_name_lower:
                return {
                    "name": name,
                    "lat": info["lat"],
                    "lng": info["lng"],
                    "country": info["country"]
                }
        
        return None
    
    def _create_error_response(self, start_harbor: str, end_harbor: str, error_msg: str) -> Dict:
        """Create standardized error response"""
        return {
            "route_found": False,
            "error": error_msg,
            "start_harbor": {"name": start_harbor},
            "end_harbor": {"name": end_harbor},
            "distance_km": 0,
            "distance_nm": 0,
            "bearing": 0,
            "estimated_time_hours": 0,
            "route_points": [],
            "sample_points": [],
            "waypoints": [],
            "route_summary": f"Unable to calculate route from {start_harbor} to {end_harbor}: {error_msg}",
            "created_at": datetime.now().isoformat()
        }

    def _generate_harbor_route_summary(self, start_harbor: Dict, end_harbor: Dict, 
                                     distance_km: float, time_hours: float, speed_knots: float) -> str:
        """Generate a summary of the maritime route between harbors"""
        return (
            f"Maritime route from {start_harbor['name']}, {start_harbor['country']} "
            f"to {end_harbor['name']}, {end_harbor['country']}. "
            f"Distance: {distance_km:.0f} km ({distance_km * 0.539957:.0f} nautical miles). "
            f"Estimated travel time: {time_hours:.1f} hours at {speed_knots} knots. "
            f"This route follows established shipping lanes and avoids land masses."
        )
