from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import logging
import traceback

from database import get_db
from models import User, ChatHistory, IRContent
from schemas import ChatMessage, ChatResponse
from .auth import get_current_user
from services.multi_agent_ai_service import multi_agent_service


# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat with AI assistant about marine weather and hazards using multi-agent system"""
    try:
        # Enforce daily chat limit
        # Generate AI response using multi-agent system
        response_data = await multi_agent_service.process_message(
            message=message.message,
            context={"user_id": current_user.id, "location": message.context_location}
        )
        
        # Store chat history
        db_chat = ChatHistory(
            user_id=current_user.id,
            message=message.message,
            response=response_data["response"],
            context_data=response_data.get("context_data")
        )
        db.add(db_chat)
        db.commit()
        
        return ChatResponse(
            response=response_data["response"],
            confidence=response_data.get("confidence"),
            context_data=response_data.get("context_data"),
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")

@router.post("/public_chat", response_model=ChatResponse)
async def public_chat_with_ai(
    message: ChatMessage,
    db: Session = Depends(get_db)
):
    """Public chat with AI assistant (no auth). Uses enhanced multi-agent system with IR snippets."""
    logger.info(f"🌐 PUBLIC CHAT REQUEST: '{message.message[:50]}...'")
    logger.info(f"📍 Context location: {message.context_location}")
    
    try:
        # Retrieve recent IR content to enrich response
        logger.info("📚 Retrieving IR content from database...")
        ir_query = db.query(IRContent).filter(IRContent.is_active == True)
        # Simple relevance filter if context_location is provided
        if message.context_location:
            like_pattern = f"%{message.context_location}%"
            ir_query = ir_query.filter((IRContent.title.ilike(like_pattern)) | (IRContent.content.ilike(like_pattern)))
        ir_content = ir_query.order_by(IRContent.created_at.desc()).limit(5).all()
        logger.info(f"📚 Found {len(ir_content)} IR content items")
        
        ir_snippets = [
            {
                "title": item.title,
                "source": item.source,
                "severity": item.severity,
                "valid_until": item.valid_until.isoformat() if item.valid_until else None,
            }
            for item in ir_content
        ]

        # Generate AI response using multi-agent system
        logger.info("🤖 Calling multi_agent_service.process_message...")
        response_data = await multi_agent_service.process_message(
            message=message.message,
            context={"location": message.context_location, "ir_snippets": ir_snippets}
        )
        
        logger.info(f"✅ Received response_data keys: {list(response_data.keys())}")
        logger.info(f"📊 Response confidence: {response_data.get('confidence', 'MISSING')}")
        logger.info(f"📝 Response length: {len(response_data.get('response', ''))}")

        final_response = ChatResponse(
            response=response_data["response"],
            confidence=response_data.get("confidence"),
            context_data=response_data.get("context_data"),
            timestamp=datetime.utcnow()
        )
        
        logger.info(f"📤 Returning ChatResponse with confidence: {final_response.confidence}")
        return final_response
        
    except Exception as e:
        logger.error(f"❌ ERROR in public_chat_with_ai: {e}")
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error processing public chat message: {str(e)}")

@router.get("/history", response_model=List[dict])
async def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's chat history"""
    chat_history = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id
    ).order_by(ChatHistory.created_at.desc()).limit(50).all()
    
    return [
        {
            "id": chat.id,
            "message": chat.message,
            "response": chat.response,
            "created_at": chat.created_at,
            "model_used": chat.model_used if hasattr(chat, 'model_used') else 'advanced'
        }
        for chat in chat_history
    ]

@router.delete("/history")
async def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear user's chat history"""
    db.query(ChatHistory).filter(ChatHistory.user_id == current_user.id).delete()
    db.commit()
    
    return {"message": "Chat history cleared successfully"}

@router.get("/suggestions")
async def get_chat_suggestions():
    """Get enhanced suggestions with real-world maritime scenarios"""
    import random
    
    # Comprehensive real-world maritime suggestions
    all_suggestions = [
        # Current weather and conditions with specific locations
        "Current weather conditions in Colombo Harbor, Sri Lanka",
        "Sea state between Mumbai and Kochi, India right now",
        "Wind and wave forecast for Bay of Bengal this week",
        "Visibility conditions in the Strait of Malacca today",
        "Storm activity in the South China Sea region",
        "Monsoon impact on Indian Ocean shipping routes",
        
        # Real route planning and optimization
        "Safe route from Singapore to Hong Kong with current weather",
        "Optimal passage from Chennai to Colombo avoiding rough seas",
        "Best time to sail from Dubai to Mumbai this month",
        "Route analysis from Jaffna to Trincomalee, Sri Lanka",
        "Pacific crossing from Los Angeles to Tokyo safety assessment",
        "Atlantic route from New York to Southampton weather routing",
        
        # Specific hazard and safety assessments
        "Typhoon tracking in Western Pacific affecting shipping",
        "Piracy alerts in Gulf of Aden and Somali waters",
        "Tsunami warnings for Indian Ocean coastal areas",
        "Maritime security threats in Red Sea shipping lanes",
        "Cyclone season impact on Australia-Asia trade routes",
        "Earthquake activity near Japan affecting maritime operations",
        
        # Real disaster and emergency information
        "Current natural disasters affecting Southeast Asian countries",
        "Hurricane activity in Caribbean affecting cruise routes",
        "Volcanic ash from Indonesia impacting air and sea navigation",
        "Flooding in Bangladesh affecting Chittagong port operations",
        "Typhoon damage assessment in Philippines ports",
        "Monsoon flooding impact on Indian subcontinent ports",
        
        # Port and harbor real-world scenarios
        "Port congestion and delays at Singapore container terminals",
        "Fuel bunker availability and prices in Dubai ports",
        "Customs clearance procedures at Hong Kong maritime facilities",
        "Pilot service availability at Colombo International Harbor",
        "Anchorage capacity at Mumbai's Jawaharlal Nehru Port",
        "Container handling capacity at Chennai Port Trust",
        
        # Regional maritime intelligence
        "Commercial vessel traffic density in Malacca Strait",
        "Fishing fleet activity near Sri Lankan territorial waters",
        "Naval exercises affecting shipping in Arabian Sea",
        "Suez Canal transit schedules and waiting times today",
        "Panama Canal expansion impact on Asian trade routes",
        "Arctic shipping route viability with current ice conditions",
        
        # Practical maritime operations
        "Best practices for monsoon season sailing in Indian Ocean",
        "Fuel efficiency tips for long-haul Pacific crossings",
        "Emergency port options between India and Middle East",
        "Communication equipment requirements for international waters",
        "Weather routing services comparison for trans-Pacific voyages",
        "Maritime insurance considerations for high-risk regions"
    ]
    
    # Return 10 random suggestions for variety
    selected_suggestions = random.sample(all_suggestions, min(10, len(all_suggestions)))
    
    return {"suggestions": selected_suggestions}
