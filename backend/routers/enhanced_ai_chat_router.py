"""
Enhanced AI Chat Router
Dedicated router for AI Chat page using the enhanced chat service
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from database import get_db
from .auth import get_current_user
from models import User, ChatHistory
from schemas import ChatMessage, ChatResponse
from services.enhanced_ai_chat_service import enhanced_ai_chat_service, process_chat_message


# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/enhanced-chat", response_model=ChatResponse)
async def enhanced_chat_with_ai(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enhanced AI chat with real-time data integration and Google Custom Search"""
    try:
        # Enforce daily chat limit
        
        # Prepare context data
        context_data = {}
        if hasattr(message, 'context_location') and message.context_location:
            context_data["location"] = message.context_location
        
        # Add user context
        context_data["user_id"] = current_user.id
        context_data["user_plan"] = current_user.plan
        
        # Process message with enhanced service
        response_data = await process_chat_message(
            message=message.message,
            context_data=context_data
        )
        
        # Store chat history
        db_chat = ChatHistory(
            user_id=current_user.id,
            message=message.message,
            response=response_data["response"],
            context_data=response_data.get("real_time_data", {})
        )
        db.add(db_chat)
        db.commit()
        
        return ChatResponse(
            response=response_data["response"],
            confidence=response_data.get("confidence", 0.8),
            context_data=response_data.get("real_time_data", {}),
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.post("/chat-with-location")
async def chat_with_location_context(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat with location context for weather and marine data"""
    try:
        # Enforce daily chat limit
        
        message = request.get("message", "")
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Extract location and context data
        context_data = {
            "location": request.get("location"),
            "current_location": request.get("current_location"),
            "weather_data": request.get("weather_data"),
            "user_id": current_user.id,
            "user_plan": current_user.plan
        }
        
        # Get the model used (basic or advanced)
        model_used = request.get("model_used", "advanced")
        
        # Process with enhanced service
        response_data = await process_chat_message(message, context_data)
        
        # Store chat history with model_used
        db_chat = ChatHistory(
            user_id=current_user.id,
            message=message,
            response=response_data["response"],
            context_data=response_data.get("real_time_data", {}),
            model_used=model_used
        )
        db.add(db_chat)
        db.commit()
        
        return {
            "response": response_data["response"],
            "confidence": response_data.get("confidence", 0.8),
            "agent_type": response_data.get("agent_type", "enhanced_chat"),
            "data_sources": response_data.get("data_sources", []),
            "real_time_data": response_data.get("real_time_data", {}),
            "timestamp": response_data.get("timestamp")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Location-based chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.get("/service-status")
async def get_service_status(current_user: User = Depends(get_current_user)):
    """Get status of enhanced AI chat services"""
    try:
        # Check service availability
        service_status = {
            "ai_provider": enhanced_ai_chat_service.ai_provider,
            "openai_available": enhanced_ai_chat_service.client is not None,
            "google_search_available": len(enhanced_ai_chat_service.google_search.api_keys) > 0,
            "real_time_data_sources": {
                "noaa_alerts": True,
                "earthquake_data": True,
                "weather_service": enhanced_ai_chat_service.real_time_data.weather_service is not None
            },
            "last_check": datetime.utcnow().isoformat()
        }
        
        return service_status
        
    except Exception as e:
        logger.error(f"Service status check error: {e}")
        return {
            "ai_provider": "error",
            "openai_available": False,
            "google_search_available": False,
            "real_time_data_sources": {},
            "error": str(e),
            "last_check": datetime.utcnow().isoformat()
        }

@router.post("/quick-marine-status")
async def get_quick_marine_status(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get quick marine status for a location"""
    try:
        location = request.get("location")
        latitude = location.get("latitude") if location else None
        longitude = location.get("longitude") if location else None
        
        # Get real-time marine data
        real_time_data = await enhanced_ai_chat_service.real_time_data.get_noaa_marine_alerts()
        
        # Quick status summary
        status_summary = "✅ No current marine alerts"
        alert_count = 0
        
        if real_time_data.get("success") and real_time_data.get("marine_alerts"):
            alerts = real_time_data["marine_alerts"]
            alert_count = len(alerts)
            if alert_count > 0:
                status_summary = f"🚨 {alert_count} active marine alerts"
        
        return {
            "status": status_summary,
            "alert_count": alert_count,
            "location": location,
            "data_sources": ["noaa_weather_api"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Quick marine status error: {e}")
        return {
            "status": "⚠️ Unable to check marine status",
            "alert_count": 0,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.post("/test-public-chat", response_model=ChatResponse)
async def test_public_enhanced_chat(
    message: ChatMessage,
    db: Session = Depends(get_db)
):
    """Public test endpoint for enhanced AI chat - for testing response cleaning"""
    try:
        logger.info(f"🧪 TEST PUBLIC CHAT: {message.message[:50]}...")
        
        # Prepare minimal context data for testing
        context_data = {}
        if hasattr(message, 'context_location') and message.context_location:
            context_data["location"] = message.context_location
        
        # Process message with enhanced service
        response_data = await process_chat_message(
            message=message.message,
            context_data=context_data
        )
        
        logger.info(f"✅ Test response generated: {len(response_data.get('response', ''))} chars")
        
        # Return ChatResponse format
        return ChatResponse(
            response=response_data["response"],
            confidence=response_data.get("confidence"),
            context_data=response_data.get("real_time_data"),
            timestamp=datetime.fromisoformat(response_data["timestamp"])
        )
        
    except Exception as e:
        logger.error(f"Test public chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Test chat processing failed: {str(e)}")
