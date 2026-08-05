"""
Environmental Control Models - Living Quarters HVAC & Air Quality
Implements database schema for temperature, humidity, air quality sensors
"""
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class EnvironmentalZone(Base):
    """Zone temperature and comfort control configuration"""
    __tablename__ = "environmental_zones"
    
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Temperature control
    current_temperature = Column(Float, default=22.0)
    setpoint = Column(Float, default=22.0)
    min_setpoint = Column(Float, default=16.0)
    max_setpoint = Column(Float, default=28.0)
    
    # Occupancy and comfort
    occupancy_count = Column(Integer, default=0)
    occupancy_detection_enabled = Column(Boolean, default=True)
    
    # HVAC mode
    hvac_mode = Column(String(20), default="auto")  # auto, heat, cool, off
    fan_mode = Column(String(20), default="auto")   # auto, on, circulate
    
    # Comfort profile
    sleep_setpoint = Column(Float, default=19.0)
    day_setpoint = Column(Float, default=22.0)
    evening_setpoint = Column(Float, default=21.0)
    
    # Active scene
    active_scene = Column(String(50), default="home")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    zone = relationship("Zone", back_populates="environmental_zone")
    tenant = relationship("Tenant", back_populates="environmental_zones")
    readings = relationship("EnvironmentalReading", back_populates="zone_config")


class EnvironmentalReading(Base):
    """Real-time sensor readings for temperature, humidity, air quality"""
    __tablename__ = "environmental_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    environmental_zone_id = Column(Integer, ForeignKey("environmental_zones.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Temperature and humidity
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    
    # Air quality metrics
    co2_ppm = Column(Float, nullable=True)           # Carbon dioxide (ppm)
    voc_ppb = Column(Float, nullable=True)           # Volatile organic compounds (ppb)
    pm25 = Column(Float, nullable=True)              # Particulate matter <2.5µm (µg/m³)
    
    # System state
    hvac_output = Column(Float, default=0.0)         # -100 to +100 (heating/cooling)
    compressor_speed_hz = Column(Float, default=0.0) # Compressor frequency
    fan_speed_percent = Column(Float, default=0.0)   # Fan PWM percentage
    
    # Quality flags
    sensor_status = Column(String(20), default="ok")  # ok, error, timeout
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    zone_config = relationship("EnvironmentalZone", back_populates="readings")


class AirQualityAlert(Base):
    """Air quality threshold violations and alerts"""
    __tablename__ = "air_quality_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    environmental_zone_id = Column(Integer, ForeignKey("environmental_zones.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # co2_high, voc_high, pm25_high, humidity_low, humidity_high
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    metric_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    
    # Response
    action_taken = Column(String(100), nullable=True)  # increase_ventilation, activate_purifier, etc
    resolved = Column(Boolean, default=False)
    
    # Timestamps
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)


class ComfortFeedback(Base):
    """User comfort ratings for ML model training"""
    __tablename__ = "comfort_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    environmental_zone_id = Column(Integer, ForeignKey("environmental_zones.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # User feedback
    comfort_rating = Column(Integer, nullable=False)  # 1-5 scale
    
    # Environmental context
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    co2_ppm = Column(Float, nullable=True)
    
    # Comments
    notes = Column(String(500), nullable=True)
    
    # Timestamp
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)


class HVACMaintenanceLog(Base):
    """HVAC system maintenance tracking"""
    __tablename__ = "hvac_maintenance_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    environmental_zone_id = Column(Integer, ForeignKey("environmental_zones.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Maintenance details
    maintenance_type = Column(String(50), nullable=False)  # filter_change, coil_clean, refrigerant_recharge
    component = Column(String(100), nullable=False)  # air_filter, hvac_coil, compressor, etc
    
    # Performance metrics
    runtime_hours = Column(Float, default=0.0)
    filter_pressure_drop_pa = Column(Float, nullable=True)
    filter_life_percent = Column(Float, default=0.0)
    compressor_amps = Column(Float, nullable=True)
    
    # Scheduling
    performed_date = Column(DateTime, nullable=True)
    next_scheduled_date = Column(DateTime, nullable=True)
    
    # Timestamps
    logged_at = Column(DateTime, default=datetime.utcnow)
