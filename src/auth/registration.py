"""
User registration module with email and password validation.
"""

import re
import os
from typing import Dict, Optional, Tuple
from passlib.context import CryptContext
from datetime import datetime


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class UserRegistration:
    """
    Handles user registration with email and password validation.
    """

    # Password requirements
    MIN_PASSWORD_LENGTH = int(os.getenv("MIN_PASSWORD_LENGTH", "8"))
    MAX_PASSWORD_LENGTH = int(os.getenv("MAX_PASSWORD_LENGTH", "128"))
    
    # Email validation regex (RFC 5322 simplified)
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    def __init__(self) -> None:
        """Initialize the UserRegistration instance."""
        self.users_db: Dict[str, Dict] = {}

    def validate_email(self, email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email format.

        Args:
            email: Email address to validate

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
        
        if not self.EMAIL_REGEX.match(email):
            return False, "Invalid email format"
        
        if email.lower() in self.users_db:
            return False, "Email already registered"
        
        return True, None

    def validate_password(self, password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength.

        Password must:
        - Be at least MIN_PASSWORD_LENGTH characters
        - Contain at least one uppercase letter
        - Contain at least one lowercase letter
        - Contain at least one digit
        - Contain at least one special character

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"
        
        if not isinstance(password, str):
            return False, "Password must be a string"
        
        if len(password) < self.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters"
        
        if len(password) > self.MAX_PASSWORD_LENGTH:
            return False, f"Password must not exceed {self.MAX_PASSWORD_LENGTH} characters"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/`~;]', password):
            return False, "Password must contain at least one special character"
        
        return True, None

    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return pwd_context.hash(password)

    def verify_password(
        self, 
        plain_password: str, 
        hashed_password: str
    ) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)

    def register(
        self, 
        email: str, 
        password: str,
        additional_data: Optional[Dict] = None
    ) -> Dict:
        """
        Register a new user with email and password.

        Args:
            email: User's email address
            password: User's password
            additional_data: Optional additional user data

        Returns:
            Dictionary containing user information (without password)

        Raises:
            ValidationError: If validation fails
        """
        # Validate email
        email_valid, email_error = self.validate_email(email)
        if not email_valid:
            raise ValidationError(email_error)
        
        # Validate password
        password_valid, password_error = self.validate_password(password)
        if not password_valid:
            raise ValidationError(password_error)
        
        # Hash password
        hashed_password = self.hash_password(password)
        
        # Create user record
        email_lower = email.lower().strip()
        user_data = {
            "email": email_lower,
            "password_hash": hashed_password,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        # Add any additional data
        if additional_data:
            user_data.update(additional_data)
        
        # Store user
        self.users_db[email_lower] = user_data
        
        # Return user data without password hash
        return {
            "email": email_lower,
            "created_at": user_data["created_at"],
            "is_active": user_data["is_active"]
        }

    def get_user(self, email: str) -> Optional[Dict]:
        """
        Retrieve user by email.

        Args:
            email: User's email address

        Returns:
            User data dictionary or None if not found
        """
        return self.users_db.get(email.lower())


def register_user(
    email: str, 
    password: str,
    additional_data: Optional[Dict] = None
) -> Dict:
    """
    Convenience function to register a user.

    Args:
        email: User's email address
        password: User's password
        additional_data: Optional additional user data

    Returns:
        Dictionary containing user information

    Raises:
        ValidationError: If validation fails
    """
    registration = UserRegistration()
    return registration.register(email, password, additional_data)
