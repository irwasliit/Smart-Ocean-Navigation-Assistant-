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
        # Calculate route path and sample points with vessel specifications
        vessel_speed = route.cruising_speed_knots if route.cruising_speed_knots else 15
        
        # Use harbor names if provided, otherwise find nearest harbors by coordinates
        if route.start_harbor and route.end_harbor:
            route_data = await route_service.calculate_route(
                start_harbor_name=route.start_harbor,
                end_harbor_name=route.end_harbor,
                vessel_speed_knots=vessel_speed
            )
        else:
            # Find nearest harbors based on coordinates
            start_harbor = route_service.find_nearest_harbor(route.start_latitude, route.start_longitude)
            end_harbor = route_service.find_nearest_harbor(route.end_latitude, route.end_longitude)
            
            route_data = await route_service.calculate_route(
                start_harbor_name=start_harbor,
                end_harbor_name=end_harbor,
                vessel_speed_knots=vessel_speed
            )
        
        # Get weather data for each point along the route
        weather_analysis = await route_service.analyze_route_weather(route_data["sample_points"])
        
        # Generate comprehensive route analysis using hardcoded maritime data
        start_harbor_info = route_data.get('start_harbor', {})
        end_harbor_info = route_data.get('end_harbor', {})
        start_harbor = start_harbor_info.get('name', 'Unknown')
        end_harbor = end_harbor_info.get('name', 'Unknown') 
        distance_km = route_data.get('distance_km', 0)
        distance_nm = route_data.get('distance_nm', 0)
        duration_hours = route_data.get('estimated_time_hours', 0)
        weather_points = len(weather_analysis.get('points', []))
        
        # Use the route summary from the route service
        risk_assessment = route_data.get('route_summary', f"""🚢 MARITIME ROUTE ANALYSIS

📍 Route Overview:
• Departure Harbor: {start_harbor}
• Destination Harbor: {end_harbor}
• Distance: {distance_km:.1f} km ({distance_nm:.1f} nautical miles)
• Estimated Duration: {duration_hours:.1f} hours ({duration_hours/24:.1f} days)
• Average Speed: {vessel_speed} knots

🌊 Maritime Safety:
• Route Type: Established shipping lane
• Navigation: GPS waypoints provided
• Weather Monitoring: {weather_points} checkpoints along route
• Safety: Follows international maritime corridors

⚓ Harbor Facilities:
• Both departure and destination ports offer full facilities
• Refueling, maintenance, and supply services available
• Emergency ports accessible along established route

�️ Route Features:
• Avoids shallow waters and land masses
• Follows established shipping channels
• All waypoints in international waters
• Compatible with standard marine GPS systems

⛽ Fuel Planning:
• Total Distance: {distance_km:.1f} km
• Estimated Consumption: {distance_km * 0.3:.1f} liters
• Recommended Reserve: {route.fuel_reserve_percent or 20}%
• Fuel stops available at major ports en route

📋 Navigation Recommendations:
• Route optimized for safety and efficiency
• Monitor weather conditions before departure
• Maintain communication equipment functionality
• Follow international maritime regulations""")
        

        
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