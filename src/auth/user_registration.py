"""User registration module for authentication system.

This module provides functionality for user registration with secure password
hashing and validation.
"""

import re
from typing import Optional
from datetime import datetime
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RegistrationError(Exception):
    """Exception raised for registration validation errors."""
    pass


class User:
    """User model representing a registered user."""
    
    def __init__(
        self,
        username: str,
        email: str,
        hashed_password: str,
        created_at: Optional[datetime] = None
    ):
        """Initialize a User instance.
        
        Args:
            username: The user's unique username
            email: The user's email address
            hashed_password: The hashed password
            created_at: Timestamp of user creation
        """
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.created_at = created_at or datetime.utcnow()
    
    def __repr__(self) -> str:
        return f"User(username='{self.username}', email='{self.email}')"


def validate_email(email: str) -> bool:
    """Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> bool:
    """Validate password strength.
    
    Password must be at least 8 characters long and contain:
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    
    Args:
        password: Password to validate
        
    Returns:
        True if password meets requirements, False otherwise
    """
    if len(password) < 8:
        return False
    
    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_digit = bool(re.search(r'\d', password))
    
    return has_upper and has_lower and has_digit


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to verify against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def register_user(username: str, email: str, password: str) -> User:
    """Register a new user with validation.
    
    Args:
        username: Desired username (3-50 characters)
        email: User's email address
        password: Plain text password
        
    Returns:
        User object with hashed password
        
    Raises:
        RegistrationError: If validation fails
    """
    # Validate username
    if not username or len(username) < 3 or len(username) > 50:
        raise RegistrationError(
            "Username must be between 3 and 50 characters"
        )
    
    # Validate email
    if not validate_email(email):
        raise RegistrationError("Invalid email format")
    
    # Validate password
    if not validate_password(password):
        raise RegistrationError(
            "Password must be at least 8 characters long and contain "
            "uppercase, lowercase, and digit characters"
        )
    
    # Hash password
    hashed_password = hash_password(password)
    
    # Create and return user
    return User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )
