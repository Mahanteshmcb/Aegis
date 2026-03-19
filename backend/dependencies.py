"""
Aegis Backend - FastAPI Dependencies
Reusable dependency injection components.
"""

from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from backend.config import settings
from backend.database import SessionLocal
from backend.exceptions import AuthenticationError


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(token: str = Depends(lambda: None)):
    """
    Get current authenticated user from JWT token.
    This is a stub - full implementation in Day 10.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if token is None:
        # Allow unauthenticated access for now
        return None
    
    try:
        # Token validation logic will be implemented in Day 10
        return {"user_id": "stub", "tenant_id": "stub"}
    except JWTError:
        raise credentials_exception


async def get_current_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Verify current user is an admin.
    This is a stub - full implementation in Day 10.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # Role check will be implemented in Day 10
    return current_user
