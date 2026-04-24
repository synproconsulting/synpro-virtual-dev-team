"""Unit tests for user registration module."""

import pytest
from src.auth.user_registration import (
    User,
    RegistrationError,
    register_user,
    validate_email,
    validate_password,
    hash_password,
    verify_password,
)


class TestEmailValidation:
    """Test email validation functionality."""
    
    def test_valid_email(self):
        """Test that valid email formats are accepted."""
        assert validate_email("user@example.com") is True
        assert validate_email("test.user@domain.co.uk") is True
        assert validate_email("user+tag@example.com") is True
    
    def test_invalid_email(self):
        """Test that invalid email formats are rejected."""
        assert validate_email("invalid.email") is False
        assert validate_email("@example.com") is False
        assert validate_email("user@") is False
        assert validate_email("user@domain") is False
        assert validate_email("") is False


class TestPasswordValidation:
    """Test password validation functionality."""
    
    def test_valid_password(self):
        """Test that valid passwords are accepted."""
        assert validate_password("Password123") is True
        assert validate_password("MyP@ssw0rd") is True
        assert validate_password("Secure1Pass") is True
    
    def test_password_too_short(self):
        """Test that short passwords are rejected."""
        assert validate_password("Pass1") is False
        assert validate_password("Ab1") is False
    
    def test_password_missing_uppercase(self):
        """Test that passwords without uppercase are rejected."""
        assert validate_password("password123") is False
    
    def test_password_missing_lowercase(self):
        """Test that passwords without lowercase are rejected."""
        assert validate_password("PASSWORD123") is False
    
    def test_password_missing_digit(self):
        """Test that passwords without digits are rejected."""
        assert validate_password("PasswordOnly") is False


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test that password hashing works."""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")
    
    def test_verify_correct_password(self):
        """Test that correct password verification works."""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """Test that incorrect password is rejected."""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert verify_password("WrongPassword123", hashed) is False
    
    def test_different_hashes_for_same_password(self):
        """Test that same password produces different hashes (salt)."""
        password = "TestPassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestUserRegistration:
    """Test user registration functionality."""
    
    def test_successful_registration(self):
        """Test successful user registration."""
        user = register_user(
            username="testuser",
            email="test@example.com",
            password="Password123"
        )
        
        assert isinstance(user, User)
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password != "Password123"
        assert user.created_at is not None
    
    def test_registration_invalid_username_too_short(self):
        """Test registration fails with short username."""
        with pytest.raises(RegistrationError) as exc_info:
            register_user(
                username="ab",
                email="test@example.com",
                password="Password123"
            )
        assert "Username must be between 3 and 50 characters" in str(exc_info.value)
    
    def test_registration_invalid_username_too_long(self):
        """Test registration fails with long username."""
        with pytest.raises(RegistrationError) as exc_info:
            register_user(
                username="a" * 51,
                email="test@example.com",
                password="Password123"
            )
        assert "Username must be between 3 and 50 characters" in str(exc_info.value)
    
    def test_registration_invalid_email(self):
        """Test registration fails with invalid email."""
        with pytest.raises(RegistrationError) as exc_info:
            register_user(
                username="testuser",
                email="invalid.email",
                password="Password123"
            )
        assert "Invalid email format" in str(exc_info.value)
    
    def test_registration_invalid_password(self):
        """Test registration fails with weak password."""
        with pytest.raises(RegistrationError) as exc_info:
            register_user(
                username="testuser",
                email="test@example.com",
                password="weak"
            )
        assert "Password must be at least 8 characters" in str(exc_info.value)
    
    def test_user_repr(self):
        """Test User string representation."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_value"
        )
        
        repr_str = repr(user)
        assert "testuser" in repr_str
        assert "test@example.com" in repr_str
