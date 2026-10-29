"""
Aegis Backend - Database Configuration
SQLAlchemy setup and session management.
"""

import logging
import re
import sqlite3
from pathlib import Path
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Float, Text, JSON, create_engine, event, text
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import json

from passlib.hash import bcrypt
from backend.config import settings
from backend.services.estate_seed import build_estate_seed_snapshot


# Base class for all ORM models
Base = declarative_base()

# Ensure all models are registered with Base

# Device model for digital twin assets (sensors, rovers, actuators)
# Enhanced with position tracking, asset ratios, battery, payload, and status monitoring
class Device(Base):
    """Digital twin device model representing sensors, rovers, and assets."""
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_type = Column(String(50), nullable=False)  # sensor, rover, zone, actuator
    subtype = Column(String(50), nullable=True)  # soil_moisture, temperature, autonomous, etc.
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=True)  # FK to zones.id

    # Device identification
    device_id = Column(String(100), unique=True, nullable=False)  # sensor_1, rover_1, etc.
    name = Column(String(100), nullable=False)

    # Position tracking (meters in digital twin coordinate system)
    position_x = Column(Float, default=0.0, nullable=False)
    position_y = Column(Float, default=0.0, nullable=False)
    position_z = Column(Float, default=0.0, nullable=False)

    # Status monitoring
    status = Column(String, default="idle", nullable=False)  # active, idle, fault, moving, charging

    # Asset ratio: model : real-world scaling
    asset_ratio = Column(String, default="1:1", nullable=False)

    # Sensor readings
    last_reading = Column(Float, default=0.0, nullable=False)
    units = Column(String, default="", nullable=False)

    # Rover-specific fields
    battery_level = Column(Float, default=100.0, nullable=True)  # 0-100 percent
    payload_capacity = Column(String, default="", nullable=True)  # e.g., "20kg"
    max_speed_m_s = Column(Float, default=0.0, nullable=True)

    # Environment
    environment_data = Column(Text, nullable=True)  # JSON: {"weather": "clear", "temp": 22}

    # Relationships
    zone = relationship("Zone", foreign_keys=[zone_id])

# Zone model for spatial grouping
class Zone(Base):
    """Spatial zone model for grouping devices in the digital twin."""
    __tablename__ = "zones"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    location = Column(String(255), nullable=True)
    name = Column(String(100), nullable=False)
    coordinates = Column(Text, nullable=True)
    asset_ratio = Column(String, default="1:1", nullable=True)
    position_ratio = Column(String, default="50:50", nullable=True)
    target_metrics = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    spatial_position = Column(JSON, nullable=True)
    dimensions = Column(JSON, nullable=True)
    orientation = Column(JSON, nullable=True)
    spatial_status = Column(String(24), nullable=False, default="inferred")
    coordinate_system = Column(String(100), nullable=True)
    length_unit = Column(String(16), nullable=False, default="m")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def zone_id(self):
        """Backward-compatible alias for legacy code expecting a string zone id."""
        return str(self.id) if self.id is not None else None

    @zone_id.setter
    def zone_id(self, value):
        if value is None:
            self.id = None
            return
        try:
            self.id = int(value)
        except (TypeError, ValueError):
            self.id = None

    def to_dict(self):
        """Convert zone to dictionary for API responses."""
        return {
            "id": self.id,
            "zone_id": self.zone_id,
            "name": self.name,
            "location": self.location,
            "coordinates": json.loads(self.coordinates) if self.coordinates else None,
            "asset_ratio": self.asset_ratio,
            "position_ratio": self.position_ratio,
            "target_metrics": json.loads(self.target_metrics) if self.target_metrics else None,
            "description": self.description,
            "tenant_id": self.tenant_id,
        }

    @property
    def position(self):
        if not isinstance(self.spatial_position, dict):
            return None
        return [self.spatial_position.get(axis, 0.0) for axis in ("x", "y", "z")]

    @property
    def size(self):
        if not isinstance(self.dimensions, dict):
            return None
        return [self.dimensions.get(axis) for axis in ("width", "height", "depth")]

    def update_from_json(self, data: dict):
        """Update zone attributes from JSON payload."""
        self.name = data.get("name", self.name)
        self.location = data.get("location", self.location)
        self.coordinates = json.dumps(data.get("coordinates", self.coordinates)) if data.get("coordinates") else None
        self.asset_ratio = data.get("asset_ratio", self.asset_ratio)
        self.position_ratio = data.get("position_ratio", self.position_ratio)
        self.target_metrics = json.dumps(data.get("target_metrics", self.target_metrics)) if data.get("target_metrics") else None
        self.description = data.get("description", self.description)

    def __repr__(self):
        return f"<Zone {self.zone_id}: {self.name}>"

    @property
    def coordinates_dict(self):
        """Get coordinates as dict."""
        return json.loads(self.coordinates) if self.coordinates else None

    @property
    def target_metrics_dict(self):
        """Get target metrics as dict."""
        return json.loads(self.target_metrics) if self.target_metrics else None


