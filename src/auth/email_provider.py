"""Email provider implementation for notification service."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from src.auth.notification_service import NotificationMessage, NotificationProvider


logger = logging.getLogger(__name__)


class EmailProvider(NotificationProvider):
    """Email provider using SMTP."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True,
        default_sender: Optional[str] = None,
    ) -> None:
        """Initialize the email provider.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP username for authentication
            password: SMTP password for authentication
            use_tls: Whether to use TLS encryption
            default_sender: Default sender email address
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.default_sender = default_sender

    async def send(self, message: NotificationMessage) -> bool:
        """Send an email notification.

        Args:
            message: The notification message to send

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            msg = self._create_email(message)
            self._send_smtp(msg, message.recipient)
            logger.info(f"Email sent to {message.recipient}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}", exc_info=True)
            return False

    def _create_email(self, message: NotificationMessage) -> MIMEMultipart:
        """Create a MIME email message.

        Args:
            message: The notification message

        Returns:
            The MIME message object
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = message.subject
        msg["From"] = message.sender or self.default_sender or "noreply@example.com"
        msg["To"] = message.recipient

        # Add plain text body
        text_part = MIMEText(message.body, "plain")
        msg.attach(text_part)

        # Add HTML body if provided
        if message.html_body:
            html_part = MIMEText(message.html_body, "html")
            msg.attach(html_part)

        return msg

    def _send_smtp(self, msg: MIMEMultipart, recipient: str) -> None:
        """Send email via SMTP.

        Args:
            msg: The MIME message to send
            recipient: The recipient email address

        Raises:
            Exception: If sending fails
        """
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.use_tls:
                server.starttls()
            if self.username and self.password:
                server.login(self.username, self.password)
            server.send_message(msg, to_addrs=[recipient])
