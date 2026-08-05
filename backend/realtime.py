"""
Realtime Socket.IO server for Day 62: emits 'systemStatus:update' and 'sensor:reading' events.
"""
import asyncio
import random
import logging
from datetime import datetime

import socketio

from backend.routers.estate import get_mock_system_status

logger = logging.getLogger(__name__)

# Do not emit Socket.IO CORS headers here; FastAPI's CORSMiddleware handles CORS for the mounted route.
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=[])
# Mounting the Socket.IO ASGI app at /socket.io means the inner app receives the remaining
# path after the mount point is stripped. Use '/' here so the mounted root path resolves correctly.
sio_app = socketio.ASGIApp(sio, socketio_path='/')

_emit_tasks = []

async def sensor_emitter():
    """Emit simulated sensor readings every 1-5 seconds."""
    try:
        while True:
            await asyncio.sleep(random.uniform(1, 5))
            data = {
                "sensor_id": f"sensor_{random.randint(1,20):02}",
                "system": random.choice(["climate", "energy", "security", "water", "comms"]),
                "value": round(random.uniform(0, 100), 2),
                "timestamp": datetime.utcnow().isoformat()
            }
            await sio.emit("sensor:reading", data)
    except asyncio.CancelledError:
        logger.info("sensor_emitter cancelled")

async def system_status_emitter():
    """Emit aggregated system status periodically (every ~5 seconds)."""
    try:
        while True:
            await asyncio.sleep(5)
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "systems": [
                    get_mock_system_status("climate", "Climate Control").dict(),
                    get_mock_system_status("energy", "Energy Management").dict(),
                    get_mock_system_status("security", "Security System").dict(),
                    get_mock_system_status("water", "Water Management").dict(),
                    get_mock_system_status("comms", "Communications").dict(),
                ]
            }
            await sio.emit("systemStatus:update", payload)
    except asyncio.CancelledError:
        logger.info("system_status_emitter cancelled")

def start_background_emitters(loop: asyncio.AbstractEventLoop):
    """Start emitter tasks on the provided event loop."""
    _emit_tasks.append(loop.create_task(sensor_emitter()))
    _emit_tasks.append(loop.create_task(system_status_emitter()))
    logger.info("Realtime emitters started")

async def stop_background_emitters():
    """Cancel and await emitter tasks."""
    for t in list(_emit_tasks):
        t.cancel()
    await asyncio.gather(*_emit_tasks, return_exceptions=True)
    _emit_tasks.clear()
    logger.info("Realtime emitters stopped")


@sio.event
async def connect(sid, environ):
    logger.info(f"Realtime client connected: {sid}")
    # Send immediate snapshot on connect
    snapshot = {
        "timestamp": datetime.utcnow().isoformat(),
        "systems": [
            get_mock_system_status("climate", "Climate Control").dict(),
            get_mock_system_status("energy", "Energy Management").dict(),
            get_mock_system_status("security", "Security System").dict(),
            get_mock_system_status("water", "Water Management").dict(),
            get_mock_system_status("comms", "Communications").dict(),
        ]
    }
    await sio.emit("systemStatus:update", snapshot, to=sid)


@sio.event
async def disconnect(sid):
    logger.info(f"Realtime client disconnected: {sid}")
