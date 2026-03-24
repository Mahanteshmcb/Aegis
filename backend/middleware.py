"""
Aegis Backend - Middleware
Request logging, error handling, request ID tracing, and CORS.
"""

import uuid
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

from backend.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add common security headers to all responses."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

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
        
        logger.info(f"[{request_id}] {request.method} {request.url.path}", extra={"request_id": request_id})
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
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
            return await call_next(request)
        except Exception as exc:
            logger.error(f"[{request_id}] Unhandled exception: {str(exc)}", extra={"request_id": request_id}, exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request_id,
                    "detail": str(exc) if settings.debug else "An error occurred"
                }
            )

def setup_cors_middleware(app):
    """Configure CORS for the application."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",   # Your Next.js frontend
            "http://127.0.0.1:3000",
            "http://localhost:8080",   # Swagger UI
        ],
        allow_credentials=True,
        allow_methods=["*"],           # Allows all methods (POST, GET, etc.)
        allow_headers=["*"],           # Allows all headers
    )
    return app

def setup_custom_middleware(app):
    """Setup custom middleware in order."""
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    return app

def setup_production_security_middleware(app):
    """Setup production-only security middleware (TrustedHost, HTTPSRedirect)."""
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "yourdomain.com"])
    app.add_middleware(HTTPSRedirectMiddleware)
    return app