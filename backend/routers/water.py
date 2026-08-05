"""
Water management API - collection, purification, irrigation, quality monitoring, and recycling.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from backend.dependencies import get_db, get_current_user
from backend.models.water import (
    WaterCollectionSystem,
    WaterPurificationUnit,
    IrrigationSystem,
    WaterQualityReading,
    WaterRecyclingLoop,
)

router = APIRouter(prefix="/api/v1/water", tags=["water"])


# --- SCHEMAS ---

class WaterCollectionSystemRequest(BaseModel):
    system_name: str
    collection_type: str
    capacity_liters: float
    location: Optional[str] = None


class WaterCollectionSystemResponse(BaseModel):
    id: int
    system_name: str
    collection_type: str
    capacity_liters: float
    current_volume_liters: float
    active: bool
    location: Optional[str]
    last_emptied: Optional[str]


class WaterPurificationUnitRequest(BaseModel):
    unit_name: str
    purification_type: str
    flow_rate_lpm: Optional[float] = None
    efficiency_percent: Optional[float] = 95.0


class WaterPurificationUnitResponse(BaseModel):
    id: int
    unit_name: str
    purification_type: str
    status: str
    flow_rate_lpm: Optional[float]
    efficiency_percent: float
    input_volume_liters: float
    output_volume_liters: float
    last_maintenance: Optional[str]


class IrrigationSystemRequest(BaseModel):
    system_name: str
    irrigation_type: str
    zone_id: Optional[int] = None
    scheduled_frequency_minutes: Optional[int] = None
    water_per_cycle_liters: Optional[float] = None
    soil_moisture_target_percent: Optional[float] = 60.0


class IrrigationSystemResponse(BaseModel):
    id: int
    system_name: str
    irrigation_type: str
    status: str
    scheduled_frequency_minutes: Optional[int]
    last_watering: Optional[str]
    next_scheduled_watering: Optional[str]
    water_per_cycle_liters: Optional[float]
    optimization_enabled: bool


class WaterQualityReadingRequest(BaseModel):
    reading_location: str
    ph_level: Optional[float] = None
    turbidity_ntu: Optional[float] = None
    total_dissolved_solids_ppm: Optional[float] = None
    chlorine_ppm: Optional[float] = None
    dissolved_oxygen_ppm: Optional[float] = None
    temperature_celsius: Optional[float] = None
    bacterial_count_cfu_ml: Optional[float] = None
    contamination_detected: Optional[bool] = False
    contamination_type: Optional[str] = None
    contaminant_level_ppm: Optional[float] = None


class WaterQualityReadingResponse(BaseModel):
    id: int
    reading_location: str
    ph_level: Optional[float]
    turbidity_ntu: Optional[float]
    total_dissolved_solids_ppm: Optional[float]
    chlorine_ppm: Optional[float]
    dissolved_oxygen_ppm: Optional[float]
    temperature_celsius: Optional[float]
    bacterial_count_cfu_ml: Optional[float]
    contamination_detected: bool
    contamination_type: Optional[str]
    overall_quality_status: str
    created_at: str


class WaterRecyclingLoopRequest(BaseModel):
    loop_name: str
    loop_type: str
    source_system: Optional[str] = None
    destination_system: Optional[str] = None


class WaterRecyclingLoopResponse(BaseModel):
    id: int
    loop_name: str
    loop_type: str
    active: bool
    daily_recycled_liters: float
    total_recycled_liters: float
    efficiency_percent: float


# --- ENDPOINTS ---

@router.get("/collection", response_model=List[WaterCollectionSystemResponse])
def list_collection_systems(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    systems = (
        db.query(WaterCollectionSystem)
        .filter(WaterCollectionSystem.tenant_id == current_user["tenant_id"])
        .all()
    )
    return [
        {
            "id": s.id,
            "system_name": s.system_name,
            "collection_type": s.collection_type,
            "capacity_liters": s.capacity_liters,
            "current_volume_liters": s.current_volume_liters,
            "active": s.active,
            "location": s.location,
            "last_emptied": s.last_emptied.isoformat() if s.last_emptied else None,
        }
        for s in systems
    ]


@router.post("/collection", response_model=WaterCollectionSystemResponse)
def create_collection_system(
    payload: WaterCollectionSystemRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    system = WaterCollectionSystem(
        tenant_id=current_user["tenant_id"],
        system_name=payload.system_name,
        collection_type=payload.collection_type,
        capacity_liters=payload.capacity_liters,
        location=payload.location,
    )
    db.add(system)
    db.commit()
    db.refresh(system)
    return {
        "id": system.id,
        "system_name": system.system_name,
        "collection_type": system.collection_type,
        "capacity_liters": system.capacity_liters,
        "current_volume_liters": system.current_volume_liters,
        "active": system.active,
        "location": system.location,
        "last_emptied": None,
    }


@router.get("/purification", response_model=List[WaterPurificationUnitResponse])
def list_purification_units(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    units = (
        db.query(WaterPurificationUnit)
        .filter(WaterPurificationUnit.tenant_id == current_user["tenant_id"])
        .all()
    )
    return [
        {
            "id": u.id,
            "unit_name": u.unit_name,
            "purification_type": u.purification_type,
            "status": u.status,
            "flow_rate_lpm": u.flow_rate_lpm,
            "efficiency_percent": u.efficiency_percent,
            "input_volume_liters": u.input_volume_liters,
            "output_volume_liters": u.output_volume_liters,
            "last_maintenance": u.last_maintenance.isoformat() if u.last_maintenance else None,
        }
        for u in units
    ]


@router.post("/purification", response_model=WaterPurificationUnitResponse)
def create_purification_unit(
    payload: WaterPurificationUnitRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    unit = WaterPurificationUnit(
        tenant_id=current_user["tenant_id"],
        unit_name=payload.unit_name,
        purification_type=payload.purification_type,
        flow_rate_lpm=payload.flow_rate_lpm,
        efficiency_percent=payload.efficiency_percent,
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return {
        "id": unit.id,
        "unit_name": unit.unit_name,
        "purification_type": unit.purification_type,
        "status": unit.status,
        "flow_rate_lpm": unit.flow_rate_lpm,
        "efficiency_percent": unit.efficiency_percent,
        "input_volume_liters": unit.input_volume_liters,
        "output_volume_liters": unit.output_volume_liters,
        "last_maintenance": None,
    }


@router.get("/irrigation", response_model=List[IrrigationSystemResponse])
def list_irrigation_systems(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    systems = (
        db.query(IrrigationSystem)
        .filter(IrrigationSystem.tenant_id == current_user["tenant_id"])
        .all()
    )
    return [
        {
            "id": s.id,
            "system_name": s.system_name,
            "irrigation_type": s.irrigation_type,
            "status": s.status,
            "scheduled_frequency_minutes": s.scheduled_frequency_minutes,
            "last_watering": s.last_watering.isoformat() if s.last_watering else None,
            "next_scheduled_watering": s.next_scheduled_watering.isoformat() if s.next_scheduled_watering else None,
            "water_per_cycle_liters": s.water_per_cycle_liters,
            "optimization_enabled": s.optimization_enabled,
        }
        for s in systems
    ]


@router.post("/irrigation", response_model=IrrigationSystemResponse)
def create_irrigation_system(
    payload: IrrigationSystemRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    system = IrrigationSystem(
        tenant_id=current_user["tenant_id"],
        system_name=payload.system_name,
        irrigation_type=payload.irrigation_type,
        zone_id=payload.zone_id,
        scheduled_frequency_minutes=payload.scheduled_frequency_minutes,
        water_per_cycle_liters=payload.water_per_cycle_liters,
        soil_moisture_target_percent=payload.soil_moisture_target_percent,
    )
    db.add(system)
    db.commit()
    db.refresh(system)
    return {
        "id": system.id,
        "system_name": system.system_name,
        "irrigation_type": system.irrigation_type,
        "status": system.status,
        "scheduled_frequency_minutes": system.scheduled_frequency_minutes,
        "last_watering": None,
        "next_scheduled_watering": None,
        "water_per_cycle_liters": system.water_per_cycle_liters,
        "optimization_enabled": system.optimization_enabled,
    }


@router.post("/quality", response_model=WaterQualityReadingResponse)
def record_water_quality(
    payload: WaterQualityReadingRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Determine overall quality status based on readings
    overall_status = "good"
    if payload.contamination_detected or (payload.contaminant_level_ppm and payload.contaminant_level_ppm > 0.5):
        overall_status = "contaminated"
    elif (payload.ph_level and (payload.ph_level < 6.5 or payload.ph_level > 8.5)) or (
        payload.turbidity_ntu and payload.turbidity_ntu > 5.0
    ):
        overall_status = "poor"
    elif payload.bacterial_count_cfu_ml and payload.bacterial_count_cfu_ml > 100:
        overall_status = "fair"

    reading = WaterQualityReading(
        tenant_id=current_user["tenant_id"],
        reading_location=payload.reading_location,
        ph_level=payload.ph_level,
        turbidity_ntu=payload.turbidity_ntu,
        total_dissolved_solids_ppm=payload.total_dissolved_solids_ppm,
        chlorine_ppm=payload.chlorine_ppm,
        dissolved_oxygen_ppm=payload.dissolved_oxygen_ppm,
        temperature_celsius=payload.temperature_celsius,
        bacterial_count_cfu_ml=payload.bacterial_count_cfu_ml,
        contamination_detected=payload.contamination_detected,
        contamination_type=payload.contamination_type,
        contaminant_level_ppm=payload.contaminant_level_ppm,
        overall_quality_status=overall_status,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return {
        "id": reading.id,
        "reading_location": reading.reading_location,
        "ph_level": reading.ph_level,
        "turbidity_ntu": reading.turbidity_ntu,
        "total_dissolved_solids_ppm": reading.total_dissolved_solids_ppm,
        "chlorine_ppm": reading.chlorine_ppm,
        "dissolved_oxygen_ppm": reading.dissolved_oxygen_ppm,
        "temperature_celsius": reading.temperature_celsius,
        "bacterial_count_cfu_ml": reading.bacterial_count_cfu_ml,
        "contamination_detected": reading.contamination_detected,
        "contamination_type": reading.contamination_type,
        "overall_quality_status": reading.overall_quality_status,
        "created_at": reading.created_at.isoformat(),
    }


@router.get("/quality/{location}", response_model=List[WaterQualityReadingResponse])
def get_quality_readings(
    location: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    readings = (
        db.query(WaterQualityReading)
        .filter(WaterQualityReading.tenant_id == current_user["tenant_id"])
        .filter(WaterQualityReading.reading_location == location)
        .order_by(WaterQualityReading.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": r.id,
            "reading_location": r.reading_location,
            "ph_level": r.ph_level,
            "turbidity_ntu": r.turbidity_ntu,
            "total_dissolved_solids_ppm": r.total_dissolved_solids_ppm,
            "chlorine_ppm": r.chlorine_ppm,
            "dissolved_oxygen_ppm": r.dissolved_oxygen_ppm,
            "temperature_celsius": r.temperature_celsius,
            "bacterial_count_cfu_ml": r.bacterial_count_cfu_ml,
            "contamination_detected": r.contamination_detected,
            "contamination_type": r.contamination_type,
            "overall_quality_status": r.overall_quality_status,
            "created_at": r.created_at.isoformat(),
        }
        for r in readings
    ]


@router.get("/recycling", response_model=List[WaterRecyclingLoopResponse])
def list_recycling_loops(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    loops = (
        db.query(WaterRecyclingLoop)
        .filter(WaterRecyclingLoop.tenant_id == current_user["tenant_id"])
        .all()
    )
    return [
        {
            "id": l.id,
            "loop_name": l.loop_name,
            "loop_type": l.loop_type,
            "active": l.active,
            "daily_recycled_liters": l.daily_recycled_liters,
            "total_recycled_liters": l.total_recycled_liters,
            "efficiency_percent": l.efficiency_percent,
        }
        for l in loops
    ]


@router.post("/recycling", response_model=WaterRecyclingLoopResponse)
def create_recycling_loop(
    payload: WaterRecyclingLoopRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    loop = WaterRecyclingLoop(
        tenant_id=current_user["tenant_id"],
        loop_name=payload.loop_name,
        loop_type=payload.loop_type,
        source_system=payload.source_system,
        destination_system=payload.destination_system,
    )
    db.add(loop)
    db.commit()
    db.refresh(loop)
    return {
        "id": loop.id,
        "loop_name": loop.loop_name,
        "loop_type": loop.loop_type,
        "active": loop.active,
        "daily_recycled_liters": loop.daily_recycled_liters,
        "total_recycled_liters": loop.total_recycled_liters,
        "efficiency_percent": loop.efficiency_percent,
    }
