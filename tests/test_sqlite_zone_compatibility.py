from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from backend import database as db_module


def test_sqlite_zone_compatibility_patch_handles_existing_transaction(monkeypatch, tmp_path):
    db_path = tmp_path / "compat_test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE tenants (id INTEGER PRIMARY KEY, name TEXT)"))
        conn.execute(
            text(
                "CREATE TABLE zones (zone_id TEXT, name TEXT, tenant_id INTEGER, location TEXT, created_at DATETIME, updated_at DATETIME)"
            )
        )
        conn.execute(text("INSERT INTO tenants (id, name) VALUES (1, 'Aegis Tenant')"))
        conn.execute(
            text(
                "INSERT INTO zones (zone_id, name, tenant_id, location, created_at, updated_at) VALUES ('7', 'Main Lab Zone', 1, 'Level 1', '2026-01-01 00:00:00', '2026-01-01 00:00:00')"
            )
        )

    monkeypatch.setattr(db_module.settings, "database_url", f"sqlite:///{db_path}")
    monkeypatch.setattr(db_module, "engine", engine)

    db_module._ensure_zone_compatibility_sqlite()
    db_module._ensure_zone_compatibility_sqlite()

    with engine.connect() as conn:
        columns = [row[1] for row in conn.execute(text("PRAGMA table_info('zones')"))]
        assert "id" in columns
        assert "coordinates" in columns
        assert "asset_ratio" in columns
        assert "position_ratio" in columns
        assert "target_metrics" in columns
        assert "description" in columns
        assert conn.execute(text("SELECT id FROM zones LIMIT 1")).scalar_one() == 7


def test_sqlite_zone_schema_patch_adds_required_metadata(monkeypatch, tmp_path):
    db_path = tmp_path / "zone_metadata.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE tenants (id INTEGER PRIMARY KEY, name TEXT)"))
        conn.execute(
            text(
                "CREATE TABLE zones (id INTEGER PRIMARY KEY, name TEXT, tenant_id INTEGER, location TEXT, created_at DATETIME, updated_at DATETIME)"
            )
        )
        conn.execute(text("INSERT INTO tenants (id, name) VALUES (1, 'Aegis Tenant')"))
        conn.execute(
            text(
                "INSERT INTO zones (id, name, tenant_id, location, created_at, updated_at) VALUES (1, 'Main Lab Zone', 1, 'Level 1', '2026-01-01 00:00:00', '2026-01-01 00:00:00')"
            )
        )

    monkeypatch.setattr(db_module.settings, "database_url", f"sqlite:///{db_path}")
    monkeypatch.setattr(db_module, "engine", engine)

    db_module._ensure_zone_compatibility_sqlite()

    with engine.connect() as conn:
        columns = [row[1] for row in conn.execute(text("PRAGMA table_info('zones')"))]
        assert "coordinates" in columns
        assert "asset_ratio" in columns
        assert "position_ratio" in columns
        assert "target_metrics" in columns
        assert "description" in columns
        assert conn.execute(text("SELECT COUNT(*) FROM zones")).scalar_one() == 1
