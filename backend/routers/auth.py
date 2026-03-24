"""
Aegis Backend - Authentication Router
Login, token refresh, user management.
"""


from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt, JWTError
from backend.dependencies import get_db
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
    """
    Register a new user (tenant-scoped).
    """
    import hashlib
    try:
        user = crud.create_user(db, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # Audit log for user creation
    user_data = f"email={user.email}|tenant_id={user.tenant_id}|role={user.role}"
    data_hash = hashlib.sha256(user_data.encode()).hexdigest()
    audit = schemas.AuditLogCreate(
        sensor_id=0,  # Not applicable for user creation
        event_type="user_created",
        data_hash=data_hash,
        blockchain_tx=None,
    )
    try:
        crud.create_audit_log(db, audit)
    except Exception:
        pass  # Do not block user creation if audit log fails
    return schemas.UserRead.from_orm(user)


@router.post("/auth/login", response_model=TokenResponse)
def login(request: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    User login endpoint.
    Returns access and refresh tokens.
    """
    user = crud.authenticate_user(db, request.email, request.password)
    if not user:
        raise AuthenticationError("Invalid email or password")
    # Token payload includes user_id, tenant_id, and role for RBAC/tenant isolation
    payload = {"sub": str(user.id), "tenant_id": user.tenant_id, "role": user.role}
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)



@router.post("/auth/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    """
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
    """
    User logout endpoint (stateless JWT, client-side only).
    """
    return {"message": "Logout successful (stateless JWT)"}
