"""
Aegis Backend - Configuration Management
Supports dev, test, and production configurations with Pydantic.
"""

import os
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # App Configuration
    app_name: str = "Aegis"
    app_version: str = "0.1.0"
    environment: Literal["dev", "test", "prod"] = Field("dev", env="ENVIRONMENT")
    debug: bool = Field(True, env="DEBUG")
    
    # Server Configuration
    server_host: str = Field("127.0.0.1", env="SERVER_HOST")
    server_port: int = Field(8000, env="SERVER_PORT")
    
    # Database Configuration
    # Example for PostgreSQL: "postgresql+psycopg2://user:password@localhost:5432/aegis"
    database_url: str = Field("sqlite:///./aegis.db", env="DATABASE_URL")
    sqlalchemy_echo: bool = Field(True, env="SQLALCHEMY_ECHO")
    
    # JWT Configuration
    jwt_secret_key: str = Field("your-secret-key-change-in-prod", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(15, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS Configuration
    cors_origins: list = Field(["http://localhost:3000", "http://localhost:8000"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: list = Field(["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: list = Field(["*"], env="CORS_ALLOW_HEADERS")
    
    # Vryndara Configuration
    vryndara_host: str = Field("localhost", env="VRYNDARA_HOST")
    vryndara_port: int = Field(50051, env="VRYNDARA_PORT")
    vryndara_timeout: int = Field(5, env="VRYNDARA_TIMEOUT")
    vryndara_fallback_enabled: bool = Field(True, env="VRYNDARA_FALLBACK_ENABLED")
    
    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings (singleton)."""
    return Settings()


# Global settings instance
settings = get_settings()
