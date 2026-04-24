"""
Authentication module for user management.

This module provides user authentication, registration, and profile update functionality.
"""

from .update_user import (
    UserUpdateService,
    UserUpdateError,
    ValidationError,
    AuthenticationError,
    UserNotFoundError,
    validate_email,
    validate_username,
    verify_token,
)
from .user_repository import InMemoryUserRepository

__all__ = [
    "UserUpdateService",
    "UserUpdateError",
    "ValidationError",
    "AuthenticationError",
    "UserNotFoundError",
    "validate_email",
    "validate_username",
    "verify_token",
    "InMemoryUserRepository",
]
