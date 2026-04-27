"""Tests for login service."""

import pytest
from src.auth.credentials import Credentials, UserRecord
from src.auth.login_service import LoginService, LoginResult
from src.auth.password_hasher import PasswordHasher
from src.auth.user_repository import InMemoryUserRepository


class TestLoginService:
    """Test cases for LoginService."""
    
    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.repo = InMemoryUserRepository()
        self.hasher = PasswordHasher()
        self.service = LoginService(self.repo, self.hasher)
        
        # Create test user
        password_hash, salt = self.hasher.hash_new_password("password123")
        user = UserRecord(
            username="testuser",
            password_hash=password_hash,
            salt=salt,
            user_id="user_1"
        )
        self.repo.save_user(user)
    
    def test_successful_login(self) -> None:
        """Test successful login with correct credentials."""
        creds = Credentials(username="testuser", password="password123")
        result = self.service.login(creds)
        
        assert result.success is True
        assert result.username == "testuser"
        assert result.user_id == "user_1"
        assert result.error_message is None
    
    def test_login_wrong_password(self) -> None:
        """Test login with incorrect password."""
        creds = Credentials(username="testuser", password="wrongpassword")
        result = self.service.login(creds)
        
        assert result.success is False
        assert result.username is None
        assert result.error_message == "Invalid username or password"
    
    def test_login_nonexistent_user(self) -> None:
        """Test login with non-existent username."""
        creds = Credentials(username="nonexistent", password="password123")
        result = self.service.login(creds)
        
        assert result.success is False
        assert result.error_message == "Invalid username or password"
    
    def test_login_inactive_user(self) -> None:
        """Test login with inactive user account."""
        password_hash, salt = self.hasher.hash_new_password("password123")
        inactive_user = UserRecord(
            username="inactive",
            password_hash=password_hash,
            salt=salt,
            is_active=False
        )
        self.repo.save_user(inactive_user)
        
        creds = Credentials(username="inactive", password="password123")
        result = self.service.login(creds)
        
        assert result.success is False
        assert result.error_message == "Account is inactive"
    
    def test_login_invalid_credentials_format(self) -> None:
        """Test login with invalid credential format."""
        with pytest.raises(ValueError):
            Credentials(username="ab", password="password123")
