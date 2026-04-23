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
            "user_name@example-domain.com",
            "123@example.com",
        ]
        for email in valid_emails:
            is_valid, error = EmailValidator.validate(email)
            assert is_valid, f"Expected {email} to be valid, but got error: {error}"
            assert error == ""

    def test_invalid_email_format(self):
        """Test validation of invalid email formats."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@.com",
            "user..name@example.com",
            "user@domain",
            "",
            "user @example.com",
            "user@exam ple.com",
        ]
        for email in invalid_emails:
            is_valid, error = EmailValidator.validate(email)
            assert not is_valid, f"Expected {email} to be invalid"
            assert error != ""

    def test_empty_email(self):
        """Test validation of empty email."""
        is_valid, error = EmailValidator.validate("")
        assert not is_valid
        assert error == "Email is required"

    def test_email_too_long(self):
        """Test validation of too long email."""
        long_email = "a" * 250 + "@example.com"
        is_valid, error = EmailValidator.validate(long_email)
        assert not is_valid
        assert "too long" in error.lower()

    def test_email_whitespace_trimmed(self):
        """Test that whitespace is handled correctly."""
        is_valid, error = EmailValidator.validate("  user@example.com  ")
        assert is_valid
        assert error == ""


class TestPasswordValidator:
    """Test cases for PasswordValidator."""

    def test_valid_password(self):
        """Test validation of valid passwords."""
        valid_passwords = [
            "Password123!",
            "MyP@ssw0rd",
            "Str0ng!Pass",
            "C0mpl3x@Password",
        ]
        for password in valid_passwords:
            is_valid, error = PasswordValidator.validate(password)
            assert is_valid, f"Expected {password} to be valid, but got error: {error}"
            assert error == ""

    def test_password_too_short(self):
        """Test validation of too short passwords."""
        short_password = "Abc1!"
        is_valid, error = PasswordValidator.validate(short_password)
        assert not is_valid
        assert "at least" in error.lower()

    def test_password_no_uppercase(self):
        """Test validation of password without uppercase letter."""
        password = "password123!"
        is_valid, error = PasswordValidator.validate(password)
        assert not is_valid
        assert "uppercase" in error.lower()

    def test_password_no_lowercase(self):
        """Test validation of password without lowercase letter."""
        password = "PASSWORD123!"
        is_valid, error = PasswordValidator.validate(password)
        assert not is_valid
        assert "lowercase" in error.lower()

    def test_password_no_digit(self):
        """Test validation of password without digit."""
        password = "Password!@#"
        is_valid, error = PasswordValidator.validate(password)
        assert not is_valid
        assert "digit" in error.lower()

    def test_password_no_special_char(self):
        """Test validation of password without special character."""
        password = "Password123"
        is_valid, error = PasswordValidator.validate(password)
        assert not is_valid
        assert "special character" in error.lower()

    def test_empty_password(self):
        """Test validation of empty password."""
        is_valid, error = PasswordValidator.validate("")
        assert not is_valid
        assert error == "Password is required"

    def test_password_too_long(self):
        """Test validation of too long password."""
        long_password = "A1!" + "a" * 130
        is_valid, error = PasswordValidator.validate(long_password)
        assert not is_valid
        assert "at most" in error.lower()

    def test_password_with_various_special_chars(self):
        """Test that various special characters are accepted."""
        special_chars = "!@#$%^&*(),.?\":{}|<>_-+=[]\\\/;`~"
        for char in special_chars:
            password = f"Password123{char}"
            is_valid, error = PasswordValidator.validate(password)
            assert is_valid, f"Expected password with '{char}' to be valid, but got error: {error}"
