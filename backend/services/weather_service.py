import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from dotenv import load_dotenv

load_dotenv()

class WeatherService:
    def __init__(self):
        # Base endpoints
        self.open_meteo_base_url = "https://api.open-meteo.com/v1"
        self.marine_meteo_base_url = "https://marine-api.open-meteo.com/v1"
        self.stormglass_base_url = "https://api.stormglass.io/v2"
        # API keys
        self.stormglass_api_key = os.getenv("STORMGLASS_API_KEY")
        
    async def get_current_weather(self, latitude: float, longitude: float) -> Dict:
        """Get current weather data from Open-Meteo API"""
        try:
            url = f"{self.open_meteo_base_url}/forecast"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                # Only valid 'current' variables for standard forecast endpoint
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,pressure_msl,visibility",
                # We removed wave_height,wave_period because they belong to marine API endpoint
                "timezone": "auto"
            }

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            current = data.get("current", {})

            # Fetch marine (wave) data separately (best effort; ignore failures)
            wave_height = None
            wave_period = None
            try:
                marine_url = f"{self.marine_meteo_base_url}/marine"
                marine_params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "hourly": "wave_height,wave_period",
                    "timezone": "auto"
                }
                m_resp = requests.get(marine_url, params=marine_params, timeout=10)
                if m_resp.status_code == 200:
                    m_data = m_resp.json()
                    m_hourly = m_data.get("hourly", {})
                    wave_height_list = m_hourly.get("wave_height") or []
                    wave_period_list = m_hourly.get("wave_period") or []
                    wave_height = wave_height_list[0] if wave_height_list else None
                    wave_period = wave_period_list[0] if wave_period_list else None
            except Exception:
                pass

            # Calculate hazard probabilities (pass placeholder hourly dict containing wave data if present)
            hourly_placeholder = {"wave_height": [wave_height] if wave_height is not None else [],
                                  "wave_period": [wave_period] if wave_period is not None else []}
            hazard_probabilities = self._calculate_hazard_probabilities(current, hourly_placeholder)

            return {
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": datetime.utcnow().isoformat(),
                "temperature": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "wind_speed": current.get("wind_speed_10m"),
                "wind_direction": current.get("wind_direction_10m"),
                "pressure": current.get("pressure_msl"),
                "visibility": current.get("visibility"),
                "wave_height": wave_height,
                "wave_period": wave_period,
                "weather_condition": self._determine_weather_condition(current),
                "hazard_probabilities": hazard_probabilities
            }
        except Exception as e:
            print(f"Error fetching current weather: {e}")
            return self._get_default_weather_data(latitude, longitude)
    
    async def get_forecast(self, latitude: float, longitude: float, days: int = 7) -> Dict:
        """Get weather forecast for specified days"""
        try:
            url = f"{self.open_meteo_base_url}/forecast"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": "temperature_2m_max,temperature_2m_min,wind_speed_10m_max,wind_direction_10m_dominant,precipitation_sum,precipitation_probability_max",
                # Remove wave parameters from standard forecast call
                "hourly": "visibility",
                "forecast_days": days,
                "timezone": "auto"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Get current weather
            current = await self.get_current_weather(latitude, longitude)
            
            # Process forecast data
            daily = data.get("daily", {})
            hourly = data.get("hourly", {})

            # Optionally fetch marine wave data for forecast (best effort)
            wave_heights = []
            wave_periods = []
            try:
                marine_url = f"{self.marine_meteo_base_url}/marine"
                marine_params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "hourly": "wave_height,wave_period",
                    "timezone": "auto"
                }
                m_resp = requests.get(marine_url, params=marine_params, timeout=10)
                if m_resp.status_code == 200:
                    m_data = m_resp.json()
                    wave_heights = m_data.get("hourly", {}).get("wave_height", [])
                    wave_periods = m_data.get("hourly", {}).get("wave_period", [])
            except Exception:
                pass
            
            forecast = []
            for i in range(days):
                day_data = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "timestamp": (datetime.utcnow() + timedelta(days=i)).isoformat(),
                    "temperature": (daily.get("temperature_2m_max", [0])[i] + daily.get("temperature_2m_min", [0])[i]) / 2,
                    "wind_speed": daily.get("wind_speed_10m_max", [0])[i],
                    "wind_direction": daily.get("wind_direction_10m_dominant", [0])[i],
                    "precipitation": daily.get("precipitation_sum", [0])[i],
                    "precipitation_probability": daily.get("precipitation_probability_max", [0])[i],
                    "wave_height": wave_heights[i] if i < len(wave_heights) else None,
                    "wave_period": wave_periods[i] if i < len(wave_periods) else None,
                    "visibility": hourly.get("visibility", [0])[i] if hourly.get("visibility") else None,
                    "hazard_probabilities": self._calculate_daily_hazard_probabilities(daily, i)
                }
                forecast.append(day_data)
            
            return {
                "current": current,
                "forecast": forecast
            }
        except Exception as e:
            print(f"Error fetching forecast: {e}")
            return {"current": await self.get_current_weather(latitude, longitude), "forecast": []}
    
    async def get_location_details(self, latitude: float, longitude: float) -> Dict:
        """Get location details using reverse geocoding"""
        try:
            # Use OpenStreetMap Nominatim for reverse geocoding
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                "lat": latitude,
                "lon": longitude,
                "format": "json",
                "addressdetails": 1,
                "zoom": 10
            }
            headers = {
                "User-Agent": "WeatherApp/1.0"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract location information
            address = data.get("address", {})
            
            # Determine the best name for the location
            name_parts = []
            if address.get("city"):
                name_parts.append(address["city"])
            elif address.get("town"):
                name_parts.append(address["town"])
            elif address.get("village"):
                name_parts.append(address["village"])
            elif address.get("hamlet"):
                name_parts.append(address["hamlet"])
            
            if address.get("state"):
                name_parts.append(address["state"])
            elif address.get("county"):
                name_parts.append(address["county"])
            
            if address.get("country"):
                name_parts.append(address["country"])
            
            # If no specific location found, check if it's in the ocean
            if not name_parts:
                if address.get("country") == "Ocean":
                    name_parts = ["Ocean"]
                else:
                    name_parts = [f"Location {latitude:.4f}, {longitude:.4f}"]
            
            location_name = ", ".join(name_parts)
            
            return {
                "name": location_name,
                "country": address.get("country"),
                "state": address.get("state") or address.get("county"),
                "city": address.get("city") or address.get("town") or address.get("village"),
                "display_name": data.get("display_name"),
                "latitude": latitude,
                "longitude": longitude
            }
            
        except Exception as e:
            print(f"Error fetching location details: {e}")
            # Return default location info if reverse geocoding fails
            return {
                "name": f"Location {latitude:.4f}, {longitude:.4f}",
                "country": None,
                "state": None,
                "city": None,
                "display_name": f"Location at {latitude:.4f}, {longitude:.4f}",
                "latitude": latitude,
                "longitude": longitude
            }
    
    async def fetch_ir_content(self, latitude: Optional[float] = None, longitude: Optional[float] = None) -> List[Dict]:
        """Fetch IR content from government sources and RSS feeds"""
        ir_content = []
        
        try:
            # NOAA Marine Weather
            noaa_content = await self._fetch_noaa_content(latitude, longitude)
            ir_content.extend(noaa_content)
            
            # NWS Warnings
            nws_content = await self._fetch_nws_content(latitude, longitude)
            ir_content.extend(nws_content)
            
            # Additional marine weather sources
            marine_content = await self._fetch_marine_weather_content(latitude, longitude)
            ir_content.extend(marine_content)
            
        except Exception as e:
            print(f"Error fetching IR content: {e}")
        
        return ir_content
    
    def _calculate_hazard_probabilities(self, current: Dict, hourly: Dict) -> Dict:
        """Calculate hazard probabilities based on current conditions"""
        probabilities = {
            "storm": 0.0,
            "fog": 0.0,
            "tsunami": 0.0,
            "high_wind": 0.0,
            "rough_sea": 0.0
        }
        
        wind_speed = current.get("wind_speed_10m", 0)
        visibility = current.get("visibility", 10000)
        wave_height = hourly.get("wave_height", [0])[0] if hourly.get("wave_height") else 0
        
        # High wind probability
        if wind_speed > 30:
            probabilities["high_wind"] = min(1.0, (wind_speed - 30) / 30)
        
        # Storm probability (based on wind and pressure)
        if wind_speed > 25:
            probabilities["storm"] = min(1.0, (wind_speed - 25) / 25)
        
        # Fog probability
        if visibility < 1000:
            probabilities["fog"] = min(1.0, (1000 - visibility) / 1000)
        
        # Rough sea probability
        if wave_height > 2.0:
            probabilities["rough_sea"] = min(1.0, (wave_height - 2.0) / 3.0)
        
        return probabilities
    
    def _calculate_daily_hazard_probabilities(self, daily: Dict, day_index: int) -> Dict:
        """Calculate hazard probabilities for a specific day"""
        probabilities = {
            "storm": 0.0,
            "fog": 0.0,
            "tsunami": 0.0,
            "high_wind": 0.0,
            "rough_sea": 0.0
        }
        
        wind_speed = daily.get("wind_speed_10m_max", [0])[day_index]
        precipitation_prob = daily.get("precipitation_probability_max", [0])[day_index]
        
        # Storm probability
        if wind_speed > 25 and precipitation_prob > 50:
            probabilities["storm"] = min(1.0, (wind_speed - 25) / 25 * precipitation_prob / 100)
        
        # High wind probability
        if wind_speed > 30:
            probabilities["high_wind"] = min(1.0, (wind_speed - 30) / 30)
        
        return probabilities
    
    def _determine_weather_condition(self, current: Dict) -> str:
        """Determine weather condition based on current data"""
        wind_speed = current.get("wind_speed_10m", 0)
        visibility = current.get("visibility", 10000)
        
        if wind_speed > 50:
            return "Gale"
        elif wind_speed > 30:
            return "Strong Wind"
        elif visibility < 1000:
            return "Fog"
        elif visibility < 5000:
            return "Poor Visibility"
        else:
            return "Clear"
    
    def _get_default_weather_data(self, latitude: float, longitude: float) -> Dict:
        """Return default weather data when API fails"""
        return {
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": datetime.utcnow().isoformat(),
            "temperature": 20.0,
            "humidity": 70.0,
            "wind_speed": 10.0,
            "wind_direction": 180.0,
            "pressure": 1013.25,
            "visibility": 10000.0,
            "wave_height": 1.0,
            "wave_period": 8.0,
            "weather_condition": "Clear",
            "hazard_probabilities": {"storm": 0.0, "fog": 0.0, "tsunami": 0.0, "high_wind": 0.0, "rough_sea": 0.0}
        }
    
    async def _fetch_noaa_content(self, latitude: Optional[float], longitude: Optional[float]) -> List[Dict]:
        """Fetch NOAA marine weather content"""
        # This would integrate with NOAA APIs
        # For now, return sample data
        return [
            {
                "source": "NOAA",
                "type": "marine_forecast",
                "title": "Marine Weather Forecast",
                "content": "Gale warning in effect for coastal waters. Winds 30-40 knots expected.",
                "location_coverage": {"latitude": latitude, "longitude": longitude} if latitude and longitude else None,
                "severity": "moderate",
                "valid_from": datetime.utcnow().isoformat(),
                "valid_until": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
        ]
    
    async def _fetch_nws_content(self, latitude: Optional[float], longitude: Optional[float]) -> List[Dict]:
        """Fetch NWS weather warnings"""
        # This would integrate with NWS APIs
        return []
    
    async def _fetch_marine_weather_content(self, latitude: Optional[float], longitude: Optional[float]) -> List[Dict]:
        """Fetch additional marine weather content"""
        # This would integrate with other marine weather sources
        return []
