import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import backend.database as database


@pytest.fixture(scope='session', autouse=True)
def in_memory_db():
    """Create an in-memory SQLite database for the test session and
    override the project's database engine and SessionLocal to point
    at it. This keeps tests hermetic and fast.
    """
    # Create in-memory engine
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create a session factory bound to the in-memory engine
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Patch the backend.database module to use the in-memory engine/session
    database.engine = engine
    database.SessionLocal = TestSessionLocal

    # Create all tables using the project's Base metadata
    database.Base.metadata.create_all(bind=engine)

    yield

    # Teardown: drop all tables
    database.Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    """Provide a fresh DB session for a test and roll back changes on close."""
    session = database.SessionLocal()
    try:
        yield session
    finally:
        session.close()
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
from backend.dependencies import get_db, get_current_user, get_current_admin


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
    
    # Mock get_current_user to bypass JWT validation in tests, while still enforcing
    # explicit auth for protected routes.
    def mock_get_current_user(request: Request):
        auth = request.headers.get("Authorization")
        token = None
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()

        if not token:
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Not authenticated")

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
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    def mock_get_current_admin(request: Request):
        current_user = mock_get_current_user(request)
        if current_user.get("role") not in ("admin", "superadmin"):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    # Use FastAPI's dependency_overrides to mock dependencies
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_current_admin] = mock_get_current_admin
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
