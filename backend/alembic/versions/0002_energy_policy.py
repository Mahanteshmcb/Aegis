"""
Add energy_policies table for persisted charging policies.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_energy_policy'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'energy_policies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id'), nullable=True, index=True),
        sa.Column('name', sa.String(length=255)),
        sa.Column('charge_threshold', sa.Float(), nullable=False, server_default='0.6'),
        sa.Column('discharge_threshold', sa.Float(), nullable=False, server_default='0.3'),
        sa.Column('max_charge_rate_kw', sa.Float(), nullable=False, server_default='2.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table('energy_policies')
