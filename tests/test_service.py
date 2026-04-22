"""
Tests for authentication service.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from src.auth.models import Base, User, PasswordResetToken
from src.auth.service import AuthService
from src.auth.schemas import UserCreate


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def auth_service(db_session):
    """Create an auth service instance."""
    return AuthService(db_session)


def test_create_user(auth_service):
    """Test user creation."""
    user_data = UserCreate(
        email="test@example.com",
        password="TestPassword123!",
        full_name="Test User"
    )
    
    user = auth_service.create_user(user_data)
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.is_active is True
    assert user.hashed_password != "TestPassword123!"


def test_create_user_duplicate_email(auth_service):
    """Test creating user with duplicate email raises error."""
    user_data = UserCreate(
        email="test@example.com",
        password="TestPassword123!",
        full_name="Test User"
    )
    
    auth_service.create_user(user_data)
    
    with pytest.raises(ValueError, match="Email already registered"):
        auth_service.create_user(user_data)


def test_get_user_by_email(auth_service):
    """Test retrieving user by email."""
    user_data = UserCreate(
        email="test@example.com",
        password="TestPassword123!",
        full_name="Test User"
    )
    
    created_user = auth_service.create_user(user_data)
    retrieved_user = auth_service.get_user_by_email("test@example.com")
    
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == created_user.email


def test_get_user_by_email_not_found(auth_service):
    """Test retrieving non-existent user returns None."""
    user = auth_service.get_user_by_email("nonexistent@example.com")
    assert user is None


def test_authenticate_user_success(auth_service):
    """Test successful user authentication."""
    user_data = UserCreate(
        email="test@example.com",
        password="TestPassword123!",
        full_name="Test User"
    )
    
    auth_service.create_user(user_data)
    authenticated_user = auth_service.authenticate_user("test@example.com", "TestPassword123!")
    
    assert authenticated_user is not None
    assert authenticated_user.email == "test@example.com"


def test_authenticate_user_wrong_password(auth_service):
    """Test authentication with wrong password fails."""
    user_data = UserCreate(
        email="test@example.com",
        password="TestPassword123!",
        full_name="Test User"
    )
    
    auth_service.create_user(user_data)
    authenticated_user = auth_service.authenticate_user("test@example.com", "WrongPassword")
    
    assert authenticated_user is None


def test_authenticate_user_nonexistent(auth_service):
    """Test authentication with non-existent user fails."""
    authenticated_user = auth_service.authenticate_user("nonexistent@example.com", "password")
    assert authenticated_user is None


def test_authenticate_user_inactive(auth_service, db_session):
    """Test authentication with inactive user fails."""
    user_data = UserCreate(
        email="test@example.com",
        password="TestPassword123!",
        full_name="Test User"
    )
    
    user = auth_service.create_user(user_data)
    user.is_active = False
    db_session.commit()
    
    authenticated_user = auth_service.authenticate_user("test@example.com", "TestPassword123!")
    assert authenticated_user is None


def test_create_password_reset_token(auth_service):
    """Test creating password reset token."""
    user_data = UserCreate(
        email="test@example.com",
        password="TestPassword123!",
        full_name="Test User"
    )
    
    auth_service.create_user(user_data)
    token = auth_service.create_password_reset_token("test@example.com")
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) == 64


def test_create_password_reset_token_nonexistent_user(auth_service):
    """Test creating reset token for non-existent user returns None."""
    token = auth_service.create_password_reset_token("nonexistent@example.com")
    assert token is None


def test_reset_password_success(auth_service):
    """Test successful password reset."""
    user_data = UserCreate(
        email="test@example.com",
        password="OldPassword123!",
        full_name="Test User"
    )
    
    auth_service.create_user(user_data)
    token = auth_service.create_password_reset_token("test@example.com")
    
    success = auth_service.reset_password(token, "NewPassword123!")
    assert success is True
    
    # Verify user can login with new password
    authenticated_user = auth_service.authenticate_user("test@example.com", "NewPassword123!")
    assert authenticated_user is not None
    
    # Verify old password no longer works
    old_auth = auth_service.authenticate_user("test@example.com", "OldPassword123!")
    assert old_auth is None


def test_reset_password_invalid_token(auth_service):
    """Test password reset with invalid token fails."""
    success = auth_service.reset_password("invalid-token", "NewPassword123!")
    assert success is False


def test_reset_password_used_token(auth_service):
    """Test password reset with already used token fails."""
    user_data = UserCreate(
        email="test@example.com",
        password="OldPassword123!",
        full_name="Test User"
    )
    
    auth_service.create_user(user_data)
    token = auth_service.create_password_reset_token("test@example.com")
    
    # Use token once
    auth_service.reset_password(token, "NewPassword123!")
    
    # Try to use token again
    success = auth_service.reset_password(token, "AnotherPassword123!")
    assert success is False
