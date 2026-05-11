"""
Aegis Backend - Database Configuration
SQLAlchemy setup and session management.
"""

import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config import settings


# Base class for all ORM models
Base = declarative_base()

# Ensure all models are registered with Base
import backend.models_db

# Create database engine
if settings.database_url.startswith("sqlite"):
    # SQLite requires special handling for concurrent access
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.sqlalchemy_echo,
    )
    
    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL or other databases
    engine = create_engine(
        settings.database_url,
        echo=settings.sqlalchemy_echo,
        pool_pre_ping=True,
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def _ensure_audit_log_tenant_column_sqlite() -> None:
    """Ensure SQLite audit_logs has tenant_id and backfill it from sensors."""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info('audit_logs')"))
        columns = [row[1] for row in result]
        if 'tenant_id' in columns:
            return

        with conn.begin():
            conn.exec_driver_sql("ALTER TABLE audit_logs ADD COLUMN tenant_id INTEGER")
            conn.exec_driver_sql(
                "UPDATE audit_logs SET tenant_id = "
                "(SELECT tenant_id FROM sensors WHERE sensors.id = audit_logs.sensor_id) "
                "WHERE sensor_id IS NOT NULL"
            )
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_audit_logs_tenant_id ON audit_logs (tenant_id)")


def init_db():
    """Initialize database - create all tables."""
    Base.metadata.create_all(bind=engine)
    if settings.database_url.startswith('sqlite'):
        try:
            _ensure_audit_log_tenant_column_sqlite()
        except Exception as exc:
            logging.getLogger(__name__).warning(
                "SQLite audit_logs tenant_id patch failed: %s", exc
            )


def drop_db():
    """Drop all tables (for testing)."""
    Base.metadata.drop_all(bind=engine)
