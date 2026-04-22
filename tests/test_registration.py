"""
Unit tests for user registration module.
"""

import pytest
from datetime import datetime
from src.auth.registration import UserRegistration, RegistrationError


class TestEmailValidation:
    """Tests for email validation."""
    
    def test_valid_email(self):
        """Test that valid email addresses are accepted."""
        registration = UserRegistration()
        
        valid_emails = [
            "user@example.com",
            "test.user@example.com",
            "user+tag@example.co.uk",
            "firstname.lastname@company.org",
            "user123@test-domain.com"
        ]
        
        for email in valid_emails:
            assert registration.validate_email(email) is True
    
    def test_invalid_email_format(self):
        """Test that invalid email formats are rejected."""
        registration = UserRegistration()
        
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
            "user@example",
            "user..double@example.com",
        ]
        
        for email in invalid_emails:
            with pytest.raises(RegistrationError, match="Invalid email format"):
                registration.validate_email(email)
    
    def test_empty_email(self):
        """Test that empty email is rejected."""
        registration = UserRegistration()
        
        with pytest.raises(RegistrationError, match="Email is required"):
            registration.validate_email("")
    
    def test_email_too_long(self):
        """Test that excessively long email is rejected."""
        registration = UserRegistration()
        long_email = "a" * 250 + "@example.com"
        
        with pytest.raises(RegistrationError, match="Email address is too long"):
            registration.validate_email(long_email)
    
    def test_email_not_string(self):
        """Test that non-string email is rejected."""
        registration = UserRegistration()
        
        with pytest.raises(RegistrationError, match="Email must be a string"):
            registration.validate_email(12345)


class TestPasswordValidation:
    """Tests for password validation."""
    
    def test_valid_password(self):
        """Test that valid passwords are accepted."""
        registration = UserRegistration()
        
        valid_passwords = [
            "SecureP@ss1",
            "MyP@ssw0rd",
            "C0mpl3x!Pass",
            "Str0ng#Password"
        ]
        
        for password in valid_passwords:
            assert registration.validate_password(password) is True
    
    def test_password_too_short(self):
        """Test that short passwords are rejected."""
        registration = UserRegistration(min_password_length=8)
        
        with pytest.raises(RegistrationError, match="at least 8 characters long"):
            registration.validate_password("Short1!")
    
    def test_password_no_uppercase(self):
        """Test that passwords without uppercase are rejected."""
        registration = UserRegistration(require_uppercase=True)
        
        with pytest.raises(RegistrationError, match="uppercase letter"):
            registration.validate_password("password123!")
    
    def test_password_no_lowercase(self):
        """Test that passwords without lowercase are rejected."""
        registration = UserRegistration(require_lowercase=True)
        
        with pytest.raises(RegistrationError, match="lowercase letter"):
            registration.validate_password("PASSWORD123!")
    
    def test_password_no_digits(self):
        """Test that passwords without digits are rejected."""
        registration = UserRegistration(require_digits=True)
        
        with pytest.raises(RegistrationError, match="digit"):
            registration.validate_password("Password!")
    
    def test_password_no_special_chars(self):
        """Test that passwords without special characters are rejected."""
        registration = UserRegistration(require_special=True)
        
        with pytest.raises(RegistrationError, match="special character"):
            registration.validate_password("Password123")
    
    def test_empty_password(self):
        """Test that empty password is rejected."""
        registration = UserRegistration()
        
        with pytest.raises(RegistrationError, match="Password is required"):
            registration.validate_password("")
    
    def test_password_not_string(self):
        """Test that non-string password is rejected."""
        registration = UserRegistration()
        
        with pytest.raises(RegistrationError, match="Password must be a string"):
            registration.validate_password(12345)
    
    def test_custom_requirements(self):
        """Test password validation with custom requirements."""
        registration = UserRegistration(
            min_password_length=6,
            require_uppercase=False,
            require_special=False
        )
        
        # Should accept simpler passwords with custom requirements
        assert registration.validate_password("pass123") is True


