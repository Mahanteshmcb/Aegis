"""Deterministic demo data and resource-domain simulation helpers."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.models.storage import InventoryItem, StorageFacility
from backend.models.waste import (
    CompostingProcess,
    RecyclingProcess,
    WasteContainer,
    WasteMetrics,
    WasteProcessingLog,
    WasteSortingLog,
)
from backend.models.water import (
    IrrigationSystem,
    WaterCollectionSystem,
    WaterPurificationUnit,
    WaterRecyclingLoop,
)


DEMO_ASSUMPTION = "generic_uncalibrated_demo_parameters"
MAX_SIMULATION_HOURS = 24 * 30


def seed_demo_resource_data(db: Session, tenant_id: int) -> None:
    """Idempotently seed missing domain data without replacing tenant records."""
    if db.query(WaterCollectionSystem.id).filter(
        WaterCollectionSystem.tenant_id == tenant_id
    ).first() is None:
        db.add_all([
            WaterCollectionSystem(
                tenant_id=tenant_id,
                system_name="Demo Rainwater Cistern",
                collection_type="rainfall",
                capacity_liters=12000,
                current_volume_liters=6400,
                location="Water Vault",
            ),
            WaterCollectionSystem(
                tenant_id=tenant_id,
                system_name="Demo Greywater Buffer",
                collection_type="greywater",
                capacity_liters=4000,
                current_volume_liters=1100,
                location="Water Vault",
            ),
            WaterCollectionSystem(
                tenant_id=tenant_id,
                system_name="Demo Purified Water Tank",
                collection_type="purified",
                capacity_liters=5000,
                current_volume_liters=1500,
                location="Water Vault",
            ),
        ])
        db.add_all([
            WaterPurificationUnit(
                tenant_id=tenant_id,
                unit_name="Demo Multi-stage Filter",
                purification_type="multi_stage",
                status="active",
                flow_rate_lpm=24,
                efficiency_percent=92,
            ),
            IrrigationSystem(
                tenant_id=tenant_id,
                system_name="Demo Greenhouse Drip Line",
                irrigation_type="drip",
                status="watering",
                scheduled_frequency_minutes=60,
                water_per_cycle_liters=24,
                soil_moisture_target_percent=60,
            ),
            WaterRecyclingLoop(
                tenant_id=tenant_id,
                loop_name="Demo Greywater Recovery",
                loop_type="greywater_reuse",
                source_system="Demo Greywater Buffer",
                destination_system="Demo Rainwater Cistern",
                active=True,
                efficiency_percent=82,
            ),
        ])

    if db.query(WasteContainer.id).filter(WasteContainer.tenant_id == tenant_id).first() is None:
        db.add_all([
            WasteContainer(
                tenant_id=tenant_id,
                container_name="Demo Organic Collection",
                waste_type="organic",
                capacity_kg=240,
                current_load_kg=64,
                location="Waste Processing",
                emptying_frequency_days=3,
            ),
            WasteContainer(
                tenant_id=tenant_id,
                container_name="Demo Recyclables",
                waste_type="recyclable",
                capacity_kg=180,
                current_load_kg=38,
                location="Waste Processing",
                emptying_frequency_days=7,
            ),
            WasteContainer(
                tenant_id=tenant_id,
                container_name="Demo Inert Waste",
                waste_type="inert",
                capacity_kg=300,
                current_load_kg=52,
                location="Waste Processing",
                emptying_frequency_days=14,
            ),
        ])
        db.add_all([
            CompostingProcess(
                tenant_id=tenant_id,
                process_name="Demo Aerobic Compost",
                pile_id="SIM-DEMO-COMPOST-01",
                status="active",
                organic_input_kg=120,
                current_weight_kg=112,
                moisture_percent=55,
                temperature_celsius=48,
                carbon_nitrogen_ratio=28,
                stage="thermophilic",
                started_at=datetime.utcnow() - timedelta(days=2),
            ),
            RecyclingProcess(
                tenant_id=tenant_id,
                process_name="Demo Mixed Plastics Batch",
                material_type="plastic",
                input_weight_kg=45,
                current_weight_kg=45,
                status="processing",
                recovery_rate_percent=78,
                processing_method="mechanical",
                started_at=datetime.utcnow() - timedelta(hours=4),
            ),
        ])
        db.add(WasteMetrics(tenant_id=tenant_id))

    if db.query(StorageFacility.id).filter(StorageFacility.tenant_id == tenant_id).first() is None:
        cold_store = StorageFacility(
            tenant_id=tenant_id,
            name="Demo Cold Store",
            location="Warehouse",
            type="cold",
            capacity=500,
        )
        dry_store = StorageFacility(
            tenant_id=tenant_id,
            name="Demo Dry Goods",
            location="Warehouse",
            type="dry",
            capacity=1200,
        )
        db.add_all([cold_store, dry_store])
        db.flush()
        db.add_all([
            InventoryItem(
                tenant_id=tenant_id,
                facility_id=cold_store.id,
                name="Demo Nutrient Solution",
                description="Synthetic inventory for the offline estate simulation.",
                quantity=180,
                unit="L",
                lot_number="SIM-DEMO-WATER-01",
                expires_at=datetime.utcnow() + timedelta(days=120),
            ),
            InventoryItem(
                tenant_id=tenant_id,
                facility_id=dry_store.id,
                name="Demo Filter Media",
                description="Synthetic inventory for the offline estate simulation.",
                quantity=340,
                unit="kg",
                lot_number="SIM-DEMO-FILTER-01",
                expires_at=datetime.utcnow() + timedelta(days=240),
            ),
            InventoryItem(
                tenant_id=tenant_id,
                facility_id=dry_store.id,
                name="Demo Seed Reserve",
                description="Synthetic inventory for the offline estate simulation.",
                quantity=620,
                unit="kg",
                lot_number="SIM-DEMO-SEED-01",
                expires_at=datetime.utcnow() + timedelta(days=60),
            ),
        ])

    db.commit()


def _validated_hours(step_hours: float) -> float:
    hours = float(step_hours)
    if not 0 < hours <= MAX_SIMULATION_HOURS:
        raise ValueError(f"step_hours must be greater than 0 and at most {MAX_SIMULATION_HOURS}")
    return hours


def advance_water_simulation(db: Session, tenant_id: int, step_hours: float) -> dict:
    """Advance resource balances; never synthesizes water-quality measurements."""
    hours = _validated_hours(step_hours)
    minutes = hours * 60
    tanks = db.query(WaterCollectionSystem).filter(
        WaterCollectionSystem.tenant_id == tenant_id,
        WaterCollectionSystem.active.is_(True),
    ).order_by(WaterCollectionSystem.id).all()
    if not tanks:
        return {"mode": "simulation", "assumptions": DEMO_ASSUMPTION, "message": "No active collection systems to simulate.", "systems_advanced": 0}

    primary_tank = next((tank for tank in tanks if tank.collection_type == "rainfall"), tanks[0])
    purified_tank = next((tank for tank in tanks if tank.collection_type == "purified"), None)
    start_volume = float(primary_tank.current_volume_liters or 0)
    rainfall_liters = 0.0
    if primary_tank.collection_type == "rainfall":
        rainfall_liters = 18.0 * hours
        primary_tank.current_volume_liters = min(
            primary_tank.capacity_liters,
            start_volume + rainfall_liters,
        )

    recycled_liters = 0.0
    loops = db.query(WaterRecyclingLoop).filter(
        WaterRecyclingLoop.tenant_id == tenant_id,
        WaterRecyclingLoop.active.is_(True),
    ).all()
    for loop in loops:
        nominal_flow_lpm = 6.0 if "greywater" in loop.loop_type else 3.0
        source = next((tank for tank in tanks if tank.system_name == loop.source_system), primary_tank)
        destination = next(
            (tank for tank in tanks if tank.system_name == loop.destination_system),
            primary_tank,
        )
        requested = nominal_flow_lpm * minutes
        input_liters = min(requested, max(0.0, float(source.current_volume_liters or 0)))
        produced = input_liters * float(loop.efficiency_percent or 0) / 100
        produced = min(produced, max(0.0, float(destination.capacity_liters or 0) - float(destination.current_volume_liters or 0)))
        source.current_volume_liters = max(0.0, float(source.current_volume_liters or 0) - input_liters)
        loop.daily_recycled_liters = produced * 24 / hours
        loop.total_recycled_liters = float(loop.total_recycled_liters or 0) + produced
        loop.last_cycle = datetime.utcnow()
        destination.current_volume_liters = float(destination.current_volume_liters or 0) + produced
        recycled_liters += produced

    irrigation_used = 0.0
    irrigation_systems = db.query(IrrigationSystem).filter(
        IrrigationSystem.tenant_id == tenant_id,
        IrrigationSystem.status == "watering",
    ).all()
    for irrigation in irrigation_systems:
        interval_minutes = max(1, int(irrigation.scheduled_frequency_minutes or 60))
        cycles = minutes / interval_minutes
        requested_liters = max(0.0, float(irrigation.water_per_cycle_liters or 0) * cycles)
        used_liters = min(requested_liters, max(0.0, primary_tank.current_volume_liters))
        primary_tank.current_volume_liters -= used_liters
        irrigation_used += used_liters
        irrigation.last_watering = datetime.utcnow()

    processed_liters = 0.0
    units = db.query(WaterPurificationUnit).filter(
        WaterPurificationUnit.tenant_id == tenant_id,
        WaterPurificationUnit.status == "active",
    ).all()
    for unit in units:
        requested_liters = max(0.0, float(unit.flow_rate_lpm or 0) * minutes)
        input_liters = min(requested_liters, max(0.0, primary_tank.current_volume_liters))
        primary_tank.current_volume_liters -= input_liters
        unit.input_volume_liters = float(unit.input_volume_liters or 0) + input_liters
        output_liters = input_liters * float(unit.efficiency_percent or 0) / 100
        unit.output_volume_liters = float(unit.output_volume_liters or 0) + output_liters
        if purified_tank is not None:
            purified_tank.current_volume_liters = min(
                purified_tank.capacity_liters,
                float(purified_tank.current_volume_liters or 0) + output_liters,
            )
        processed_liters += input_liters

    db.commit()
    return {
        "mode": "simulation",
        "assumptions": DEMO_ASSUMPTION,
        "step_hours": hours,
        "systems_advanced": len(tanks) + len(loops) + len(irrigation_systems) + len(units),
        "rainfall_added_liters": round(rainfall_liters, 2),
        "recycled_liters": round(recycled_liters, 2),
        "irrigation_used_liters": round(irrigation_used, 2),
        "purification_input_liters": round(processed_liters, 2),
        "primary_tank_volume_liters": round(float(primary_tank.current_volume_liters or 0), 2),
        "purified_tank_volume_liters": round(float(purified_tank.current_volume_liters or 0), 2) if purified_tank else None,
        "quality_readings_note": "No synthetic water-quality readings are created; only measured readings appear in quality history.",
    }


def advance_waste_simulation(db: Session, tenant_id: int, step_hours: float) -> dict:
    """Advance demo waste streams and processing with bounded deterministic rates."""
    hours = _validated_hours(step_hours)
    days = hours / 24
    containers = db.query(WasteContainer).filter(
        WasteContainer.tenant_id == tenant_id,
        WasteContainer.active.is_(True),
        WasteContainer.container_name.like("Demo %"),
    ).all()
    rates_kg_per_day = {"organic": 8.0, "recyclable": 3.5, "inert": 2.0, "hazardous": 0.0}
    generated_kg = 0.0
    sorting_events_created = 0
    simulated_at = datetime.utcnow()
    for container in containers:
        added = rates_kg_per_day.get(container.waste_type, 0.0) * days
        capacity_remaining = max(0.0, container.capacity_kg - float(container.current_load_kg or 0))
        added = min(added, capacity_remaining)
        container.current_load_kg = float(container.current_load_kg or 0) + added
        generated_kg += added
        if added > 0:
            db.add(WasteSortingLog(
                tenant_id=tenant_id,
                waste_type=container.waste_type,
                weight_kg=added,
                source_location=container.location,
                destination_container=container.container_name,
                sorting_method="automated",
                contamination_detected=False,
                quality_score=100,
                processed_at=simulated_at,
                created_at=simulated_at,
            ))
            sorting_events_created += 1

    compost = db.query(CompostingProcess).filter(
        CompostingProcess.tenant_id == tenant_id,
        CompostingProcess.pile_id.like("SIM-DEMO-%"),
        CompostingProcess.status.in_(["active", "curing"]),
    ).all()
    newly_completed_compost_kg = 0.0
    newly_completed_compost_input_kg = 0.0
    for process in compost:
        current_temp = float(process.temperature_celsius or 35)
        process.temperature_celsius = current_temp + (52.0 - current_temp) * min(1.0, hours / 48)
        process.moisture_percent = min(65.0, max(40.0, float(process.moisture_percent or 52)))
        starting_mass = float(process.current_weight_kg or 0)
        mass_loss = starting_mass * min(0.04, 0.01 * days)
        process.current_weight_kg = max(0.0, starting_mass - mass_loss)
        process.stage = "thermophilic" if process.temperature_celsius >= 45 else "mesophilic"
        db.add(WasteProcessingLog(
            tenant_id=tenant_id,
            operation_type="composting",
            waste_category="organic",
            input_weight_kg=starting_mass,
            output_weight_kg=process.current_weight_kg,
            processing_efficiency_percent=(
                process.current_weight_kg * 100 / starting_mass if starting_mass else 0
            ),
            notes=f"Simulation-only compost step; {DEMO_ASSUMPTION}.",
            completed_at=simulated_at,
            created_at=simulated_at,
        ))
        if process.current_weight_kg <= float(process.organic_input_kg or 0) * 0.65:
            process.status = "completed"
            process.compost_output_kg = float(process.organic_input_kg or 0) * 0.45
            process.completed_at = datetime.utcnow()
            newly_completed_compost_kg += process.compost_output_kg
            newly_completed_compost_input_kg += float(process.organic_input_kg or 0)

    recycling = db.query(RecyclingProcess).filter(
        RecyclingProcess.tenant_id == tenant_id,
        RecyclingProcess.process_name.like("Demo %"),
        RecyclingProcess.status.in_(["pending", "sorting", "processing"]),
    ).all()
    recycled_output_kg = 0.0
    recycled_input_kg = 0.0
    for process in recycling:
        process.status = "completed"
        process.recovery_rate_percent = min(95.0, max(0.0, float(process.recovery_rate_percent or 0) or 78.0))
        process.output_weight_kg = float(process.input_weight_kg or 0) * process.recovery_rate_percent / 100
        process.current_weight_kg = 0.0
        process.completed_at = simulated_at
        recycled_output_kg += process.output_weight_kg
        recycled_input_kg += float(process.input_weight_kg or 0)
        db.add(WasteProcessingLog(
            tenant_id=tenant_id,
            operation_type="recycling",
            waste_category=process.material_type,
            input_weight_kg=float(process.input_weight_kg or 0),
            output_weight_kg=process.output_weight_kg,
            processing_efficiency_percent=process.recovery_rate_percent,
            notes=f"Simulation-only recycling batch; {DEMO_ASSUMPTION}.",
            completed_at=simulated_at,
            created_at=simulated_at,
        ))

    metrics = db.query(WasteMetrics).filter(
        WasteMetrics.tenant_id == tenant_id
    ).order_by(WasteMetrics.metric_date.desc()).first()
    if metrics is None:
        metrics = WasteMetrics(tenant_id=tenant_id)
        db.add(metrics)
    metrics.total_waste_collected_kg = float(metrics.total_waste_collected_kg or 0) + generated_kg + recycled_input_kg + newly_completed_compost_input_kg
    metrics.organic_waste_kg = float(metrics.organic_waste_kg or 0) + generated_kg * 8 / 13.5 + newly_completed_compost_input_kg
    metrics.recyclable_waste_kg = float(metrics.recyclable_waste_kg or 0) + generated_kg * 3.5 / 13.5 + recycled_input_kg
    metrics.inert_waste_kg = float(metrics.inert_waste_kg or 0) + generated_kg * 2 / 13.5
    metrics.recycled_material_kg = float(metrics.recycled_material_kg or 0) + recycled_output_kg
    metrics.compost_produced_kg = float(metrics.compost_produced_kg or 0) + newly_completed_compost_kg
    total = metrics.total_waste_collected_kg
    metrics.recycling_rate_percent = min(100.0, metrics.recycled_material_kg * 100 / total) if total else 0.0
    diverted = metrics.recycled_material_kg + metrics.compost_produced_kg
    metrics.waste_diversion_rate_percent = min(100.0, diverted * 100 / total) if total else 0.0
    db.commit()
    return {
        "mode": "simulation",
        "assumptions": DEMO_ASSUMPTION,
        "step_hours": hours,
        "generated_waste_kg": round(generated_kg, 2),
        "recycled_output_kg": round(recycled_output_kg, 2),
        "sorting_events_created": sorting_events_created,
        "containers_advanced": len(containers),
        "compost_processes_advanced": len(compost),
        "recycling_batches_advanced": len(recycling),
    }


def advance_storage_simulation(db: Session, tenant_id: int, step_hours: float) -> dict:
    """Apply demo-only stock consumption rates to explicitly seeded inventory lots."""
    hours = _validated_hours(step_hours)
    days = hours / 24
    demo_lots = {
        "SIM-DEMO-WATER-01": 2.0,
        "SIM-DEMO-FILTER-01": 0.5,
        "SIM-DEMO-SEED-01": 1.25,
    }
    items = db.query(InventoryItem).filter(
        InventoryItem.tenant_id == tenant_id,
        InventoryItem.lot_number.in_(demo_lots),
    ).all()
    consumed_by_unit: dict[str, float] = {}
    for item in items:
        consumed = min(
            max(0.0, float(item.quantity or 0)),
            demo_lots[item.lot_number] * days,
        )
        item.quantity = float(item.quantity or 0) - consumed
        unit = item.unit or "units"
        consumed_by_unit[unit] = consumed_by_unit.get(unit, 0.0) + consumed
    db.commit()
    return {
        "mode": "simulation",
        "assumptions": DEMO_ASSUMPTION,
        "step_hours": hours,
        "inventory_items_advanced": len(items),
        "consumed_by_unit": {unit: round(amount, 2) for unit, amount in consumed_by_unit.items()},
        "scope_note": "Only SIM-DEMO inventory lots change; tenant-entered inventory is not modified.",
    }
