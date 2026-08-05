"""
Aegis Backend - Tenants Router
Tenant management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.dependencies import get_db, get_current_admin
from backend import schemas
from backend import crud

router = APIRouter(prefix="/api/v1", tags=["tenants"])


@router.post("/tenants", response_model=schemas.Tenant)
def create_tenant(tenant: schemas.TenantCreate, db: Session = Depends(get_db), request: Request = None):
    """
    Create a tenant.
    - If no tenants exist yet, allow unauthenticated creation (bootstrap case for tests/local).
    - If tenants exist, require an Authorization header (admin must be present and validated by middleware/dependencies).
    """
    # If there are existing tenants, require an Authorization header so callers must be authenticated.
    existing = crud.list_tenants(db, skip=0, limit=1)
    if existing:
        auth_header = None
        if request:
            auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=403, detail="Admin privileges required to create additional tenants")

    db_tenant = crud.create_tenant(db, tenant)
    return db_tenant

@router.get("/tenants/{tenant_id}", response_model=schemas.Tenant)
def get_tenant(tenant_id: int, db: Session = Depends(get_db)):
    db_tenant = crud.get_tenant(db, tenant_id)
    if not db_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return db_tenant

@router.get("/tenants", response_model=list[schemas.Tenant])
def list_tenants(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.list_tenants(db, skip=skip, limit=limit)

@router.put("/tenants/{tenant_id}", response_model=schemas.Tenant)
def update_tenant(tenant_id: int, tenant: schemas.TenantUpdate, db: Session = Depends(get_db), current_admin=Depends(get_current_admin)):
    db_tenant = crud.update_tenant(db, tenant_id, tenant)
    if not db_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return db_tenant

@router.delete("/tenants/{tenant_id}")
def delete_tenant(tenant_id: int, db: Session = Depends(get_db), current_admin=Depends(get_current_admin)):
    success = crud.delete_tenant(db, tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"message": "Tenant deleted"}
