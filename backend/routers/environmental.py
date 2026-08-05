"""
Environmental Control API Routes
REST endpoints for HVAC control, air quality monitoring, comfort management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import logging
import random

from backend.dependencies import get_db, get_current_user
from backend.models.environmental import (
    EnvironmentalZone, EnvironmentalReading, AirQualityAlert, ComfortFeedback
)
from backend.models_db import Zone, Tenant
from backend.services.environmental_control import HVACEngine, AirQualityController, CircadianOptimizer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/environmental", tags=["environmental"])

# Initialize control engines
hvac_engine = HVACEngine()
air_quality_controller = AirQualityController()
circadian_optimizer = CircadianOptimizer()


# ============================================================================
# ENVIRONMENTAL ZONE MANAGEMENT
# ============================================================================

@router.get("/zones/{zone_id}/config")
async def get_environmental_config(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get environmental control configuration for zone"""
    env_zone = db.query(EnvironmentalZone).join(
        Zone
    ).filter(
        EnvironmentalZone.zone_id == zone_id,
        EnvironmentalZone.tenant_id == current_user['tenant_id'],
        Zone.tenant_id == current_user['tenant_id']
    ).first()
    
    if not env_zone:
        raise HTTPException(status_code=404, detail="Environmental zone not found")
    
    return {
        'zone_id': zone_id,
        'current_temperature': env_zone.current_temperature,
        'setpoint': env_zone.setpoint,
        'hvac_mode': env_zone.hvac_mode,
        'fan_mode': env_zone.fan_mode,
        'active_scene': env_zone.active_scene,
        'occupancy_count': env_zone.occupancy_count,
        'occupancy_detection_enabled': env_zone.occupancy_detection_enabled,
        'comfort_profiles': {
            'sleep': env_zone.sleep_setpoint,
            'day': env_zone.day_setpoint,
            'evening': env_zone.evening_setpoint
        }
    }


