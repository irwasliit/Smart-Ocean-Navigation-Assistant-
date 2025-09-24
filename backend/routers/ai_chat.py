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
from services.usage_service import UsageService

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
        UsageService.check_and_increment(db, current_user, feature="chat")
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
            "created_at": chat.created_at
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
    """Get enhanced suggestions for the multi-agent AI chat"""
    suggestions = [
        "Analyze current weather conditions for my location",
        "Optimize route from Miami to Nassau considering weather",
        "Detect maritime hazards along the Gulf Coast",
        "Find latest maritime safety bulletins",
        "What's the best departure time for my route?",
        "Compare weather conditions between two ports",
        "Are there any storm warnings in my area?",
        "Explain marine weather patterns in simple terms",
        "Provide route recommendations for heavy seas",
        "Search for recent maritime incidents"
    ]
    
    return {"suggestions": suggestions}
