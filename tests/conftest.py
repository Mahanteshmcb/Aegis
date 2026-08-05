"""
Aegis Backend - Pytest Configuration & Fixtures
Global pytest configuration and reusable fixtures.
"""

import os
# Signal to application code that pytest is running so background daemons can be skipped
os.environ.setdefault("PYTEST_RUNNING", "1")

import pytest
import os
import time
import tempfile
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch


class MockUser:
    """Mock user that supports attribute and dict-style access."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getitem__(self, key):
        return getattr(self, key)
    def get(self, key, default=None):
        return getattr(self, key, default)
from fastapi.testclient import TestClient
from fastapi import Depends, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config import settings
from backend.database import Base
import backend.models_db  # Ensure all models are registered with Base
from backend.main import app
from backend.dependencies import get_db, get_current_user


# Test database setup

@pytest.fixture(scope="function", autouse=True)
def mock_blockchain(monkeypatch):
    """Auto-mock blockchain connector for all tests."""
    # Create a mock instance of BlockchainConnector
    mock_bc = MagicMock()
    mock_bc.is_connected = True
    mock_bc.connect = MagicMock(return_value=True)
    mock_bc.submit_audit_log = MagicMock(return_value="0x" + "a" * 64)
    mock_bc.submit_requirement_request = MagicMock(return_value="0x" + "b" * 64)

    # Patch the BlockchainConnector class to return our mock instance
    monkeypatch.setattr("backend.blockchain_connector.BlockchainConnector", MagicMock(return_value=mock_bc))

    # Also patch get_blockchain_connector everywhere it's used
    monkeypatch.setattr(
        "backend.routers.robotics.get_blockchain_connector",
        lambda: mock_bc
    )
    monkeypatch.setattr(
        "backend.blockchain_connector.get_blockchain_connector",
        lambda: mock_bc
    )
    monkeypatch.setattr(
        "backend.routers.audit.get_blockchain_connector",
        lambda: mock_bc
    )
    return mock_bc


@pytest.fixture(scope="function")
def test_db():
    """Create an in-memory SQLite test database and yield a session."""
    # Use a temporary file-based SQLite DB to avoid in-memory threading issues on Windows
    tmpfile = tempfile.NamedTemporaryFile(prefix="aegis_test_", suffix=".db", delete=False)
    tmpfile_path = tmpfile.name
    tmpfile.close()
    test_db_url = f"sqlite:///{tmpfile_path}"
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    SessionLocal = TestingSessionLocal
    def override_get_db():
        try:
            db = SessionLocal()
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield SessionLocal
    app.dependency_overrides.clear()
    
    # Clean up test DB file with proper engine disposal
    try:
        engine.dispose()
    except Exception:
        pass
    
    for _ in range(5):
        try:
            if os.path.exists(tmpfile_path):
                os.remove(tmpfile_path)
            break
        except PermissionError:
            time.sleep(0.1)


@pytest.fixture
def client(test_db, monkeypatch):
    """Create a FastAPI TestClient with mocked JWT auth and blockchain."""
    from backend.blockchain_connector import get_blockchain_connector
    
    # Mock blockchain connector
    mock_bc = MagicMock()
    mock_bc.is_connected = True
    mock_bc.connect = MagicMock(return_value=True)
    mock_bc.submit_audit_log = MagicMock(return_value="0x" + "a" * 64)
    mock_bc.submit_requirement_request = MagicMock(return_value="0x" + "b" * 64)
    
    # Mock the global blockchain_connector variable to prevent initialization
    monkeypatch.setattr("backend.blockchain_connector.blockchain_connector", mock_bc)
    
    # Also mock the get_blockchain_connector function
    monkeypatch.setattr("backend.blockchain_connector.get_blockchain_connector", lambda: mock_bc)
    
    # Mock get_current_user to bypass JWT validation in tests
    def mock_get_current_user(request: Request):
        # Read Authorization header if provided, otherwise return default admin mock
        auth = request.headers.get("Authorization")
        token = None
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()

        # If a token is provided, try to decode it to respect multi-tenant tests.
        if token:
            try:
                from jose import jwt as _jwt
                from backend.config import settings as _settings
                payload = _jwt.decode(token, _settings.jwt_secret_key, algorithms=[_settings.jwt_algorithm])
                sub = payload.get("sub")
                tenant_id = payload.get("tenant_id") or payload.get("tenantId") or payload.get("user_id")
                role = payload.get("role", "admin")
                email = sub if sub else payload.get("email", "test@example.com")
                return MockUser(id=1, email=email, tenant_id=int(tenant_id) if tenant_id is not None else 1, role=role)
            except Exception:
                # Fall back to default mock user on decode failure
                return MockUser(id=1, email="test@example.com", tenant_id=1, role="admin")

        # No token: try to find an admin user in the test DB and return it.
        try:
            from backend.main import app as _app
            from backend.dependencies import get_db as _get_db
            override = _app.dependency_overrides.get(_get_db)
            if override:
                gen = override()
                try:
                    db = next(gen)
                except TypeError:
                    db = gen
                try:
                    from backend import models_db as _models_db
                    admin_user = db.query(_models_db.User).filter(_models_db.User.role == "admin").first()
                    if admin_user:
                        return MockUser(id=admin_user.id, email=admin_user.email, tenant_id=admin_user.tenant_id, role=admin_user.role)
                    # No admin found: if any tenant exists, return a tenant-scoped admin mock
                    from backend.models_db import Tenant as _Tenant
                    tenant_obj = db.query(_Tenant).order_by(_Tenant.id).first()
                    if tenant_obj:
                        return MockUser(id=0, email="implicit-admin@example.com", tenant_id=tenant_obj.id, role="admin")
                    # No admin or tenant: create one for tests.
                    from backend.models_db import User as _User
                    tenant_obj = _Tenant(name="Default Test Tenant", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
                    db.add(tenant_obj)
                    db.commit()
                    db.refresh(tenant_obj)
                    admin_user = _User(
                        email="test@example.com",
                        hashed_password="test",
                        tenant_id=tenant_obj.id,
                        role="admin",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    db.add(admin_user)
                    db.commit()
                    db.refresh(admin_user)
                    return MockUser(id=admin_user.id, email=admin_user.email, tenant_id=admin_user.tenant_id, role=admin_user.role)
                finally:
                    try:
                        gen.close()
                    except Exception:
                        pass
        except Exception:
            pass

        # If no admin exists in DB, respond as unauthorized
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Use FastAPI's dependency_overrides to mock dependencies
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_blockchain_connector] = lambda: mock_bc
    
    yield TestClient(app)
    
    # Clean up after test
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    # Stub for Day 10
    return {"id": "test-user-1", "email": "test@example.com", "tenant_id": "test-tenant"}


@pytest.fixture
def test_tenant(test_db):
    """Create a test tenant."""
    # Stub for Day 9
    return {"id": "test-tenant", "name": "Test Tenant"}


# Helper functions for tests

def create_tenant(db, tenant_name):
    """Create a test tenant in the database."""
    from backend.models_db import Tenant
    from datetime import datetime
    
    tenant = Tenant(
        name=tenant_name,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def create_operator_user(db, email, tenant_id):
    """Create a test operator user in the database."""
    from backend.models_db import User
    from datetime import datetime
    from passlib.hash import bcrypt
    
    user = User(
        email=email,
        hashed_password=bcrypt.hash("testpassword123"),
        tenant_id=tenant_id,
        role="operator",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_token_for_user(user):
    """Generate a JWT token for a test user."""
    from datetime import timedelta
    from jose import jwt
    from backend.config import settings
    
    token = jwt.encode(
        {"sub": user.email, "user_id": user.id, "tenant_id": user.tenant_id, "role": user.role},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return token


# Helper to produce auth headers for tests that import `auth_headers`
def auth_headers(user=None):
    if user is None:
        user_obj = MockUser(id=1, email="test@example.com", tenant_id=1, role="admin")
    else:
        # Accept dict-like or object
        if isinstance(user, dict):
            user_obj = MockUser(**user)
        else:
            user_obj = user
    return {"Authorization": f"Bearer {get_token_for_user(user_obj)}"}


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create an asyncio event loop for the test session to support async fixtures/plugins."""
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()
