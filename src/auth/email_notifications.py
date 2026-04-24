"""Email notification service for account registration events."""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending email notifications for authentication events."""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        use_tls: bool = True,
    ):
        """Initialize the email notification service.

        Args:
            smtp_host: SMTP server hostname (defaults to SMTP_HOST env var)
            smtp_port: SMTP server port (defaults to SMTP_PORT env var or 587)
            smtp_username: SMTP username (defaults to SMTP_USERNAME env var)
            smtp_password: SMTP password (defaults to SMTP_PASSWORD env var)
            from_email: Sender email address (defaults to FROM_EMAIL env var)
            use_tls: Whether to use TLS encryption
        """
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = smtp_username or os.getenv("SMTP_USERNAME", "")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD", "")
        self.from_email = from_email or os.getenv("FROM_EMAIL", "noreply@example.com")
        self.use_tls = use_tls

    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create and configure SMTP connection.

        Returns:
            Configured SMTP connection

        Raises:
            smtplib.SMTPException: If connection fails
        """
        smtp = smtplib.SMTP(self.smtp_host, self.smtp_port)
        if self.use_tls:
            smtp.starttls()
        if self.smtp_username and self.smtp_password:
            smtp.login(self.smtp_username, self.smtp_password)
        return smtp

    def _send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> bool:
        """Send an email message.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body_text: Plain text email body
            body_html: HTML email body (optional)

        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            msg.attach(MIMEText(body_text, "plain"))
            if body_html:
                msg.attach(MIMEText(body_html, "html"))

            with self._create_smtp_connection() as smtp:
                smtp.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_registration_email(
        self,
        user_email: str,
        user_name: str,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send account registration confirmation email.

        Args:
            user_email: User's email address
            user_name: User's display name
            additional_data: Optional additional data to include in email

        Returns:
            True if email was sent successfully, False otherwise
        """
        subject = "Welcome! Your Account Has Been Created"
        
        body_text = f"""Hello {user_name},

Welcome to our platform! Your account has been successfully created.

Email: {user_email}
Registration Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Thank you for joining us!

Best regards,
The Team
"""

        body_html = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .info {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #4CAF50; }}
        .footer {{ text-align: center; padding: 20px; color: #777; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to Our Platform!</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{user_name}</strong>,</p>
            <p>Your account has been successfully created. We're excited to have you on board!</p>
            <div class="info">
                <p><strong>Email:</strong> {user_email}</p>
                <p><strong>Registration Date:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
            <p>Thank you for joining us!</p>
        </div>
        <div class="footer">
            <p>Best regards,<br>The Team</p>
        </div>
    </div>
</body>
</html>
"""

        return self._send_email(user_email, subject, body_text, body_html)

    def send_registration_notification_to_admin(
        self,
        admin_email: str,
        user_email: str,
        user_name: str,
        user_id: Optional[str] = None,
    ) -> bool:
        """Send admin notification about new user registration.

        Args:
            admin_email: Admin email address
            user_email: New user's email address
            user_name: New user's display name
            user_id: New user's ID (optional)

        Returns:
            True if email was sent successfully, False otherwise
        """
        subject = f"New User Registration: {user_name}"
        
        user_id_text = f"\nUser ID: {user_id}" if user_id else ""
        
        body_text = f"""New User Registration Alert

A new user has registered on the platform.

User Details:
Name: {user_name}
Email: {user_email}{user_id_text}
Registration Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

This is an automated notification.
"""

        user_id_html = f"<p><strong>User ID:</strong> {user_id}</p>" if user_id else ""

        body_html = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .info {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #2196F3; }}
        .footer {{ text-align: center; padding: 20px; color: #777; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>New User Registration</h2>
        </div>
        <div class="content">
            <p>A new user has registered on the platform.</p>
            <div class="info">
                <h3>User Details:</h3>
                <p><strong>Name:</strong> {user_name}</p>
                <p><strong>Email:</strong> {user_email}</p>
                {user_id_html}
                <p><strong>Registration Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
        </div>
        <div class="footer">
            <p>This is an automated notification.</p>
        </div>
    </div>
</body>
</html>
"""

        return self._send_email(admin_email, subject, body_text, body_html)
