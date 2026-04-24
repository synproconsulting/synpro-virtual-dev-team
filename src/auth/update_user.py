"""
User update module for username and email modification.

This module provides functionality to update user username and email
with proper validation and authentication.
"""

import re
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class UserUpdateError(Exception):
    """Base exception for user update errors."""
    pass


class ValidationError(UserUpdateError):
    """Exception raised for validation errors."""
    pass


class AuthenticationError(UserUpdateError):
    """Exception raised for authentication errors."""
    pass


class UserNotFoundError(UserUpdateError):
    """Exception raised when user is not found."""
    pass


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def validate_username(username: str) -> bool:
    """
    Validate username format.
    
    Username must be 3-30 characters, alphanumeric with underscores and hyphens.
    
    Args:
        username: Username to validate
        
    Returns:
        True if username is valid, False otherwise
    """
    if not username or len(username) < 3 or len(username) > 30:
        return False
    username_pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(username_pattern, username))


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token and extract user information.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary containing user information from token payload
        
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Invalid token: missing user ID")
        return payload
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


class UserUpdateService:
    """Service for updating user information."""
    
    def __init__(self, user_repository):
        """
        Initialize the user update service.
        
        Args:
            user_repository: Repository instance for user data persistence
        """
        self.user_repository = user_repository
    
    def update_username(
        self, 
        user_id: int, 
        new_username: str, 
        token: str
    ) -> Dict[str, Any]:
        """
        Update user's username.
        
        Args:
            user_id: ID of the user to update
            new_username: New username to set
            token: JWT authentication token
            
        Returns:
            Dictionary containing updated user information
            
        Raises:
            ValidationError: If username format is invalid
            AuthenticationError: If token is invalid
            UserNotFoundError: If user doesn't exist
            UserUpdateError: If username is already taken
        """
        # Verify authentication
        payload = verify_token(token)
        token_user_id = int(payload.get("sub"))
        
        if token_user_id != user_id:
            raise AuthenticationError("Unauthorized: cannot update other users")
        
        # Validate new username
        if not validate_username(new_username):
            raise ValidationError(
                "Username must be 3-30 characters and contain only "
                "alphanumeric characters, underscores, and hyphens"
            )
        
        # Check if user exists
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Check if username is already taken
        existing_user = self.user_repository.get_by_username(new_username)
        if existing_user and existing_user.get("id") != user_id:
            raise UserUpdateError("Username is already taken")
        
        # Update username
        updated_user = self.user_repository.update_username(user_id, new_username)
        
        return {
            "id": updated_user["id"],
            "username": updated_user["username"],
            "email": updated_user["email"],
            "updated_at": updated_user.get("updated_at", datetime.utcnow().isoformat())
        }
    
    def update_email(
        self, 
        user_id: int, 
        new_email: str, 
        token: str
    ) -> Dict[str, Any]:
        """
        Update user's email address.
        
        Args:
            user_id: ID of the user to update
            new_email: New email address to set
            token: JWT authentication token
            
        Returns:
            Dictionary containing updated user information
            
        Raises:
            ValidationError: If email format is invalid
            AuthenticationError: If token is invalid
            UserNotFoundError: If user doesn't exist
            UserUpdateError: If email is already taken
        """
        # Verify authentication
        payload = verify_token(token)
        token_user_id = int(payload.get("sub"))
        
        if token_user_id != user_id:
            raise AuthenticationError("Unauthorized: cannot update other users")
        
        # Validate new email
        if not validate_email(new_email):
            raise ValidationError("Invalid email format")
        
        # Check if user exists
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Check if email is already taken
        existing_user = self.user_repository.get_by_email(new_email)
        if existing_user and existing_user.get("id") != user_id:
            raise UserUpdateError("Email is already taken")
        
        # Update email
        updated_user = self.user_repository.update_email(user_id, new_email)
        
        return {
            "id": updated_user["id"],
            "username": updated_user["username"],
            "email": updated_user["email"],
            "updated_at": updated_user.get("updated_at", datetime.utcnow().isoformat())
        }
    
    def update_user_profile(
        self,
        user_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None,
        token: str = None
    ) -> Dict[str, Any]:
        """
        Update user profile (username and/or email).
        
        Args:
            user_id: ID of the user to update
            username: New username (optional)
            email: New email address (optional)
            token: JWT authentication token
            
        Returns:
            Dictionary containing updated user information
            
        Raises:
            ValidationError: If any field format is invalid
            AuthenticationError: If token is invalid
            UserNotFoundError: If user doesn't exist
            UserUpdateError: If username or email is already taken
        """
        if not username and not email:
            raise ValidationError("At least one field (username or email) must be provided")
        
        # Verify authentication
        payload = verify_token(token)
        token_user_id = int(payload.get("sub"))
        
        if token_user_id != user_id:
            raise AuthenticationError("Unauthorized: cannot update other users")
        
        # Check if user exists
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Validate and update username if provided
        if username:
            if not validate_username(username):
                raise ValidationError(
                    "Username must be 3-30 characters and contain only "
                    "alphanumeric characters, underscores, and hyphens"
                )
            existing_user = self.user_repository.get_by_username(username)
            if existing_user and existing_user.get("id") != user_id:
                raise UserUpdateError("Username is already taken")
        
        # Validate and update email if provided
        if email:
            if not validate_email(email):
                raise ValidationError("Invalid email format")
            existing_user = self.user_repository.get_by_email(email)
            if existing_user and existing_user.get("id") != user_id:
                raise UserUpdateError("Email is already taken")
        
        # Update user profile
        updated_user = self.user_repository.update_profile(
            user_id, 
            username=username, 
            email=email
        )
        
        return {
            "id": updated_user["id"],
            "username": updated_user["username"],
            "email": updated_user["email"],
            "updated_at": updated_user.get("updated_at", datetime.utcnow().isoformat())
        }
