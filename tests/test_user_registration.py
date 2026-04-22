"""
Unit tests for user registration module.

Tests cover:
- Email validation
- Password strength validation
- Password matching
- User registration flow
- Duplicate user prevention
"""

import pytest
from pydantic import ValidationError

from src.auth.user_registration import (
    UserRegistrationService,
    UserRegistrationInput,
    PasswordRequirements,
    RegistrationError,
    User,
)


class TestPasswordValidation:
    """Test suite for password validation."""
    
    def test_valid_password(self):
        """Test that a valid password passes all checks."""
        service = UserRegistrationService()
        is_valid, message = service.validate_password_strength("SecurePass123!")
        assert is_valid is True
        assert message == ""
    
    def test_password_too_short(self):
        """Test that short passwords are rejected."""
        service = UserRegistrationService()
        is_valid, message = service.validate_password_strength("Short1!")
        assert is_valid is False
        assert "at least 8 characters" in message
    
    def test_password_missing_uppercase(self):
        """Test that passwords without uppercase are rejected."""
        service = UserRegistrationService()
        is_valid, message = service.validate_password_strength("lowercase123!")
        assert is_valid is False
        assert "uppercase letter" in message
    
    def test_password_missing_lowercase(self):
        """Test that passwords without lowercase are rejected."""
        service = UserRegistrationService()
        is_valid, message = service.validate_password_strength("UPPERCASE123!")
        assert is_valid is False
        assert "lowercase letter" in message
    
    def test_password_missing_digit(self):
        """Test that passwords without digits are rejected."""
        service = UserRegistrationService()
        is_valid, message = service.validate_password_strength("NoDigitsHere!")
        assert is_valid is False
        assert "digit" in message
    
    def test_password_missing_special_char(self):
        """Test that passwords without special characters are rejected."""
        service = UserRegistrationService()
        is_valid, message = service.validate_password_strength("NoSpecial123")
        assert is_valid is False
        assert "special character" in message
    
    def test_custom_password_requirements(self):
        """Test custom password requirements configuration."""
        custom_reqs = PasswordRequirements(
            min_length=6,
            require_uppercase=False,
            require_special=False
        )
        service = UserRegistrationService(password_requirements=custom_reqs)
        is_valid, message = service.validate_password_strength("simple123")
        assert is_valid is True
        assert message == ""


class TestEmailValidation:
    """Test suite for email validation."""
    
    def test_valid_email(self):
        """Test that valid emails are accepted."""
        user_input = UserRegistrationInput(
            email="user@example.com",
            password="SecurePass123!",
            confirm_password="SecurePass123!"
        )
        assert user_input.email == "user@example.com"
    
    def test_invalid_email_format(self):
        """Test that invalid email formats are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationInput(
                email="not-an-email",
                password="SecurePass123!",
                confirm_password="SecurePass123!"
            )
        assert "email" in str(exc_info.value).lower()
    
    def test_empty_email(self):
        """Test that empty emails are rejected."""
        with pytest.raises(ValidationError):
            UserRegistrationInput(
                email="",
                password="SecurePass123!",
                confirm_password="SecurePass123!"
            )


class TestPasswordMatching:
    """Test suite for password confirmation matching."""
    
    def test_passwords_match(self):
        """Test that matching passwords are accepted."""
        user_input = UserRegistrationInput(
            email="user@example.com",
            password="SecurePass123!",
            confirm_password="SecurePass123!"
        )
        assert user_input.password == user_input.confirm_password
    
    def test_passwords_do_not_match(self):
        """Test that non-matching passwords are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationInput(
                email="user@example.com",
                password="SecurePass123!",
                confirm_password="DifferentPass123!"
            )
        assert "do not match" in str(exc_info.value).lower()


class TestPasswordHashing:
    """Test suite for password hashing functionality."""
    
    def test_password_is_hashed(self):
        """Test that passwords are properly hashed."""
        service = UserRegistrationService()
        password = "SecurePass123!"
        hashed = service.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_correct_password(self):
        """Test that correct passwords verify successfully."""
        service = UserRegistrationService()
        password = "SecurePass123!"
        hashed = service.hash_password(password)
        
        assert service.verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """Test that incorrect passwords fail verification."""
        service = UserRegistrationService()
        password = "SecurePass123!"
        hashed = service.hash_password(password)
        
        assert service.verify_password("WrongPassword!", hashed) is False
    
    def test_different_hashes_for_same_password(self):
        """Test that same password produces different hashes (salt)."""
        service = UserRegistrationService()
        password = "SecurePass123!"
        hash1 = service.hash_password(password)
        hash2 = service.hash_password(password)
        
        assert hash1 != hash2
        assert service.verify_password(password, hash1) is True
        assert service.verify_password(password, hash2) is True


