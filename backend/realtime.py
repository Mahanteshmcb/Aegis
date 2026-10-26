"""Tenant-scoped Socket.IO transport for persisted digital-twin state."""
import asyncio
import logging

import socketio
from jose import JWTError, jwt

from backend.config import settings

logger = logging.getLogger(__name__)

# Do not emit Socket.IO CORS headers here; FastAPI's CORSMiddleware handles CORS for the mounted route.
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=["http://localhost:3000", "http://localhost:8001", "*"])
# Mounting the Socket.IO ASGI app at /socket.io means the inner app receives the remaining
# path after the mount point is stripped. Use '/' here so the mounted root path resolves correctly.
sio_app = socketio.ASGIApp(sio, socketio_path='/')

_emit_tasks = []


def tenant_room(tenant_id: int) -> str:
    return f"tenant:{tenant_id}"


def _tenant_id_from_auth(auth) -> int | None:
    token = auth.get("token") if isinstance(auth, dict) else None
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        tenant_id = payload.get("tenant_id")
        return int(tenant_id) if tenant_id is not None else None
    except (JWTError, TypeError, ValueError):
        return None


async def emit_tenant_event(event: str, payload: dict, tenant_id: int | None = None) -> None:
    """Keep tenant-owned realtime data inside its authenticated tenant room."""
    if tenant_id is None:
        await sio.emit(event, payload)
    else:
        await sio.emit(event, payload, room=tenant_room(tenant_id))

async def digital_twin_emitter():
    """Advance the persisted twin and publish its tenant-scoped state transitions."""
    try:
        from backend.database import SessionLocal
        from backend.services.digital_twin import tick_once

        while True:
            await asyncio.sleep(1)
            try:
                with SessionLocal() as db:
                    snapshots = tick_once(db)
                for snapshot in snapshots:
                    tenant_id = snapshot.get("tenant_id")
                    await emit_tenant_event("digital_twin:device_update", snapshot, tenant_id)
                    if snapshot.get("alert"):
                        await emit_tenant_event("digital_twin:alert", snapshot["alert"], tenant_id)
                    if snapshot.get("alert_cleared"):
                        await emit_tenant_event("digital_twin:alert_cleared", snapshot["alert_cleared"], tenant_id)
            except Exception:
                logger.exception("Digital-twin simulation tick failed")
    except asyncio.CancelledError:
        logger.info("digital_twin_emitter cancelled")

def start_background_emitters(loop: asyncio.AbstractEventLoop):
    """Start emitter tasks on the provided event loop."""
    _emit_tasks.append(loop.create_task(digital_twin_emitter()))
    # Start robot lifecycle worker (Day 72)
    try:
        from backend.services.robot_worker import robot_task_worker
        _emit_tasks.append(loop.create_task(robot_task_worker()))
    except Exception:
        logger.exception("Failed to start robot_task_worker")
    logger.info("Realtime emitters started")

async def stop_background_emitters():
    """Cancel and await emitter tasks."""
    for t in list(_emit_tasks):
        t.cancel()
    await asyncio.gather(*_emit_tasks, return_exceptions=True)
    _emit_tasks.clear()
    logger.info("Realtime emitters stopped")


@sio.event
async def connect(sid, environ, auth=None):
    tenant_id = _tenant_id_from_auth(auth)
    if isinstance(auth, dict) and auth.get("token") and tenant_id is None:
        logger.warning("Rejected realtime client with invalid authentication: %s", sid)
        return False

    if tenant_id is not None:
        await sio.enter_room(sid, tenant_room(tenant_id))
    logger.info("Realtime client connected: %s (tenant=%s)", sid, tenant_id)
@sio.event
async def disconnect(sid):
    logger.info(f"Realtime client disconnected: {sid}")
