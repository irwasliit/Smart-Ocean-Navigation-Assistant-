"""
Multi-Agent AI Service for Smart Ocean Navigation Assistant
Simplified version for immediate functionality
"""

import openai
import os
import asyncio
import json
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import requests
# from bs4 import BeautifulSoup
import re
# import numpy as np
from dotenv import load_dotenv
import logging
import traceback

# Configure minimal logging - Only errors and warnings
logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import free AI alternatives
try:
    from .ollama_ai_service import ollama_service
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    from .huggingface_ai_service import huggingface_service
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False

load_dotenv()

class AgentType(Enum):
    WEATHER_ANALYST = "weather_analyst"
    ROUTE_OPTIMIZER = "route_optimizer"
    HAZARD_DETECTOR = "hazard_detector"
    COMMUNICATION_MANAGER = "communication_manager"
    INFORMATION_RETRIEVER = "information_retriever"
    DISASTER_PREDICTOR = "disaster_predictor"

@dataclass
class AgentResponse:
    agent_type: AgentType
    content: str
    confidence: float
    metadata: Dict[str, Any]
    timestamp: datetime

@dataclass
class NavigationContext:
    vessel_type: str
    vessel_size: str
    experience_level: str
    cargo_type: Optional[str]
    departure_port: str
    destination_port: str
    departure_time: str  # Changed from datetime to str
    urgency_level: str

class WeatherAnalystAgent:
    """Specialized agent for weather analysis and prediction"""
    
    def __init__(self, openai_client):
        self.client = openai_client
        self.agent_type = AgentType.WEATHER_ANALYST
        
    async def analyze_weather_conditions(self, weather_data: Dict, location: Dict) -> AgentResponse:
        """Analyze current and forecast weather conditions"""
        
        current = weather_data.get("current", {})
        forecast = weather_data.get("forecast", [])
        
        # Calculate weather severity index
        severity_index = self._calculate_weather_severity(current, forecast)
        
        # Enhanced weather analysis with NLP understanding
        temperature = current.get('temperature_2m', current.get('temperature', 0))
        humidity = current.get('relative_humidity_2m', current.get('humidity', 0))
        wind_speed = current.get('wind_speed_10m', current.get('wind_speed', 0))
        wind_direction = current.get('wind_direction_10m', current.get('wind_direction', 0))
        pressure = current.get('pressure_msl', current.get('pressure', 0))
        visibility = current.get('visibility', 0)
        
        # Convert wind direction to compass bearing
        wind_compass = self._wind_direction_to_compass(wind_direction)
        
        # Enhanced prompt with better NLP context
        prompt = f"""
        As an expert marine meteorologist, provide a comprehensive weather analysis for {location.get('name', 'the requested location')}:
        
        CURRENT CONDITIONS:
        • Temperature: {temperature}°C ({temperature * 9/5 + 32:.1f}°F)
        • Humidity: {humidity}%
        • Wind: {wind_speed} km/h ({wind_speed * 0.539957:.1f} knots) from {wind_compass} ({wind_direction}°)
        • Atmospheric Pressure: {pressure} hPa ({pressure * 0.02953:.2f} inHg)
        • Visibility: {visibility/1000:.1f} km ({visibility * 0.000621371:.1f} miles)
        • Wave Height: {current.get('wave_height', 'N/A')} meters
        • Wave Period: {current.get('wave_period', 'N/A')} seconds
        
        FORECAST OVERVIEW:
        {self._format_forecast_summary(forecast)}
        
        WEATHER SEVERITY INDEX: {severity_index}/10
        {self._get_severity_description(severity_index)}
        
        Please provide a comprehensive marine weather analysis including:
        
        1. **IMMEDIATE CONDITIONS** - Current weather assessment with safety recommendations
        2. **WEATHER TRENDS** - Short-term (24-48h) and medium-term (3-7 day) outlook
        3. **NAVIGATION IMPACT** - How conditions affect different vessel operations
        4. **SAFETY RECOMMENDATIONS** - Specific advice for current conditions
        5. **OPTIMAL WINDOWS** - Best weather periods in the forecast
        6. **HAZARD ALERTS** - Any weather-related dangers or precautions
        
        Respond in clear, conversational language that mariners can easily understand and act upon.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a senior marine meteorologist with 20+ years of experience in ocean weather analysis. Provide precise, actionable insights for marine navigation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            confidence = min(0.9, 0.5 + (severity_index / 20))  # Higher confidence for clearer conditions
            
            return AgentResponse(
                agent_type=self.agent_type,
                content=content,
                confidence=confidence,
                metadata={
                    "severity_index": severity_index,
                    "location": location,
                    "analysis_type": "weather_conditions"
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return AgentResponse(
                agent_type=self.agent_type,
                content=f"Weather analysis unavailable: {str(e)}",
                confidence=0.1,
                metadata={"error": str(e)},
                timestamp=datetime.now()
            )
    
    def _calculate_weather_severity(self, current: Dict, forecast: List) -> float:
        """Calculate weather severity index (0-10)"""
        severity = 0
        
        # Wind severity
        wind_speed = current.get('wind_speed', 0)
        if wind_speed > 50: severity += 3
        elif wind_speed > 30: severity += 2
        elif wind_speed > 20: severity += 1
        
        # Wave severity
        wave_height = current.get('wave_height', 0)
        if wave_height > 4: severity += 3
        elif wave_height > 2.5: severity += 2
        elif wave_height > 1.5: severity += 1
        
        # Visibility severity
        visibility = current.get('visibility', 10000)
        if visibility < 1000: severity += 2
        elif visibility < 5000: severity += 1
        
        # Pressure trend
        if len(forecast) >= 2:
            pressure_trend = forecast[1].get('pressure', 1013) - current.get('pressure', 1013)
            if abs(pressure_trend) > 10: severity += 1
        
        return min(10, severity)
    
    def _format_forecast_summary(self, forecast: List) -> str:
        """Format forecast data for analysis"""
        summary = []
        for i, day in enumerate(forecast[:7]):
            day_summary = f"Day {i+1}: Wind {day.get('wind_speed', 0)}km/h, Waves {day.get('wave_height', 0)}m"
            summary.append(day_summary)
        return "\n".join(summary)
    
    def _wind_direction_to_compass(self, degrees: float) -> str:
        """Convert wind direction degrees to compass bearing"""
        if degrees is None or degrees == 0:
            return "Unknown"
        
        compass_bearings = [
            "North", "North-Northeast", "Northeast", "East-Northeast",
            "East", "East-Southeast", "Southeast", "South-Southeast", 
            "South", "South-Southwest", "Southwest", "West-Southwest",
            "West", "West-Northwest", "Northwest", "North-Northwest"
        ]
        
        index = round(degrees / 22.5) % 16
        return compass_bearings[index]
    
    def _get_severity_description(self, severity_index: float) -> str:
        """Get human-readable description of weather severity"""
        if severity_index <= 2:
            return "🟢 EXCELLENT - Ideal conditions for all marine activities"
        elif severity_index <= 4:
            return "🟡 GOOD - Suitable for most vessels with normal precautions"
        elif severity_index <= 6:
            return "🟠 CAUTION - Challenging conditions, experienced mariners advised"
        elif severity_index <= 8:
            return "🔴 DANGEROUS - High risk, only essential travel recommended"
        else:
            return "⛔ EXTREME - Severe conditions, avoid marine operations"

class RouteOptimizerAgent:
    """Specialized agent for route optimization and navigation planning"""
    
    def __init__(self, openai_client):
        self.client = openai_client
        self.agent_type = AgentType.ROUTE_OPTIMIZER
        
    async def optimize_route(self, route_data: Dict, weather_analysis: Dict, context: NavigationContext) -> AgentResponse:
        """Optimize route based on weather conditions and vessel requirements"""
        
        route_points = route_data.get('sample_points', [])
        total_distance = route_data.get('distance', 0)
        estimated_duration = route_data.get('estimated_duration', 0)
        
        # Calculate route risk score
        risk_score = self._calculate_route_risk(weather_analysis, context)
        
        # Create concise prompt to stay under token limit
        weather_summary = self._create_weather_summary(weather_analysis)
        
        prompt = f"""Maritime Route Analysis:

ROUTE: {context.departure_port} → {context.destination_port}
Distance: {total_distance:.0f}km ({total_distance * 0.54:.0f}nm)
Duration: {estimated_duration:.1f}h
Vessel: {context.vessel_type} ({context.vessel_size})
Risk Level: {risk_score}/10

WEATHER: {weather_summary}

Provide concise maritime intelligence:
1. Safety assessment & hazards
2. Navigation recommendations  
3. Optimal speed/timing
4. Risk mitigation steps
5. Emergency procedures

