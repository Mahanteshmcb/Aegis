"""
Aegis Backend - Spatial Mapping Router

Day 33: REST API endpoints for 3D spatial mapping, crop positioning,
and biological species management.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.dependencies import get_current_user, get_db
from backend.models_db import BiologicalSpecies, SpatialZone, CropInstance, User
from ai.spatial_mapping import spatial_engine, VerticalLayer, Coordinate3D, CropProfile, SpatialZone as SpatialZoneModel

router = APIRouter(prefix="/api/v1/spatial", tags=["Spatial Mapping"])

logger = logging.getLogger(__name__)


# ============================================================================
# SCHEMAS
# ============================================================================

class BiologicalSpeciesCreate(BaseModel):
    scientific_name: str = Field(..., description="Scientific name (e.g., 'Solanum lycopersicum')")
    common_name: str = Field(..., description="Common name (e.g., 'Tomato')")
    family: Optional[str] = None
    genus: Optional[str] = None
    species: Optional[str] = None
    max_height_cm: Optional[float] = None
    canopy_radius_cm: Optional[float] = None
    root_depth_cm: Optional[float] = None
    growth_cycle_days: Optional[int] = None
    vertical_layer: str = Field(..., description="Vertical layer: 'ground', 'mid_canopy', 'upper'")
    optimal_temp_min_c: Optional[float] = None
    optimal_temp_max_c: Optional[float] = None
    optimal_humidity_percent: Optional[float] = None
    soil_ph_min: Optional[float] = None
    soil_ph_max: Optional[float] = None
    light_requirement: Optional[str] = None
    companion_species: List[int] = Field(default_factory=list)
    antagonistic_species: List[int] = Field(default_factory=list)
    description: Optional[str] = None
    nutritional_value: Dict[str, Any] = Field(default_factory=dict)
    medicinal_properties: Dict[str, Any] = Field(default_factory=dict)


class BiologicalSpeciesResponse(BiologicalSpeciesCreate):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]


class SpatialZoneCreate(BaseModel):
    name: str
    description: Optional[str] = None
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    min_z: float = 0.0
    max_z: float = 3.0
    zone_type: Optional[str] = None
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    sunlight_exposure: Optional[str] = None
    microclimate: Dict[str, Any] = Field(default_factory=dict)
    supports_ground_layer: bool = True
    supports_mid_canopy: bool = True
    supports_upper_canopy: bool = False
    max_capacity: Optional[int] = None


class SpatialZoneResponse(SpatialZoneCreate):
    id: int
    tenant_id: int
    current_occupancy: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]


class CropInstanceCreate(BaseModel):
    species_id: int
    spatial_zone_id: int
    position_x: float
    position_y: float
    position_z: float
    planting_date: Optional[datetime] = None
    expected_harvest_date: Optional[datetime] = None
    vertical_layer: str
    planting_soil_ph: Optional[float] = None
    planting_soil_moisture: Optional[float] = None
    planting_temperature_c: Optional[float] = None
    notes: Optional[str] = None
    batch_id: Optional[str] = None


class CropInstanceResponse(CropInstanceCreate):
    id: int
    actual_harvest_date: Optional[datetime]
    harvest_yield_kg: Optional[float]
    current_height_cm: Optional[float]
    health_status: str
    growth_stage: Optional[str]
    last_watered: Optional[datetime]
    last_fertilized: Optional[datetime]
    last_pruned: Optional[datetime]
    pest_incidents: List[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]


class SpatialOptimizationRequest(BaseModel):
    zone_id: int
    crop_instances: List[Dict[str, Any]] = Field(..., description="List of crop instance data with species_id and id")


class Coordinate3DModel(BaseModel):
    x: float
    y: float
    z: float


class SpatialQueryRequest(BaseModel):
    zone_id: Optional[int] = None
    species_id: Optional[int] = None
    vertical_layer: Optional[str] = None
    health_status: Optional[str] = None
    min_x: Optional[float] = None
    max_x: Optional[float] = None
    min_y: Optional[float] = None
    max_y: Optional[float] = None
    min_z: Optional[float] = None
    max_z: Optional[float] = None


# ============================================================================
# BIOLOGICAL SPECIES ENDPOINTS
# ============================================================================

@router.post("/species", response_model=BiologicalSpeciesResponse)
async def create_biological_species(
    species: BiologicalSpeciesCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new biological species entry."""
    # Check if species already exists
    existing = db.query(BiologicalSpecies).filter(
        BiologicalSpecies.scientific_name == species.scientific_name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Species already exists")

    db_species = BiologicalSpecies(**species.dict())
    db.add(db_species)
    db.commit()
    db.refresh(db_species)

    # Register with spatial engine
    profile = CropProfile(
        species_id=db_species.id,
        scientific_name=db_species.scientific_name,
        max_height_cm=db_species.max_height_cm or 0,
        canopy_radius_cm=db_species.canopy_radius_cm or 0,
        vertical_layer=VerticalLayer(db_species.vertical_layer),
        companion_species=set(db_species.companion_species or []),
        antagonistic_species=set(db_species.antagonistic_species or [])
    )
    spatial_engine.register_crop_profile(profile)

    return db_species


@router.get("/species", response_model=List[BiologicalSpeciesResponse])
async def list_biological_species(
    skip: int = 0,
    limit: int = 100,
    scientific_name: Optional[str] = None,
    common_name: Optional[str] = None,
    vertical_layer: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List biological species with optional filtering."""
    query = db.query(BiologicalSpecies)

    if scientific_name:
        query = query.filter(BiologicalSpecies.scientific_name.ilike(f"%{scientific_name}%"))
    if common_name:
        query = query.filter(BiologicalSpecies.common_name.ilike(f"%{common_name}%"))
    if vertical_layer:
        query = query.filter(BiologicalSpecies.vertical_layer == vertical_layer)

    return query.offset(skip).limit(limit).all()


@router.get("/species/{species_id}", response_model=BiologicalSpeciesResponse)
async def get_biological_species(
    species_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific biological species."""
    species = db.query(BiologicalSpecies).filter(BiologicalSpecies.id == species_id).first()
    if not species:
        raise HTTPException(status_code=404, detail="Species not found")
    return species


# ============================================================================
# SPATIAL ZONES ENDPOINTS
# ============================================================================

@router.post("/zones", response_model=SpatialZoneResponse)
async def create_spatial_zone(
    zone: SpatialZoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new spatial zone."""
    db_zone = SpatialZone(
        tenant_id=current_user.tenant_id,
        **zone.dict()
    )
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)

    # Register with spatial engine
    spatial_zone = SpatialZoneModel(
        zone_id=db_zone.id,
        min_x=db_zone.min_x,
        max_x=db_zone.max_x,
        min_y=db_zone.min_y,
        max_y=db_zone.max_y,
        min_z=db_zone.min_z,
        max_z=db_zone.max_z,
        supports_ground=db_zone.supports_ground_layer,
        supports_mid_canopy=db_zone.supports_mid_canopy,
        supports_upper=db_zone.supports_upper_canopy
    )
    spatial_engine.register_spatial_zone(spatial_zone)

    return db_zone


@router.get("/zones", response_model=List[SpatialZoneResponse])
async def list_spatial_zones(
    skip: int = 0,
    limit: int = 100,
    zone_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List spatial zones for the current tenant."""
    query = db.query(SpatialZone).filter(SpatialZone.tenant_id == current_user.tenant_id)

    if zone_type:
        query = query.filter(SpatialZone.zone_type == zone_type)
    if is_active is not None:
        query = query.filter(SpatialZone.is_active == is_active)

    return query.offset(skip).limit(limit).all()


@router.get("/zones/{zone_id}", response_model=SpatialZoneResponse)
async def get_spatial_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific spatial zone."""
    zone = db.query(SpatialZone).filter(
        SpatialZone.id == zone_id,
        SpatialZone.tenant_id == current_user.tenant_id
    ).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


# ============================================================================
# CROP INSTANCES ENDPOINTS
# ============================================================================

@router.post("/crops", response_model=CropInstanceResponse)
async def create_crop_instance(
    crop: CropInstanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new crop instance with 3D positioning."""
    # Validate zone belongs to tenant
    zone = db.query(SpatialZone).filter(
        SpatialZone.id == crop.spatial_zone_id,
        SpatialZone.tenant_id == current_user.tenant_id
    ).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found or access denied")

    # Validate species exists
    species = db.query(BiologicalSpecies).filter(BiologicalSpecies.id == crop.species_id).first()
    if not species:
        raise HTTPException(status_code=404, detail="Species not found")

    # Check for spatial collisions
    position = Coordinate3D(crop.position_x, crop.position_y, crop.position_z)
    collision = spatial_engine.check_collision(
        crop.spatial_zone_id,
        position,
        (species.canopy_radius_cm or 0) / 100,  # Convert cm to meters
        VerticalLayer(crop.vertical_layer)
    )

    if collision:
        raise HTTPException(status_code=400, detail="Spatial collision detected at proposed position")

    db_crop = CropInstance(**crop.dict())
    db.add(db_crop)
    db.commit()
    db.refresh(db_crop)

    # Update zone occupancy
    zone.current_occupancy += 1
    db.commit()

    return db_crop


@router.get("/crops", response_model=List[CropInstanceResponse])
async def list_crop_instances(
    query: SpatialQueryRequest = Depends(),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List crop instances with spatial filtering."""
    query_db = db.query(CropInstance).join(SpatialZone).filter(
        SpatialZone.tenant_id == current_user.tenant_id
    )

    if query.zone_id:
        query_db = query_db.filter(CropInstance.spatial_zone_id == query.zone_id)
    if query.species_id:
        query_db = query_db.filter(CropInstance.species_id == query.species_id)
    if query.vertical_layer:
        query_db = query_db.filter(CropInstance.vertical_layer == query.vertical_layer)
    if query.health_status:
        query_db = query_db.filter(CropInstance.health_status == query.health_status)

    # Spatial bounds filtering
    if query.min_x is not None:
        query_db = query_db.filter(CropInstance.position_x >= query.min_x)
    if query.max_x is not None:
        query_db = query_db.filter(CropInstance.position_x <= query.max_x)
    if query.min_y is not None:
        query_db = query_db.filter(CropInstance.position_y >= query.min_y)
    if query.max_y is not None:
        query_db = query_db.filter(CropInstance.position_y <= query.max_y)
    if query.min_z is not None:
        query_db = query_db.filter(CropInstance.position_z >= query.min_z)
    if query.max_z is not None:
        query_db = query_db.filter(CropInstance.position_z <= query.max_z)

    return query_db.offset(skip).limit(limit).all()


@router.post("/optimize", response_model=Dict[str, Any])
async def optimize_zone_layout(
    request: SpatialOptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Optimize the spatial layout of crops in a zone."""
    # Validate zone belongs to tenant
    zone = db.query(SpatialZone).filter(
        SpatialZone.id == request.zone_id,
        SpatialZone.tenant_id == current_user.tenant_id
    ).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found or access denied")

    # Run optimization
    result = spatial_engine.optimize_zone_layout(request.zone_id, request.crop_instances)

    return result


@router.get("/layers/{zone_id}", response_model=Dict[str, List[Dict[str, Any]]])
async def get_vertical_layers(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get crop distribution across vertical layers in a zone."""
    # Validate zone access
    zone = db.query(SpatialZone).filter(
        SpatialZone.id == zone_id,
        SpatialZone.tenant_id == current_user.tenant_id
    ).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found or access denied")

    # Query crops by layer
    layers = {}
    for layer in ["ground", "mid_canopy", "upper"]:
        crops = db.query(CropInstance).filter(
            CropInstance.spatial_zone_id == zone_id,
            CropInstance.vertical_layer == layer,
            CropInstance.is_active == True
        ).all()

        layers[layer] = [
            {
                "id": crop.id,
                "species_id": crop.species_id,
                "position": {"x": crop.position_x, "y": crop.position_y, "z": crop.position_z},
                "health_status": crop.health_status,
                "growth_stage": crop.growth_stage
            }
            for crop in crops
        ]

    return layers