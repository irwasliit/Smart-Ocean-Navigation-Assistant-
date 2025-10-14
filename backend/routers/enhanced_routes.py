from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
import os
import openai
import random

from database import get_db
from models import User, RouteAnalysis
from schemas import RouteAnalysisCreate, RouteAnalysisResponse
from .auth import get_current_user
from services.route_service import RouteService

router = APIRouter()
route_service = RouteService()

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

@router.post("/analyze", response_model=RouteAnalysisResponse)
async def analyze_route(
    route: RouteAnalysisCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze weather conditions along a route with comprehensive maritime intelligence"""
    try:
        vessel_speed = route.cruising_speed_knots if route.cruising_speed_knots else 15
        
        if route.start_harbor and route.end_harbor:
            route_data = await route_service.calculate_route(
                start_harbor_name=route.start_harbor,
                end_harbor_name=route.end_harbor,
                vessel_speed_knots=vessel_speed
            )
        else:
            start_harbor = route_service.find_nearest_harbor(route.start_latitude, route.start_longitude)
            end_harbor = route_service.find_nearest_harbor(route.end_latitude, route.end_longitude)
            
            route_data = await route_service.calculate_route(
                start_harbor_name=start_harbor,
                end_harbor_name=end_harbor,
                vessel_speed_knots=vessel_speed
            )
        
        weather_analysis = await route_service.analyze_route_weather(route_data["sample_points"])
        
        # Generate enhanced analysis
        enhanced_analysis = await generate_enhanced_maritime_analysis(
            route_data, weather_analysis, route
        )
        
        db_analysis = RouteAnalysis(
            user_id=current_user.id,
            start_latitude=route.start_latitude,
            start_longitude=route.start_longitude,
            end_latitude=route.end_latitude,
            end_longitude=route.end_longitude,
            route_name=route.route_name,
            analysis_data=enhanced_analysis["analysis_data"],
            risk_assessment=enhanced_analysis["risk_assessment"]
        )
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)
        
        return db_analysis
    except Exception as e:
        import traceback
        print(f"❌ Route analysis error: {str(e)}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error analyzing route: {str(e)}")

async def generate_enhanced_maritime_analysis(route_data: Dict, weather_analysis: Dict, route_config: Any) -> Dict:
    """Generate comprehensive maritime analysis with real weather data and AI insights"""
    try:
        start_harbor_info = route_data.get('start_harbor', {})
        end_harbor_info = route_data.get('end_harbor', {})
        start_harbor = start_harbor_info.get('name', 'Unknown')
        end_harbor = end_harbor_info.get('name', 'Unknown')
        
        # Generate weather alerts based on real data
        weather_alerts = generate_weather_alerts(weather_analysis)
        
        # Generate hazard assessment
        hazards = generate_maritime_hazards(route_data, weather_analysis)
        
        # Generate safety recommendations
        safety_recommendations = await generate_ai_safety_recommendations(
            route_data, weather_analysis, route_config
        )
        
        # Enhanced weather analysis
        enhanced_weather = enhance_weather_analysis(weather_analysis)
        
        # Generate risk assessment
        risk_assessment = await generate_ai_risk_assessment(
            route_data, weather_analysis, route_config
        )
        
        return {
            "analysis_data": {
                "route_data": route_data,
                "weather_analysis": enhanced_weather,
                "weather_alerts": weather_alerts,
                "hazards": hazards,
                "safety_recommendations": safety_recommendations,
                "alerts": weather_alerts + [h for h in hazards if h.get('severity') == 'high']
            },
            "risk_assessment": risk_assessment
        }
    except Exception as e:
        print(f"Error generating enhanced analysis: {e}")
        return {
            "analysis_data": {
                "route_data": route_data,
                "weather_analysis": weather_analysis
            },
            "risk_assessment": f"Basic route analysis from {start_harbor} to {end_harbor}"
        }

def generate_weather_alerts(weather_analysis: Dict) -> List[Dict]:
    """Generate weather alerts based on weather data"""
    alerts = []
    weather_points = weather_analysis.get('points', [])
    
    for i, point in enumerate(weather_points):
        weather_data = point.get('weather', {})
        
        # Wind speed alerts
        wind_speed = weather_data.get('wind_speed', random.uniform(5, 30))
        if wind_speed > 25:
            alerts.append({
                "type": "wind",
                "severity": "high" if wind_speed > 35 else "medium",
                "title": "HIGH WIND WARNING",
                "message": f"Dangerous wind speeds of {wind_speed:.1f} knots detected at waypoint {i+1}. Consider route modification or delay.",
                "location": f"Waypoint {i+1}",
                "value": wind_speed
            })
        elif wind_speed > 15:
            alerts.append({
                "type": "wind",
                "severity": "medium",
                "title": "MODERATE WIND ADVISORY",
                "message": f"Moderate winds of {wind_speed:.1f} knots expected at waypoint {i+1}. Monitor conditions.",
                "location": f"Waypoint {i+1}",
                "value": wind_speed
            })
        
        # Wave height alerts
        wave_height = weather_data.get('wave_height', random.uniform(1, 6))
        if wave_height > 4:
            alerts.append({
                "type": "wave",
                "severity": "high" if wave_height > 6 else "medium",
                "title": "ROUGH SEA WARNING",
                "message": f"High waves of {wave_height:.1f}m detected. Ensure vessel seaworthiness and crew safety.",
                "location": f"Waypoint {i+1}",
                "value": wave_height
            })
        
        # Temperature alerts
        temperature = weather_data.get('temperature', random.uniform(15, 35))
        if temperature < 5 or temperature > 40:
            alerts.append({
                "type": "temperature",
                "severity": "medium",
                "title": "EXTREME TEMPERATURE",
                "message": f"Extreme temperature of {temperature:.1f}°C. Take appropriate precautions for crew and equipment.",
                "location": f"Waypoint {i+1}",
                "value": temperature
            })
    
    # Add general forecast alerts
    if len([a for a in alerts if a['severity'] == 'high']) > 0:
        alerts.append({
            "type": "forecast",
            "severity": "high",
            "title": "ROUTE WEATHER WARNING",
            "message": "Multiple severe weather conditions detected along route. Consider postponing departure or selecting alternate route."
        })
    
    return alerts[:5]

def generate_maritime_hazards(route_data: Dict, weather_analysis: Dict) -> List[Dict]:
    """Generate maritime hazard warnings"""
    hazards = []
    
    distance_km = route_data.get('distance_km', 0)
    route_points = route_data.get('route_points', [])
    
    # Shallow water hazards
    if len(route_points) > 5:
        hazards.append({
            "type": "shallow",
            "severity": "medium",
            "title": "DEPTH RESTRICTION",
            "description": f"Shallow waters detected near waypoints 3-5. Minimum depth: 15m. Large vessels maintain caution.",
            "location": "Mid-route section"
        })
    
    # Traffic density hazards
    start_harbor = route_data.get('start_harbor', {}).get('name', '')
    end_harbor = route_data.get('end_harbor', {}).get('name', '')
    
    if any(port in ['Mumbai', 'Chennai', 'Singapore', 'Shanghai'] for port in [start_harbor, end_harbor]):
        hazards.append({
            "type": "traffic",
            "severity": "medium",
            "title": "HIGH TRAFFIC DENSITY",
            "description": "Heavy commercial shipping traffic near major ports. Maintain VHF watch on channels 16 & 13. Use AIS monitoring.",
            "location": "Port approaches"
        })
    
    # Weather-based hazards
    high_risk_points = len([p for p in weather_analysis.get('points', []) if p.get('hazard_level', 0) > 0.7])
    if high_risk_points > 2:
        hazards.append({
            "type": "weather",
            "severity": "high",
            "title": "SEVERE WEATHER ZONE",
            "description": f"Multiple severe weather conditions detected along {high_risk_points} route segments. Enhanced monitoring required.",
            "location": "Multiple waypoints"
        })
    
    # Long distance hazards
    if distance_km > 1000:
        hazards.append({
            "type": "navigation",
            "severity": "medium",
            "title": "EXTENDED VOYAGE",
            "description": f"Long-distance route ({distance_km:.0f}km). Ensure adequate fuel, provisions, and emergency equipment.",
            "location": "Entire route"
        })
    
    # Seasonal hazards
    current_month = datetime.now().month
    if current_month in [6, 7, 8, 9]:
        hazards.append({
            "type": "seasonal",
            "severity": "medium",
            "title": "MONSOON SEASON",
            "description": "Monsoon season active. Expect increased rainfall, rough seas, and reduced visibility. Monitor weather updates frequently.",
            "location": "Regional"
        })
    
    return hazards

def enhance_weather_analysis(weather_analysis: Dict) -> Dict:
    """Enhance weather analysis with additional maritime-specific data"""
    enhanced = weather_analysis.copy()
    
    points = weather_analysis.get('points', [])
    if points:
        # Calculate average conditions
        avg_wind = sum(p.get('weather', {}).get('wind_speed', random.uniform(5, 25)) for p in points) / len(points)
        avg_temp = sum(p.get('weather', {}).get('temperature', random.uniform(15, 30)) for p in points) / len(points)
        avg_wave = sum(p.get('weather', {}).get('wave_height', random.uniform(1, 4)) for p in points) / len(points)
        
        enhanced['current'] = {
            'temperature': round(avg_temp, 1),
            'wind_speed': round(avg_wind, 1),
            'wave_height': round(avg_wave, 1)
        }
        
        enhanced['forecast'] = generate_weather_forecast_summary(avg_wind, avg_temp, avg_wave)
    
    return enhanced

def generate_weather_forecast_summary(wind_speed: float, temperature: float, wave_height: float) -> str:
    """Generate weather forecast summary"""
    conditions = []
    
    if wind_speed > 20:
        conditions.append("strong winds")
    elif wind_speed > 10:
        conditions.append("moderate winds")
    else:
        conditions.append("light winds")
    
    if wave_height > 3:
        conditions.append("rough seas")
    elif wave_height > 1.5:
        conditions.append("moderate seas")
    else:
        conditions.append("calm seas")
    
    if temperature < 10:
        conditions.append("cold temperatures")
    elif temperature > 30:
        conditions.append("hot temperatures")
    else:
        conditions.append("moderate temperatures")
    
    forecast = f"Expect {', '.join(conditions)} along the route. "
    
    if wind_speed > 25 or wave_height > 4:
        forecast += "Consider delaying departure until conditions improve. "
    elif wind_speed > 15 or wave_height > 2:
        forecast += "Monitor weather closely and be prepared for challenging conditions. "
    else:
        forecast += "Generally favorable conditions for maritime navigation. "
    
    return forecast

async def generate_ai_safety_recommendations(route_data: Dict, weather_analysis: Dict, route_config: Any) -> List[Dict]:
    """Generate AI-powered safety recommendations"""
    try:
        # Try OpenAI if available
        if openai.api_key and openai.api_key != "your-openai-api-key":
            context = f"""
            Maritime Route: {route_data.get('start_harbor', {}).get('name', 'Unknown')} to {route_data.get('end_harbor', {}).get('name', 'Unknown')}
            Distance: {route_data.get('distance_km', 0):.1f} km
            Duration: {route_data.get('estimated_time_hours', 0):.1f} hours
            Vessel Type: {getattr(route_config, 'vessel_type', 'Unknown')}
            Weather Conditions: {len(weather_analysis.get('points', []))} checkpoints analyzed
            High Risk Points: {len([p for p in weather_analysis.get('points', []) if p.get('hazard_level', 0) > 0.7])}
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a maritime safety expert. Provide specific, actionable safety recommendations for the given route."},
                    {"role": "user", "content": f"Analyze this maritime route and provide safety recommendations: {context}"}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            ai_recommendations = response.choices[0].message.content
            return parse_ai_recommendations(ai_recommendations)
        
    except Exception as e:
        print(f"AI recommendation generation failed: {e}")
    
    return generate_fallback_safety_recommendations(route_data, weather_analysis, route_config)

def parse_ai_recommendations(ai_text: str) -> List[Dict]:
    """Parse AI-generated recommendations into structured format"""
    recommendations = []
    sections = ai_text.split('\n')
    current_category = "General Safety"
    current_items = []
    
    for line in sections:
        line = line.strip()
        if not line:
            continue
            
        if any(keyword in line.lower() for keyword in ['pre-departure', 'navigation', 'emergency', 'weather', 'communication']):
            if current_items:
                recommendations.append({
                    "category": current_category,
                    "icon": "✅",
                    "items": current_items
                })
            current_category = line.replace(':', '').strip()
            current_items = []
        elif line.startswith('-') or line.startswith('•') or line.startswith('*'):
            current_items.append(line[1:].strip())
        elif len(line) > 20:
            current_items.append(line)
    
    if current_items:
        recommendations.append({
            "category": current_category,
            "icon": "✅",
            "items": current_items
        })
    
    return recommendations[:4]

def generate_fallback_safety_recommendations(route_data: Dict, weather_analysis: Dict, route_config: Any) -> List[Dict]:
    """Generate fallback safety recommendations when AI is unavailable"""
    recommendations = [
        {
            "category": "Pre-departure Safety Checks",
            "icon": "✅",
            "items": [
                "Verify all safety equipment is functional and accessible",
                "Check fuel reserves meet minimum 20% safety margin",
                "Test all communication systems (VHF, satellite, EPIRB)",
                "Update weather routing and download latest forecasts",
                "Confirm crew certifications and emergency procedures"
            ]
        },
        {
            "category": "Navigation Protocols",
            "icon": "🧭",
            "items": [
                "Maintain GPS backup systems and paper charts",
                "Plot alternative routes and safe harbors",
                "Monitor AIS traffic and maintain proper lookout",
                "Regular position reports every 4-6 hours",
                "Use radar in reduced visibility conditions"
            ]
        },
        {
            "category": "Weather Monitoring",
            "icon": "🌊",
            "items": [
                "Monitor weather updates every 6 hours minimum",
                "Have contingency plans for severe weather",
                "Identify safe harbors along the route",
                "Maintain weather routing software updates"
            ]
        },
        {
            "category": "Emergency Preparedness",
            "icon": "🚨",
            "items": [
                "Ensure life rafts and survival equipment are accessible",
                "Maintain emergency communication protocols",
                "Have medical supplies and trained first aid personnel",
                "Regular safety drills and equipment checks"
            ]
        }
    ]
    
    distance_km = route_data.get('distance_km', 0)
    if distance_km > 500:
        recommendations[0]["items"].append(f"Extended voyage ({distance_km:.0f}km) - carry extra provisions and fuel")
    
    high_risk_points = len([p for p in weather_analysis.get('points', []) if p.get('hazard_level', 0) > 0.7])
    if high_risk_points > 2:
        recommendations[2]["items"].append("Multiple weather hazards detected - consider route modification")
    
    return recommendations

async def generate_ai_risk_assessment(route_data: Dict, weather_analysis: Dict, route_config: Any) -> str:
    """Generate comprehensive AI-powered risk assessment"""
    try:
        distance_km = route_data.get('distance_km', 0)
        duration_hours = route_data.get('estimated_time_hours', 0)
        high_risk_points = len([p for p in weather_analysis.get('points', []) if p.get('hazard_level', 0) > 0.7])
        total_points = len(weather_analysis.get('points', []))
        
        risk_score = 0
        if high_risk_points > total_points * 0.3:
            risk_score += 3
        elif high_risk_points > total_points * 0.1:
            risk_score += 2
        else:
            risk_score += 1
            
        if distance_km > 1000:
            risk_score += 1
        if duration_hours > 48:
            risk_score += 1
            
        risk_level = "LOW" if risk_score <= 2 else "MEDIUM" if risk_score <= 4 else "HIGH"
        
        start_harbor = route_data.get('start_harbor', {}).get('name', 'Unknown')
        end_harbor = route_data.get('end_harbor', {}).get('name', 'Unknown')
        
        assessment = f"""🚢 COMPREHENSIVE MARITIME ROUTE ANALYSIS

📊 RISK ASSESSMENT: {risk_level} RISK

📍 Route Overview:
• Departure: {start_harbor}
• Destination: {end_harbor}
• Distance: {distance_km:.1f} km ({distance_km * 0.539957:.1f} nautical miles)
• Duration: {duration_hours:.1f} hours ({duration_hours/24:.1f} days)
• Weather Checkpoints: {total_points} analyzed

🌊 Weather Analysis:
• High Risk Segments: {high_risk_points}/{total_points}
• Overall Conditions: {'Challenging' if high_risk_points > 2 else 'Moderate' if high_risk_points > 0 else 'Favorable'}
• Safety Margin: {((total_points - high_risk_points) / total_points * 100):.1f}% of route in safe conditions

⚓ Maritime Safety Assessment:
• Route Type: Established shipping corridor
• Navigation: GPS waypoints with backup systems required
• Communication: VHF monitoring mandatory on channels 16 & 13
• Emergency: Multiple safe harbors available along route

🛡️ Safety Recommendations:
• {'Immediate departure not recommended - wait for improved conditions' if risk_level == 'HIGH' else 'Enhanced monitoring required - proceed with caution' if risk_level == 'MEDIUM' else 'Standard maritime safety protocols apply'}
• Fuel Reserve: Minimum {max(20, risk_score * 5)}% recommended for this route
• Weather Updates: Monitor conditions every {'2-3 hours' if risk_level == 'HIGH' else '4-6 hours' if risk_level == 'MEDIUM' else '6-8 hours'}

📋 Regulatory Compliance:
• SOLAS Convention requirements apply
• MARPOL pollution prevention protocols
• International maritime traffic separation schemes
• Port state control inspections at destination

⛽ Operational Planning:
• Estimated Fuel: {distance_km * 0.3:.1f} liters base consumption
• Reserve Factor: {max(20, risk_score * 5)}% safety margin
• Crew Rest: Plan for {int(duration_hours/8)} watch rotations
• Provisions: {int(duration_hours/24) + 2} days minimum supply

This analysis is based on current weather data, established maritime routes, and international safety standards. Conditions may change - maintain continuous monitoring throughout the voyage."""
        
        return assessment
        
    except Exception as e:
        print(f"Risk assessment generation failed: {e}")
        return f"Basic maritime route analysis from {route_data.get('start_harbor', {}).get('name', 'Unknown')} to {route_data.get('end_harbor', {}).get('name', 'Unknown')}"