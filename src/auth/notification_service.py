"""Notification service for sending emails and other notifications."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications supported by the service."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


@dataclass
class Notification:
    """Represents a notification to be sent."""

    recipient: str
    subject: str
    body: str
    notification_type: NotificationType
    metadata: dict[str, Any] | None = None
    html_body: str | None = None


class NotificationProvider(ABC):
    """Abstract base class for notification providers."""

    @abstractmethod
    async def send(self, notification: Notification) -> bool:
        """Send a notification.

        Args:
            notification: The notification to send

        Returns:
            True if sent successfully, False otherwise
        """
        pass


class NotificationService:
    """Service for sending notifications through various providers."""

    def __init__(self) -> None:
        """Initialize the notification service."""
        self._providers: dict[NotificationType, NotificationProvider] = {}

    def register_provider(
        self, notification_type: NotificationType, provider: NotificationProvider
    ) -> None:
        """Register a notification provider for a specific type.

        Args:
            notification_type: The type of notification
            provider: The provider instance
        """
        self._providers[notification_type] = provider
        logger.info(f"Registered provider for {notification_type.value}")

    async def send_notification(self, notification: Notification) -> bool:
        """Send a notification using the appropriate provider.

        Args:
            notification: The notification to send

        Returns:
            True if sent successfully, False otherwise

        Raises:
            ValueError: If no provider is registered for the notification type
        """
        provider = self._providers.get(notification.notification_type)
        if not provider:
            raise ValueError(
                f"No provider registered for {notification.notification_type.value}"
            )

        try:
            result = await provider.send(notification)
            if result:
                logger.info(
                    f"Notification sent to {notification.recipient} "
                    f"via {notification.notification_type.value}"
                )
            return result
        except Exception as e:
            logger.error(
                f"Failed to send notification to {notification.recipient}: {e}"
            )
            return False

    async def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        html_body: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Convenience method to send an email notification.

        Args:
            recipient: Email address of the recipient
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            metadata: Optional metadata

        Returns:
            True if sent successfully, False otherwise
        """
        notification = Notification(
            recipient=recipient,
            subject=subject,
            body=body,
            notification_type=NotificationType.EMAIL,
            html_body=html_body,
            metadata=metadata,
        )
        return await self.send_notification(notification)
