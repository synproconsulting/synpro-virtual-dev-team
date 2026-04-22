"""
User storage interface and in-memory implementation.
"""

from typing import Dict, Optional
from uuid import uuid4

from src.auth.models import User


class UserStorageInterface:
    """
    Interface for user storage operations.
    """
    
    def save_user(self, user: User) -> User:
        """Save a user to storage."""
        raise NotImplementedError
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email address."""
        raise NotImplementedError
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user by ID."""
        raise NotImplementedError
    
    def email_exists(self, email: str) -> bool:
        """Check if an email is already registered."""
        raise NotImplementedError


class InMemoryUserStorage(UserStorageInterface):
    """
    In-memory implementation of user storage for development/testing.
    
    Note: This is not suitable for production use. In production,
    use a proper database implementation (PostgreSQL, MongoDB, etc.)
    """
    
    def __init__(self) -> None:
        """Initialize in-memory storage."""
        self._users_by_id: Dict[str, User] = {}
        self._users_by_email: Dict[str, User] = {}
    
    def save_user(self, user: User) -> User:
        """
        Save a user to in-memory storage.
        
        Args:
            user: User object to save
            
        Returns:
            Saved user with generated ID
        """
        if not user.user_id:
            user.user_id = str(uuid4())
        
        self._users_by_id[user.user_id] = user
        self._users_by_email[user.email.lower()] = user
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            User object if found, None otherwise
        """
        return self._users_by_email.get(email.lower())
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user by ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            User object if found, None otherwise
        """
        return self._users_by_id.get(user_id)
    
    def email_exists(self, email: str) -> bool:
        """
        Check if an email is already registered.
        
        Args:
            email: Email address to check
            
        Returns:
            True if email exists, False otherwise
        """
        return email.lower() in self._users_by_email
