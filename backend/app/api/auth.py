"""
Authentication endpoints
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt
import logging

from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str
    expires_in: int


def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login endpoint
    
    For MVP, using simple authentication.
    In production, integrate with OAuth2/SSO.
    """
    # TODO: Implement proper authentication
    # For now, accept any username/password for demo
    
    if not request.username or not request.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required"
        )
    
    # Create token
    access_token = create_access_token(
        data={
            "sub": request.username,
            "username": request.username,
            "role": "developer"  # Default role for MVP
        }
    )
    
    logger.info(f"User {request.username} logged in successfully")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout():
    """Logout endpoint"""
    # For JWT, logout is typically handled client-side by removing the token
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user():
    """Get current user information"""
    # TODO: Implement proper user extraction from JWT token
    return {
        "username": "demo_user",
        "role": "developer",
        "email": "demo@example.com"
    }
