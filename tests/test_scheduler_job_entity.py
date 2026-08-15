import asyncio
import pytest
from backend.database import SessionLocal, Base
from backend.models.lab_automation import AutomationJob
from backend import models_scene as models_scene
from backend.services import automation_scheduler

# Ensure realtime emits are no-ops during tests
import backend.realtime as realtime

@pytest.fixture(autouse=True)
def noop_realtime_emit(monkeypatch):
    async def _noop(*a, **k):
        return None
    monkeypatch.setattr(realtime.sio, 'emit', _noop)
    yield


def test_execute_job_moves_entity():
    # Create entity and job, run _execute_job and assert entity moved
    Base.metadata.create_all(bind=SessionLocal.kw['bind'])
    session = SessionLocal()
    try:
        session.query(models_scene.SceneEntity).delete()
        session.query(AutomationJob).delete()
        from backend.models.lab_automation import AutomationDevice
        session.query(AutomationDevice).delete()
        from backend.models_db import Tenant
        session.query(Tenant).delete()
        session.commit()

        # Ensure a tenant exists for FK constraints
        import uuid
        tenant = Tenant(name=f'Test Tenant {uuid.uuid4().hex[:8]}')
        session.add(tenant)
        session.commit()
        session.refresh(tenant)

        # create a scene entity first and then an AutomationDevice sharing the same id
        ent = models_scene.SceneEntity(name='TestEntity', type='robot', x=0.0, y=0.0, z=0.0, rotation=0.0)
        session.add(ent)
        session.commit()
        session.refresh(ent)
        ent.x = 0.0
        ent.y = 0.0
        session.add(ent)
        session.commit()
        session.refresh(ent)

        # create an AutomationDevice with explicit id matching the SceneEntity so the scheduler can find the scene object
        device = AutomationDevice(id=ent.id, tenant_id=tenant.id, name='DeviceForTest', device_type='robot')
        session.add(device)
        session.commit()
        session.refresh(device)

        # create job targeting the device/entity
        job = AutomationJob(tenant_id=tenant.id, device_id=device.id, name='MoveTest', command='robot:command', parameters={'dx': 2, 'dy': 1}, status='pending')
        session.add(job)
        session.commit()
        session.refresh(job)

        # run the async executor
        old_x = float(ent.x)
        old_y = float(ent.y)
        asyncio.get_event_loop().run_until_complete(automation_scheduler._execute_job(session, job))

        # reload entity and assert deltas match command parameters
        session.refresh(ent)
        assert abs((ent.x - old_x) - 2.0) < 0.25
        assert abs((ent.y - old_y) - 1.0) < 0.25

        # reload job
        session.refresh(job)
        assert job.status in ('completed', 'pending', 'running', 'failed')
    finally:
        session.close()