Keep response under 500 words, focus on actionable guidance."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a master mariner with expertise in route planning, weather routing, and maritime safety. Prioritize safety while optimizing efficiency."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.4
            )
            
            content = response.choices[0].message.content.strip()
            confidence = max(0.6, 1.0 - (risk_score / 15))  # Lower confidence for riskier routes
            
            return AgentResponse(
                agent_type=self.agent_type,
                content=content,
                confidence=confidence,
                metadata={
                    "risk_score": risk_score,
                    "route_distance": total_distance,
                    "optimization_type": "full_route"
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return AgentResponse(
                agent_type=self.agent_type,
                content=f"Route optimization unavailable: {str(e)}",
                confidence=0.1,
                metadata={"error": str(e)},
                timestamp=datetime.now()
            )
    
    def _calculate_route_risk(self, weather_analysis: Dict, context: NavigationContext) -> float:
        """Calculate overall route risk score (0-10)"""
        base_risk = 2  # Baseline ocean navigation risk
        
        # Weather-based risk
        weather_severity = weather_analysis.get('severity_index', 5)
        weather_risk = weather_severity * 0.6
        
        # Vessel-based risk modifiers
        if context.vessel_type.lower() in ['small_boat', 'recreational']:
            base_risk += 2
        elif context.vessel_type.lower() in ['commercial', 'cargo']:
            base_risk += 1
        
        if context.experience_level.lower() in ['beginner', 'novice']:
            base_risk += 2
        elif context.experience_level.lower() == 'intermediate':
            base_risk += 1
        
        # Urgency modifier
        if context.urgency_level.lower() == 'emergency':
            base_risk += 1  # Might need to travel in worse conditions
        
        return min(10, base_risk + weather_risk)
    
    def _create_weather_summary(self, weather_analysis: Dict) -> str:
        """Create concise weather summary to reduce token usage"""
        points = weather_analysis.get('points', [])
        if not points:
            return "No weather data available"
        
        # Get average conditions
        temps = [p.get('temperature', 20) for p in points if p.get('temperature')]
        winds = [p.get('wind_speed', 10) for p in points if p.get('wind_speed')]
        waves = [p.get('wave_height', 1) for p in points if p.get('wave_height')]
        
        avg_temp = sum(temps) / len(temps) if temps else 20
        avg_wind = sum(winds) / len(winds) if winds else 10
        avg_wave = sum(waves) / len(waves) if waves else 1
        
        severity = weather_analysis.get('severity_index', 5)
        
        return f"Temp: {avg_temp:.0f}°C, Wind: {avg_wind:.0f}kts, Waves: {avg_wave:.1f}m, Severity: {severity}/10"

class HazardDetectorAgent:
    """Specialized agent for detecting and analyzing maritime hazards"""
    
    def __init__(self, openai_client):
        self.client = openai_client
        self.agent_type = AgentType.HAZARD_DETECTOR
        
    async def detect_hazards(self, weather_data: Dict, route_data: Dict, ir_content: List[Dict]) -> AgentResponse:
        """Detect and analyze potential maritime hazards"""
        
        # Extract hazard information from weather data
        hazard_probabilities = self._extract_hazard_probabilities(weather_data)
        
        # Analyze IR content for hazard mentions
        ir_hazards = self._analyze_ir_content_for_hazards(ir_content)
        
        prompt = f"""
        As a maritime safety expert, analyze potential hazards for this route:
        
        Weather-Based Hazard Probabilities:
        {json.dumps(hazard_probabilities, indent=2)}
        
        Information from Maritime Bulletins:
        {json.dumps(ir_hazards, indent=2)}
        
        Route Information:
        - Distance: {route_data.get('distance', 0)} km
        - Sample Points: {len(route_data.get('sample_points', []))}
        
        Identify and assess:
        1. Immediate hazards (next 24 hours)
        2. Route-specific hazards and high-risk areas
        3. Weather-related hazards (storms, fog, high winds)
        4. Maritime traffic and navigation hazards
        5. Seasonal/regional hazards
        6. Emergency response capabilities along route
        
        For each hazard, provide:
        - Risk level (low/medium/high/critical)
        - Probability of occurrence
        - Potential impact on navigation
        - Mitigation strategies
        - Monitoring requirements
        
        Format as structured JSON with hazard categories and details.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a maritime safety officer with expertise in hazard assessment and risk management. Focus on actionable safety information."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.2
            )
            
            content = response.choices[0].message.content.strip()
            
            # Calculate confidence based on data quality
            confidence = self._calculate_hazard_confidence(hazard_probabilities, ir_hazards)
            
            return AgentResponse(
                agent_type=self.agent_type,
                content=content,
                confidence=confidence,
                metadata={
                    "hazard_count": len(hazard_probabilities) + len(ir_hazards),
                    "ir_sources": len(ir_content),
                    "analysis_type": "comprehensive_hazard_assessment"
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return AgentResponse(
                agent_type=self.agent_type,
                content=f"Hazard detection unavailable: {str(e)}",
                confidence=0.1,
                metadata={"error": str(e)},
                timestamp=datetime.now()
            )
    
    def _extract_hazard_probabilities(self, weather_data: Dict) -> Dict:
        """Extract hazard probabilities from weather data"""
        hazards = {}
        
        current = weather_data.get("current", {})
        forecast = weather_data.get("forecast", [])
        
        # Wind-based hazards
        wind_speed = current.get('wind_speed', 0)
        if wind_speed > 30:
            hazards['high_winds'] = {'probability': 0.9, 'severity': 'high'}
        elif wind_speed > 20:
            hazards['moderate_winds'] = {'probability': 0.7, 'severity': 'medium'}
        
        # Wave-based hazards
        wave_height = current.get('wave_height', 0)
        if wave_height > 3:
            hazards['rough_seas'] = {'probability': 0.9, 'severity': 'high'}
        elif wave_height > 2:
            hazards['choppy_conditions'] = {'probability': 0.8, 'severity': 'medium'}
        
        # Visibility hazards
        visibility = current.get('visibility', 10000)
        if visibility < 2000:
            hazards['poor_visibility'] = {'probability': 0.9, 'severity': 'high'}
        elif visibility < 5000:
            hazards['reduced_visibility'] = {'probability': 0.7, 'severity': 'medium'}
        
        return hazards
    
    def _analyze_ir_content_for_hazards(self, ir_content: List[Dict]) -> List[Dict]:
        """Analyze IR content for hazard mentions using NLP"""
        hazards = []
        
        hazard_keywords = {
            'storm': ['storm', 'hurricane', 'typhoon', 'cyclone', 'tempest'],
            'fog': ['fog', 'mist', 'haze', 'visibility'],
            'ice': ['ice', 'iceberg', 'frozen', 'frost'],
            'shipping': ['traffic', 'vessel', 'collision', 'shipping'],
            'equipment': ['equipment', 'failure', 'breakdown', 'malfunction'],
            'navigation': ['navigation', 'gps', 'compass', 'charts']
        }
        
        for content in ir_content:
            text = content.get('text', '').lower()
            title = content.get('title', '').lower()
            
            for hazard_type, keywords in hazard_keywords.items():
                for keyword in keywords:
                    if keyword in text or keyword in title:
                        hazards.append({
                            'type': hazard_type,
                            'source': content.get('source', 'unknown'),
                            'title': content.get('title', ''),
                            'relevance': 'high' if keyword in title else 'medium'
                        })
                        break  # Avoid duplicate entries for same content
        
        return hazards
    
    def _calculate_hazard_confidence(self, weather_hazards: Dict, ir_hazards: List[Dict]) -> float:
        """Calculate confidence in hazard detection"""
        base_confidence = 0.6
        
        # More hazard data increases confidence
        data_bonus = min(0.3, (len(weather_hazards) + len(ir_hazards)) * 0.05)
        
        # IR content increases confidence
        ir_bonus = min(0.1, len(ir_hazards) * 0.02)
        
        return min(0.95, base_confidence + data_bonus + ir_bonus)

class DisasterPredictorAgent:
    """Specialized agent for disaster prediction and historical analysis"""
    
    def __init__(self, openai_client):
        self.client = openai_client
        self.agent_type = AgentType.DISASTER_PREDICTOR
        
    async def analyze_disaster_risks(self, location: str, latitude: float = None, longitude: float = None, weather_data: Dict = None) -> AgentResponse:
        """Analyze disaster risks and provide predictions"""
        try:
            from .disaster_prediction_service import disaster_service
            
            # Get historical disaster data
            historical_disasters = await disaster_service.search_historical_disasters(
                location=location,
                latitude=latitude,
                longitude=longitude,
                radius_km=200, 
                years_back=10
            )
            
            # Get disaster predictions
            predictions = await disaster_service.generate_disaster_predictions(
                location=location,
                latitude=latitude,
                longitude=longitude,
                weather_data=weather_data
            )
            
            # Format historical disasters summary
            historical_summary = ""
            if historical_disasters:
                historical_summary = "HISTORICAL DISASTERS (Past 10 years):\n"
                for disaster in historical_disasters[:5]:  # Show top 5 recent
                    historical_summary += f"• {disaster.event_type}: {disaster.description} ({disaster.date.strftime('%Y-%m-%d')})\n"
            else:
                historical_summary = "No significant historical disasters found in this area."
            
            # Format predictions summary
            predictions_summary = ""
            if predictions:
                predictions_summary = "CURRENT RISK PREDICTIONS:\n"
                for pred in predictions:
                    risk_level = "HIGH" if pred.probability > 0.6 else "MEDIUM" if pred.probability > 0.3 else "LOW"
                    predictions_summary += f"• {pred.prediction_type}: {risk_level} risk ({pred.probability:.1%} probability)\n"
                    predictions_summary += f"  Time Window: {pred.time_window}\n"
                    predictions_summary += f"  Key Safety Measures: {', '.join(pred.safety_measures[:3])}\n\n"
            else:
                predictions_summary = "No elevated disaster risks detected for current conditions."
            
            # Create comprehensive AI analysis
            prompt = f"""
            As a disaster risk expert specializing in maritime safety, analyze the following disaster risk assessment for {location}:
            
            LOCATION ANALYSIS:
            - Location: {location}
            - Coordinates: {latitude:.2f}, {longitude:.2f} (if available)
            
            {historical_summary}
            
            {predictions_summary}
            
            CURRENT CONDITIONS:
            {self._format_weather_for_disaster_analysis(weather_data)}
            
            Provide a comprehensive disaster risk analysis including:
            
            1. **HISTORICAL CONTEXT** - Summary of past disasters and patterns
            2. **CURRENT RISK ASSESSMENT** - Immediate and near-term threats
            3. **PREDICTIVE ANALYSIS** - Likelihood and timeline of potential disasters
            4. **SAFETY RECOMMENDATIONS** - Specific protective measures and preparations
            5. **MONITORING STRATEGY** - Key indicators and information sources to watch
            6. **EMERGENCY PREPAREDNESS** - Essential emergency planning considerations
            
            Focus on actionable intelligence that helps mariners make informed safety decisions.
            Be clear about confidence levels and data limitations.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a senior disaster risk analyst with expertise in maritime safety and emergency preparedness. Provide thorough, evidence-based risk assessments while maintaining appropriate caution about prediction limitations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.2
            )
            
            content = response.choices[0].message.content.strip()
            
            # Calculate confidence based on data availability
            confidence = 0.3  # Base confidence
            if historical_disasters:
                confidence += 0.2  # Historical data available
            if predictions:
                confidence += 0.3  # Current predictions available
            if weather_data:
                confidence += 0.2  # Weather context available
            
            return AgentResponse(
                agent_type=self.agent_type,
                content=content,
                confidence=min(0.9, confidence),
                metadata={
                    "historical_disasters": len(historical_disasters),
                    "active_predictions": len(predictions),
                    "analysis_type": "comprehensive_disaster_risk",
                    "location": location,
                    "coordinates": {"lat": latitude, "lon": longitude} if latitude and longitude else None
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Disaster prediction analysis failed: {e}")
            return AgentResponse(
                agent_type=self.agent_type,
                content=f"Disaster risk analysis unavailable: {str(e)}",
                confidence=0.1,
                metadata={"error": str(e)},
                timestamp=datetime.now()
            )
    
    async def analyze_current_hazard_alerts(self, location: str = None, latitude: float = None, longitude: float = None) -> AgentResponse:
        """Analyze current real-time hazard alerts using the hazard alerts service"""
        print(f"🚨 ANALYZE_CURRENT_HAZARD_ALERTS: Starting analysis for location={location}, lat={latitude}, lon={longitude}")
        try:
            from .hazard_alerts_service import hazard_alerts_service
            
            # Smart detection of global vs local queries
            # Global indicators: asking about multiple countries, global situation, "any country", etc.
            global_keywords = ["countries", "global", "world", "worldwide", "any country", "which country", "what countries", "affected by", "international", "globally"]
            is_global_query = (
                not location or 
                location == "requested location" or 
                any(word in (location or "").lower() for word in ["countries", "global", "world"]) or
                any(keyword in user_query.lower() for keyword in global_keywords) if hasattr(self, '_current_query') else True
            )
            
            if is_global_query or not latitude or not longitude:
                # For global queries, get alerts for major regions
                global_alerts = []
                print(f"🌍 ANALYZE_CURRENT_HAZARD_ALERTS: Performing GLOBAL analysis (location='{location}', is_global={is_global_query})")
                
                # Major regions to check for global overview
                regions = [
                    {"name": "East Asia (China/Taiwan)", "lat": 24.0, "lon": 121.0},
                    {"name": "Southeast Asia", "lat": 1.3, "lon": 103.8},
                    {"name": "North America", "lat": 40.7, "lon": -74.0},
                    {"name": "Europe", "lat": 51.5, "lon": 0.0},
                    {"name": "Australia", "lat": -33.9, "lon": 151.2}
                ]
                
                for region in regions:
                    result = await hazard_alerts_service.get_comprehensive_alerts(
                        latitude=region["lat"], 
                        longitude=region["lon"]
                    )
                    alerts = result.get("alerts", [])
                    if alerts:
                        global_alerts.extend([{"region": region["name"], "alerts": alerts}])
            else:
                # Get alerts for specific location
                print(f"📍 ANALYZE_CURRENT_HAZARD_ALERTS: Performing LOCAL analysis for lat={latitude}, lon={longitude}")
                result = await hazard_alerts_service.get_comprehensive_alerts(
                    latitude=latitude, 
                    longitude=longitude
                )
                alerts = result.get("alerts", [])
                global_alerts = [{"region": location or f"Location ({latitude:.2f}, {longitude:.2f})", "alerts": alerts}]
            
            # Format current alerts summary
            current_alerts_summary = ""
            total_alerts = 0
            affected_regions = []
            major_disasters = []
            
            if global_alerts:
                current_alerts_summary = "CURRENT ACTIVE DISASTERS & HAZARDS:\n\n"
                for region_data in global_alerts:
                    region_name = region_data["region"]
                    alerts = region_data["alerts"]
                    
                    if alerts:
                        total_alerts += len(alerts)
                        affected_regions.append(region_name)
                        current_alerts_summary += f"🌍 **{region_name}**:\n"
                        
                        for alert in alerts[:3]:  # Show top 3 alerts per region
                            severity_emoji = "🔴" if alert.get("severity", "").lower() in ["extreme", "severe"] else "🟠" if alert.get("severity", "").lower() == "moderate" else "🟡"
                            current_alerts_summary += f"  {severity_emoji} {alert.get('title', 'Alert')}\n"
                            current_alerts_summary += f"     • Type: {alert.get('event_type', 'Unknown')}\n"
                            current_alerts_summary += f"     • Severity: {alert.get('severity', 'Unknown')}\n"
                            
                            # Track major disasters
                            if alert.get("severity", "").lower() in ["extreme", "severe"]:
                                major_disasters.append({
                                    "region": region_name,
                                    "title": alert.get('title', 'Alert'),
                                    "type": alert.get('event_type', 'Unknown')
                                })
                            
                            if alert.get('description'):
                                current_alerts_summary += f"     • Details: {alert.get('description')[:100]}...\n"
                            current_alerts_summary += "\n"
                        
                        if len(alerts) > 3:
                            current_alerts_summary += f"     ... and {len(alerts) - 3} more alerts\n\n"
            else:
                current_alerts_summary = "✅ No major active disasters detected in monitored regions."
            
            print(f"🚨 ANALYZE_CURRENT_HAZARD_ALERTS: Total alerts found: {total_alerts}, Affected regions: {len(affected_regions)}")
            
            # Create comprehensive AI analysis
            prompt = f"""
            As a real-time disaster monitoring expert specializing in maritime safety, analyze the following current hazard alert situation:
            
            REAL-TIME GLOBAL DISASTER STATUS:
            - Total Active Alerts: {total_alerts}
            - Affected Regions: {len(affected_regions)}
            - Major Disasters: {len(major_disasters)}
            
            {current_alerts_summary}
            
            MAJOR DISASTERS SUMMARY:
            {chr(10).join([f"• {d['region']}: {d['title']} ({d['type']})" for d in major_disasters]) if major_disasters else "No major disasters currently active"}
            
            Provide a comprehensive real-time disaster analysis including:
            
            1. **GLOBAL SITUATION OVERVIEW** - Current state of natural disasters worldwide
            2. **AFFECTED COUNTRIES/REGIONS** - Specific areas experiencing disasters now
            3. **DISASTER TYPES & SEVERITY** - What types of disasters and their impact levels
            4. **MARITIME IMPACT** - How these disasters affect marine navigation and safety
            5. **IMMEDIATE CONCERNS** - Most urgent situations requiring attention
            6. **SAFETY RECOMMENDATIONS** - Actionable advice for mariners in affected areas
            
            Focus on providing current, factual information about active disasters. Be specific about which countries and regions are affected RIGHT NOW.
            If no major disasters are active, clearly state that as well.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a real-time disaster monitoring expert with access to current global hazard data. Provide accurate, timely information about active natural disasters and their maritime implications."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            # Calculate confidence based on data availability
            confidence = 0.5  # Base confidence for real-time data
            if total_alerts > 0:
                confidence += 0.3  # Active alerts available
            if major_disasters:
                confidence += 0.2  # Major disasters detected
            
            return AgentResponse(
                agent_type=self.agent_type,
                content=content,
                confidence=min(0.95, confidence),
                metadata={
                    "total_active_alerts": total_alerts,
                    "affected_regions": affected_regions,
                    "major_disasters": len(major_disasters),
                    "analysis_type": "real_time_hazard_alerts",
                    "regions_checked": len(global_alerts) if global_alerts else 0
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            print(f"🚨 ANALYZE_CURRENT_HAZARD_ALERTS: ERROR - {str(e)}")
            logger.error(f"Real-time hazard alert analysis failed: {e}")
            import traceback
            print(f"🚨 ANALYZE_CURRENT_HAZARD_ALERTS: Full traceback: {traceback.format_exc()}")
            return AgentResponse(
                agent_type=self.agent_type,
                content=f"Real-time disaster monitoring unavailable: {str(e)}. Please check official disaster monitoring websites for current information.",
                confidence=0.1,
                metadata={"error": str(e)},
                timestamp=datetime.now()
            )

    def _format_weather_for_disaster_analysis(self, weather_data: Dict) -> str:
        """Format weather data for disaster risk analysis"""
        if not weather_data:
            return "No current weather data available."
        
        current = weather_data.get('current', weather_data)
        
        return f"""Weather Conditions:
        - Wind Speed: {current.get('wind_speed_10m', current.get('wind_speed', 'N/A'))} km/h
        - Atmospheric Pressure: {current.get('pressure_msl', current.get('pressure', 'N/A'))} hPa  
        - Wave Height: {current.get('wave_height', 'N/A')} meters
        - Visibility: {current.get('visibility', 'N/A')} meters
        - Temperature: {current.get('temperature_2m', current.get('temperature', 'N/A'))}°C"""

class InformationRetrieverAgent:
    """Specialized agent for retrieving and processing maritime information"""
    
    def __init__(self, openai_client):
        self.client = openai_client
        self.agent_type = AgentType.INFORMATION_RETRIEVER
        
    async def process_maritime_bulletins(self, raw_content: List[str]) -> AgentResponse:
        """Process and summarize maritime bulletins and notices"""
        
        processed_content = []
        for content in raw_content:
            summary = await self._summarize_bulletin(content)
            processed_content.append(summary)
        
        prompt = f"""
        As a maritime information specialist, analyze these maritime bulletins and notices:
        
        Bulletin Summaries:
        {json.dumps(processed_content, indent=2)}
        
        Extract and organize:
        1. Navigation warnings and notices
        2. Weather-related maritime advisories
        3. Port and harbor information
        4. Safety alerts and emergency notices
        5. Regulatory updates affecting navigation
        6. Temporary restrictions or closures
        
        Prioritize information by:
        - Immediate safety impact
        - Route relevance
        - Time sensitivity
        - Regulatory compliance requirements
        
        Format as structured JSON with categories and priority levels.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a maritime information analyst specializing in processing navigation notices and bulletins for operational relevance."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            confidence = min(0.9, 0.7 + len(processed_content) * 0.05)
            
            return AgentResponse(
                agent_type=self.agent_type,
                content=content,
                confidence=confidence,
                metadata={
                    "bulletins_processed": len(processed_content),
                    "processing_type": "maritime_bulletins"
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return AgentResponse(
                agent_type=self.agent_type,
                content=f"Information processing unavailable: {str(e)}",
                confidence=0.1,
                metadata={"error": str(e)},
                timestamp=datetime.now()
            )
    
    async def _summarize_bulletin(self, content: str) -> Dict:
        """Summarize individual bulletin content"""
        # Extract key information using regex patterns
        date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}'
        time_pattern = r'\d{1,2}:\d{2}'
        position_pattern = r'\d+°\d+\'[NS]\s+\d+°\d+\'[EW]'
        
        dates = re.findall(date_pattern, content)
        times = re.findall(time_pattern, content)
        positions = re.findall(position_pattern, content)
        
        # Basic keyword extraction
        keywords = []
        important_terms = ['warning', 'danger', 'caution', 'closed', 'restricted', 'emergency']
        for term in important_terms:
            if term.lower() in content.lower():
                keywords.append(term)
        
        return {
            'summary': content[:200] + '...' if len(content) > 200 else content,
            'dates': dates,
            'times': times,
            'positions': positions,
            'keywords': keywords,
            'length': len(content)
        }

class CommunicationManagerAgent:
    """Specialized agent for managing communications and user interactions"""
    
    def __init__(self, openai_client):
        self.client = openai_client
        self.agent_type = AgentType.COMMUNICATION_MANAGER
        
    def _calculate_maritime_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> dict:
        """Calculate accurate maritime distance using Haversine formula"""
        import math
        
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        distance_km = c * r
        distance_nm = distance_km * 0.539957  # Convert to nautical miles
        
        return {
            'km': round(distance_km, 2),
            'nm': round(distance_nm, 2),
            'miles': round(distance_km * 0.621371, 2)
        }
    
    def _extract_locations_from_query(self, query: str) -> tuple:
        """Extract two locations from distance calculation queries"""
        import re
        
        # Common location database for maritime queries
        locations = {
            'chennai': (13.0827, 80.2707),
            'chennai fort': (13.0827, 80.2707),
            'colombo': (6.9271, 79.8612),
            'colombo fort': (6.9271, 79.8612),
            'mumbai': (19.0760, 72.8777),
            'kochi': (9.9312, 76.2673),
            'singapore': (1.3521, 103.8198),
            'manila': (14.5995, 120.9842),
            'hong kong': (22.3193, 114.1694),
            'dubai': (25.2048, 55.2708),
            'port said': (31.2653, 32.3019),
            'suez': (29.9668, 32.5498),
            'jaffna': (9.6615, 80.0255),
            'trincomalee': (8.5874, 81.2152),
            'galle': (6.0535, 80.2210),
            'new york': (40.7128, -74.0060),
            'london': (51.5074, -0.1278)
        }
        
        query_lower = query.lower()
        found_locations = []
        
        # Find locations mentioned in the query
        for location_name, coords in locations.items():
            if location_name in query_lower:
                found_locations.append((location_name, coords))
        
        # If we found exactly 2 locations, return them
        if len(found_locations) == 2:
            return found_locations[0], found_locations[1]
        
        return None, None

    async def generate_user_response(self, user_query: str, agent_responses: List[AgentResponse], context: Optional[NavigationContext] = None, weather_data: Dict = None, location_name: str = None) -> AgentResponse:
        """Generate user-friendly response from agent analysis"""
        
        # Check if this is a distance calculation query
        distance_keywords = ['distance', 'calculate', 'between', 'minimum distance', 'nautical miles', 'how far']
        is_distance_query = any(keyword in user_query.lower() for keyword in distance_keywords)
        
        distance_info = ""
        base_confidence = 0.5
        
        if is_distance_query:
            loc1, loc2 = self._extract_locations_from_query(user_query)
            if loc1 and loc2:
                loc1_name, loc1_coords = loc1
                loc2_name, loc2_coords = loc2
                
                distances = self._calculate_maritime_distance(
                    loc1_coords[0], loc1_coords[1], 
                    loc2_coords[0], loc2_coords[1]
                )
                
                distance_info = f"""
                
MARITIME DISTANCE CALCULATION:
📍 From: {loc1_name.title()} ({loc1_coords[0]}°N, {loc1_coords[1]}°E)
📍 To: {loc2_name.title()} ({loc2_coords[0]}°N, {loc2_coords[1]}°E)
📏 Great Circle Distance: {distances['nm']} nautical miles ({distances['km']} km)
⏱️ Estimated sailing time: ~{distances['nm']//10}-{distances['nm']//8} hours at 8-10 knots
🧭 This is the shortest sea route distance (great circle)
                """
                base_confidence = 0.9  # High confidence for distance calculations
            else:
                distance_info = "\n⚠️ Could not identify both locations for distance calculation. Please specify both departure and destination ports clearly."
                base_confidence = 0.3
        
        # Compile information from all agents
        compiled_info = self._compile_agent_information(agent_responses)
        
        # Enhanced weather information formatting
        weather_info = ""
        if weather_data:
            current = weather_data.get('current', weather_data)
            temperature = current.get('temperature_2m', current.get('temperature', 'N/A'))
            humidity = current.get('relative_humidity_2m', current.get('humidity', 'N/A'))
            wind_speed = current.get('wind_speed_10m', current.get('wind_speed', 'N/A'))
            wind_direction = current.get('wind_direction_10m', current.get('wind_direction', 'N/A'))
            pressure = current.get('pressure_msl', current.get('pressure', 'N/A'))
            visibility = current.get('visibility', 'N/A')
            
            # Convert units for better understanding
            temp_f = f"{temperature * 9/5 + 32:.1f}°F" if isinstance(temperature, (int, float)) else "N/A"
            wind_knots = f"{wind_speed * 0.539957:.1f} knots" if isinstance(wind_speed, (int, float)) else "N/A"
            vis_miles = f"{visibility * 0.000621371:.1f} miles" if isinstance(visibility, (int, float)) and visibility > 0 else "N/A"
            
            weather_info = f"""
        
        LIVE WEATHER DATA for {location_name or 'requested location'}:
        🌡️ Temperature: {temperature}°C ({temp_f})
        💧 Humidity: {humidity}%
        💨 Wind: {wind_speed} km/h ({wind_knots}) from {wind_direction}°
        📊 Pressure: {pressure} hPa
        👁️ Visibility: {visibility/1000 if isinstance(visibility, (int, float)) and visibility > 0 else 'N/A'} km ({vis_miles})
        🌊 Wave Height: {current.get('wave_height', 'N/A')} meters
        ⏱️ Data timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
        """
        
        # Enhanced NLP understanding for better responses
        query_type = self._analyze_query_intent(user_query)
        
        prompt = f"""
        As a professional maritime navigation expert, provide a precise, accurate response to this query:
        
        USER QUERY: "{user_query}"
        QUERY TYPE: {query_type}
        
        EXPERT ANALYSIS AVAILABLE:
        {json.dumps(compiled_info, indent=2, default=str)}
        {weather_info}
        {distance_info}
        
        CONTEXT: {json.dumps(context.__dict__ if context else {}, indent=2, default=str)}
        
        CRITICAL INSTRUCTIONS:
        🎯 GIVE SPECIFIC, ACCURATE ANSWERS - No generic responses
        📊 USE PROVIDED CALCULATIONS - Don't recalculate, use the exact distance data provided
        🔢 BE PRECISE - Include exact numbers, coordinates, and measurements when available
        ⚓ MARITIME FOCUS - Use proper nautical terminology and units (nautical miles, knots, etc.)
        🚫 NO FLUFF - Skip generic safety advice unless specifically asked
        ✅ DIRECT ANSWERS - Answer the exact question asked, then provide brief context
        📍 LOCATION SPECIFIC - Use exact coordinates and location names provided
        
        RESPONSE STRUCTURE:
        1. Direct answer to the specific question
        2. Key technical details/calculations 
        3. Brief practical implications (only if relevant)
        
        LENGTH: Concise and focused (150-250 words maximum)
        TONE: Professional maritime expert - confident, precise, technical when needed
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a friendly but professional maritime navigation assistant. Always prioritize safety while being helpful and informative."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.6
            )
            
            content = response.choices[0].message.content.strip()
            
            # Enhanced confidence calculation
            if agent_responses:
                # Use average of agent confidences but boost if we have distance calculations
                avg_confidence = sum(resp.confidence for resp in agent_responses) / len(agent_responses)
                final_confidence = max(avg_confidence, base_confidence)
            else:
                # For direct queries without agent analysis, use intelligent confidence
                if is_distance_query and distance_info and "Could not identify" not in distance_info:
                    final_confidence = 0.95  # Very high confidence for successful distance calculations
                elif weather_data:
                    final_confidence = 0.85  # High confidence when we have real weather data
                elif any(keyword in user_query.lower() for keyword in ['what is', 'how to', 'explain', 'define']):
                    final_confidence = 0.80  # Good confidence for knowledge questions
                else:
                    final_confidence = 0.75  # Default confidence for general maritime queries
            
            return AgentResponse(
                agent_type=self.agent_type,
                content=content,
                confidence=final_confidence,
                metadata={
                    "source_agents": [resp.agent_type.value for resp in agent_responses],
                    "user_query": user_query,
                    "has_distance_calc": is_distance_query and distance_info != "",
                    "has_weather_data": weather_data is not None
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            # Check for specific OpenAI errors
            error_str = str(e)
            if "insufficient_quota" in error_str or "quota" in error_str.lower():
                content = "I'm currently experiencing service limitations due to API quota restrictions. The AI features are temporarily unavailable. Please try again later or contact support."
            elif "api_key" in error_str.lower() or "authentication" in error_str.lower():
                content = "There's an issue with the AI service configuration. Please contact support for assistance."
            else:
                content = "I'm sorry, I'm having trouble processing your request right now. Please try again later or contact support for assistance."
            
            return AgentResponse(
                agent_type=self.agent_type,
                content=content,
                confidence=0.1,
                metadata={"error": str(e)},
                timestamp=datetime.now()
            )
    
    def _analyze_query_intent(self, user_query: str) -> str:
        """Analyze user query to understand intent for better NLP processing"""
        query_lower = user_query.lower()
        
        # Weather-related queries
        if any(word in query_lower for word in ['weather', 'wind', 'wave', 'storm', 'temperature', 'forecast', 'conditions', 'rain', 'sunny', 'cloudy']):
            if any(word in query_lower for word in ['current', 'now', 'today', 'present']):
                return "Current Weather Inquiry"
            elif any(word in query_lower for word in ['forecast', 'tomorrow', 'week', 'future', 'will be']):
                return "Weather Forecast Request"
            else:
                return "General Weather Information"
        
        # Navigation and route queries
        if any(word in query_lower for word in ['route', 'navigation', 'path', 'course', 'direction', 'navigate', 'travel', 'journey']):
            return "Navigation Planning"
        
        # Safety and hazard queries
        if any(word in query_lower for word in ['safe', 'danger', 'hazard', 'risk', 'warning', 'alert', 'emergency']):
            return "Safety Assessment"
        
        # Location-specific queries
        if any(word in query_lower for word in ['where', 'location', 'place', 'coordinates', 'position']):
            return "Location Information"
        
        # Vessel operations
        if any(word in query_lower for word in ['vessel', 'boat', 'ship', 'marina', 'harbor', 'port', 'dock']):
            return "Vessel Operations"
        
        # General maritime questions
        if any(word in query_lower for word in ['marine', 'maritime', 'ocean', 'sea', 'water']):
            return "Maritime Information"
        
        return "General Inquiry"
    
    def _compile_agent_information(self, agent_responses: List[AgentResponse]) -> Dict:
        """Compile information from multiple agents"""
        compiled = {
            "agent_count": len(agent_responses),
            "average_confidence": sum(resp.confidence for resp in agent_responses) / len(agent_responses) if agent_responses else 0,
            "responses_by_type": {}
        }
        
        for response in agent_responses:
            compiled["responses_by_type"][response.agent_type.value] = {
                "content": response.content,
                "confidence": response.confidence,
                "metadata": response.metadata
            }
        
        return compiled

class MultiAgentAIService:
    """Main service coordinating multiple AI agents"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Try OpenAI first
        if self.openai_api_key:
            try:
                self.client = openai.OpenAI(
                    api_key=self.openai_api_key,
                    timeout=150.0  # 150 second timeout for OpenAI API calls
                )
                
                # Test the connection
                test_response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                print("✅ OpenAI API working!")
                self.ai_provider = "openai"
            except Exception as e:
                logger.error(f"❌ OpenAI API failed during initialization: {e}")
                logger.error(f"❌ Full traceback: {traceback.format_exc()}")
                print(f"⚠️ OpenAI API failed: {e}")
                self.client = None
                self.ai_provider = self._setup_free_alternative()
        else:
            logger.warning("⚠️ No OpenAI API key found in environment")
            print("ℹ️ No OpenAI API key found, using free alternatives")
            self.client = None
            self.ai_provider = self._setup_free_alternative()
        
        # Initialize agents only if OpenAI is working
        if self.client and self.ai_provider == "openai":
            self.weather_analyst = WeatherAnalystAgent(self.client)
            self.route_optimizer = RouteOptimizerAgent(self.client)
            self.hazard_detector = HazardDetectorAgent(self.client)
            self.disaster_predictor = DisasterPredictorAgent(self.client)
            self.information_retriever = InformationRetrieverAgent(self.client)
            self.communication_manager = CommunicationManagerAgent(self.client)
        else:
            print(f"🔄 Using {self.ai_provider} for AI functionality")
    
    def _setup_free_alternative(self) -> str:
        """Setup free AI alternative"""
        if OLLAMA_AVAILABLE and ollama_service.available:
            print("🚀 Using Ollama (Local AI)")
            return "ollama"
        elif HUGGINGFACE_AVAILABLE:
            print("🤗 Using Hugging Face (Free API)")
            return "huggingface"
        else:
            print("📋 Using fallback responses")
            return "fallback"
    
    async def comprehensive_analysis(self, weather_data: Dict, route_data: Dict, 
                                   ir_content: List[Dict], context: NavigationContext) -> Dict[str, AgentResponse]:
        """Run comprehensive analysis using all agents"""
        
        if not self.client:
            return self._generate_fallback_responses()
        
        # Run agents in parallel for efficiency
        tasks = []
        
        # Weather analysis
        if weather_data:
            location = {"name": f"{context.departure_port} to {context.destination_port}"}
            tasks.append(self.weather_analyst.analyze_weather_conditions(weather_data, location))
        
        # Route optimization
        if route_data:
            # Need weather analysis for route optimization, so we'll do this after
            pass
        
        # Hazard detection
        if weather_data and route_data:
            tasks.append(self.hazard_detector.detect_hazards(weather_data, route_data, ir_content))
        
        # Information retrieval
        if ir_content:
            bulletin_texts = [item.get('text', '') for item in ir_content]
            tasks.append(self.information_retriever.process_maritime_bulletins(bulletin_texts))
        
        # Execute initial tasks
        initial_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        responses = {}
        weather_analysis = {}
        
        # Process initial results
        for i, result in enumerate(initial_results):
            if isinstance(result, AgentResponse):
                if result.agent_type == AgentType.WEATHER_ANALYST:
                    responses["weather"] = result
                    weather_analysis = {"severity_index": result.metadata.get("severity_index", 5)}
                elif result.agent_type == AgentType.HAZARD_DETECTOR:
                    responses["hazards"] = result
                elif result.agent_type == AgentType.INFORMATION_RETRIEVER:
                    responses["information"] = result
        
        # Now run route optimization with weather analysis
        if route_data and weather_analysis:
            route_response = await self.route_optimizer.optimize_route(route_data, weather_analysis, context)
            responses["route"] = route_response
        
        return responses
    
    async def chat_response(self, user_query: str, context_data: Dict = None) -> AgentResponse:
        """Generate chat response for user queries"""
        if not self.client:
            logger.error("❌ No OpenAI client available, returning fallback")
            return self._generate_fallback_response(user_query)
        
        # Determine what analysis is needed based on the query
        query_lower = user_query.lower()
        
        agent_responses = []
        
        # Check if user is asking for weather and try to extract location
        weather_requested = any(word in query_lower for word in ['weather', 'wind', 'wave', 'storm', 'temperature', 'forecast', 'conditions'])
        if weather_requested:
            location_match = None
            use_current_location = False
            
            # Check if current location coordinates are available
            if context_data and 'current_location' in context_data:
                current_loc = context_data['current_location']
                if 'latitude' in current_loc and 'longitude' in current_loc:
                    use_current_location = True
            
            # If current location is not available or user specified a different location, try to extract from query
            if not use_current_location:
                # Try to extract location from query
                import re
                # Look for patterns like "weather of [location]", "weather in [location]", etc.
                location_patterns = [
                    r'weather\s+(?:of|in|at|for)\s+([^?.,!]+)',
                    r'current\s+weather\s+(?:of|in|at|for)\s+([^?.,!]+)',
                    r'conditions\s+(?:of|in|at|for)\s+([^?.,!]+)',
                    r'(?:wind|wave|temperature)\s+(?:of|in|at|for)\s+([^?.,!]+)'
                ]
                
                for pattern in location_patterns:
                    match = re.search(pattern, query_lower)
                    if match:
                        location_match = match.group(1).strip()
                        break
            
            # If no location found in query, try to find standalone location names
            if not location_match:
                words = query_lower.split()
                # Common location indicators
                for i, word in enumerate(words):
                    if word in ['jaffna', 'sri', 'lanka', 'colombo', 'galle', 'trincomalee', 'kandy', 'manila', 'singapore', 'mumbai', 'delhi', 'chennai', 'kochi', 'new', 'york', 'london', 'paris', 'tokyo']:
                        # Try to capture location
                        if word == 'sri' and i + 1 < len(words) and words[i+1] == 'lanka':
                            location_match = 'sri lanka'
                        elif word == 'new' and i + 1 < len(words) and words[i+1] == 'york':
                            location_match = 'new york'
                        elif word in ['jaffna', 'colombo', 'galle', 'trincomalee', 'kandy']:
                            location_match = f"{word} sri lanka"
                        else:
                            location_match = word
                        break
            
            # Fetch real weather data
            if use_current_location:
                # Use current location coordinates
                current_loc = context_data['current_location']
                weather_data = await self._fetch_real_weather_data(
                    lat=current_loc['latitude'], 
                    lon=current_loc['longitude']
                )
                if weather_data:
                    context_data = context_data or {}
                    context_data['weather_data'] = weather_data
                    context_data['location_name'] = "your current location"
                else:
                    logger.warning("⚠️ Failed to fetch weather data for current location")
            elif location_match:
                weather_data = await self._fetch_real_weather_data(location=location_match)
                if weather_data:
                    context_data = context_data or {}
                    context_data['weather_data'] = weather_data
                    context_data['location_name'] = location_match
                else:
                    logger.warning("⚠️ Failed to fetch real weather data")
        
        # Skip connection test for faster response (client already initialized)
        
        # If context data is available, run relevant analyses
        if context_data:
            weather_data = context_data.get('weather_data')
            route_data = context_data.get('route_data')
            ir_content = context_data.get('ir_content', [])
            
            # Run quick analyses based on query content
            if any(word in query_lower for word in ['weather', 'wind', 'wave', 'storm']):
                if weather_data:
                    location = {"name": "Queried Location"}
                    weather_response = await self.weather_analyst.analyze_weather_conditions(weather_data, location)
                    agent_responses.append(weather_response)
            
            if any(word in query_lower for word in ['route', 'path', 'navigate', 'optimize']):
                if route_data and weather_data:
                    # Create minimal context for route analysis
                    min_context = NavigationContext(
                        vessel_type="general",
                        vessel_size="medium",
                        experience_level="intermediate",
                        cargo_type=None,
                        departure_port="Start",
                        destination_port="End",
                        departure_time=datetime.now().isoformat(),
                        urgency_level="normal"
                    )
                    route_response = await self.route_optimizer.optimize_route(
                        route_data, {"severity_index": 5}, min_context
                    )
                    agent_responses.append(route_response)
            
            if any(word in query_lower for word in ['hazard', 'danger', 'risk', 'safe']):
                if weather_data and route_data:
                    hazard_response = await self.hazard_detector.detect_hazards(weather_data, route_data, ir_content)
                    agent_responses.append(hazard_response)
            
            # Check for disaster-related queries
            if any(word in query_lower for word in ['disaster', 'earthquake', 'tsunami', 'hurricane', 'typhoon', 'storm', 'prediction', 'previous', 'historical', 'warning']):
                location_name = context_data.get('location_name', 'requested location')
                current_loc = context_data.get('current_location', {})
                lat = current_loc.get('latitude') if current_loc else None
                lon = current_loc.get('longitude') if current_loc else None
                
                # Detect if user is asking about CURRENT disasters vs historical
                is_current_query = any(word in query_lower for word in ['now', 'current', 'currently', 'today', 'active', 'affecting', 'recent', 'latest', 'any country', 'any place'])
                
                print(f"🔍 OPENAI: Disaster query detected. Current query: {is_current_query}. Message: '{user_query[:50]}...'")
                
                if is_current_query:
                    # Use real-time hazard alerts for current disaster queries
                    # Pass the query to help determine if it's global or local
                    self.disaster_predictor._current_query = user_query
                    disaster_response = await self.disaster_predictor.analyze_current_hazard_alerts(
                        location=location_name,
                        latitude=lat,
                        longitude=lon
                    )
                else:
                    # Use historical disaster prediction for prediction/historical queries
                    disaster_response = await self.disaster_predictor.analyze_disaster_risks(
                        location=location_name,
                        latitude=lat,
                        longitude=lon,
                        weather_data=weather_data
                    )
                agent_responses.append(disaster_response)
        
        # Generate final response
        try:
            # Pass weather data to communication manager if available
            weather_data = context_data.get('weather_data') if context_data else None
            location_name = context_data.get('location_name') if context_data else None
            
            final_response = await self.communication_manager.generate_user_response(
                user_query, agent_responses, None, weather_data, location_name
            )
            return final_response
        except Exception as e:
            # If communication manager fails, return a fallback response
            logger.error(f"❌ Communication manager failed: {e}")
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            
            error_str = str(e)
            query_lower = user_query.lower()
            
            if "insufficient_quota" in error_str or "quota" in error_str.lower():
                logger.warning("⚠️ Quota issue detected, generating quota-specific fallback")
                if any(word in query_lower for word in ['weather', 'wind', 'wave', 'storm', 'forecast']):
                    content = "I'm currently unable to provide AI-powered weather analysis due to service limitations. For current marine weather information, please check NOAA Marine Weather Services or your local maritime weather broadcasts."
                elif any(word in query_lower for word in ['route', 'navigation', 'course', 'path']):
                    content = "I'm currently unable to provide AI-powered route optimization due to service limitations. For navigation assistance, please consult your marine charts and current weather conditions from official sources."
                elif any(word in query_lower for word in ['hazard', 'danger', 'safety', 'warning']):
                    content = "I'm currently unable to provide AI-powered hazard analysis due to service limitations. For maritime safety information, please monitor official marine safety broadcasts and NAVTEX transmissions."
                else:
                    content = "I'm sorry, the AI assistant is temporarily unavailable due to service limitations. Please try again later or consult official marine weather and navigation resources."
            else:
                logger.warning("⚠️ Generic error, generating generic fallback")
                content = "I'm sorry, I'm having trouble processing your request right now. Please try again later."
            
            fallback_response = AgentResponse(
                agent_type=AgentType.COMMUNICATION_MANAGER,
                content=content,
                confidence=0.1,
                metadata={"error": str(e), "fallback_mode": True},
                timestamp=datetime.now()
            )
            logger.info(f"📤 Returning fallback response with 10% confidence")
            return fallback_response
    
    async def process_message(self, message: str, context: Dict = None) -> Dict[str, str]:
        """Process a message and return response in expected format for API"""
        logger.info(f"📨 Processing message: '{message[:50]}...'")
        logger.info(f"🔧 AI Provider: {self.ai_provider}")
        logger.info(f"🔗 Client available: {self.client is not None}")
        
        try:
            # Use free AI alternatives if available
            if self.ai_provider == "ollama" and OLLAMA_AVAILABLE:
                logger.info("🚀 Using Ollama AI service")
                print(f"🚀 AI SERVICE: Using Ollama for message: '{message[:50]}...'")
                return await ollama_service.process_message(message, context)
            elif self.ai_provider == "huggingface" and HUGGINGFACE_AVAILABLE:
                logger.info("🤗 Using HuggingFace AI service")
                print(f"🤗 AI SERVICE: Using HuggingFace for message: '{message[:50]}...'")
                return await huggingface_service.process_message(message, context)
            elif self.ai_provider == "openai" and self.client:
                # Use OpenAI (original method)
                print(f"🔥 AI SERVICE: Using OpenAI for message: '{message[:50]}...'")
                agent_response = await self.chat_response(message, context)
                
                result = {
                    "response": agent_response.content,
                    "confidence": agent_response.confidence,
                    "context_data": agent_response.metadata
                }
                return result
            else:
                # Use enhanced fallback with real weather data
                logger.warning(f"⚠️ Using fallback response - AI Provider: {self.ai_provider}, Client: {self.client is not None}")
                print(f"📋 AI SERVICE: Using FALLBACK for message: '{message[:50]}...' (Provider: {self.ai_provider}, Client: {self.client is not None})")
                return await self._get_smart_fallback_response(message, context)
                
        except Exception as e:
            logger.error(f"❌ Error in process_message: {e}")
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            print(f"Error in process_message: {e}")
            return await self._get_smart_fallback_response(message, context, str(e))
    
    async def _fetch_real_weather_data(self, location: str = None, lat: float = None, lon: float = None) -> Dict[str, Any]:
        """Fetch real-time weather data directly from weather service"""
        try:
            # Import weather service directly
            from .weather_service import WeatherService
            from .location_search_service import LocationSearchService
            
            weather_service = WeatherService()
            location_service = LocationSearchService()
            
            if lat is not None and lon is not None:
                # Use coordinates if provided
                logger.info(f"🌐 Fetching weather for coordinates: {lat}, {lon}")
                weather_data = await weather_service.get_current_weather(lat, lon)
                return weather_data
            elif location:
                # Get coordinates from location name first
                logger.info(f"🔍 Searching for location: {location}")
                locations = await location_service.search_locations(location, limit=1)
                if locations:
                    first_location = locations[0]
                    lat = first_location.get('latitude')
                    lon = first_location.get('longitude')
                    
                    if lat and lon and lat != 0 and lon != 0:
                        logger.info(f"🌐 Fetching weather for {location} at coordinates: {lat}, {lon}")
                        weather_data = await weather_service.get_current_weather(lat, lon)
                        return weather_data
                    else:
                        logger.warning(f"⚠️ No valid coordinates found for location: {location}")
                        return None
                else:
                    logger.warning(f"⚠️ Location not found: {location}")
                    return None
            else:
                logger.warning("⚠️ No location or coordinates provided")
                return None
                        
        except Exception as e:
            logger.error(f"❌ Error fetching weather data: {e}")
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return None

    def _format_weather_response(self, weather_data: Dict[str, Any], location: str = None) -> str:
        """Format weather data into a readable response"""
        if not weather_data:
            return "🌊 Unable to fetch current weather data. Please check NOAA Marine Weather or VHF broadcasts."
        
        location_str = f" for {location}" if location else ""
        response = f"🌊 **Current Marine Weather{location_str}**\n\n"
        
        # Temperature
        if weather_data.get('temperature'):
            response += f"🌡️ **Temperature:** {weather_data['temperature']}°F\n"
        
        # Wind conditions
        if weather_data.get('wind_speed') and weather_data.get('wind_direction'):
            response += f"💨 **Wind:** {weather_data['wind_direction']} at {weather_data['wind_speed']} mph\n"
        elif weather_data.get('wind_speed'):
            response += f"💨 **Wind Speed:** {weather_data['wind_speed']} mph\n"
        
        # Wave conditions
        if weather_data.get('wave_height'):
            response += f"🌊 **Wave Height:** {weather_data['wave_height']} ft"
            if weather_data.get('wave_period'):
                response += f" (Period: {weather_data['wave_period']}s)"
            response += "\n"
        
        # Visibility
        if weather_data.get('visibility'):
            response += f"👁️ **Visibility:** {weather_data['visibility']} miles\n"
        
        # Pressure
        if weather_data.get('pressure'):
            response += f"📊 **Pressure:** {weather_data['pressure']} mb\n"
        
        # Weather condition
        if weather_data.get('weather_condition'):
            response += f"☁️ **Conditions:** {weather_data['weather_condition']}\n"
        
        # Hazard warnings
        if weather_data.get('hazard_probabilities'):
            hazards = weather_data['hazard_probabilities']
            high_risk_hazards = [hazard for hazard, prob in hazards.items() if prob > 0.6]
            if high_risk_hazards:
                response += f"\n⚠️ **High Risk Hazards:** {', '.join(high_risk_hazards)}\n"
        
        response += f"\n📅 **Updated:** {datetime.now().strftime('%H:%M UTC')}"
        response += "\n\n💡 **Always verify with multiple sources before departure!**"
        
        return response

    async def _get_smart_fallback_response(self, message: str, context: Dict = None, error: str = None) -> Dict[str, str]:
        """Smart fallback responses with marine expertise and real weather data"""
        message_lower = message.lower()
        location = context.get('location', '') if context else ''
        lat = context.get('latitude') if context else None
        lon = context.get('longitude') if context else None
        
        # Extract location from message if not in context
        if not location and not (lat and lon):
            location_match = re.search(r'(weather|forecast|conditions).*(in|at|for|near)\s+([a-zA-Z\s]+)', message, re.IGNORECASE)
            if location_match:
                location = location_match.group(3).strip()
        
        if any(word in message_lower for word in ['weather', 'wind', 'wave', 'storm', 'forecast']):
            # Try to fetch real weather data
            weather_data = await self._fetch_real_weather_data(location, lat, lon)
            if weather_data:
                response = self._format_weather_response(weather_data, location)
            else:
                response = f"🌊 **Marine Weather {f'for {location}' if location else ''}**\n\n"
                response += "📡 **Official Sources:**\n"
                response += "• NOAA Marine Weather: weather.gov/marine\n"
                response += "• VHF Weather: Channels WX1-WX7\n"
                response += "• Marine apps: PredictWind, Windy, SailFlow\n\n"
                response += "⚠️ Always check multiple sources before departure!"
            
        elif any(word in message_lower for word in ['route', 'plan', 'course', 'navigation']):
            response = f"🧭 **Route Planning {f'for {location}' if location else ''}**\n\n"
            response += "📊 **Essential Tools:**\n"
            response += "• Marine Charts: Paper + digital backup\n"
            response += "• Navigation apps: Navionics, ActiveCaptain\n"
            response += "• Tide/Current: NOAA tide tables\n\n"
            response += "📋 **Safety:** File a float plan with someone ashore!"
            
        elif any(word in message_lower for word in ['disaster', 'typhoon', 'hurricane', 'earthquake', 'tsunami', 'affected', 'countries', 'now', 'current', 'active']):
            # Handle disaster/typhoon queries with real-time data
            print(f"🚨 FALLBACK: Detected disaster query: '{message[:50]}...'")
            
            # Smart detection: if asking about "countries" or "global", always do global check
            is_global_fallback = any(word in message_lower for word in ['countries', 'global', 'world', 'any country', 'which country', 'what countries'])
            
            try:
                from .hazard_alerts_service import hazard_alerts_service
                
                # For global queries or when no specific location, check major regions
                if is_global_fallback or not (lat and lon):
                    print(f"🌍 FALLBACK: Performing GLOBAL disaster check")
                    regions = [
                        {"name": "East Asia (China/Taiwan)", "lat": 24.0, "lon": 121.0},
                        {"name": "Southeast Asia", "lat": 1.3, "lon": 103.8},
                        {"name": "North America", "lat": 40.7, "lon": -74.0},
                        {"name": "Europe", "lat": 51.5, "lon": 0.0}
                    ]
                else:
                    print(f"📍 FALLBACK: Checking specific location: {location}")
                    regions = [{"name": location or "Your Location", "lat": lat, "lon": lon}]
                
                global_alerts = []
                total_alerts = 0
                affected_regions = []
                
                for region in regions:
                    result = await hazard_alerts_service.get_comprehensive_alerts(
                        latitude=region["lat"], 
                        longitude=region["lon"]
                    )
                    alerts = result.get("alerts", [])
                    if alerts:
                        total_alerts += len(alerts)
                        affected_regions.append(region["name"])
                        global_alerts.append({"region": region["name"], "alerts": alerts})
                
                if total_alerts > 0:
                    response = f"🚨 **CURRENT GLOBAL DISASTERS ({total_alerts} Active Alerts)**\n\n"
                    
                    for region_data in global_alerts:
                        region_name = region_data["region"]
                        alerts = region_data["alerts"]
                        
                        response += f"🌍 **{region_name}** ({len(alerts)} alerts)\n"
                        for alert in alerts[:2]:  # Show top 2 per region
                            severity_emoji = "🔴" if alert.get("severity", "").lower() in ["extreme", "severe"] else "🟠" if alert.get("severity", "").lower() == "moderate" else "🟡"
                            response += f"  {severity_emoji} {alert.get('title', 'Alert')}\n"
                            response += f"     • Type: {alert.get('event_type', 'Unknown')}\n"
                            if alert.get('description'):
                                response += f"     • Details: {alert.get('description')[:80]}...\n"
                        response += "\n"
                    
                    response += "⚠️ **Maritime Impact:** Severe disruption to shipping in affected areas\n"
                    response += "📡 **Monitor:** Official weather services & maritime alerts"
                else:
                    response = "✅ **No Major Disasters Currently Active**\n\n"
                    response += "🌍 Global disaster monitoring shows no major active events\n\n"
                    response += "📡 **Stay Informed:**\n"
                    response += "• GDACS Global Disaster Alert System\n"
                    response += "• National weather services\n"
                    response += "• Maritime safety broadcasts"
                    
            except Exception as e:
                response = "🚨 **Current Disaster Information**\n\n"
                response += "⚠️ Real-time disaster monitoring temporarily unavailable\n\n"
                response += "📡 **Check Official Sources:**\n"
                response += "• GDACS: gdacs.org\n"
                response += "• National weather services\n"
                response += "• Maritime emergency broadcasts"

        elif any(word in message_lower for word in ['safety', 'emergency', 'hazard', 'danger']):
            response = "⚠️ **Maritime Safety Information**\n\n"
            response += "📻 **Emergency Communications:**\n"
            response += "• VHF Channel 16 (Coast Guard)\n"
            response += "• Phone: *CG or *24 (Coast Guard)\n"
            response += "• EPIRB/PLB for offshore\n\n"
            response += "📢 **Stay Informed:**\n"
            response += "• Notice to Mariners (Coast Guard)\n"
            response += "• NAVTEX broadcasts"
            
        elif any(word in message_lower for word in ['tides', 'tide', 'current', 'currents']):
            response = f"🌊 **Tidal & Current Information {f'for {location}' if location else ''}**\n\n"
            response += "📊 **Official Sources:**\n"
            response += "• NOAA Tides & Currents: tidesandcurrents.noaa.gov\n"
            response += "• UK Admiralty: admiralty.co.uk/tides\n"
            response += "• Marine apps: Tide Charts, iStreams\n\n"
            response += "⚠️ **Critical:** Always check local tide tables before departure!"
            
        elif any(word in message_lower for word in ['port', 'harbor', 'harbour', 'marina']):
            response = f"⚓ **Port & Harbor Information {f'for {location}' if location else ''}**\n\n"
            response += "🏢 **Port Resources:**\n"
            response += "• Port authorities & harbormaster contacts\n"
            response += "• Berthing & mooring information\n"
            response += "• Fuel, water, and supply services\n"
            response += "• Customs & immigration procedures\n\n"
            response += "📞 **Always contact port authority before arrival!**"
            
        elif any(word in message_lower for word in ['fish', 'fishing', 'commercial']):
            response = "🎣 **Commercial Marine Operations**\n\n"
            response += "📋 **Key Considerations:**\n"
            response += "• Weather windows for safe operations\n"
            response += "• Seasonal fish migration patterns\n"
            response += "• Maritime traffic & shipping lanes\n"
            response += "• Regulatory zones & restrictions\n\n"
            response += "🌊 **Check local fishing regulations & marine protected areas**"
            
        elif any(word in message_lower for word in ['hello', 'hi', 'help', 'start']):
            response = "⚓ **Welcome to Advanced Marine AI Assistant!**\n\n"
            response += "🌊 **I'm your comprehensive marine expert for:**\n"
            response += "• 🌪️ **Real-time disasters & hazards** (global & local)\n"
            response += "• 🌤️ **Marine weather & forecasting**\n"
            response += "• 🧭 **Route planning & navigation**\n"
            response += "• ⚓ **Port information & services**\n"
            response += "• 🌊 **Tides, currents & oceanographic data**\n"
            response += "• 🎣 **Commercial marine operations**\n"
            response += "• 🚨 **Emergency procedures & safety**\n\n"
            response += "💡 **Ask me anything marine-related - I understand context!**"
            
        else:
            response = "🌊 **Marine Navigation Assistance**\n\n"
            response += "📍 **Key Resources:**\n"
            response += "• Weather: NOAA Marine (weather.gov/marine)\n"
            response += "• Charts: Navionics, OpenCPN, paper charts\n"
            response += "• Safety: Coast Guard VHF 16\n"
            response += "• Tides: NOAA tide predictions\n\n"
            response += "❓ What specific marine information do you need?"
        
        metadata = {"ai_provider": "smart_fallback", "location": location}
        if error:
            metadata["error"] = error
            
        return {
            "response": response,
            "context_data": metadata
        }
    
    async def _test_openai_connection(self) -> bool:
        """Test OpenAI connection with minimal request"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            print(f"OpenAI connection test failed: {e}")
            return False
    
    def _generate_fallback_response(self, user_query: str, error: str = None) -> AgentResponse:
        """Generate fallback response when AI is unavailable"""
        query_lower = user_query.lower()
        
        if any(word in query_lower for word in ['weather', 'wind', 'wave', 'storm', 'forecast']):
            content = "I'm currently unable to provide AI-powered weather analysis due to service limitations. For current marine weather information, please check NOAA Marine Weather Services at weather.gov/marine or your local maritime weather broadcasts on VHF radio."
        elif any(word in query_lower for word in ['route', 'navigation', 'course', 'path', 'optimize']):
            content = "I'm currently unable to provide AI-powered route optimization due to service limitations. For navigation assistance, please consult your marine charts, check current weather conditions from official sources, and consider using navigation apps like Navionics or ActiveCaptain."
        elif any(word in query_lower for word in ['hazard', 'danger', 'safety', 'warning', 'alert']):
            content = "I'm currently unable to provide AI-powered hazard analysis due to service limitations. For maritime safety information, please monitor official marine safety broadcasts, NAVTEX transmissions, and check the Coast Guard's Notice to Mariners."
        elif any(word in query_lower for word in ['hello', 'hi', 'help', 'what', 'how']):
            content = "Hello! I'm the Smart Ocean Navigation Assistant. I'm currently experiencing some service limitations, but I can still help guide you to the right marine resources. For weather, check NOAA Marine Weather. For navigation, use your marine charts and GPS. For safety alerts, monitor VHF radio and Coast Guard broadcasts."
        else:
            content = "I'm sorry, the AI assistant is temporarily unavailable due to service limitations. For marine weather information, visit weather.gov/marine. For navigation assistance, consult your marine charts and official maritime resources. Please try again later."
        
        metadata = {"fallback_mode": True, "service_status": "limited"}
        if error:
            metadata["error"] = error
        
        return AgentResponse(
            agent_type=AgentType.COMMUNICATION_MANAGER,
            content=content,
            confidence=0.1,
            metadata=metadata,
            timestamp=datetime.now()
        )
    
    def _generate_fallback_responses(self) -> Dict[str, AgentResponse]:
        """Generate fallback responses when AI is unavailable"""
        fallback_content = "AI analysis is currently unavailable. Please check your OpenAI API configuration."
        
        return {
            "weather": AgentResponse(AgentType.WEATHER_ANALYST, fallback_content, 0.1, {}, datetime.now()),
            "route": AgentResponse(AgentType.ROUTE_OPTIMIZER, fallback_content, 0.1, {}, datetime.now()),
            "hazards": AgentResponse(AgentType.HAZARD_DETECTOR, fallback_content, 0.1, {}, datetime.now()),
            "information": AgentResponse(AgentType.INFORMATION_RETRIEVER, fallback_content, 0.1, {}, datetime.now())
        }

# Singleton instance
multi_agent_service = MultiAgentAIService()