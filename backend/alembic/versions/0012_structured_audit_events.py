"""Add structured actor and entity details to audit events."""
from alembic import op
import sqlalchemy as sa


revision = "0012_structured_audit_events"
down_revision = "0011_device_control_modes"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("audit_logs") as batch_op:
        batch_op.add_column(sa.Column("actor_user_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("actor_email", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("action", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("entity_type", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("entity_id", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("outcome", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("details", sa.JSON(), nullable=True))
        batch_op.create_index("ix_audit_logs_actor_user_id", ["actor_user_id"])
        batch_op.create_foreign_key("fk_audit_logs_actor_user_id_users", "users", ["actor_user_id"], ["id"])


def downgrade():
    with op.batch_alter_table("audit_logs") as batch_op:
        batch_op.drop_constraint("fk_audit_logs_actor_user_id_users", type_="foreignkey")
        batch_op.drop_index("ix_audit_logs_actor_user_id")
        batch_op.drop_column("details")
        batch_op.drop_column("outcome")
        batch_op.drop_column("entity_id")
        batch_op.drop_column("entity_type")
        batch_op.drop_column("action")
        batch_op.drop_column("actor_email")
        batch_op.drop_column("actor_user_id")