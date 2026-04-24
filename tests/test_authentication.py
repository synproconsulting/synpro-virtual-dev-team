"""
Unit tests for authentication service.
"""

import os
import pytest
from datetime import datetime, timedelta

from src.auth.authentication import AuthService
from src.auth.user import User


class TestAuthService:
    """Test suite for AuthService class."""
    
    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        os.environ["JWT_SECRET_KEY"] = "test-secret-key"
        os.environ["JWT_ALGORITHM"] = "HS256"
        os.environ["JWT_EXPIRATION_MINUTES"] = "30"
        self.auth_service = AuthService()
    
    def test_hash_password(self) -> None:
        """Test password hashing functionality."""
        password = "test_password123"
        hashed = self.auth_service.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)
    
    def test_verify_password_success(self) -> None:
        """Test password verification with correct password."""
        password = "test_password123"
        hashed = self.auth_service.hash_password(password)
        
        assert self.auth_service.verify_password(password, hashed) is True
    
    def test_verify_password_failure(self) -> None:
        """Test password verification with incorrect password."""
        password = "test_password123"
        hashed = self.auth_service.hash_password(password)
        
        assert self.auth_service.verify_password("wrong_password", hashed) is False
    
    def test_register_user_success(self) -> None:
        """Test successful user registration."""
        email = "test@example.com"
        password = "secure_password123"
        
        user = self.auth_service.register_user(email, password)
        
        assert isinstance(user, User)
        assert user.email == email
        assert user.user_id is not None
        assert len(user.user_id) > 0
        assert user.password_hash != password
        assert isinstance(user.created_at, datetime)
    
    def test_register_user_duplicate_email(self) -> None:
        """Test registration with duplicate email raises ValueError."""
        email = "test@example.com"
        password = "secure_password123"
        
        self.auth_service.register_user(email, password)
        
        with pytest.raises(ValueError, match="User with this email already exists"):
            self.auth_service.register_user(email, password)
    
    def test_register_user_short_password(self) -> None:
        """Test registration with short password raises ValueError."""
        email = "test@example.com"
        password = "short"
        
        with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
            self.auth_service.register_user(email, password)
    
    def test_authenticate_user_success(self) -> None:
        """Test successful user authentication."""
        email = "test@example.com"
        password = "secure_password123"
        
        self.auth_service.register_user(email, password)
        result = self.auth_service.authenticate_user(email, password)
        
        assert result is True
    
    def test_authenticate_user_wrong_password(self) -> None:
        """Test authentication with wrong password."""
        email = "test@example.com"
        password = "secure_password123"
        
        self.auth_service.register_user(email, password)
        result = self.auth_service.authenticate_user(email, "wrong_password")
        
        assert result is False
    
    def test_authenticate_user_nonexistent(self) -> None:
        """Test authentication with non-existent user."""
        result = self.auth_service.authenticate_user("nonexistent@example.com", "password")
        
        assert result is False
    
    def test_generate_token(self) -> None:
        """Test JWT token generation."""
        user_id = "test-user-id-123"
        token = self.auth_service.generate_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_validate_token_success(self) -> None:
        """Test JWT token validation with valid token."""
        user_id = "test-user-id-123"
        token = self.auth_service.generate_token(user_id)
        
        payload = self.auth_service.validate_token(token)
        
        assert payload is not None
        assert payload["sub"] == user_id
        assert "exp" in payload
        assert "iat" in payload
    
    def test_validate_token_invalid(self) -> None:
        """Test JWT token validation with invalid token."""
        invalid_token = "invalid.token.here"
        
        payload = self.auth_service.validate_token(invalid_token)
        
        assert payload is None
    
    def test_get_user_by_email_success(self) -> None:
        """Test retrieving user by email."""
        email = "test@example.com"
        password = "secure_password123"
        
        registered_user = self.auth_service.register_user(email, password)
        retrieved_user = self.auth_service.get_user_by_email(email)
        
        assert retrieved_user is not None
        assert retrieved_user.email == email
        assert retrieved_user.user_id == registered_user.user_id
    
    def test_get_user_by_email_not_found(self) -> None:
        """Test retrieving non-existent user by email."""
        retrieved_user = self.auth_service.get_user_by_email("nonexistent@example.com")
        
        assert retrieved_user is None
    
    def test_last_login_updated(self) -> None:
        """Test that last_login is updated on successful authentication."""
        email = "test@example.com"
        password = "secure_password123"
        
        user = self.auth_service.register_user(email, password)
        assert user.last_login is None
        
        self.auth_service.authenticate_user(email, password)
        
        updated_user = self.auth_service.get_user_by_email(email)
        assert updated_user.last_login is not None
        assert isinstance(updated_user.last_login, datetime)


class TestUser:
    """Test suite for User model."""
    
    def test_user_creation_valid(self) -> None:
        """Test creating a valid user."""
        user = User(
            user_id="123",
            email="test@example.com",
            password_hash="hashed_password",
            created_at=datetime.utcnow()
        )
        
        assert user.user_id == "123"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.last_login is None
    
    def test_user_invalid_email(self) -> None:
        """Test that invalid email raises ValueError."""
        with pytest.raises(ValueError, match="Invalid email address"):
            User(
                user_id="123",
                email="invalid-email",
                password_hash="hashed_password",
                created_at=datetime.utcnow()
            )
    
    def test_user_empty_email(self) -> None:
        """Test that empty email raises ValueError."""
        with pytest.raises(ValueError, match="Invalid email address"):
            User(
                user_id="123",
                email="",
                password_hash="hashed_password",
                created_at=datetime.utcnow()
            )
    
    def test_user_empty_password_hash(self) -> None:
        """Test that empty password hash raises ValueError."""
        with pytest.raises(ValueError, match="Password hash cannot be empty"):
            User(
                user_id="123",
                email="test@example.com",
                password_hash="",
                created_at=datetime.utcnow()
            )
    
    def test_user_empty_user_id(self) -> None:
        """Test that empty user ID raises ValueError."""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            User(
                user_id="",
                email="test@example.com",
                password_hash="hashed_password",
                created_at=datetime.utcnow()
            )