# Ensure all models are registered with Base
import backend.models_db
import backend.models.storage
import backend.models.safety
import backend.models.lab_automation
import backend.models.hvac_schedule
import backend.models.digital_twin
import backend.models.environmental
import backend.models.estate_hierarchy
import backend.models.water
import backend.models.waste

def _create_sqlite_engine(database_url: str):
    """Create a file-backed SQLite engine with independent pooled connections."""
    return create_engine(
        database_url,
        connect_args={"check_same_thread": False, "timeout": 30},
        echo=settings.sqlalchemy_echo,
    )


# Create database engine
if settings.database_url.startswith("sqlite"):
    engine = _create_sqlite_engine(settings.database_url)

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


def _ensure_zone_compatibility_sqlite() -> None:
    """Normalize legacy zone tables to the canonical id-based schema used by Aegis."""
    if not settings.database_url.startswith('sqlite'):
        return

    with engine.begin() as conn:
        try:
            result = conn.execute(text("PRAGMA table_info('zones')"))
        except Exception:
            return
        columns = [row[1] for row in result]

        def add_column(column_name: str, column_type: str) -> None:
            if column_name in columns:
                return
            try:
                conn.exec_driver_sql(f"ALTER TABLE zones ADD COLUMN {column_name} {column_type}")
                columns.append(column_name)
            except Exception as exc:
                message = str(exc).lower()
                if "duplicate column" in message:
                    columns.append(column_name)
                    return
                raise

        # Restore the canonical zone schema used by the estate dashboard and environmental views.
        add_column("id", "INTEGER")
        add_column("tenant_id", "INTEGER")
        add_column("location", "TEXT")
        add_column("coordinates", "TEXT")
        add_column("asset_ratio", "TEXT")
        add_column("position_ratio", "TEXT")
        add_column("target_metrics", "TEXT")
        add_column("description", "TEXT")
        add_column("spatial_position", "JSON")
        add_column("dimensions", "JSON")
        add_column("spatial_status", "TEXT DEFAULT 'inferred'")
        add_column("coordinate_system", "TEXT")
        add_column("length_unit", "TEXT DEFAULT 'm'")
        add_column("created_at", "DATETIME")
        add_column("updated_at", "DATETIME")
        if "zone_id" in columns:
            conn.execute(
                text(
                    "UPDATE zones "
                    "SET id = CAST(TRIM(zone_id) AS INTEGER) "
                    "WHERE id IS NULL "
                    "AND TRIM(zone_id) <> '' "
                    "AND TRIM(zone_id) NOT GLOB '*[^0-9]*'"
                )
            )


