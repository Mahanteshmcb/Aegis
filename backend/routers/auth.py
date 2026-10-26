"""
Aegis Backend - Authentication Router
Login, token refresh, user management.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from typing import Optional

logger = logging.getLogger(__name__)

from backend.dependencies import (
    BUILTIN_ROLE_PERMISSIONS,
    get_db,
    get_current_user,
    get_role_permissions,
    has_permission,
    require_permission,
    role_exists_for_tenant,
)
from backend.exceptions import AuthenticationError
from backend import crud, schemas
from backend.config import settings
from backend.audit_utils import record_actor_audit_event, record_audit_event
from backend.blockchain_connector import get_blockchain_connector
from backend.models_db import AuditLog, Session as AuthSession

router = APIRouter(prefix="/api/v1", tags=["auth"])


def _record_user_action(db: Session, actor: dict, event_type: str, user, details: dict | None = None):
    return record_actor_audit_event(
        db,
        actor["tenant_id"],
        actor,
        event_type,
        "user",
        user.id,
        {"target_email": user.email, **(details or {})},
        blockchain=get_blockchain_connector(),
    )

class TokenResponse(schemas.BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(schemas.BaseModel):
    refresh_token: str


class ChangePasswordRequest(schemas.BaseModel):
    current_password: str
    new_password: str

class RegisterRequest(schemas.UserCreate):
    pass

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=settings.jwt_refresh_token_expire_days))
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

@router.post("/auth/register", response_model=schemas.UserRead)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user (tenant-scoped)."""
    if settings.environment == "prod":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-registration is disabled. Contact your tenant administrator.",
        )
    try:
        user = crud.create_user(db, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    _record_user_action(
        db,
        {"id": user.id, "email": user.email, "tenant_id": user.tenant_id},
        "user_created",
        user,
        {"role": user.role, "registration": "self_service"},
    )

    return schemas.UserRead.from_orm(user)

@router.post("/auth/signup", response_model=schemas.UserRead)
def signup(request: RegisterRequest, db: Session = Depends(get_db)):
    """Self-service registration always creates a least-privilege viewer."""
    return register(request.model_copy(update={"role": "viewer"}), db)

@router.post("/auth/reset-password")
async def reset_password(request: Request, db: Session = Depends(get_db)):
    """Accept a reset request and return a neutral success response."""
    try:
        body = await request.json()
        email = body.get("email")
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request format")

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required")

    user = crud.get_user_by_email(db, email)
    if user:
        # In Phase 1 we do not send real email, but log the intent for audit.
        try:
            record_audit_event(db, None, user.tenant_id, "password_reset_requested", {
                "action": "password_reset_requested",
                "actor_user_id": None,
                "actor_email": None,
                "entity_type": "user",
                "entity_id": str(user.id),
                "outcome": "accepted",
                "target_email": user.email,
                "delivery_configured": False,
                "user_agent": request.headers.get("user-agent"),
                "client_ip": request.client.host if request.client else None,
            })
        except Exception:
            logger.exception("Failed to write password_reset_requested audit log for tenant %s", user.tenant_id)

    return {"message": "If the account exists, the reset request was recorded. Contact your tenant administrator to complete the reset."}

@router.post("/auth/login", response_model=TokenResponse)
async def login(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Sovereign Login: Handles both Form Data (Swagger) and JSON (Frontend) 
    manually to avoid Pydantic validation 422 errors.
    """
    email = None
    password = None
    content_type = request.headers.get("Content-Type", "")

    # 1. Handle Swagger / OAuth2 Form Data
    if "application/x-www-form-urlencoded" in content_type:
        form_data = await request.form()
        email = str(form_data.get("username") or "")  # Swagger field is 'username'
        password = str(form_data.get("password") or "")
    
    # 2. Handle Frontend JSON Data
    else:
        try:
            body = await request.json()
            email = str(body.get("email") or "")
            password = str(body.get("password") or "")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Invalid request format"
            )

        if not email or not password:
            raise AuthenticationError("Missing email or password")

    # Authenticate via CRUD
    try:
        user = crud.authenticate_user(db, email, password)
    except Exception as e:
        # If the DB isn't initialized (no tables), attempt to initialize and retry once.
        err_str = str(e).lower()
        if "no such table" in err_str or "operationalerror" in e.__class__.__name__.lower():
            try:
                from backend.database import init_db
                init_db()
                user = crud.authenticate_user(db, email, password)
            except Exception as e2:
                raise HTTPException(status_code=500, detail=f"Authentication backend error: {str(e2)}")
        else:
            # Defensive: map unexpected errors to 500 with clear message
            raise HTTPException(status_code=500, detail=f"Authentication backend error: {str(e)}")

    if not user:
        raise AuthenticationError("Invalid email or password")

    # Token payload
    payload = {
        "sub": user.email, 
        "tenant_id": user.tenant_id, 
        "role": user.role
    }
    
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    # Record session for revocation support
    session_row = None
    try:
        import hashlib as _hashlib
        # Compute token hash and expiry
        token_hash = _hashlib.sha256(access_token.encode()).hexdigest()
        # decode to get exp
        payload_decoded = jwt.decode(access_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        exp_ts = payload_decoded.get("exp")
        expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc) if exp_ts else None
        session_row = crud.create_session(db, user.tenant_id, user.id, token_hash, token_type="access", expires_at=expires_at)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to persist login session for user %s", user.id)
        raise HTTPException(status_code=500, detail="Failed to persist login session") from exc

    try:
        login_time = datetime.now(timezone.utc)
        record_audit_event(db, get_blockchain_connector(), user.tenant_id, "login_success", {
            "action": "login",
            "actor_user_id": user.id,
            "actor_email": user.email,
            "entity_type": "session",
            "entity_id": str(session_row.id) if session_row else None,
            "outcome": "success",
            "timestamp": login_time.isoformat(),
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None,
        })
    except Exception as exc:
        logger.exception("Failed to write login_success audit log for tenant %s", user.tenant_id)
        raise HTTPException(status_code=500, detail="Failed to record login audit event") from exc

    return TokenResponse(
        access_token=access_token, 
        refresh_token=refresh_token, 
        token_type="bearer"
    )

@router.get("/auth/me", response_model=schemas.UserProfile)
def get_current_user_profile(current_user=Depends(get_current_user)):
    """Return the current authenticated user's profile."""
    return schemas.UserProfile(
        id=current_user["id"],
        email=current_user["email"],
        role=current_user["role"],
        tenant_id=current_user["tenant_id"],
        permissions=current_user.get("permissions", []),
    )


@router.post("/auth/change-password")
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from passlib.hash import bcrypt
    from backend.models_db import Session as UserSession

    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    user = crud.get_user_by_id(db, current_user["id"])
    if not user or user.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=404, detail="User not found")
    if not bcrypt.verify(request.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if bcrypt.verify(request.new_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="New password must differ from current password")

    user.hashed_password = bcrypt.hash(request.new_password)
    db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.tenant_id == user.tenant_id,
        UserSession.revoked.is_(False),
    ).update({UserSession.revoked: True}, synchronize_session=False)
    db.add(user)
    db.commit()

    _record_user_action(
        db,
        current_user,
        "password_changed",
        user,
        {"revoked_sessions": True},
    )

    return {"message": "Password changed. Sign in again to refresh your sessions."}

@router.post("/auth/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    try:
        payload = jwt.decode(request.refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        role = payload.get("role")
        if not user_id or not tenant_id:
            raise AuthenticationError("Invalid refresh token")
        new_payload = {"sub": user_id, "tenant_id": tenant_id, "role": role}
        access_token = create_access_token(new_payload)
        refresh_token = create_refresh_token(new_payload)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
    except JWTError:
        raise AuthenticationError("Invalid refresh token")

@router.post("/auth/logout")
def logout(request: Request, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Revoke the current access token and record the session duration."""
    import hashlib

    authorization = request.headers.get("Authorization", "")
    token = authorization.partition(" ")[2].strip()
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session_row = db.query(AuthSession).filter(AuthSession.token_hash == token_hash).first()
    duration_seconds = None
    if session_row and session_row.tenant_id == current_user["tenant_id"]:
        session_row.revoked = True
        duration_seconds = max(0, int((datetime.utcnow() - session_row.created_at).total_seconds()))
        db.commit()

    record_audit_event(db, get_blockchain_connector(), current_user["tenant_id"], "user_logout", {
        "action": "logout",
        "actor_user_id": current_user["id"],
        "actor_email": current_user["email"],
        "entity_type": "session",
        "entity_id": str(session_row.id) if session_row else None,
        "outcome": "success",
        "session_duration_seconds": duration_seconds,
        "user_agent": request.headers.get("user-agent"),
        "client_ip": request.client.host if request.client else None,
    })
    return {"message": "Logout successful", "session_duration_seconds": duration_seconds}

# === Day 19: RBAC User Management ===
@router.get("/users")
def list_users(current_user=Depends(require_permission("users.manage")), db: Session = Depends(get_db)):
    """
    List all users in the current tenant (admin only).
    Returns user list with roles for admin panel.
    """
    users = crud.list_users_by_tenant(db, current_user["tenant_id"])
    return [
        {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "tenant_id": user.tenant_id,
            "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') else None,
        }
        for user in users
    ]

@router.get("/auth/users")
def list_users_auth(current_user=Depends(require_permission("users.manage")), db: Session = Depends(get_db)):
    """
    List all users in the current tenant (admin only) - /auth path.
    Returns user list with roles for admin panel.
    """
    users = crud.list_users_by_tenant(db, current_user["tenant_id"])
    return [
        {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "tenant_id": user.tenant_id,
            "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') else None,
        }
        for user in users
    ]

@router.post("/auth/users")
async def create_user_endpoint(
    request: Request,
    current_user=Depends(require_permission("users.manage")),
    db: Session = Depends(get_db)
):
    """
    Create a new user (admin only, within same tenant).
    Expects: {"email": "user@example.com", "password": "password123", "role": "operator"}
    """
    try:
        body = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid request format")
    
    if not body:
        raise HTTPException(status_code=400, detail="Invalid request format")
    
    email = body.get("email", "").strip().lower()
    password = body.get("password", "").strip()
    role = body.get("role", "operator")
    
    # Validation
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    if not password:
        raise HTTPException(status_code=400, detail="Password is required")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if not role_exists_for_tenant(db, current_user["tenant_id"], role):
        raise HTTPException(status_code=400, detail="Role is not defined for this tenant")
    if role == "superadmin" and current_user.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="Only a superadmin can assign the superadmin role")
    if role == "admin" and not has_permission(current_user, "admin.access"):
        raise HTTPException(status_code=403, detail="Only an administrator can assign the admin role")
    _ensure_assignable_role(db, current_user, role)
    
    # Check if user exists
    existing_user = crud.get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(status_code=400, detail=f"User with email {email} already exists")
    
    # Create user
    try:
        user_create = schemas.UserCreate(
            email=email,
            password=password,
            role=role,
            tenant_id=current_user["tenant_id"]
        )
        new_user = crud.create_user(db, user_create)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
    
    _record_user_action(
        db,
        current_user,
        "user_created_by_admin",
        new_user,
        {"role": new_user.role},
    )
    
    return {
        "id": new_user.id,
        "email": new_user.email,
        "role": new_user.role,
        "tenant_id": new_user.tenant_id,
        "message": f"User {new_user.email} created successfully"
    }

from fastapi import Body


def _ensure_assignable_role(db: Session, current_user: dict, role_key: str):
    current_permissions = set(
        current_user.get("permissions")
        or BUILTIN_ROLE_PERMISSIONS.get(current_user.get("role"), set())
    )
    role_permissions = get_role_permissions(db, current_user["tenant_id"], role_key)
    if role_permissions is None or not role_permissions.issubset(current_permissions):
        raise HTTPException(status_code=403, detail="Cannot assign a role with permissions you do not hold")


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    body: dict = Body(...),
    current_user=Depends(require_permission("users.manage")),
    db: Session = Depends(get_db)
):
    """
    Update a user's role (admin only, within same tenant).
    Prevents privilege escalation by verifying tenant ownership.
    """
    new_role = body.get("role")

    if not new_role or not role_exists_for_tenant(db, current_user["tenant_id"], new_role):
        raise HTTPException(status_code=400, detail="Role is not defined for this tenant")
    if new_role == "superadmin" and current_user.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="Only a superadmin can assign the superadmin role")
    if new_role == "admin" and not has_permission(current_user, "admin.access"):
        raise HTTPException(status_code=403, detail="Only an administrator can assign the admin role")
    _ensure_assignable_role(db, current_user, new_role)

    # Get target user
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify same tenant (security)
    if user.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Cannot modify users from other tenants")

    # Prevent self-demotion
    if user_id == current_user.get("id") and new_role != "admin":
        raise HTTPException(status_code=400, detail="Cannot remove your own admin privileges")

    # Update role
    previous_role = user.role
    updated_user = crud.update_user_role(db, user_id, new_role)
    _record_user_action(
        db,
        current_user,
        "user_role_changed",
        updated_user,
        {"previous_role": previous_role, "new_role": new_role},
    )

    return {
        "id": updated_user.id,
        "email": updated_user.email,
        "role": updated_user.role,
        "message": f"User role updated to {new_role}"
    }

@router.delete("/users/{user_id}")
def delete_user_endpoint(
    user_id: int,
    current_user=Depends(require_permission("users.manage")),
    db: Session = Depends(get_db)
):
    """
    Delete a user (admin only, within same tenant).
    """
    # Get target user
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify same tenant
    if user.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Cannot delete users from other tenants")
    
    # Prevent self-deletion
    if user_id == current_user.get("id"):
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    deleted_user_email = user.email
    deleted_user_role = user.role
    deleted_sessions = db.query(AuthSession).filter(
        AuthSession.user_id == user_id,
        AuthSession.tenant_id == current_user["tenant_id"],
    ).count()
    db.query(AuthSession).filter(
        AuthSession.user_id == user_id,
        AuthSession.tenant_id == current_user["tenant_id"],
    ).delete(synchronize_session=False)
    db.query(AuditLog).filter(AuditLog.actor_user_id == user_id).update(
        {AuditLog.actor_user_id: None},
        synchronize_session=False,
    )
    db.delete(user)
    record_actor_audit_event(
        db,
        current_user["tenant_id"],
        current_user,
        "user_deleted",
        "user",
        user_id,
        {
            "target_email": deleted_user_email,
            "previous_role": deleted_user_role,
            "revoked_sessions": deleted_sessions,
        },
        blockchain=get_blockchain_connector(),
    )
    return {"message": f"User {deleted_user_email} deleted successfully"}