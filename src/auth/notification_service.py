"""Notification service for sending emails and other notifications."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications supported."""

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
    html_body: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


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
    """Service for managing and sending notifications."""

    def __init__(self) -> None:
        """Initialize the notification service."""
        self._providers: dict[NotificationType, NotificationProvider] = {}
        self._default_provider: Optional[NotificationProvider] = None

    def register_provider(
        self,
        notification_type: NotificationType,
        provider: NotificationProvider,
        set_as_default: bool = False,
    ) -> None:
        """Register a notification provider.

        Args:
            notification_type: Type of notifications this provider handles
            provider: The provider instance
            set_as_default: Whether to set as default provider
        """
        self._providers[notification_type] = provider
        if set_as_default:
            self._default_provider = provider
        logger.info(f"Registered provider for {notification_type.value}")

    async def send(self, notification: Notification) -> bool:
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
                    f"Notification sent to {notification.recipient} via {notification.notification_type.value}"
                )
            else:
                logger.warning(
                    f"Failed to send notification to {notification.recipient}"
                )
            return result
        except Exception as e:
            logger.error(f"Error sending notification: {e}", exc_info=True)
            return False

    def get_provider(
        self, notification_type: NotificationType
    ) -> Optional[NotificationProvider]:
        """Get a registered provider.

        Args:
            notification_type: The notification type

        Returns:
            The provider if registered, None otherwise
        """
        return self._providers.get(notification_type)
