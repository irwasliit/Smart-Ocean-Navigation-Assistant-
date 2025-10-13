from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    plan: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Location schemas
class SavedLocationCreate(BaseModel):
    name: str
    latitude: float
    longitude: float
    location_type: str = "single"

class SavedLocationResponse(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    location_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Weather schemas
class WeatherDataResponse(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime
    temperature: Optional[float]
    humidity: Optional[float]
    wind_speed: Optional[float]
    wind_direction: Optional[float]
    wave_height: Optional[float]
    wave_period: Optional[float]
    visibility: Optional[float]
    pressure: Optional[float]
    weather_condition: Optional[str]
    hazard_probabilities: Optional[Dict[str, float]]
    
    class Config:
        from_attributes = True

class WeatherForecastResponse(BaseModel):
    location: str
    current: WeatherDataResponse
    forecast: List[WeatherDataResponse]
    hazard_summary: str  # AI-generated summary

# Route schemas
class RouteAnalysisCreate(BaseModel):
    start_latitude: float
    start_longitude: float
    end_latitude: float
    end_longitude: float
    start_harbor: Optional[str] = None  # Harbor name for start point
    end_harbor: Optional[str] = None    # Harbor name for end point
    route_name: Optional[str] = None
    # Optional vessel parameters for safety and fuel planning
    vessel_type: Optional[str] = None
    cruising_speed_knots: Optional[float] = None
    fuel_range_km: Optional[float] = None  # Max safe range on current fuel
    fuel_reserve_percent: Optional[float] = None  # Desired reserve percentage (e.g., 20)

class RouteAnalysisResponse(BaseModel):
    id: int
    start_latitude: float
    start_longitude: float
    end_latitude: float
    end_longitude: float
    route_name: Optional[str]
    analysis_data: Optional[Dict[str, Any]]
    risk_assessment: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Alert schemas
class AlertPreferenceCreate(BaseModel):
    location_id: int
    alert_types: List[str]
    threshold_values: Dict[str, float]

class AlertPreferenceResponse(BaseModel):
    id: int
    location_id: int
    alert_types: List[str]
    threshold_values: Dict[str, float]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class AlertHistoryResponse(BaseModel):
    id: int
    location_id: int
    alert_type: str
    severity: Optional[str]
    message: str
    weather_data: Optional[Dict[str, Any]]
    sent_at: datetime
    is_read: bool
    
    class Config:
        from_attributes = True

# AI Chat schemas
class ChatMessage(BaseModel):
    message: str
    context_location: Optional[str] = None  # For location-specific queries

class ChatResponse(BaseModel):
    response: str
    confidence: Optional[float] = None
    context_data: Optional[Dict[str, Any]]
    timestamp: datetime

# IR Content schemas
class IRContentResponse(BaseModel):
    id: int
    source: str
    content_type: str
    title: str
    content: str
    location_coverage: Optional[Dict[str, Any]]
    severity: Optional[str]
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True
