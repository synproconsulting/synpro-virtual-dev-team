"""
test_auth_router.py
───────────────────
Unit tests for the authentication router module.
Tests registration, login, password reset, and token verification.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone, timedelta
import jwt

from main import app
from database import Base, get_db
from models import User, PasswordResetToken
from auth_router import hash_password, verify_password, create_jwt, JWT_SECRET

# ── Test Database Setup ────────────────────────────────────────────────────────

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"

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


# ── Helper Function Tests ──────────────────────────────────────────────────────


def test_hash_password():
    """Test password hashing."""
    password = "test_password_123"
    hashed = hash_password(password)
    
    assert len(hashed) > 64
    assert hashed != password


def test_verify_password():
    """Test password verification."""
    password = "test_password_123"
    hashed = hash_password(password)
    
    assert verify_password(hashed, password) is True
    assert verify_password(hashed, "wrong_password") is False


def test_create_jwt():
    """Test JWT creation."""
    user_id = "test-user-id"
    email = "test@example.com"
    
    token = create_jwt(user_id, email)
    
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Decode and verify
    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    assert payload["user_id"] == user_id
    assert payload["email"] == email
    assert "exp" in payload


# ── Registration Tests ─────────────────────────────────────────────────────────


def test_register_success():
    """Test successful user registration."""
    response = client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "User registered successfully"
    assert "token" in data
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["username"] == "newuser"


def test_register_duplicate_email():
    """Test registration with duplicate email."""
    # Register first user
    client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "password123"
        }
    )
    
    # Try to register with same email
    response = client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "username": "user2",
            "password": "password123"
        }
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_register_short_password():
    """Test registration with short password."""
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "short"
        }
    )
    
    assert response.status_code == 400
    assert "at least 8 characters" in response.json()["detail"]


def test_register_short_username():
    """Test registration with short username."""
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "username": "a",
            "password": "password123"
        }
    )
    
    assert response.status_code == 400
    assert "at least 2 characters" in response.json()["detail"]


# ── Login Tests ────────────────────────────────────────────────────────────────


def test_login_success():
    """Test successful login."""
    # Register user first
    client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "username": "loginuser",
            "password": "password123"
        }
    )
    
    # Login
    response = client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["email"] == "login@example.com"


def test_login_wrong_password():
    """Test login with wrong password."""
    # Register user first
    client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "username": "loginuser",
            "password": "password123"
        }
    )
    
    # Login with wrong password
    response = client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_nonexistent_user():
    """Test login with nonexistent user."""
    response = client.post(
        "/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


# ── Password Reset Tests ───────────────────────────────────────────────────────


def test_reset_password_request():
    """Test password reset request."""
    # Register user first
    client.post(
        "/auth/register",
        json={
            "email": "reset@example.com",
            "username": "resetuser",
            "password": "password123"
        }
    )
    
    # Request password reset
    response = client.post(
        "/auth/reset-password",
        json={"email": "reset@example.com"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "expires_at" in data


def test_reset_password_nonexistent_user():
    """Test password reset for nonexistent user."""
    response = client.post(
        "/auth/reset-password",
        json={"email": "nonexistent@example.com"}
    )
    
    # Should not reveal if email exists
    assert response.status_code == 200


def test_confirm_reset_success():
    """Test successful password reset confirmation."""
    # Register user
    client.post(
        "/auth/register",
        json={
            "email": "reset@example.com",
            "username": "resetuser",
            "password": "oldpassword123"
        }
    )
    
    # Request reset
    reset_response = client.post(
        "/auth/reset-password",
        json={"email": "reset@example.com"}
    )
    token = reset_response.json()["token"]
    
    # Confirm reset
    response = client.post(
        "/auth/confirm-reset",
        json={
            "token": token,
            "new_password": "newpassword123"
        }
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successfully"
    
    # Verify can login with new password
    login_response = client.post(
        "/auth/login",
        json={
            "email": "reset@example.com",
            "password": "newpassword123"
        }
    )
    assert login_response.status_code == 200


def test_confirm_reset_invalid_token():
    """Test password reset with invalid token."""
    response = client.post(
        "/auth/confirm-reset",
        json={
            "token": "invalid-token",
            "new_password": "newpassword123"
        }
    )
    
    assert response.status_code == 400
    assert "Invalid or expired" in response.json()["detail"]


def test_confirm_reset_short_password():
    """Test password reset with short password."""
    # Register and get reset token
    client.post(
        "/auth/register",
        json={
            "email": "reset@example.com",
            "username": "resetuser",
            "password": "oldpassword123"
        }
    )
    
    reset_response = client.post(
        "/auth/reset-password",
        json={"email": "reset@example.com"}
    )
    token = reset_response.json()["token"]
    
    # Try to reset with short password
    response = client.post(
        "/auth/confirm-reset",
        json={
            "token": token,
            "new_password": "short"
        }
    )
    
    assert response.status_code == 400
    assert "at least 8 characters" in response.json()["detail"]


# ── Token Verification Tests ───────────────────────────────────────────────────


def test_verify_valid_token():
    """Test verification of valid JWT token."""
    # Register user and get token
    register_response = client.post(
        "/auth/register",
        json={
            "email": "verify@example.com",
            "username": "verifyuser",
            "password": "password123"
        }
    )
    token = register_response.json()["token"]
    
    # Verify token
    response = client.get(f"/auth/verify?token={token}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert "payload" in data
    assert data["payload"]["email"] == "verify@example.com"


def test_verify_invalid_token():
    """Test verification of invalid token."""
    response = client.get("/auth/verify?token=invalid-token")
    
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]


def test_verify_expired_token():
    """Test verification of expired token."""
    # Create an expired token
    payload = {
        "user_id": "test-user",
        "email": "test@example.com",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1)
    }
    expired_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    response = client.get(f"/auth/verify?token={expired_token}")
    
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()
