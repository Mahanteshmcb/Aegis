"""
Aegis Backend - Middleware
Request logging, error handling, request ID tracing.
"""

import uuid
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from backend.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path}",
            extra={"request_id": request_id}
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({process_time:.3f}s)",
                extra={"request_id": request_id, "status_code": response.status_code, "duration_ms": process_time * 1000}
            )
            
            return response
        
        except Exception as exc:
            process_time = time.time() - start_time
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} -> ERROR ({process_time:.3f}s): {str(exc)}",
                extra={"request_id": request_id, "duration_ms": process_time * 1000},
                exc_info=True
            )
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Handle exceptions and return consistent error responses."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = getattr(request.state, "request_id", "unknown")
        
        try:
            response = await call_next(request)
            return response
        
        except Exception as exc:
            logger.error(
                f"[{request_id}] Unhandled exception: {str(exc)}",
                extra={"request_id": request_id},
                exc_info=True
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request_id,
                    "detail": str(exc) if settings.debug else "An error occurred"
                }
            )


def setup_cors_middleware(app):
    """Setup CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    return app


def setup_custom_middleware(app):
    """Setup custom middleware in order."""
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    return app
