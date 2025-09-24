from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import date

from database import get_db
from .auth import get_current_user
from models import User, DailyUsage
from services.usage_service import UsageService
from services import PLAN_LIMITS

router = APIRouter()

@router.get("/today")
async def get_today_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's usage statistics for the current user"""
    try:
        usage = UsageService._get_today_usage(db, current_user.id)
        
        # Get limits for the user's plan
        limits = PLAN_LIMITS.get(current_user.plan or "free", PLAN_LIMITS["free"])
        
        return {
            "date": usage.date,
            "usage": {
                "chat": {
                    "count": usage.chat_count,
                    "limit": limits.get("daily_chat")
                },
                "weather": {
                    "count": usage.weather_count,
                    "limit": limits.get("daily_weather")
                },
                "route": {
                    "count": usage.route_count,
                    "limit": limits.get("daily_route")
                },
                "hazard": {
                    "count": usage.hazard_count,
                    "limit": limits.get("daily_hazard")
                }
            },
            "plan": current_user.plan or "free",
            "limits": {
                "max_locations": limits.get("max_locations"),
                "max_alerts": limits.get("max_alerts")
            }
        }
    except Exception as e:
        print(f"Error fetching usage data: {e}")
        # Return default usage data if there's an error
        limits = PLAN_LIMITS.get(current_user.plan or "free", PLAN_LIMITS["free"])
        return {
            "date": str(date.today()),
            "usage": {
                "chat": {
                    "count": 0,
                    "limit": limits.get("daily_chat")
                },
                "weather": {
                    "count": 0,
                    "limit": limits.get("daily_weather")
                },
                "route": {
                    "count": 0,
                    "limit": limits.get("daily_route")
                },
                "hazard": {
                    "count": 0,
                    "limit": limits.get("daily_hazard")
                }
            },
            "plan": current_user.plan or "free",
            "limits": {
                "max_locations": limits.get("max_locations"),
                "max_alerts": limits.get("max_alerts")
            }
        }

@router.get("/limits")
async def get_usage_limits(
    current_user: User = Depends(get_current_user)
):
    """Get usage limits for the current user's plan"""
    limits = PLAN_LIMITS.get(current_user.plan or "free", PLAN_LIMITS["free"])
    
    return {
        "plan": current_user.plan or "free",
        "limits": limits
    }

@router.get("/stats")
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive usage statistics"""
    try:
        # Get today's usage
        today_usage = UsageService._get_today_usage(db, current_user.id)
        
        # Get plan limits
        limits = PLAN_LIMITS.get(current_user.plan or "free", PLAN_LIMITS["free"])
        
        # Calculate usage percentages
        usage_percentages = {}
        for feature in ["chat", "weather", "route", "hazard"]:
            count = getattr(today_usage, f"{feature}_count", 0)
            limit = limits.get(f"daily_{feature}")
            if limit is None:
                usage_percentages[feature] = 0  # Unlimited
            elif limit == 0:
                usage_percentages[feature] = 100  # No access
            else:
                usage_percentages[feature] = min(100, (count / limit) * 100)
        
        return {
            "today": {
                "date": today_usage.date,
                "usage": {
                    "chat": getattr(today_usage, "chat_count", 0),
                    "weather": getattr(today_usage, "weather_count", 0),
                    "route": getattr(today_usage, "route_count", 0),
                    "hazard": getattr(today_usage, "hazard_count", 0)
                },
                "percentages": usage_percentages
            },
            "plan": current_user.plan or "free",
            "limits": limits
        }
    except Exception as e:
        print(f"Error fetching usage stats: {e}")
        # Return default stats if there's an error
        limits = PLAN_LIMITS.get(current_user.plan or "free", PLAN_LIMITS["free"])
        return {
            "today": {
                "date": str(date.today()),
                "usage": {
                    "chat": 0,
                    "weather": 0,
                    "route": 0,
                    "hazard": 0
                },
                "percentages": {
                    "chat": 0,
                    "weather": 0,  
                    "route": 0,
                    "hazard": 0
                }
            },
            "plan": current_user.plan or "free",
            "limits": limits
        }