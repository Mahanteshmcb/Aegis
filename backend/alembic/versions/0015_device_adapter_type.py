"""Associate twin devices with a simulation or hardware transport adapter."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0015_device_adapter_type"
down_revision = "0014_zone_geometry_defaults"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("digital_twin_devices"):
        return
    columns = {column["name"] for column in inspector.get_columns("digital_twin_devices")}
    if "adapter_type" not in columns:
        op.add_column(
            "digital_twin_devices",
            sa.Column("adapter_type", sa.String(length=24), nullable=False, server_default="simulation"),
        )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if inspector.has_table("digital_twin_devices"):
        columns = {column["name"] for column in inspector.get_columns("digital_twin_devices")}
        if "adapter_type" in columns:
            op.drop_column("digital_twin_devices", "adapter_type")
