"""
Notification service package.

Provides email notification capabilities and extensible notification service.
"""

from .service import NotificationService
from .email_provider import EmailProvider, SMTPEmailProvider
from .models import EmailMessage, NotificationStatus

__all__ = [
    "NotificationService",
    "EmailProvider",
    "SMTPEmailProvider",
    "EmailMessage",
    "NotificationStatus",
]
