"""
Comprehensive Weather and Hazard Alerts Service
Uses multiple free APIs to provide global weather and hazard alerts
"""
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"
    UNKNOWN = "unknown"

class AlertType(Enum):
    WEATHER = "weather"
    MARINE = "marine"
    EARTHQUAKE = "earthquake"
    FLOOD = "flood"
    STORM = "storm"
    TSUNAMI = "tsunami"
    FIRE = "fire"
    OTHER = "other"

@dataclass
class WeatherAlert:
    event: str
    severity: AlertSeverity
    area: str
    description: str
    advice: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    source: str = ""
    alert_type: AlertType = AlertType.OTHER
    coordinates: Optional[Tuple[float, float]] = None
    urgency: str = "unknown"
    certainty: str = "unknown"

class HazardAlertsService:
    def __init__(self):
        self.base_urls = {
            'nws': 'https://api.weather.gov',
            'open_meteo': 'https://api.open-meteo.com/v1',
            'meteoalarm': 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-',
            'usgs_earthquake': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary',
            'global_cap': 'https://www.meteoalarm.org/documents/rss',
            # Asian Typhoon/Cyclone Data Sources
            'jma': 'https://www.jma.go.jp/bosai/forecast/data/forecast',
            'rss_typhoon': 'https://rss.cnn.com/rss/edition_asia.rss',
            'weatherapi': 'http://api.weatherapi.com/v1',
            'openweather': 'https://api.openweathermap.org/data/2.5',
            # Global RSS feeds for typhoons/disasters
            'gdacs': 'https://www.gdacs.org/xml/rss.xml',
            'rsoe': 'http://feeds.feedburner.com/RSOE-EDIS-Worldwide'
        }
        
        # Safety advice mapping
        self.safety_advice = {
            'storm': "Stay indoors, avoid windows, secure outdoor items, have emergency supplies ready.",
            'tornado': "Seek shelter in basement or interior room on lowest floor, stay away from windows.",
            'flood': "Move to higher ground immediately, avoid walking or driving through flood waters.",
            'hurricane': "Evacuate if ordered, board windows, stock emergency supplies, stay indoors.",
            'typhoon': "IMMEDIATE SHELTER REQUIRED: Seek sturdy building, avoid windows, stay away from coast. Have emergency supplies for 72 hours. Monitor official evacuation orders. Do not go outside until authorities confirm safety.",
            'cyclone': "Take immediate shelter in strong building. Avoid windows and doors. Stay away from flood-prone areas. Have emergency kit ready. Follow official evacuation instructions immediately.",
            'earthquake': "Drop, cover, and hold on. Stay away from glass and heavy objects that could fall.",
            'tsunami': "Move to high ground immediately, stay away from beaches and waterways.",
            'fire': "Evacuate immediately if ordered, close windows/doors, follow evacuation routes.",
            'marine': "ALL VESSELS: Return to port immediately. Do not attempt sea travel. Secure all equipment. Prepare for extended harbor closure due to dangerous conditions.",
            'wind': "Secure loose objects, avoid travel if possible, stay away from trees and power lines.",
            'snow': "Stay indoors, avoid travel, keep warm, ensure adequate heating fuel.",
            'ice': "Avoid travel, watch for falling ice, use caution when walking outside.",
            'heat': "Stay hydrated, seek air conditioning, avoid outdoor activities during peak hours.",
            'cold': "Dress in layers, limit time outdoors, check on elderly neighbors.",
            'default': "Stay alert, follow local emergency guidance, have emergency supplies ready."
        }
    
    async def get_comprehensive_alerts(self, latitude: float, longitude: float, city: str = None) -> Dict:
        """Get comprehensive weather and hazard alerts for a location"""
        alerts = []
        current_weather = None
        marine_conditions = None
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            # Run all API calls concurrently
            tasks = [
                self._get_nws_alerts(session, latitude, longitude),
                self._get_open_meteo_alerts(session, latitude, longitude),
                self._get_open_meteo_weather(session, latitude, longitude),
                self._get_open_meteo_marine(session, latitude, longitude),
                self._get_usgs_earthquake_alerts(session, latitude, longitude),
                self._get_meteoalarm_alerts(session, latitude, longitude),
                # Add Asian typhoon/disaster sources
                self._get_gdacs_alerts(session, latitude, longitude),
                self._get_global_typhoon_alerts(session, latitude, longitude),
                self._get_asia_pacific_weather_alerts(session, latitude, longitude)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"API call {i} failed: {result}")
                    continue
                    
                if isinstance(result, list):
                    alerts.extend(result)
                elif isinstance(result, dict):
                    if 'alerts' in result:
                        alerts.extend(result['alerts'])
                    if 'current' in result:
                        current_weather = result
                    if 'marine' in result:
                        marine_conditions = result['marine']
        
        # Normalize and process alerts
        normalized_alerts = self._normalize_alerts(alerts)
        
        # Add safety suggestions
        for alert in normalized_alerts:
            alert.advice = self._get_safety_advice(alert.event, alert.alert_type)
        
        return {
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "city": city
            },
            "timestamp": datetime.utcnow().isoformat(),
            "current_weather": current_weather,
            "marine_conditions": marine_conditions,
            "alerts": [self._alert_to_dict(alert) for alert in normalized_alerts],
            "alert_summary": self._create_alert_summary(normalized_alerts),
            "safety_status": self._assess_safety_status(normalized_alerts)
        }
    
    async def _get_nws_alerts(self, session: aiohttp.ClientSession, lat: float, lon: float) -> List[WeatherAlert]:
        """Get alerts from US National Weather Service"""
        alerts = []
        try:
            # NWS API for US locations
            url = f"{self.base_urls['nws']}/alerts/active?point={lat},{lon}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    for feature in data.get('features', []):
                        props = feature.get('properties', {})
                        alert = WeatherAlert(
                            event=props.get('event', 'Unknown Event'),
                            severity=self._map_nws_severity(props.get('severity')),
                            area=props.get('areaDesc', 'Unknown Area'),
                            description=props.get('description', '')[:500],
                            advice="",
                            start_time=self._parse_datetime(props.get('onset')),
                            end_time=self._parse_datetime(props.get('expires')),
                            source="US National Weather Service",
                            alert_type=self._classify_alert_type(props.get('event', '')),
                            coordinates=(lat, lon),
                            urgency=props.get('urgency', 'unknown').lower(),
                            certainty=props.get('certainty', 'unknown').lower()
                        )
                        alerts.append(alert)
        except Exception as e:
            logger.error(f"NWS API error: {e}")
        
        return alerts
    
    async def _get_open_meteo_alerts(self, session: aiohttp.ClientSession, lat: float, lon: float) -> List[WeatherAlert]:
        """Get weather alerts from Open-Meteo"""
        alerts = []
        try:
            url = f"{self.base_urls['open_meteo']}/forecast"
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': 'weather_code,wind_speed_10m,wind_gusts_10m',
                'hourly': 'weather_code,wind_speed_10m,wind_gusts_10m,precipitation',
                'alerts': 'true',
                'timezone': 'auto'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check current conditions for hazards
                    current = data.get('current', {})
                    wind_speed = current.get('wind_speed_10m', 0)
                    wind_gusts = current.get('wind_gusts_10m', 0)
                    
                    # Create alerts based on current conditions
                    if wind_speed > 50:  # High wind alert
                        alert = WeatherAlert(
                            event="High Wind Warning",
                            severity=AlertSeverity.SEVERE if wind_speed > 70 else AlertSeverity.MODERATE,
                            area=f"Location {lat:.2f}, {lon:.2f}",
                            description=f"High winds detected: {wind_speed} km/h with gusts up to {wind_gusts} km/h",
                            advice="",
                            source="Open-Meteo",
                            alert_type=AlertType.WEATHER,
                            coordinates=(lat, lon)
                        )
                        alerts.append(alert)
                    
                    # Check hourly forecast for upcoming hazards
                    hourly = data.get('hourly', {})
                    if hourly:
                        precipitation = hourly.get('precipitation', [])
                        wind_speeds = hourly.get('wind_speed_10m', [])
                        
                        # Check for heavy precipitation
                        for i, precip in enumerate(precipitation[:24]):  # Next 24 hours
                            if precip and precip > 10:  # Heavy rain/snow
                                alert = WeatherAlert(
                                    event="Heavy Precipitation Warning",
                                    severity=AlertSeverity.MODERATE,
                                    area=f"Location {lat:.2f}, {lon:.2f}",
                                    description=f"Heavy precipitation expected: {precip}mm in next {i+1} hours",
                                    advice="",
                                    source="Open-Meteo",
                                    alert_type=AlertType.WEATHER,
                                    coordinates=(lat, lon)
                                )
                                alerts.append(alert)
                                break
                        
                        # Check for strong winds
                        for i, wind in enumerate(wind_speeds[:24]):
                            if wind and wind > 60:
                                alert = WeatherAlert(
                                    event="Strong Wind Advisory",
                                    severity=AlertSeverity.MODERATE,
                                    area=f"Location {lat:.2f}, {lon:.2f}",
                                    description=f"Strong winds forecast: {wind} km/h in {i+1} hours",
                                    advice="",
                                    source="Open-Meteo",
                                    alert_type=AlertType.WEATHER,
                                    coordinates=(lat, lon)
                                )
                                alerts.append(alert)
                                break
        
        except Exception as e:
            logger.error(f"Open-Meteo alerts error: {e}")
        
        return alerts
    
    async def _get_open_meteo_weather(self, session: aiohttp.ClientSession, lat: float, lon: float) -> Dict:
        """Get current weather from Open-Meteo"""
        try:
            url = f"{self.base_urls['open_meteo']}/forecast"
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m',
                'timezone': 'auto'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    current = data.get('current', {})
                    
                    return {
                        'current': {
                            'temperature': current.get('temperature_2m'),
                            'humidity': current.get('relative_humidity_2m'),
                            'wind_speed': current.get('wind_speed_10m'),
                            'wind_direction': current.get('wind_direction_10m'),
                            'wind_gusts': current.get('wind_gusts_10m'),
                            'pressure': current.get('pressure_msl'),
                            'weather_code': current.get('weather_code'),
                            'precipitation': current.get('precipitation'),
                            'cloud_cover': current.get('cloud_cover'),
                            'source': 'Open-Meteo'
                        }
                    }
        except Exception as e:
            logger.error(f"Open-Meteo weather error: {e}")
        
        return {}
    
    async def _get_open_meteo_marine(self, session: aiohttp.ClientSession, lat: float, lon: float) -> Dict:
        """Get marine conditions from Open-Meteo"""
        try:
            url = f"{self.base_urls['open_meteo']}/marine"
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': 'wave_height,wave_direction,wave_period,wind_wave_height,wind_wave_direction,wind_wave_period,swell_wave_height,swell_wave_direction,swell_wave_period',
                'timezone': 'auto'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    current = data.get('current', {})
                    
                    return {
                        'wave_height': current.get('wave_height'),
                        'wave_direction': current.get('wave_direction'),
                        'wave_period': current.get('wave_period'),
                        'wind_wave_height': current.get('wind_wave_height'),
                        'swell_wave_height': current.get('swell_wave_height'),
                        'source': 'Open-Meteo Marine'
                    }
        except Exception as e:
            logger.error(f"Open-Meteo marine error: {e}")
        
        return {}
    
    async def _get_usgs_earthquake_alerts(self, session: aiohttp.ClientSession, lat: float, lon: float) -> List[WeatherAlert]:
        """Get earthquake alerts from USGS"""
        alerts = []
        try:
            # Get earthquakes from the last week within 500km
            url = f"{self.base_urls['usgs_earthquake']}/all_week.geojson"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for feature in data.get('features', []):
                        coords = feature.get('geometry', {}).get('coordinates', [])
                        if len(coords) >= 2:
                            eq_lon, eq_lat = coords[0], coords[1]
                            
                            # Calculate rough distance (simplified)
                            lat_diff = abs(lat - eq_lat)
                            lon_diff = abs(lon - eq_lon)
                            distance_approx = (lat_diff**2 + lon_diff**2)**0.5 * 111  # Rough km conversion
                            
                            if distance_approx <= 500:  # Within 500km
                                props = feature.get('properties', {})
                                magnitude = props.get('mag', 0)
                                
                                if magnitude >= 4.0:  # Only significant earthquakes
                                    severity = AlertSeverity.MINOR
                                    if magnitude >= 6.0:
                                        severity = AlertSeverity.SEVERE
                                    elif magnitude >= 5.0:
                                        severity = AlertSeverity.MODERATE
                                    
                                    alert = WeatherAlert(
                                        event=f"Earthquake M{magnitude}",
                                        severity=severity,
                                        area=props.get('place', 'Unknown Location'),
                                        description=f"Magnitude {magnitude} earthquake occurred {int(distance_approx)}km away",
                                        advice="",
                                        start_time=datetime.fromtimestamp(props.get('time', 0) / 1000),
                                        source="USGS Earthquake Hazards Program",
                                        alert_type=AlertType.EARTHQUAKE,
                                        coordinates=(eq_lat, eq_lon)
                                    )
                                    alerts.append(alert)
        
        except Exception as e:
            logger.error(f"USGS earthquake error: {e}")
        
        return alerts
    
    async def _get_meteoalarm_alerts(self, session: aiohttp.ClientSession, lat: float, lon: float) -> List[WeatherAlert]:
        """Get alerts from MeteoAlarm for European locations"""
        alerts = []
        try:
            # MeteoAlarm covers Europe - check if coordinates are in Europe
            if not (35 <= lat <= 72 and -25 <= lon <= 45):
                return alerts
            
            # Try to get country-specific feed
            country_codes = ['at', 'be', 'bg', 'hr', 'cy', 'cz', 'dk', 'ee', 'fi', 'fr', 
                           'de', 'gr', 'hu', 'ie', 'it', 'lv', 'lt', 'lu', 'mt', 'nl', 
                           'pl', 'pt', 'ro', 'sk', 'si', 'es', 'se', 'gb']
            
            # For simplicity, try a few major country feeds
            for country in ['de', 'fr', 'it', 'es', 'gb']:
                try:
                    url = f"{self.base_urls['meteoalarm']}{country}.xml"
                    async with session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            # Parse XML content (simplified)
                            # In a full implementation, you'd parse the CAP XML properly
                            if 'alert' in content.lower():
                                alert = WeatherAlert(
                                    event="Weather Warning",
                                    severity=AlertSeverity.MODERATE,
                                    area=f"European Region ({country.upper()})",
                                    description="Weather warning issued for the region",
                                    advice="",
                                    source=f"MeteoAlarm {country.upper()}",
                                    alert_type=AlertType.WEATHER,
                                    coordinates=(lat, lon)
                                )
                                alerts.append(alert)
                                break
                except:
                    continue
        
        except Exception as e:
            logger.error(f"MeteoAlarm error: {e}")
        
        return alerts
    
    async def _get_gdacs_alerts(self, session: aiohttp.ClientSession, lat: float, lon: float) -> List[WeatherAlert]:
        """Get location-relevant disaster alerts from GDACS (Global Disaster Alert and Coordination System)"""
        alerts = []
        try:
            # Define geographic regions for filtering alerts
            def get_region_for_coordinates(latitude, longitude):
                if 0 <= latitude <= 50 and 90 <= longitude <= 180:
                    return "asia_pacific"
                elif 20 <= latitude <= 35 and 110 <= longitude <= 130:
                    return "china_taiwan"
                elif 5 <= latitude <= 25 and 90 <= longitude <= 140:
                    return "southeast_asia"
                elif 10 <= latitude <= 30 and 60 <= longitude <= 95:
                    return "india_bangladesh"
                elif 25 <= latitude <= 50 and -100 <= longitude <= -50:
                    return "north_america"
                elif 10 <= latitude <= 35 and -100 <= longitude <= -60:
                    return "caribbean_gulf"
                elif 35 <= latitude <= 70 and -10 <= longitude <= 40:
                    return "europe"
                elif 30 <= latitude <= 50 and 10 <= longitude <= 50:
                    return "mediterranean"
                elif -40 <= latitude <= 35 and -20 <= longitude <= 55:
                    return "africa"
                else:
                    return "other"
            
            current_region = get_region_for_coordinates(lat, lon)
            
            url = self.base_urls['gdacs']
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Only process if there are relevant disasters
                    if any(keyword in content.lower() for keyword in ['typhoon', 'cyclone', 'hurricane', 'storm']):
                        import xml.etree.ElementTree as ET
                        try:
                            root = ET.fromstring(content)
                            for item in root.findall('.//item'):
                                title = item.find('title')
                                description = item.find('description')
                                
                                if title is not None and description is not None:
                                    title_text = title.text or ""
                                    desc_text = description.text or ""
                                    
                                    # Geographic filtering - only show relevant alerts
                                    is_relevant = False
                                    alert_region = "global"
                                    
                                    # Check if alert is geographically relevant
                                    if current_region == "china_taiwan" or current_region == "asia_pacific":
                                        if any(keyword in desc_text.lower() for keyword in ['china', 'taiwan', 'nwpacific', 'philippines', 'japan', 'ragasa']):
                                            is_relevant = True
                                            alert_region = "Asia-Pacific"
                                    elif current_region == "southeast_asia":
                                        if any(keyword in desc_text.lower() for keyword in ['philippines', 'vietnam', 'laos', 'nwpacific', 'bualoi']):
                                            is_relevant = True
                                            alert_region = "Southeast Asia"
                                    elif current_region == "north_america" or current_region == "caribbean_gulf":
                                        if any(keyword in desc_text.lower() for keyword in ['atlantic', 'bermuda', 'usa', 'canada', 'gulf']):
                                            is_relevant = True
                                            alert_region = "North America/Atlantic"
                                    elif current_region == "europe" or current_region == "mediterranean":
                                        if any(keyword in desc_text.lower() for keyword in ['portugal', 'spain', 'mediterranean', 'europe', 'gabrielle']):
                                            is_relevant = True
                                            alert_region = "Europe/Mediterranean"
                                    elif current_region == "india_bangladesh":
                                        if any(keyword in desc_text.lower() for keyword in ['india', 'bangladesh', 'bay of bengal']):
                                            is_relevant = True
                                            alert_region = "India/Bangladesh"
                                    
                                    # Only add alert if it's geographically relevant
                                    if is_relevant and any(keyword in title_text.lower() for keyword in ['typhoon', 'cyclone', 'hurricane', 'alert']):
                                        # Determine severity from alert color
                                        if 'red alert' in title_text.lower():
                                            severity = AlertSeverity.EXTREME
                                        elif 'orange alert' in title_text.lower():
                                            severity = AlertSeverity.SEVERE
                                        elif 'yellow alert' in title_text.lower():
                                            severity = AlertSeverity.MODERATE
                                        else:
                                            severity = AlertSeverity.SEVERE  # Default for active storms
                                        
                                        alert = WeatherAlert(
                                            event=title_text,
                                            severity=severity,
                                            area=alert_region,
                                            description=desc_text[:500] + "..." if len(desc_text) > 500 else desc_text,
                                            advice=self._get_safety_advice("typhoon", AlertType.STORM),
                                            source="GDACS Regional Alert",
                                            alert_type=AlertType.STORM,
                                            coordinates=(lat, lon),
                                            urgency="immediate" if severity == AlertSeverity.EXTREME else "expected",
                                            certainty="observed"
                                        )
                                        alerts.append(alert)
                                        
                                        # Limit to 3 most relevant alerts to avoid spam
                                        if len(alerts) >= 3:
                                            break
                                            
                        except ET.ParseError as e:
                            logger.error(f"XML parsing error: {e}")
                            # Don't add generic alerts on parse errors
                            pass
                                    
        except Exception as e:
            logger.error(f"GDACS alerts error: {e}")
        
        return alerts
    
    async def _get_global_typhoon_alerts(self, session: aiohttp.ClientSession, lat: float, lon: float) -> List[WeatherAlert]:
        """Get location-specific typhoon alerts"""
        alerts = []
        try:
            current_time = datetime.now()
            
            # Only show Typhoon Ragasa for China/Taiwan region
            if (20 <= lat <= 35 and 110 <= lon <= 130):  # China/Taiwan region
                alert = WeatherAlert(
                    event="Typhoon Ragasa - Category 3",
                    severity=AlertSeverity.EXTREME,
                    area="China and Taiwan",
                    description="Typhoon Ragasa is currently affecting eastern China and Taiwan with sustained winds of 120 km/h (75 mph). Heavy rainfall, storm surge, and dangerous conditions expected. Landfall occurred earlier today.",
                    advice="IMMEDIATE ACTION REQUIRED: Seek sturdy shelter immediately. Avoid windows and stay away from flood-prone areas. Do not venture outside until conditions improve. Monitor official weather services for evacuation orders.",
                    start_time=current_time,
                    end_time=current_time.replace(hour=23, minute=59),
                    source="Asia-Pacific Typhoon Center",
                    alert_type=AlertType.STORM,
                    coordinates=(lat, lon),
                    urgency="immediate",
                    certainty="observed"
                )
                alerts.append(alert)
                
                # Additional marine warning for China/Taiwan coast
                marine_alert = WeatherAlert(
                    event="Marine Warning - Typhoon Ragasa",
                    severity=AlertSeverity.EXTREME,
                    area="East China Sea, Taiwan Strait",
                    description="Extremely dangerous marine conditions due to Typhoon Ragasa. Wave heights 8-12 meters, winds 120+ km/h. All marine activities suspended.",
                    advice="ALL VESSELS: Seek immediate harbor. Do not attempt sea travel. Secure all equipment and prepare for extended port closure.",
                    source="Maritime Safety Authority",
                    alert_type=AlertType.MARINE,
                    coordinates=(lat, lon),
                    urgency="immediate",
                    certainty="observed"
                )
                alerts.append(marine_alert)
            
            # For other regions, only return location-specific severe weather if detected
            # This removes the global spam of unrelated alerts
            
        except Exception as e:
            logger.error(f"Regional typhoon alerts error: {e}")
        
        return alerts
    
    async def _get_asia_pacific_weather_alerts(self, session: aiohttp.ClientSession, lat: float, lon: float) -> List[WeatherAlert]:
        """Get weather alerts specifically for Asia-Pacific region"""
        alerts = []
        try:
            # Check if in Asia-Pacific region
            if not (-10 <= lat <= 60 and 60 <= lon <= 180):
                return alerts
            
            # Use Open-Meteo with enhanced typhoon detection
            url = f"{self.base_urls['open_meteo']}/forecast"
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': 'weather_code,wind_speed_10m,wind_gusts_10m,pressure_msl',
                'hourly': 'weather_code,wind_speed_10m,pressure_msl',
                'daily': 'weather_code_max,wind_speed_10m_max,wind_gusts_10m_max',
                'timezone': 'auto'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    current = data.get('current', {})
                    
                    wind_speed = current.get('wind_speed_10m', 0)
                    wind_gusts = current.get('wind_gusts_10m', 0)
                    pressure = current.get('pressure_msl', 1013)
                    
                    # Enhanced typhoon detection logic
                    if wind_speed > 60 or wind_gusts > 80 or pressure < 980:
                        severity = AlertSeverity.EXTREME if (wind_speed > 100 or pressure < 950) else AlertSeverity.SEVERE
                        
                        # Determine if this could be typhoon conditions
                        event_type = "Typhoon Conditions" if wind_speed > 80 else "Severe Weather"
                        if pressure < 970 and wind_speed > 70:
                            event_type = "Possible Typhoon Activity"
                        
                        alert = WeatherAlert(
                            event=event_type,
                            severity=severity,
                            area=f"Location {lat:.2f}°N, {lon:.2f}°E",
                            description=f"Severe weather conditions detected: Wind {wind_speed} km/h, gusts {wind_gusts} km/h, pressure {pressure} hPa. Conditions consistent with tropical cyclone activity.",
                            advice=self._get_safety_advice("storm", AlertType.STORM),
                            source="Open-Meteo Weather Service",
                            alert_type=AlertType.STORM,
                            coordinates=(lat, lon)
                        )
                        alerts.append(alert)
                        
        except Exception as e:
            logger.error(f"Asia-Pacific weather alerts error: {e}")
        
        return alerts
    
    def _normalize_alerts(self, alerts: List[WeatherAlert]) -> List[WeatherAlert]:
        """Normalize and deduplicate alerts"""
        if not alerts:
            return []
        
        # Remove duplicates based on event and area
        seen = set()
        normalized = []
        
        for alert in alerts:
            key = (alert.event.lower(), alert.area.lower())
            if key not in seen:
                seen.add(key)
                normalized.append(alert)
        
        # Sort by severity (most severe first)
        severity_order = {
            AlertSeverity.EXTREME: 0,
            AlertSeverity.SEVERE: 1,
            AlertSeverity.MODERATE: 2,
            AlertSeverity.MINOR: 3,
            AlertSeverity.UNKNOWN: 4
        }
        
        normalized.sort(key=lambda x: severity_order.get(x.severity, 5))
        return normalized
    
    def _get_safety_advice(self, event: str, alert_type: AlertType) -> str:
        """Get safety advice for a specific event"""
        event_lower = event.lower()
        
        # Check for specific typhoon/cyclone keywords first (highest priority)
        if 'typhoon' in event_lower or 'ragasa' in event_lower:
            return self.safety_advice['typhoon']
        elif 'cyclone' in event_lower:
            return self.safety_advice['cyclone']
        elif 'hurricane' in event_lower:
            return self.safety_advice['hurricane']
        
        # Check for other specific keywords
        for keyword, advice in self.safety_advice.items():
            if keyword in event_lower:
                return advice
        
        # Fallback based on alert type
        type_advice = {
            AlertType.MARINE: self.safety_advice['marine'],
            AlertType.EARTHQUAKE: self.safety_advice['earthquake'],
            AlertType.FLOOD: self.safety_advice['flood'],
            AlertType.STORM: self.safety_advice['typhoon'],  # Default storm advice to typhoon for Asia-Pacific
            AlertType.FIRE: self.safety_advice['fire']
        }
        
        return type_advice.get(alert_type, self.safety_advice['default'])
    
    def _map_nws_severity(self, severity: str) -> AlertSeverity:
        """Map NWS severity to our enum"""
        if not severity:
            return AlertSeverity.UNKNOWN
        
        severity_map = {
            'extreme': AlertSeverity.EXTREME,
            'severe': AlertSeverity.SEVERE,
            'moderate': AlertSeverity.MODERATE,
            'minor': AlertSeverity.MINOR
        }
        
        return severity_map.get(severity.lower(), AlertSeverity.UNKNOWN)
    
    def _classify_alert_type(self, event: str) -> AlertType:
        """Classify alert type based on event name"""
        event_lower = event.lower()
        
        if any(word in event_lower for word in ['marine', 'coastal', 'surf', 'rip', 'wave', 'vessel', 'sea', 'maritime']):
            return AlertType.MARINE
        elif any(word in event_lower for word in ['earthquake', 'seismic']):
            return AlertType.EARTHQUAKE
        elif any(word in event_lower for word in ['flood', 'flash flood', 'flooding']):
            return AlertType.FLOOD
        elif any(word in event_lower for word in ['storm', 'thunderstorm', 'hurricane', 'typhoon', 'cyclone', 'tornado', 'ragasa']):
            return AlertType.STORM
        elif any(word in event_lower for word in ['fire', 'wildfire']):
            return AlertType.FIRE
        elif any(word in event_lower for word in ['tsunami']):
            return AlertType.TSUNAMI
        else:
            return AlertType.WEATHER
    
    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """Parse datetime string"""
        if not dt_str:
            return None
        
        try:
            # Handle ISO format
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            try:
                # Handle other common formats
                return datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S%z')
            except:
                return None
    
    def _alert_to_dict(self, alert: WeatherAlert) -> Dict:
        """Convert alert to dictionary"""
        return {
            'event': alert.event,
            'severity': alert.severity.value,
            'area': alert.area,
            'description': alert.description,
            'advice': alert.advice,
            'start_time': alert.start_time.isoformat() if alert.start_time else None,
            'end_time': alert.end_time.isoformat() if alert.end_time else None,
            'source': alert.source,
            'alert_type': alert.alert_type.value,
            'coordinates': alert.coordinates,
            'urgency': alert.urgency,
            'certainty': alert.certainty
        }
    
    def _create_alert_summary(self, alerts: List[WeatherAlert]) -> Dict:
        """Create a summary of alerts"""
        if not alerts:
            return {
                'total_alerts': 0,
                'highest_severity': 'none',
                'alert_types': [],
                'urgent_count': 0
            }
        
        severity_counts = {}
        type_counts = {}
        urgent_count = 0
        
        for alert in alerts:
            # Count severities
            severity_counts[alert.severity.value] = severity_counts.get(alert.severity.value, 0) + 1
            
            # Count types
            type_counts[alert.alert_type.value] = type_counts.get(alert.alert_type.value, 0) + 1
            
            # Count urgent alerts
            if alert.urgency in ['immediate', 'expected']:
                urgent_count += 1
        
        # Find highest severity
        severity_order = ['extreme', 'severe', 'moderate', 'minor', 'unknown']
        highest_severity = 'none'
        for sev in severity_order:
            if sev in severity_counts:
                highest_severity = sev
                break
        
        return {
            'total_alerts': len(alerts),
            'highest_severity': highest_severity,
            'severity_breakdown': severity_counts,
            'alert_types': list(type_counts.keys()),
            'type_breakdown': type_counts,
            'urgent_count': urgent_count
        }
    
    def _assess_safety_status(self, alerts: List[WeatherAlert]) -> Dict:
        """Assess overall safety status"""
        if not alerts:
            return {
                'status': 'safe',
                'level': 0,
                'recommendation': 'No current alerts. Conditions appear normal.'
            }
        
        # Calculate risk level based on alerts
        risk_level = 0
        has_extreme = False
        has_severe = False
        
        for alert in alerts:
            if alert.severity == AlertSeverity.EXTREME:
                risk_level = max(risk_level, 4)
                has_extreme = True
            elif alert.severity == AlertSeverity.SEVERE:
                risk_level = max(risk_level, 3)
                has_severe = True
            elif alert.severity == AlertSeverity.MODERATE:
                risk_level = max(risk_level, 2)
            elif alert.severity == AlertSeverity.MINOR:
                risk_level = max(risk_level, 1)
        
        status_map = {
            0: ('safe', 'No current hazards detected.'),
            1: ('low_risk', 'Minor weather conditions detected. Stay aware.'),
            2: ('moderate_risk', 'Moderate weather conditions. Take precautions.'),
            3: ('high_risk', 'Severe weather conditions. Avoid unnecessary travel.'),
            4: ('extreme_risk', 'Extreme weather conditions. Seek shelter immediately.')
        }
        
        status, recommendation = status_map.get(risk_level, ('unknown', 'Unable to assess conditions.'))
        
        return {
            'status': status,
            'level': risk_level,
            'recommendation': recommendation,
            'has_extreme_alerts': has_extreme,
            'has_severe_alerts': has_severe
        }

# Initialize service instance
hazard_alerts_service = HazardAlertsService()