"""
Authentication module.

This module provides authentication and authorization functionality.
"""

from src.auth.register import UserRegistration, RegistrationError

__all__ = ["UserRegistration", "RegistrationError"]
