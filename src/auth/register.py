"""
User registration module.

This module provides user registration functionality with password hashing,
email validation, and secure storage.
"""

import os
import re
from typing import Dict, Optional
from passlib.context import CryptContext
from datetime import datetime


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RegistrationError(Exception):
    """Custom exception for registration errors."""
    pass


class UserRegistration:
    """
    Handles user registration with validation and secure password storage.
    """

    def __init__(self):
        """Initialize the user registration service."""
        self.users_db: Dict[str, Dict] = {}
        self.min_password_length = int(os.getenv("MIN_PASSWORD_LENGTH", "8"))

    def _validate_email(self, email: str) -> bool:
        """
        Validate email format.

        Args:
            email: Email address to validate

        Returns:
            True if email is valid, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _validate_password(self, password: str) -> bool:
        """
        Validate password strength.

        Args:
            password: Password to validate

        Returns:
            True if password meets requirements, False otherwise
        """
        if len(password) < self.min_password_length:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        return has_upper and has_lower and has_digit

    def _hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return pwd_context.hash(password)

    def register_user(
        self, 
        username: str, 
        email: str, 
        password: str
    ) -> Dict[str, str]:
        """
        Register a new user.

        Args:
            username: Unique username
            email: User's email address
            password: User's password

        Returns:
            Dictionary containing user information (without password)

        Raises:
            RegistrationError: If validation fails or user already exists
        """
        if not username or len(username) < 3:
            raise RegistrationError("Username must be at least 3 characters")

        if username in self.users_db:
            raise RegistrationError("Username already exists")

        if not self._validate_email(email):
            raise RegistrationError("Invalid email format")

        if not self._validate_password(password):
            raise RegistrationError(
                f"Password must be at least {self.min_password_length} characters "
                "and contain uppercase, lowercase, and digit"
            )

        hashed_password = self._hash_password(password)
        
        user_data = {
            "username": username,
            "email": email,
            "password_hash": hashed_password,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        self.users_db[username] = user_data

        return {
            "username": username,
            "email": email,
            "created_at": user_data["created_at"],
            "is_active": user_data["is_active"]
        }

    def user_exists(self, username: str) -> bool:
        """
        Check if a user exists.

        Args:
            username: Username to check

        Returns:
            True if user exists, False otherwise
        """
        return username in self.users_db

    def verify_password(self, username: str, password: str) -> bool:
        """
        Verify a user's password.

        Args:
            username: Username
            password: Plain text password to verify

        Returns:
            True if password is correct, False otherwise
        """
        if username not in self.users_db:
            return False
        
        stored_hash = self.users_db[username]["password_hash"]
        return pwd_context.verify(password, stored_hash)
