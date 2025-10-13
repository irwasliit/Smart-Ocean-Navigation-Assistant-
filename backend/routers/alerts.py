from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
from models import User, AlertPreference, AlertHistory, SavedLocation
from schemas import AlertPreferenceCreate, AlertPreferenceResponse, AlertHistoryResponse
from .auth import get_current_user
from services.alert_service import AlertService

router = APIRouter()
alert_service = AlertService() 

@router.post("/preferences", response_model=AlertPreferenceResponse)
async def create_alert_preference(
    preference: AlertPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create alert preferences for a location"""
    # Verify location belongs to user
    location = db.query(SavedLocation).filter(
        SavedLocation.id == preference.location_id,
        SavedLocation.user_id == current_user.id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    # Create alert preference
    db_preference = AlertPreference(
        user_id=current_user.id,
        location_id=preference.location_id,
        alert_types=preference.alert_types,
        threshold_values=preference.threshold_values
    )
    db.add(db_preference)
    db.commit()
    db.refresh(db_preference)
    
    return db_preference

@router.get("/preferences", response_model=List[AlertPreferenceResponse])
async def get_alert_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's alert preferences"""
    preferences = db.query(AlertPreference).filter(
        AlertPreference.user_id == current_user.id
    ).all()
    return preferences

@router.put("/preferences/{preference_id}", response_model=AlertPreferenceResponse)
async def update_alert_preference(
    preference_id: int,
    preference: AlertPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update alert preferences"""
    db_preference = db.query(AlertPreference).filter(
        AlertPreference.id == preference_id,
        AlertPreference.user_id == current_user.id
    ).first()
    
    if not db_preference:
        raise HTTPException(status_code=404, detail="Alert preference not found")
    
    # Update preference
    db_preference.alert_types = preference.alert_types
    db_preference.threshold_values = preference.threshold_values
    db.commit()
    db.refresh(db_preference)
    
    return db_preference

@router.delete("/preferences/{preference_id}")
async def delete_alert_preference(
    preference_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete alert preference"""
    db_preference = db.query(AlertPreference).filter(
        AlertPreference.id == preference_id,
        AlertPreference.user_id == current_user.id
    ).first()
    
    if not db_preference:
        raise HTTPException(status_code=404, detail="Alert preference not found")
    
    db.delete(db_preference)
    db.commit()
    
    return {"message": "Alert preference deleted successfully"}

@router.get("/active", response_model=List[AlertHistoryResponse])
async def get_active_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's active (unread) alerts"""
    alerts = db.query(AlertHistory).filter(
        AlertHistory.user_id == current_user.id,
        AlertHistory.is_read == False
    ).order_by(AlertHistory.sent_at.desc()).all()
    return alerts

@router.get("/history", response_model=List[AlertHistoryResponse])
async def get_alert_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's alert history"""
    alerts = db.query(AlertHistory).filter(
        AlertHistory.user_id == current_user.id
    ).order_by(AlertHistory.sent_at.desc()).all()
    return alerts

@router.put("/history/{alert_id}/read")
async def mark_alert_as_read(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark an alert as read"""
    alert = db.query(AlertHistory).filter(
        AlertHistory.id == alert_id,
        AlertHistory.user_id == current_user.id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_read = True
    db.commit()
    
    return {"message": "Alert marked as read"}

@router.post("/test/{location_id}")
async def test_alert(
    location_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test alert system for a location"""
    # Get location
    location = db.query(SavedLocation).filter(
        SavedLocation.id == location_id,
        SavedLocation.user_id == current_user.id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Get alert preferences
    preferences = db.query(AlertPreference).filter(
        AlertPreference.location_id == location_id,
        AlertPreference.user_id == current_user.id
    ).all()
    
    if not preferences:
        raise HTTPException(status_code=404, detail="No alert preferences found for this location")
    
    # Test alert
    result = await alert_service.test_alert(location, preferences[0], current_user.email)
    
    return {"message": "Test alert sent", "result": result}

@router.post("/test-email")
async def test_email_notification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test email notification functionality"""
    try:
        from services.notification_scheduler import scheduler
        
        # Get user's first saved location or use default
        location = db.query(SavedLocation).filter(
            SavedLocation.user_id == current_user.id
        ).first()
          
        location_name = location.name if location else "Test Location"
        
        # Send test notification
        success = await scheduler.test_notification(
            email=current_user.email,
            location_name=location_name
        )
        
        if success:
            return {
                "success": True,
                "message": f"Test email sent successfully to {current_user.email}",
                "location": location_name
            }
        else:
            return {
                "success": False,
                "message": "Failed to send test email. Please check email configuration.",
                "location": location_name
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error sending test email: {str(e)}"
        )
