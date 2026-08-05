from datetime import datetime
from io import StringIO
import csv
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from backend.dependencies import get_current_user, get_db
from backend import crud, schemas
from backend import playback_engine

router = APIRouter(prefix="/api/v1/telemetry", tags=["Telemetry Playback"])


@router.post("/playbacks")
async def create_playback(payload: schemas.TelemetryPlaybackCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        session = crud.create_playback_session(db, current_user["tenant_id"], current_user["id"], payload.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "success", "data": {"id": session.id, "name": session.name}}


@router.get("/playbacks")
async def list_playbacks(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = crud.list_playback_sessions(db, current_user["tenant_id"])
    out = []
    for s in sessions:
        out.append({
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "start_time": s.start_time.isoformat(),
            "end_time": s.end_time.isoformat(),
            "status": s.status,
            "playback_speed": s.playback_speed,
            "filters": s.filters,
            "recurring": s.recurring,
            "schedule_cron": s.schedule_cron,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
        })
    return {"status": "success", "data": out}


@router.get("/playbacks/{session_id}")
async def get_playback(session_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    session = crud.get_playback_session(db, current_user["tenant_id"], session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Playback session not found")
    return {
        "status": "success",
        "data": {
            "id": session.id,
            "name": session.name,
            "description": session.description,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat(),
            "status": session.status,
            "playback_speed": session.playback_speed,
            "filters": session.filters,
            "recurring": session.recurring,
            "schedule_cron": session.schedule_cron,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }
    }


@router.patch("/playbacks/{session_id}")
async def update_playback(session_id: int, payload: schemas.TelemetryPlaybackUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    session = crud.get_playback_session(db, current_user["tenant_id"], session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Playback session not found")
    updated = crud.update_playback_session(db, session, payload.dict(exclude_unset=True))
    return {
        "status": "success",
        "data": {
            "id": updated.id,
            "name": updated.name,
            "description": updated.description,
            "start_time": updated.start_time.isoformat(),
            "end_time": updated.end_time.isoformat(),
            "status": updated.status,
            "playback_speed": updated.playback_speed,
            "filters": updated.filters,
            "recurring": updated.recurring,
            "schedule_cron": updated.schedule_cron,
            "created_at": updated.created_at.isoformat(),
            "updated_at": updated.updated_at.isoformat(),
        }
    }


@router.post("/playbacks/{session_id}/pause")
async def pause_playback(session_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    session = crud.get_playback_session(db, current_user["tenant_id"], session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Playback session not found")
    playback_engine.pause_playback(session.id)
    session = crud.update_playback_status(db, session, "paused")
    return {"status": "success", "data": {"id": session.id, "status": session.status}}


@router.post("/playbacks/{session_id}/resume")
async def resume_playback(session_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    session = crud.get_playback_session(db, current_user["tenant_id"], session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Playback session not found")
    playback_engine.resume_playback(session.id, current_user["tenant_id"], session.start_time, session.end_time, session.playback_speed)
    session = crud.update_playback_status(db, session, "running")
    return {"status": "success", "data": {"id": session.id, "status": session.status}}


@router.post("/playbacks/{session_id}/start")
async def start_playback(session_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    session = crud.get_playback_session(db, current_user["tenant_id"], session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Playback session not found")
    # Mark status and start background playback task
    session = crud.update_playback_status(db, session, "running")
    # start engine
    playback_engine.start_playback(session.id, current_user["tenant_id"], session.start_time, session.end_time, session.playback_speed)
    return {"status": "success", "data": {"id": session.id, "status": session.status}}


@router.post("/playbacks/{session_id}/stop")
async def stop_playback(session_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    session = crud.get_playback_session(db, current_user["tenant_id"], session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Playback session not found")
    # stop engine and mark stopped
    playback_engine.stop_playback(session.id)
    session = crud.update_playback_status(db, session, "stopped")
    return {"status": "success", "data": {"id": session.id, "status": session.status}}


@router.get("/playbacks/{session_id}/export")
async def export_playback(session_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    session = crud.get_playback_session(db, current_user["tenant_id"], session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Playback session not found")

    rows = crud.export_playback_sensor_data(db, current_user["tenant_id"], session.start_time, session.end_time)

    # Create CSV
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["timestamp", "sensor_id", "value", "unit"])
    for r in rows:
        writer.writerow([r.timestamp.isoformat(), r.sensor_id, r.value, r.unit])
    csv_bytes = si.getvalue().encode("utf-8")
    return Response(content=csv_bytes, media_type="text/csv")
