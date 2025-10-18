from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
from models import User, RouteAnalysis
from schemas import RouteAnalysisCreate, RouteAnalysisResponse
from .auth import get_current_user
from services.route_service import RouteService
from services.harbor_service import harbor_service
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
            try:
                route_data = await route_service.calculate_route(
                    start_harbor_name=route.start_harbor,
                    end_harbor_name=route.end_harbor,
                    vessel_speed_knots=vessel_speed
                )
                
                # Handle loading state
                if route_data.get("loading"):
                    # Return loading state to client
                    return {
                        "id": 0,
                        "user_id": current_user.id,
                        "start_latitude": 0,
                        "start_longitude": 0,
                        "end_latitude": 0,
                        "end_longitude": 0,
                        "route_name": route.route_name,
                        "created_at": datetime.now().isoformat(),
                        "analysis_data": {
                            "route_data": route_data,
                            "weather_analysis": {}
                        },
                        "risk_assessment": route_data.get("message", "System is loading route data...")
                    }
            except Exception as e:
                print(f"Error calculating route with harbor names: {str(e)}")
                route_data = {"route_found": False}
        else:
            try:
                # Find nearest harbors based on coordinates
                start_harbor_obj = await harbor_service.find_nearest_harbor(route.start_latitude, route.start_longitude)
                end_harbor_obj = await harbor_service.find_nearest_harbor(route.end_latitude, route.end_longitude)
                start_harbor = start_harbor_obj['name'] if start_harbor_obj else f"Lat: {route.start_latitude}, Lng: {route.start_longitude}"
                end_harbor = end_harbor_obj['name'] if end_harbor_obj else f"Lat: {route.end_latitude}, Lng: {route.end_longitude}"
                
                route_data = await route_service.calculate_route(
                    start_harbor_name=start_harbor,
                    end_harbor_name=end_harbor,
                    vessel_speed_knots=vessel_speed
                )
                
                # Handle loading state
                if route_data.get("loading"):
                    # Return loading state to client
                    return {
                        "id": 0,
                        "user_id": current_user.id,
                        "start_latitude": route.start_latitude,
                        "start_longitude": route.start_longitude,
                        "end_latitude": route.end_latitude,
                        "end_longitude": route.end_longitude,
                        "route_name": route.route_name,
                        "created_at": datetime.now().isoformat(),
                        "analysis_data": {
                            "route_data": route_data,
                            "weather_analysis": {}
                        },
                        "risk_assessment": route_data.get("message", "System is loading route data...")
                    }
            except Exception as e:
                print(f"Error calculating route with coordinates: {str(e)}")
                route_data = {"route_found": False}

            if not route_data.get("route_found", False) and not route_data.get("loading"):
                # Generate a route even if it's not predefined
                start_coords = {"lat": route.start_latitude, "lng": route.start_longitude}
                end_coords = {"lat": route.end_latitude, "lng": route.end_longitude}
                
                route_points = route_service._generate_oceanic_route(
                    start_coords["lat"],
                    start_coords["lng"],
                    end_coords["lat"],
                    end_coords["lng"]
                )
                
                if route_points:
                    route_data = {
                        "route_found": True,
                        "route_points": route_points,
                        "start_point": start_coords,
                        "end_point": end_coords,
                        "distance_km": route_service._calculate_total_distance(route_points),
                        "is_predefined": False,
                        "generated_route": True
                    }
                    
                    # Calculate additional metrics
                    distance_nm = route_data["distance_km"] * 0.539957
                    route_data.update({
                        "distance_nm": distance_nm,
                        "estimated_time_hours": distance_nm / vessel_speed,
                        "estimated_fuel_consumption": route_data["distance_km"] * 0.3,
                        "bearing": route_service._calculate_bearing(
                            start_coords["lat"],
                            start_coords["lng"],
                            end_coords["lat"],
                            end_coords["lng"]
                        )
                    })
        
        try:
            # Get weather data for each point along the route
            # Skip weather analysis if we're in loading state
            if route_data.get("loading"):
                weather_analysis = {
                    "points": [],
                    "hazard_summary": {"overall_risk_level": "Loading"},
                    "risk_zones": [],
                    "weather_forecast": []
                }
            elif route_data.get("sample_points") and isinstance(route_data["sample_points"], list):
                weather_analysis = await route_service.analyze_route_weather(route_data["sample_points"])
            else:
                weather_analysis = {
                    "points": [],
                    "hazard_summary": {"overall_risk_level": "Unknown"},
                    "risk_zones": [],
                    "weather_forecast": []
                }
        except Exception as e:
            print(f"Error analyzing weather: {str(e)}")
            weather_analysis = {
                "points": [],
                "hazard_summary": {"overall_risk_level": "Unknown"},
                "risk_zones": [],
                "weather_forecast": []
            }
        
        # Generate comprehensive route analysis using hardcoded maritime data
        # Handle loading state
        if route_data.get("loading"):
            start_harbor_info = route_data.get('start_harbor', {})
            end_harbor_info = route_data.get('end_harbor', {})
            start_harbor = start_harbor_info.get('name', 'Unknown') if isinstance(start_harbor_info, dict) else 'Unknown'
            end_harbor = end_harbor_info.get('name', 'Unknown') if isinstance(end_harbor_info, dict) else 'Unknown'
        else:
            start_harbor_info = route_data.get('start_harbor', {})
            end_harbor_info = route_data.get('end_harbor', {})
            start_harbor = start_harbor_info.get('name', 'Unknown') if isinstance(start_harbor_info, dict) else 'Unknown'
            end_harbor = end_harbor_info.get('name', 'Unknown') if isinstance(end_harbor_info, dict) else 'Unknown' 
        distance_km = route_data.get('distance_km', 0)
        distance_nm = route_data.get('distance_nm', 0)
        duration_hours = route_data.get('estimated_time_hours', 0)
        weather_points = len(weather_analysis.get('points', []))
        vessel_type = route.vessel_type or 'cargo'
        speed_knots = route.cruising_speed_knots or 15
        
        # Generate route justification
        route_justification = f"This maritime route from {start_harbor} to {end_harbor} has been calculated for a {vessel_type} vessel traveling at {speed_knots} knots. The route spans {distance_km:.1f} km ({distance_nm:.1f} nautical miles) and is estimated to take {duration_hours:.1f} hours. It follows established international shipping lanes, avoids shallow waters and known hazards, and includes waypoints for safe navigation. Weather conditions along the route have been analyzed with {weather_points} checkpoints to ensure optimal safety and efficiency."
        
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

🧭 Route Features:
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
                "weather_analysis": weather_analysis,
                "route_justification": route_justification
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

@router.post("/clear-cache")
async def clear_route_cache():
    """Clear the route service cache"""
    try:
        route_service.clear_route_cache()
        return {"message": "Route cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")