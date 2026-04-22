"""
User registration service with email and password validation.
"""

from typing import Dict, Any

from src.auth.validators import validate_email, validate_password
from src.auth.password_hasher import hash_password
from src.auth.models import User
from src.auth.storage import UserStorageInterface, InMemoryUserStorage


class RegistrationError(Exception):
    """Exception raised when user registration fails."""
    pass


class UserRegistration:
    """
    Service for handling user registration with validation.
    """
    
    def __init__(self, storage: UserStorageInterface = None) -> None:
        """
        Initialize the registration service.
        
        Args:
            storage: User storage implementation (defaults to in-memory)
        """
        self.storage = storage or InMemoryUserStorage()
    
    def register_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Register a new user with email and password validation.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dictionary containing user information (excluding password)
            
        Raises:
            RegistrationError: If validation fails or email already exists
        """
        # Validate email
        email_valid, email_error = validate_email(email)
        if not email_valid:
            raise RegistrationError(email_error)
        
        # Normalize email to lowercase
        email = email.lower().strip()
        
        # Check if email already exists
        if self.storage.email_exists(email):
            raise RegistrationError("Email address is already registered")
        
        # Validate password
        password_valid, password_error = validate_password(password)
        if not password_valid:
            raise RegistrationError(password_error)
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Create user object
        user = User(
            email=email,
            hashed_password=hashed_password
        )
        
        # Save user
        saved_user = self.storage.save_user(user)
        
        # Return user data (without password)
        return saved_user.to_dict()
    
    def validate_registration_data(self, email: str, password: str) -> Dict[str, Any]:
        """
        Validate registration data without actually registering.
        
        Useful for client-side validation feedback.
        
        Args:
            email: Email address to validate
            password: Password to validate
            
        Returns:
            Dictionary with validation results
        """
        email_valid, email_error = validate_email(email)
        password_valid, password_error = validate_password(password)
        
        email_exists = False
        if email_valid:
            email_exists = self.storage.email_exists(email.lower().strip())
        
        return {
            "email": {
                "valid": email_valid and not email_exists,
                "error": email_error if not email_valid else (
                    "Email already registered" if email_exists else ""
                )
            },
            "password": {
                "valid": password_valid,
                "error": password_error
            },
            "overall_valid": email_valid and password_valid and not email_exists
        }
