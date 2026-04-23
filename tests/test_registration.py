"""
Unit tests for user registration module.
"""

import pytest
from src.auth.registration import (
    UserRegistration, 
    ValidationError, 
    register_user
)


class TestEmailValidation:
    """Test email validation."""

    def test_valid_email(self):
        """Test valid email formats."""
        registration = UserRegistration()
        
        valid_emails = [
            "user@example.com",
            "test.user@example.co.uk",
            "user+tag@example.com",
            "user_name@example.com",
            "user123@example.com",
            "123@example.com"
        ]
        
        for email in valid_emails:
            is_valid, error = registration.validate_email(email)
            assert is_valid, f"Email {email} should be valid"
            assert error is None

    def test_invalid_email_format(self):
        """Test invalid email formats."""
        registration = UserRegistration()
        
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
            "user@example",
            "",
            "user@@example.com"
        ]
        
        for email in invalid_emails:
            is_valid, error = registration.validate_email(email)
            assert not is_valid, f"Email {email} should be invalid"
            assert error is not None

    def test_email_too_long(self):
        """Test email exceeding maximum length."""
        registration = UserRegistration()
        long_email = "a" * 250 + "@example.com"
        
        is_valid, error = registration.validate_email(long_email)
        assert not is_valid
        assert "too long" in error.lower()

    def test_email_required(self):
        """Test that email is required."""
        registration = UserRegistration()
        
        is_valid, error = registration.validate_email("")
        assert not is_valid
        assert "required" in error.lower()

    def test_duplicate_email(self):
        """Test that duplicate emails are rejected."""
        registration = UserRegistration()
        email = "test@example.com"
        password = "ValidPass123!"
        
        # Register first user
        registration.register(email, password)
        
        # Try to validate same email again
        is_valid, error = registration.validate_email(email)
        assert not is_valid
        assert "already registered" in error.lower()


class TestPasswordValidation:
    """Test password validation."""

    def test_valid_password(self):
        """Test valid password."""
        registration = UserRegistration()
        valid_passwords = [
            "ValidPass123!",
            "MyP@ssw0rd",
            "Str0ng!Pass",
            "C0mpl3x@Password"
        ]
        
        for password in valid_passwords:
            is_valid, error = registration.validate_password(password)
            assert is_valid, f"Password {password} should be valid"
            assert error is None

    def test_password_too_short(self):
        """Test password below minimum length."""
        registration = UserRegistration()
        
        is_valid, error = registration.validate_password("Short1!")
        assert not is_valid
        assert "at least" in error.lower()

    def test_password_missing_uppercase(self):
        """Test password without uppercase letter."""
        registration = UserRegistration()
        
        is_valid, error = registration.validate_password("password123!")
        assert not is_valid
        assert "uppercase" in error.lower()

    def test_password_missing_lowercase(self):
        """Test password without lowercase letter."""
        registration = UserRegistration()
        
        is_valid, error = registration.validate_password("PASSWORD123!")
        assert not is_valid
        assert "lowercase" in error.lower()

    def test_password_missing_digit(self):
        """Test password without digit."""
        registration = UserRegistration()
        
        is_valid, error = registration.validate_password("Password!")
        assert not is_valid
        assert "digit" in error.lower()

    def test_password_missing_special_character(self):
        """Test password without special character."""
        registration = UserRegistration()
        
        is_valid, error = registration.validate_password("Password123")
        assert not is_valid
        assert "special character" in error.lower()

    def test_password_required(self):
        """Test that password is required."""
        registration = UserRegistration()
        
        is_valid, error = registration.validate_password("")
        assert not is_valid
        assert "required" in error.lower()

    def test_password_too_long(self):
        """Test password exceeding maximum length."""
        registration = UserRegistration()
        long_password = "A" * 130 + "a1!"
        
        is_valid, error = registration.validate_password(long_password)
        assert not is_valid
        assert "must not exceed" in error.lower()


