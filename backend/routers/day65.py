from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import StringIO
import csv
from datetime import datetime

from backend.dependencies import get_current_admin, get_db
from backend import crud, schemas

router = APIRouter(prefix="/api/v1", tags=["day65"])


@router.get("/audit/export")
def export_audit_logs(start: str | None = None, end: str | None = None, event_type: str | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    """Export audit logs as CSV for tenant. Date format: ISO 8601."""
    start_ts = datetime.fromisoformat(start) if start else None
    end_ts = datetime.fromisoformat(end) if end else None
    logs = crud.export_audit_logs(db, current_user["tenant_id"], start_ts, end_ts, event_type)

    def gen():
        w = csv.writer(StringIO())
        buf = StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "tenant_id", "sensor_id", "event_type", "data_hash", "blockchain_tx", "created_at"])
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate(0)
        for l in logs:
            writer.writerow([l.id, l.tenant_id, l.sensor_id, l.event_type, l.data_hash or "", l.blockchain_tx or "", l.created_at.isoformat()])
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)

    return StreamingResponse(gen(), media_type="text/csv")


@router.get("/sessions")
def list_sessions(db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    sessions = crud.list_sessions_by_tenant(db, current_user["tenant_id"])
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "token_type": s.token_type,
            "expires_at": s.expires_at.isoformat() if s.expires_at else None,
            "revoked": s.revoked,
            "created_at": s.created_at.isoformat(),
        }
        for s in sessions
    ]


@router.post("/sessions/{session_id}/revoke")
def revoke_session_endpoint(session_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    ok = crud.revoke_session(db, session_id, current_user["tenant_id"])
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session revoked"}


@router.post("/sensors/bulk_import")
async def sensors_bulk_import(file: UploadFile = File(...), db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    """Accept CSV file to bulk import sensors. CSV headers: name,type,location,zone_id"""
    content = (await file.read()).decode("utf-8")
    reader = csv.DictReader(StringIO(content))
    sensors = []
    for row in reader:
        sensors.append({
            "name": row.get("name"),
            "type": row.get("type"),
            "location": row.get("location"),
            "zone_id": int(row.get("zone_id")) if row.get("zone_id") else None,
        })
    summary = crud.bulk_import_sensors(db, current_user["tenant_id"], sensors)
    return {"summary": summary}
