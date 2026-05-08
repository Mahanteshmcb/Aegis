"""
Add 3D spatial mapping models for Day 33.

Revision ID: 0002_spatial_mapping
Revises: 0001_initial
Create Date: 2026-05-09 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_spatial_mapping'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

def upgrade():
    # Create biological_species table
    op.create_table(
        'biological_species',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('scientific_name', sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column('common_name', sa.String(length=255), nullable=False, index=True),
        sa.Column('family', sa.String(length=100), index=True),
        sa.Column('genus', sa.String(length=100), index=True),
        sa.Column('species', sa.String(length=100), index=True),
        sa.Column('max_height_cm', sa.Float()),
        sa.Column('canopy_radius_cm', sa.Float()),
        sa.Column('root_depth_cm', sa.Float()),
        sa.Column('growth_cycle_days', sa.Integer()),
        sa.Column('vertical_layer', sa.String(length=20)),
        sa.Column('optimal_temp_min_c', sa.Float()),
        sa.Column('optimal_temp_max_c', sa.Float()),
        sa.Column('optimal_humidity_percent', sa.Float()),
        sa.Column('soil_ph_min', sa.Float()),
        sa.Column('soil_ph_max', sa.Float()),
        sa.Column('light_requirement', sa.String(length=50)),
        sa.Column('companion_species', sa.JSON(), default=list),
        sa.Column('antagonistic_species', sa.JSON(), default=list),
        sa.Column('description', sa.Text()),
        sa.Column('nutritional_value', sa.JSON(), default=dict),
        sa.Column('medicinal_properties', sa.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # Create spatial_zones table
    op.create_table(
        'spatial_zones',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('min_x', sa.Float(), nullable=False),
        sa.Column('max_x', sa.Float(), nullable=False),
        sa.Column('min_y', sa.Float(), nullable=False),
        sa.Column('max_y', sa.Float(), nullable=False),
        sa.Column('min_z', sa.Float(), nullable=False, default=0.0),
        sa.Column('max_z', sa.Float(), nullable=False, default=3.0),
        sa.Column('zone_type', sa.String(length=50)),
        sa.Column('soil_type', sa.String(length=100)),
        sa.Column('irrigation_type', sa.String(length=50)),
        sa.Column('sunlight_exposure', sa.String(length=50)),
        sa.Column('microclimate', sa.JSON(), default=dict),
        sa.Column('supports_ground_layer', sa.Boolean(), default=True),
        sa.Column('supports_mid_canopy', sa.Boolean(), default=True),
        sa.Column('supports_upper_canopy', sa.Boolean(), default=False),
        sa.Column('max_capacity', sa.Integer()),
        sa.Column('current_occupancy', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # Create crop_instances table
    op.create_table(
        'crop_instances',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('species_id', sa.Integer(), sa.ForeignKey('biological_species.id'), nullable=False, index=True),
        sa.Column('spatial_zone_id', sa.Integer(), sa.ForeignKey('spatial_zones.id'), nullable=False, index=True),
        sa.Column('position_x', sa.Float(), nullable=False),
        sa.Column('position_y', sa.Float(), nullable=False),
        sa.Column('position_z', sa.Float(), nullable=False),
        sa.Column('planting_date', sa.DateTime()),
        sa.Column('expected_harvest_date', sa.DateTime()),
        sa.Column('actual_harvest_date', sa.DateTime()),
        sa.Column('harvest_yield_kg', sa.Float()),
        sa.Column('current_height_cm', sa.Float()),
        sa.Column('health_status', sa.String(length=50), default='healthy'),
        sa.Column('growth_stage', sa.String(length=50)),
        sa.Column('vertical_layer', sa.String(length=20), nullable=False),
        sa.Column('planting_soil_ph', sa.Float()),
        sa.Column('planting_soil_moisture', sa.Float()),
        sa.Column('planting_temperature_c', sa.Float()),
        sa.Column('last_watered', sa.DateTime()),
        sa.Column('last_fertilized', sa.DateTime()),
        sa.Column('last_pruned', sa.DateTime()),
        sa.Column('pest_incidents', sa.JSON(), default=list),
        sa.Column('notes', sa.Text()),
        sa.Column('batch_id', sa.String(length=100)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # Add indexes for performance
    op.create_index('ix_biological_species_scientific_name', 'biological_species', ['scientific_name'])
    op.create_index('ix_biological_species_common_name', 'biological_species', ['common_name'])
    op.create_index('ix_spatial_zones_tenant_id', 'spatial_zones', ['tenant_id'])
    op.create_index('ix_crop_instances_species_id', 'crop_instances', ['species_id'])
    op.create_index('ix_crop_instances_spatial_zone_id', 'crop_instances', ['spatial_zone_id'])
    op.create_index('ix_crop_instances_position', 'crop_instances', ['position_x', 'position_y', 'position_z'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('crop_instances')
    op.drop_table('spatial_zones')
    op.drop_table('biological_species')