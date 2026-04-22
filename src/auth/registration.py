"""
User registration module with email and password validation.
"""

import re
import os
from typing import Optional, Dict, Any
from datetime import datetime
from passlib.context import CryptContext


class RegistrationError(Exception):
    """Custom exception for registration errors."""
    pass


class UserRegistration:
    """
    Handles user registration with email and password validation.
    
    Attributes:
        password_context: Passlib context for password hashing
        min_password_length: Minimum required password length
        require_uppercase: Whether password must contain uppercase letters
        require_lowercase: Whether password must contain lowercase letters
        require_digits: Whether password must contain digits
        require_special: Whether password must contain special characters
    """
    
    def __init__(
        self,
        min_password_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digits: bool = True,
        require_special: bool = True
    ):
        """
        Initialize the UserRegistration instance.
        
        Args:
            min_password_length: Minimum password length (default: 8)
            require_uppercase: Require uppercase letters (default: True)
            require_lowercase: Require lowercase letters (default: True)
            require_digits: Require digits (default: True)
            require_special: Require special characters (default: True)
        """
        self.password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.min_password_length = min_password_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
        
        # Email regex pattern (RFC 5322 simplified)
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
    
    def validate_email(self, email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email is valid
            
        Raises:
            RegistrationError: If email format is invalid
        """
        if not email:
            raise RegistrationError("Email is required")
        
        if not isinstance(email, str):
            raise RegistrationError("Email must be a string")
        
        email = email.strip()
        
        if len(email) > 254:  # RFC 5321
            raise RegistrationError("Email address is too long")
        
        if not self.email_pattern.match(email):
            raise RegistrationError("Invalid email format")
        
        return True
    
    def validate_password(self, password: str) -> bool:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            True if password meets requirements
            
        Raises:
            RegistrationError: If password does not meet requirements
        """
        if not password:
            raise RegistrationError("Password is required")
        
        if not isinstance(password, str):
            raise RegistrationError("Password must be a string")
        
        if len(password) < self.min_password_length:
            raise RegistrationError(
                f"Password must be at least {self.min_password_length} characters long"
            )
        
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            raise RegistrationError("Password must contain at least one uppercase letter")
        
        if self.require_lowercase and not re.search(r'[a-z]', password):
            raise RegistrationError("Password must contain at least one lowercase letter")
        
        if self.require_digits and not re.search(r'\d', password):
            raise RegistrationError("Password must contain at least one digit")
        
        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise RegistrationError(
                "Password must contain at least one special character"
            )
        
        return True
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return self.password_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password to verify against
            
        Returns:
            True if password matches hash
        """
        return self.password_context.verify(plain_password, hashed_password)
    
    def register_user(
        self,
        email: str,
        password: str,
        confirm_password: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register a new user with email and password validation.
        
        Args:
            email: User's email address
            password: User's password
            confirm_password: Password confirmation (optional)
            additional_data: Additional user data (optional)
            
        Returns:
            Dictionary containing user registration data
            
        Raises:
            RegistrationError: If validation fails
        """
        # Validate email
        self.validate_email(email)
        
        # Validate password
        self.validate_password(password)
        
        # Check password confirmation if provided
        if confirm_password is not None and password != confirm_password:
            raise RegistrationError("Passwords do not match")
        
        # Hash the password
        hashed_password = self.hash_password(password)
        
        # Prepare user data
        user_data = {
            "email": email.strip().lower(),
            "password_hash": hashed_password,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        # Add additional data if provided
        if additional_data:
            user_data.update(additional_data)
        
        return user_data
