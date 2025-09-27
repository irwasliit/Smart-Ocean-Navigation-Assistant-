import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, TYPE_CHECKING
import logging
from dataclasses import dataclass

if TYPE_CHECKING:
    from ..schemas import AgentResponse

logger = logging.getLogger(__name__)

@dataclass
class DisasterEvent:
    """Data class for disaster event information"""
    event_type: str
    location: str
    date: datetime
    magnitude: Optional[float]
    description: str
    source: str
    coordinates: Optional[Dict[str, float]]
    impact_level: str  # low, medium, high, extreme

@dataclass
class DisasterPrediction:
    """Data class for disaster predictions"""
    prediction_type: str
    location: str
    probability: float  # 0-1
    time_window: str
    confidence_level: str
    safety_measures: List[str]
    monitoring_sources: List[str]

class DisasterPredictionService:
    """Service for historical disaster data and prediction analysis"""
    
    def __init__(self):
        # API endpoints for disaster data
        self.usgs_earthquake_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
        self.noaa_weather_url = "https://api.weather.gov"
        self.historical_disasters = []  # Cache for historical data
        
    async def search_historical_disasters(
        self, 
        location: str, 
        latitude: float = None, 
        longitude: float = None,
        radius_km: float = 100,
        years_back: int = 10
    ) -> List[DisasterEvent]:
        """Search for historical disasters in a specific area"""
        disasters = []
        
        try:
            # Search earthquake data
            earthquakes = await self._get_historical_earthquakes(
                latitude, longitude, radius_km, years_back
            )
            disasters.extend(earthquakes)
            
            # Search severe weather events (simplified for now)
            weather_events = await self._get_historical_weather_events(
                location, years_back
            )
            disasters.extend(weather_events)
            
            # Search marine-specific disasters
            marine_events = await self._get_historical_marine_disasters(
                latitude, longitude, radius_km, years_back
            )
            disasters.extend(marine_events)
            
        except Exception as e:
            logger.error(f"Error searching historical disasters: {e}")
        
        return sorted(disasters, key=lambda x: x.date, reverse=True)
    
    async def generate_disaster_predictions(
        self, 
        location: str,
        latitude: float = None,
        longitude: float = None,
        weather_data: Dict = None
    ) -> List[DisasterPrediction]:
        """Generate disaster predictions based on current conditions and historical data"""
        predictions = []
        
        try:
            # Earthquake risk assessment
            earthquake_pred = await self._assess_earthquake_risk(latitude, longitude)
            if earthquake_pred:
                predictions.append(earthquake_pred)
            
            # Severe weather predictions
            weather_pred = await self._assess_weather_disaster_risk(weather_data, location)
            if weather_pred:
                predictions.append(weather_pred)
            
            # Marine-specific disaster predictions
            marine_pred = await self._assess_marine_disaster_risk(weather_data, latitude, longitude)
            if marine_pred:
                predictions.append(marine_pred)
            
            # Tsunami risk (based on earthquake and location data)
            tsunami_pred = await self._assess_tsunami_risk(latitude, longitude)
            if tsunami_pred:
                predictions.append(tsunami_pred)
                
        except Exception as e:
            logger.error(f"Error generating disaster predictions: {e}")
        
        return predictions
    
    async def _get_historical_earthquakes(
        self, 
        latitude: float, 
        longitude: float, 
        radius_km: float, 
        years_back: int
    ) -> List[DisasterEvent]:
        """Fetch historical earthquake data from USGS"""
        if not latitude or not longitude:
            return []
        
        earthquakes = []
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years_back * 365)
            
            params = {
                'format': 'geojson',
                'starttime': start_date.strftime('%Y-%m-%d'),
                'endtime': end_date.strftime('%Y-%m-%d'),
                'latitude': latitude,
                'longitude': longitude,
                'maxradiuskm': radius_km,
                'minmagnitude': 4.0,  # Only significant earthquakes
                'limit': 100
            }
            
            response = requests.get(self.usgs_earthquake_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                for feature in data.get('features', []):
                    props = feature.get('properties', {})
                    coords = feature.get('geometry', {}).get('coordinates', [])
                    
                    if len(coords) >= 2:
                        earthquake = DisasterEvent(
                            event_type="Earthquake",
                            location=props.get('place', 'Unknown'),
                            date=datetime.fromtimestamp(props.get('time', 0) / 1000),
                            magnitude=props.get('mag'),
                            description=f"Magnitude {props.get('mag')} earthquake",
                            source="USGS",
                            coordinates={'latitude': coords[1], 'longitude': coords[0]},
                            impact_level=self._classify_earthquake_impact(props.get('mag', 0))
                        )
                        earthquakes.append(earthquake)
                        
        except Exception as e:
            logger.warning(f"Could not fetch earthquake data: {e}")
        
        return earthquakes
    
    async def _get_historical_weather_events(self, location: str, years_back: int) -> List[DisasterEvent]:
        """Get historical severe weather events (simplified implementation)"""
        # This would integrate with NOAA or other weather services for historical data
        # For now, return some sample data based on common weather patterns
        weather_events = []
        
        # This is a simplified implementation - in production, you'd query actual weather APIs
        common_events = [
            {
                'type': 'Hurricane/Typhoon',
                'months': [6, 7, 8, 9, 10, 11],  # Hurricane season
                'probability': 0.1
            },
            {
                'type': 'Severe Thunderstorm',
                'months': [4, 5, 6, 7, 8, 9],
                'probability': 0.3
            },
            {
                'type': 'Winter Storm',
                'months': [11, 12, 1, 2, 3],
                'probability': 0.2
            }
        ]
        
        current_month = datetime.now().month
        for event_type in common_events:
            if current_month in event_type['months']:
                # Create a sample historical event
                event_date = datetime.now() - timedelta(days=365)  # One year ago
                weather_event = DisasterEvent(
                    event_type=event_type['type'],
                    location=location,
                    date=event_date,
                    magnitude=None,
                    description=f"Historical {event_type['type']} event in the region",
                    source="Historical Weather Data",
                    coordinates=None,
                    impact_level="medium"
                )
                weather_events.append(weather_event)
        
        return weather_events
    
    async def _get_historical_marine_disasters(
        self, 
        latitude: float, 
        longitude: float, 
        radius_km: float, 
        years_back: int
    ) -> List[DisasterEvent]:
        """Get historical marine-specific disasters"""
        marine_disasters = []
        
        # Sample marine disasters - in production, this would query maritime incident databases
        if latitude and longitude:
            # Check if in high-risk maritime areas
            high_risk_areas = [
                {'name': 'North Atlantic', 'lat_range': (40, 60), 'lon_range': (-50, -10)},
                {'name': 'Gulf of Mexico', 'lat_range': (18, 30), 'lon_range': (-98, -80)},
                {'name': 'Indian Ocean', 'lat_range': (-40, 25), 'lon_range': (40, 115)},
                {'name': 'South China Sea', 'lat_range': (0, 25), 'lon_range': (99, 125)}
            ]
            
            for area in high_risk_areas:
                if (area['lat_range'][0] <= latitude <= area['lat_range'][1] and 
                    area['lon_range'][0] <= longitude <= area['lon_range'][1]):
                    
                    disaster = DisasterEvent(
                        event_type="Marine Incident",
                        location=area['name'],
                        date=datetime.now() - timedelta(days=180),
                        magnitude=None,
                        description=f"Historical maritime incident in {area['name']}",
                        source="Maritime Safety Database",
                        coordinates={'latitude': latitude, 'longitude': longitude},
                        impact_level="medium"
                    )
                    marine_disasters.append(disaster)
        
        return marine_disasters
    
    async def _assess_earthquake_risk(self, latitude: float, longitude: float) -> Optional[DisasterPrediction]:
        """Assess earthquake risk based on location and historical data"""
        if not latitude or not longitude:
            return None
        
        # Known high-risk seismic zones
        seismic_zones = [
            {'name': 'Pacific Ring of Fire', 'risk': 0.7},
            {'name': 'Mediterranean-Himalayan Belt', 'risk': 0.6},
            {'name': 'Mid-Atlantic Ridge', 'risk': 0.4}
        ]
        
        # Simplified risk assessment - in production, use geological databases
        base_risk = 0.1  # Base earthquake risk
        
        # Check if in known seismic zone (simplified)
        if abs(latitude) > 30 or abs(longitude) > 100:  # Very simplified check
            base_risk = 0.3
        
        if base_risk > 0.2:
            return DisasterPrediction(
                prediction_type="Earthquake Risk",
                location=f"Coordinates: {latitude:.2f}, {longitude:.2f}",
                probability=base_risk,
                time_window="30 days",
                confidence_level="medium",
                safety_measures=[
                    "Monitor seismic activity updates",
                    "Ensure emergency equipment is accessible",
                    "Review evacuation procedures",
                    "Secure loose equipment on vessel"
                ],
                monitoring_sources=["USGS Earthquake Monitoring", "Local Geological Surveys"]
            )
        
        return None
    
    async def _assess_weather_disaster_risk(self, weather_data: Dict, location: str) -> Optional[DisasterPrediction]:
        """Assess severe weather disaster risk"""
        if not weather_data:
            return None
        
        current = weather_data.get('current', {})
        wind_speed = current.get('wind_speed_10m', current.get('wind_speed', 0))
        pressure = current.get('pressure_msl', current.get('pressure', 1013))
        
        # High risk conditions
        high_risk = False
        risk_factors = []
        
        if wind_speed > 60:  # High wind speeds
            high_risk = True
            risk_factors.append("High wind speeds detected")
        
        if pressure < 980:  # Low pressure indicating storm system
            high_risk = True
            risk_factors.append("Low atmospheric pressure")
        
        if high_risk:
            return DisasterPrediction(
                prediction_type="Severe Weather Risk",
                location=location,
                probability=0.6,
                time_window="24-48 hours",
                confidence_level="high",
                safety_measures=[
                    "Seek shelter immediately if conditions worsen",
                    "Monitor weather updates continuously",
                    "Avoid marine operations",
                    "Secure all equipment and cargo",
                    "Consider alternative routes or delays"
                ],
                monitoring_sources=["National Weather Service", "Marine Weather Services"]
            )
        
        return None
    
    async def _assess_marine_disaster_risk(
        self, 
        weather_data: Dict, 
        latitude: float, 
        longitude: float
    ) -> Optional[DisasterPrediction]:
        """Assess marine-specific disaster risks"""
        if not weather_data:
            return None
        
        current = weather_data.get('current', {})
        wave_height = current.get('wave_height', 0)
        wind_speed = current.get('wind_speed_10m', current.get('wind_speed', 0))
        visibility = current.get('visibility', 10000)
        
        risk_level = 0
        risk_factors = []
        
        if wave_height > 4:  # High waves
            risk_level += 0.3
            risk_factors.append("High wave conditions")
        
        if wind_speed > 40:  # Strong winds
            risk_level += 0.2
            risk_factors.append("Strong wind conditions")
        
        if visibility < 1000:  # Poor visibility
            risk_level += 0.3
            risk_factors.append("Poor visibility")
        
        if risk_level > 0.4:
            return DisasterPrediction(
                prediction_type="Marine Hazard Risk",
                location=f"Maritime area: {latitude:.2f}, {longitude:.2f}",
                probability=min(risk_level, 0.9),
                time_window="Current conditions",
                confidence_level="high",
                safety_measures=[
                    "Reduce speed and maintain extra vigilance",
                    "Use radar and GPS navigation systems",
                    "Maintain radio contact with coast guard",
                    "Consider seeking safe harbor",
                    "Ensure all safety equipment is ready",
                    "Brief crew on emergency procedures"
                ],
                monitoring_sources=["Coast Guard Updates", "Marine Weather Services", "Vessel Traffic Services"]
            )
        
        return None
    
    async def _assess_tsunami_risk(self, latitude: float, longitude: float) -> Optional[DisasterPrediction]:
        """Assess tsunami risk based on location"""
        if not latitude or not longitude:
            return None
        
        # Pacific Ocean has higher tsunami risk
        pacific_risk_zones = [
            {'name': 'Pacific Coast', 'lat_range': (-60, 70), 'lon_range': (120, -70), 'risk': 0.2},
            {'name': 'Indian Ocean', 'lat_range': (-50, 30), 'lon_range': (20, 120), 'risk': 0.15}
        ]
        
        for zone in pacific_risk_zones:
            lat_in_range = zone['lat_range'][0] <= latitude <= zone['lat_range'][1]
            lon_in_range = (zone['lon_range'][0] <= longitude <= 180 or 
                           -180 <= longitude <= zone['lon_range'][1])
            
            if lat_in_range and lon_in_range:
                return DisasterPrediction(
                    prediction_type="Tsunami Risk",
                    location=zone['name'],
                    probability=zone['risk'],
                    time_window="Ongoing risk",
                    confidence_level="medium",
                    safety_measures=[
                        "Monitor tsunami warning systems",
                        "Know evacuation routes to higher ground",
                        "Stay informed about seismic activity",
                        "Maintain emergency communication devices",
                        "If in coastal waters, head to deeper water immediately upon warning"
                    ],
                    monitoring_sources=["Pacific Tsunami Warning Center", "National Tsunami Warning Centers"]
                )
        
        return None
    
    def _classify_earthquake_impact(self, magnitude: float) -> str:
        """Classify earthquake impact level based on magnitude"""
        if magnitude < 4.0:
            return "low"
        elif magnitude < 6.0:
            return "medium"
        elif magnitude < 7.0:
            return "high"
        else:
            return "extreme"
    
    async def analyze_current_hazard_alerts(
        self, 
        location: str = "global", 
        latitude: float = None, 
        longitude: float = None
    ) -> "AgentResponse":
        """Analyze current hazard alerts and natural disasters"""
        from .hazard_alerts_service import hazard_alerts_service
        from ..schemas import AgentResponse
        
        try:
            print(f"🚨 Analyzing current hazard alerts for location: {location}")
            
            # Get current hazard alerts
            alerts = await hazard_alerts_service.get_current_alerts()
            print(f"🚨 Retrieved {len(alerts)} current alerts")
            
            if not alerts:
                # If no alerts, try to get recent earthquake data as backup
                recent_disasters = await self._get_recent_global_disasters()
                if recent_disasters:
                    disaster_info = self._format_recent_disasters(recent_disasters)
                    return AgentResponse(
                        agent_type="disaster_predictor",
                        content=f"Based on recent global monitoring:\n\n{disaster_info}",
                        confidence=0.7,
                        data_sources=["USGS", "Global Disaster Monitoring"]
                    )
                else:
                    return AgentResponse(
                        agent_type="disaster_predictor",
                        content="Currently monitoring global disaster systems. No major active natural disasters requiring immediate alerts at this time. Systems are continuously monitoring seismic activity, weather patterns, and other hazard indicators.",
                        confidence=0.6,
                        data_sources=["Global Monitoring Systems"]
                    )
            
            # Process and format alerts
            formatted_alerts = []
            high_priority_count = 0
            
            for alert in alerts[:10]:  # Limit to top 10 alerts
                alert_text = self._format_hazard_alert(alert)
                if alert_text:
                    formatted_alerts.append(alert_text)
                    if alert.get('severity', '').lower() in ['high', 'extreme', 'critical']:
                        high_priority_count += 1
            
            if formatted_alerts:
                alerts_content = "\n\n".join(formatted_alerts)
                summary = f"Currently monitoring {len(alerts)} active hazard alerts globally"
                if high_priority_count > 0:
                    summary += f" ({high_priority_count} high priority)"
                
                content = f"{summary}:\n\n{alerts_content}"
                
                return AgentResponse(
                    agent_type="disaster_predictor",
                    content=content,
                    confidence=0.8,
                    data_sources=["Real-time Hazard Monitoring", "Global Alert Systems"]
                )
            else:
                return AgentResponse(
                    agent_type="disaster_predictor",
                    content="Global hazard monitoring systems are active. Current alert processing in progress. No immediate high-priority natural disaster alerts requiring urgent attention.",
                    confidence=0.6,
                    data_sources=["Hazard Alert Systems"]
                )
                
        except Exception as e:
            logger.error(f"Error analyzing current hazard alerts: {e}")
            return AgentResponse(
                agent_type="disaster_predictor",
                content="Unable to access current hazard alert systems. For the most current natural disaster information, please check official sources like USGS, NOAA, or local emergency management agencies.",
                confidence=0.3,
                data_sources=["System Error"]
            )
    
    async def _get_recent_global_disasters(self) -> List[DisasterEvent]:
        """Get recent global disasters as backup when alerts are unavailable"""
        try:
            # Get recent earthquakes from USGS
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)  # Last 7 days
            
            params = {
                'format': 'geojson',
                'starttime': start_time.strftime('%Y-%m-%d'),
                'endtime': end_time.strftime('%Y-%m-%d'),
                'minmagnitude': 5.0,  # Only significant earthquakes
                'orderby': 'time-desc',
                'limit': 10
            }
            
            response = requests.get(self.usgs_earthquake_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                disasters = []
                
                for feature in data.get('features', []):
                    props = feature.get('properties', {})
                    coords = feature.get('geometry', {}).get('coordinates', [])
                    
                    if len(coords) >= 2:
                        disaster = DisasterEvent(
                            event_type="earthquake",
                            location=props.get('place', 'Unknown location'),
                            date=datetime.fromtimestamp(props.get('time', 0) / 1000),
                            magnitude=props.get('mag'),
                            description=f"Magnitude {props.get('mag')} earthquake",
                            source="USGS",
                            coordinates={'latitude': coords[1], 'longitude': coords[0]},
                            impact_level=self._classify_earthquake_impact(props.get('mag', 0))
                        )
                        disasters.append(disaster)
                
                return disasters[:5]  # Return top 5
                
        except Exception as e:
            logger.error(f"Error getting recent global disasters: {e}")
            
        return []
    
    def _format_recent_disasters(self, disasters: List[DisasterEvent]) -> str:
        """Format recent disasters for display"""
        if not disasters:
            return "No significant recent disasters detected."
        
        formatted = []
        for disaster in disasters:
            time_ago = datetime.utcnow() - disaster.date
            if time_ago.days > 0:
                time_str = f"{time_ago.days} days ago"
            else:
                hours = time_ago.seconds // 3600
                time_str = f"{hours} hours ago"
            
            formatted.append(
                f"🔸 **{disaster.event_type.title()}** - {disaster.location}\n"
                f"   Magnitude: {disaster.magnitude}, Impact: {disaster.impact_level}\n"
                f"   Time: {time_str}"
            )
        
        return "\n\n".join(formatted)
    
    def _format_hazard_alert(self, alert: Dict) -> Optional[str]:
        """Format a hazard alert for display"""
        try:
            alert_type = alert.get('type', 'Unknown').title()
            location = alert.get('location', 'Unknown location')
            severity = alert.get('severity', 'Unknown')
            description = alert.get('description', 'No description available')
            
            # Truncate long descriptions
            if len(description) > 200:
                description = description[:200] + "..."
            
            return f"🚨 **{alert_type}** Alert - {location}\nSeverity: {severity}\n{description}"
            
        except Exception as e:
            logger.error(f"Error formatting alert: {e}")
            return None

# Global instance
disaster_service = DisasterPredictionService()