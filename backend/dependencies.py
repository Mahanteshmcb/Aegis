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
import hashlib
from sqlalchemy.orm import Session

def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

BUILTIN_ROLE_PERMISSIONS = {
    "admin": {
        "admin.access", "roles.manage", "users.manage", "zones.manage",
        "devices.manage", "devices.control", "alerts.manage", "audit.read",
    },
    "superadmin": {
        "admin.access", "roles.manage", "users.manage", "zones.manage",
        "devices.manage", "devices.control", "alerts.manage", "audit.read",
    },
    "operator": {"devices.manage", "devices.control", "alerts.manage"},
    "auditor": {"audit.read"},
    "viewer": set(),
}
CUSTOM_ROLE_PERMISSIONS = {
    "users.manage", "zones.manage", "devices.manage", "devices.control",
    "alerts.manage", "audit.read",
}


def has_permission(user: Any, permission: str) -> bool:
    if isinstance(user, dict):
        permissions = user.get("permissions")
        role = user.get("role")
    else:
        permissions = getattr(user, "permissions", None)
        role = getattr(user, "role", None)
    if permissions is None:
        return permission in BUILTIN_ROLE_PERMISSIONS.get(role, set())
    return permission in permissions


def role_exists_for_tenant(db: Session, tenant_id: int, role_key: str) -> bool:
    if role_key in BUILTIN_ROLE_PERMISSIONS:
        return True
    return db.query(models_db.RoleDefinition.id).filter(
        models_db.RoleDefinition.tenant_id == tenant_id,
        models_db.RoleDefinition.key == role_key,
    ).first() is not None


def get_role_permissions(db: Session, tenant_id: int, role_key: str) -> set[str] | None:
    builtin = BUILTIN_ROLE_PERMISSIONS.get(role_key)
    if builtin is not None:
        return set(builtin)
    role = db.query(models_db.RoleDefinition).filter(
        models_db.RoleDefinition.tenant_id == tenant_id,
        models_db.RoleDefinition.key == role_key,
    ).first()
    return set(role.permissions or []) if role else None


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
        # Check session revocation status by token hash
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        try:
            session_row = db.query(models_db.Session).filter(models_db.Session.token_hash == token_hash).first()
        except Exception:
            session_row = None
        if session_row and session_row.revoked:
            raise credentials_exception

        permissions = get_role_permissions(db, user.tenant_id, user.role) or set()
            
        return {
            "id": user.id, 
            "tenant_id": user.tenant_id, 
            "role": user.role,
            "email": user.email,
            "permissions": sorted(permissions),
        }
    except (JWTError, ValueError) as e:
        print(f"Token Validation Error: {e}") # Optional: Helps with debugging in terminal
        raise credentials_exception

def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Verify the user has tenant-administration permission.
    """
    if not has_permission(current_user, "admin.access"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


def require_permission(permission: str):
    """Build a dependency that checks a permission resolved from the user's role."""
    def permission_dependency(current_user: dict = Depends(get_current_user)) -> dict:
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}",
            )
        return current_user

    return permission_dependency