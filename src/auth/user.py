"""
User model for authentication system.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """
    Represents a user in the authentication system.
    
    Attributes:
        user_id: Unique identifier for the user
        email: User's email address
        password_hash: Hashed password
        created_at: Timestamp when the user was created
        last_login: Timestamp of the last login (optional)
    """
    
    user_id: str
    email: str
    password_hash: str
    created_at: datetime
    last_login: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        """Validate user data after initialization."""
        if not self.email or "@" not in self.email:
            raise ValueError("Invalid email address")
        if not self.password_hash:
            raise ValueError("Password hash cannot be empty")
        if not self.user_id:
            raise ValueError("User ID cannot be empty")
