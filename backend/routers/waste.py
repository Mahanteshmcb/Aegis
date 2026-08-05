"""
Waste management API - sorting, composting, recycling, and hazardous waste containment.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from backend.dependencies import get_db, get_current_user
from backend.models.waste import (
    WasteContainer,
    WasteSortingLog,
    CompostingProcess,
    RecyclingProcess,
    HazardousWasteStorage,
    WasteProcessingLog,
    WasteMetrics,
)

router = APIRouter(prefix="/api/v1/waste", tags=["waste"])


# --- SCHEMAS ---

class WasteContainerRequest(BaseModel):
    container_name: str
    waste_type: str
    capacity_kg: float
    location: Optional[str] = None
    emptying_frequency_days: Optional[int] = 7


class WasteContainerResponse(BaseModel):
    id: int
    container_name: str
    waste_type: str
    capacity_kg: float
    current_load_kg: float
    location: Optional[str]
    active: bool
    last_emptied: Optional[str]


class WasteSortingLogRequest(BaseModel):
    waste_type: str
    weight_kg: float
    source_location: Optional[str] = None
    destination_container: Optional[str] = None
    sorting_method: str
    contamination_detected: Optional[bool] = False
    contamination_type: Optional[str] = None


class WasteSortingLogResponse(BaseModel):
    id: int
    waste_type: str
    weight_kg: float
    source_location: Optional[str]
    destination_container: Optional[str]
    sorting_method: str
    contamination_detected: bool
    contamination_type: Optional[str]
    quality_score: Optional[float]
    processed_at: str


class CompostingProcessRequest(BaseModel):
    process_name: str
    pile_id: str
    organic_input_kg: float
    moisture_percent: Optional[float] = None
    temperature_celsius: Optional[float] = None
    carbon_nitrogen_ratio: Optional[float] = None


class CompostingProcessResponse(BaseModel):
    id: int
    process_name: str
    pile_id: str
    status: str
    organic_input_kg: float
    current_weight_kg: float
    moisture_percent: Optional[float]
    temperature_celsius: Optional[float]
    stage: Optional[str]
    completed_at: Optional[str]
    compost_output_kg: float


class RecyclingProcessRequest(BaseModel):
    process_name: str
    material_type: str
    input_weight_kg: float
    processing_method: Optional[str] = None
    destination_facility: Optional[str] = None


class RecyclingProcessResponse(BaseModel):
    id: int
    process_name: str
    material_type: str
    input_weight_kg: float
    current_weight_kg: float
    status: str
    recovery_rate_percent: float
    output_weight_kg: float
    completed_at: Optional[str]
    environmental_impact_score: Optional[float]


class HazardousWasteStorageRequest(BaseModel):
    container_id: str
    chemical_name: str
    chemical_type: str
    cas_number: Optional[str] = None
    hazard_classification: Optional[str] = None
    quantity_liters: float
    concentration_percent: Optional[float] = None
    physical_state: str
    storage_location: str
    storage_temperature_min: Optional[float] = None
    storage_temperature_max: Optional[float] = None
    ventilation_required: Optional[bool] = False


class HazardousWasteStorageResponse(BaseModel):
    id: int
    container_id: str
    chemical_name: str
    chemical_type: str
    cas_number: Optional[str]
    hazard_classification: Optional[str]
    quantity_liters: float
    storage_location: str
    container_condition: str
    is_sealed: bool
    last_inspected: Optional[str]
    disposal_scheduled: Optional[str]
    disposal_facility: Optional[str]


class WasteProcessingLogRequest(BaseModel):
    operation_type: str
    waste_category: str
    input_weight_kg: float
    output_weight_kg: Optional[float] = None
    energy_consumed_kwh: Optional[float] = None
    emissions_kg_co2: Optional[float] = None
    operator: Optional[str] = None
    notes: Optional[str] = None


class WasteProcessingLogResponse(BaseModel):
    id: int
    operation_type: str
    waste_category: str
    input_weight_kg: float
    output_weight_kg: Optional[float]
    processing_efficiency_percent: Optional[float]
    completed_at: str


class WasteMetricsResponse(BaseModel):
    id: int
    metric_date: str
    total_waste_collected_kg: float
    organic_waste_kg: float
    recyclable_waste_kg: float
    hazardous_waste_kg: float
    compost_produced_kg: float
    recycled_material_kg: float
    recycling_rate_percent: float
    waste_diversion_rate_percent: float


# --- ENDPOINTS ---


def _get_or_create_metrics(db: Session, tenant_id: int) -> WasteMetrics:
    metrics = (
        db.query(WasteMetrics)
        .filter(WasteMetrics.tenant_id == tenant_id)
        .order_by(WasteMetrics.metric_date.desc())
        .first()
    )
    if not metrics:
        metrics = WasteMetrics(tenant_id=tenant_id)
        db.add(metrics)
        db.commit()
        db.refresh(metrics)
    return metrics


def _recalculate_metrics(metrics: WasteMetrics) -> None:
    total = metrics.total_waste_collected_kg
    if total > 0:
        metrics.recycling_rate_percent = (
            (metrics.recycled_material_kg / total) * 100
        ) if metrics.recycled_material_kg else 0.0
        metrics.waste_diversion_rate_percent = (
            (
                metrics.organic_waste_kg
                + metrics.recyclable_waste_kg
                + metrics.hazardous_waste_kg
                + metrics.compost_produced_kg
                + metrics.recycled_material_kg
                + metrics.inert_waste_kg
            )
            / total
        ) * 100
    else:
        metrics.recycling_rate_percent = 0.0
        metrics.waste_diversion_rate_percent = 0.0

@router.get("/containers", response_model=List[WasteContainerResponse])
def list_waste_containers(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    containers = (
        db.query(WasteContainer)
        .filter(WasteContainer.tenant_id == current_user["tenant_id"])
        .all()
    )
    return [
        {
            "id": c.id,
            "container_name": c.container_name,
            "waste_type": c.waste_type,
            "capacity_kg": c.capacity_kg,
            "current_load_kg": c.current_load_kg,
            "location": c.location,
            "active": c.active,
            "last_emptied": c.last_emptied.isoformat() if c.last_emptied else None,
        }
        for c in containers
    ]


@router.post("/containers", response_model=WasteContainerResponse)
def create_waste_container(
    payload: WasteContainerRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    container = WasteContainer(
        tenant_id=current_user["tenant_id"],
        container_name=payload.container_name,
        waste_type=payload.waste_type,
        capacity_kg=payload.capacity_kg,
        location=payload.location,
        emptying_frequency_days=payload.emptying_frequency_days,
    )
    db.add(container)
    db.commit()
    db.refresh(container)
    return {
        "id": container.id,
        "container_name": container.container_name,
        "waste_type": container.waste_type,
        "capacity_kg": container.capacity_kg,
        "current_load_kg": container.current_load_kg,
        "location": container.location,
        "active": container.active,
        "last_emptied": container.last_emptied.isoformat() if container.last_emptied else None,
    }


@router.post("/sorting", response_model=WasteSortingLogResponse)
def log_waste_sorting(
    payload: WasteSortingLogRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Calculate quality score based on contamination
    quality_score = 100.0
    if payload.contamination_detected:
        quality_score -= 30
    
    log = WasteSortingLog(
        tenant_id=current_user["tenant_id"],
        waste_type=payload.waste_type,
        weight_kg=payload.weight_kg,
        source_location=payload.source_location,
        destination_container=payload.destination_container,
        sorting_method=payload.sorting_method,
        contamination_detected=payload.contamination_detected,
        contamination_type=payload.contamination_type,
        quality_score=quality_score,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    metrics = _get_or_create_metrics(db, current_user["tenant_id"])
    metrics.total_waste_collected_kg += log.weight_kg
    if log.waste_type == "organic":
        metrics.organic_waste_kg += log.weight_kg
    elif log.waste_type == "recyclable":
        metrics.recyclable_waste_kg += log.weight_kg
    elif log.waste_type == "hazardous":
        metrics.hazardous_waste_kg += log.weight_kg
    elif log.waste_type == "inert":
        metrics.inert_waste_kg += log.weight_kg
    _recalculate_metrics(metrics)
    db.commit()

    return {
        "id": log.id,
        "waste_type": log.waste_type,
        "weight_kg": log.weight_kg,
        "source_location": log.source_location,
        "destination_container": log.destination_container,
        "sorting_method": log.sorting_method,
        "contamination_detected": log.contamination_detected,
        "contamination_type": log.contamination_type,
        "quality_score": log.quality_score,
        "processed_at": log.processed_at.isoformat(),
    }


@router.get("/sorting", response_model=List[WasteSortingLogResponse])
def get_sorting_logs(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    logs = (
        db.query(WasteSortingLog)
        .filter(WasteSortingLog.tenant_id == current_user["tenant_id"])
        .order_by(WasteSortingLog.processed_at.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": l.id,
            "waste_type": l.waste_type,
            "weight_kg": l.weight_kg,
            "source_location": l.source_location,
            "destination_container": l.destination_container,
            "sorting_method": l.sorting_method,
            "contamination_detected": l.contamination_detected,
            "contamination_type": l.contamination_type,
            "quality_score": l.quality_score,
            "processed_at": l.processed_at.isoformat(),
        }
        for l in logs
    ]


@router.post("/composting", response_model=CompostingProcessResponse)
def create_composting_process(
    payload: CompostingProcessRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    process = CompostingProcess(
        tenant_id=current_user["tenant_id"],
        process_name=payload.process_name,
        pile_id=payload.pile_id,
        organic_input_kg=payload.organic_input_kg,
        current_weight_kg=payload.organic_input_kg,
        moisture_percent=payload.moisture_percent,
        temperature_celsius=payload.temperature_celsius,
        carbon_nitrogen_ratio=payload.carbon_nitrogen_ratio,
        started_at=datetime.utcnow(),
    )
    db.add(process)
    db.commit()
    db.refresh(process)

    metrics = _get_or_create_metrics(db, current_user["tenant_id"])
    metrics.total_waste_collected_kg += process.organic_input_kg
    metrics.organic_waste_kg += process.organic_input_kg
    _recalculate_metrics(metrics)
    db.commit()

    return {
        "id": process.id,
        "process_name": process.process_name,
        "pile_id": process.pile_id,
        "status": process.status,
        "organic_input_kg": process.organic_input_kg,
        "current_weight_kg": process.current_weight_kg,
        "moisture_percent": process.moisture_percent,
        "temperature_celsius": process.temperature_celsius,
        "stage": process.stage,
        "completed_at": None,
        "compost_output_kg": process.compost_output_kg,
    }


@router.get("/composting", response_model=List[CompostingProcessResponse])
def list_composting_processes(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    processes = (
        db.query(CompostingProcess)
        .filter(CompostingProcess.tenant_id == current_user["tenant_id"])
        .all()
    )
    return [
        {
            "id": p.id,
            "process_name": p.process_name,
            "pile_id": p.pile_id,
            "status": p.status,
            "organic_input_kg": p.organic_input_kg,
            "current_weight_kg": p.current_weight_kg,
            "moisture_percent": p.moisture_percent,
            "temperature_celsius": p.temperature_celsius,
            "stage": p.stage,
            "completed_at": p.completed_at.isoformat() if p.completed_at else None,
            "compost_output_kg": p.compost_output_kg,
        }
        for p in processes
    ]


@router.post("/recycling", response_model=RecyclingProcessResponse)
def create_recycling_process(
    payload: RecyclingProcessRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    process = RecyclingProcess(
        tenant_id=current_user["tenant_id"],
        process_name=payload.process_name,
        material_type=payload.material_type,
        input_weight_kg=payload.input_weight_kg,
        current_weight_kg=payload.input_weight_kg,
        processing_method=payload.processing_method,
        destination_facility=payload.destination_facility,
        started_at=datetime.utcnow(),
    )
    db.add(process)
    db.commit()
    db.refresh(process)

    metrics = _get_or_create_metrics(db, current_user["tenant_id"])
    metrics.total_waste_collected_kg += process.input_weight_kg
    metrics.recyclable_waste_kg += process.input_weight_kg
    _recalculate_metrics(metrics)
    db.commit()

    return {
        "id": process.id,
        "process_name": process.process_name,
        "material_type": process.material_type,
        "input_weight_kg": process.input_weight_kg,
        "current_weight_kg": process.current_weight_kg,
        "status": process.status,
        "recovery_rate_percent": process.recovery_rate_percent,
        "output_weight_kg": process.output_weight_kg,
        "completed_at": None,
        "environmental_impact_score": process.environmental_impact_score,
    }


@router.get("/recycling", response_model=List[RecyclingProcessResponse])
def list_recycling_processes(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    processes = (
        db.query(RecyclingProcess)
        .filter(RecyclingProcess.tenant_id == current_user["tenant_id"])
        .all()
    )
    return [
        {
            "id": p.id,
            "process_name": p.process_name,
            "material_type": p.material_type,
            "input_weight_kg": p.input_weight_kg,
            "current_weight_kg": p.current_weight_kg,
            "status": p.status,
            "recovery_rate_percent": p.recovery_rate_percent,
            "output_weight_kg": p.output_weight_kg,
            "completed_at": p.completed_at.isoformat() if p.completed_at else None,
            "environmental_impact_score": p.environmental_impact_score,
        }
        for p in processes
    ]


@router.post("/hazardous", response_model=HazardousWasteStorageResponse)
def create_hazardous_waste_storage(
    payload: HazardousWasteStorageRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    storage = HazardousWasteStorage(
        tenant_id=current_user["tenant_id"],
        container_id=payload.container_id,
        chemical_name=payload.chemical_name,
        chemical_type=payload.chemical_type,
        cas_number=payload.cas_number,
        quantity_liters=payload.quantity_liters,
        concentration_percent=payload.concentration_percent,
        hazard_classification=payload.hazard_classification,
        physical_state=payload.physical_state,
        storage_location=payload.storage_location,
        storage_temperature_min=payload.storage_temperature_min,
        storage_temperature_max=payload.storage_temperature_max,
        ventilation_required=payload.ventilation_required,
        last_inspected=datetime.utcnow(),
    )
    db.add(storage)
    db.commit()
    db.refresh(storage)

    metrics = _get_or_create_metrics(db, current_user["tenant_id"])
    metrics.total_waste_collected_kg += storage.quantity_liters
    metrics.hazardous_waste_kg += storage.quantity_liters
    _recalculate_metrics(metrics)
    db.commit()

    return {
        "id": storage.id,
        "container_id": storage.container_id,
        "chemical_name": storage.chemical_name,
        "chemical_type": storage.chemical_type,
        "cas_number": storage.cas_number,
        "hazard_classification": storage.hazard_classification,
        "quantity_liters": storage.quantity_liters,
        "storage_location": storage.storage_location,
        "container_condition": storage.container_condition,
        "is_sealed": storage.is_sealed,
        "last_inspected": storage.last_inspected.isoformat(),
        "disposal_scheduled": storage.disposal_scheduled.isoformat() if storage.disposal_scheduled else None,
        "disposal_facility": storage.disposal_facility,
    }


@router.get("/hazardous", response_model=List[HazardousWasteStorageResponse])
def list_hazardous_waste(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    storages = (
        db.query(HazardousWasteStorage)
        .filter(HazardousWasteStorage.tenant_id == current_user["tenant_id"])
        .all()
    )
    return [
        {
            "id": s.id,
            "container_id": s.container_id,
            "chemical_name": s.chemical_name,
            "chemical_type": s.chemical_type,
            "cas_number": s.cas_number,
            "hazard_classification": s.hazard_classification,
            "quantity_liters": s.quantity_liters,
            "storage_location": s.storage_location,
            "container_condition": s.container_condition,
            "is_sealed": s.is_sealed,
            "last_inspected": s.last_inspected.isoformat(),
            "disposal_scheduled": s.disposal_scheduled.isoformat() if s.disposal_scheduled else None,
            "disposal_facility": s.disposal_facility,
        }
        for s in storages
    ]


@router.post("/processing", response_model=WasteProcessingLogResponse)
def log_waste_processing(
    payload: WasteProcessingLogRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Calculate processing efficiency
    efficiency = 0.0
    if payload.output_weight_kg and payload.input_weight_kg > 0:
        efficiency = (payload.output_weight_kg / payload.input_weight_kg) * 100
    
    log = WasteProcessingLog(
        tenant_id=current_user["tenant_id"],
        operation_type=payload.operation_type,
        waste_category=payload.waste_category,
        input_weight_kg=payload.input_weight_kg,
        output_weight_kg=payload.output_weight_kg,
        processing_efficiency_percent=efficiency,
        energy_consumed_kwh=payload.energy_consumed_kwh,
        emissions_kg_co2=payload.emissions_kg_co2,
        processing_time_hours=1.0,
        operator=payload.operator,
        notes=payload.notes,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    metrics = _get_or_create_metrics(db, current_user["tenant_id"])
    if log.emissions_kg_co2:
        metrics.total_emissions_kg_co2 += log.emissions_kg_co2
    _recalculate_metrics(metrics)
    db.commit()

    return {
        "id": log.id,
        "operation_type": log.operation_type,
        "waste_category": log.waste_category,
        "input_weight_kg": log.input_weight_kg,
        "output_weight_kg": log.output_weight_kg,
        "processing_efficiency_percent": log.processing_efficiency_percent,
        "completed_at": log.completed_at.isoformat(),
    }


@router.get("/processing", response_model=List[WasteProcessingLogResponse])
def list_waste_processing_logs(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    logs = (
        db.query(WasteProcessingLog)
        .filter(WasteProcessingLog.tenant_id == current_user["tenant_id"])
        .order_by(WasteProcessingLog.completed_at.desc())
        .all()
    )
    return [
        {
            "id": l.id,
            "operation_type": l.operation_type,
            "waste_category": l.waste_category,
            "input_weight_kg": l.input_weight_kg,
            "output_weight_kg": l.output_weight_kg,
            "processing_efficiency_percent": l.processing_efficiency_percent,
            "completed_at": l.completed_at.isoformat(),
        }
        for l in logs
    ]


@router.get("/metrics", response_model=WasteMetricsResponse)
def get_waste_metrics(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # Get latest metrics or create new ones
    metrics = (
        db.query(WasteMetrics)
        .filter(WasteMetrics.tenant_id == current_user["tenant_id"])
        .order_by(WasteMetrics.metric_date.desc())
        .first()
    )
    
    if not metrics:
        metrics = WasteMetrics(tenant_id=current_user["tenant_id"])
        db.add(metrics)
        db.commit()
        db.refresh(metrics)
    
    return {
        "id": metrics.id,
        "metric_date": metrics.metric_date.isoformat(),
        "total_waste_collected_kg": metrics.total_waste_collected_kg,
        "organic_waste_kg": metrics.organic_waste_kg,
        "recyclable_waste_kg": metrics.recyclable_waste_kg,
        "hazardous_waste_kg": metrics.hazardous_waste_kg,
        "compost_produced_kg": metrics.compost_produced_kg,
        "recycled_material_kg": metrics.recycled_material_kg,
        "recycling_rate_percent": metrics.recycling_rate_percent,
        "waste_diversion_rate_percent": metrics.waste_diversion_rate_percent,
    }
