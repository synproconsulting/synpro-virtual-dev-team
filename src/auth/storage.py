"""
In-memory storage for user data.

For production use, replace with a proper database implementation.
"""
from typing import Optional, Dict
from src.auth.models import User


class UserStorage:
    """
    In-memory storage for user accounts.
    
    This is a simple implementation for development/testing.
    In production, replace with a proper database (PostgreSQL, MongoDB, etc.).
    """
    
    def __init__(self):
        """Initialize empty user storage."""
        self._users: Dict[str, User] = {}
        self._emails: Dict[str, str] = {}  # email -> user_id mapping
    
    def save_user(self, user: User) -> None:
        """
        Save a user to storage.
        
        Args:
            user: The user object to save
        """
        self._users[user.id] = user
        self._emails[user.email.lower()] = user.id
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user by ID.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            User object if found, None otherwise
        """
        return self._users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by email address.
        
        Args:
            email: The user's email address
            
        Returns:
            User object if found, None otherwise
        """
        user_id = self._emails.get(email.lower())
        if user_id:
            return self._users.get(user_id)
        return None
    
    def email_exists(self, email: str) -> bool:
        """
        Check if an email address is already registered.
        
        Args:
            email: The email address to check
            
        Returns:
            True if email exists, False otherwise
        """
        return email.lower() in self._emails
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user from storage.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            True if user was deleted, False if not found
        """
        user = self._users.get(user_id)
        if user:
            del self._users[user_id]
            del self._emails[user.email.lower()]
            return True
        return False
