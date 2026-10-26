"""Persist selected 3D model filenames for scene entities."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0009_scene_entity_model"
down_revision = "0008_digital_twin_devices"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("scene_entities"):
        op.create_table(
            "scene_entities",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("tenant_id", sa.Integer(), nullable=True),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("type", sa.String(length=64), nullable=True),
            sa.Column("model", sa.String(length=128), nullable=True),
            sa.Column("x", sa.Float(), nullable=True),
            sa.Column("y", sa.Float(), nullable=True),
            sa.Column("z", sa.Float(), nullable=True),
            sa.Column("rotation", sa.Float(), nullable=True),
            sa.Column("state", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_scene_entities_id", "scene_entities", ["id"])
        op.create_index("ix_scene_entities_tenant_id", "scene_entities", ["tenant_id"])
        return

    if "model" not in {column["name"] for column in inspector.get_columns("scene_entities")}:
        op.add_column("scene_entities", sa.Column("model", sa.String(length=128), nullable=True))


def downgrade():
    if inspect(op.get_bind()).has_table("scene_entities"):
        columns = {column["name"] for column in inspect(op.get_bind()).get_columns("scene_entities")}
        if "model" in columns:
            with op.batch_alter_table("scene_entities") as batch_op:
                batch_op.drop_column("model")