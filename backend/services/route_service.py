import math
from typing import Dict, List, Tuple
from geopy.distance import geodesic
import requests
from services.weather_service import WeatherService

class RouteService:
    def __init__(self):
        self.weather_service = WeatherService()
        
    async def calculate_route(self, start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> Dict:
        """Calculate route between two points with sample points for weather analysis"""
        try:
            # Calculate great circle distance
            start_point = (start_lat, start_lon)
            end_point = (end_lat, end_lon)
            distance = geodesic(start_point, end_point).kilometers
            
            # Calculate bearing
            bearing = self._calculate_bearing(start_lat, start_lon, end_lat, end_lon)
            
            # Generate sample points along the route
            sample_points = self._generate_sample_points(start_lat, start_lon, end_lat, end_lon, distance)
            
            # Estimate travel time (assuming average speed of 20 knots = 37 km/h)
            estimated_duration = distance / 37.0  # hours
            
            return {
                "start_point": {"latitude": start_lat, "longitude": start_lon},
                "end_point": {"latitude": end_lat, "longitude": end_lon},
                "distance": round(distance, 2),
                "bearing": round(bearing, 2),
                "estimated_duration": round(estimated_duration, 2),
                "sample_points": sample_points
            }
            
        except Exception as e:
            print(f"Error calculating route: {e}")
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
