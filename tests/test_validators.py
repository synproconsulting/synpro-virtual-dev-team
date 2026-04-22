"""
Unit tests for email and password validators.
"""
import pytest
from src.auth.validators import EmailValidator, PasswordValidator


class TestEmailValidator:
    """Test cases for EmailValidator."""
    
    def test_valid_email(self):
        """Test validation of valid email addresses."""
        valid_emails = [
            "user@example.com",
            "test.user@example.com",
            "user+tag@example.co.uk",
            "firstname.lastname@company.org",
            "user123@test-domain.com",
        ]
        
        for email in valid_emails:
            is_valid, error = EmailValidator.validate(email)
            assert is_valid is True, f"Email {email} should be valid"
            assert error == ""
    
    def test_invalid_email_format(self):
        """Test validation of invalid email formats."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
            "user@example",
            "user..name@example.com",
        ]
        
        for email in invalid_emails:
            is_valid, error = EmailValidator.validate(email)
            assert is_valid is False, f"Email {email} should be invalid"
            assert error != ""
    
    def test_empty_email(self):
        """Test validation of empty email."""
        is_valid, error = EmailValidator.validate("")
        assert is_valid is False
        assert "required" in error.lower()
    
    def test_email_too_long(self):
        """Test validation of overly long email."""
        long_email = "a" * 250 + "@test.com"
        is_valid, error = EmailValidator.validate(long_email)
        assert is_valid is False
        assert "too long" in error.lower()
    
    def test_email_with_whitespace(self):
        """Test that emails with whitespace are handled."""
        is_valid, error = EmailValidator.validate("  user@example.com  ")
        assert is_valid is True
        assert error == ""
    
    def test_non_string_email(self):
        """Test validation rejects non-string input."""
        is_valid, error = EmailValidator.validate(12345)
        assert is_valid is False
        assert "string" in error.lower()


class TestPasswordValidator:
    """Test cases for PasswordValidator."""
    
    def test_valid_password(self):
        """Test validation of valid passwords."""
        valid_passwords = [
            "Password123!",
            "Str0ng@Pass",
            "C0mpl3x!ty",
            "MyP@ssw0rd",
            "Secure#123",
        ]
        
        for password in valid_passwords:
            is_valid, error = PasswordValidator.validate(password)
            assert is_valid is True, f"Password should be valid"
            assert error == ""
    
    def test_password_too_short(self):
        """Test validation of too short password."""
        is_valid, error = PasswordValidator.validate("Short1!")
        assert is_valid is False
        assert "at least" in error.lower()
    
    def test_password_too_long(self):
        """Test validation of too long password."""
        long_password = "A1!" + "a" * 130
        is_valid, error = PasswordValidator.validate(long_password)
        assert is_valid is False
        assert "exceed" in error.lower()
    
    def test_password_missing_uppercase(self):
        """Test validation of password without uppercase."""
        is_valid, error = PasswordValidator.validate("password123!")
        assert is_valid is False
        assert "uppercase" in error.lower()
    
    def test_password_missing_lowercase(self):
        """Test validation of password without lowercase."""
        is_valid, error = PasswordValidator.validate("PASSWORD123!")
        assert is_valid is False
        assert "lowercase" in error.lower()
    
    def test_password_missing_digit(self):
        """Test validation of password without digit."""
        is_valid, error = PasswordValidator.validate("Password!")
        assert is_valid is False
        assert "digit" in error.lower()
    
    def test_password_missing_special_char(self):
        """Test validation of password without special character."""
        is_valid, error = PasswordValidator.validate("Password123")
        assert is_valid is False
        assert "special character" in error.lower()
    
    def test_empty_password(self):
        """Test validation of empty password."""
        is_valid, error = PasswordValidator.validate("")
        assert is_valid is False
        assert "required" in error.lower()
    
    def test_non_string_password(self):
        """Test validation rejects non-string input."""
        is_valid, error = PasswordValidator.validate(12345)
        assert is_valid is False
        assert "string" in error.lower()
