"""Persist surveyed orientation and device spatial provenance."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0016_spatial_orientation"
down_revision = "0015_device_adapter_type"
branch_labels = None
depends_on = None


def _add_missing_columns(table_name, columns):
    inspector = inspect(op.get_bind())
    if not inspector.has_table(table_name):
        return
    existing = {column["name"] for column in inspector.get_columns(table_name)}
    for column_name, column in columns:
        if column_name not in existing:
            op.add_column(table_name, column)


def upgrade():
    _add_missing_columns(
        "zones",
        [("orientation", sa.Column("orientation", sa.JSON(), nullable=True))],
    )
    _add_missing_columns(
        "digital_twin_devices",
        [
            ("orientation", sa.Column("orientation", sa.JSON(), nullable=True)),
            ("spatial_status", sa.Column("spatial_status", sa.String(length=24), nullable=False, server_default="inferred")),
            ("coordinate_system", sa.Column("coordinate_system", sa.String(length=100), nullable=True)),
            ("length_unit", sa.Column("length_unit", sa.String(length=16), nullable=False, server_default="m")),
        ],
    )


def downgrade():
    inspector = inspect(op.get_bind())
    for table_name, columns in [
        ("digital_twin_devices", ("length_unit", "coordinate_system", "spatial_status", "orientation")),
        ("zones", ("orientation",)),
    ]:
        if not inspector.has_table(table_name):
            continue
        existing = {column["name"] for column in inspector.get_columns(table_name)}
        for column_name in columns:
            if column_name in existing:
                op.drop_column(table_name, column_name)
