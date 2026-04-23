"""
User profile viewing module.

This module provides functionality to view user profile details.
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)


class UserProfileError(Exception):
    """Base exception for user profile operations."""
    pass


class UserNotFoundError(UserProfileError):
    """Exception raised when user is not found."""
    pass


class DatabaseConnectionError(UserProfileError):
    """Exception raised when database connection fails."""
    pass


class UserProfile:
    """
    Handle user profile viewing operations.
    
    This class manages retrieval and display of user profile information
    from the database.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize UserProfile with database connection.
        
        Args:
            database_url: PostgreSQL connection string. 
                         If None, reads from DATABASE_URL environment variable.
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise DatabaseConnectionError(
                "DATABASE_URL not provided and not found in environment variables"
            )
    
    def _get_connection(self):
        """
        Get database connection.
        
        Returns:
            psycopg2 connection object.
            
        Raises:
            DatabaseConnectionError: If connection fails.
        """
        try:
            return psycopg2.connect(self.database_url)
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise DatabaseConnectionError(f"Failed to connect to database: {e}")
    
    def get_profile_by_id(self, user_id: int) -> Dict[str, Any]:
        """
        Retrieve user profile by user ID.
        
        Args:
            user_id: The unique identifier of the user.
            
        Returns:
            Dictionary containing user profile information.
            
        Raises:
            UserNotFoundError: If user with given ID doesn't exist.
            DatabaseConnectionError: If database operation fails.
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        """
                        SELECT 
                            id,
                            username,
                            email,
                            full_name,
                            bio,
                            avatar_url,
                            created_at,
                            updated_at,
                            last_login
                        FROM users
                        WHERE id = %s
                        """,
                        (user_id,)
                    )
                    user = cursor.fetchone()
                    
                    if not user:
                        raise UserNotFoundError(f"User with ID {user_id} not found")
                    
                    return dict(user)
        except psycopg2.Error as e:
            logger.error(f"Database query failed: {e}")
            raise DatabaseConnectionError(f"Failed to retrieve user profile: {e}")
    
    def get_profile_by_username(self, username: str) -> Dict[str, Any]:
        """
        Retrieve user profile by username.
        
        Args:
            username: The username of the user.
            
        Returns:
            Dictionary containing user profile information.
            
        Raises:
            UserNotFoundError: If user with given username doesn't exist.
            DatabaseConnectionError: If database operation fails.
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        """
                        SELECT 
                            id,
                            username,
                            email,
                            full_name,
                            bio,
                            avatar_url,
                            created_at,
                            updated_at,
                            last_login
                        FROM users
                        WHERE username = %s
                        """,
                        (username,)
                    )
                    user = cursor.fetchone()
                    
                    if not user:
                        raise UserNotFoundError(f"User with username '{username}' not found")
                    
                    return dict(user)
        except psycopg2.Error as e:
            logger.error(f"Database query failed: {e}")
            raise DatabaseConnectionError(f"Failed to retrieve user profile: {e}")
    
    def get_public_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Retrieve public user profile information (excludes sensitive data like email).
        
        Args:
            user_id: The unique identifier of the user.
            
        Returns:
            Dictionary containing public user profile information.
            
        Raises:
            UserNotFoundError: If user with given ID doesn't exist.
            DatabaseConnectionError: If database operation fails.
        """
        profile = self.get_profile_by_id(user_id)
        
        # Remove sensitive information for public view
        public_fields = ['id', 'username', 'full_name', 'bio', 'avatar_url', 'created_at']
        return {key: profile[key] for key in public_fields if key in profile}
    
    def format_profile_display(self, profile: Dict[str, Any]) -> str:
        """
        Format user profile for display.
        
        Args:
            profile: Dictionary containing user profile data.
            
        Returns:
            Formatted string representation of the profile.
        """
        lines = [
            "=" * 50,
            "USER PROFILE",
            "=" * 50,
            f"ID: {profile.get('id', 'N/A')}",
            f"Username: {profile.get('username', 'N/A')}",
            f"Email: {profile.get('email', 'N/A')}",
            f"Full Name: {profile.get('full_name', 'N/A')}",
            f"Bio: {profile.get('bio', 'N/A')}",
            f"Avatar URL: {profile.get('avatar_url', 'N/A')}",
            f"Created: {profile.get('created_at', 'N/A')}",
            f"Last Updated: {profile.get('updated_at', 'N/A')}",
            f"Last Login: {profile.get('last_login', 'N/A')}",
            "=" * 50
        ]
        return "\n".join(lines)
