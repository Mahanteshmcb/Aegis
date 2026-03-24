"""
Aegis Backend - FastAPI Dependencies
Reusable dependency injection components.
"""


from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from backend.config import settings
from backend.database import SessionLocal
from backend.exceptions import AuthenticationError
from backend import crud, models_db


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get current authenticated user from JWT token.
    Enforces tenant isolation and RBAC.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        role = payload.get("role")
        if user_id is None or tenant_id is None:
            raise credentials_exception
        user = db.query(models_db.User).filter(models_db.User.id == int(user_id), models_db.User.tenant_id == tenant_id).first()
        if not user:
            raise credentials_exception
        return {"user_id": user.id, "tenant_id": user.tenant_id, "role": user.role}
    except JWTError:
        raise credentials_exception



def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Verify current user is an admin (RBAC).
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    if current_user["role"] not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user
