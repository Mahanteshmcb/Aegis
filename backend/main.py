"""
Aegis Backend - Main Application
FastAPI app initialization and startup/shutdown events.
"""

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
from backend.routers import auth, zones, sensors, research, health, audit, tenants, robotics

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
    logger.info("🛡️ Vryndara Guard: Active Background Monitoring initialized.")
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
    guard_task = asyncio.create_task(vryndara_guard_loop())

    # Initialize blockchain monitoring (Day 26)
    blockchain_monitor_task = None
    try:
        from backend.blockchain_connector import get_blockchain_connector
        from backend.blockchain_monitor import get_blockchain_monitor

        blockchain_connector = get_blockchain_connector()
        if blockchain_connector.is_connected:
            blockchain_monitor = get_blockchain_monitor(blockchain_connector)
            blockchain_monitor_task = asyncio.create_task(
                blockchain_monitor.start_monitoring(interval_seconds=30)
            )
            logger.info("✅ Blockchain monitoring started")
        else:
            logger.warning("⚠️ Blockchain not connected, monitoring disabled")

    except Exception as e:
        logger.error(f"Failed to initialize blockchain monitoring: {e}")

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

    guard_task.cancel()
    try:
        await guard_task
    except asyncio.CancelledError:
        pass

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
app.include_router(tenants.router)
app.include_router(zones.router)
app.include_router(sensors.router)
app.include_router(research.router)
app.include_router(robotics.router)
app.include_router(audit.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )