"""
Aegis Backend - Database Configuration
SQLAlchemy setup and session management.
"""

import logging
from pathlib import Path
from shutil import copy2
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime
import json

from passlib.hash import bcrypt
from backend.config import settings


# Base class for all ORM models
Base = declarative_base()

# Ensure all models are registered with Base
import backend.models_db
import backend.models.storage
import backend.models.safety
import backend.models.lab_automation
import backend.models.hvac_schedule
import backend.models.digital_twin
import backend.models.environmental
import backend.models.estate_hierarchy

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


def _seed_default_tenant_and_sample_data() -> None:
    """Seed a default tenant, admin user, sample zone, and sample sensor."""
    with engine.begin() as conn:
        tenant_row = conn.execute(
            text("SELECT id FROM tenants WHERE name = :name"),
            {"name": "Aegis Tenant"},
        ).fetchone()

        if tenant_row is None:
            existing_tenant = conn.execute(
                text("SELECT id FROM tenants ORDER BY id LIMIT 1")
            ).fetchone()
            if existing_tenant is not None:
                tenant_id = existing_tenant[0]
            else:
                now = datetime.utcnow().isoformat(sep=' ')
                conn.execute(
                    text(
                        "INSERT INTO tenants (name, settings, created_at, updated_at) VALUES (:name, :settings, :created_at, :updated_at)"
                    ),
                    {
                        "name": "Aegis Tenant",
                        "settings": "{}",
                        "created_at": now,
                        "updated_at": now,
                    },
                )
                tenant_id = conn.execute(
                    text("SELECT id FROM tenants WHERE name = :name"),
                    {"name": "Aegis Tenant"},
                ).scalar_one()
        else:
            tenant_id = tenant_row[0]

        # Ensure a default admin user exists for login and setup.
        admin_email = "admin@aegis.com"
        legacy_admin_email = "admin@aegis.local"

        current_admin = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": admin_email},
        ).fetchone()
        legacy_admin = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": legacy_admin_email},
        ).fetchone()

        if current_admin is None and legacy_admin is None:
            now = datetime.utcnow().isoformat(sep=' ')
            admin_password = bcrypt.hash("admin1234")
            conn.execute(
                text(
                    "INSERT INTO users (email, hashed_password, role, tenant_id, created_at, updated_at) "
                    "VALUES (:email, :hashed_password, :role, :tenant_id, :created_at, :updated_at)"
                ),
                {
                    "email": admin_email,
                    "hashed_password": admin_password,
                    "role": "admin",
                    "tenant_id": tenant_id,
                    "created_at": now,
                    "updated_at": now,
                },
            )
        else:
            user_id = current_admin[0] if current_admin is not None else legacy_admin[0]
            now = datetime.utcnow().isoformat(sep=' ')
            admin_password = bcrypt.hash("admin1234")
            conn.execute(
                text(
                    "UPDATE users SET email = :email, hashed_password = :hashed_password, role = :role, tenant_id = :tenant_id, updated_at = :updated_at "
                    "WHERE id = :id"
                ),
                {
                    "id": user_id,
                    "email": admin_email,
                    "hashed_password": admin_password,
                    "role": "admin",
                    "tenant_id": tenant_id,
                    "updated_at": now,
                },
            )

            # Remove any leftover legacy local-admin row.
            conn.execute(
                text("DELETE FROM users WHERE email = :legacy_email"),
                {"legacy_email": legacy_admin_email},
            )

        # Ensure a sample zone exists for the tenant.
        zone_count = conn.execute(
            text("SELECT COUNT(*) FROM zones WHERE tenant_id = :tenant_id AND name = :name"),
            {"tenant_id": tenant_id, "name": "Main Lab Zone"},
        ).scalar_one()
        if zone_count == 0:
            now = datetime.utcnow().isoformat(sep=' ')
            conn.execute(
                text(
                    "INSERT INTO zones (name, description, location, tenant_id, created_at, updated_at) "
                    "VALUES (:name, :description, :location, :tenant_id, :created_at, :updated_at)"
                ),
                {
                    "name": "Main Lab Zone",
                    "description": "Primary laboratory space with climate control.",
                    "location": "Level 1",
                    "tenant_id": tenant_id,
                    "created_at": now,
                    "updated_at": now,
                },
            )

        zone_id = conn.execute(
            text("SELECT id FROM zones WHERE tenant_id = :tenant_id AND name = :name"),
            {"tenant_id": tenant_id, "name": "Main Lab Zone"},
        ).scalar_one()

        sample_reading = json.dumps(
            {
                "value": 21.8,
                "unit": "C",
                "timestamp": datetime.utcnow().isoformat(sep=' '),
            }
        )

        sensor_count = conn.execute(
            text("SELECT COUNT(*) FROM sensors WHERE tenant_id = :tenant_id AND name = :name"),
            {"tenant_id": tenant_id, "name": "Lab Temperature Sensor"},
        ).scalar_one()
        if sensor_count == 0:
            now = datetime.utcnow().isoformat(sep=' ')
            conn.execute(
                text(
                    "INSERT INTO sensors (tenant_id, zone_id, name, type, location, last_reading, created_at, updated_at) "
                    "VALUES (:tenant_id, :zone_id, :name, :type, :location, :last_reading, :created_at, :updated_at)"
                ),
                {
                    "tenant_id": tenant_id,
                    "zone_id": zone_id,
                    "name": "Lab Temperature Sensor",
                    "type": "temperature",
                    "location": "Main Lab",
                    "last_reading": sample_reading,
                    "created_at": now,
                    "updated_at": now,
                },
            )

        sensor_id = conn.execute(
            text("SELECT id FROM sensors WHERE tenant_id = :tenant_id AND name = :name"),
            {"tenant_id": tenant_id, "name": "Lab Temperature Sensor"},
        ).scalar_one()

        reading_count = conn.execute(
            text("SELECT COUNT(*) FROM sensor_data WHERE sensor_id = :sensor_id"),
            {"sensor_id": sensor_id},
        ).scalar_one()
        if reading_count == 0:
            now = datetime.utcnow().isoformat(sep=' ')
            conn.execute(
                text(
                    "INSERT INTO sensor_data (sensor_id, timestamp, value, unit, created_at) "
                    "VALUES (:sensor_id, :timestamp, :value, :unit, :created_at)"
                ),
                {
                    "sensor_id": sensor_id,
                    "timestamp": datetime.utcnow().isoformat(sep=' '),
                    "value": "21.8",
                    "unit": "C",
                    "created_at": now,
                },
            )

        # Keep the Day 71/72 demo fleet available after a fresh restart.
        demo_sensors = [
            ("Sim Soil Probe 1", "soil_moisture", "Field A", "35"),
            ("Sim Energy Inverter 1", "inverter", "Power Shed", "72"),
            ("Sim Acoustic Pest Monitor 1", "acoustic_pest", "Canopy North", "0"),
            ("Test Soil Probe 1", "soil_moisture", "Test Field", "41"),
            ("Test Soil Probe 2", "soil_moisture", "Test Field", "44"),
        ]
        for name, sensor_type, location, value in demo_sensors:
            exists = conn.execute(
                text("SELECT COUNT(*) FROM sensors WHERE tenant_id = :tenant_id AND name = :name"),
                {"tenant_id": tenant_id, "name": name},
            ).scalar_one()
            if exists == 0:
                now = datetime.utcnow().isoformat(sep=' ')
                conn.execute(
                    text(
                        "INSERT INTO sensors (tenant_id, zone_id, name, type, location, last_reading, created_at, updated_at) "
                        "VALUES (:tenant_id, :zone_id, :name, :type, :location, :last_reading, :created_at, :updated_at)"
                    ),
                    {
                        "tenant_id": tenant_id,
                        "zone_id": zone_id,
                        "name": name,
                        "type": sensor_type,
                        "location": location,
                        "last_reading": json.dumps({"value": value, "unit": "%", "timestamp": now}),
                        "created_at": now,
                        "updated_at": now,
                    },
                )


def _create_sqlite_backup() -> str | None:
    """Create a timestamped SQLite backup in a local backups folder."""
    if not settings.database_url.startswith("sqlite"):
        return None

    db_path = settings.database_url.replace("sqlite:///", "", 1)
    if not db_path:
        return None

    db_file = Path(db_path).resolve()
    if not db_file.exists():
        return None

    backup_dir = db_file.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_file = backup_dir / f"{db_file.stem}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db"
    copy2(db_file, backup_file)
    return str(backup_file)


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

    try:
        _seed_default_tenant_and_sample_data()
    except Exception as exc:
        logging.getLogger(__name__).warning("Failed to seed default tenant and sample data: %s", exc)

    if settings.database_url.startswith('sqlite'):
        try:
            backup_path = _create_sqlite_backup()
            if backup_path:
                logging.getLogger(__name__).info("SQLite backup created at %s", backup_path)
        except Exception as exc:
            logging.getLogger(__name__).warning("Failed to create SQLite backup: %s", exc)


def drop_db():
    """Drop all tables (for testing)."""
    Base.metadata.drop_all(bind=engine)
