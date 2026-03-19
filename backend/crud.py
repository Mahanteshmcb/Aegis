from sqlalchemy.orm import Session

from . import models, schemas


def create_tenant(db: Session, tenant: schemas.TenantCreate) -> models.Tenant:
    db_tenant = models.Tenant(name=tenant.name)
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant


def get_tenant(db: Session, tenant_id: int) -> models.Tenant | None:
    return db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()


def list_tenants(db: Session, skip: int = 0, limit: int = 100) -> list[models.Tenant]:
    return db.query(models.Tenant).offset(skip).limit(limit).all()


def create_sensor(db: Session, sensor: schemas.SensorCreate) -> models.Sensor:
    db_sensor = models.Sensor(
        tenant_id=sensor.tenant_id,
        type=sensor.type,
        location=sensor.location,
    )
    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    return db_sensor


def get_sensor(db: Session, sensor_id: int) -> models.Sensor | None:
    return db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()


def update_sensor_reading(db: Session, sensor: models.Sensor, update: schemas.SensorUpdate) -> models.Sensor:
    if update.type is not None:
        sensor.type = update.type
    if update.location is not None:
        sensor.location = update.location
    if update.last_reading is not None:
        sensor.last_reading = update.last_reading
    db.commit()
    db.refresh(sensor)
    return sensor


def create_audit_log(db: Session, audit: schemas.AuditLogCreate) -> models.AuditLog:
    db_log = models.AuditLog(
        sensor_id=audit.sensor_id,
        event_type=audit.event_type,
        data_hash=audit.data_hash,
        blockchain_tx=audit.blockchain_tx,
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def list_audit_logs(db: Session, sensor_id: int, skip: int = 0, limit: int = 100) -> list[models.AuditLog]:
    return (
        db.query(models.AuditLog)
        .filter(models.AuditLog.sensor_id == sensor_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
