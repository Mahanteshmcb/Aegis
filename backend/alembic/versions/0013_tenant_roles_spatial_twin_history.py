"""Persist tenant roles, surveyed zone geometry, and digital-twin history/media."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0013_tenant_roles_spatial_twin_history"
down_revision = ("0012_structured_audit_events", "0002_energy_policy")
branch_labels = None
depends_on = None


def _ensure_index(table_name, index_name, columns):
    inspector = inspect(op.get_bind())
    if inspector.has_table(table_name):
        existing = {index["name"] for index in inspector.get_indexes(table_name)}
        if index_name not in existing:
            op.create_index(index_name, table_name, columns)


def upgrade():
    inspector = inspect(op.get_bind())
    if not inspector.has_table("role_definitions"):
        op.create_table(
            "role_definitions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
            sa.Column("key", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.String(length=500), nullable=True),
            sa.Column("permissions", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("tenant_id", "key", name="uq_role_definitions_tenant_key"),
        )
    _ensure_index("role_definitions", "ix_role_definitions_tenant_id", ["tenant_id"])

    zone_columns = {column["name"] for column in inspector.get_columns("zones")}
    missing_zone_columns = [
        (name, column)
        for name, column in [
            ("spatial_position", sa.Column("spatial_position", sa.JSON(), nullable=True)),
            ("dimensions", sa.Column("dimensions", sa.JSON(), nullable=True)),
            ("spatial_status", sa.Column("spatial_status", sa.String(length=24), nullable=False, server_default="inferred")),
            ("coordinate_system", sa.Column("coordinate_system", sa.String(length=100), nullable=True)),
            ("length_unit", sa.Column("length_unit", sa.String(length=16), nullable=False, server_default="m")),
        ]
        if name not in zone_columns
    ]
    if missing_zone_columns:
        with op.batch_alter_table("zones") as batch_op:
            for _, column in missing_zone_columns:
                batch_op.add_column(column)

    if not inspector.has_table("digital_twin_telemetry"):
        op.create_table(
            "digital_twin_telemetry",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
            sa.Column("device_id", sa.Integer(), sa.ForeignKey("digital_twin_devices.id", ondelete="CASCADE"), nullable=False),
            sa.Column("snapshot", sa.JSON(), nullable=False),
            sa.Column("recorded_at", sa.DateTime(), nullable=False),
        )
    _ensure_index("digital_twin_telemetry", "ix_digital_twin_telemetry_tenant_id", ["tenant_id"])
    _ensure_index("digital_twin_telemetry", "ix_digital_twin_telemetry_device_id", ["device_id"])
    _ensure_index("digital_twin_telemetry", "ix_digital_twin_telemetry_recorded_at", ["recorded_at"])
    _ensure_index(
        "digital_twin_telemetry",
        "ix_digital_twin_telemetry_tenant_device_time",
        ["tenant_id", "device_id", "recorded_at"],
    )

    if not inspector.has_table("digital_twin_media"):
        op.create_table(
            "digital_twin_media",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
            sa.Column("device_id", sa.Integer(), sa.ForeignKey("digital_twin_devices.id", ondelete="CASCADE"), nullable=False),
            sa.Column("storage_key", sa.String(length=36), nullable=False, unique=True),
            sa.Column("original_name", sa.String(length=255), nullable=False),
            sa.Column("content_type", sa.String(length=100), nullable=False),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
        )
    _ensure_index("digital_twin_media", "ix_digital_twin_media_tenant_id", ["tenant_id"])
    _ensure_index("digital_twin_media", "ix_digital_twin_media_device_id", ["device_id"])
    _ensure_index("digital_twin_media", "ix_digital_twin_media_created_at", ["created_at"])
    _ensure_index("digital_twin_media", "ix_digital_twin_media_expires_at", ["expires_at"])


def downgrade():
    inspector = inspect(op.get_bind())
    for table_name, indexes in [
        ("digital_twin_media", [
            "ix_digital_twin_media_expires_at", "ix_digital_twin_media_created_at",
            "ix_digital_twin_media_device_id", "ix_digital_twin_media_tenant_id",
        ]),
        ("digital_twin_telemetry", [
            "ix_digital_twin_telemetry_tenant_device_time", "ix_digital_twin_telemetry_recorded_at",
            "ix_digital_twin_telemetry_device_id", "ix_digital_twin_telemetry_tenant_id",
        ]),
        ("role_definitions", ["ix_role_definitions_tenant_id"]),
    ]:
        if inspector.has_table(table_name):
            existing = {index["name"] for index in inspector.get_indexes(table_name)}
            for index_name in indexes:
                if index_name in existing:
                    op.drop_index(index_name, table_name=table_name)
            op.drop_table(table_name)
    zone_columns = {column["name"] for column in inspector.get_columns("zones")}
    columns_to_drop = [
        name for name in ("length_unit", "coordinate_system", "spatial_status", "dimensions", "spatial_position")
        if name in zone_columns
    ]
    if columns_to_drop:
        with op.batch_alter_table("zones") as batch_op:
            for column_name in columns_to_drop:
                batch_op.drop_column(column_name)
