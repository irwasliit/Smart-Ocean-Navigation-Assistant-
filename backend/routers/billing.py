from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, constr
from sqlalchemy.orm import Session

from database import get_db
from models import User, SavedLocation, AlertPreference
from .auth import get_current_user


router = APIRouter()


class UpgradeRequest(BaseModel):
    plan: constr(pattern=r"^(pro|premium)$")
    card_number: constr(min_length=16, max_length=16)
    cvv: constr(min_length=3, max_length=3)
    exp_month: constr(pattern=r"^(0[1-9]|1[0-2])$")
    exp_year: constr(min_length=2, max_length=4)


@router.post("/upgrade")
async def upgrade_plan(
    req: UpgradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Fake validation: ensure fields are present and look valid
    if not req.card_number.isdigit() or len(req.card_number) != 16:
        raise HTTPException(status_code=400, detail="Card number must be exactly 16 digits")
    if not req.cvv.isdigit() or len(req.cvv) != 3:
        raise HTTPException(status_code=400, detail="CVV must be exactly 3 digits")
    # Basic expiry validation
    if not req.exp_year.isdigit():
        raise HTTPException(status_code=400, detail="Invalid expiry year")

    # Perform fake charge success
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.plan = req.plan
    db.commit()

    return {"message": "Plan upgraded successfully", "plan": user.plan}


@router.post("/downgrade")
async def downgrade_to_free(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.plan = "free"
    # Remove all alert preferences and saved locations when downgrading to free
    db.query(AlertPreference).filter(AlertPreference.user_id == user.id).delete()
    db.query(SavedLocation).filter(SavedLocation.user_id == user.id).delete()
    db.commit()

    return {"message": "Plan downgraded to free", "plan": user.plan}


@router.post("/apply-plan-rules")
async def apply_plan_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ensure user's data adheres to current plan limits (prune extras)."""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.plan == "free":
        db.query(AlertPreference).filter(AlertPreference.user_id == user.id).delete()
        db.query(SavedLocation).filter(SavedLocation.user_id == user.id).delete()
        db.commit()
        return {"message": "Applied free plan rules: removed all alerts and locations"}

    if user.plan == "pro":
        # Keep only the 5 most recent of each
        prefs = (
            db.query(AlertPreference)
            .filter(AlertPreference.user_id == user.id)
            .order_by(AlertPreference.created_at.desc())
            .all()
        )
        if len(prefs) > 5:
            ids_to_keep = {p.id for p in prefs[:5]}
            db.query(AlertPreference).filter(
                AlertPreference.user_id == user.id,
                ~AlertPreference.id.in_(ids_to_keep)
            ).delete(synchronize_session=False)

        locs = (
            db.query(SavedLocation)
            .filter(SavedLocation.user_id == user.id)
            .order_by(SavedLocation.created_at.desc())
            .all()
        )
        if len(locs) > 5:
            ids_to_keep = {l.id for l in locs[:5]}
            db.query(SavedLocation).filter(
                SavedLocation.user_id == user.id,
                ~SavedLocation.id.in_(ids_to_keep)
            ).delete(synchronize_session=False)

        db.commit()
        return {"message": "Applied pro plan rules: limited to 5 alerts and locations"}

    return {"message": "Premium plan: no changes needed"}


