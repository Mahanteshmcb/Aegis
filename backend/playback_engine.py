"""Simple telemetry playback engine: queries sensor_data and emits via realtime.sio
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict

from backend.database import SessionLocal
from backend import models_db
from backend import realtime

logger = logging.getLogger(__name__)

# Map of session_id -> asyncio.Task
_playback_tasks: Dict[int, asyncio.Task] = {}
# Map of session_id -> playback state for pause/resume
_playback_states: Dict[int, dict] = {}


def _make_payload(row: models_db.SensorData):
    return {
        "sensor_id": f"{row.sensor_id}",
        "value": row.value,
        "unit": row.unit,
        "timestamp": row.timestamp.isoformat(),
    }


async def _run_playback(
    session_id: int,
    tenant_id: int,
    start_time: datetime,
    end_time: datetime,
    playback_speed: float,
    resume_index: int = 0,
):
    logger.info("Starting playback task %s", session_id)
    state = _playback_states.setdefault(session_id, {
        "tenant_id": tenant_id,
        "start_time": start_time,
        "end_time": end_time,
        "playback_speed": playback_speed,
        "next_index": resume_index,
        "clear_on_cancel": True,
    })
    try:
        db = SessionLocal()
        try:
            rows = (
                db.query(models_db.SensorData)
                .join(models_db.Sensor)
                .filter(models_db.Sensor.tenant_id == tenant_id)
                .filter(models_db.SensorData.timestamp >= start_time)
                .filter(models_db.SensorData.timestamp <= end_time)
                .order_by(models_db.SensorData.timestamp)
                .all()
            )
        finally:
            db.close()

        rows = rows[resume_index:]
        if not rows:
            logger.info("No sensor data for playback %s", session_id)
            return

        prev_ts = None
        for row_index, r in enumerate(rows, start=resume_index):
            if prev_ts is not None:
                delta = (r.timestamp - prev_ts).total_seconds()
                wait = max(0.0, delta / max(0.0001, playback_speed))
                await asyncio.sleep(wait)
            payload = _make_payload(r)
            await realtime.sio.emit("sensor:reading", payload)
            prev_ts = r.timestamp
            state["next_index"] = row_index + 1

    except asyncio.CancelledError:
        logger.info("Playback %s cancelled", session_id)
        raise
    except Exception:
        logger.exception("Playback %s failed", session_id)
    finally:
        _playback_tasks.pop(session_id, None)
        if state.get("clear_on_cancel", True):
            _playback_states.pop(session_id, None)
        logger.info("Playback task %s finished", session_id)


def start_playback(session_id: int, tenant_id: int, start_time: datetime, end_time: datetime, playback_speed: float):
    if session_id in _playback_tasks:
        logger.info("Playback %s already running", session_id)
        return
    state = {
        "tenant_id": tenant_id,
        "start_time": start_time,
        "end_time": end_time,
        "playback_speed": playback_speed,
        "next_index": 0,
        "clear_on_cancel": True,
    }
    _playback_states[session_id] = state
    loop = asyncio.get_event_loop()
    task = loop.create_task(_run_playback(session_id, tenant_id, start_time, end_time, playback_speed, resume_index=0))
    _playback_tasks[session_id] = task
    logger.info("Scheduled playback task %s", session_id)


def pause_playback(session_id: int):
    task = _playback_tasks.get(session_id)
    if not task:
        return
    state = _playback_states.get(session_id)
    if state is not None:
        state["clear_on_cancel"] = False
    task.cancel()


def resume_playback(session_id: int, tenant_id: int, start_time: datetime, end_time: datetime, playback_speed: float):
    if session_id in _playback_tasks:
        logger.info("Playback %s already running", session_id)
        return
    state = _playback_states.get(session_id)
    resume_index = 0
    if state is not None:
        resume_index = state.get("next_index", 0)
    state = {
        "tenant_id": tenant_id,
        "start_time": start_time,
        "end_time": end_time,
        "playback_speed": playback_speed,
        "next_index": resume_index,
        "clear_on_cancel": True,
    }
    _playback_states[session_id] = state
    loop = asyncio.get_event_loop()
    task = loop.create_task(_run_playback(session_id, tenant_id, start_time, end_time, playback_speed, resume_index=resume_index))
    _playback_tasks[session_id] = task
    logger.info("Resumed playback task %s from index %s", session_id, resume_index)


def stop_playback(session_id: int):
    task = _playback_tasks.get(session_id)
    if not task:
        return
    state = _playback_states.get(session_id)
    if state is not None:
        state["clear_on_cancel"] = True
    task.cancel()


def is_running(session_id: int) -> bool:
    t = _playback_tasks.get(session_id)
    return t is not None and not t.done()
