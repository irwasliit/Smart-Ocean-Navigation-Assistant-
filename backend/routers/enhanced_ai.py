from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import asyncio
import traceback

from database import get_db
from .auth import get_current_user
from models import User
from services.multi_agent_ai_service import multi_agent_service, NavigationContext
from services.simple_enhanced_ir_service import simple_enhanced_ir_service as enhanced_ir_service
from services.enhanced_ai_chat_service import enhanced_ai_chat_service, process_chat_message
from datetime import datetime


router = APIRouter()

@router.post("/chat")
async def chat_with_ai(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enhanced AI chat endpoint using multi-agent system"""
    try:
        # Enforce daily chat limit (AI Marine Assistant)
        message = request.get("message", "")
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Prepare context data if available
        context_data = {}
        if "weather_data" in request:
            context_data["weather_data"] = request["weather_data"]
        if "route_data" in request:
            context_data["route_data"] = request["route_data"]
        if "location" in request:
            context_data["location"] = request["location"]
        if "current_location" in request:
            context_data["current_location"] = request["current_location"]
        
        # Get recent IR content for context
        try:
            ir_documents = await enhanced_ir_service.get_latest_maritime_bulletins(limit=5)
            context_data["ir_content"] = [
                {"text": doc.get("content", ""), "title": doc.get("title", ""), "source": doc.get("source", "")}
                for doc in ir_documents
            ]
        except Exception as e:
            print(f"Warning: Could not retrieve IR content: {e}")
            context_data["ir_content"] = []
        
        # Get AI response using multi-agent system
        print(f"🔥 ENHANCED AI: Calling multi_agent_service.chat_response with message: '{message[:50]}...'")
        response = await multi_agent_service.chat_response(message, context_data)
        print(f"🔥 ENHANCED AI: Received response with confidence: {response.confidence}")
        
        # Generate dynamic suggestions with real-world locations based on query type
        import random
        dynamic_suggestions = []
        query_lower = message.lower()
        
        if any(word in query_lower for word in ['weather', 'conditions', 'forecast']):
            weather_suggestions = [
                "How are sea conditions in Atlantic Ocean now",
                "What is the weather like in Indian Ocean currently",
                "Are there any storms affecting Pacific routes",
                "What are current wind conditions for sailing",
                "Is it safe to navigate during monsoon season",
                "What severe weather systems are active now",
                "How are wave conditions in major shipping lanes",
                "What ocean areas have rough seas currently"
            ]
            dynamic_suggestions = random.sample(weather_suggestions, 4)
            
        elif any(word in query_lower for word in ['disaster', 'natural', 'earthquake', 'tsunami', 'hurricane', 'typhoon']):
            disaster_suggestions = [
                "Which countries affected by natural disasters now",
                "What natural disasters currently happening globally",
                "Are there any active tsunami warnings worldwide",
                "Which regions have earthquake activity right now",
                "What typhoons and hurricanes are currently active",
                "Are there any volcanic eruptions affecting shipping",
                "Which areas have severe weather warnings now",
                "What emergency alerts are active for maritime routes"
            ]
            dynamic_suggestions = random.sample(disaster_suggestions, 4)
            
        elif any(word in query_lower for word in ['route', 'navigation', 'path', 'course']):
            route_suggestions = [
                "Which ocean routes are safest right now",
                "What shipping lanes have current hazards",
                "Are Atlantic crossing routes safe today",
                "Which Pacific routes should be avoided now",
                "What are the safest paths through Indian Ocean",
                "Are there any route restrictions currently active",
                "Which maritime corridors have weather issues",
                "What alternative routes are recommended now"
            ]
            dynamic_suggestions = random.sample(route_suggestions, 4)
            
        elif any(word in query_lower for word in ['current', 'now', 'today', 'happening']):
            current_suggestions = [
                "Is it safe to travel in Pacific Ocean now",
                "What are current sea conditions globally",
                "Are there any active weather warnings for shipping",
                "Which ocean routes are safe right now",
                "What maritime hazards are active today",
                "Are there any piracy threats currently",
                "Which shipping lanes have disruptions now",
                "What natural disasters affecting oceans currently"
            ]
            dynamic_suggestions = random.sample(current_suggestions, 4)
            
        elif any(word in query_lower for word in ['port', 'harbor', 'terminal', 'dock']):
            port_suggestions = [
                "Which ports have operational issues currently",
                "Are there any harbor closures worldwide now",
                "What ports have congestion problems today",
                "Which terminals are experiencing delays now",
                "Are there any port security alerts active",
                "What harbors have weather restrictions currently",
                "Which ports have fuel shortage issues now",
                "Are there any customs delays at major ports"
            ]
            dynamic_suggestions = random.sample(port_suggestions, 4)
            
        else:
            general_suggestions = [
                "What maritime safety issues are happening now",
                "Are there any global shipping disruptions currently",
                "Which ocean areas have security concerns today",
                "What weather patterns are affecting ships now",
                "Are there any seasonal navigation warnings active",
                "Which regions have emergency alerts for vessels",
                "What global maritime threats should I know about",
                "Are there any international shipping advisories now"
            ]
            dynamic_suggestions = random.sample(general_suggestions, 4)
        
        # Safely extract agent type and timestamp
        try:
            agent_type = response.agent_type.value if hasattr(response.agent_type, 'value') else str(response.agent_type)
        except:
            agent_type = "communication_manager"
            
        try:
            timestamp = response.timestamp.isoformat() if hasattr(response.timestamp, 'isoformat') else str(response.timestamp)
        except:
            timestamp = datetime.now().isoformat()
        
        return {
            "response": response.content,
            "confidence": response.confidence,
            "agent_type": agent_type,
            "timestamp": timestamp,
            "suggestions": dynamic_suggestions
        }
        
    except Exception as e:
        print(f"❌ Error in AI chat: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Full traceback: {traceback.format_exc()}")
        
        # Try fallback response
        try:
            fallback_response = f"I apologize, but I'm experiencing technical difficulties. The AI service is temporarily limited. Please try your question again, or try asking: 'What are current marine weather conditions?' Error details: {str(e)[:100]}"
            
            return {
                "response": fallback_response,
                "confidence": 0.1,
                "agent_type": "fallback",
                "timestamp": datetime.now(),
                "suggestions": [
                    "What are current marine weather conditions?",
                    "Are there any weather alerts for sailing?",
                    "Is it safe to navigate today?",
                    "What are current wind conditions?"
                ]
            }
        except Exception as fallback_error:
            print(f"❌ Even fallback failed: {fallback_error}")
            raise HTTPException(status_code=500, detail=f"AI service temporarily unavailable: {str(e)}")

@router.post("/analyze-conditions")
async def analyze_maritime_conditions(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Comprehensive maritime conditions analysis using multi-agent system"""
    try:
        location_data = request.get("location", {})
        weather_data = request.get("weather_data", {})
        
        if not location_data or not weather_data:
            raise HTTPException(status_code=400, detail="Location and weather data are required")
        
        # Create navigation context
        vessel_params = request.get("vessel_params", {})
        context = NavigationContext(
            vessel_type=vessel_params.get("type", "general"),
            vessel_size=vessel_params.get("size", "medium"),
            experience_level=vessel_params.get("experience", "intermediate"),
            cargo_type=vessel_params.get("cargo"),
            departure_port=location_data.get("name", "Unknown"),
            destination_port=location_data.get("name", "Unknown"),
            departure_time=datetime.now(),
            urgency_level=vessel_params.get("urgency", "normal")
        )
        
        # Get IR content
        ir_documents = await enhanced_ir_service.retrieve_and_process_content()
        ir_content = [
            {"text": doc.content, "title": doc.title, "source": doc.source}
            for doc in ir_documents[:10]
        ]
        
        # Run comprehensive analysis
        route_data = {"distance": 0, "sample_points": [location_data]}
        agent_responses = await multi_agent_service.comprehensive_analysis(
            weather_data, route_data, ir_content, context
        )
        
        # Format response
        analysis_result = {
            "location": location_data,
            "analysis_timestamp": datetime.now(),
            "agent_responses": {}
        }
        
        for agent_type, response in agent_responses.items():
            analysis_result["agent_responses"][agent_type] = {
                "content": response.content,
                "confidence": response.confidence,
                "timestamp": response.timestamp,
                "metadata": response.metadata
            }
        
        return analysis_result
        
    except Exception as e:
        print(f"Error in conditions analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze maritime conditions")

@router.post("/optimize-route")
async def optimize_route(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Route optimization using multi-agent system"""
    try:
        route_data = request.get("route_data", {})
        weather_data = request.get("weather_data", {})
        vessel_params = request.get("vessel_params", {})
        
        if not route_data:
            raise HTTPException(status_code=400, detail="Route data is required")
        
        # Create navigation context
        context = NavigationContext(
            vessel_type=vessel_params.get("type", "general"),
            vessel_size=vessel_params.get("size", "medium"),
            experience_level=vessel_params.get("experience", "intermediate"),
            cargo_type=vessel_params.get("cargo"),
            departure_port=vessel_params.get("departure", "Start"),
            destination_port=vessel_params.get("destination", "End"),
            departure_time=datetime.fromisoformat(vessel_params.get("departure_time", datetime.now().isoformat())),
            urgency_level=vessel_params.get("urgency", "normal")
        )
        
        # Get IR content
        ir_documents = await enhanced_ir_service.retrieve_and_process_content()
        ir_content = [
            {"text": doc.content, "title": doc.title, "source": doc.source}
            for doc in ir_documents[:10]
        ]
        
        # Run route optimization
        agent_responses = await multi_agent_service.comprehensive_analysis(
            weather_data, route_data, ir_content, context
        )
        
        # Extract route optimization response
        route_response = agent_responses.get("route")
        weather_response = agent_responses.get("weather")
        hazard_response = agent_responses.get("hazards")
        
        optimization_result = {
            "route_analysis": {
                "content": route_response.content if route_response else "Route analysis unavailable",
                "confidence": route_response.confidence if route_response else 0.1
            },
            "weather_impact": {
                "content": weather_response.content if weather_response else "Weather analysis unavailable",
                "confidence": weather_response.confidence if weather_response else 0.1
            },
            "hazard_assessment": {
                "content": hazard_response.content if hazard_response else "Hazard assessment unavailable",
                "confidence": hazard_response.confidence if hazard_response else 0.1
            },
            "optimization_timestamp": datetime.now(),
            "route_metadata": {
                "distance": route_data.get("distance", 0),
                "waypoints": len(route_data.get("sample_points", [])),
                "vessel_context": vessel_params
            }
        }
        
        return optimization_result
        
    except Exception as e:
        print(f"Error in route optimization: {e}")
        raise HTTPException(status_code=500, detail="Failed to optimize route")

@router.post("/detect-hazards")
async def detect_hazards(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Maritime hazard detection using multi-agent system"""
    try:
        weather_data = request.get("weather_data", {})
        route_data = request.get("route_data", {})
        location_data = request.get("location", {})
        
        # Get fresh IR content for hazard detection
        ir_documents = await enhanced_ir_service.retrieve_and_process_content()
        ir_content = [
            {"text": doc.content, "title": doc.title, "source": doc.source}
            for doc in ir_documents
        ]
        
        # Also extract maritime alerts
        alerts = await enhanced_ir_service.extract_alerts(ir_documents)
        
        # Use hazard detection agent
        hazard_detector = multi_agent_service.hazard_detector
        if hazard_detector:
            hazard_response = await hazard_detector.detect_hazards(
                weather_data, route_data or {"distance": 0, "sample_points": [location_data]}, ir_content
            )
            
            return {
                "hazard_analysis": {
                    "content": hazard_response.content,
                    "confidence": hazard_response.confidence,
                    "timestamp": hazard_response.timestamp,
                    "metadata": hazard_response.metadata
                },
                "maritime_alerts": [
                    {
                        "id": alert.alert_id,
                        "type": alert.alert_type,
                        "severity": alert.severity,
                        "description": alert.description,
                        "location": alert.location,
                        "effective_date": alert.effective_date,
                        "recommendations": alert.recommendations
                    }
                    for alert in alerts
                ],
                "ir_sources_analyzed": len(ir_documents),
                "detection_timestamp": datetime.now()
            }
        else:
            return {
                "hazard_analysis": {
                    "content": "Hazard detection service unavailable",
                    "confidence": 0.1,
                    "timestamp": datetime.now(),
                    "metadata": {}
                },
                "maritime_alerts": [],
                "ir_sources_analyzed": 0,
                "detection_timestamp": datetime.now()
            }
        
    except Exception as e:
        print(f"Error in hazard detection: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect hazards")

@router.get("/ir-content")
async def get_ir_content(
    sources: Optional[str] = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get processed IR content"""
    try:
        source_list = sources.split(",") if sources else None
        ir_documents = await enhanced_ir_service.retrieve_and_process_content(source_list)
        
        # Limit results
        limited_docs = ir_documents[:limit]
        
        return {
            "documents": [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "summary": doc.summary,
                    "source": doc.source,
                    "url": doc.url,
                    "published_date": doc.published_date,
                    "relevance_score": doc.relevance_score,
                    "keywords": doc.keywords,
                    "category": doc.category,
                    "priority": doc.priority,
                    "sentiment": doc.sentiment
                }
                for doc in limited_docs
            ],
            "total_processed": len(ir_documents),
            "retrieval_timestamp": datetime.now()
        }
        
    except Exception as e:
        print(f"Error retrieving IR content: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve IR content")

@router.post("/search-ir")
async def search_ir_content(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search IR content using NLP"""
    try:
        query = request.get("query", "")
        max_results = request.get("max_results", 10)
        
        if not query:
            raise HTTPException(status_code=400, detail="Search query is required")
        
        # Get all documents first
        ir_documents = await enhanced_ir_service.retrieve_and_process_content()
        
        # Search using NLP
        search_results = await enhanced_ir_service.search_content(query, ir_documents, max_results)
        
        return {
            "query": query,
            "results": [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "summary": doc.summary,
                    "content": doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
                    "source": doc.source,
                    "relevance_score": doc.relevance_score,
                    "keywords": doc.keywords,
                    "category": doc.category,
                    "priority": doc.priority
                }
                for doc in search_results
            ],
            "total_results": len(search_results),
            "search_timestamp": datetime.now()
        }
        
    except Exception as e:
        print(f"Error searching IR content: {e}")
        raise HTTPException(status_code=500, detail="Failed to search IR content")
