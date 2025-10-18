from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    plan = Column(String(20), default="free")  # free, pro, premium
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    saved_locations = relationship("SavedLocation", back_populates="user")
    alert_preferences = relationship("AlertPreference", back_populates="user")
    chat_history = relationship("ChatHistory", back_populates="user")

class SavedLocation(Base):
    __tablename__ = "saved_locations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    location_type = Column(String(50), default="single")  # single, route_start, route_end
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="saved_locations")

class AlertPreference(Base):
    __tablename__ = "alert_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("saved_locations.id"), nullable=False)
    alert_types = Column(JSON)  # ["storm", "fog", "tsunami", "high_wind"]
    threshold_values = Column(JSON)  # {"wind_speed": 50, "wave_height": 3.0}
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="alert_preferences")

class WeatherData(Base):
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    temperature = Column(Float)
    humidity = Column(Float)
    wind_speed = Column(Float, index=True)
    wind_direction = Column(Float)
    wave_height = Column(Float, index=True)
    wave_period = Column(Float)
    visibility = Column(Float)
    pressure = Column(Float)
    weather_condition = Column(String(100), index=True)
    hazard_probabilities = Column(JSON)  # {"storm": 0.3, "fog": 0.1, "tsunami": 0.0}
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

class RouteAnalysis(Base):
    __tablename__ = "route_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_latitude = Column(Float, nullable=False)
    start_longitude = Column(Float, nullable=False)
    end_latitude = Column(Float, nullable=False)
    end_longitude = Column(Float, nullable=False)
    route_name = Column(String(255))
    analysis_data = Column(JSON)  # Route weather analysis results
    risk_assessment = Column(Text)  # AI-generated risk summary
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AlertHistory(Base):
    __tablename__ = "alert_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("saved_locations.id"), nullable=False, index=True)
    alert_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), index=True)  # low, medium, high, critical
    message = Column(Text, nullable=False)
    weather_data = Column(JSON)  # Weather conditions that triggered the alert
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    is_read = Column(Boolean, default=False, index=True)

class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    context_data = Column(JSON)  # Weather data used for response
    model_used = Column(String(20), default='advanced')  # 'basic' or 'advanced' - track which model was used
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_history")

class IRContent(Base):
    __tablename__ = "ir_content"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(255), nullable=False)  # NOAA, NWS, etc.
    content_type = Column(String(100))  # bulletin, warning, forecast
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    location_coverage = Column(JSON)  # Geographic areas covered
    severity = Column(String(50))
    valid_from = Column(DateTime(timezone=True))
    valid_until = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
