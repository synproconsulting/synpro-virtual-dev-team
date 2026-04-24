"""
Authentication and user management module.
"""

from .profile import (
    UserProfile,
    UserProfileError,
    UserNotFoundError,
    DatabaseConnectionError
)

__all__ = [
    'UserProfile',
    'UserProfileError',
    'UserNotFoundError',
    'DatabaseConnectionError'
]
