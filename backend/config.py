"""
Aegis Backend - Configuration Management
Supports dev, test, and production configurations with Pydantic.
"""

from pathlib import Path
from typing import Literal
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    # App Configuration
    app_name: str = "Aegis"
    app_version: str = "0.1.0"
    environment: Literal["dev", "test", "prod"] = "dev"
    debug: bool = True

    # Server Configuration
    server_host: str = "127.0.0.1"
    server_port: int = 8001

    # Database Configuration
    # Example for PostgreSQL: "postgresql+psycopg2://user:password@localhost:5432/aegis"
    database_url: str = "sqlite:///./aegis.db"
    sqlalchemy_echo: bool = True

    # JWT Configuration
    jwt_secret_key: str = "your-secret-key-change-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # CORS Configuration
    cors_origins: list = ["http://localhost:3000", "http://localhost:8001"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]

    # Vryndara Configuration
    vryndara_host: str = "localhost"
    vryndara_port: int = 50051
    vryndara_timeout: int = 5
    vryndara_fallback_enabled: bool = True

    # Robotics Configuration
    robotics_host: str = "localhost"
    robotics_port: int = 50053
    robotics_timeout: int = 5
    robotics_fallback_enabled: bool = True

    # gRPC Performance Configuration
    grpc_max_workers: int = 10
    grpc_keepalive_time_ms: int = 30000
    grpc_keepalive_timeout_ms: int = 5000
    grpc_max_concurrent_streams: int = 100
    grpc_compression_enabled: bool = True

    # Load Testing Configuration
    load_test_concurrent_users: int = 50
    load_test_duration_seconds: int = 60
    load_test_ramp_up_seconds: int = 10

    # Logging Configuration
    log_level: str = "INFO"
    digital_twin_media_dir: str = str(BASE_DIR / "storage" / "digital-twin-media")
    digital_twin_media_retention_days: int = Field(default=30, ge=1, le=3650)
    digital_twin_telemetry_retention_days: int = Field(default=90, ge=1, le=3650)
    digital_twin_media_max_bytes: int = Field(default=25 * 1024 * 1024, ge=1, le=1024 * 1024 * 1024)
    arduino_gateway_url: str = Field(
        default="http://127.0.0.1:8765",
        validation_alias="AEGIS_ARDUINO_GATEWAY_URL",
    )
    arduino_gateway_token: SecretStr | None = Field(
        default=None,
        validation_alias="AEGIS_ARDUINO_GATEWAY_TOKEN",
    )
    arduino_gateway_timeout_seconds: float = Field(
        default=4.0,
        ge=0.5,
        le=15.0,
        validation_alias="AEGIS_ARDUINO_GATEWAY_TIMEOUT_SECONDS",
    )


def get_settings() -> Settings:
    """Get application settings (singleton)."""
    settings = Settings()

    if not settings.jwt_secret_key or not settings.jwt_secret_key.strip():
        settings.jwt_secret_key = "aegis-dev-secret-key"

    if settings.database_url.startswith("sqlite:///"):
        sqlite_path = settings.database_url[len("sqlite:///"):]
        if sqlite_path and not Path(sqlite_path).is_absolute():
            absolute_path = (BASE_DIR / sqlite_path).resolve()
            settings.database_url = f"sqlite:///{absolute_path.as_posix()}"

    return settings


# Global settings instance
settings = get_settings()
