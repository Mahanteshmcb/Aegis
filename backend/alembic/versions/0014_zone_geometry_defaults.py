"""Backfill defaults for legacy zone spatial fields."""
from alembic import op
import sqlalchemy as sa


revision = "0014_zone_geometry_defaults"
down_revision = "0013_tenant_roles_spatial_twin_history"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        sa.text(
            "UPDATE zones SET spatial_status = 'inferred' "
            "WHERE spatial_status IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE zones SET length_unit = 'm' "
            "WHERE length_unit IS NULL"
        )
    )


def downgrade():
    pass
