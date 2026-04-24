"""
Authentication module for user management system.
"""

from .change_password import (
    PasswordChangeRequest,
    PasswordChangeResponse,
    PasswordChangeService,
)

__all__ = [
    "PasswordChangeRequest",
    "PasswordChangeResponse",
    "PasswordChangeService",
]
