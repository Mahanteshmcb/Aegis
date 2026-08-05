"""
Create security patrol and evacuation protocol tables for Day 65.

Revision ID: 0003_security_patrols_evacuation
Revises: 0002_spatial_mapping
Create Date: 2026-05-29 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_security_patrols_evacuation'
down_revision = '0002_spatial_mapping'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'security_patrols',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, default=False),
        sa.Column('route_name', sa.String(length=200), nullable=True),
        sa.Column('assigned_robot', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, default='idle'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_security_patrols_tenant_id', 'security_patrols', ['tenant_id'])

    op.create_table(
        'evacuation_protocols',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, default=False),
        sa.Column('initiated_by', sa.String(length=120), nullable=True),
        sa.Column('incident_type', sa.String(length=120), nullable=True),
        sa.Column('affected_zones', sa.String(length=500), nullable=True),
        sa.Column('stage', sa.String(length=120), nullable=False, default='standby'),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_evacuation_protocols_tenant_id', 'evacuation_protocols', ['tenant_id'])


def downgrade():
    op.drop_index('ix_evacuation_protocols_tenant_id', table_name='evacuation_protocols')
    op.drop_table('evacuation_protocols')
    op.drop_index('ix_security_patrols_tenant_id', table_name='security_patrols')
    op.drop_table('security_patrols')
