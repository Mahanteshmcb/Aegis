"""Energy management API router

Provides endpoints for energy balance, naive battery schedule,
and adaptive weather-aware scheduling (Day 58).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from backend.models_db import Sensor, SensorData, EnergyPolicy, WeatherForecastCache
from ai.energy_management import compute_energy_balance, naive_charge_schedule, smart_adaptive_schedule

router = APIRouter(prefix="/api/v1/energy", tags=["energy"])


class EnergyStatus(BaseModel):
    balance_kwh: float
    generation_kwh: float
    consumption_kwh: float
    battery_soc: float
    solar_asset_count: int
    wind_asset_count: int
    hydro_asset_count: int
    geothermal_asset_count: int
    biomass_asset_count: int
    battery_asset_count: int
    grid_asset_count: int
    source_counts: Dict[str, int]
    source_breakdown: Dict[str, float]
    schedule: List[dict]


# Simple in-memory policy store: tenant_id -> policy dict
ENERGY_POLICIES: Dict[Optional[int], Dict[str, Any]] = {}


def _parse_sensor_value(sensor: Sensor, db: Session) -> Optional[float]:
    # Try last_reading first
    try:
        lr = sensor.last_reading
        if isinstance(lr, dict) and 'value' in lr:
            return float(lr['value'])
        if isinstance(lr, (int, float)):
            return float(lr)
    except Exception:
        pass

    # Fallback: look up latest SensorData
    try:
        sd = db.query(SensorData).filter(SensorData.sensor_id == sensor.id).order_by(SensorData.timestamp.desc()).first()
        if sd and sd.value is not None:
            return float(sd.value)
    except Exception:
        pass

    return None


def _classify_sensor_source(sensor: Sensor) -> str:
    t = (sensor.type or '').lower()
    if any(k in t for k in ('solar', 'pv', 'panel', 'inverter')):
        return 'solar'
    if any(k in t for k in ('wind', 'turbine')):
        return 'wind'
    if any(k in t for k in ('hydro', 'water', 'dam', 'river')):
        return 'hydro'
    if any(k in t for k in ('cable', 'grid', 'utility', 'electricity', 'mains')):
        return 'grid'
    if 'geothermal' in t:
        return 'geothermal'
    if any(k in t for k in ('biomass', 'bio')):
        return 'biomass'
    if 'battery' in t or 'soc' in t:
        return 'battery'
    if any(k in t for k in ('meter', 'consum', 'load', 'usage', 'demand', 'draw')):
        return 'consumption'
    return 'other'


@router.get("/status", response_model=EnergyStatus)
async def get_energy_status(db: Session = Depends(get_db), tenant_id: Optional[int] = None, zone_id: Optional[int] = None):
    """Compute energy balance from recent telemetry and return naive schedule.

    If no telemetry is available, falls back to demo series.
    """
    # Heuristic classification of sensors
    q = db.query(Sensor)
    if tenant_id:
        q = q.filter(Sensor.tenant_id == tenant_id)

    sensors = q.all()

    gen_vals = []
    cons_vals = []
    battery_socs = []
    source_totals = {
        'solar': 0.0,
        'wind': 0.0,
        'hydro': 0.0,
        'geothermal': 0.0,
        'biomass': 0.0,
        'grid': 0.0,
        'other': 0.0,
    }
    source_counts = {key: 0 for key in source_totals}

    solar_asset_count = 0
    wind_asset_count = 0
    hydro_asset_count = 0
    geothermal_asset_count = 0
    biomass_asset_count = 0
    battery_asset_count = 0
    grid_asset_count = 0

    for s in sensors:
        category = _classify_sensor_source(s)
        val = _parse_sensor_value(s, db)
        if category in source_counts:
            source_counts[category] += 1
        if category == 'solar':
            solar_asset_count += 1
        elif category == 'wind':
            wind_asset_count += 1
        elif category == 'hydro':
            hydro_asset_count += 1
        elif category == 'geothermal':
            geothermal_asset_count += 1
        elif category == 'biomass':
            biomass_asset_count += 1
        elif category == 'grid':
            grid_asset_count += 1
        elif category == 'battery':
            battery_asset_count += 1

        if val is None:
            continue

        if category == 'consumption':
            cons_vals.append(val)
        elif category == 'battery':
            battery_socs.append(val)
        elif category in source_totals:
            source_totals[category] += val
            gen_vals.append(val)
        else:
            source_totals['other'] += val
            gen_vals.append(val)

    if gen_vals and cons_vals:
        # use averages to build short series
        mean_gen = sum(gen_vals) / len(gen_vals)
        mean_cons = sum(cons_vals) / len(cons_vals)
        generation = [mean_gen] * 4
        consumption = [mean_cons] * 4
        soc = float(sum(battery_socs) / len(battery_socs)) if battery_socs else 0.4
    else:
        # fallback demo values
        consumption = [1.0, 1.5, 2.0, 1.0]
        generation = [0.5, 2.0, 2.5, 0.5]
        soc = 0.4

    breakdown = {k: round(v, 2) for k, v in source_totals.items()}

    cache_q = db.query(WeatherForecastCache)
    if tenant_id is not None:
        cache_q = cache_q.filter(WeatherForecastCache.tenant_id == tenant_id)
    if zone_id is not None:
        cache_q = cache_q.filter(WeatherForecastCache.zone_id == zone_id)

    latest = cache_q.order_by(WeatherForecastCache.computed_at.desc()).first()
    wf = latest.forecast if latest else None

    balance = compute_energy_balance(consumption, generation)
    schedule = naive_charge_schedule(consumption, generation, battery_capacity=10.0, soc=soc, weather_forecast=wf)
    return EnergyStatus(
        balance_kwh=balance,
        generation_kwh=sum(generation),
        consumption_kwh=sum(consumption),
        battery_soc=soc,
        solar_asset_count=solar_asset_count,
        wind_asset_count=wind_asset_count,
        hydro_asset_count=hydro_asset_count,
        geothermal_asset_count=geothermal_asset_count,
        biomass_asset_count=biomass_asset_count,
        battery_asset_count=battery_asset_count,
        grid_asset_count=grid_asset_count,
        source_counts=source_counts,
        source_breakdown=breakdown,
        schedule=schedule,
    )


class PolicyIn(BaseModel):
    charge_threshold: float = 0.6
    discharge_threshold: float = 0.3
    max_charge_rate_kw: float = 2.0


@router.get('/overview')
async def get_energy_overview(db: Session = Depends(get_db), tenant_id: Optional[int] = None, zone_id: Optional[int] = None):
    """Return estate-wide energy optimization summary and smart grid recommendations."""
    q = db.query(Sensor)
    if tenant_id:
        q = q.filter(Sensor.tenant_id == tenant_id)
    sensors = q.all()

    gen_vals = []
    cons_vals = []
    battery_socs = []
    source_totals = {
        'solar': 0.0,
        'wind': 0.0,
        'hydro': 0.0,
        'geothermal': 0.0,
        'biomass': 0.0,
        'grid': 0.0,
        'other': 0.0,
    }
    source_counts = {key: 0 for key in source_totals}

    solar_asset_count = 0
    wind_asset_count = 0
    hydro_asset_count = 0
    geothermal_asset_count = 0
    biomass_asset_count = 0
    battery_asset_count = 0
    grid_asset_count = 0

    for s in sensors:
        category = _classify_sensor_source(s)
        val = _parse_sensor_value(s, db)
        if category in source_counts:
            source_counts[category] += 1
        if category == 'solar':
            solar_asset_count += 1
        elif category == 'wind':
            wind_asset_count += 1
        elif category == 'hydro':
            hydro_asset_count += 1
        elif category == 'geothermal':
            geothermal_asset_count += 1
        elif category == 'biomass':
            biomass_asset_count += 1
        elif category == 'grid':
            grid_asset_count += 1
        elif category == 'battery':
            battery_asset_count += 1

        if val is None:
            continue

        if category == 'consumption':
            cons_vals.append(val)
        elif category == 'battery':
            battery_socs.append(val)
        elif category in source_totals:
            source_totals[category] += val
            gen_vals.append(val)
        else:
            source_totals['other'] += val
            gen_vals.append(val)

    if gen_vals and cons_vals:
        mean_gen = sum(gen_vals) / len(gen_vals)
        mean_cons = sum(cons_vals) / len(cons_vals)
        generation = [mean_gen] * 24
        consumption = [mean_cons] * 24
    else:
        generation = [0.0, 0.5, 1.5, 2.0, 3.0, 2.8, 2.5, 2.0, 1.5, 1.2, 1.0, 0.8, 0.8, 1.0, 1.2, 1.5, 1.8, 2.2, 2.5, 2.0, 1.0, 0.5, 0.2, 0.1]
        consumption = [1.2, 1.1, 1.3, 1.5, 1.8, 2.0, 2.1, 2.0, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.8, 1.6, 1.4, 1.2]

    breakdown = {k: round(v, 2) for k, v in source_totals.items()}

    soc = float(sum(battery_socs) / len(battery_socs)) if battery_socs else 0.45
    cache_q = db.query(WeatherForecastCache)
    if tenant_id is not None:
        cache_q = cache_q.filter(WeatherForecastCache.tenant_id == tenant_id)
    if zone_id is not None:
        cache_q = cache_q.filter(WeatherForecastCache.zone_id == zone_id)

    latest = cache_q.order_by(WeatherForecastCache.computed_at.desc()).first()
    wf = latest.forecast if latest else None
    forecast_available = bool(wf)

    # adapt with weather-aware smart schedule and estate policy
    policy_q = db.query(EnergyPolicy)
    if tenant_id is not None:
        policy_q = policy_q.filter(EnergyPolicy.tenant_id == tenant_id)
    policy = policy_q.order_by(EnergyPolicy.id.desc()).first()
    charge_threshold = policy.charge_threshold if policy else 0.3
    discharge_threshold = policy.discharge_threshold if policy else 0.7
    max_charge_rate = policy.max_charge_rate_kw if policy else 5.0

    result = smart_adaptive_schedule(
        consumption=consumption,
        generation=generation,
        battery_capacity=15.0,
        soc=soc,
        weather_forecast=wf,
        charge_threshold=charge_threshold,
        discharge_threshold=discharge_threshold,
        max_charge_rate_kw=max_charge_rate,
    )

    return {
        "total_generation_kwh": round(sum(generation), 2),
        "total_consumption_kwh": round(sum(consumption), 2),
        "net_balance_kwh": round(compute_energy_balance(consumption, generation), 2),
        "battery_soc": soc,
        "battery_capacity_kwh": 15.0,
        "solar_asset_count": solar_asset_count,
        "wind_asset_count": wind_asset_count,
        "hydro_asset_count": hydro_asset_count,
        "geothermal_asset_count": geothermal_asset_count,
        "biomass_asset_count": biomass_asset_count,
        "battery_asset_count": battery_asset_count,
        "grid_asset_count": grid_asset_count,
        "source_counts": source_counts,
        "source_breakdown": {k: round(v, 2) for k, v in source_totals.items()},
        "forecast_available": forecast_available,
        **result,
    }


@router.get('/policy')
async def get_policy(db: Session = Depends(get_db), tenant_id: Optional[int] = None):
    q = db.query(EnergyPolicy)
    if tenant_id is not None:
        q = q.filter(EnergyPolicy.tenant_id == tenant_id)
    policy = q.order_by(EnergyPolicy.id.desc()).first()
    if not policy:
        return {}
    return {
        'charge_threshold': policy.charge_threshold,
        'discharge_threshold': policy.discharge_threshold,
        'max_charge_rate_kw': policy.max_charge_rate_kw,
    }


@router.post('/policy')
async def set_policy(payload: PolicyIn, db: Session = Depends(get_db), tenant_id: Optional[int] = None):
    policy = EnergyPolicy(
        tenant_id=tenant_id,
        charge_threshold=payload.charge_threshold,
        discharge_threshold=payload.discharge_threshold,
        max_charge_rate_kw=payload.max_charge_rate_kw,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return {"ok": True, "policy": {
        'charge_threshold': policy.charge_threshold,
        'discharge_threshold': policy.discharge_threshold,
        'max_charge_rate_kw': policy.max_charge_rate_kw,
    }}


@router.get('/smart_schedule')
async def get_smart_adaptive_schedule(db: Session = Depends(get_db), tenant_id: Optional[int] = None, zone_id: Optional[int] = None):
    """Get adaptive charge/discharge schedule informed by weather forecast.
    
    Uses smart_adaptive_schedule to incorporate weather signals (precipitation,
    cloud cover, temperature) into charging decisions and load-shifting recommendations.
    """
    # Heuristic classification of sensors (same as status endpoint)
    q = db.query(Sensor)
    if tenant_id:
        q = q.filter(Sensor.tenant_id == tenant_id)

    sensors = q.all()

    gen_vals = []
    cons_vals = []
    battery_socs = []

    for s in sensors:
        t = (s.type or '').lower()
        val = _parse_sensor_value(s, db)
        if val is None:
            continue

        if any(k in t for k in ('solar', 'pv', 'inverter', 'generation')):
            gen_vals.append(val)
        elif any(k in t for k in ('meter', 'consum', 'load', 'usage', 'grid')):
            cons_vals.append(val)
        elif 'battery' in t or 'soc' in t:
            battery_socs.append(val)

    if gen_vals and cons_vals:
        mean_gen = sum(gen_vals) / len(gen_vals)
        mean_cons = sum(cons_vals) / len(cons_vals)
        generation = [mean_gen] * 24  # 24-hour forecast
        consumption = [mean_cons] * 24
        soc = float(sum(battery_socs) / len(battery_socs)) if battery_socs else 0.4
    else:
        consumption = [1.0, 1.5, 2.0, 1.5, 1.0, 0.8, 0.9, 1.2, 1.5, 2.0, 2.2, 2.0, 1.8, 1.6, 1.5, 1.3, 1.2, 1.0, 0.9, 0.8, 0.7, 0.6, 0.7, 0.8]
        generation = [0.0, 0.0, 0.0, 0.2, 0.5, 1.0, 2.0, 2.5, 3.0, 3.2, 3.0, 2.5, 2.0, 1.5, 1.0, 0.5, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        soc = 0.5

    # Get weather forecast cache
    cache_q = db.query(WeatherForecastCache)
    if tenant_id is not None:
        cache_q = cache_q.filter(WeatherForecastCache.tenant_id == tenant_id)
    if zone_id is not None:
        cache_q = cache_q.filter(WeatherForecastCache.zone_id == zone_id)

    latest = cache_q.order_by(WeatherForecastCache.computed_at.desc()).first()
    wf = latest.forecast if latest else None

    # Get policy for tenant
    policy_q = db.query(EnergyPolicy)
    if tenant_id is not None:
        policy_q = policy_q.filter(EnergyPolicy.tenant_id == tenant_id)
    policy = policy_q.order_by(EnergyPolicy.id.desc()).first()

    charge_threshold = policy.charge_threshold if policy else 0.3
    discharge_threshold = policy.discharge_threshold if policy else 0.7
    max_charge_rate = policy.max_charge_rate_kw if policy else 5.0

    result = smart_adaptive_schedule(
        consumption=consumption,
        generation=generation,
        battery_capacity=10.0,
        soc=soc,
        weather_forecast=wf,
        charge_threshold=charge_threshold,
        discharge_threshold=discharge_threshold,
        max_charge_rate_kw=max_charge_rate,
    )

    return {"ok": True, **result}
