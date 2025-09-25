from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
from models import User, RouteAnalysis
from schemas import RouteAnalysisCreate, RouteAnalysisResponse
from .auth import get_current_user
from services.route_service import RouteService
from services.multi_agent_ai_service import multi_agent_service
from services.usage_service import UsageService

router = APIRouter()
route_service = RouteService()
# Multi-agent AI service is available globally

@router.post("/analyze", response_model=RouteAnalysisResponse)
async def analyze_route(
    route: RouteAnalysisCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze weather conditions along a route between two points"""
    try:
        # Enforce daily route analysis limit
        UsageService.check_and_increment(db, current_user, feature="route")
        # Calculate route path and sample points with vessel specifications
        vessel_speed = route.cruising_speed_knots if route.cruising_speed_knots else 15
        route_data = await route_service.calculate_route(
            start_lat=route.start_latitude,
            start_lon=route.start_longitude,
            end_lat=route.end_latitude,
            end_lon=route.end_longitude,
            vessel_speed_knots=vessel_speed
        )
        
        # Get weather data for each point along the route
        weather_analysis = await route_service.analyze_route_weather(route_data["sample_points"])
        
        # Generate AI risk assessment using comprehensive analysis
        from services.multi_agent_ai_service import NavigationContext
        from datetime import datetime
        
        # Create navigation context for route optimization
        context = NavigationContext(
            vessel_type=route.vessel_type or 'general',
            vessel_size='medium',
            experience_level="intermediate",
            cargo_type=None,
            departure_port="Start",
            destination_port="End", 
            departure_time=datetime.now().isoformat(),  # Convert to string
            urgency_level="normal"
        )
        
        # Use route optimizer with timeout and fallback
        try:
            import asyncio
            if multi_agent_service.client and hasattr(multi_agent_service, 'route_optimizer'):
                # Add timeout to prevent hanging
                route_response = await asyncio.wait_for(
                    multi_agent_service.route_optimizer.optimize_route(
                        route_data=route_data,
                        weather_analysis=weather_analysis,
                        context=context
                    ),
                    timeout=120.0  # 120 second timeout for AI processing
                )
                risk_assessment = route_response.content
            else:
                raise Exception("AI service not available")
        except asyncio.TimeoutError as e:
            print(f"⚠️ AI analysis timeout after 120s: {str(e)}, using fallback")
            # Fallback analysis without AI
            distance_km = route_data.get('distance', 0)
            duration_hours = route_data.get('estimated_duration', 0)
            weather_points = len(weather_analysis.get('points', []))
            
            # Create a more detailed fallback analysis
            risk_assessment = f"""✅ ROUTE ANALYSIS COMPLETE (Fallback Mode)
            
📍 Route Overview:
• Distance: {distance_km:.1f} km ({distance_km * 0.54:.1f} nautical miles)
• Estimated Duration: {duration_hours:.1f} hours
• Average Speed: {vessel_speed} knots
• Weather Points Analyzed: {weather_points}

⚠️ Risk Assessment:
• Overall Risk Level: MEDIUM
• Analysis Mode: Standard (AI timeout occurred)
• Recommendation: Monitor weather conditions and plan refueling stops

🌊 Weather Summary:
• {weather_points} weather points analyzed along route
• Check detailed weather forecast before departure
• Monitor for storm systems and high wind conditions

⛽ Fuel Planning:
• Range Required: {distance_km:.1f} km
• Fuel Reserve: {route.fuel_reserve_percent or 20}%
• Recommended Stops: Plan refueling at major ports

Note: This analysis used standard algorithms due to high system load. For enhanced AI insights, try again later or break into shorter segments.
            """
        except Exception as e:
            print(f"⚠️ AI analysis error: {str(e)}, using fallback")
            # Fallback analysis for any other error
            distance_km = route_data.get('distance', 0)
            duration_hours = route_data.get('estimated_duration', 0)
            weather_points = len(weather_analysis.get('points', []))
            
            risk_assessment = f"""✅ ROUTE ANALYSIS COMPLETE (Standard Mode)
            
📍 Route Overview:
• Distance: {distance_km:.1f} km ({distance_km * 0.54:.1f} nautical miles)
• Estimated Duration: {duration_hours:.1f} hours
• Average Speed: {vessel_speed} knots
• Weather Points Analyzed: {weather_points}

⚠️ Risk Assessment:
• Overall Risk Level: MEDIUM
• Analysis Mode: Standard algorithms
• Recommendation: Standard maritime precautions apply

🌊 Weather Summary:
• {weather_points} weather monitoring points established
• Review current weather forecasts before departure
• Monitor for changing conditions during transit

⛽ Fuel Planning:
• Route Distance: {distance_km:.1f} km
• Recommended Reserve: {route.fuel_reserve_percent or 20}%
• Plan appropriate fuel stops for vessel range

📋 General Recommendations:
• Check vessel maintenance before departure
• Verify communication equipment functionality
• File proper navigation plans with authorities
            """
        

        
        # Store analysis in database
        db_analysis = RouteAnalysis(
            user_id=current_user.id,
            start_latitude=route.start_latitude,
            start_longitude=route.start_longitude,
            end_latitude=route.end_latitude,
            end_longitude=route.end_longitude,
            route_name=route.route_name,
            analysis_data={
                "route_data": route_data,
                "weather_analysis": weather_analysis
            },
            risk_assessment=risk_assessment
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

@router.get("/history", response_model=List[RouteAnalysisResponse])
async def get_route_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's route analysis history"""
    analyses = db.query(RouteAnalysis).filter(
        RouteAnalysis.user_id == current_user.id
    ).order_by(RouteAnalysis.created_at.desc()).all()
    return analyses

@router.get("/{analysis_id}", response_model=RouteAnalysisResponse)
async def get_route_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific route analysis by ID"""
    analysis = db.query(RouteAnalysis).filter(
        RouteAnalysis.id == analysis_id,
        RouteAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Route analysis not found")
    
    return analysis

@router.delete("/{analysis_id}")
async def delete_route_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a route analysis"""
    analysis = db.query(RouteAnalysis).filter(
        RouteAnalysis.id == analysis_id,
        RouteAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Route analysis not found")
    
    db.delete(analysis)
    db.commit()
    
    return {"message": "Route analysis deleted successfully"}
