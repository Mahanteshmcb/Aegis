"""
Standalone Socket.IO app used to validate realtime tests while main app import is blocked by aiohttp SSL on Windows.
Run this with the aegis env active:
    conda activate aegis
    python backend/standalone_socketio.py

This script applies the same safe SSL monkeypatches and exposes the same sio_app used by backend.realtime,
listening on port 8002 so tests can connect directly to http://127.0.0.1:8002/socket.io
"""
import asyncio
import ssl
import os
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except Exception:
    pass
try:
    ssl.SSLContext._load_windows_store_certs = lambda self, storename, purpose: None
except Exception:
    pass

import socketio
from aiohttp import web
import random
import json

sio = socketio.AsyncServer(async_mode="aiohttp", cors_allowed_origins="*")
app = web.Application()
sio.attach(app)

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit("systemStatus:update", {"status": "ok"}, to=sid)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

async def sensor_emitter():
    while True:
        await asyncio.sleep(random.uniform(0.5, 2.0))
        payload = {"sensor_id": "sim-1", "value": random.random()}
        await sio.emit("sensor:reading", payload)

async def start_background(loop):
    loop.create_task(sensor_emitter())

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_background(loop))
    web.run_app(app, host="127.0.0.1", port=8001)
