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
from backend.routers import auth, zones, sensors, research, health, audit, tenants

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
    
    # Check Vryndara connectivity
    try:
        import sys, os
        vryndara_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../ai'))
        if vryndara_path not in sys.path:
            sys.path.insert(0, vryndara_path)
        from vryndara_connector import VryndaraConnector
        vryndara = VryndaraConnector()
        if vryndara.health_check():
            logger.info(f"Vryndara endpoint: {settings.vryndara_host}:{settings.vryndara_port} CONNECTED")
        else:
            logger.warning("Vryndara kernel unavailable, fallback mode enabled")
    except Exception as e:
        logger.error(f"Vryndara health check failed: {e}")

    # Start the Day 19 Background Monitor
    guard_task = asyncio.create_task(vryndara_guard_loop())
    
    yield
    
    # --- Shutdown ---
    logger.info("Shutting down Aegis backend...")
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
        "health": "/api/v1/health",
    }

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(tenants.router)
app.include_router(zones.router)
app.include_router(sensors.router)
app.include_router(research.router)
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