# backend/routers/routes.py - Maritime Route Analysis API
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import traceback

from database import get_db
from models import User
from services.route_service import RouteService
from services.enhanced_ai_chat_service import EnhancedAIChatService

# Import get_current_user from auth
from routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Initialize services
route_service = RouteService()
enhanced_ai_chat_service = EnhancedAIChatService()

# Pydantic models for request/response
class RouteAnalysisRequest(BaseModel):
    start_latitude: float
    start_longitude: float
    end_latitude: float  
    end_longitude: float
    route_name: Optional[str] = None
    vessel_type: str = "cargo"
    cruising_speed_knots: float = 15.0
    fuel_range_km: float = 5000.0
    fuel_reserve_percent: float = 20.0
    detailed_analysis: bool = True
    include_waypoints: bool = True
    weather_forecast: bool = True
    hazard_assessment: bool = True

class RouteAnalysisResponse(BaseModel):
    success: bool
    route_name: str
    distance_km: float
    distance_nautical_miles: float
    estimated_duration_hours: float
    estimated_duration_days: float
    bearing: float
    vessel_speed_knots: float
    route_analysis: Dict[str, Any]
    weather_analysis: Optional[Dict[str, Any]] = None
    waypoints: List[Dict[str, Any]]
    hazard_assessment: Dict[str, Any]
    fuel_analysis: Dict[str, Any]
    recommendations: Dict[str, Any]
    enhanced_routing: Optional[Dict[str, Any]] = None
    created_at: str

