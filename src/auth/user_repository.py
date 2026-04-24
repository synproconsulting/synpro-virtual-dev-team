"""
User repository interface for password management.

This module provides an abstract interface and in-memory implementation
for user data operations related to password management.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from datetime import datetime
from threading import Lock


class UserRepositoryInterface(ABC):
    """Abstract interface for user data operations."""
    
    @abstractmethod
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user by ID.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            User dictionary or None if not found
        """
        pass
    
    @abstractmethod
    def update_password(
        self, 
        user_id: str, 
        password_hash: str, 
        changed_at: datetime
    ) -> bool:
        """
        Update user password.
        
        Args:
            user_id: Unique user identifier
            password_hash: New hashed password
            changed_at: Timestamp of password change
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_password_history(
        self, 
        user_id: str, 
        limit: int = 5
    ) -> List[str]:
        """
        Get password history for a user.
        
        Args:
            user_id: Unique user identifier
            limit: Maximum number of historical passwords to return
            
        Returns:
            List of historical password hashes
        """
        pass
    
    @abstractmethod
    def add_to_password_history(
        self, 
        user_id: str, 
        password_hash: str
    ) -> None:
        """
        Add password to user's password history.
        
        Args:
            user_id: Unique user identifier
            password_hash: Hashed password to add to history
        """
        pass


class InMemoryUserRepository(UserRepositoryInterface):
    """In-memory implementation of user repository for testing/development."""
    
    def __init__(self):
        """Initialize the in-memory repository."""
        self._users: Dict[str, Dict[str, Any]] = {}
        self._password_history: Dict[str, List[str]] = {}
        self._lock = Lock()
    
    def create_user(
        self, 
        user_id: str, 
        password_hash: str, 
        email: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            user_id: Unique user identifier
            password_hash: Hashed password
            email: User email address
            **kwargs: Additional user attributes
            
        Returns:
            Created user dictionary
        """
        with self._lock:
            user = {
                "user_id": user_id,
                "email": email,
                "password_hash": password_hash,
                "password_changed_at": datetime.utcnow(),
                "created_at": datetime.utcnow(),
                **kwargs
            }
            self._users[user_id] = user
            self._password_history[user_id] = [password_hash]
            return user.copy()
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user by ID.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            User dictionary or None if not found
        """
        with self._lock:
            user = self._users.get(user_id)
            return user.copy() if user else None
    
    def update_password(
        self, 
        user_id: str, 
        password_hash: str, 
        changed_at: datetime
    ) -> bool:
        """
        Update user password.
        
        Args:
            user_id: Unique user identifier
            password_hash: New hashed password
            changed_at: Timestamp of password change
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if user_id not in self._users:
                return False
            
            self._users[user_id]["password_hash"] = password_hash
            self._users[user_id]["password_changed_at"] = changed_at
            return True
    
    def get_password_history(
        self, 
        user_id: str, 
        limit: int = 5
    ) -> List[str]:
        """
        Get password history for a user.
        
        Args:
            user_id: Unique user identifier
            limit: Maximum number of historical passwords to return
            
        Returns:
            List of historical password hashes
        """
        with self._lock:
            history = self._password_history.get(user_id, [])
            return history[-limit:] if limit > 0 else history
    
    def add_to_password_history(
        self, 
        user_id: str, 
        password_hash: str
    ) -> None:
        """
        Add password to user's password history.
        
        Args:
            user_id: Unique user identifier
            password_hash: Hashed password to add to history
        """
        with self._lock:
            if user_id not in self._password_history:
                self._password_history[user_id] = []
            
            self._password_history[user_id].append(password_hash)
    
    def clear(self) -> None:
        """Clear all data from repository (for testing)."""
        with self._lock:
            self._users.clear()
            self._password_history.clear()
