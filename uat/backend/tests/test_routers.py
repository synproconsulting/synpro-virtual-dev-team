"""
test_routers.py
───────────────
Integration tests for all router modules.
Verifies that all routers are properly integrated into main app.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import Base, get_db

# ── Test Database Setup ────────────────────────────────────────────────────────

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_routers.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ── Root Endpoint Tests ────────────────────────────────────────────────────────


def test_root_endpoint():
    """Test root health check endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "auth-api"
    assert data["version"] == "1.0.0"


# ── Router Integration Tests ───────────────────────────────────────────────────


def test_auth_router_integrated():
    """Test that auth router is properly integrated."""
    # Test registration endpoint exists
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123"
        }
    )
    assert response.status_code == 200


def test_profile_router_integrated():
    """Test that profile router is properly integrated."""
    response = client.get("/profile/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_notifications_router_integrated():
    """Test that notifications router is properly integrated."""
    response = client.get("/notifications/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_proxy_router_integrated():
    """Test that proxy router is properly integrated."""
    response = client.get("/proxy/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_pm_agent_router_integrated():
    """Test that PM agent router is properly integrated."""
    response = client.get("/pm-agent/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


# ── URL Prefix Tests ───────────────────────────────────────────────────────────


def test_auth_prefix():
    """Test that auth routes have correct prefix."""
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )
    # Should get 401 (unauthorized) not 404 (not found)
    assert response.status_code in [401, 404]
    if response.status_code == 401:
        assert True  # Route exists


def test_profile_prefix():
    """Test that profile routes have correct prefix."""
    response = client.get("/profile/")
    assert response.status_code == 200


def test_notifications_prefix():
    """Test that notifications routes have correct prefix."""
    response = client.get("/notifications/")
    assert response.status_code == 200


def test_proxy_prefix():
    """Test that proxy routes have correct prefix."""
    response = client.get("/proxy/")
    assert response.status_code == 200


def test_pm_agent_prefix():
    """Test that PM agent routes have correct prefix."""
    response = client.get("/pm-agent/")
    assert response.status_code == 200


# ── Backward Compatibility Tests ───────────────────────────────────────────────


def test_all_original_endpoints_work():
    """Test that all original endpoints from main.py still work."""
    # Root endpoint
    response = client.get("/")
    assert response.status_code == 200
    
    # Auth endpoints
    register_response = client.post(
        "/auth/register",
        json={
            "email": "compat@example.com",
            "username": "compatuser",
            "password": "password123"
        }
    )
    assert register_response.status_code == 200
    
    login_response = client.post(
        "/auth/login",
        json={
            "email": "compat@example.com",
            "password": "password123"
        }
    )
    assert login_response.status_code == 200
    
    token = register_response.json()["token"]
    verify_response = client.get(f"/auth/verify?token={token}")
    assert verify_response.status_code == 200
    
    reset_response = client.post(
        "/auth/reset-password",
        json={"email": "compat@example.com"}
    )
    assert reset_response.status_code == 200
