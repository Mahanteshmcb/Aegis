"""Create customer estate hierarchy tables."""
from alembic import op
import sqlalchemy as sa


revision = "0010_estate_hierarchy"
down_revision = "0009_scene_entity_model"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "estates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("layout", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_estates_tenant_id", "estates", ["tenant_id"])
    op.create_table(
        "estate_nodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("estate_id", sa.Integer(), sa.ForeignKey("estates.id"), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("estate_nodes.id"), nullable=True),
        sa.Column("node_type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("position", sa.JSON(), nullable=True),
        sa.Column("dimensions", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_estate_nodes_estate_id", "estate_nodes", ["estate_id"])
    op.create_index("ix_estate_nodes_parent_id", "estate_nodes", ["parent_id"])


def downgrade():
    op.drop_index("ix_estate_nodes_parent_id", table_name="estate_nodes")
    op.drop_index("ix_estate_nodes_estate_id", table_name="estate_nodes")
    op.drop_table("estate_nodes")
    op.drop_index("ix_estates_tenant_id", table_name="estates")
    op.drop_table("estates")