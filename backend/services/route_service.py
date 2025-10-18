import os
import math
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from geopy.distance import geodesic
from pyproj import Geod
import geopandas as gpd
from shapely.geometry import Point, GeometryCollection

# Keep your project's WeatherService import (adjust path if needed)
from services.weather_service import WeatherService


class RouteService:
    """
    RouteService:
      - predefined maritime routes
      - land-avoidance checks using Natural Earth polygons (with robust fallback)
      - route generation, distance/bearing, and weather-analysis hooks
    """

    def __init__(self, samples_per_segment: int = 30):
        self.weather_service = WeatherService()

        # --- Harbors ---
        self.major_harbors: Dict[str, Dict] = {
            "Chennai": {"lat": 13.0827, "lng": 80.2707, "country": "India"},
            "Mumbai": {"lat": 19.0760, "lng": 72.8777, "country": "India"},
            "Singapore": {"lat": 1.3521, "lng": 103.8198, "country": "Singapore"},
            "Shanghai": {"lat": 31.2304, "lng": 121.4737, "country": "China"},
            "Colombo": {"lat": 6.9271, "lng": 79.8612, "country": "Sri Lanka"},
        }

        # --- Predefined maritime routes (kept from your original dataset) ---
        self.maritime_routes: Dict[Tuple[str, str], List[Dict]] = {
            ("Chennai", "Mumbai"): [
                {"lat": 13.0827, "lng": 80.2707},
                {"lat": 12.5, "lng": 81.5},
                {"lat": 10.5, "lng": 83.0},
                {"lat": 7.5, "lng": 84.0},
                {"lat": 5.5, "lng": 80.0},
                {"lat": 7.5, "lng": 77.5},
                {"lat": 9.5, "lng": 75.5},
                {"lat": 12.0, "lng": 73.5},
                {"lat": 15.0, "lng": 72.8},
                {"lat": 19.0760, "lng": 72.8777},
            ],
            ("Chennai", "Singapore"): [
                {"lat": 13.0827, "lng": 80.2707},
                {"lat": 12.5, "lng": 82.0},
                {"lat": 11.0, "lng": 85.0},
                {"lat": 9.5, "lng": 88.0},
                {"lat": 8.0, "lng": 91.0},
                {"lat": 6.5, "lng": 94.0},
                {"lat": 6.412144, "lng": 97.141792},
                {"lat": 3.5, "lng": 100.0},
                {"lat": 2.0, "lng": 102.0},
                {"lat": 1.3521, "lng": 103.8198},
            ],
            ("Chennai", "Shanghai"): [
                {"lat": 13.0827, "lng": 80.2707},
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
                {"lat": 31.2304, "lng": 121.4737},
            ],
           


            ("Chennai", "Colombo"): [
                {"lat": 13.0827, "lng": 80.2707},  
                {"lat": 12.5, "lng": 80.4},        
                {"lat": 11.5, "lng": 80.5},        
                {"lat": 10.5, "lng": 80.3},        
                {"lat":9.44655,"lng":79.508824},        
                {"lat": 9.0, "lng": 79.6},         
                {"lat": 8.5, "lng": 79.6},         
                {"lat": 7.5, "lng": 79.7},       
                {"lat": 6.9271, "lng": 79.8612}    
            ],

           ("Mumbai", "Colombo"): [
               {"lat": 19.0760, "lng": 72.8777},
               {"lat": 17.5, "lng": 72.8},
               {"lat": 15.8, "lng": 73.0},
               {"lat": 13.5, "lng": 74.0},
               {"lat": 11.0, "lng": 75.5},
               {"lat": 7.4, "lng": 76.8},
               {"lat": 7.5, "lng": 78.0},
               {"lat": 6.9271, "lng": 79.8612}
           ],

            ("Mumbai", "Singapore"): [
                {"lat": 19.0760, "lng": 72.8777},
                {"lat": 17.0, "lng": 74.0},
                {"lat": 14.0, "lng": 76.0},
                {"lat": 11.0, "lng": 78.0},
                {"lat": 8.0, "lng": 81.0},
                {"lat": 6.412144, "lng": 97.141792},
                {"lat": 3.0, "lng": 90.0},
                
                {"lat": 2.0, "lng": 95.0},
                {"lat": 1.5, "lng": 100.0},
                {"lat": 1.2, "lng": 103.8198},
                {"lat": 1.3521, "lng": 103.8198},
            ],
            ("Mumbai", "Shanghai"): [
                {"lat": 19.0760, "lng": 72.8777},
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
                {"lat": 31.2304, "lng": 121.4737},
            ],
            # REMOVE THIS DUPLICATE - it's already defined above at line 90
            # ("Mumbai", "Colombo"): [ ... ]
            
            ("Singapore", "Shanghai"): [
                {"lat": 1.3521, "lng": 103.8198},
                {"lat": 3.0, "lng": 105.0},
                {"lat": 5.0, "lng": 107.0},
                {"lat": 8.0, "lng": 109.0},
                {"lat": 12.0, "lng": 111.0},
                {"lat": 16.0, "lng": 113.0},
                {"lat": 20.0, "lng": 115.0},
                {"lat": 24.0, "lng": 117.0},
                {"lat": 28.0, "lng": 119.0},
                {"lat": 31.2304, "lng": 121.4737},
            ],
            ("Singapore", "Colombo"): [
                {"lat": 1.3521, "lng": 103.8198},  
                       
                
                {"lat":2.199114,"lng":101.838026},       
                {"lat":3.718648,"lng":100.112985},
                {"lat":6.783205,"lng":97.492549},     
                {"lat":5.800404,"lng":92.086686},
                {"lat":5.023573,"lng":80.090392},
                {"lat": 6.9271, "lng": 79.8612}
            ],
            ("Shanghai", "Colombo"): [
                {"lat": 31.2304, "lng": 121.4737},
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
                
                {"lat": 6.9271, "lng": 79.8612},
            ],
        }

        # geodetic helper (WGS84)
        self._geod = Geod(ellps="WGS84")

        # --- Load Natural Earth (robustly) ---
        world = None
        try:
            # Preferred: old convenience (may not exist in geopandas >= 1.0)
            data_path = gpd.datasets.get_path("naturalearth_lowres")
            world = gpd.read_file(data_path)
        except Exception:
            # Fallback: attempt reading a small countries GeoJSON from GitHub
            fallback_url = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"
            try:
                world = gpd.read_file(fallback_url)
            except Exception:
                # Fallback 2: download & cache locally
                try:
                    import requests
                    cache_dir = os.path.join(os.path.dirname(__file__), "data")
                    os.makedirs(cache_dir, exist_ok=True)
                    cached_file = os.path.join(cache_dir, "countries.geojson")
                    if not os.path.exists(cached_file):
                        resp = requests.get(fallback_url, timeout=15)
                        resp.raise_for_status()
                        with open(cached_file, "wb") as fh:
                            fh.write(resp.content)
                    world = gpd.read_file(cached_file)
                except Exception:
                    # Ultimate fallback: empty GeoDataFrame (route service will treat everything as water)
                    print("[RouteService] Warning: couldn't load Natural Earth polygons; land checks disabled.")
                    world = gpd.GeoDataFrame()

        # Build union geometry (if available)
        if world is None or world.empty:
            self._land_union = GeometryCollection()
        else:
            self._land_union = world.unary_union

        # Optionally run route fixer here (comment out to avoid expensive startup work)
        try:
            # self.maritime_routes = self._fix_all_routes(self.maritime_routes, samples_per_segment=samples_per_segment)
            # Commented out by default for faster startup during development.
            pass
        except Exception as e:
            print(f"[RouteService] Route fix failed during init: {e}")

    # -------------------------
    # Basic helpers
    # -------------------------
    def _is_land(self, lat: float, lon: float) -> bool:
        """Return True if (lat, lon) is on land according to loaded polygons."""
        try:
            return self._land_union.contains(Point(lon, lat))
        except Exception:
            return False

    def _interpolate_segment(self, a: Dict, b: Dict, n_samples: int = 30) -> List[Tuple[float, float]]:
        if n_samples <= 1:
            return []
        pts = self._geod.npts(a["lng"], a["lat"], b["lng"], b["lat"], max(n_samples - 1, 1))
        return [(lat, lon) for (lon, lat) in pts]

    def _bearing_and_distance(self, from_lat: float, from_lon: float, to_lat: float, to_lon: float):
        az12, az21, dist = self._geod.inv(from_lon, from_lat, to_lon, to_lat)
        return az12, az21, dist

    def _move_along_bearing_until_water(self, lat: float, lon: float, bearing_deg: float,
                                       step_km: float = 5, max_km: float = 200) -> Optional[Tuple[float, float]]:
        steps = max(int(max_km / step_km), 1)
        for i in range(1, steps + 1):
            dist_m = i * step_km * 1000
            try:
                lon2, lat2, _ = self._geod.fwd(lon, lat, bearing_deg, dist_m)
            except Exception:
                continue
            if not self._is_land(lat2, lon2):
                return lat2, lon2
        return None

    def _find_nearest_water_from_point(self, lat: float, lon: float,
                                       target_lat: Optional[float] = None, target_lon: Optional[float] = None) -> Optional[Tuple[float, float]]:
        bearings: List[float] = []
        if target_lat is not None and target_lon is not None:
            try:
                az, _, _ = self._bearing_and_distance(lat, lon, target_lat, target_lon)
                bearings.append(az)
            except Exception:
                pass
        bearings.extend([0, 90, 180, 270])

        for bearing in bearings:
            res = self._move_along_bearing_until_water(lat, lon, bearing, step_km=5, max_km=500)
            if res:
                return res

        for b in range(0, 360, 30):
            res = self._move_along_bearing_until_water(lat, lon, b, step_km=5, max_km=500)
            if res:
                return res

        return None

    def _clean_route_points(self, route_points: List[Dict], samples_per_segment: int = 30) -> List[Dict]:
        if not route_points:
            return []
        cleaned: List[Dict] = [route_points[0]]
        for i in range(len(route_points) - 1):
            a = route_points[i]
            b = route_points[i + 1]
            samples = self._interpolate_segment(a, b, n_samples=samples_per_segment)
            for (s_lat, s_lon) in samples:
                if self._is_land(s_lat, s_lon):
                    candidate = self._find_nearest_water_from_point(s_lat, s_lon, target_lat=b["lat"], target_lon=b["lng"])
                    if candidate:
                        cleaned.append({"lat": candidate[0], "lng": candidate[1]})
                    else:
                        cleaned.append({"lat": s_lat, "lng": s_lon})
                else:
                    cleaned.append({"lat": s_lat, "lng": s_lon})
            cleaned.append(b)

        simplified: List[Dict] = [cleaned[0]]
        for p in cleaned[1:]:
            prev = simplified[-1]
            if abs(prev["lat"] - p["lat"]) < 1e-6 and abs(prev["lng"] - p["lng"]) < 1e-6:
                continue
            simplified.append(p)
        return simplified

    def _fix_all_routes(self, maritime_routes: Dict[Tuple[str, str], List[Dict]], samples_per_segment: int = 30) -> Dict:
        fixed: Dict = {}
        for key, points in maritime_routes.items():
            try:
                fixed_points = self._clean_route_points(points, samples_per_segment=samples_per_segment)
                land_before = sum(1 for p in points if self._is_land(p["lat"], p["lng"]))
                land_after = sum(1 for p in fixed_points if self._is_land(p["lat"], p["lng"]))
                print(f"[RouteService] Route {key}: land points before={land_before}, after={land_after}, pts_before={len(points)}, pts_after={len(fixed_points)}")
                fixed[key] = fixed_points
            except Exception as e:
                print(f"[RouteService] Failed to fix route {key}: {e}")
                fixed[key] = points
        return fixed

    # -------------------------
    # Harbor / route utilities
    # -------------------------
    def find_harbor_by_name(self, harbor_name: str) -> Optional[Dict]:
        if not harbor_name:
            return None
        # Normalize the harbor name - strip common suffixes
        harbor_name_normalized = harbor_name.lower().strip()
        for suffix in [' port', ' harbor', ' harbour', ' seaport', ' bay']:
            if harbor_name_normalized.endswith(suffix):
                harbor_name_normalized = harbor_name_normalized[:-len(suffix)].strip()
                break
        
        # Try exact match first (case insensitive)
        for name, info in self.major_harbors.items():
            if harbor_name_normalized == name.lower():
                return {"name": name, "lat": info["lat"], "lng": info["lng"], "country": info["country"]}
        
        # Try partial match
        for name, info in self.major_harbors.items():
            if harbor_name_normalized in name.lower() or name.lower() in harbor_name_normalized:
                return {"name": name, "lat": info["lat"], "lng": info["lng"], "country": info["country"]}
        return None

    def get_maritime_route(self, start_harbor: str, end_harbor: str) -> List[Dict]:
        # Normalize harbor names by finding them in major_harbors
        start_harbor_info = self.find_harbor_by_name(start_harbor)
        end_harbor_info = self.find_harbor_by_name(end_harbor)
        
        if not start_harbor_info or not end_harbor_info:
            # If we can't find the harbors, return empty
            return []
        
        # Use the normalized names from major_harbors
        start_name = start_harbor_info["name"]
        end_name = end_harbor_info["name"]
        
        # Check if we have a hardcoded route
        route_key = (start_name, end_name)
        reverse_key = (end_name, start_name)
        
        if route_key in self.maritime_routes:
            return self.maritime_routes[route_key]
        if reverse_key in self.maritime_routes:
            return list(reversed(self.maritime_routes[reverse_key]))
        
        # Fall back to generated route using coordinates
        start_coords = self.major_harbors.get(start_name)
        end_coords = self.major_harbors.get(end_name)
        
        if start_coords is None or end_coords is None:
            return []
        
        return self._generate_oceanic_route(start_coords["lat"], start_coords["lng"], end_coords["lat"], end_coords["lng"])

    def _generate_oceanic_route(self, start_lat: float, start_lng: float, end_lat: float, end_lng: float) -> List[Dict]:
        waypoints: List[Dict] = [{"lat": start_lat, "lng": start_lng}]
        lat_diff = end_lat - start_lat
        lng_diff = end_lng - start_lng
        num_points = max(5, int((abs(lat_diff) + abs(lng_diff)) // 5))
        for i in range(1, num_points):
            factor = i / num_points
            curve_factor = math.sin(factor * math.pi) * 0.1
            inter_lat = start_lat + lat_diff * factor
            inter_lng = start_lng + lng_diff * factor
            if abs(lng_diff) > abs(lat_diff):
                inter_lat += curve_factor * (10 if lat_diff >= 0 else -10)
            else:
                inter_lng += curve_factor * (10 if lng_diff >= 0 else -10)
            waypoints.append({"lat": inter_lat, "lng": inter_lng})
        waypoints.append({"lat": end_lat, "lng": end_lng})
        return waypoints

    def _calculate_bearing(self, start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> float:
        lat1 = math.radians(start_lat)
        lat2 = math.radians(end_lat)
        delta_lon = math.radians(end_lon - start_lon)
        y = math.sin(delta_lon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        return bearing

    def _generate_navigation_waypoints_from_route(self, route_points: List[Dict]) -> List[Dict]:
        waypoints: List[Dict] = []
        for i, p in enumerate(route_points):
            waypoint = {
                "latitude": p["lat"],
                "longitude": p["lng"],
                "waypoint_number": i + 1,
                "type": "route_point",
                "name": ("Departure Point" if i == 0 else "Arrival Point" if i == len(route_points) - 1 else f"Waypoint {i}")
            }
            waypoints.append(waypoint)
        return waypoints

    def _generate_enhanced_sample_points(self, start_lat: float, start_lon: float, end_lat: float, end_lon: float,
                                         distance_km: float) -> List[Dict]:
        sample_points: List[Dict] = []
        num_points = max(10, int(distance_km / 25))  # every ~25km
        for i in range(num_points + 1):
            factor = i / num_points if num_points > 0 else 0
            lat = start_lat + (end_lat - start_lat) * factor
            lon = start_lon + (end_lon - start_lon) * factor
            point_distance = distance_km * factor
            sample_points.append({
                "latitude": lat,
                "longitude": lon,
                "distance_from_start": round(point_distance, 2),
                "point_index": i,
                "is_waypoint": i % 3 == 0,
            })
        return sample_points

    # -------------------------
    # Public route calculation & analysis
    # -------------------------
    async def calculate_route(self, start_harbor_name: str, end_harbor_name: str, vessel_speed_knots: float = 15.0) -> Dict:
        try:
            start_h = self.find_harbor_by_name(start_harbor_name)
            end_h = self.find_harbor_by_name(end_harbor_name)
            if not start_h or not end_h:
                return self._create_error_response(start_harbor_name, end_harbor_name, "Harbor not found")

            route_points = self.get_maritime_route(start_h["name"], end_h["name"])
            if not route_points:
                return self._create_error_response(start_harbor_name, end_harbor_name, "No route available")

            total_distance_km = 0.0
            sample_points: List[Dict] = []
            for i, rp in enumerate(route_points):
                if i > 0:
                    seg_km = geodesic((route_points[i-1]["lat"], route_points[i-1]["lng"]),
                                      (rp["lat"], rp["lng"])).kilometers
                    total_distance_km += seg_km
                sample_points.append({
                    "latitude": rp["lat"],
                    "longitude": rp["lng"],
                    "distance_from_start": round(total_distance_km, 3)
                })

            total_distance_nm = total_distance_km * 0.539957
            bearing = self._calculate_bearing(start_h["lat"], start_h["lng"], end_h["lat"], end_h["lng"])
            estimated_time_hours = total_distance_nm / max(vessel_speed_knots, 0.1)
            estimated_fuel_consumption = total_distance_km * 0.3

            waypoints = self._generate_navigation_waypoints_from_route(route_points)
            enhanced_samples = self._generate_enhanced_sample_points(start_h["lat"], start_h["lng"],
                                                                     end_h["lat"], end_h["lng"], total_distance_km)

            route_summary_text = self._generate_harbor_route_summary(start_h, end_h, total_distance_km, estimated_time_hours, vessel_speed_knots)

            return {
                "route_found": True,
                "start_point": {"latitude": start_h["lat"], "longitude": start_h["lng"]},
                "end_point": {"latitude": end_h["lat"], "longitude": end_h["lng"]},
                "start_harbor": start_h,
                "end_harbor": end_h,
                "distance_km": round(total_distance_km, 2),
                "distance_nm": round(total_distance_nm, 2),
                "bearing": round(bearing, 2),
                "estimated_time_hours": round(estimated_time_hours, 2),
                "estimated_fuel_consumption": round(estimated_fuel_consumption, 2),
                "vessel_speed_knots": vessel_speed_knots,
                "sample_points": sample_points,
                "route_points": route_points,
                "waypoints": waypoints,
                "enhanced_sample_points": enhanced_samples,
                "route_type": "maritime_route",
                "route_summary": route_summary_text,
                "created_at": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[RouteService] Error calculating route: {e}")
            return self._create_error_response(start_harbor_name, end_harbor_name, str(e))

    async def analyze_route_weather(self, sample_points: List[Dict]) -> Dict:
        weather_analysis = {"points": [], "hazard_summary": {}, "risk_zones": []}
        try:
            for i, point in enumerate(sample_points):
                weather_data = await self.weather_service.get_current_weather(point["latitude"], point["longitude"])
                hazard_level = self._calculate_point_hazard_level(weather_data)
                point_analysis = {
                    "point_index": i,
                    "distance_from_start": point.get("distance_from_start", 0),
                    "latitude": point["latitude"],
                    "longitude": point["longitude"],
                    "weather": weather_data,
                    "hazard_level": hazard_level
                }
                weather_analysis["points"].append(point_analysis)
                if hazard_level > 0.7:
                    weather_analysis["risk_zones"].append({
                        "start_distance": point.get("distance_from_start", 0),
                        "end_distance": point.get("distance_from_start", 0) + 20,
                        "hazard_level": hazard_level,
                        "hazards": self._identify_hazards(weather_data)
                    })
            weather_analysis["hazard_summary"] = self._generate_hazard_summary(weather_analysis["points"])
        except Exception as e:
            print(f"[RouteService] Error analyzing route weather: {e}")
        return weather_analysis

    def _calculate_point_hazard_level(self, weather_data: Dict) -> float:
        hazard_probabilities = weather_data.get("hazard_probabilities", {}) if isinstance(weather_data, dict) else {}
        weights = {"storm": 0.4, "high_wind": 0.3, "rough_sea": 0.2, "fog": 0.1}
        total = 0.0
        for hazard, prob in hazard_probabilities.items():
            weight = weights.get(hazard, 0.1)
            try:
                total += float(prob) * weight
            except Exception:
                continue
        return min(1.0, total)

    def _identify_hazards(self, weather_data: Dict) -> List[str]:
        hazards = []
        hazard_probabilities = weather_data.get("hazard_probabilities", {}) if isinstance(weather_data, dict) else {}
        for hazard, prob in hazard_probabilities.items():
            try:
                if float(prob) > 0.5:
                    hazards.append(hazard)
            except Exception:
                continue
        return hazards

    def _generate_hazard_summary(self, points: List[Dict]) -> Dict:
        total_points = len(points)
        high = sum(1 for p in points if p.get("hazard_level", 0) > 0.7)
        med = sum(1 for p in points if 0.4 < p.get("hazard_level", 0) <= 0.7)
        overall = "Low"
        if high > total_points * 0.3:
            overall = "High"
        elif med > total_points * 0.3:
            overall = "Medium"
        safe_pct = round((total_points - high) / total_points * 100, 1) if total_points > 0 else 100.0
        return {"total_points": total_points, "high_hazard_points": high, "medium_hazard_points": med, "overall_risk_level": overall, "safe_percentage": safe_pct}

    def _create_error_response(self, start_harbor: str, end_harbor: str, error_msg: str) -> Dict:
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
        return (
            f"Maritime route from {start_harbor['name']}, {start_harbor.get('country','')} "
            f"to {end_harbor['name']}, {end_harbor.get('country','')}. "
            f"Distance: {distance_km:.1f} km ({distance_km * 0.539957:.1f} nm). "
            f"ETA: {time_hours:.1f} hours at {speed_knots} knots."
        )
