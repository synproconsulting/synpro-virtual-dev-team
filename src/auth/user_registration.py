"""
User registration module with email and password validation.

This module provides functionality for user registration including:
- Email format validation
- Password strength validation
- Secure password hashing
- User data storage
"""

import re
import os
from typing import Dict, Optional, Tuple
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, validator


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordRequirements(BaseModel):
    """Configuration for password validation requirements."""
    
    min_length: int = Field(default=8, ge=1)
    require_uppercase: bool = Field(default=True)
    require_lowercase: bool = Field(default=True)
    require_digit: bool = Field(default=True)
    require_special: bool = Field(default=True)


class UserRegistrationInput(BaseModel):
    """Input model for user registration."""
    
    email: EmailStr
    password: str
    confirm_password: str
    full_name: Optional[str] = None
    
    @validator('confirm_password')
    def passwords_match(cls, v: str, values: Dict) -> str:
        """Validate that password and confirm_password match."""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class User(BaseModel):
    """User model representing a registered user."""
    
    email: EmailStr
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True


class RegistrationError(Exception):
    """Custom exception for registration errors."""
    pass


class UserRegistrationService:
    """Service class for handling user registration logic."""
    
    def __init__(
        self,
        password_requirements: Optional[PasswordRequirements] = None
    ):
        """
        Initialize the registration service.
        
        Args:
            password_requirements: Custom password requirements configuration.
                                 If None, uses default requirements.
        """
        self.password_requirements = password_requirements or PasswordRequirements()
        self.users_db: Dict[str, User] = {}
    
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """
        Validate password against strength requirements.
        
        Args:
            password: The password to validate.
            
        Returns:
            Tuple of (is_valid, error_message). If valid, error_message is empty.
        """
        reqs = self.password_requirements
        
        if len(password) < reqs.min_length:
            return False, f"Password must be at least {reqs.min_length} characters long"
        
        if reqs.require_uppercase and not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if reqs.require_lowercase and not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if reqs.require_digit and not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if reqs.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, ""
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: The plain text password to hash.
            
        Returns:
            The hashed password.
        """
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: The plain text password.
            hashed_password: The hashed password to verify against.
            
        Returns:
            True if password matches, False otherwise.
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def user_exists(self, email: str) -> bool:
        """
        Check if a user with the given email already exists.
        
        Args:
            email: The email address to check.
            
        Returns:
            True if user exists, False otherwise.
        """
        return email.lower() in self.users_db
    
    def register_user(
        self,
        email: str,
        password: str,
        confirm_password: str,
        full_name: Optional[str] = None
    ) -> User:
        """
        Register a new user with email and password validation.
        
        Args:
            email: User's email address.
            password: User's password.
            confirm_password: Password confirmation.
            full_name: Optional full name of the user.
            
        Returns:
            The created User object.
            
        Raises:
            RegistrationError: If validation fails or user already exists.
        """
        # Validate input using Pydantic model
        try:
            user_input = UserRegistrationInput(
                email=email,
                password=password,
                confirm_password=confirm_password,
                full_name=full_name
            )
        except ValueError as e:
            raise RegistrationError(f"Validation error: {str(e)}")
        
        # Check if user already exists
        if self.user_exists(user_input.email):
            raise RegistrationError(f"User with email {user_input.email} already exists")
        
        # Validate password strength
        is_valid, error_message = self.validate_password_strength(user_input.password)
        if not is_valid:
            raise RegistrationError(error_message)
        
        # Hash the password
        hashed_password = self.hash_password(user_input.password)
        
        # Create user object
        user = User(
            email=user_input.email,
            hashed_password=hashed_password,
            full_name=user_input.full_name
        )
        
        # Store user (in-memory for this implementation)
        self.users_db[user.email.lower()] = user
        
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by email address.
        
        Args:
            email: The email address to look up.
            
        Returns:
            User object if found, None otherwise.
        """
        return self.users_db.get(email.lower())
