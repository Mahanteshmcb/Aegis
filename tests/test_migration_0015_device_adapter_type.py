import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "0015_device_adapter_type.py"
)
SPEC = importlib.util.spec_from_file_location("migration_0015_device_adapter_type", MIGRATION_PATH)
MIGRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATION)


@pytest.mark.parametrize("column_exists", [False, True])
def test_upgrade_adds_adapter_type_only_when_missing(column_exists):
    engine = sa.create_engine("sqlite://")
    try:
        with engine.begin() as connection:
            connection.execute(sa.text("CREATE TABLE digital_twin_devices (id INTEGER PRIMARY KEY)"))
            if column_exists:
                connection.execute(
                    sa.text(
                        "ALTER TABLE digital_twin_devices "
                        "ADD COLUMN adapter_type VARCHAR(24) NOT NULL DEFAULT 'simulation'"
                    )
                )

            context = MigrationContext.configure(connection)
            with Operations.context(context):
                MIGRATION.upgrade()
                MIGRATION.upgrade()

            columns = {
                column["name"]: column
                for column in sa.inspect(connection).get_columns("digital_twin_devices")
            }
            assert "adapter_type" in columns
            assert columns["adapter_type"]["nullable"] is False
            assert columns["adapter_type"]["default"] == "'simulation'"
    finally:
        engine.dispose()


def test_upgrade_skips_when_digital_twin_table_is_absent():
    engine = sa.create_engine("sqlite://")
    try:
        with engine.begin() as connection:
            context = MigrationContext.configure(connection)
            with Operations.context(context):
                MIGRATION.upgrade()
    finally:
        engine.dispose()
