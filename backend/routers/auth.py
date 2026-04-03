"""
Aegis Backend - Authentication Router
Login, token refresh, user management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
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
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=settings.jwt_refresh_token_expire_days))
    to_encode.update({"exp": expire})
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
        crud.create_audit_log(db, audit)
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
            crud.create_audit_log(db, audit)
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
    user = crud.authenticate_user(db, email, password)
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