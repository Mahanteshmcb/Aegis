"""
Aegis Backend - Authentication Router
Login, token refresh, user management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from typing import Optional

from backend.dependencies import get_db, get_current_user
from backend.exceptions import AuthenticationError
from backend import crud, schemas
from backend.config import settings

router = APIRouter(prefix="/api/v1", tags=["auth"])

class TokenResponse(schemas.BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(schemas.BaseModel):
    refresh_token: str

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
    import hashlib
    try:
        user = crud.create_user(db, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    user_data = f"email={user.email}|tenant_id={user.tenant_id}|role={user.role}"
    data_hash = hashlib.sha256(user_data.encode()).hexdigest()
    
    audit = schemas.AuditLogCreate(
        event_type="user_created",
        data_hash=data_hash,
        blockchain_tx=None,
    )
    
    try:
        crud.create_audit_log(db, audit, tenant_id=user.tenant_id)
    except Exception:
        pass 
        
    return schemas.UserRead.from_orm(user)

@router.post("/auth/signup", response_model=schemas.UserRead)
def signup(request: RegisterRequest, db: Session = Depends(get_db)):
    """Alias for register endpoint to support frontend signup."""
    return register(request, db)

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
        import hashlib
        user_hash = hashlib.sha256(f"reset={email}".encode()).hexdigest()
        audit = schemas.AuditLogCreate(
            event_type="password_reset_requested",
            data_hash=user_hash,
            blockchain_tx=None,
        )
        try:
            crud.create_audit_log(db, audit, tenant_id=user.tenant_id)
        except Exception:
            pass

    return {"message": "If the email exists, password reset instructions have been issued."}

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
    try:
        import hashlib as _hashlib
        from backend import crud as _crud
        from datetime import datetime
        # Compute token hash and expiry
        token_hash = _hashlib.sha256(access_token.encode()).hexdigest()
        # decode to get exp
        payload_decoded = jwt.decode(access_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        exp_ts = payload_decoded.get("exp")
        expires_at = datetime.utcfromtimestamp(exp_ts) if exp_ts else None
        try:
            _crud.create_session(db, user.tenant_id, user.id, token_hash, token_type="access", expires_at=expires_at)
        except Exception:
            pass
    except Exception:
        pass

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
    )

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
def logout():
    """User logout endpoint."""
    return {"message": "Logout successful (stateless JWT)"}

# === Day 19: RBAC User Management ===
from backend.dependencies import get_current_admin

@router.get("/users")
def list_users(current_user=Depends(get_current_admin), db: Session = Depends(get_db)):
    """
    List all users in the current tenant (admin only).
    Returns user list with roles for admin panel.
    """
    from backend.dependencies import get_current_admin
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
def list_users_auth(current_user=Depends(get_current_admin), db: Session = Depends(get_db)):
    """
    List all users in the current tenant (admin only) - /auth path.
    Returns user list with roles for admin panel.
    """
    from backend.dependencies import get_current_admin
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
    current_user=Depends(get_current_admin),
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
    if role not in ["admin", "auditor", "operator", "viewer"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be: admin, auditor, operator, or viewer")
    
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
    
    # Audit log
    import hashlib
    user_data = f"email={new_user.email}|tenant_id={new_user.tenant_id}|role={new_user.role}"
    data_hash = hashlib.sha256(user_data.encode()).hexdigest()
    
    audit = schemas.AuditLogCreate(
        event_type="user_created_by_admin",
        data_hash=data_hash,
        blockchain_tx=None,
    )
    
    try:
        crud.create_audit_log(db, audit, tenant_id=current_user["tenant_id"])
    except Exception:
        pass
    
    return {
        "id": new_user.id,
        "email": new_user.email,
        "role": new_user.role,
        "tenant_id": new_user.tenant_id,
        "message": f"User {new_user.email} created successfully"
    }

from fastapi import Body


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    body: dict = Body(...),
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update a user's role (admin only, within same tenant).
    Prevents privilege escalation by verifying tenant ownership.
    """
    new_role = body.get("role")

    if not new_role or new_role not in ["admin", "viewer", "auditor", "operator"]:
        raise HTTPException(status_code=400, detail="Invalid role")

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
    updated_user = crud.update_user_role(db, user_id, new_role)

    return {
        "id": updated_user.id,
        "email": updated_user.email,
        "role": updated_user.role,
        "message": f"User role updated to {new_role}"
    }

@router.delete("/users/{user_id}")
def delete_user_endpoint(
    user_id: int,
    current_user=Depends(get_current_admin),
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
    
    success = crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user")
    
    return {"message": f"User {user.email} deleted successfully"}