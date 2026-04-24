"""
Unit tests for user registration module.
"""

import pytest
from src.auth.register import UserRegistration, RegistrationError


@pytest.fixture
def registration_service():
    """Fixture providing a fresh UserRegistration instance."""
    return UserRegistration()


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email(self, registration_service):
        """Test that valid email formats are accepted."""
        assert registration_service._validate_email("user@example.com")
        assert registration_service._validate_email("test.user@domain.co.uk")
        assert registration_service._validate_email("user+tag@example.com")

    def test_invalid_email(self, registration_service):
        """Test that invalid email formats are rejected."""
        assert not registration_service._validate_email("invalid")
        assert not registration_service._validate_email("@example.com")
        assert not registration_service._validate_email("user@")
        assert not registration_service._validate_email("user@.com")


class TestPasswordValidation:
    """Tests for password validation."""

    def test_valid_password(self, registration_service):
        """Test that valid passwords are accepted."""
        assert registration_service._validate_password("Password123")
        assert registration_service._validate_password("MyP@ssw0rd")
        assert registration_service._validate_password("Secure1Pass")

    def test_password_too_short(self, registration_service):
        """Test that short passwords are rejected."""
        assert not registration_service._validate_password("Pass1")
        assert not registration_service._validate_password("Abc123")

    def test_password_missing_uppercase(self, registration_service):
        """Test that passwords without uppercase are rejected."""
        assert not registration_service._validate_password("password123")

    def test_password_missing_lowercase(self, registration_service):
        """Test that passwords without lowercase are rejected."""
        assert not registration_service._validate_password("PASSWORD123")

    def test_password_missing_digit(self, registration_service):
        """Test that passwords without digits are rejected."""
        assert not registration_service._validate_password("PasswordOnly")


class TestUserRegistration:
    """Tests for user registration."""

    def test_successful_registration(self, registration_service):
        """Test successful user registration."""
        result = registration_service.register_user(
            username="testuser",
            email="test@example.com",
            password="SecurePass123"
        )
        
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"
        assert result["is_active"] is True
        assert "created_at" in result
        assert "password" not in result
        assert "password_hash" not in result

    def test_username_too_short(self, registration_service):
        """Test that short usernames are rejected."""
        with pytest.raises(RegistrationError, match="at least 3 characters"):
            registration_service.register_user(
                username="ab",
                email="test@example.com",
                password="SecurePass123"
            )

    def test_duplicate_username(self, registration_service):
        """Test that duplicate usernames are rejected."""
        registration_service.register_user(
            username="testuser",
            email="test1@example.com",
            password="SecurePass123"
        )
        
        with pytest.raises(RegistrationError, match="already exists"):
            registration_service.register_user(
                username="testuser",
                email="test2@example.com",
                password="SecurePass456"
            )

    def test_invalid_email_registration(self, registration_service):
        """Test that invalid emails are rejected during registration."""
        with pytest.raises(RegistrationError, match="Invalid email"):
            registration_service.register_user(
                username="testuser",
                email="invalid-email",
                password="SecurePass123"
            )

    def test_weak_password_registration(self, registration_service):
        """Test that weak passwords are rejected during registration."""
        with pytest.raises(RegistrationError, match="Password must be"):
            registration_service.register_user(
                username="testuser",
                email="test@example.com",
                password="weak"
            )


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_password_is_hashed(self, registration_service):
        """Test that passwords are hashed and not stored in plain text."""
        registration_service.register_user(
            username="testuser",
            email="test@example.com",
            password="SecurePass123"
        )
        
        stored_hash = registration_service.users_db["testuser"]["password_hash"]
        assert stored_hash != "SecurePass123"
        assert stored_hash.startswith("$2b$")  # bcrypt prefix

    def test_password_verification_success(self, registration_service):
        """Test successful password verification."""
        registration_service.register_user(
            username="testuser",
            email="test@example.com",
            password="SecurePass123"
        )
        
        assert registration_service.verify_password("testuser", "SecurePass123")

    def test_password_verification_failure(self, registration_service):
        """Test failed password verification."""
        registration_service.register_user(
            username="testuser",
            email="test@example.com",
            password="SecurePass123"
        )
        
        assert not registration_service.verify_password("testuser", "WrongPass123")

    def test_password_verification_nonexistent_user(self, registration_service):
        """Test password verification for nonexistent user."""
        assert not registration_service.verify_password("nobody", "SecurePass123")


class TestUserExists:
    """Tests for user existence checking."""

    def test_user_exists_true(self, registration_service):
        """Test that existing users are found."""
        registration_service.register_user(
            username="testuser",
            email="test@example.com",
            password="SecurePass123"
        )
        
        assert registration_service.user_exists("testuser")

    def test_user_exists_false(self, registration_service):
        """Test that nonexistent users are not found."""
        assert not registration_service.user_exists("nobody")
