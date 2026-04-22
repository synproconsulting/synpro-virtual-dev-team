"""
Tests for user registration service.
"""

import pytest
from src.auth.registration import UserRegistration, RegistrationError
from src.auth.storage import InMemoryUserStorage


class TestUserRegistration:
    """Test cases for user registration."""
    
    def test_successful_registration(self):
        """Test successful user registration."""
        registration = UserRegistration()
        email = "newuser@example.com"
        password = "ValidPass123!"
        
        result = registration.register_user(email, password)
        
        assert result is not None
        assert result["email"] == email
        assert result["user_id"] is not None
        assert result["is_active"] is True
        assert "hashed_password" not in result
    
    def test_registration_email_normalization(self):
        """Test that email is normalized to lowercase."""
        registration = UserRegistration()
        email = "NewUser@Example.COM"
        password = "ValidPass123!"
        
        result = registration.register_user(email, password)
        
        assert result["email"] == "newuser@example.com"
    
    def test_registration_duplicate_email(self):
        """Test that duplicate email registration fails."""
        registration = UserRegistration()
        email = "duplicate@example.com"
        password = "ValidPass123!"
        
        # First registration should succeed
        registration.register_user(email, password)
        
        # Second registration with same email should fail
        with pytest.raises(RegistrationError) as exc_info:
            registration.register_user(email, password)
        
        assert "already registered" in str(exc_info.value).lower()
    
    def test_registration_invalid_email(self):
        """Test that invalid email fails registration."""
        registration = UserRegistration()
        invalid_email = "not-an-email"
        password = "ValidPass123!"
        
        with pytest.raises(RegistrationError) as exc_info:
            registration.register_user(invalid_email, password)
        
        assert "email" in str(exc_info.value).lower()
    
    def test_registration_invalid_password(self):
        """Test that invalid password fails registration."""
        registration = UserRegistration()
        email = "user@example.com"
        weak_password = "weak"
        
        with pytest.raises(RegistrationError) as exc_info:
            registration.register_user(email, weak_password)
        
        assert "password" in str(exc_info.value).lower()
    
    def test_registration_empty_email(self):
        """Test that empty email fails registration."""
        registration = UserRegistration()
        
        with pytest.raises(RegistrationError) as exc_info:
            registration.register_user("", "ValidPass123!")
        
        assert "required" in str(exc_info.value).lower()
    
    def test_registration_empty_password(self):
        """Test that empty password fails registration."""
        registration = UserRegistration()
        
        with pytest.raises(RegistrationError) as exc_info:
            registration.register_user("user@example.com", "")
        
        assert "required" in str(exc_info.value).lower()
    
    def test_validate_registration_data_valid(self):
        """Test validation of valid registration data."""
        registration = UserRegistration()
        
        result = registration.validate_registration_data(
            "valid@example.com",
            "ValidPass123!"
        )
        
        assert result["email"]["valid"] is True
        assert result["password"]["valid"] is True
        assert result["overall_valid"] is True
    
    def test_validate_registration_data_invalid_email(self):
        """Test validation with invalid email."""
        registration = UserRegistration()
        
        result = registration.validate_registration_data(
            "invalid-email",
            "ValidPass123!"
        )
        
        assert result["email"]["valid"] is False
        assert result["email"]["error"] != ""
        assert result["overall_valid"] is False
    
    def test_validate_registration_data_weak_password(self):
        """Test validation with weak password."""
        registration = UserRegistration()
        
        result = registration.validate_registration_data(
            "valid@example.com",
            "weak"
        )
        
        assert result["password"]["valid"] is False
        assert result["password"]["error"] != ""
        assert result["overall_valid"] is False
    
    def test_validate_registration_data_existing_email(self):
        """Test validation with already registered email."""
        registration = UserRegistration()
        email = "existing@example.com"
        
        # Register user first
        registration.register_user(email, "ValidPass123!")
        
        # Validate with same email
        result = registration.validate_registration_data(email, "AnotherPass123!")
        
        assert result["email"]["valid"] is False
        assert "already registered" in result["email"]["error"].lower()
        assert result["overall_valid"] is False
    
    def test_password_is_hashed(self):
        """Test that password is properly hashed in storage."""
        storage = InMemoryUserStorage()
        registration = UserRegistration(storage)
        email = "user@example.com"
        password = "MyPassword123!"
        
        result = registration.register_user(email, password)
        
        # Get user from storage
        user = storage.get_user_by_email(email)
        
        assert user is not None
        assert user.hashed_password != password
        assert len(user.hashed_password) > 0
