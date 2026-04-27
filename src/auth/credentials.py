"""Credential models and validation."""

from dataclasses import dataclass
from typing import Optional
import re


@dataclass(frozen=True)
class Credentials:
    """User login credentials."""
    
    username: str
    password: str
    
    def __post_init__(self) -> None:
        """Validate credentials on initialization."""
        if not self.username or not self.username.strip():
            raise ValueError("Username cannot be empty")
        if not self.password:
            raise ValueError("Password cannot be empty")
        if len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(self.password) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.match(r"^[a-zA-Z0-9_.-]+$", self.username):
            raise ValueError("Username contains invalid characters")


@dataclass(frozen=True)
class UserRecord:
    """Stored user record with hashed password."""
    
    username: str
    password_hash: str
    salt: str
    is_active: bool = True
    user_id: Optional[str] = None
