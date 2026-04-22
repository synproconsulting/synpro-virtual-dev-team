"""
User data models for authentication.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class User:
    """
    User model representing a registered user.
    
    Attributes:
        id: Unique user identifier
        email: User's email address
        password_hash: Hashed password (never store plaintext)
        created_at: Timestamp of user creation
        is_active: Whether the user account is active
        is_verified: Whether the email has been verified
    """
    
    email: str
    password_hash: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    is_verified: bool = False
    
    def to_dict(self) -> dict:
        """
        Convert user to dictionary representation.
        
        Returns:
            Dictionary with user data (excludes password_hash)
        """
        return {
            "id": self.id,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
            "is_verified": self.is_verified,
        }
