"""
User repository for data persistence operations.

This module provides a repository pattern implementation for user data management.
"""

from typing import Optional, Dict, Any
from datetime import datetime


class InMemoryUserRepository:
    """
    In-memory implementation of user repository.
    
    This is a simple implementation for demonstration purposes.
    In production, this would connect to a real database.
    """
    
    def __init__(self):
        """Initialize the repository with an empty user store."""
        self.users: Dict[int, Dict[str, Any]] = {}
        self.next_id = 1
    
    def create(self, username: str, email: str, hashed_password: str) -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            username: User's username
            email: User's email address
            hashed_password: Hashed password
            
        Returns:
            Dictionary containing created user information
        """
        user_id = self.next_id
        self.next_id += 1
        
        user = {
            "id": user_id,
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self.users[user_id] = user
        return user
    
    def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            User dictionary if found, None otherwise
        """
        return self.users.get(user_id)
    
    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User dictionary if found, None otherwise
        """
        for user in self.users.values():
            if user["username"] == username:
                return user
        return None
    
    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email.
        
        Args:
            email: Email address to search for
            
        Returns:
            User dictionary if found, None otherwise
        """
        for user in self.users.values():
            if user["email"] == email:
                return user
        return None
    
    def update_username(self, user_id: int, new_username: str) -> Dict[str, Any]:
        """
        Update user's username.
        
        Args:
            user_id: ID of user to update
            new_username: New username value
            
        Returns:
            Updated user dictionary
            
        Raises:
            ValueError: If user not found
        """
        user = self.users.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        user["username"] = new_username
        user["updated_at"] = datetime.utcnow().isoformat()
        
        return user
    
    def update_email(self, user_id: int, new_email: str) -> Dict[str, Any]:
        """
        Update user's email.
        
        Args:
            user_id: ID of user to update
            new_email: New email value
            
        Returns:
            Updated user dictionary
            
        Raises:
            ValueError: If user not found
        """
        user = self.users.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        user["email"] = new_email
        user["updated_at"] = datetime.utcnow().isoformat()
        
        return user
    
    def update_profile(
        self, 
        user_id: int, 
        username: Optional[str] = None, 
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update user profile fields.
        
        Args:
            user_id: ID of user to update
            username: New username (optional)
            email: New email (optional)
            
        Returns:
            Updated user dictionary
            
        Raises:
            ValueError: If user not found
        """
        user = self.users.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        if username is not None:
            user["username"] = username
        
        if email is not None:
            user["email"] = email
        
        user["updated_at"] = datetime.utcnow().isoformat()
        
        return user
    
    def delete(self, user_id: int) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: ID of user to delete
            
        Returns:
            True if user was deleted, False if not found
        """
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False
    
    def list_all(self) -> list[Dict[str, Any]]:
        """
        List all users.
        
        Returns:
            List of all user dictionaries
        """
        return list(self.users.values())
