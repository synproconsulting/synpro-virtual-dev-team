"""
Unit tests for user registration module.
"""

import pytest
from datetime import datetime
from src.auth.user_registration import (
    UserRegistration,
    PasswordValidationError,
    EmailValidationError,
    UserAlreadyExistsError
)


@pytest.fixture
def registration_service():
    """Fixture to provide a fresh UserRegistration instance for each test."""
    return UserRegistration()


class TestEmailValidation:
    """Test cases for email validation."""
    
    def test_valid_email(self, registration_service):
        """Test that valid email addresses are accepted."""
        valid_emails = [
            "user@example.com",
            "test.user@domain.co.uk",
            "admin+tag@company.org",
            "user123@test-domain.com"
        ]
        
        for email in valid_emails:
            result = registration_service.validate_email(email)
            assert result is not None
            assert "@" in result
    
    def test_invalid_email_format(self, registration_service):
        """Test that invalid email formats are rejected."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
            "",
            "user@.com"
        ]
        
        for email in invalid_emails:
            with pytest.raises(EmailValidationError):
                registration_service.validate_email(email)
    
    def test_email_normalization(self, registration_service):
        """Test that emails are normalized."""
        email = "User@EXAMPLE.COM"
        normalized = registration_service.validate_email(email)
        assert normalized == "user@example.com"
    
    def test_none_email(self, registration_service):
        """Test that None email is rejected."""
        with pytest.raises(EmailValidationError):
            registration_service.validate_email(None)
    
    def test_non_string_email(self, registration_service):
        """Test that non-string email is rejected."""
        with pytest.raises(EmailValidationError):
            registration_service.validate_email(12345)


class TestPasswordValidation:
    """Test cases for password validation."""
    
    def test_valid_password(self, registration_service):
        """Test that valid passwords are accepted."""
        valid_passwords = [
            "Password123!",
            "MyP@ssw0rd",
            "Secure#Pass1",
            "Test1234!@#$"
        ]
        
        for password in valid_passwords:
            registration_service.validate_password(password)  # Should not raise
    
    def test_password_too_short(self, registration_service):
        """Test that short passwords are rejected."""
        with pytest.raises(PasswordValidationError, match="at least 8 characters"):
            registration_service.validate_password("Pass1!")
    
    def test_password_too_long(self, registration_service):
        """Test that excessively long passwords are rejected."""
        long_password = "A1a!" + ("x" * 125)
        with pytest.raises(PasswordValidationError, match="must not exceed"):
            registration_service.validate_password(long_password)
    
    def test_password_no_uppercase(self, registration_service):
        """Test that passwords without uppercase are rejected."""
        with pytest.raises(PasswordValidationError, match="uppercase letter"):
            registration_service.validate_password("password123!")
    
    def test_password_no_lowercase(self, registration_service):
        """Test that passwords without lowercase are rejected."""
        with pytest.raises(PasswordValidationError, match="lowercase letter"):
            registration_service.validate_password("PASSWORD123!")
    
    def test_password_no_digit(self, registration_service):
        """Test that passwords without digits are rejected."""
        with pytest.raises(PasswordValidationError, match="digit"):
            registration_service.validate_password("Password!")
    
    def test_password_no_special_char(self, registration_service):
        """Test that passwords without special characters are rejected."""
        with pytest.raises(PasswordValidationError, match="special character"):
            registration_service.validate_password("Password123")
    
    def test_empty_password(self, registration_service):
        """Test that empty password is rejected."""
        with pytest.raises(PasswordValidationError):
            registration_service.validate_password("")
    
    def test_none_password(self, registration_service):
        """Test that None password is rejected."""
        with pytest.raises(PasswordValidationError):
            registration_service.validate_password(None)


class TestPasswordHashing:
    """Test cases for password hashing and verification."""
    
    def test_password_hashing(self, registration_service):
        """Test that passwords are hashed correctly."""
        password = "SecurePass123!"
        hashed = registration_service.hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
    
    def test_password_verification_success(self, registration_service):
        """Test successful password verification."""
        password = "SecurePass123!"
        hashed = registration_service.hash_password(password)
        
        assert registration_service.verify_password(password, hashed) is True
    
    def test_password_verification_failure(self, registration_service):
        """Test failed password verification."""
        password = "SecurePass123!"
        hashed = registration_service.hash_password(password)
        
        assert registration_service.verify_password("WrongPass123!", hashed) is False
    
    def test_different_hashes_for_same_password(self, registration_service):
        """Test that same password produces different hashes (salt)."""
        password = "SecurePass123!"
        hash1 = registration_service.hash_password(password)
        hash2 = registration_service.hash_password(password)
        
        assert hash1 != hash2
        assert registration_service.verify_password(password, hash1)
        assert registration_service.verify_password(password, hash2)


class TestUserRegistration:
    """Test cases for user registration."""
    
    def test_successful_registration(self, registration_service):
        """Test successful user registration."""
        email = "newuser@example.com"
        password = "SecurePass123!"
        
        user = registration_service.register_user(email, password)
        
        assert user is not None
        assert user['email'] == "newuser@example.com"
        assert user['username'] == "newuser"
        assert user['is_active'] is True
        assert 'created_at' in user
        assert 'password_hash' not in user  # Should not expose hash
    
    def test_registration_with_username(self, registration_service):
        """Test user registration with custom username."""
        email = "user@example.com"
        password = "SecurePass123!"
        username = "custom_user"
        
        user = registration_service.register_user(email, password, username)
        
        assert user['username'] == username
    
    def test_duplicate_user_registration(self, registration_service):
        """Test that duplicate registration is prevented."""
        email = "user@example.com"
        password = "SecurePass123!"
        
        registration_service.register_user(email, password)
        
        with pytest.raises(UserAlreadyExistsError):
            registration_service.register_user(email, password)
    
    def test_registration_with_invalid_email(self, registration_service):
        """Test registration with invalid email."""
        with pytest.raises(EmailValidationError):
            registration_service.register_user("invalid-email", "SecurePass123!")
    
    def test_registration_with_invalid_password(self, registration_service):
        """Test registration with invalid password."""
        with pytest.raises(PasswordValidationError):
            registration_service.register_user("user@example.com", "weak")
    
    def test_get_existing_user(self, registration_service):
        """Test retrieving an existing user."""
        email = "user@example.com"
        password = "SecurePass123!"
        
        registered_user = registration_service.register_user(email, password)
        retrieved_user = registration_service.get_user(email)
        
        assert retrieved_user is not None
        assert retrieved_user['email'] == registered_user['email']
        assert retrieved_user['username'] == registered_user['username']
        assert 'password_hash' not in retrieved_user
    
    def test_get_nonexistent_user(self, registration_service):
        """Test retrieving a non-existent user."""
        user = registration_service.get_user("nonexistent@example.com")
        assert user is None
    
    def test_password_stored_as_hash(self, registration_service):
        """Test that passwords are stored as hashes, not plaintext."""
        email = "user@example.com"
        password = "SecurePass123!"
        
        registration_service.register_user(email, password)
        
        # Access internal store to verify hash
        stored_user = registration_service.user_store[email]
        assert 'password_hash' in stored_user
        assert stored_user['password_hash'] != password
        assert registration_service.verify_password(
            password, 
            stored_user['password_hash']
        )
    
    def test_case_insensitive_email_lookup(self, registration_service):
        """Test that email lookup is case-insensitive."""
        email = "User@Example.COM"
        password = "SecurePass123!"
        
        registration_service.register_user(email, password)
        
        # Try to register with different case
        with pytest.raises(UserAlreadyExistsError):
            registration_service.register_user("user@example.com", password)
        
        # Retrieve with different case
        user = registration_service.get_user("USER@EXAMPLE.COM")
        assert user is not None


class TestUserStore:
    """Test cases for user store functionality."""
    
    def test_custom_user_store(self):
        """Test that custom user store can be provided."""
        custom_store = {}
        registration_service = UserRegistration(user_store=custom_store)
        
        email = "user@example.com"
        password = "SecurePass123!"
        
        registration_service.register_user(email, password)
        
        assert email in custom_store
        assert custom_store[email]['email'] == email
    
    def test_multiple_users_in_store(self, registration_service):
        """Test storing multiple users."""
        users = [
            ("user1@example.com", "Password1!"),
            ("user2@example.com", "Password2!"),
            ("user3@example.com", "Password3!")
        ]
        
        for email, password in users:
            registration_service.register_user(email, password)
        
        assert len(registration_service.user_store) == 3
        
        for email, _ in users:
            assert registration_service.get_user(email) is not None
