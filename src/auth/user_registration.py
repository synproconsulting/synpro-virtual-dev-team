"""
User registration module with email and password validation.

This module provides functionality for user registration with comprehensive
email and password validation, including password hashing using bcrypt.
"""

import re
import os
from typing import Dict, Tuple, Optional
from datetime import datetime
from passlib.context import CryptContext
from email_validator import validate_email, EmailNotValidError


# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordValidationError(Exception):
    """Raised when password validation fails."""
    pass


class EmailValidationError(Exception):
    """Raised when email validation fails."""
    pass


class UserAlreadyExistsError(Exception):
    """Raised when attempting to register a user that already exists."""
    pass


class UserRegistration:
    """
    Handles user registration with email and password validation.
    
    This class provides methods to validate emails, passwords, and register
    new users with secure password hashing.
    """
    
    def __init__(self, user_store: Optional[Dict] = None):
        """
        Initialize the UserRegistration instance.
        
        Args:
            user_store: Optional dictionary to store users. If None, creates new dict.
        """
        self.user_store = user_store if user_store is not None else {}
        self.min_password_length = int(os.getenv('MIN_PASSWORD_LENGTH', '8'))
        self.max_password_length = int(os.getenv('MAX_PASSWORD_LENGTH', '128'))
    
    def validate_email(self, email: str) -> str:
        """
        Validate email address format and deliverability.
        
        Args:
            email: Email address to validate
            
        Returns:
            Normalized email address
            
        Raises:
            EmailValidationError: If email is invalid
        """
        if not email or not isinstance(email, str):
            raise EmailValidationError("Email must be a non-empty string")
        
        try:
            # Validate and normalize email
            email_info = validate_email(email, check_deliverability=False)
            return email_info.normalized
        except EmailNotValidError as e:
            raise EmailValidationError(f"Invalid email address: {str(e)}")
    
    def validate_password(self, password: str) -> None:
        """
        Validate password strength and requirements.
        
        Password must meet the following criteria:
        - Minimum length (default: 8 characters)
        - Maximum length (default: 128 characters)
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one digit
        - Contains at least one special character
        
        Args:
            password: Password to validate
            
        Raises:
            PasswordValidationError: If password doesn't meet requirements
        """
        if not password or not isinstance(password, str):
            raise PasswordValidationError("Password must be a non-empty string")
        
        if len(password) < self.min_password_length:
            raise PasswordValidationError(
                f"Password must be at least {self.min_password_length} characters long"
            )
        
        if len(password) > self.max_password_length:
            raise PasswordValidationError(
                f"Password must not exceed {self.max_password_length} characters"
            )
        
        if not re.search(r'[A-Z]', password):
            raise PasswordValidationError(
                "Password must contain at least one uppercase letter"
            )
        
        if not re.search(r'[a-z]', password):
            raise PasswordValidationError(
                "Password must contain at least one lowercase letter"
            )
        
        if not re.search(r'\d', password):
            raise PasswordValidationError(
                "Password must contain at least one digit"
            )
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/`~;]', password):
            raise PasswordValidationError(
                "Password must contain at least one special character"
            )
    
    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password string
        """
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def register_user(
        self, 
        email: str, 
        password: str, 
        username: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Register a new user with email and password.
        
        Args:
            email: User's email address
            password: User's password (will be hashed)
            username: Optional username
            
        Returns:
            Dictionary containing user information (without password)
            
        Raises:
            EmailValidationError: If email is invalid
            PasswordValidationError: If password doesn't meet requirements
            UserAlreadyExistsError: If user with email already exists
        """
        # Validate email
        normalized_email = self.validate_email(email)
        
        # Check if user already exists
        if normalized_email in self.user_store:
            raise UserAlreadyExistsError(
                f"User with email {normalized_email} already exists"
            )
        
        # Validate password
        self.validate_password(password)
        
        # Hash password
        hashed_password = self.hash_password(password)
        
        # Create user record
        user_data = {
            'email': normalized_email,
            'username': username or normalized_email.split('@')[0],
            'password_hash': hashed_password,
            'created_at': datetime.utcnow().isoformat(),
            'is_active': True
        }
        
        # Store user
        self.user_store[normalized_email] = user_data
        
        # Return user data without password hash
        return {
            'email': user_data['email'],
            'username': user_data['username'],
            'created_at': user_data['created_at'],
            'is_active': user_data['is_active']
        }
    
    def get_user(self, email: str) -> Optional[Dict[str, any]]:
        """
        Retrieve user by email.
        
        Args:
            email: Email address of user to retrieve
            
        Returns:
            User data dictionary without password hash, or None if not found
        """
        try:
            normalized_email = self.validate_email(email)
            user_data = self.user_store.get(normalized_email)
            
            if user_data:
                # Return copy without password hash
                return {
                    'email': user_data['email'],
                    'username': user_data['username'],
                    'created_at': user_data['created_at'],
                    'is_active': user_data['is_active']
                }
            return None
        except EmailValidationError:
            return None
