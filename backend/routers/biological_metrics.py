"""
Aegis Backend - Biological Metrics Router
Stores aggregated ML-derived crop health metrics and sensor fusion results.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.dependencies import get_db, get_current_user, get_current_admin
from backend import schemas
from backend.blockchain_connector import get_blockchain_connector
from backend.audit_utils import record_audit_event
from backend.models_db import BiologicalMetric, CropInstance, SpatialZone

router = APIRouter(prefix="/api/v1", tags=["Biological Metrics"])


def _record_biological_metric_audit(db: Session, tenant_id: int, event_type: str, metadata: Dict[str, Any]) -> None:
    blockchain = get_blockchain_connector()
    try:
        record_audit_event(db, blockchain, tenant_id, event_type, metadata)
    except Exception:
        pass


@router.post("/crops/{crop_id}/metrics", response_model=schemas.BiologicalMetricResponse)
async def create_biological_metric(
    crop_id: int,
    metric: schemas.BiologicalMetricCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    crop = (
        db.query(CropInstance)
        .join(SpatialZone)
        .filter(
            CropInstance.id == crop_id,
            SpatialZone.tenant_id == current_admin["tenant_id"],
        )
        .first()
    )
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found or tenant mismatch")

    db_metric = BiologicalMetric(crop_instance_id=crop_id, **metric.dict())
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)

    _record_biological_metric_audit(
        db,
        current_admin["tenant_id"],
        "biological_metric_recorded",
        {
            "crop_id": crop_id,
            "measurement_date": str(metric.measurement_date),
            "health_score": metric.health_score,
            "health_status": metric.health_status,
            "ndvi": metric.ndvi,
            "recommendations": metric.recommendations,
        },
    )

    return db_metric


@router.get("/crops/{crop_id}/metrics", response_model=List[schemas.BiologicalMetricResponse])
async def list_biological_metrics(
    crop_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    crop = (
        db.query(CropInstance)
        .join(SpatialZone)
        .filter(
            CropInstance.id == crop_id,
            SpatialZone.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found or tenant mismatch")

    metrics = (
        db.query(BiologicalMetric)
        .filter(BiologicalMetric.crop_instance_id == crop_id)
        .order_by(BiologicalMetric.measurement_date.desc())
        .limit(limit)
        .all()
    )
    return metrics
