"""
Authentication module for user registration and password management.
"""

from src.auth.registration import UserRegistration, RegistrationError

__all__ = ["UserRegistration", "RegistrationError"]
