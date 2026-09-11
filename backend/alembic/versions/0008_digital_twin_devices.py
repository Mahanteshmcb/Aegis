"""Create persisted digital-twin device state."""
from alembic import op
import sqlalchemy as sa


revision = "0008_digital_twin_devices"
down_revision = "0007_notification_rules"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "digital_twin_devices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("zone_id", sa.Integer(), sa.ForeignKey("zones.id"), nullable=True),
        sa.Column("device_id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("device_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="online"),
        sa.Column("position", sa.JSON(), nullable=True),
        sa.Column("state", sa.JSON(), nullable=True),
        sa.Column("simulation_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_updated", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_digital_twin_devices_tenant_id", "digital_twin_devices", ["tenant_id"])
    op.create_index("ix_digital_twin_devices_zone_id", "digital_twin_devices", ["zone_id"])
    op.create_index("ix_digital_twin_devices_device_id", "digital_twin_devices", ["device_id"])


def downgrade():
    op.drop_index("ix_digital_twin_devices_device_id", table_name="digital_twin_devices")
    op.drop_index("ix_digital_twin_devices_zone_id", table_name="digital_twin_devices")
    op.drop_index("ix_digital_twin_devices_tenant_id", table_name="digital_twin_devices")
    op.drop_table("digital_twin_devices")