class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_hash_password(self):
        """Test password hashing."""
        registration = UserRegistration()
        password = "ValidPass123!"
        
        hashed = registration.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash prefix

    def test_verify_password(self):
        """Test password verification."""
        registration = UserRegistration()
        password = "ValidPass123!"
        
        hashed = registration.hash_password(password)
        
        # Correct password should verify
        assert registration.verify_password(password, hashed)
        
        # Incorrect password should not verify
        assert not registration.verify_password("WrongPass123!", hashed)

    def test_different_hashes_for_same_password(self):
        """Test that same password produces different hashes (salt)."""
        registration = UserRegistration()
        password = "ValidPass123!"
        
        hash1 = registration.hash_password(password)
        hash2 = registration.hash_password(password)
        
        assert hash1 != hash2
        # Both should still verify
        assert registration.verify_password(password, hash1)
        assert registration.verify_password(password, hash2)


class TestUserRegistration:
    """Test complete user registration flow."""

    def test_successful_registration(self):
        """Test successful user registration."""
        registration = UserRegistration()
        email = "newuser@example.com"
        password = "ValidPass123!"
        
        result = registration.register(email, password)
        
        assert result["email"] == email.lower()
        assert "created_at" in result
        assert result["is_active"] is True
        assert "password_hash" not in result  # Should not return password

    def test_registration_with_additional_data(self):
        """Test registration with additional user data."""
        registration = UserRegistration()
        email = "newuser@example.com"
        password = "ValidPass123!"
        additional_data = {
            "first_name": "John",
            "last_name": "Doe"
        }
        
        result = registration.register(email, password, additional_data)
        
        assert result["email"] == email.lower()
        assert result["is_active"] is True

    def test_registration_invalid_email(self):
        """Test registration with invalid email."""
        registration = UserRegistration()
        
        with pytest.raises(ValidationError) as exc_info:
            registration.register("invalid-email", "ValidPass123!")
        
        assert "email" in str(exc_info.value).lower()

    def test_registration_invalid_password(self):
        """Test registration with invalid password."""
        registration = UserRegistration()
        
        with pytest.raises(ValidationError) as exc_info:
            registration.register("valid@example.com", "weak")
        
        assert "password" in str(exc_info.value).lower()

    def test_get_user(self):
        """Test retrieving registered user."""
        registration = UserRegistration()
        email = "test@example.com"
        password = "ValidPass123!"
        
        registration.register(email, password)
        user = registration.get_user(email)
        
        assert user is not None
        assert user["email"] == email.lower()
        assert "password_hash" in user

    def test_get_nonexistent_user(self):
        """Test retrieving non-existent user."""
        registration = UserRegistration()
        
        user = registration.get_user("nonexistent@example.com")
        assert user is None

    def test_email_case_insensitive(self):
        """Test that email lookup is case-insensitive."""
        registration = UserRegistration()
        email = "Test@Example.COM"
        password = "ValidPass123!"
        
        registration.register(email, password)
        
        # Should find user with different case
        user = registration.get_user("test@example.com")
        assert user is not None
        assert user["email"] == "test@example.com"


class TestConvenienceFunction:
    """Test the convenience register_user function."""

    def test_register_user_function(self):
        """Test register_user convenience function."""
        email = "user@example.com"
        password = "ValidPass123!"
        
        result = register_user(email, password)
        
        assert result["email"] == email.lower()
        assert "created_at" in result
        assert result["is_active"] is True

    def test_register_user_with_additional_data(self):
        """Test register_user with additional data."""
        email = "user@example.com"
        password = "ValidPass123!"
        additional_data = {"role": "user"}
        
        result = register_user(email, password, additional_data)
        
        assert result["email"] == email.lower()
        assert result["is_active"] is True

    def test_register_user_validation_error(self):
        """Test register_user with validation error."""
        with pytest.raises(ValidationError):
            register_user("invalid-email", "ValidPass123!")
