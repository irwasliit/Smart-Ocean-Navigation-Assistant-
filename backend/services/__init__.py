# Services package initialization

PLAN_LIMITS = {
    "free": {
        "max_locations": 0,
        "max_alerts": 0,
        "daily_chat": 10,
        "daily_weather": 10,
        "daily_route": 10,
        "daily_hazard": 10,
    },
    "pro": {
        "max_locations": 5,
        "max_alerts": 5,
        "daily_chat": 50,
        "daily_weather": 50,
        "daily_route": 50,
        "daily_hazard": 50,
    },
    "premium": {
        "max_locations": None,  # unlimited
        "max_alerts": None,
        "daily_chat": None,
        "daily_weather": None,
        "daily_route": None,
        "daily_hazard": None,
    },
}