@router.get("/zones/{zone_id}/current")
async def get_current_environmental(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get current temperature, humidity, air quality for zone"""
    env_zone = db.query(EnvironmentalZone).filter(
        EnvironmentalZone.zone_id == zone_id,
        EnvironmentalZone.tenant_id == current_user['tenant_id']
    ).first()
    
    if not env_zone:
        # Auto-create environmental zone if it doesn't exist
        try:
            env_zone = EnvironmentalZone(
                zone_id=zone_id,
                tenant_id=current_user['tenant_id'],
                current_temperature=22.0,
                setpoint=22.0,
                hvac_mode='auto',
                fan_mode='auto',
                active_scene='home',
                occupancy_count=0
            )
            db.add(env_zone)
            db.commit()
            db.refresh(env_zone)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create environmental zone: {str(e)}")
    
    # Get latest reading
    latest_reading = db.query(EnvironmentalReading).filter(
        EnvironmentalReading.environmental_zone_id == env_zone.id,
        EnvironmentalReading.tenant_id == current_user['tenant_id']
    ).order_by(EnvironmentalReading.timestamp.desc()).first()
    
    # If no reading exists, create a demo reading
    if not latest_reading:
        import random
        demo_reading = EnvironmentalReading(
            environmental_zone_id=env_zone.id,
            zone_id=zone_id,
            tenant_id=current_user['tenant_id'],
            temperature=22.0 + random.uniform(-0.5, 0.5),
            humidity=50.0 + random.uniform(-5, 5),
            co2_ppm=700 + random.randint(-100, 200),
            voc_ppb=50 + random.randint(0, 50),
            pm25=15 + random.uniform(0, 10),
            hvac_output=0.0,
            compressor_speed_hz=0.0,
            fan_speed_percent=20.0,
            sensor_status='ok',
            timestamp=datetime.utcnow()
        )
        db.add(demo_reading)
        db.commit()
        db.refresh(demo_reading)
        latest_reading = demo_reading
    
    if not latest_reading:
        raise HTTPException(status_code=404, detail="No sensor readings available")
    
    return {
        'zone_id': zone_id,
        'temperature': latest_reading.temperature,
        'humidity': latest_reading.humidity,
        'co2_ppm': latest_reading.co2_ppm,
        'voc_ppb': latest_reading.voc_ppb,
        'pm25': latest_reading.pm25,
        'setpoint': env_zone.setpoint,
        'hvac_mode': env_zone.hvac_mode,
        'compressor_speed_hz': latest_reading.compressor_speed_hz,
        'fan_speed_percent': latest_reading.fan_speed_percent,
        'sensor_status': latest_reading.sensor_status,
        'timestamp': latest_reading.timestamp.isoformat()
    }


# ============================================================================
# TEMPERATURE CONTROL
# ============================================================================

@router.patch("/zones/{zone_id}/setpoint")
async def update_setpoint(
    zone_id: int,
    request: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update temperature setpoint for zone (16-28°C valid range)"""
    env_zone = db.query(EnvironmentalZone).filter(
        EnvironmentalZone.zone_id == zone_id,
        EnvironmentalZone.tenant_id == current_user['tenant_id']
    ).first()
    
    if not env_zone:
        raise HTTPException(status_code=404, detail="Environmental zone not found")
    
    new_setpoint = request.get('setpoint')
    if not isinstance(new_setpoint, (int, float)) or not (16 <= new_setpoint <= 28):
        raise HTTPException(status_code=400, detail="Setpoint out of valid range (16-28°C)")
    
    old_setpoint = env_zone.setpoint
    env_zone.setpoint = new_setpoint
    env_zone.updated_at = datetime.utcnow()
    
    db.commit()
    logger.info(f"Zone {zone_id} setpoint changed: {old_setpoint}°C → {new_setpoint}°C")
    
    return {
        'status': 'success',
        'zone_id': zone_id,
        'setpoint': new_setpoint,
        'timestamp': datetime.utcnow().isoformat()
    }


@router.patch("/zones/{zone_id}/hvac-mode")
async def update_hvac_mode(
    zone_id: int,
    request: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update HVAC mode (auto, heat, cool, off)"""
    valid_modes = ['auto', 'heat', 'cool', 'off']
    mode = request.get('mode')
    
    if mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Invalid mode. Must be one of: {valid_modes}")
    
    env_zone = db.query(EnvironmentalZone).filter(
        EnvironmentalZone.zone_id == zone_id,
        EnvironmentalZone.tenant_id == current_user['tenant_id']
    ).first()
    
    if not env_zone:
        raise HTTPException(status_code=404, detail="Environmental zone not found")
    
    env_zone.hvac_mode = mode
    env_zone.updated_at = datetime.utcnow()
    db.commit()
    
    return {'status': 'success', 'mode': mode}


# ============================================================================
# COMFORT SCENES
# ============================================================================

COMFORT_SCENES = {
    'home': {'setpoint': 22.0, 'fan_mode': 'auto', 'description': 'Active occupancy'},
    'away': {'setpoint': 26.0, 'fan_mode': 'circulate', 'description': 'Reduced conditioning'},
    'sleep': {'setpoint': 19.0, 'fan_mode': 'auto', 'description': 'Cool for sleep'},
    'party': {'setpoint': 21.0, 'fan_mode': 'on', 'description': 'Continuous circulation'},
}


@router.post("/zones/{zone_id}/scene/{scene_name}")
async def activate_scene(
    zone_id: int,
    scene_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Activate predefined comfort scene"""
    if scene_name not in COMFORT_SCENES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scene. Available: {list(COMFORT_SCENES.keys())}"
        )
    
    env_zone = db.query(EnvironmentalZone).filter(
        EnvironmentalZone.zone_id == zone_id,
        EnvironmentalZone.tenant_id == current_user['tenant_id']
    ).first()
    
    if not env_zone:
        raise HTTPException(status_code=404, detail="Environmental zone not found")
    
    scene = COMFORT_SCENES[scene_name]
    env_zone.active_scene = scene_name
    env_zone.setpoint = scene['setpoint']
    env_zone.fan_mode = scene['fan_mode']
    env_zone.updated_at = datetime.utcnow()
    
    db.commit()
    logger.info(f"Zone {zone_id} activated scene: {scene_name}")
    
    return {
        'status': 'success',
        'scene': scene_name,
        'setpoint': scene['setpoint'],
        'fan_mode': scene['fan_mode'],
        'description': scene['description']
    }


@router.get("/comfort-scenes")
async def list_comfort_scenes():
    """List available comfort scenes"""
    return {
        'scenes': [
            {
                'name': name,
                'setpoint': config['setpoint'],
                'fan_mode': config['fan_mode'],
                'description': config['description']
            }
            for name, config in COMFORT_SCENES.items()
        ]
    }


# ============================================================================
# AIR QUALITY MONITORING
# ============================================================================

@router.get("/zones/{zone_id}/air-quality/current")
async def get_current_air_quality(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get current air quality metrics"""
    env_zone = db.query(EnvironmentalZone).filter(
        EnvironmentalZone.zone_id == zone_id,
        EnvironmentalZone.tenant_id == current_user['tenant_id']
    ).first()
    
    if not env_zone:
        raise HTTPException(status_code=404, detail="Environmental zone not found")
    
    latest_reading = db.query(EnvironmentalReading).filter(
        EnvironmentalReading.environmental_zone_id == env_zone.id
    ).order_by(EnvironmentalReading.timestamp.desc()).first()
    
    if not latest_reading:
        raise HTTPException(status_code=404, detail="No readings available")
    
    # Categorize readings
    co2_status = 'excellent' if latest_reading.co2_ppm < 800 else \
                 'good' if latest_reading.co2_ppm < 1200 else \
                 'fair' if latest_reading.co2_ppm < 1800 else 'poor'
    
    pm25_status = 'good' if latest_reading.pm25 < 12 else \
                  'moderate' if latest_reading.pm25 < 35 else \
                  'sensitive' if latest_reading.pm25 < 55 else \
                  'unhealthy' if latest_reading.pm25 < 150 else 'very_unhealthy'
    
    humidity_status = 'low' if latest_reading.humidity < 30 else \
                      'optimal' if latest_reading.humidity < 60 else \
                      'high' if latest_reading.humidity < 70 else 'very_high'
    
    return {
        'zone_id': zone_id,
        'co2': {
            'ppm': latest_reading.co2_ppm,
            'status': co2_status,
            'healthy_threshold': 800
        },
        'pm25': {
            'value': latest_reading.pm25,
            'unit': 'µg/m³',
            'status': pm25_status,
            'healthy_threshold': 12
        },
        'voc': {
            'ppb': latest_reading.voc_ppb,
            'alert_threshold': 500
        },
        'humidity': {
            'percent': latest_reading.humidity,
            'status': humidity_status,
            'optimal_range': '40-60%'
        },
        'timestamp': latest_reading.timestamp.isoformat()
    }


@router.get("/zones/{zone_id}/air-quality/24h")
async def get_air_quality_history(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get 24-hour air quality trend"""
    env_zone = db.query(EnvironmentalZone).filter(
        EnvironmentalZone.zone_id == zone_id,
        EnvironmentalZone.tenant_id == current_user['tenant_id']
    ).first()
    
    if not env_zone:
        raise HTTPException(status_code=404, detail="Environmental zone not found")
    
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    readings = db.query(EnvironmentalReading).filter(
        EnvironmentalReading.environmental_zone_id == env_zone.id,
        EnvironmentalReading.timestamp >= cutoff_time
    ).order_by(EnvironmentalReading.timestamp).all()
    
    return {
        'zone_id': zone_id,
        'data': [
            {
                'timestamp': r.timestamp.isoformat(),
                'co2_ppm': r.co2_ppm,
                'pm25': r.pm25,
                'voc_ppb': r.voc_ppb,
                'humidity': r.humidity
            }
            for r in readings
        ],
        'record_count': len(readings)
    }


@router.get("/zones/{zone_id}/air-quality/alerts")
async def get_air_quality_alerts(
    zone_id: int,
    limit: int = Query(10, ge=1, le=100),
    unresolved_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get air quality alerts for zone"""
    env_zone = db.query(EnvironmentalZone).filter(
        EnvironmentalZone.zone_id == zone_id,
        EnvironmentalZone.tenant_id == current_user['tenant_id']
    ).first()
    
    if not env_zone:
        raise HTTPException(status_code=404, detail="Environmental zone not found")
    
    query = db.query(AirQualityAlert).filter(
        AirQualityAlert.environmental_zone_id == env_zone.id
    )
    
    if unresolved_only:
        query = query.filter(AirQualityAlert.resolved == False)
    
    alerts = query.order_by(AirQualityAlert.triggered_at.desc()).limit(limit).all()
    
    return {
        'zone_id': zone_id,
        'alerts': [
            {
                'id': a.id,
                'type': a.alert_type,
                'severity': a.severity,
                'metric_value': a.metric_value,
                'threshold': a.threshold,
                'action_taken': a.action_taken,
                'triggered_at': a.triggered_at.isoformat(),
                'resolved': a.resolved
            }
            for a in alerts
        ]
    }


# ============================================================================
# COMFORT FEEDBACK & LEARNING
# ============================================================================

@router.post("/zones/{zone_id}/comfort-feedback")
async def log_comfort_feedback(
    zone_id: int,
    request: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Log user comfort rating for ML model training (1-5 scale)"""
    env_zone = db.query(EnvironmentalZone).filter(
        EnvironmentalZone.zone_id == zone_id,
        EnvironmentalZone.tenant_id == current_user['tenant_id']
    ).first()
    
    if not env_zone:
        raise HTTPException(status_code=404, detail="Environmental zone not found")
    
    rating = request.get('rating')
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    
    # Get current environmental conditions
    latest_reading = db.query(EnvironmentalReading).filter(
        EnvironmentalReading.environmental_zone_id == env_zone.id
    ).order_by(EnvironmentalReading.timestamp.desc()).first()
    
    feedback = ComfortFeedback(
        environmental_zone_id=env_zone.id,
        zone_id=zone_id,
        tenant_id=current_user['tenant_id'],
        user_id=current_user['id'],
        comfort_rating=rating,
        temperature=latest_reading.temperature if latest_reading else None,
        humidity=latest_reading.humidity if latest_reading else None,
        co2_ppm=latest_reading.co2_ppm if latest_reading else None,
        notes=request.get('notes'),
        recorded_at=datetime.utcnow()
    )
    
    db.add(feedback)
    db.commit()
    
    logger.info(f"User {current_user['id']} rated zone {zone_id} comfort: {rating}/5")
    
    return {
        'status': 'success',
        'feedback_id': feedback.id,
        'rating': rating,
        'timestamp': feedback.recorded_at.isoformat()
    }


@router.get("/zones/{zone_id}/comfort-feedback/recent")
async def get_recent_comfort_feedback(
    zone_id: int,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get recent comfort feedback for analysis"""
    env_zone = db.query(EnvironmentalZone).filter(
        EnvironmentalZone.zone_id == zone_id,
        EnvironmentalZone.tenant_id == current_user['tenant_id']
    ).first()
    
    if not env_zone:
        raise HTTPException(status_code=404, detail="Environmental zone not found")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    feedback = db.query(ComfortFeedback).filter(
        ComfortFeedback.environmental_zone_id == env_zone.id,
        ComfortFeedback.recorded_at >= cutoff_date
    ).order_by(ComfortFeedback.recorded_at.desc()).all()
    
    # Calculate statistics
    if feedback:
        avg_rating = sum(f.comfort_rating for f in feedback) / len(feedback)
        avg_temp = sum(f.temperature for f in feedback if f.temperature) / len([f for f in feedback if f.temperature])
    else:
        avg_rating = 0
        avg_temp = 0
    
    return {
        'zone_id': zone_id,
        'period_days': days,
        'total_responses': len(feedback),
        'average_rating': round(avg_rating, 2),
        'average_temperature': round(avg_temp, 1),
        'recent_feedback': [
            {
                'rating': f.comfort_rating,
                'temperature': f.temperature,
                'humidity': f.humidity,
                'co2_ppm': f.co2_ppm,
                'notes': f.notes,
                'recorded_at': f.recorded_at.isoformat()
            }
            for f in feedback[:10]
        ]
    }


# ============================================================================
# SYSTEM STATUS & DIAGNOSTICS
# ============================================================================

@router.get("/zones/{zone_id}/hvac-status")
async def get_hvac_status(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get current HVAC system status"""
    env_zone = db.query(EnvironmentalZone).filter(
        EnvironmentalZone.zone_id == zone_id,
        EnvironmentalZone.tenant_id == current_user['tenant_id']
    ).first()
    
    if not env_zone:
        raise HTTPException(status_code=404, detail="Environmental zone not found")
    
    latest_reading = db.query(EnvironmentalReading).filter(
        EnvironmentalReading.environmental_zone_id == env_zone.id
    ).order_by(EnvironmentalReading.timestamp.desc()).first()
    
    if not latest_reading:
        raise HTTPException(status_code=404, detail="No readings available")
    
    # Determine mode based on compressor speed
    if latest_reading.compressor_speed_hz == 0:
        mode = 'idle'
    elif latest_reading.hvac_output_percent > 0:
        mode = 'heating'
    else:
        mode = 'cooling'
    
    return {
        'zone_id': zone_id,
        'mode': mode,
        'compressor_speed_hz': latest_reading.compressor_speed_hz,
        'fan_speed_percent': latest_reading.fan_speed_percent,
        'hvac_output_percent': latest_reading.hvac_output_percent,
        'temperature_error_c': env_zone.setpoint - latest_reading.temperature,
        'system_runtime_hours': 0,  # Would be tracked in maintenance log
        'timestamp': latest_reading.timestamp.isoformat()
    }
