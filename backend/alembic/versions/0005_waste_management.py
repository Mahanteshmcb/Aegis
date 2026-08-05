"""Waste management system tables.

Revision ID: 0005_waste_management
Revises: 0004_water_management
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0005_waste_management'
down_revision = '0004_water_management'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create waste_containers table
    op.create_table(
        'waste_containers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('container_name', sa.String(200), nullable=False),
        sa.Column('waste_type', sa.String(100), nullable=False),
        sa.Column('capacity_kg', sa.Float(), nullable=False),
        sa.Column('current_load_kg', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_emptied', sa.DateTime(), nullable=True),
        sa.Column('emptying_frequency_days', sa.Integer(), server_default='7', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_waste_containers_id'), 'waste_containers', ['id'], unique=False)
    op.create_index(op.f('ix_waste_containers_tenant_id'), 'waste_containers', ['tenant_id'], unique=False)

    # Create waste_sorting_logs table
    op.create_table(
        'waste_sorting_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('waste_stream_id', sa.Integer(), nullable=True),
        sa.Column('waste_type', sa.String(100), nullable=False),
        sa.Column('weight_kg', sa.Float(), nullable=False),
        sa.Column('source_location', sa.String(200), nullable=True),
        sa.Column('destination_container', sa.String(200), nullable=True),
        sa.Column('sorting_method', sa.String(100), nullable=False),
        sa.Column('contamination_detected', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('contamination_type', sa.String(200), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_waste_sorting_logs_id'), 'waste_sorting_logs', ['id'], unique=False)
    op.create_index(op.f('ix_waste_sorting_logs_tenant_id'), 'waste_sorting_logs', ['tenant_id'], unique=False)

    # Create composting_processes table
    op.create_table(
        'composting_processes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('process_name', sa.String(200), nullable=False),
        sa.Column('pile_id', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), server_default='preparing', nullable=False),
        sa.Column('organic_input_kg', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('current_weight_kg', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('moisture_percent', sa.Float(), nullable=True),
        sa.Column('temperature_celsius', sa.Float(), nullable=True),
        sa.Column('carbon_nitrogen_ratio', sa.Float(), nullable=True),
        sa.Column('stage', sa.String(50), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('expected_completion', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('compost_output_kg', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('pathogen_tested', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('pathogen_safe', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_composting_processes_id'), 'composting_processes', ['id'], unique=False)
    op.create_index(op.f('ix_composting_processes_tenant_id'), 'composting_processes', ['tenant_id'], unique=False)

    # Create recycling_processes table
    op.create_table(
        'recycling_processes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('process_name', sa.String(200), nullable=False),
        sa.Column('material_type', sa.String(100), nullable=False),
        sa.Column('input_weight_kg', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('current_weight_kg', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('status', sa.String(50), server_default='pending', nullable=False),
        sa.Column('recovery_rate_percent', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('output_material_type', sa.String(100), nullable=True),
        sa.Column('output_weight_kg', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('destination_facility', sa.String(200), nullable=True),
        sa.Column('processing_method', sa.String(100), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('cost_per_kg', sa.Float(), nullable=True),
        sa.Column('environmental_impact_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recycling_processes_id'), 'recycling_processes', ['id'], unique=False)
    op.create_index(op.f('ix_recycling_processes_tenant_id'), 'recycling_processes', ['tenant_id'], unique=False)

    # Create hazardous_waste_storage table
    op.create_table(
        'hazardous_waste_storage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('container_id', sa.String(100), nullable=False),
        sa.Column('chemical_name', sa.String(200), nullable=False),
        sa.Column('chemical_type', sa.String(100), nullable=False),
        sa.Column('cas_number', sa.String(50), nullable=True),
        sa.Column('quantity_liters', sa.Float(), nullable=False),
        sa.Column('concentration_percent', sa.Float(), nullable=True),
        sa.Column('hazard_classification', sa.String(200), nullable=True),
        sa.Column('physical_state', sa.String(50), nullable=False),
        sa.Column('storage_location', sa.String(200), nullable=False),
        sa.Column('storage_temperature_min', sa.Float(), nullable=True),
        sa.Column('storage_temperature_max', sa.Float(), nullable=True),
        sa.Column('container_condition', sa.String(50), server_default='good', nullable=False),
        sa.Column('is_sealed', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('leak_detection_sensor', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('ventilation_required', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('last_inspected', sa.DateTime(), nullable=True),
        sa.Column('inspection_interval_days', sa.Integer(), server_default='30', nullable=False),
        sa.Column('disposal_scheduled', sa.DateTime(), nullable=True),
        sa.Column('disposal_facility', sa.String(200), nullable=True),
        sa.Column('safety_data_sheet_available', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hazardous_waste_storage_id'), 'hazardous_waste_storage', ['id'], unique=False)
    op.create_index(op.f('ix_hazardous_waste_storage_tenant_id'), 'hazardous_waste_storage', ['tenant_id'], unique=False)

    # Create waste_processing_logs table
    op.create_table(
        'waste_processing_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('operation_type', sa.String(100), nullable=False),
        sa.Column('waste_category', sa.String(100), nullable=False),
        sa.Column('input_weight_kg', sa.Float(), nullable=False),
        sa.Column('output_weight_kg', sa.Float(), nullable=True),
        sa.Column('processing_efficiency_percent', sa.Float(), nullable=True),
        sa.Column('energy_consumed_kwh', sa.Float(), nullable=True),
        sa.Column('emissions_kg_co2', sa.Float(), nullable=True),
        sa.Column('processing_time_hours', sa.Float(), nullable=True),
        sa.Column('operator', sa.String(200), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_waste_processing_logs_id'), 'waste_processing_logs', ['id'], unique=False)
    op.create_index(op.f('ix_waste_processing_logs_tenant_id'), 'waste_processing_logs', ['tenant_id'], unique=False)

    # Create waste_metrics table
    op.create_table(
        'waste_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('metric_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('total_waste_collected_kg', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('organic_waste_kg', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('recyclable_waste_kg', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('hazardous_waste_kg', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('inert_waste_kg', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('compost_produced_kg', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('recycled_material_kg', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('landfill_waste_kg', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('recycling_rate_percent', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('waste_diversion_rate_percent', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('total_emissions_kg_co2', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('cost_per_kg', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_waste_metrics_id'), 'waste_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_waste_metrics_tenant_id'), 'waste_metrics', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_waste_metrics_tenant_id'), table_name='waste_metrics')
    op.drop_index(op.f('ix_waste_metrics_id'), table_name='waste_metrics')
    op.drop_table('waste_metrics')

    op.drop_index(op.f('ix_waste_processing_logs_tenant_id'), table_name='waste_processing_logs')
    op.drop_index(op.f('ix_waste_processing_logs_id'), table_name='waste_processing_logs')
    op.drop_table('waste_processing_logs')

    op.drop_index(op.f('ix_hazardous_waste_storage_tenant_id'), table_name='hazardous_waste_storage')
    op.drop_index(op.f('ix_hazardous_waste_storage_id'), table_name='hazardous_waste_storage')
    op.drop_table('hazardous_waste_storage')

    op.drop_index(op.f('ix_recycling_processes_tenant_id'), table_name='recycling_processes')
    op.drop_index(op.f('ix_recycling_processes_id'), table_name='recycling_processes')
    op.drop_table('recycling_processes')

    op.drop_index(op.f('ix_composting_processes_tenant_id'), table_name='composting_processes')
    op.drop_index(op.f('ix_composting_processes_id'), table_name='composting_processes')
    op.drop_table('composting_processes')

    op.drop_index(op.f('ix_waste_sorting_logs_tenant_id'), table_name='waste_sorting_logs')
    op.drop_index(op.f('ix_waste_sorting_logs_id'), table_name='waste_sorting_logs')
    op.drop_table('waste_sorting_logs')

    op.drop_index(op.f('ix_waste_containers_tenant_id'), table_name='waste_containers')
    op.drop_index(op.f('ix_waste_containers_id'), table_name='waste_containers')
    op.drop_table('waste_containers')
