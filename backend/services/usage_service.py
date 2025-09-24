from datetime import datetime, date
from sqlalchemy.orm import Session

from models import DailyUsage, User
from . import PLAN_LIMITS


class UsageService:
    @staticmethod
    def _get_today_usage(db: Session, user_id: int) -> DailyUsage:
        today = date.today()
        usage = (
            db.query(DailyUsage)
            .filter(DailyUsage.user_id == user_id, DailyUsage.date == today)
            .first()
        )
        if not usage:
            usage = DailyUsage(user_id=user_id, date=today)
            db.add(usage)
            db.commit()
            db.refresh(usage)
        return usage

    @staticmethod
    def check_and_increment(db: Session, user: User, feature: str) -> None:
        limits = PLAN_LIMITS.get(user.plan or "free", PLAN_LIMITS["free"])
        daily_limit = limits.get(f"daily_{feature}")
        if daily_limit is None:
            return

        usage = UsageService._get_today_usage(db, user.id)
        current_count = getattr(usage, f"{feature}_count")
        if current_count >= daily_limit:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail=f"Daily limit reached for {feature} on {user.plan} plan")

        setattr(usage, f"{feature}_count", current_count + 1)
        db.commit()

    @staticmethod
    def safe_check_and_increment(db: Session, user: User, feature: str) -> None:
        """Same as check_and_increment but never raises; logs and returns on errors."""
        try:
            UsageService.check_and_increment(db, user, feature)
        except Exception as exc:  # noqa: BLE001
            # Avoid breaking primary flows if usage table or limits cause issues
            try:
                import logging
                logging.getLogger(__name__).warning("Usage limit check failed for feature %s: %s", feature, exc)
            except Exception:
                pass

    @staticmethod
    def can_create_location(db: Session, user: User) -> bool:
        limits = PLAN_LIMITS.get(user.plan or "free", PLAN_LIMITS["free"])
        max_locations = limits.get("max_locations")
        if max_locations is None:
            return True
        from models import SavedLocation
        count = db.query(SavedLocation).filter(SavedLocation.user_id == user.id).count()
        return count < max_locations

    @staticmethod
    def can_create_alert(db: Session, user: User) -> bool:
        limits = PLAN_LIMITS.get(user.plan or "free", PLAN_LIMITS["free"])
        max_alerts = limits.get("max_alerts")
        if max_alerts is None:
            return True
        from models import AlertPreference
        count = db.query(AlertPreference).filter(AlertPreference.user_id == user.id).count()
        return count < max_alerts


