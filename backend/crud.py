from sqlalchemy.orm import Session

from . import models_db as models, schemas


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


# --- User CRUD for authentication ---
from sqlalchemy.exc import IntegrityError
from passlib.hash import bcrypt

def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = bcrypt.hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        tenant_id=user.tenant_id,
    )
    db.add(db_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("User with this email already exists")
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> models.User | None:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not bcrypt.verify(password, user.hashed_password):
        return None
    return user
