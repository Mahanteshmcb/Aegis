"""Weather API router (Day 55 scaffold)."""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from backend.models_db import WeatherObservation, WeatherForecastCache
from ai.weather_integration import get_forecast

router = APIRouter(prefix="/api/v1/weather", tags=["weather"])


class ObservationIn(BaseModel):
    tenant_id: Optional[int] = None
    zone_id: Optional[int] = None
    sensor_id: Optional[int] = None
    timestamp: Optional[str] = None
    temp_c: Optional[float] = None
    humidity_percent: Optional[float] = None
    wind_m_s: Optional[float] = None
    precip_mm: Optional[float] = None
    pressure_hpa: Optional[float] = None


def compute_local_forecast(db: Session, zone_id: Optional[int] = None, tenant_id: Optional[int] = None, horizon: int = 24):
    """Compute or return cached local forecast for a zone/tenant using only local observations."""
    # Check cache
    q = db.query(WeatherForecastCache)
    if tenant_id is not None:
        q = q.filter(WeatherForecastCache.tenant_id == tenant_id)
    if zone_id is not None:
        q = q.filter(WeatherForecastCache.zone_id == zone_id)
    cache = q.order_by(WeatherForecastCache.computed_at.desc()).first()
    from datetime import datetime, timedelta
    if cache and (datetime.utcnow() - cache.computed_at).total_seconds() < 900:
        return {"ok": True, "forecast": cache.forecast, "cached": True}

    obs_q = db.query(WeatherObservation)
    if tenant_id is not None:
        obs_q = obs_q.filter(WeatherObservation.tenant_id == tenant_id)
    if zone_id is not None:
        obs_q = obs_q.filter(WeatherObservation.zone_id == zone_id)
    three_hours_ago = datetime.utcnow() - timedelta(hours=3)
    obs_q = obs_q.filter(WeatherObservation.timestamp >= three_hours_ago)
    obs = obs_q.all()

    if not obs:
        fc = get_forecast(0.0, 0.0)
    else:
        avg_temp = sum(o.temp_c for o in obs if o.temp_c is not None) / max(1, sum(1 for o in obs if o.temp_c is not None))
        avg_hum = sum(o.humidity_percent for o in obs if o.humidity_percent is not None) / max(1, sum(1 for o in obs if o.humidity_percent is not None))
        fc = get_forecast(0.0, 0.0)
        for entry in fc:
            entry['temp_c'] = round(avg_temp + (entry.get('temp_c', 0) - entry.get('temp_c', 0)), 2)
            entry['humidity_percent'] = round(avg_hum, 1)

    cache_row = WeatherForecastCache(tenant_id=tenant_id, zone_id=zone_id, horizon_hours=horizon, forecast=fc)
    db.add(cache_row)
    db.commit()
    db.refresh(cache_row)
    return {"ok": True, "forecast": fc, "cached": False}


@router.post('/observe')
async def ingest_observation(payload: ObservationIn, db: Session = Depends(get_db)):
    """Ingest a single local weather observation from an on-site sensor.

    This endpoint is intended for local-only sensor ingestion (no cloud).
    """
    from datetime import datetime

    ts = None
    if payload.timestamp:
        try:
            ts = datetime.fromisoformat(payload.timestamp)
        except Exception:
            ts = datetime.utcnow()
    else:
        ts = datetime.utcnow()

    obs = WeatherObservation(
        tenant_id=payload.tenant_id,
        zone_id=payload.zone_id,
        sensor_id=payload.sensor_id,
        timestamp=ts,
        temp_c=payload.temp_c,
        humidity_percent=payload.humidity_percent,
        wind_m_s=payload.wind_m_s,
        precip_mm=payload.precip_mm,
        pressure_hpa=payload.pressure_hpa,
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return {"ok": True, "id": obs.id}


@router.get('/local_forecast')
async def local_forecast(zone_id: Optional[int] = None, tenant_id: Optional[int] = None, horizon: int = 24, db: Session = Depends(get_db)):
    return compute_local_forecast(db, zone_id=zone_id, tenant_id=tenant_id, horizon=horizon)


@router.get('/observations')
async def observations(zone_id: Optional[int] = None, tenant_id: Optional[int] = None, limit: int = 20, db: Session = Depends(get_db)):
    q = db.query(WeatherObservation)
    if tenant_id is not None:
        q = q.filter(WeatherObservation.tenant_id == tenant_id)
    if zone_id is not None:
        q = q.filter(WeatherObservation.zone_id == zone_id)
    obs_rows = q.order_by(WeatherObservation.timestamp.desc()).limit(limit).all()
    return {
        "ok": True,
        "observations": [
            {
                "id": obs.id,
                "tenant_id": obs.tenant_id,
                "zone_id": obs.zone_id,
                "sensor_id": obs.sensor_id,
                "timestamp": obs.timestamp.isoformat() if obs.timestamp else None,
                "temp_c": obs.temp_c,
                "humidity_percent": obs.humidity_percent,
                "wind_m_s": obs.wind_m_s,
                "precip_mm": obs.precip_mm,
                "pressure_hpa": obs.pressure_hpa,
            }
            for obs in obs_rows
        ],
    }


@router.get('/maintenance/recommendations')
async def maintenance_recommendations(zone_id: Optional[int] = None, tenant_id: Optional[int] = None, db: Session = Depends(get_db)):
    res = compute_local_forecast(db, zone_id=zone_id, tenant_id=tenant_id)
    fc = res.get('forecast', [])
    recs = []
    for entry in fc:
        h = entry.get('dt')
        if entry.get('precip_mm', 0) >= 1.0:
            recs.append({'when': h, 'action': 'skip_irrigation', 'reason': 'precipitation_expected'})
        if entry.get('temp_c', 999) <= 2.0:
            recs.append({'when': h, 'action': 'frost_protection', 'reason': 'low_temperature'})
        if entry.get('wind_m_s', 0) >= 12.0:
            recs.append({'when': h, 'action': 'secure_vents', 'reason': 'high_wind'})

    return {"ok": True, "recommendations": recs}
