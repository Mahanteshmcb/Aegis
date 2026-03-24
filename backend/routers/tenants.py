"""
Aegis Backend - Tenants Router
Tenant management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.dependencies import get_db
from backend import schemas
from backend import crud

router = APIRouter(prefix="/api/v1", tags=["tenants"])

@router.post("/tenants", response_model=schemas.Tenant)
def create_tenant(tenant: schemas.TenantCreate, db: Session = Depends(get_db)):
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
