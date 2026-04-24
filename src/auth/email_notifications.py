"""
Email notification service for authentication events.

Handles sending email notifications for password resets and login alerts.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending authentication-related email notifications."""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
    ):
        """
        Initialize the email notification service.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_username: SMTP authentication username
            smtp_password: SMTP authentication password
            from_email: Email address to send from
        """
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = smtp_username or os.getenv("SMTP_USERNAME", "")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD", "")
        self.from_email = from_email or os.getenv("FROM_EMAIL", "noreply@example.com")

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
    ) -> bool:
        """
        Send an email using SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML version of the email body
            text_content: Plain text version of the email body

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email

            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")

            message.attach(part1)
            message.attach(part2)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.from_email, to_email, message.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        reset_url_base: Optional[str] = None,
    ) -> bool:
        """
        Send a password reset email.

        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            reset_url_base: Base URL for password reset (without token)

        Returns:
            True if email sent successfully, False otherwise
        """
        reset_url_base = reset_url_base or os.getenv(
            "PASSWORD_RESET_URL", "https://example.com/reset-password"
        )
        reset_link = f"{reset_url_base}?token={reset_token}"

        subject = "Password Reset Request"

        text_content = f"""
Hello,

You have requested to reset your password. Please click the link below to reset your password:

{reset_link}

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email.

Best regards,
The Security Team
"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .button {{ 
            display: inline-block; 
            padding: 12px 24px; 
            background-color: #007bff; 
            color: #ffffff; 
            text-decoration: none; 
            border-radius: 4px; 
            margin: 20px 0;
        }}
        .warning {{ color: #856404; background-color: #fff3cd; padding: 10px; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Password Reset Request</h2>
        <p>Hello,</p>
        <p>You have requested to reset your password. Click the button below to reset your password:</p>
        <a href="{reset_link}" class="button">Reset Password</a>
        <p>Or copy and paste this link into your browser:</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <div class="warning">
            <p><strong>Important:</strong> This link will expire in 1 hour.</p>
        </div>
        <p>If you did not request this password reset, please ignore this email.</p>
        <p>Best regards,<br>The Security Team</p>
    </div>
</body>
</html>
"""

        return self._send_email(to_email, subject, html_content, text_content)

    def send_login_alert_email(
        self,
        to_email: str,
        login_time: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        location: Optional[str] = None,
    ) -> bool:
        """
        Send a login alert email.

        Args:
            to_email: Recipient email address
            login_time: Time of login (defaults to now)
            ip_address: IP address of the login
            user_agent: User agent string
            location: Approximate location (city, country)

        Returns:
            True if email sent successfully, False otherwise
        """
        login_time = login_time or datetime.utcnow()
        login_time_str = login_time.strftime("%Y-%m-%d %H:%M:%S UTC")

        subject = "New Login Alert"

        text_content = f"""
Hello,

We detected a new login to your account:

Time: {login_time_str}
IP Address: {ip_address or 'Unknown'}
Location: {location or 'Unknown'}
Device: {user_agent or 'Unknown'}

If this was you, no action is needed.

If you did not perform this login, please:
1. Change your password immediately
2. Review your account activity
3. Contact our support team

Best regards,
The Security Team
"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .alert {{ 
            background-color: #d1ecf1; 
            border: 1px solid #bee5eb; 
            color: #0c5460; 
            padding: 15px; 
            border-radius: 4px; 
            margin: 20px 0;
        }}
        .details {{ 
            background-color: #f8f9fa; 
            padding: 15px; 
            border-radius: 4px; 
            margin: 20px 0;
        }}
        .warning {{ 
            color: #721c24; 
            background-color: #f8d7da; 
            padding: 15px; 
            border-radius: 4px; 
            margin: 20px 0;
        }}
        .detail-row {{ margin: 8px 0; }}
        .detail-label {{ font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>New Login Alert</h2>
        <div class="alert">
            <p><strong>We detected a new login to your account.</strong></p>
        </div>
        
        <div class="details">
            <h3>Login Details</h3>
            <div class="detail-row">
                <span class="detail-label">Time:</span> {login_time_str}
            </div>
            <div class="detail-row">
                <span class="detail-label">IP Address:</span> {ip_address or 'Unknown'}
            </div>
            <div class="detail-row">
                <span class="detail-label">Location:</span> {location or 'Unknown'}
            </div>
            <div class="detail-row">
                <span class="detail-label">Device:</span> {user_agent or 'Unknown'}
            </div>
        </div>
        
        <p>If this was you, no action is needed.</p>
        
        <div class="warning">
            <p><strong>If you did not perform this login:</strong></p>
            <ol>
                <li>Change your password immediately</li>
                <li>Review your account activity</li>
                <li>Contact our support team</li>
            </ol>
        </div>
        
        <p>Best regards,<br>The Security Team</p>
    </div>
</body>
</html>
"""

        return self._send_email(to_email, subject, html_content, text_content)

    def send_password_changed_email(self, to_email: str) -> bool:
        """
        Send a password changed confirmation email.

        Args:
            to_email: Recipient email address

        Returns:
            True if email sent successfully, False otherwise
        """
        subject = "Password Changed Successfully"

        text_content = """
Hello,

Your password has been changed successfully.

If you did not make this change, please contact our support team immediately.

Best regards,
The Security Team
"""

        html_content = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .success { 
            background-color: #d4edda; 
            border: 1px solid #c3e6cb; 
            color: #155724; 
            padding: 15px; 
            border-radius: 4px; 
            margin: 20px 0;
        }
        .warning { 
            color: #721c24; 
            background-color: #f8d7da; 
            padding: 15px; 
            border-radius: 4px; 
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Password Changed</h2>
        <div class="success">
            <p><strong>Your password has been changed successfully.</strong></p>
        </div>
        
        <div class="warning">
            <p>If you did not make this change, please contact our support team immediately.</p>
        </div>
        
        <p>Best regards,<br>The Security Team</p>
    </div>
</body>
</html>
"""

        return self._send_email(to_email, subject, html_content, text_content)
