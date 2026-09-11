"""Add manual, automation, and AI control metadata to virtual devices."""
from alembic import op
import sqlalchemy as sa


revision = "0011_device_control_modes"
down_revision = "0010_estate_hierarchy"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("digital_twin_devices", sa.Column("control_mode", sa.String(length=24), nullable=False, server_default="automation"))
    op.add_column("digital_twin_devices", sa.Column("automation_policy", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("digital_twin_devices", "automation_policy")
    op.drop_column("digital_twin_devices", "control_mode")