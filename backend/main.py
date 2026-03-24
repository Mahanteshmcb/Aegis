"""
Aegis Backend - Main Application
FastAPI app initialization and startup/shutdown events.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import init_db, SessionLocal
from backend.exceptions import AegisException
from backend.middleware import setup_cors_middleware, setup_custom_middleware, setup_production_security_middleware

# Import routers
from backend.routers import auth, zones, sensors, research, health, audit

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Aegis backend...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database: {settings.database_url}")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Check Vryndara connectivity on startup
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
    
    yield
    
    # Shutdown
    logger.info("Shutting down Aegis backend...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Decentralized Digital Twin for IoT Audit & Autonomous Control",
    version=settings.app_version,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Setup middleware
setup_cors_middleware(app)
setup_custom_middleware(app)

# Enable production security middleware if not in debug mode
if not settings.debug:
    setup_production_security_middleware(app)


# Exception handlers
@app.exception_handler(AegisException)
async def aegis_exception_handler(request: Request, exc: AegisException):
    """Handle Aegis custom exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"[{request_id}] {exc.message}", extra={"request_id": request_id})
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "request_id": request_id,
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(f"[{request_id}] Validation error: {exc}", extra={"request_id": request_id})
    
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
    """Handle unexpected exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"[{request_id}] Unexpected error: {exc}", extra={"request_id": request_id}, exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request_id,
            "detail": str(exc) if settings.debug else "An error occurred"
        }
    )


# Health check root endpoint
@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


# Include routers

# Register routers
app.include_router(health.router)
app.include_router(auth.router)
from backend.routers import tenants
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
