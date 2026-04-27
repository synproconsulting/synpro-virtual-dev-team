"""Email provider implementation for notification service."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from src.auth.notification_service import Notification, NotificationProvider


logger = logging.getLogger(__name__)


class EmailConfig:
    """Configuration for email provider."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        use_tls: bool = True,
        use_ssl: bool = False,
    ) -> None:
        """Initialize email configuration.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            from_email: Default sender email address
            use_tls: Whether to use TLS
            use_ssl: Whether to use SSL
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.use_tls = use_tls
        self.use_ssl = use_ssl


class SMTPEmailProvider(NotificationProvider):
    """Email provider using SMTP."""

    def __init__(self, config: EmailConfig) -> None:
        """Initialize the SMTP email provider.

        Args:
            config: Email configuration
        """
        self.config = config

    async def send(self, notification: Notification) -> bool:
        """Send an email notification.

        Args:
            notification: The notification to send

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = notification.subject
            msg["From"] = self.config.from_email
            msg["To"] = notification.recipient

            # Attach plain text body
            msg.attach(MIMEText(notification.body, "plain"))

            # Attach HTML body if provided
            if notification.html_body:
                msg.attach(MIMEText(notification.html_body, "html"))

            # Connect and send
            if self.config.use_ssl:
                server = smtplib.SMTP_SSL(self.config.smtp_host, self.config.smtp_port)
            else:
                server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)

            try:
                if self.config.use_tls and not self.config.use_ssl:
                    server.starttls()

                server.login(self.config.username, self.config.password)
                server.send_message(msg)
                logger.info(f"Email sent successfully to {notification.recipient}")
                return True
            finally:
                server.quit()

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}", exc_info=True)
            return False
