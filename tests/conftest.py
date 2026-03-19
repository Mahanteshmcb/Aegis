"""
Aegis Backend - Pytest Configuration & Fixtures
Global pytest configuration and reusable fixtures.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config import settings
from backend.database import Base
from backend.main import app
from backend.dependencies import get_db


# Test database setup
@pytest.fixture(scope="function")
def test_db():
    """Create a test database and yield a session."""
    engine = create_engine("sqlite:///:memory:")
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


@pytest.fixture
def client(test_db):
    """Create a FastAPI TestClient."""
    return TestClient(app)


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


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow"
    )
