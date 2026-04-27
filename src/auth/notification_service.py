"""Notification service for sending emails and other notifications."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications supported."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


@dataclass
class NotificationMessage:
    """Represents a notification message."""

    recipient: str
    subject: str
    body: str
    notification_type: NotificationType
    sender: Optional[str] = None
    html_body: Optional[str] = None
    attachments: Optional[list[str]] = None


class NotificationProvider(ABC):
    """Abstract base class for notification providers."""

    @abstractmethod
    async def send(self, message: NotificationMessage) -> bool:
        """Send a notification message.

        Args:
            message: The notification message to send

        Returns:
            True if sent successfully, False otherwise
        """
        pass


class NotificationService:
    """Service for managing and sending notifications."""

    def __init__(self) -> None:
        """Initialize the notification service."""
        self._providers: dict[NotificationType, NotificationProvider] = {}

    def register_provider(
        self, notification_type: NotificationType, provider: NotificationProvider
    ) -> None:
        """Register a notification provider.

        Args:
            notification_type: The type of notification this provider handles
            provider: The provider instance
        """
        self._providers[notification_type] = provider
        logger.info(f"Registered provider for {notification_type.value}")

    async def send_notification(self, message: NotificationMessage) -> bool:
        """Send a notification using the appropriate provider.

        Args:
            message: The notification message to send

        Returns:
            True if sent successfully, False otherwise

        Raises:
            ValueError: If no provider is registered for the notification type
        """
        provider = self._providers.get(message.notification_type)
        if not provider:
            raise ValueError(
                f"No provider registered for {message.notification_type.value}"
            )

        try:
            result = await provider.send(message)
            if result:
                logger.info(
                    f"Notification sent to {message.recipient} via {message.notification_type.value}"
                )
            else:
                logger.warning(
                    f"Failed to send notification to {message.recipient}"
                )
            return result
        except Exception as e:
            logger.error(f"Error sending notification: {e}", exc_info=True)
            return False

    def has_provider(self, notification_type: NotificationType) -> bool:
        """Check if a provider is registered for a notification type.

        Args:
            notification_type: The notification type to check

        Returns:
            True if a provider is registered, False otherwise
        """
        return notification_type in self._providers
