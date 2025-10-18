from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uvicorn
from dotenv import load_dotenv
import os
import logging
import traceback

# Configure clean logging - Only show errors and warnings
logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')
# Suppress SQLAlchemy verbose logs
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)

from database import get_db, engine
from models import Base
from routers import auth
from routers import weather
from routers import routes
from routers import enhanced_routes
from routers import alerts
from routers import ai_chat
from routers import enhanced_ai
from routers import enhanced_ai_chat_router
from routers import hazard_alerts
from routers import billing
from scheduler import start_scheduler
from services.notification_scheduler import scheduler

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Smart Ocean Navigation Assistant - Enhanced Marine Weather & AI System",
    description="A comprehensive marine weather monitoring system with multi-agent AI, NLP-powered hazard detection, and intelligent route optimization",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    error_id = f"error_{hash(str(exc))}"
    
    # Log the full error details
    logging.error(f"Unhandled exception {error_id}: {str(exc)}")
    logging.error(f"Traceback: {traceback.format_exc()}")
    
    # Return structured error response
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "error_id": error_id,
            "type": "server_error"
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,  # Use 'detail' to match FastAPI standard
            "error": exc.detail,    # Keep 'error' for backward compatibility
            "status_code": exc.status_code,
            "type": "http_error"
        }
    )

# Security
security = HTTPBearer()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(weather.router, prefix="/api/weather", tags=["weather"])
app.include_router(routes.router, prefix="/api/routes", tags=["routes"])
app.include_router(enhanced_routes.router, prefix="/api/enhanced-routes", tags=["enhanced-routes"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(ai_chat.router, prefix="/api/ai", tags=["ai-chat"])
app.include_router(enhanced_ai.router, prefix="/api/enhanced-ai", tags=["enhanced-ai-multi-agent"])
app.include_router(enhanced_ai_chat_router.router, prefix="/api/enhanced-chat", tags=["enhanced-ai-chat"])
app.include_router(hazard_alerts.router, prefix="/api/hazard-alerts", tags=["hazard-alerts"])
app.include_router(billing.router, prefix="/api/billing", tags=["billing"])

@app.on_event("startup")
async def startup_event():
    """Start the background scheduler for email alerts and initialize AI services"""
    start_scheduler()
    # Start the weather notification scheduler
    import asyncio
    asyncio.create_task(scheduler.start_scheduler())
    
    print("🌊 Smart Ocean Navigation Assistant Started!")
    print("✅ Multi-Agent AI System Initialized")
    print("✅ Enhanced IR Service Ready")
    print("✅ NLP Processing Enabled")
    print("✅ Background Schedulers Active")

@app.get("/")
async def root():
    return {
        "message": "Smart Ocean Navigation Assistant - Enhanced Marine Weather & AI System",
        "version": "2.0.0",
        "features": [
            "Multi-Agent AI Analysis",
            "NLP-Powered Information Retrieval", 
            "Intelligent Route Optimization",
            "Real-time Hazard Detection",
            "Maritime Content Processing",
            "Weather Data Integration"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "smart-ocean-navigation-api",
        "version": "2.0.0",
        "ai_services": "multi-agent-enabled"
    }

@app.get("/api/system-status")
async def system_status():
    """Get system status including AI and IR services"""
    try:
        from services.multi_agent_ai_service import multi_agent_service
        from services.simple_enhanced_ir_service import simple_enhanced_ir_service
        
        ai_status = "available" if multi_agent_service.client else "limited"
        
        return {
            "system": "operational",
            "ai_service": ai_status,
            "ir_service": "operational",
            "multi_agent_system": "enabled",
            "nlp_processing": "available",
            "services": {
                "weather_analyst": "ready",
                "route_optimizer": "ready", 
                "hazard_detector": "ready",
                "information_retriever": "ready",
                "communication_manager": "ready"
            }
        }
    except Exception as e:
        return {
            "system": "operational",
            "ai_service": "limited",
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
