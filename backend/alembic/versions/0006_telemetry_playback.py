"""
Alembic migration: add telemetry_playback_sessions table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0006_telemetry_playback'
down_revision = '0005_waste_management'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'telemetry_playback_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('playback_speed', sa.Float(), nullable=False, default=1.0),
        sa.Column('status', sa.String(length=50), nullable=False, default='stopped'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

def downgrade():
    op.drop_table('telemetry_playback_sessions')
