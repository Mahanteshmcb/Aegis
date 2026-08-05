"""Water management system tables.

Revision ID: 0004_water_management
Revises: 0003_security_patrols_evacuation
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0004_water_management'
down_revision = '0003_security_patrols_evacuation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create water_collection_systems table
    op.create_table(
        'water_collection_systems',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('system_name', sa.String(200), nullable=False),
        sa.Column('collection_type', sa.String(100), nullable=False),
        sa.Column('capacity_liters', sa.Float(), nullable=False),
        sa.Column('current_volume_liters', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('last_emptied', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_water_collection_systems_id'), 'water_collection_systems', ['id'], unique=False)
    op.create_index(op.f('ix_water_collection_systems_tenant_id'), 'water_collection_systems', ['tenant_id'], unique=False)

    # Create water_purification_units table
    op.create_table(
        'water_purification_units',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('unit_name', sa.String(200), nullable=False),
        sa.Column('purification_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), server_default='ready', nullable=False),
        sa.Column('flow_rate_lpm', sa.Float(), nullable=True),
        sa.Column('efficiency_percent', sa.Float(), server_default='95.0', nullable=False),
        sa.Column('input_volume_liters', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('output_volume_liters', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('last_maintenance', sa.DateTime(), nullable=True),
        sa.Column('maintenance_interval_days', sa.Integer(), server_default='30', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_water_purification_units_id'), 'water_purification_units', ['id'], unique=False)
    op.create_index(op.f('ix_water_purification_units_tenant_id'), 'water_purification_units', ['tenant_id'], unique=False)

    # Create irrigation_systems table
    op.create_table(
        'irrigation_systems',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('system_name', sa.String(200), nullable=False),
        sa.Column('zone_id', sa.Integer(), nullable=True),
        sa.Column('irrigation_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), server_default='idle', nullable=False),
        sa.Column('scheduled_frequency_minutes', sa.Integer(), nullable=True),
        sa.Column('last_watering', sa.DateTime(), nullable=True),
        sa.Column('next_scheduled_watering', sa.DateTime(), nullable=True),
        sa.Column('water_per_cycle_liters', sa.Float(), nullable=True),
        sa.Column('optimization_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('soil_moisture_target_percent', sa.Float(), server_default='60.0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['zone_id'], ['zones.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_irrigation_systems_id'), 'irrigation_systems', ['id'], unique=False)
    op.create_index(op.f('ix_irrigation_systems_tenant_id'), 'irrigation_systems', ['tenant_id'], unique=False)

    # Create water_quality_readings table
    op.create_table(
        'water_quality_readings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('reading_location', sa.String(200), nullable=False),
        sa.Column('ph_level', sa.Float(), nullable=True),
        sa.Column('turbidity_ntu', sa.Float(), nullable=True),
        sa.Column('total_dissolved_solids_ppm', sa.Float(), nullable=True),
        sa.Column('chlorine_ppm', sa.Float(), nullable=True),
        sa.Column('dissolved_oxygen_ppm', sa.Float(), nullable=True),
        sa.Column('temperature_celsius', sa.Float(), nullable=True),
        sa.Column('bacterial_count_cfu_ml', sa.Float(), nullable=True),
        sa.Column('contamination_detected', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('contamination_type', sa.String(200), nullable=True),
        sa.Column('contaminant_level_ppm', sa.Float(), nullable=True),
        sa.Column('overall_quality_status', sa.String(50), server_default='good', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_water_quality_readings_id'), 'water_quality_readings', ['id'], unique=False)
    op.create_index(op.f('ix_water_quality_readings_tenant_id'), 'water_quality_readings', ['tenant_id'], unique=False)

    # Create water_recycling_loops table
    op.create_table(
        'water_recycling_loops',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('loop_name', sa.String(200), nullable=False),
        sa.Column('loop_type', sa.String(100), nullable=False),
        sa.Column('source_system', sa.String(200), nullable=True),
        sa.Column('destination_system', sa.String(200), nullable=True),
        sa.Column('active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('daily_recycled_liters', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('total_recycled_liters', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('efficiency_percent', sa.Float(), server_default='85.0', nullable=False),
        sa.Column('last_cycle', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_water_recycling_loops_id'), 'water_recycling_loops', ['id'], unique=False)
    op.create_index(op.f('ix_water_recycling_loops_tenant_id'), 'water_recycling_loops', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_water_recycling_loops_tenant_id'), table_name='water_recycling_loops')
    op.drop_index(op.f('ix_water_recycling_loops_id'), table_name='water_recycling_loops')
    op.drop_table('water_recycling_loops')

    op.drop_index(op.f('ix_water_quality_readings_tenant_id'), table_name='water_quality_readings')
    op.drop_index(op.f('ix_water_quality_readings_id'), table_name='water_quality_readings')
    op.drop_table('water_quality_readings')

    op.drop_index(op.f('ix_irrigation_systems_tenant_id'), table_name='irrigation_systems')
    op.drop_index(op.f('ix_irrigation_systems_id'), table_name='irrigation_systems')
    op.drop_table('irrigation_systems')

    op.drop_index(op.f('ix_water_purification_units_tenant_id'), table_name='water_purification_units')
    op.drop_index(op.f('ix_water_purification_units_id'), table_name='water_purification_units')
    op.drop_table('water_purification_units')

    op.drop_index(op.f('ix_water_collection_systems_tenant_id'), table_name='water_collection_systems')
    op.drop_index(op.f('ix_water_collection_systems_id'), table_name='water_collection_systems')
    op.drop_table('water_collection_systems')
