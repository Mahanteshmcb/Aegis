"""
Aegis Backend - Custom Exceptions
Consistent error handling across the application.
"""

from fastapi import status


class AegisException(Exception):
    """Base exception for Aegis application."""
    
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(AegisException):
    """User authentication failed."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(AegisException):
    """User lacks required permissions."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class NotFoundError(AegisException):
    """Resource not found."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ValidationError(AegisException):
    """Invalid input data."""
    
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class ConflictError(AegisException):
    """Resource conflict."""
    
    def __init__(self, message: str = "Conflict"):
        super().__init__(message, status.HTTP_409_CONFLICT)


class VryndaraError(AegisException):
    """Vryndara service error."""
    
    def __init__(self, message: str = "Vryndara service unavailable"):
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE)
