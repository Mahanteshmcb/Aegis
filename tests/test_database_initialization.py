from pathlib import Path
import importlib.util
import os
import sqlite3

from alembic.migration import MigrationContext
from alembic.operations import Operations
from backend import database
from backend.models_db import Tenant, User
from passlib.hash import bcrypt
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker


def test_default_seed_creates_login_user_and_inferred_zone(in_memory_db):
    database._seed_default_tenant_and_sample_data()

    with database.SessionLocal() as db:
        user = db.query(User).filter_by(email="admin@aegis.com").one()
        zone = db.query(database.Zone).filter_by(
            tenant_id=user.tenant_id,
            name="Main Lab Zone",
        ).one()

        assert user.role == "admin"
        assert zone.spatial_status == "inferred"
        assert zone.length_unit == "m"


def test_file_backed_startup_seed_commits_before_canonical_seed(monkeypatch, tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'startup-seed.db'}",
        connect_args={"check_same_thread": False, "timeout": 3},
    )
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", session_factory)
    database.Base.metadata.create_all(bind=engine)

    try:
        database._seed_default_tenant_and_sample_data()

        with session_factory() as db:
            user = db.query(User).filter_by(email="admin@aegis.com").one()
            assert user.role == "admin"
            assert bcrypt.verify("admin1234", user.hashed_password)
            assert db.query(Tenant).count() == 1
    finally:
        engine.dispose()


def test_sqlite_backup_retains_two_consistent_snapshots(monkeypatch, tmp_path):
    db_file = tmp_path / "aegis.db"
    with sqlite3.connect(db_file) as db:
        db.execute("CREATE TABLE backup_probe (value TEXT NOT NULL)")
        db.execute("INSERT INTO backup_probe (value) VALUES ('current')")

    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    for suffix in ("20261020_000000", "20261021_000000", "20261022_000000"):
        (backup_dir / f"aegis_{suffix}.db").write_bytes(b"old snapshot")
    stale_snapshot = backup_dir / "aegis_before_restore_20260828_190753.db"
    stale_snapshot.write_bytes(b"older snapshot")
    os.utime(stale_snapshot, (1, 1))
    stale_temporary = backup_dir / "aegis_20261024_000000.db.tmp"
    stale_temporary.write_bytes(b"incomplete snapshot")
    unrelated_file = backup_dir / "other_database.db"
    unrelated_file.write_bytes(b"leave untouched")

    monkeypatch.setattr(database.settings, "database_url", f"sqlite:///{db_file}")
    created_backup = database._create_sqlite_backup()

    assert created_backup is not None
    backups = sorted(backup_dir.glob("aegis_*.db"))
    assert len(backups) == 2
    assert Path(created_backup) in backups
    assert not stale_snapshot.exists()
    assert not stale_temporary.exists()
    assert unrelated_file.exists()
    with sqlite3.connect(created_backup) as snapshot:
        assert snapshot.execute("SELECT value FROM backup_probe").fetchone() == ("current",)


def test_spatial_orientation_migration_is_safe_to_retry(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'spatial-migration.db'}")
    migration_path = Path(__file__).parents[1] / "backend" / "alembic" / "versions" / "0016_spatial_orientation.py"
    spec = importlib.util.spec_from_file_location("spatial_orientation_migration", migration_path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE zones (id INTEGER PRIMARY KEY)")
        connection.exec_driver_sql(
            "CREATE TABLE digital_twin_devices (id INTEGER PRIMARY KEY, adapter_type VARCHAR(24) NOT NULL)"
        )
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            migration.upgrade()

        zone_columns = {column["name"] for column in inspect(connection).get_columns("zones")}
        device_columns = {column["name"] for column in inspect(connection).get_columns("digital_twin_devices")}

    assert "orientation" in zone_columns
    assert {"orientation", "spatial_status", "coordinate_system", "length_unit"} <= device_columns
    engine.dispose()


def test_device_position_provenance_migration_is_safe_to_retry(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'device-position-migration.db'}")
    migration_path = Path(__file__).parents[1] / "backend" / "alembic" / "versions" / "0017_device_position_provenance.py"
    spec = importlib.util.spec_from_file_location("device_position_provenance_migration", migration_path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE digital_twin_devices (id INTEGER PRIMARY KEY)")
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            migration.upgrade()
        columns = {column["name"] for column in inspect(connection).get_columns("digital_twin_devices")}

    assert "position_configured" in columns
    engine.dispose()
