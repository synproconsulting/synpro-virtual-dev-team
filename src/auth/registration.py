"""
User registration functionality with secure password handling.
"""

import os
import hashlib
import secrets
from datetime import datetime
from typing import Dict, Optional
from passlib.hash import bcrypt
from .validators import EmailValidator, PasswordValidator


class RegistrationError(Exception):
    """Custom exception for registration errors."""
    pass


class UserRegistration:
    """
    Handles user registration with email and password validation.
    
    Uses bcrypt for secure password hashing.
    """

    def __init__(self, storage_backend: Optional[object] = None):
        """
        Initialize the registration handler.

        Args:
            storage_backend: Optional storage backend for persisting users.
                           If None, uses in-memory storage (for testing/demo).
        """
        self.storage = storage_backend or InMemoryUserStorage()
        self.email_validator = EmailValidator()
        self.password_validator = PasswordValidator()

    def register_user(
        self,
        email: str,
        password: str,
        confirm_password: str,
        additional_data: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Register a new user with email and password.

        Args:
            email: User's email address
            password: User's password
            confirm_password: Password confirmation
            additional_data: Optional additional user data (e.g., name, phone)

        Returns:
            Dictionary containing user_id and email

        Raises:
            RegistrationError: If validation fails or user already exists
        """
        # Validate email
        email_valid, email_error = self.email_validator.validate(email)
        if not email_valid:
            raise RegistrationError(email_error)

        # Normalize email
        normalized_email = email.strip().lower()

        # Check if user already exists
        if self.storage.user_exists(normalized_email):
            raise RegistrationError("User with this email already exists")

        # Validate password
        password_valid, password_error = self.password_validator.validate(password)
        if not password_valid:
            raise RegistrationError(password_error)

        # Check password confirmation
        if password != confirm_password:
            raise RegistrationError("Passwords do not match")

        # Hash password
        password_hash = self._hash_password(password)

        # Generate user ID
        user_id = self._generate_user_id()

        # Create user data
        user_data = {
            "user_id": user_id,
            "email": normalized_email,
            "password_hash": password_hash,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True,
        }

        if additional_data:
            user_data.update(additional_data)

        # Store user
        self.storage.save_user(user_data)

        # Return user info (without password hash)
        return {
            "user_id": user_id,
            "email": normalized_email,
        }

    def _hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return bcrypt.hash(password)

    def _generate_user_id(self) -> str:
        """
        Generate a unique user ID.

        Returns:
            Unique user ID string
        """
        return secrets.token_hex(16)


class InMemoryUserStorage:
    """
    Simple in-memory storage for users.
    For production, replace with a proper database backend.
    """

    def __init__(self):
        """Initialize empty user storage."""
        self.users: Dict[str, Dict[str, str]] = {}

    def user_exists(self, email: str) -> bool:
        """
        Check if a user with the given email exists.

        Args:
            email: Email to check

        Returns:
            True if user exists, False otherwise
        """
        return email in self.users

    def save_user(self, user_data: Dict[str, str]) -> None:
        """
        Save user data to storage.

        Args:
            user_data: Dictionary containing user information
        """
        email = user_data["email"]
        self.users[email] = user_data

    def get_user(self, email: str) -> Optional[Dict[str, str]]:
        """
        Retrieve user data by email.

        Args:
            email: Email of the user

        Returns:
            User data dictionary or None if not found
        """
        return self.users.get(email)
