"""
User data models for authentication.
"""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class User:
    """
    User model representing a registered user.
    """
    email: str
    hashed_password: str
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    is_verified: bool = False
    
    def to_dict(self) -> dict:
        """
        Convert user object to dictionary.
        
        Returns:
            Dictionary representation of user (excluding password)
        """
        return {
            "user_id": self.user_id,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
            "is_verified": self.is_verified,
        }
