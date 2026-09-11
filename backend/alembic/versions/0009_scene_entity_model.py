"""Persist selected 3D model filenames for scene entities."""
from alembic import op
import sqlalchemy as sa


revision = "0009_scene_entity_model"
down_revision = "0008_digital_twin_devices"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("scene_entities", sa.Column("model", sa.String(length=128), nullable=True))


def downgrade():
    op.drop_column("scene_entities", "model")