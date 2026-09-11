"""
Aegis Backend - Main Application
FastAPI app initialization and startup/shutdown events.
"""

# SSL and cert handling for third-party libs (aiohttp, web3)
import ssl
import os
try:
    # Prefer a cert bundle from certifi to avoid Windows cert store issues
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except Exception:
    pass
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Workaround: On some Windows environments, loading certs from the system store
# can raise ASN1 parsing errors. Monkeypatch the internal loader to be a no-op
# so import-time SSL context creation does not fail.
try:
    ssl.SSLContext._load_windows_store_certs = lambda self, storename, purpose: None
except Exception:
    pass

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordBearer

from backend.config import settings
from backend.database import init_db
from backend.exceptions import AegisException
from backend.middleware import setup_cors_middleware, setup_custom_middleware, setup_production_security_middleware

# Import routers
from backend.routers import auth, zones, sensors, research, health, audit, tenants, robotics, spatial, orchestration, iot_sensors
from backend.routers import crops, agricultural_sensors, crop_lifecycle, biological_metrics, succession
from backend.routers import biodiversity, energy, environmental
from backend.routers import weather, lab_automation
from backend.routers import hvac_schedules
from backend.routers import safety
from backend.routers import stream
from backend.routers import storage
from backend.routers import water
from backend.routers import waste
from backend.routers import communication, communication_extended
from backend.routers import estate, alerts, robotics_compat
from backend.routers import scene
from backend.routers import scene_admin
from backend import realtime
from backend.routers import day65
from backend.routers import day67_playback
from backend.routers import day68_notifications
from backend.routers import digital_twin
from backend.routers import local_iot
from backend.routers import estate_hierarchy

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def vryndara_guard_loop():
    """
    Day 19: Background Watcher
    Simulates Vryndara's continuous oversight of sector integrity.
    """
    logger.info("??? Vryndara Guard: Active Background Monitoring initialized.")
    try:
        while True:
            # In Phase 2, this will trigger actual anomaly detection logic
            # for now, it serves as the 'Heartbeat' of the autonomous system.
            logger.debug("Vryndara Guard: Scanning Sector integrity...")
            await asyncio.sleep(30)
    except asyncio.CancelledError:
        logger.info("Vryndara Guard: Background Monitoring suspended.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Handles startup and shutdown events.
    """
    # --- Startup ---
    logger.info("Starting Aegis backend...")
    logger.info(f"Environment: {settings.environment}")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Vryndara initialization deferred to first use (lazy loading)
    # This prevents startup blockages from gRPC connection attempts
    logger.info("Vryndara connector will initialize on first research endpoint call")



    # Start the Day 19 Background Monitor
    guard_task = None
    # Skip starting background daemons during pytest runs to avoid shutdown races
    if not os.environ.get("PYTEST_RUNNING"):
        guard_task = asyncio.create_task(vryndara_guard_loop())

    # Start automation scheduler (Day 63)
    scheduler_task = None
    if not os.environ.get("PYTEST_RUNNING"):
        try:
            from backend.services.automation_scheduler import get_scheduler
            scheduler = get_scheduler()
            scheduler_task = scheduler.start()
            logger.info("Automation scheduler started")
        except Exception as e:
            logger.error(f"Failed to start automation scheduler: {e}")

    # Start sensor health monitor
    sensor_monitor_task = None
    if not os.environ.get("PYTEST_RUNNING"):
        try:
            from backend.services.sensor_monitor import get_sensor_monitor
            monitor = get_sensor_monitor()
            sensor_monitor_task = monitor.start()
            logger.info("Sensor health monitor started")
        except Exception as e:
            logger.error(f"Failed to start sensor monitor: {e}")

    # Initialize blockchain monitoring (Day 26)
    blockchain_monitor_task = None
    if not os.environ.get("PYTEST_RUNNING"):
        try:
            from backend.blockchain_connector import get_blockchain_connector
            from backend.blockchain_monitor import get_blockchain_monitor

            blockchain_connector = get_blockchain_connector()
            if blockchain_connector.is_connected:
                blockchain_monitor = get_blockchain_monitor(blockchain_connector)
                blockchain_monitor_task = asyncio.create_task(
                    blockchain_monitor.start_monitoring(interval_seconds=30)
                )
                logger.info("? Blockchain monitoring started")
            else:
                logger.warning("?? Blockchain not connected, monitoring disabled")

        except Exception as e:
            logger.error(f"Failed to initialize blockchain monitoring: {e}")

    # Start realtime emitters (Day 62)
    if not os.environ.get("PYTEST_RUNNING"):
        try:
            realtime.start_background_emitters(asyncio.get_running_loop())
            logger.info("Realtime emitters scheduled")
        except Exception as e:
            logger.error(f"Failed to start realtime emitters: {e}")

    yield

    # --- Shutdown ---
    logger.info("Shutting down Aegis backend...")

    # Stop blockchain monitoring
    if blockchain_monitor_task:
        try:
            from backend.blockchain_monitor import get_blockchain_monitor
            from backend.blockchain_connector import blockchain_connector
            monitor = get_blockchain_monitor(blockchain_connector)
            monitor.stop_monitoring()
            blockchain_monitor_task.cancel()
            await blockchain_monitor_task
        except Exception as e:
            logger.error(f"Error stopping blockchain monitoring: {e}")

    if guard_task:
        guard_task.cancel()
        try:
            await guard_task
        except asyncio.CancelledError:
            pass

    # Stop automation scheduler if running
    try:
        from backend.services.automation_scheduler import get_scheduler
        scheduler = get_scheduler()
        await scheduler.stop()
        logger.info("Automation scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping automation scheduler: {e}")
    # Stop sensor monitor
    if sensor_monitor_task:
        try:
            from backend.services.sensor_monitor import get_sensor_monitor
            monitor = get_sensor_monitor()
            await monitor.stop()
            logger.info("Sensor health monitor stopped")
        except Exception as e:
            logger.error(f"Error stopping sensor monitor: {e}")

    # Stop realtime emitters (Day 62)
    try:
        await realtime.stop_background_emitters()
    except Exception as e:
        logger.error(f"Error stopping realtime emitters: {e}")

# Security Scheme for Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

app = FastAPI(
    title=settings.app_name,
    description="Decentralized Digital Twin for IoT Audit & Autonomous Control",
    version=settings.app_version,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True} 
)

# Setup middleware
setup_cors_middleware(app)
setup_custom_middleware(app)

if not settings.debug:
    setup_production_security_middleware(app)

# --- Exception Handlers ---

@app.exception_handler(AegisException)
async def aegis_exception_handler(request: Request, exc: AegisException):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"[{request_id}] {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "request_id": request_id}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "request_id": request_id,
            "details": exc.errors() if settings.debug else "Invalid input"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"[{request_id}] Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request_id,
            "detail": str(exc) if settings.debug else "An error occurred"
        }
    )

# --- Routes ---

@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health",
    }

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(estate.router)
app.include_router(tenants.router)
app.include_router(zones.router)
app.include_router(sensors.router)
app.include_router(research.router)
app.include_router(robotics.router)
app.include_router(spatial.router)
app.include_router(orchestration.router)
app.include_router(iot_sensors.router)
app.include_router(crops.router)
app.include_router(agricultural_sensors.router)
app.include_router(crop_lifecycle.router)
app.include_router(biological_metrics.router)
app.include_router(succession.router)
app.include_router(audit.router)
app.include_router(biodiversity.router)
app.include_router(energy.router)
app.include_router(environmental.router)
app.include_router(weather.router)
app.include_router(lab_automation.router)
app.include_router(hvac_schedules.router)
app.include_router(safety.router)
app.include_router(stream.router)
app.include_router(storage.router)
app.include_router(water.router)
app.include_router(waste.router)
app.include_router(communication.router)
app.include_router(communication_extended.router)
app.include_router(robotics_compat.router)
app.include_router(scene.router)
app.include_router(scene_admin.router)
app.mount("/socket.io", realtime.sio_app)
app.include_router(alerts.router)
app.include_router(day65.router)
app.include_router(day67_playback.router)
app.include_router(day68_notifications.router)
app.include_router(digital_twin.router)
app.include_router(local_iot.router)
app.include_router(estate_hierarchy.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
