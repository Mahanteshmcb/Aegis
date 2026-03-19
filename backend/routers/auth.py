"""
Aegis Backend - Authentication Router
Login, token refresh, user management.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

from backend.dependencies import get_db
from backend.exceptions import AuthenticationError

router = APIRouter(prefix="/api/v1", tags=["auth"])


class LoginRequest(BaseModel):
    """Login request payload."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db=Depends(get_db)):
    """
    User login endpoint.
    Returns access and refresh tokens.
    Implemented in Day 10.
    """
    # Stub for Day 10
    raise AuthenticationError("Login endpoint not yet implemented")


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db=Depends(get_db)):
    """
    Refresh access token using refresh token.
    Implemented in Day 10.
    """
    # Stub for Day 10
    raise AuthenticationError("Refresh endpoint not yet implemented")


@router.post("/auth/logout")
async def logout():
    """
    User logout endpoint.
    Implemented in Day 10.
    """
    return {"message": "Logout endpoint not yet implemented"}