def _ensure_device_adapter_column_sqlite() -> None:
    """Keep create_all-based local development compatible with the adapter migration."""
    if not settings.database_url.startswith("sqlite"):
        return
    with engine.begin() as conn:
        columns = {
            row[1] for row in conn.execute(text("PRAGMA table_info('digital_twin_devices')"))
        }
        if "adapter_type" not in columns:
            conn.exec_driver_sql(
                "ALTER TABLE digital_twin_devices "
                "ADD COLUMN adapter_type VARCHAR(24) NOT NULL DEFAULT 'simulation'"
            )

        if 'zone_id' in columns and 'id' in columns:
            conn.execute(
                text("UPDATE zones SET id = CAST(zone_id AS INTEGER) WHERE id IS NULL OR id = 0 AND zone_id NOT NULL AND zone_id GLOB '[0-9]*'"),
            )

        conn.execute(text("UPDATE zones SET id = rowid WHERE id IS NULL OR id = 0"))

        default_tenant = conn.execute(text("SELECT id FROM tenants ORDER BY id LIMIT 1")).scalar_one_or_none()
        if default_tenant is not None:
            conn.execute(
                text("UPDATE zones SET tenant_id = :tenant_id WHERE tenant_id IS NULL"),
                {"tenant_id": default_tenant},
            )
            conn.execute(
                text("UPDATE zones SET location = COALESCE(location, name) WHERE location IS NULL OR location = ''"),
            )
            conn.execute(
                text("UPDATE zones SET coordinates = COALESCE(coordinates, json_object('x', 0.0, 'y', 0.0, 'z', 0.0)) WHERE coordinates IS NULL OR coordinates = ''"),
            )
            conn.execute(
                text("UPDATE zones SET asset_ratio = COALESCE(asset_ratio, '1:1') WHERE asset_ratio IS NULL OR asset_ratio = ''"),
            )
            conn.execute(
                text("UPDATE zones SET position_ratio = COALESCE(position_ratio, '50:50') WHERE position_ratio IS NULL OR position_ratio = ''"),
            )
            conn.execute(
                text("UPDATE zones SET target_metrics = COALESCE(target_metrics, '{}') WHERE target_metrics IS NULL OR target_metrics = ''"),
            )
            conn.execute(
                text("UPDATE zones SET description = COALESCE(description, name) WHERE description IS NULL OR description = ''"),
            )
            conn.execute(
                text("UPDATE zones SET created_at = COALESCE(created_at, datetime('now')) WHERE created_at IS NULL"),
            )
            conn.execute(
                text("UPDATE zones SET updated_at = COALESCE(updated_at, datetime('now')) WHERE updated_at IS NULL"),
            )

        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_zones_id ON zones (id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_zones_tenant_id ON zones (tenant_id)"))


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
                    "INSERT INTO zones (name, description, location, tenant_id, spatial_status, length_unit, created_at, updated_at) "
                    "VALUES (:name, :description, :location, :tenant_id, :spatial_status, :length_unit, :created_at, :updated_at)"
                ),
                {
                    "name": "Main Lab Zone",
                    "description": "Primary laboratory space with climate control.",
                    "location": "Level 1",
                    "tenant_id": tenant_id,
                    "spatial_status": "inferred",
                    "length_unit": "m",
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

    _seed_canonical_estate_snapshot(tenant_id, zone_id)


def _seed_canonical_estate_snapshot(tenant_id: int, fallback_zone_id: int | None = None) -> None:
    """Seed a realistic estate model from one canonical snapshot.

    This keeps the database consistent across controllers and pages by removing
    layered ad hoc mock seeds.
    """
    snapshot = build_estate_seed_snapshot()
    zone_lookup: dict[str, int] = {}

    with engine.begin() as conn:
        for zone in snapshot["zones"]:
            zone_name = zone["name"]
            existing = conn.execute(
                text("SELECT id FROM zones WHERE tenant_id = :tenant_id AND name = :name"),
                {"tenant_id": tenant_id, "name": zone_name},
            ).scalar_one_or_none()

            if existing is None:
                result = conn.execute(
                    text(
                        "INSERT INTO zones (tenant_id, name, description, location, coordinates, asset_ratio, position_ratio, target_metrics, spatial_status, coordinate_system, length_unit, created_at, updated_at) "
                        "VALUES (:tenant_id, :name, :description, :location, :coordinates, :asset_ratio, :position_ratio, :target_metrics, :spatial_status, :coordinate_system, :length_unit, :created_at, :updated_at)"
                    ),
                    {
                        "tenant_id": tenant_id,
                        "name": zone_name,
                        "description": zone["description"],
                        "location": zone["location"],
                        "coordinates": json.dumps({"type": "estate", "points": []}),
                        "asset_ratio": "1:1",
                        "position_ratio": "50:50",
                        "target_metrics": json.dumps({"status": "configured"}),
                        "spatial_status": "inferred",
                        "coordinate_system": "estate-local",
                        "length_unit": "m",
                        "created_at": datetime.utcnow().isoformat(sep=' '),
                        "updated_at": datetime.utcnow().isoformat(sep=' '),
                    },
                )
                existing = result.lastrowid
            zone_lookup[zone_name] = int(existing)

        for device in snapshot["devices"]:
            device_id = device["device_id"]
            zone_name = device["zone_name"]
            zone_id = zone_lookup.get(zone_name, fallback_zone_id)

            existing = conn.execute(
                text("SELECT id FROM digital_twin_devices WHERE tenant_id = :tenant_id AND device_id = :device_id"),
                {"tenant_id": tenant_id, "device_id": device_id},
            ).scalar_one_or_none()

            if existing is not None:
                continue

            conn.execute(
                text(
                    "INSERT INTO digital_twin_devices "
                    "(tenant_id, zone_id, device_id, name, kind, device_type, adapter_type, status, position, state, simulation_enabled, control_mode, automation_policy, last_updated, created_at) "
                    "VALUES (:tenant_id, :zone_id, :device_id, :name, :kind, :device_type, :adapter_type, :status, :position, :state, :simulation_enabled, :control_mode, :automation_policy, :last_updated, :created_at)"
                ),
                {
                    "tenant_id": tenant_id,
                    "zone_id": zone_id,
                    "device_id": device_id,
                    "name": device["name"],
                    "kind": device["kind"],
                    "device_type": device["device_type"],
                    "adapter_type": device.get("adapter_type", "simulation"),
                    "status": "online",
                    "position": json.dumps(device.get("position", {"x": 0.0, "y": 0.0, "z": 0.0})),
                    "state": json.dumps(device.get("state", {})),
                    "simulation_enabled": 1,
                    "control_mode": device.get("control_mode", "automation"),
                    "automation_policy": json.dumps(device.get("automation_policy", {})),
                    "last_updated": datetime.utcnow().isoformat(sep=' '),
                    "created_at": datetime.utcnow().isoformat(sep=' '),
                },
            )

    from backend.services.domain_simulation import seed_demo_resource_data

    with SessionLocal() as db:
        seed_demo_resource_data(db, tenant_id)


def _create_sqlite_backup() -> str | None:
    """Create a consistent SQLite snapshot and retain only the latest two copies."""
    if not settings.database_url.startswith("sqlite"):
        return None

    db_path = settings.database_url.replace("sqlite:///", "", 1)
    if not db_path or db_path == ":memory:":
        return None

    db_file = Path(db_path).resolve()
    if not db_file.exists():
        return None

    backup_dir = db_file.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_pattern = re.compile(rf"^{re.escape(db_file.stem)}_.*\.db$")
    temporary_pattern = re.compile(rf"^{re.escape(db_file.stem)}_.*\.db\.tmp$")
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"{db_file.stem}_{timestamp}.db"
    if backup_file.exists():
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        backup_file = backup_dir / f"{db_file.stem}_{timestamp}.db"

    temporary_file = backup_file.with_suffix(".db.tmp")
    source = sqlite3.connect(str(db_file))
    target = sqlite3.connect(str(temporary_file))
    try:
        source.backup(target)
        target.close()
        source.close()
        temporary_file.replace(backup_file)
    finally:
        target.close()
        source.close()
        if temporary_file.exists():
            temporary_file.unlink()

    backups = sorted(
        (
            path for path in backup_dir.iterdir()
            if path.is_file() and backup_pattern.fullmatch(path.name)
        ),
        key=lambda path: (path.stat().st_mtime_ns, path.name),
        reverse=True,
    )
    for old_backup in backups[2:]:
        old_backup.unlink()
    for stale_temporary in backup_dir.iterdir():
        if stale_temporary.is_file() and temporary_pattern.fullmatch(stale_temporary.name):
            stale_temporary.unlink()
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
            _ensure_zone_compatibility_sqlite()
        except Exception as exc:
            logging.getLogger(__name__).warning(
                "SQLite zone compatibility patch failed: %s", exc
            )
        try:
            _ensure_device_adapter_column_sqlite()
        except Exception as exc:
            logging.getLogger(__name__).warning(
                "SQLite device adapter compatibility patch failed: %s", exc
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
