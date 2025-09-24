"""
Hazard Alerts Router
Provides comprehensive weather and hazard alerts from multiple free APIs
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime

from services.hazard_alerts_service import hazard_alerts_service
from .auth import get_current_user
from models import User
from services.usage_service import UsageService
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()

@router.get("/alerts/comprehensive")
async def get_comprehensive_alerts(
    latitude: float = Query(..., description="Latitude (-90 to 90)"),
    longitude: float = Query(..., description="Longitude (-180 to 180)"),
    city: Optional[str] = Query(None, description="City name (optional)"),
    include_marine: bool = Query(True, description="Include marine/coastal alerts"),
    include_earthquakes: bool = Query(True, description="Include earthquake alerts"),
    radius_km: int = Query(500, description="Alert search radius in kilometers"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive weather and hazard alerts for a location using multiple free APIs.
    
    Sources:
    - US National Weather Service (api.weather.gov)
    - Open-Meteo (global weather and marine)
    - USGS Earthquake Hazards Program
    - MeteoAlarm (European alerts)
    
    Returns normalized alerts with safety suggestions.
    """
    try:
    # Validate coordinates
        if not (-90 <= latitude <= 90):
            raise HTTPException(status_code=400, detail="Latitude must be between -90 and 90")
        if not (-180 <= longitude <= 180):
            raise HTTPException(status_code=400, detail="Longitude must be between -180 and 180")
        
        # Enforce daily hazard usage
        UsageService.safe_check_and_increment(db, current_user, feature="hazard")
        # Get comprehensive alerts
        result = await hazard_alerts_service.get_comprehensive_alerts(
            latitude=latitude,
            longitude=longitude,
            city=city
        )
        
        # Filter results based on parameters
        if not include_marine:
            result['alerts'] = [alert for alert in result['alerts'] 
                              if alert.get('alert_type') != 'marine']
        
        if not include_earthquakes:
            result['alerts'] = [alert for alert in result['alerts'] 
                              if alert.get('alert_type') != 'earthquake']
        
        # Update summary after filtering
        if not include_marine or not include_earthquakes:
            from services.hazard_alerts_service import WeatherAlert, AlertSeverity, AlertType
            filtered_alerts = []
            for alert_dict in result['alerts']:
                alert = WeatherAlert(
                    event=alert_dict['event'],
                    severity=AlertSeverity(alert_dict['severity']),
                    area=alert_dict['area'],
                    description=alert_dict['description'],
                    advice=alert_dict['advice'],
                    source=alert_dict['source'],
                    alert_type=AlertType(alert_dict['alert_type'])
                )
                filtered_alerts.append(alert)
            
            result['alert_summary'] = hazard_alerts_service._create_alert_summary(filtered_alerts)
            result['safety_status'] = hazard_alerts_service._assess_safety_status(filtered_alerts)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")

