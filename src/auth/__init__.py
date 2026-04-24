"""
Authentication and authorization module.

This module provides authentication, registration, and notification services.
"""

from src.auth.email_notifications import (
    EmailConfig,
    RegistrationEmailService,
    send_registration_notification,
)

__all__ = [
    "EmailConfig",
    "RegistrationEmailService",
    "send_registration_notification",
]
