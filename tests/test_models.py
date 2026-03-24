"""
Aegis Backend - SQLAlchemy Model Unit Tests
"""
import pytest
from backend.models_db import Tenant, User, Zone, Sensor, SensorData, AuditLog, VryndaraRequest
from datetime import datetime

def test_tenant_model():
    t = Tenant(name="Test Tenant")
    assert t.name == "Test Tenant"
    # created_at is None until added to a session and flushed
    assert t.created_at is None

def test_user_model():
    u = User(email="user@example.com", hashed_password="x", role="admin", tenant_id=1)
    assert u.email == "user@example.com"
    assert u.role == "admin"
    assert u.tenant_id == 1

def test_zone_model():
    z = Zone(name="Zone 1", description="desc", location="loc", tenant_id=1)
    assert z.name == "Zone 1"
    assert z.tenant_id == 1

def test_sensor_model():
    s = Sensor(type="temp", location="lab", tenant_id=1)
    assert s.type == "temp"
    assert s.location == "lab"
    assert s.tenant_id == 1

def test_sensor_data_model():
    sd = SensorData(sensor_id=1, timestamp=datetime.utcnow(), value="42", unit="C")
    assert sd.value == "42"
    assert sd.unit == "C"
    assert sd.sensor_id == 1

def test_audit_log_model():
    al = AuditLog(sensor_id=1, event_type="test", data_hash="abc", blockchain_tx="tx1")
    assert al.event_type == "test"
    assert al.data_hash == "abc"
    assert al.blockchain_tx == "tx1"
    assert al.sensor_id == 1

def test_vryndara_request_model():
    vr = VryndaraRequest(
        tenant_id=1,
        agent="Researcher",
        request_type="test",
        payload={"foo": "bar"},
        status="pending"
    )
    assert vr.tenant_id == 1
    assert vr.agent == "Researcher"
    assert vr.status == "pending"
    assert vr.payload["foo"] == "bar"
