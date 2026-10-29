"""Track whether a device position is explicitly configured."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0017_device_position_provenance"
down_revision = "0016_spatial_orientation"
branch_labels = None
depends_on = None


def upgrade():
    inspector = inspect(op.get_bind())
    if not inspector.has_table("digital_twin_devices"):
        return
    columns = {column["name"] for column in inspector.get_columns("digital_twin_devices")}
    if "position_configured" not in columns:
        op.add_column(
            "digital_twin_devices",
            sa.Column("position_configured", sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade():
    inspector = inspect(op.get_bind())
    if not inspector.has_table("digital_twin_devices"):
        return
    columns = {column["name"] for column in inspector.get_columns("digital_twin_devices")}
    if "position_configured" in columns:
        op.drop_column("digital_twin_devices", "position_configured")
