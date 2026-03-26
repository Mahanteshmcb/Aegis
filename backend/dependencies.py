"""
Aegis Backend - FastAPI Dependencies
Reusable dependency injection components.
"""

from typing import Generator, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from backend.config import settings
from backend.database import SessionLocal
from backend import models_db

def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token.
    Returns a dictionary for compatibility with router logic.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        sub_value: str = payload.get("sub")
        tenant_id: int = payload.get("tenant_id")
        
        if sub_value is None or tenant_id is None:
            raise credentials_exception
            
        # FIX: Check if the sub claim is an email or an ID to prevent ValueError crashes
        if "@" in str(sub_value):
            user = db.query(models_db.User).filter(
                models_db.User.email == sub_value, 
                models_db.User.tenant_id == tenant_id
            ).first()
        else:
            user = db.query(models_db.User).filter(
                models_db.User.id == int(sub_value), 
                models_db.User.tenant_id == tenant_id
            ).first()
        
        if not user:
            raise credentials_exception
            
        return {
            "id": user.id, 
            "tenant_id": user.tenant_id, 
            "role": user.role,
            "email": user.email
        }
    except (JWTError, ValueError) as e:
        print(f"Token Validation Error: {e}") # Optional: Helps with debugging in terminal
        raise credentials_exception

def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Verify current user is an admin (RBAC).
    """
    if current_user["role"] not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user