class TestPasswordHashing:
    """Tests for password hashing and verification."""
    
    def test_hash_password(self):
        """Test that password is hashed correctly."""
        registration = UserRegistration()
        password = "SecureP@ss1"
        
        hashed = registration.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash prefix
    
    def test_verify_password_correct(self):
        """Test that correct password verification works."""
        registration = UserRegistration()
        password = "SecureP@ss1"
        
        hashed = registration.hash_password(password)
        
        assert registration.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test that incorrect password verification fails."""
        registration = UserRegistration()
        password = "SecureP@ss1"
        wrong_password = "WrongP@ss1"
        
        hashed = registration.hash_password(password)
        
        assert registration.verify_password(wrong_password, hashed) is False
    
    def test_different_hashes_for_same_password(self):
        """Test that same password produces different hashes (salt)."""
        registration = UserRegistration()
        password = "SecureP@ss1"
        
        hash1 = registration.hash_password(password)
        hash2 = registration.hash_password(password)
        
        assert hash1 != hash2
        assert registration.verify_password(password, hash1) is True
        assert registration.verify_password(password, hash2) is True


class TestUserRegistration:
    """Tests for complete user registration flow."""
    
    def test_successful_registration(self):
        """Test successful user registration."""
        registration = UserRegistration()
        
        user_data = registration.register_user(
            email="user@example.com",
            password="SecureP@ss1"
        )
        
        assert user_data["email"] == "user@example.com"
        assert "password_hash" in user_data
        assert user_data["password_hash"].startswith("$2b$")
        assert "created_at" in user_data
        assert user_data["is_active"] is True
    
    def test_registration_with_password_confirmation(self):
        """Test registration with password confirmation."""
        registration = UserRegistration()
        
        user_data = registration.register_user(
            email="user@example.com",
            password="SecureP@ss1",
            confirm_password="SecureP@ss1"
        )
        
        assert user_data["email"] == "user@example.com"
    
    def test_registration_password_mismatch(self):
        """Test registration fails when passwords don't match."""
        registration = UserRegistration()
        
        with pytest.raises(RegistrationError, match="Passwords do not match"):
            registration.register_user(
                email="user@example.com",
                password="SecureP@ss1",
                confirm_password="DifferentP@ss1"
            )
    
    def test_registration_with_additional_data(self):
        """Test registration with additional user data."""
        registration = UserRegistration()
        
        additional_data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890"
        }
        
        user_data = registration.register_user(
            email="user@example.com",
            password="SecureP@ss1",
            additional_data=additional_data
        )
        
        assert user_data["first_name"] == "John"
        assert user_data["last_name"] == "Doe"
        assert user_data["phone"] == "+1234567890"
    
    def test_registration_email_normalized(self):
        """Test that email is normalized (lowercased and trimmed)."""
        registration = UserRegistration()
        
        user_data = registration.register_user(
            email="  User@Example.COM  ",
            password="SecureP@ss1"
        )
        
        assert user_data["email"] == "user@example.com"
    
    def test_registration_invalid_email(self):
        """Test that registration fails with invalid email."""
        registration = UserRegistration()
        
        with pytest.raises(RegistrationError, match="Invalid email format"):
            registration.register_user(
                email="invalid-email",
                password="SecureP@ss1"
            )
    
    def test_registration_invalid_password(self):
        """Test that registration fails with invalid password."""
        registration = UserRegistration()
        
        with pytest.raises(RegistrationError):
            registration.register_user(
                email="user@example.com",
                password="weak"
            )
    
    def test_registration_created_at_format(self):
        """Test that created_at timestamp is in ISO format."""
        registration = UserRegistration()
        
        user_data = registration.register_user(
            email="user@example.com",
            password="SecureP@ss1"
        )
        
        # Should be able to parse the ISO format timestamp
        created_at = datetime.fromisoformat(user_data["created_at"])
        assert isinstance(created_at, datetime)


class TestCustomConfiguration:
    """Tests for custom configuration options."""
    
    def test_custom_min_password_length(self):
        """Test custom minimum password length."""
        registration = UserRegistration(min_password_length=12)
        
        with pytest.raises(RegistrationError, match="at least 12 characters long"):
            registration.validate_password("Short1!")
    
    def test_relaxed_password_requirements(self):
        """Test with relaxed password requirements."""
        registration = UserRegistration(
            min_password_length=4,
            require_uppercase=False,
            require_lowercase=False,
            require_digits=False,
            require_special=False
        )
        
        # Should accept very simple passwords
        assert registration.validate_password("test") is True
    
    def test_strict_password_requirements(self):
        """Test with strict password requirements."""
        registration = UserRegistration(
            min_password_length=16,
            require_uppercase=True,
            require_lowercase=True,
            require_digits=True,
            require_special=True
        )
        
        # Should reject passwords that don't meet all requirements
        with pytest.raises(RegistrationError):
            registration.validate_password("ShortP@ss1")
        
        # Should accept passwords that meet all requirements
        assert registration.validate_password("VeryL0ng&SecurePassword!") is True
