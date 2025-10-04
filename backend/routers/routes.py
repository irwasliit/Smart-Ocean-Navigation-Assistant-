# backend/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from typing import Optional

from database import get_db
from models import User
from schemas import UserCreate, UserResponse, UserLogin, Token, UserUpdate

load_dotenv()

router = APIRouter()
security = HTTPBearer()

# -----------------------
# Password hashing
# -----------------------
# Use pbkdf2_sha256 to avoid bcrypt's 72-byte limit and native C dependency.
# If you prefer bcrypt, see the note at the end of this file.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash password (no bcrypt 72-byte limit when using pbkdf2_sha256)."""
    if password is None:
        raise ValueError("Password must not be None")
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against the stored hash."""
    if plain_password is None or hashed_password is None:
        return False
    return pwd_context.verify(plain_password, hashed_password)

# -----------------------
# JWT settings
# -----------------------
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    # jose.jwt accepts datetime for "exp"
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# -----------------------
# Dependency: get current user
# -----------------------
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security),
                     db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        # token "sub" may be string: convert to int safely
        try:
            user_id = int(sub)
        except (TypeError, ValueError):
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

# -----------------------
# Routes
# -----------------------
@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Basic sanity check - you can strengthen validation in your Pydantic schema
    if not user.password or not user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )

    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash and save
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    if not user_credentials.password or not user_credentials.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )

    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/usage/today")
async def get_today_usage(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get today's usage statistics for the current user"""
    from datetime import date
    from models import DailyUsage

    today = date.today()
    usage = (
        db.query(DailyUsage)
        .filter(DailyUsage.user_id == current_user.id, DailyUsage.date == today)
        .first()
    )

    if not usage:
        return {
            "chat_count": 0,
            "weather_count": 0,
            "route_count": 0,
            "hazard_count": 0,
            "date": today.isoformat()
        }

    return {
        "chat_count": usage.chat_count or 0,
        "weather_count": usage.weather_count or 0,
        "route_count": usage.route_count or 0,
        "hazard_count": usage.hazard_count or 0,
        "date": usage.date.isoformat()
    }

@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the current user's profile"""

    # Check if email is being changed and if it's already taken
    if user_update.email and user_update.email != current_user.email:
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email

    # Update full name if provided
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name

    # Update the updated_at timestamp
    current_user.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(current_user)
        return current_user
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
