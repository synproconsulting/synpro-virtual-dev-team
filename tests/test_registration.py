"""
Unit tests for user registration functionality.
"""
import pytest
from src.auth.registration import UserRegistration, RegistrationError
from src.auth.storage import UserStorage
from src.auth.password_hasher import PasswordHasher


class TestUserRegistration:
    """Test cases for UserRegistration."""
    
    def test_register_user_success(self):
        """Test successful user registration."""
        registration = UserRegistration()
        
        success, message, user = registration.register_user(
            "test@example.com",
            "Password123!"
        )
        
        assert success is True
        assert "success" in message.lower()
        assert user is not None
        assert user.email == "test@example.com"
    
    def test_register_user_invalid_email(self):
        """Test registration with invalid email."""
        registration = UserRegistration()
        
        success, message, user = registration.register_user(
            "invalid-email",
            "Password123!"
        )
        
        assert success is False
        assert "email" in message.lower()
        assert user is None
    
    def test_register_user_invalid_password(self):
        """Test registration with invalid password."""
        registration = UserRegistration()
        
        success, message, user = registration.register_user(
            "test@example.com",
            "weak"
        )
        
        assert success is False
        assert "password" in message.lower()
        assert user is None
    
    def test_register_user_duplicate_email(self):
        """Test registration with already registered email."""
        registration = UserRegistration()
        
        # First registration
        registration.register_user("test@example.com", "Password123!")
        
        # Attempt duplicate registration
        success, message, user = registration.register_user(
            "test@example.com",
            "DifferentPass123!"
        )
        
        assert success is False
        assert "already registered" in message.lower()
        assert user is None
    
    def test_register_user_email_normalized(self):
        """Test that email is normalized to lowercase."""
        registration = UserRegistration()
        
        success, message, user = registration.register_user(
            "Test@Example.COM",
            "Password123!"
        )
        
        assert success is True
        assert user.email == "test@example.com"
    
    def test_register_user_password_hashed(self):
        """Test that password is hashed, not stored in plaintext."""
        registration = UserRegistration()
        password = "Password123!"
        
        success, message, user = registration.register_user(
            "test@example.com",
            password
        )
        
        assert success is True
        assert user.password_hash != password
        assert len(user.password_hash) > len(password)
    
    def test_register_user_strict_success(self):
        """Test strict registration mode on success."""
        registration = UserRegistration()
        
        user = registration.register_user_strict(
            "test@example.com",
            "Password123!"
        )
        
        assert user is not None
        assert user.email == "test@example.com"
    
    def test_register_user_strict_raises_on_error(self):
        """Test strict registration mode raises exception on error."""
        registration = UserRegistration()
        
        with pytest.raises(RegistrationError):
            registration.register_user_strict(
                "invalid-email",
                "Password123!"
            )
    
    def test_get_user_by_email(self):
        """Test retrieving user by email."""
        registration = UserRegistration()
        
        registration.register_user("test@example.com", "Password123!")
        user = registration.get_user_by_email("test@example.com")
        
        assert user is not None
        assert user.email == "test@example.com"
    
    def test_get_user_by_email_not_found(self):
        """Test retrieving non-existent user by email."""
        registration = UserRegistration()
        
        user = registration.get_user_by_email("notfound@example.com")
        
        assert user is None
    
    def test_verify_credentials_success(self):
        """Test successful credential verification."""
        registration = UserRegistration()
        password = "Password123!"
        
        registration.register_user("test@example.com", password)
        is_valid, user = registration.verify_credentials("test@example.com", password)
        
        assert is_valid is True
        assert user is not None
        assert user.email == "test@example.com"
    
    def test_verify_credentials_wrong_password(self):
        """Test credential verification with wrong password."""
        registration = UserRegistration()
        
        registration.register_user("test@example.com", "Password123!")
        is_valid, user = registration.verify_credentials("test@example.com", "WrongPass123!")
        
        assert is_valid is False
        assert user is None
    
    def test_verify_credentials_nonexistent_user(self):
        """Test credential verification for non-existent user."""
        registration = UserRegistration()
        
        is_valid, user = registration.verify_credentials(
            "notfound@example.com",
            "Password123!"
        )
        
        assert is_valid is False
        assert user is None
    
    def test_multiple_users_registration(self):
        """Test registering multiple users."""
        registration = UserRegistration()
        
        users_data = [
            ("user1@example.com", "Password123!"),
            ("user2@example.com", "Different456@"),
            ("user3@example.com", "Another789#"),
        ]
        
        for email, password in users_data:
            success, _, user = registration.register_user(email, password)
            assert success is True
            assert user.email == email
        
        # Verify all users can be retrieved
        for email, _ in users_data:
            user = registration.get_user_by_email(email)
            assert user is not None
