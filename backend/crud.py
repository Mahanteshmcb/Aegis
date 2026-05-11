from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from . import models_db as models, schemas


def create_tenant(db: Session, tenant: schemas.TenantCreate) -> models.Tenant:
    db_tenant = models.Tenant(name=tenant.name, settings=tenant.settings or {})
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant


def get_tenant(db: Session, tenant_id: int) -> models.Tenant | None:
    return db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()


def list_tenants(db: Session, skip: int = 0, limit: int = 100) -> list[models.Tenant]:
    return db.query(models.Tenant).offset(skip).limit(limit).all()


def update_tenant(db: Session, tenant_id: int, tenant_update: schemas.TenantUpdate) -> models.Tenant | None:
    db_tenant = db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()
    if not db_tenant:
        return None
    update_data = tenant_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tenant, field, value)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant


def delete_tenant(db: Session, tenant_id: int) -> bool:
    db_tenant = db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()
    if not db_tenant:
        return False
    db.delete(db_tenant)
    db.commit()
    return True


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


def create_audit_log(db: Session, audit: schemas.AuditLogCreate, tenant_id: int | None = None) -> models.AuditLog:
    # Infer tenant_id from the sensor when possible
    if tenant_id is None and audit.sensor_id is not None:
        sensor = db.query(models.Sensor).filter(models.Sensor.id == audit.sensor_id).first()
        tenant_id = sensor.tenant_id if sensor else None

    db_log = models.AuditLog(
        tenant_id=tenant_id,
        sensor_id=audit.sensor_id,
        event_type=audit.event_type,
        data_hash=audit.data_hash,
        blockchain_tx=audit.blockchain_tx,
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def create_audit_log_with_transaction(
    db: Session,
    event_type: str,
    data_hash: str,
    tenant_id: int,
    blockchain_tx: str | None = None,
    sensor_id: int | None = None,
) -> models.AuditLog:
    """Create an audit log record with an optional blockchain transaction hash."""
    audit = schemas.AuditLogCreate(
        event_type=event_type,
        data_hash=data_hash,
        blockchain_tx=blockchain_tx,
    )
    audit.sensor_id = sensor_id
    return create_audit_log(db, audit, tenant_id=tenant_id)


def create_scheduled_task(db: Session, scheduled_task: schemas.ScheduledTaskCreate, tenant_id: int) -> models.ScheduledRoboticTask:
    db_task = models.ScheduledRoboticTask(
        tenant_id=tenant_id,
        task_id=scheduled_task.task_id,
        operation_type=scheduled_task.operation_type,
        requested_robot_id=scheduled_task.requested_robot_id,
        zone_id=scheduled_task.zone_id,
        priority=scheduled_task.priority,
        task_detail=scheduled_task.task_detail or {},
        task_metadata=scheduled_task.metadata or {},
        timeout_seconds=scheduled_task.timeout_seconds,
        status=scheduled_task.status,
        conflict_reason=scheduled_task.conflict_reason,
        enqueue_time=scheduled_task.enqueue_time or datetime.utcnow(),
    )
    db.add(db_task)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("Scheduled task with this task_id already exists")
    db.refresh(db_task)
    return db_task


def get_scheduled_task_by_task_id(db: Session, tenant_id: int, task_id: str) -> models.ScheduledRoboticTask | None:
    return (
        db.query(models.ScheduledRoboticTask)
        .filter(models.ScheduledRoboticTask.tenant_id == tenant_id)
        .filter(models.ScheduledRoboticTask.task_id == task_id)
        .first()
    )


def list_scheduled_tasks(db: Session, tenant_id: int, status: str | None = None) -> list[models.ScheduledRoboticTask]:
    query = db.query(models.ScheduledRoboticTask).filter(models.ScheduledRoboticTask.tenant_id == tenant_id)
    if status is not None:
        query = query.filter(models.ScheduledRoboticTask.status == status)
    return query.order_by(models.ScheduledRoboticTask.priority.desc(), models.ScheduledRoboticTask.enqueue_time.asc()).all()


def update_scheduled_task_status(
    db: Session,
    scheduled_task: models.ScheduledRoboticTask,
    status: str,
    assigned_robot_id: str | None = None,
    conflict_reason: str | None = None,
) -> models.ScheduledRoboticTask:
    scheduled_task.status = status
    if assigned_robot_id is not None:
        scheduled_task.assigned_robot_id = assigned_robot_id
    if conflict_reason is not None:
        scheduled_task.conflict_reason = conflict_reason
    if status == "assigned" and scheduled_task.assigned_time is None:
        scheduled_task.assigned_time = datetime.utcnow()
    db.commit()
    db.refresh(scheduled_task)
    return scheduled_task


def delete_scheduled_task(db: Session, tenant_id: int, task_id: str) -> bool:
    """Delete a scheduled task if it exists and belongs to the tenant."""
    db_task = (
        db.query(models.ScheduledRoboticTask)
        .filter(models.ScheduledRoboticTask.tenant_id == tenant_id)
        .filter(models.ScheduledRoboticTask.task_id == task_id)
        .first()
    )
    if not db_task:
        return False
    db.delete(db_task)
    db.commit()
    return True


def list_audit_logs(db: Session, tenant_id: int, sensor_id: int | None = None, skip: int = 0, limit: int = 100) -> list[models.AuditLog]:
    query = db.query(models.AuditLog).filter(models.AuditLog.tenant_id == tenant_id)
    if sensor_id is not None:
        query = query.filter(models.AuditLog.sensor_id == sensor_id)
    return query.order_by(models.AuditLog.created_at.desc()).offset(skip).limit(limit).all()


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

def list_users_by_tenant(db: Session, tenant_id: int, skip: int = 0, limit: int = 100) -> list[models.User]:
    """List all users in a specific tenant (admin only)."""
    return (
        db.query(models.User)
        .filter(models.User.tenant_id == tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_user_by_id(db: Session, user_id: int) -> models.User | None:
    """Get a user by ID."""
    return db.query(models.User).filter(models.User.id == user_id).first()

def update_user_role(db: Session, user_id: int, new_role: str) -> models.User:
    """Update a user's role (admin only)."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError("User not found")
    user.role = new_role
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user (admin only)."""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


# ============================================================================
# MONITORING CRUD OPERATIONS
# ============================================================================

def create_system_alert(db: Session, alert: schemas.SystemAlertCreate) -> models.SystemAlert:
    """Create a new system alert."""
    db_alert = models.SystemAlert(
        tenant_id=alert.tenant_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        source=alert.source,
        data=alert.data or {},
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


def get_system_alert(db: Session, alert_id: int, tenant_id: int) -> models.SystemAlert | None:
    """Get a specific system alert."""
    return (
        db.query(models.SystemAlert)
        .filter(models.SystemAlert.id == alert_id)
        .filter(models.SystemAlert.tenant_id == tenant_id)
        .first()
    )


def list_system_alerts(
    db: Session,
    tenant_id: int,
    acknowledged: bool | None = None,
    severity: str | None = None,
    alert_type: str | None = None,
    limit: int = 100
) -> list[models.SystemAlert]:
    """List system alerts with optional filtering."""
    query = db.query(models.SystemAlert).filter(models.SystemAlert.tenant_id == tenant_id)

    if acknowledged is not None:
        query = query.filter(models.SystemAlert.acknowledged == acknowledged)
    if severity:
        query = query.filter(models.SystemAlert.severity == severity)
    if alert_type:
        query = query.filter(models.SystemAlert.alert_type == alert_type)

    return query.order_by(models.SystemAlert.created_at.desc()).limit(limit).all()


def acknowledge_system_alert(db: Session, alert_id: int, tenant_id: int, user_id: int) -> models.SystemAlert | None:
    """Acknowledge a system alert."""
    alert = get_system_alert(db, alert_id, tenant_id)
    if not alert:
        return None

    alert.acknowledged = True
    alert.acknowledged_by = user_id
    alert.acknowledged_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return alert


def create_emergency_event(db: Session, event: schemas.EmergencyEventCreate, tenant_id: int, triggered_by_user: int | None = None) -> models.EmergencyEvent:
    """Create a new emergency event."""
    db_event = models.EmergencyEvent(
        tenant_id=tenant_id,
        event_id=event.metadata.get("event_id", f"evt-{int(datetime.utcnow().timestamp() * 1000)}"),
        event_type=event.event_type,
        severity=event.severity,
        description=event.description,
        triggered_by=event.triggered_by or "automated",
        triggered_by_user=triggered_by_user,
        status="active",
        affected_systems=event.affected_systems or [],
        root_cause=event.root_cause,
        event_metadata=event.metadata or {},
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_emergency_event(db: Session, tenant_id: int, event_id: str) -> models.EmergencyEvent | None:
    """Retrieve an emergency event by event_id."""
    return (
        db.query(models.EmergencyEvent)
        .filter(models.EmergencyEvent.tenant_id == tenant_id)
        .filter(models.EmergencyEvent.event_id == event_id)
        .first()
    )


def list_emergency_events(db: Session, tenant_id: int, status: str | None = None, limit: int = 100) -> list[models.EmergencyEvent]:
    """List emergency events."""
    query = db.query(models.EmergencyEvent).filter(models.EmergencyEvent.tenant_id == tenant_id)
    if status:
        query = query.filter(models.EmergencyEvent.status == status)
    return query.order_by(models.EmergencyEvent.response_timestamp.desc()).limit(limit).all()


def create_emergency_response(db: Session, event_id: int, response: schemas.EmergencyResponseCreate) -> models.EmergencyResponse:
    """Create a response action for an emergency event."""
    db_response = models.EmergencyResponse(
        event_id=event_id,
        action_type=response.action_type,
        action_name=response.action_name,
        description=response.description,
        priority=response.priority or 0,
        affected_robots=response.affected_robots or [],
        affected_zones=response.affected_zones or [],
        affected_tasks=response.affected_tasks or [],
        status="pending",
    )
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response


def update_emergency_response_status(db: Session, response_id: int, status: str, success: bool, error_message: str | None = None, result_data: dict | None = None) -> models.EmergencyResponse:
    """Update the status of an emergency response."""
    response = db.query(models.EmergencyResponse).filter(models.EmergencyResponse.id == response_id).first()
    if not response:
        raise ValueError("Emergency response not found")
    response.status = status
    response.success = success
    response.error_message = error_message
    response.result_data = result_data or {}
    response.completed_at = datetime.utcnow()
    response.execution_time_ms = int((datetime.utcnow() - response.initiated_at).total_seconds() * 1000)
    db.commit()
    db.refresh(response)
    return response


def create_backup_power_state(db: Session, tenant_id: int, state: schemas.BackupPowerStateCreate) -> models.BackupPowerState:
    """Record a backup power state transition."""
    db_state = models.BackupPowerState(
        tenant_id=tenant_id,
        event_id=state.event_id,
        is_active=state.is_active,
        power_mode=state.power_mode,
        battery_level_percent=state.battery_level_percent,
        battery_capacity_wh=state.battery_capacity_wh,
        estimated_runtime_hours=state.estimated_runtime_hours,
        solar_generation_w=state.solar_generation_w,
        solar_max_capacity_w=state.solar_max_capacity_w,
        current_load_w=state.current_load_w,
        max_load_w=state.max_load_w,
        transition_reason=state.transition_reason,
        transition_timestamp=datetime.utcnow(),
        transition_duration_ms=0,
        recovery_status=state.recovery_status or "pending",
        recovery_eta_seconds=state.recovery_eta_seconds,
    )
    db.add(db_state)
    db.commit()
    db.refresh(db_state)
    return db_state


def list_backup_power_states(db: Session, tenant_id: int, limit: int = 100) -> list[models.BackupPowerState]:
    """List recent backup power states."""
    return (
        db.query(models.BackupPowerState)
        .filter(models.BackupPowerState.tenant_id == tenant_id)
        .order_by(models.BackupPowerState.transition_timestamp.desc())
        .limit(limit)
        .all()
    )


def create_data_backup_snapshot(db: Session, tenant_id: int, snapshot: schemas.DataBackupSnapshotCreate) -> models.DataBackupSnapshot:
    """Create a new data backup snapshot record."""
    db_snapshot = models.DataBackupSnapshot(
        tenant_id=tenant_id,
        event_id=snapshot.event_id,
        snapshot_id=snapshot.snapshot_id or f"backup-{int(datetime.utcnow().timestamp() * 1000)}",
        source=snapshot.source,
        record_count=snapshot.record_count or 0,
        data_hash=snapshot.data_hash,
        storage_uri=snapshot.storage_uri,
        status=snapshot.status or "created",
        integrity_verified=snapshot.integrity_verified or False,
        verification_hash=snapshot.verification_hash,
        verification_notes=snapshot.verification_notes,
        verified_at=snapshot.verified_at,
        created_at=datetime.utcnow(),
        completed_at=None,
    )
    db.add(db_snapshot)
    db.commit()
    db.refresh(db_snapshot)
    return db_snapshot


def list_data_backup_snapshots(db: Session, tenant_id: int, limit: int = 100) -> list[models.DataBackupSnapshot]:
    """List recent data backup snapshots."""
    return (
        db.query(models.DataBackupSnapshot)
        .filter(models.DataBackupSnapshot.tenant_id == tenant_id)
        .order_by(models.DataBackupSnapshot.created_at.desc())
        .limit(limit)
        .all()
    )


def verify_data_backup_snapshot(
    db: Session,
    tenant_id: int,
    snapshot_id: str,
    verification_hash: Optional[str] = None,
    verification_notes: Optional[str] = None,
    status: str = "verified",
) -> models.DataBackupSnapshot | None:
    """Mark a backup snapshot as verified and record integrity metadata."""
    snapshot = (
        db.query(models.DataBackupSnapshot)
        .filter(models.DataBackupSnapshot.tenant_id == tenant_id)
        .filter(models.DataBackupSnapshot.snapshot_id == snapshot_id)
        .first()
    )
    if not snapshot:
        return None

    snapshot.status = status
    snapshot.integrity_verified = True
    snapshot.verification_hash = verification_hash or snapshot.data_hash
    snapshot.verification_notes = verification_notes
    snapshot.verified_at = datetime.utcnow()
    snapshot.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(snapshot)
    return snapshot


def create_data_sync_job(db: Session, tenant_id: int, sync_job: schemas.DataSyncJobCreate) -> models.DataSyncJob:
    """Create a new offline synchronization job."""
    db_job = models.DataSyncJob(
        tenant_id=tenant_id,
        sync_id=sync_job.sync_id or f"sync-{int(datetime.utcnow().timestamp() * 1000)}",
        source_system=sync_job.source_system,
        target_system=sync_job.target_system,
        status=sync_job.status or "pending",
        attempt_count=sync_job.attempt_count or 0,
        payload_hash=sync_job.payload_hash,
        result_summary=sync_job.result_summary,
        last_attempt=sync_job.last_attempt,
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def list_data_sync_jobs(db: Session, tenant_id: int, limit: int = 100) -> list[models.DataSyncJob]:
    """List recent data sync jobs."""
    return (
        db.query(models.DataSyncJob)
        .filter(models.DataSyncJob.tenant_id == tenant_id)
        .order_by(models.DataSyncJob.created_at.desc())
        .limit(limit)
        .all()
    )


def complete_data_sync_job(
    db: Session,
    tenant_id: int,
    sync_id: str,
    success: bool,
    result_summary: Optional[str] = None,
    payload_hash: Optional[str] = None,
) -> models.DataSyncJob | None:
    """Complete a sync job and update its status."""
    job = (
        db.query(models.DataSyncJob)
        .filter(models.DataSyncJob.tenant_id == tenant_id)
        .filter(models.DataSyncJob.sync_id == sync_id)
        .first()
    )
    if not job:
        return None

    job.status = "completed" if success else "failed"
    job.attempt_count = (job.attempt_count or 0) + 1
    job.last_attempt = datetime.utcnow()
    if payload_hash:
        job.payload_hash = payload_hash
    if result_summary:
        job.result_summary = result_summary
    db.commit()
    db.refresh(job)
    return job


def create_recovery_procedure(db: Session, procedure: schemas.RecoveryProcedureCreate) -> models.RecoveryProcedure:
    """Create a recovery procedure for an emergency event."""
    db_procedure = models.RecoveryProcedure(
        event_id=procedure.event_id,
        procedure_name=procedure.procedure_name,
        procedure_type=procedure.procedure_type,
        description=procedure.description,
        estimated_duration_minutes=procedure.estimated_duration_minutes or 0,
        status="pending",
        total_steps=0,
        completed_steps=0,
        success=False,
        validation_passed=False,
        rollback_performed=False,
    )
    db.add(db_procedure)
    db.commit()
    db.refresh(db_procedure)
    return db_procedure


def list_recovery_procedures(db: Session, tenant_id: int, event_id: int, limit: int = 100) -> list[models.RecoveryProcedure]:
    """List recovery procedures for a specific emergency event."""
    return (
        db.query(models.RecoveryProcedure)
        .filter(models.RecoveryProcedure.event_id == event_id)
        .order_by(models.RecoveryProcedure.created_at.desc())
        .limit(limit)
        .all()
    )


def create_robot_health_snapshot(db: Session, tenant_id: int, robot_health: schemas.RobotHealthStatus) -> models.RobotHealthSnapshot:
    """Create a robot health snapshot."""
    db_snapshot = models.RobotHealthSnapshot(
        tenant_id=tenant_id,
        robot_id=robot_health.robot_id,
        status=robot_health.status,
        battery_level=robot_health.battery_level,
        cpu_usage_percent=robot_health.cpu_usage_percent,
        memory_usage_percent=robot_health.memory_usage_percent,
        temperature_c=robot_health.temperature_c,
        uptime_seconds=robot_health.uptime_seconds,
        error_count=robot_health.error_count,
        warning_count=robot_health.warning_count,
        position=robot_health.position,
        current_task=robot_health.current_task,
        firmware_version=robot_health.firmware_version,
        last_seen=robot_health.last_seen or datetime.utcnow(),
    )
    db.add(db_snapshot)
    db.commit()
    db.refresh(db_snapshot)
    return db_snapshot


def get_recent_robot_health_snapshots(db: Session, tenant_id: int, robot_id: str | None = None, hours: int = 24) -> list[models.RobotHealthSnapshot]:
    """Get recent robot health snapshots."""
    from datetime import timedelta

    query = db.query(models.RobotHealthSnapshot).filter(
        models.RobotHealthSnapshot.tenant_id == tenant_id,
        models.RobotHealthSnapshot.last_seen >= datetime.utcnow() - timedelta(hours=hours)
    )

    if robot_id:
        query = query.filter(models.RobotHealthSnapshot.robot_id == robot_id)

    return query.order_by(models.RobotHealthSnapshot.last_seen.desc()).all()


def create_system_performance_metric(
    db: Session,
    tenant_id: int,
    metric_name: str,
    metric_category: str,
    value: float,
    unit: str | None = None,
    context_data: dict | None = None
) -> models.SystemPerformanceMetric:
    """Create a system performance metric."""
    db_metric = models.SystemPerformanceMetric(
        tenant_id=tenant_id,
        metric_name=metric_name,
        metric_category=metric_category,
        value=value,
        unit=unit,
        timestamp=datetime.utcnow(),
        context_data=context_data or {},
    )
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric


def get_system_performance_metrics(
    db: Session,
    tenant_id: int,
    metric_name: str | None = None,
    metric_category: str | None = None,
    hours: int = 24
) -> list[models.SystemPerformanceMetric]:
    """Get system performance metrics."""
    from datetime import timedelta

    query = db.query(models.SystemPerformanceMetric).filter(
        models.SystemPerformanceMetric.tenant_id == tenant_id,
        models.SystemPerformanceMetric.timestamp >= datetime.utcnow() - timedelta(hours=hours)
    )

    if metric_name:
        query = query.filter(models.SystemPerformanceMetric.metric_name == metric_name)
    if metric_category:
        query = query.filter(models.SystemPerformanceMetric.metric_category == metric_category)

    return query.order_by(models.SystemPerformanceMetric.timestamp.desc()).all()
