"""Tenant-scoped durable telemetry and local camera-media APIs."""
from datetime import datetime, timedelta
from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.config import settings
from backend.dependencies import get_current_user, get_db, require_permission
from backend.models.digital_twin import DigitalTwinDevice
from backend.models_db import DigitalTwinMedia, DigitalTwinTelemetry

router = APIRouter(prefix="/api/v1/digital-twin", tags=["digital-twin-history"])
ALLOWED_MEDIA_TYPES = {
    "image/jpeg", "image/png", "image/webp",
    "video/mp4", "video/webm", "video/quicktime",
}


def _media_path(storage_key: str) -> Path:
    try:
        canonical_key = str(uuid.UUID(storage_key))
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="Stored media key is invalid") from exc
    return Path(settings.digital_twin_media_dir).resolve() / canonical_key


def _get_device(db: Session, tenant_id: int, device_id: int) -> DigitalTwinDevice:
    device = db.query(DigitalTwinDevice).filter(
        DigitalTwinDevice.id == device_id,
        DigitalTwinDevice.tenant_id == tenant_id,
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.get("/devices/{device_id}/history")
def list_device_history(
    device_id: int,
    limit: int = Query(default=120, ge=1, le=1000),
    after: datetime | None = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = current_user["tenant_id"]
    device = _get_device(db, tenant_id, device_id)
    query = db.query(DigitalTwinTelemetry).filter(
        DigitalTwinTelemetry.tenant_id == tenant_id,
        DigitalTwinTelemetry.device_id == device.id,
    )
    if after is not None:
        query = query.filter(DigitalTwinTelemetry.recorded_at > after)
    rows = query.order_by(DigitalTwinTelemetry.recorded_at.desc()).limit(limit).all()
    return {
        "device_id": device.device_id,
        "data": [
            {"id": row.id, "recorded_at": row.recorded_at.isoformat(), "snapshot": row.snapshot}
            for row in reversed(rows)
        ],
    }


@router.get("/devices/{device_id}/media")
def list_device_media(
    device_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    device = _get_device(db, current_user["tenant_id"], device_id)
    rows = db.query(DigitalTwinMedia).filter(
        DigitalTwinMedia.tenant_id == current_user["tenant_id"],
        DigitalTwinMedia.device_id == device.id,
        DigitalTwinMedia.expires_at > datetime.utcnow(),
    ).order_by(DigitalTwinMedia.created_at.desc()).limit(100).all()
    return {"device_id": device.device_id, "data": [_media_metadata(row) for row in rows]}


def _media_metadata(media: DigitalTwinMedia) -> dict:
    return {
        "id": media.id,
        "device_id": media.device_id,
        "name": media.original_name,
        "content_type": media.content_type,
        "size_bytes": media.size_bytes,
        "created_at": media.created_at.isoformat(),
        "expires_at": media.expires_at.isoformat(),
        "content_url": f"/api/v1/digital-twin/media/{media.id}/content",
    }


@router.post("/devices/{device_id}/media", status_code=201)
async def upload_device_media(
    device_id: int,
    file: UploadFile = File(...),
    current_user=Depends(require_permission("devices.manage")),
    db: Session = Depends(get_db),
):
    device = _get_device(db, current_user["tenant_id"], device_id)
    if "camera" not in device.device_type.casefold():
        raise HTTPException(status_code=422, detail="Media can only be attached to a camera device")
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_MEDIA_TYPES:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG, WebP, MP4, WebM, and QuickTime media are accepted")

    root = Path(settings.digital_twin_media_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    storage_key = str(uuid.uuid4())
    target = _media_path(storage_key)
    temporary = target.with_suffix(".upload")
    total_size = 0
    try:
        with temporary.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                total_size += len(chunk)
                if total_size > settings.digital_twin_media_max_bytes:
                    raise HTTPException(status_code=413, detail="Uploaded media exceeds the configured size limit")
                output.write(chunk)
        if total_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded media is empty")
        temporary.replace(target)
        now = datetime.utcnow()
        media = DigitalTwinMedia(
            tenant_id=current_user["tenant_id"],
            device_id=device.id,
            storage_key=storage_key,
            original_name=Path(file.filename or "camera-media").name[:255],
            content_type=content_type,
            size_bytes=total_size,
            created_at=now,
            expires_at=now + timedelta(days=settings.digital_twin_media_retention_days),
        )
        db.add(media)
        from backend.audit_utils import record_actor_audit_event
        from backend.blockchain_connector import get_blockchain_connector
        record_actor_audit_event(
            db,
            current_user["tenant_id"],
            current_user,
            "camera_media_uploaded",
            "digital_twin_media",
            media.id,
            {
                "device_id": device.device_id,
                "name": media.original_name,
                "content_type": media.content_type,
                "size_bytes": media.size_bytes,
                "expires_at": media.expires_at.isoformat(),
            },
            blockchain=get_blockchain_connector(),
        )
        db.refresh(media)
        return _media_metadata(media)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        if target.exists():
            target.unlink()
        db.rollback()
        raise
    finally:
        await file.close()


@router.get("/media/{media_id}/content")
def download_device_media(
    media_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    media = db.query(DigitalTwinMedia).filter(
        DigitalTwinMedia.id == media_id,
        DigitalTwinMedia.tenant_id == current_user["tenant_id"],
        DigitalTwinMedia.expires_at > datetime.utcnow(),
    ).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found or expired")
    path = _media_path(media.storage_key)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Stored media file is missing")
    return FileResponse(
        path,
        media_type=media.content_type,
        filename=Path(media.original_name).name,
        content_disposition_type="attachment",
    )


@router.delete("/media/{media_id}", status_code=204)
def delete_device_media(
    media_id: int,
    current_user=Depends(require_permission("devices.manage")),
    db: Session = Depends(get_db),
):
    media = db.query(DigitalTwinMedia).filter(
        DigitalTwinMedia.id == media_id,
        DigitalTwinMedia.tenant_id == current_user["tenant_id"],
    ).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    path = _media_path(media.storage_key)
    if path.exists():
        path.unlink()
    db.delete(media)
    from backend.audit_utils import record_actor_audit_event
    from backend.blockchain_connector import get_blockchain_connector
    record_actor_audit_event(
        db,
        current_user["tenant_id"],
        current_user,
        "camera_media_deleted",
        "digital_twin_media",
        media.id,
        {"device_id": media.device_id, "name": media.original_name},
        blockchain=get_blockchain_connector(),
    )