class TestUserRegistration:
    """Test suite for user registration flow."""
    
    def test_successful_registration(self):
        """Test successful user registration."""
        service = UserRegistrationService()
        user = service.register_user(
            email="newuser@example.com",
            password="SecurePass123!",
            confirm_password="SecurePass123!",
            full_name="John Doe"
        )
        
        assert isinstance(user, User)
        assert user.email == "newuser@example.com"
        assert user.full_name == "John Doe"
        assert user.is_active is True
        assert user.hashed_password != "SecurePass123!"
    
    def test_registration_without_full_name(self):
        """Test registration without providing full name."""
        service = UserRegistrationService()
        user = service.register_user(
            email="user@example.com",
            password="SecurePass123!",
            confirm_password="SecurePass123!"
        )
        
        assert user.email == "user@example.com"
        assert user.full_name is None
    
    def test_duplicate_email_registration(self):
        """Test that duplicate email registration is prevented."""
        service = UserRegistrationService()
        
        # Register first user
        service.register_user(
            email="duplicate@example.com",
            password="SecurePass123!",
            confirm_password="SecurePass123!"
        )
        
        # Attempt to register with same email
        with pytest.raises(RegistrationError) as exc_info:
            service.register_user(
                email="duplicate@example.com",
                password="AnotherPass123!",
                confirm_password="AnotherPass123!"
            )
        
        assert "already exists" in str(exc_info.value)
    
    def test_registration_with_weak_password(self):
        """Test that registration fails with weak password."""
        service = UserRegistrationService()
        
        with pytest.raises(RegistrationError) as exc_info:
            service.register_user(
                email="user@example.com",
                password="weak",
                confirm_password="weak"
            )
        
        error_message = str(exc_info.value)
        assert len(error_message) > 0
    
    def test_registration_with_mismatched_passwords(self):
        """Test that registration fails when passwords don't match."""
        service = UserRegistrationService()
        
        with pytest.raises(RegistrationError) as exc_info:
            service.register_user(
                email="user@example.com",
                password="SecurePass123!",
                confirm_password="DifferentPass123!"
            )
        
        assert "do not match" in str(exc_info.value).lower()
    
    def test_registration_with_invalid_email(self):
        """Test that registration fails with invalid email."""
        service = UserRegistrationService()
        
        with pytest.raises(RegistrationError):
            service.register_user(
                email="invalid-email",
                password="SecurePass123!",
                confirm_password="SecurePass123!"
            )
    
    def test_case_insensitive_email_duplicate_check(self):
        """Test that email duplicate check is case-insensitive."""
        service = UserRegistrationService()
        
        # Register with lowercase email
        service.register_user(
            email="user@example.com",
            password="SecurePass123!",
            confirm_password="SecurePass123!"
        )
        
        # Attempt to register with uppercase email
        with pytest.raises(RegistrationError) as exc_info:
            service.register_user(
                email="USER@EXAMPLE.COM",
                password="SecurePass123!",
                confirm_password="SecurePass123!"
            )
        
        assert "already exists" in str(exc_info.value)


class TestUserRetrieval:
    """Test suite for user retrieval functionality."""
    
    def test_get_user_by_email(self):
        """Test retrieving a user by email."""
        service = UserRegistrationService()
        
        # Register a user
        registered_user = service.register_user(
            email="findme@example.com",
            password="SecurePass123!",
            confirm_password="SecurePass123!",
            full_name="Find Me"
        )
        
        # Retrieve the user
        retrieved_user = service.get_user_by_email("findme@example.com")
        
        assert retrieved_user is not None
        assert retrieved_user.email == registered_user.email
        assert retrieved_user.full_name == "Find Me"
    
    def test_get_nonexistent_user(self):
        """Test retrieving a non-existent user returns None."""
        service = UserRegistrationService()
        user = service.get_user_by_email("nonexistent@example.com")
        assert user is None
    
    def test_user_exists_check(self):
        """Test user existence check."""
        service = UserRegistrationService()
        
        # User doesn't exist initially
        assert service.user_exists("exists@example.com") is False
        
        # Register user
        service.register_user(
            email="exists@example.com",
            password="SecurePass123!",
            confirm_password="SecurePass123!"
        )
        
        # User now exists
        assert service.user_exists("exists@example.com") is True
