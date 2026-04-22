"""
Tests for email and password validators.
"""

import pytest
from src.auth.validators import validate_email, validate_password


class TestEmailValidation:
    """Test cases for email validation."""
    
    def test_valid_email(self):
        """Test that valid email addresses are accepted."""
        valid_emails = [
            "user@example.com",
            "john.doe@company.co.uk",
            "test+tag@domain.org",
            "first_last@subdomain.example.com",
            "123@numbers.com",
        ]
        
        for email in valid_emails:
            is_valid, error = validate_email(email)
            assert is_valid, f"Email {email} should be valid but got error: {error}"
            assert error == ""
    
    def test_empty_email(self):
        """Test that empty email is rejected."""
        is_valid, error = validate_email("")
        assert not is_valid
        assert error == "Email is required"
    
    def test_invalid_email_format(self):
        """Test that invalid email formats are rejected."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
            "user@example",
            "user..name@example.com",
            ".user@example.com",
            "user.@example.com",
        ]
        
        for email in invalid_emails:
            is_valid, error = validate_email(email)
            assert not is_valid, f"Email {email} should be invalid"
            assert error != ""
    
    def test_email_too_long(self):
        """Test that emails exceeding max length are rejected."""
        long_email = "a" * 310 + "@example.com"
        is_valid, error = validate_email(long_email)
        assert not is_valid
        assert "too long" in error.lower()
    
    def test_local_part_too_long(self):
        """Test that local part exceeding 64 chars is rejected."""
        long_local = "a" * 65 + "@example.com"
        is_valid, error = validate_email(long_local)
        assert not is_valid
        assert "local part" in error.lower()


class TestPasswordValidation:
    """Test cases for password validation."""
    
    def test_valid_password(self):
        """Test that valid passwords are accepted."""
        valid_passwords = [
            "Password123!",
            "MyP@ssw0rd",
            "Str0ng!Pass",
            "C0mplex#Password",
        ]
        
        for password in valid_passwords:
            is_valid, error = validate_password(password)
            assert is_valid, f"Password should be valid but got error: {error}"
            assert error == ""
    
    def test_empty_password(self):
        """Test that empty password is rejected."""
        is_valid, error = validate_password("")
        assert not is_valid
        assert error == "Password is required"
    
    def test_password_too_short(self):
        """Test that passwords shorter than 8 chars are rejected."""
        is_valid, error = validate_password("Pass1!")
        assert not is_valid
        assert "at least 8 characters" in error
    
    def test_password_too_long(self):
        """Test that passwords longer than 128 chars are rejected."""
        long_password = "A1!" + "a" * 126
        is_valid, error = validate_password(long_password)
        assert not is_valid
        assert "too long" in error.lower()
    
    def test_password_no_uppercase(self):
        """Test that password without uppercase is rejected."""
        is_valid, error = validate_password("password123!")
        assert not is_valid
        assert "uppercase" in error.lower()
    
    def test_password_no_lowercase(self):
        """Test that password without lowercase is rejected."""
        is_valid, error = validate_password("PASSWORD123!")
        assert not is_valid
        assert "lowercase" in error.lower()
    
    def test_password_no_digit(self):
        """Test that password without digit is rejected."""
        is_valid, error = validate_password("Password!")
        assert not is_valid
        assert "digit" in error.lower()
    
    def test_password_no_special_char(self):
        """Test that password without special character is rejected."""
        is_valid, error = validate_password("Password123")
        assert not is_valid
        assert "special character" in error.lower()