@router.post("/analyze", response_model=RouteAnalysisResponse)
async def analyze_route(
    request: RouteAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Comprehensive maritime route analysis with weather, hazards, and AI insights
    """
    try:
        logger.info(f"Route analysis requested by user {current_user.id}: {request.route_name}")
        
        # 1. Calculate basic route using RouteService
        basic_route = await route_service.calculate_route(
            start_lat=request.start_latitude,
            start_lon=request.start_longitude,
            end_lat=request.end_latitude,
            end_lon=request.end_longitude,
            vessel_speed_knots=request.cruising_speed_knots
        )
        
        # 2. Enhanced route analysis using AI Chat Service (for port-to-port routes)
        enhanced_routing = None
        try:
            # Try to get enhanced routing if we can identify ports
            route_query = f"best route from coordinates {request.start_latitude},{request.start_longitude} to {request.end_latitude},{request.end_longitude}"
            ai_response = await enhanced_ai_chat_service.process_chat_message(route_query)
            
            if ai_response and hasattr(ai_response, 'real_time_data'):
                enhanced_routing = ai_response.real_time_data.get('route_data')
        except Exception as e:
            logger.warning(f"Enhanced routing failed: {e}")
            # Continue with basic route analysis
        
        # 3. Weather analysis along the route
        weather_analysis = None
        if request.weather_forecast and basic_route.get("sample_points"):
            try:
                weather_analysis = await route_service.analyze_route_weather(
                    basic_route["sample_points"]
                )
            except Exception as e:
                logger.warning(f"Weather analysis failed: {e}")
                weather_analysis = {"error": "Weather analysis unavailable", "points": []}
        
        # 4. Hazard Assessment
        hazard_assessment = {
            "overall_risk": "MODERATE",
            "risk_factors": [],
            "recommendations": [],
            "hazard_zones": []
        }
        
        try:
            # Calculate distance-based risk factors
            distance_km = basic_route.get("distance", 0)
            if distance_km > 5000:
                hazard_assessment["risk_factors"].append("Long ocean crossing - increased weather risk")
                hazard_assessment["recommendations"].append("Ensure adequate fuel and supplies")
                
            if distance_km < 500:
                hazard_assessment["overall_risk"] = "LOW"
                hazard_assessment["recommendations"].append("Short coastal route - monitor local conditions")
            elif distance_km > 3000:
                hazard_assessment["overall_risk"] = "HIGH"
                hazard_assessment["recommendations"].append("Trans-oceanic route - comprehensive weather routing required")
                
            # Add weather-based hazards if available
            if weather_analysis and weather_analysis.get("risk_zones"):
                for zone in weather_analysis["risk_zones"]:
                    hazard_assessment["hazard_zones"].append({
                        "location": f"Distance {zone.get('start_distance', 0)}-{zone.get('end_distance', 0)}km",
                        "hazard_level": zone.get("hazard_level", 0.5),
                        "hazards": zone.get("hazards", [])
                    })
                    
        except Exception as e:
            logger.warning(f"Hazard assessment failed: {e}")
        
        # 5. Fuel Analysis
        fuel_analysis = {
            "estimated_consumption": basic_route.get("estimated_fuel_consumption", 0),
            "fuel_range_adequate": True,
            "refueling_needed": False,
            "fuel_recommendations": []
        }
        
        # Check if fuel range is adequate
        distance_km = basic_route.get("distance", 0)
        if distance_km > request.fuel_range_km:
            fuel_analysis["fuel_range_adequate"] = False
            fuel_analysis["refueling_needed"] = True
            fuel_analysis["fuel_recommendations"].append("Route exceeds vessel fuel range - plan intermediate refueling")
            
        # Add reserve fuel check
        required_fuel_with_reserve = distance_km * (1 + request.fuel_reserve_percent / 100)
        if required_fuel_with_reserve > request.fuel_range_km:
            fuel_analysis["fuel_recommendations"].append(f"Consider {request.fuel_reserve_percent}% fuel reserve for safety")
        
        # 6. General Recommendations
        recommendations = {
            "route_optimization": [],
            "safety_measures": [],
            "weather_considerations": [],
            "operational_advice": []
        }
        
        # Add route-specific recommendations
        if basic_route.get("distance", 0) > 1000:
            recommendations["route_optimization"].append("Consider weather routing for optimal fuel efficiency")
            recommendations["safety_measures"].append("Maintain 24/7 watch schedule for long voyage")
            
        if weather_analysis and weather_analysis.get("hazard_summary"):
            recommendations["weather_considerations"].append("Monitor weather conditions along route")
            
        recommendations["operational_advice"].append("File proper voyage plan with maritime authorities")
        recommendations["operational_advice"].append("Ensure all safety equipment is operational")
        
        # 7. Prepare response
        response = RouteAnalysisResponse(
            success=True,
            route_name=request.route_name or f"Route Analysis {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            distance_km=basic_route.get("distance", 0),
            distance_nautical_miles=basic_route.get("distance_nautical_miles", 0),
            estimated_duration_hours=basic_route.get("estimated_duration", 0),
            estimated_duration_days=basic_route.get("estimated_duration", 0) / 24,
            bearing=basic_route.get("bearing", 0),
            vessel_speed_knots=request.cruising_speed_knots,
            route_analysis={
                "route_type": basic_route.get("route_type", "great_circle"),
                "complexity": "simple" if basic_route.get("distance", 0) < 1000 else "complex",
                "ocean_crossing": basic_route.get("distance", 0) > 2000
            },
            weather_analysis=weather_analysis,
            waypoints=basic_route.get("waypoints", []),
            hazard_assessment=hazard_assessment,
            fuel_analysis=fuel_analysis,
            recommendations=recommendations,
            enhanced_routing=enhanced_routing,
            created_at=datetime.now().isoformat()
        )
        
        logger.info(f"Route analysis completed successfully for user {current_user.id}")
        return response
        
    except Exception as e:
        logger.error(f"Route analysis error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Route analysis failed",
                "message": str(e),
                "type": "analysis_error"
            }
        )

@router.get("/health")
async def route_service_health():
    """Check route service health"""
    return {
        "status": "healthy",
        "service": "route_analysis",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "basic_routing": True,
            "weather_analysis": True,
            "hazard_assessment": True,
            "fuel_analysis": True,
            "enhanced_ai_routing": True
        }
    }
    # jose.jwt accepts datetime for "exp"
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# -----------------------
# Dependency: get current user
# -----------------------
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security),
                     db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        # token "sub" may be string: convert to int safely
        try:
            user_id = int(sub)
        except (TypeError, ValueError):
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

# -----------------------
# Routes
# -----------------------
@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Basic sanity check - you can strengthen validation in your Pydantic schema
    if not user.password or not user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )

    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash and save
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    if not user_credentials.password or not user_credentials.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )

    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/usage/today")
async def get_today_usage(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get today's usage statistics for the current user"""
    from datetime import date
    from models import DailyUsage

    today = date.today()
    usage = (
        db.query(DailyUsage)
        .filter(DailyUsage.user_id == current_user.id, DailyUsage.date == today)
        .first()
    )

    if not usage:
        return {
            "chat_count": 0,
            "weather_count": 0,
            "route_count": 0,
            "hazard_count": 0,
            "date": today.isoformat()
        }

    return {
        "chat_count": usage.chat_count or 0,
        "weather_count": usage.weather_count or 0,
        "route_count": usage.route_count or 0,
        "hazard_count": usage.hazard_count or 0,
        "date": usage.date.isoformat()
    }

@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the current user's profile"""

    # Check if email is being changed and if it's already taken
    if user_update.email and user_update.email != current_user.email:
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email

    # Update full name if provided
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name

    # Update the updated_at timestamp
    current_user.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(current_user)
        return current_user
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
