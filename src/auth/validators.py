"""
Validation utilities for email and password.
"""

import re
from typing import Tuple


class EmailValidator:
    """Validates email addresses according to standard format."""

    EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    @staticmethod
    def validate(email: str) -> Tuple[bool, str]:
        """
        Validate an email address.

        Args:
            email: The email address to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return False, "Email is required"

        if not isinstance(email, str):
            return False, "Email must be a string"

        email = email.strip()

        if len(email) > 254:
            return False, "Email is too long (max 254 characters)"

        if not re.match(EmailValidator.EMAIL_REGEX, email):
            return False, "Invalid email format"

        return True, ""


class PasswordValidator:
    """Validates passwords according to security requirements."""

    MIN_LENGTH = 8
    MAX_LENGTH = 128

    @staticmethod
    def validate(password: str) -> Tuple[bool, str]:
        """
        Validate a password against security requirements.

        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character

        Args:
            password: The password to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"

        if not isinstance(password, str):
            return False, "Password must be a string"

        if len(password) < PasswordValidator.MIN_LENGTH:
            return False, f"Password must be at least {PasswordValidator.MIN_LENGTH} characters long"

        if len(password) > PasswordValidator.MAX_LENGTH:
            return False, f"Password must be at most {PasswordValidator.MAX_LENGTH} characters long"

        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"

        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;`~]', password):
            return False, "Password must contain at least one special character"

        return True, ""
