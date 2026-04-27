"""Tests for credential validation."""

import pytest
from src.auth.credentials import Credentials, UserRecord


class TestCredentials:
    """Test cases for Credentials class."""
    
    def test_valid_credentials(self) -> None:
        """Test creating valid credentials."""
        creds = Credentials(username="testuser", password="password123")
        assert creds.username == "testuser"
        assert creds.password == "password123"
    
    def test_empty_username(self) -> None:
        """Test that empty username raises error."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            Credentials(username="", password="password123")
    
    def test_whitespace_username(self) -> None:
        """Test that whitespace-only username raises error."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            Credentials(username="   ", password="password123")
    
    def test_empty_password(self) -> None:
        """Test that empty password raises error."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            Credentials(username="testuser", password="")
    
    def test_short_username(self) -> None:
        """Test that username shorter than 3 chars raises error."""
        with pytest.raises(ValueError, match="Username must be at least 3 characters"):
            Credentials(username="ab", password="password123")
    
    def test_short_password(self) -> None:
        """Test that password shorter than 8 chars raises error."""
        with pytest.raises(ValueError, match="Password must be at least 8 characters"):
            Credentials(username="testuser", password="pass")
    
    def test_invalid_username_characters(self) -> None:
        """Test that invalid characters in username raise error."""
        with pytest.raises(ValueError, match="Username contains invalid characters"):
            Credentials(username="test@user", password="password123")
    
    def test_valid_username_characters(self) -> None:
        """Test valid username characters."""
        creds = Credentials(username="test_user-123", password="password123")
        assert creds.username == "test_user-123"


class TestUserRecord:
    """Test cases for UserRecord class."""
    
    def test_user_record_creation(self) -> None:
        """Test creating user record."""
        user = UserRecord(
            username="testuser",
            password_hash="abc123",
            salt="def456",
            user_id="user_1"
        )
        assert user.username == "testuser"
        assert user.password_hash == "abc123"
        assert user.salt == "def456"
        assert user.is_active is True
        assert user.user_id == "user_1"
    
    def test_user_record_inactive(self) -> None:
        """Test creating inactive user record."""
        user = UserRecord(
            username="testuser",
            password_hash="abc123",
            salt="def456",
            is_active=False
        )
        assert user.is_active is False
