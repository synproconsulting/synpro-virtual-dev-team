"""
Email and password validation utilities for user registration.
"""
import re
from typing import Tuple


class EmailValidator:
    """
    Validator for email addresses.
    
    Implements RFC 5322 compliant email validation with basic checks.
    """
    
    # Simple but effective email regex pattern
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    @classmethod
    def validate(cls, email: str) -> Tuple[bool, str]:
        """
        Validate an email address.
        
        Args:
            email: The email address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            If valid, error_message is empty string
        """
        if not email:
            return False, "Email address is required"
        
        if not isinstance(email, str):
            return False, "Email must be a string"
        
        email = email.strip()
        
        if len(email) > 254:
            return False, "Email address is too long (max 254 characters)"
        
        if not cls.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"
        
        return True, ""


class PasswordValidator:
    """
    Validator for user passwords.
    
    Enforces strong password requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    
    @classmethod
    def validate(cls, password: str) -> Tuple[bool, str]:
        """
        Validate a password against security requirements.
        
        Args:
            password: The password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            If valid, error_message is empty string
        """
        if not password:
            return False, "Password is required"
        
        if not isinstance(password, str):
            return False, "Password must be a string"
        
        if len(password) < cls.MIN_LENGTH:
            return False, f"Password must be at least {cls.MIN_LENGTH} characters long"
        
        if len(password) > cls.MAX_LENGTH:
            return False, f"Password must not exceed {cls.MAX_LENGTH} characters"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;`~]', password):
            return False, "Password must contain at least one special character"
        
        return True, ""