@router.get("/alerts/by-city")
async def get_alerts_by_city(
    city: str = Query(..., description="City name"),
    country: Optional[str] = Query(None, description="Country code (optional)"),
    include_marine: bool = Query(True, description="Include marine alerts"),
    include_earthquakes: bool = Query(True, description="Include earthquake alerts"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get alerts for a city by name (requires geocoding lookup first).
    Note: This is a simplified version. In production, you'd use a geocoding service.
    """
    try:
        # Simple city to coordinates mapping for demo
        # In production, use a proper geocoding service like OpenCage, Nominatim, etc.
        city_coords = {
            'new york': (40.7128, -74.0060),
            'london': (51.5074, -0.1278),
            'tokyo': (35.6762, 139.6503),
            'sydney': (-33.8688, 151.2093),
            'mumbai': (19.0760, 72.8777),
            'colombo': (6.9271, 79.8612),
            'jaffna': (9.6615, 80.0255),
            'miami': (25.7617, -80.1918),
            'los angeles': (34.0522, -118.2437),
            'berlin': (52.5200, 13.4050),
            'paris': (48.8566, 2.3522),
            'rome': (41.9028, 12.4964),
            'madrid': (40.4168, -3.7038)
        }
        
        city_key = city.lower()
        if country:
            city_key = f"{city.lower()}, {country.lower()}"
        
        # Find coordinates
        coords = None
        for key, coord in city_coords.items():
            if city.lower() in key:
                coords = coord
                break
        
        if not coords:
            # Fallback for unknown cities - use a default location
            raise HTTPException(
                status_code=404, 
                detail=f"City '{city}' not found in database. Please use latitude/longitude instead."
            )
        
        latitude, longitude = coords
        
        # Enforce daily hazard usage
        UsageService.safe_check_and_increment(db, current_user, feature="hazard")
        # Get alerts using coordinates
        return await get_comprehensive_alerts(
            latitude=latitude,
            longitude=longitude,
            city=city,
            include_marine=include_marine,
            include_earthquakes=include_earthquakes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing city request: {str(e)}")

@router.get("/alerts/quick")
async def get_quick_alerts(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a quick summary of alerts for a location (faster response, less detail).
    """
    try:
        # Enforce daily hazard usage
        UsageService.safe_check_and_increment(db, current_user, feature="hazard")
        # Get basic alerts (skip slower APIs)
        result = await hazard_alerts_service.get_comprehensive_alerts(
            latitude=latitude,
            longitude=longitude
        )
        
        # Return simplified response
        return {
            "location": result["location"],
            "timestamp": result["timestamp"],
            "alert_count": len(result["alerts"]),
            "safety_status": result["safety_status"],
            "top_alerts": result["alerts"][:3],  # Only top 3 alerts
            "marine_conditions": result.get("marine_conditions"),
            "current_weather": result.get("current_weather")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching quick alerts: {str(e)}")

@router.get("/alerts/marine")
async def get_marine_alerts(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get marine-specific alerts and conditions.
    """
    try:
        # Enforce daily hazard usage
        UsageService.safe_check_and_increment(db, current_user, feature="hazard")
        result = await hazard_alerts_service.get_comprehensive_alerts(
            latitude=latitude,
            longitude=longitude
        )
        
        # Filter for marine alerts only
        marine_alerts = [alert for alert in result["alerts"] 
                        if alert.get("alert_type") == "marine"]
        
        return {
            "location": result["location"],
            "timestamp": result["timestamp"],
            "marine_conditions": result.get("marine_conditions"),
            "marine_alerts": marine_alerts,
            "marine_safety_advice": hazard_alerts_service._get_safety_advice("marine conditions", "marine"),
            "current_weather": result.get("current_weather")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching marine alerts: {str(e)}")

@router.get("/alerts/earthquake")
async def get_earthquake_alerts(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    radius_km: int = Query(500, description="Search radius in kilometers"),
    min_magnitude: float = Query(4.0, description="Minimum earthquake magnitude"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get earthquake alerts within a specified radius.
    """
    try:
        # Enforce daily hazard usage
        UsageService.check_and_increment(db, current_user, feature="hazard")
        result = await hazard_alerts_service.get_comprehensive_alerts(
            latitude=latitude,
            longitude=longitude
        )
        
        # Filter for earthquake alerts only
        earthquake_alerts = [alert for alert in result["alerts"] 
                           if alert.get("alert_type") == "earthquake"]
        
        return {
            "location": result["location"],
            "timestamp": result["timestamp"],
            "search_radius_km": radius_km,
            "min_magnitude": min_magnitude,
            "earthquake_alerts": earthquake_alerts,
            "earthquake_count": len(earthquake_alerts),
            "safety_advice": hazard_alerts_service._get_safety_advice("earthquake", "earthquake")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching earthquake alerts: {str(e)}")

@router.get("/alerts/status")
async def get_alert_status() -> Dict[str, Any]:
    """
    Get the status of alert services and available data sources.
    """
    return {
        "service_status": "operational",
        "data_sources": {
            "us_nws": {
                "name": "US National Weather Service",
                "url": "https://api.weather.gov",
                "coverage": "United States",
                "types": ["weather", "marine", "severe_weather"]
            },
            "open_meteo": {
                "name": "Open-Meteo",
                "url": "https://api.open-meteo.com",
                "coverage": "Global",
                "types": ["weather", "marine", "forecasts"]
            },
            "usgs_earthquake": {
                "name": "USGS Earthquake Hazards",
                "url": "https://earthquake.usgs.gov",
                "coverage": "Global",
                "types": ["earthquake"]
            },
            "meteoalarm": {
                "name": "MeteoAlarm",
                "url": "https://feeds.meteoalarm.org",
                "coverage": "Europe",
                "types": ["weather", "severe_weather"]
            }
        },
        "alert_types": [
            "weather", "marine", "earthquake", "flood", 
            "storm", "tsunami", "fire", "other"
        ],
        "severity_levels": [
            "minor", "moderate", "severe", "extreme"
        ],
        "last_updated": datetime.utcnow().isoformat()
    }