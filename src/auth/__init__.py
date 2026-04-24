"""Authentication module for user registration and password management."""

from .user_registration import (
    User,
    RegistrationError,
    register_user,
    validate_email,
    validate_password,
    hash_password,
    verify_password,
)

__all__ = [
    "User",
    "RegistrationError",
    "register_user",
    "validate_email",
    "validate_password",
    "hash_password",
    "verify_password",
]
