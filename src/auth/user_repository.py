"""User storage repository interface."""

from abc import ABC, abstractmethod
from typing import Optional
from src.auth.credentials import UserRecord


class UserRepository(ABC):
    """Abstract interface for user storage operations."""
    
    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[UserRecord]:
        """Retrieve user record by username.
        
        Args:
            username: Username to look up
            
        Returns:
            UserRecord if found, None otherwise
        """
        pass
    
    @abstractmethod
    def save_user(self, user: UserRecord) -> None:
        """Save or update a user record.
        
        Args:
            user: UserRecord to save
        """
        pass


class InMemoryUserRepository(UserRepository):
    """In-memory implementation of UserRepository for testing/development."""
    
    def __init__(self) -> None:
        """Initialize empty user storage."""
        self._users: dict[str, UserRecord] = {}
    
    def get_user_by_username(self, username: str) -> Optional[UserRecord]:
        """Retrieve user record by username.
        
        Args:
            username: Username to look up
            
        Returns:
            UserRecord if found, None otherwise
        """
        return self._users.get(username)
    
    def save_user(self, user: UserRecord) -> None:
        """Save or update a user record.
        
        Args:
            user: UserRecord to save
        """
        self._users[user.username] = user
