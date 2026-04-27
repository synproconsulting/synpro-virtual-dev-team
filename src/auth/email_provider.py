"""Email provider implementations for the notification service."""

import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import aiosmtplib

from src.auth.notification_service import Notification, NotificationProvider

logger = logging.getLogger(__name__)


class SMTPEmailProvider(NotificationProvider):
    """SMTP-based email provider."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = True,
        from_address: str | None = None,
    ) -> None:
        """Initialize the SMTP email provider.

        Args:
            host: SMTP server host (defaults to SMTP_HOST env var)
            port: SMTP server port (defaults to SMTP_PORT env var or 587)
            username: SMTP username (defaults to SMTP_USERNAME env var)
            password: SMTP password (defaults to SMTP_PASSWORD env var)
            use_tls: Whether to use TLS (defaults to True)
            from_address: Sender email address (defaults to SMTP_FROM_ADDRESS env var)
        """
        self.host = host or os.getenv("SMTP_HOST", "localhost")
        self.port = port or int(os.getenv("SMTP_PORT", "587"))
        self.username = username or os.getenv("SMTP_USERNAME")
        self.password = password or os.getenv("SMTP_PASSWORD")
        self.use_tls = use_tls
        self.from_address = from_address or os.getenv(
            "SMTP_FROM_ADDRESS", "noreply@example.com"
        )

    async def send(self, notification: Notification) -> bool:
        """Send an email notification via SMTP.

        Args:
            notification: The notification to send

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            message = self._create_message(notification)
            await self._send_message(message, notification.recipient)
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {notification.recipient}: {e}")
            return False

    def _create_message(self, notification: Notification) -> MIMEMultipart:
        """Create a MIME message from a notification.

        Args:
            notification: The notification to convert

        Returns:
            A MIME multipart message
        """
        message = MIMEMultipart("alternative")
        message["Subject"] = notification.subject
        message["From"] = self.from_address
        message["To"] = notification.recipient

        # Add plain text part
        text_part = MIMEText(notification.body, "plain")
        message.attach(text_part)

        # Add HTML part if provided
        if notification.html_body:
            html_part = MIMEText(notification.html_body, "html")
            message.attach(html_part)

        return message

    async def _send_message(self, message: MIMEMultipart, recipient: str) -> None:
        """Send a MIME message via SMTP.

        Args:
            message: The message to send
            recipient: The recipient email address
        """
        smtp_client = aiosmtplib.SMTP(
            hostname=self.host, port=self.port, use_tls=self.use_tls
        )

        async with smtp_client:
            if self.username and self.password:
                await smtp_client.login(self.username, self.password)
            await smtp_client.send_message(message)

        logger.info(f"Email sent successfully to {recipient}")
