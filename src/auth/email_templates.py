"""Email templates for authentication-related notifications."""

from typing import Optional

from src.auth.notification_service import Notification, NotificationType


class EmailTemplates:
    """Factory for creating email notifications from templates."""

    @staticmethod
    def welcome_email(recipient: str, username: str) -> Notification:
        """Create a welcome email notification.

        Args:
            recipient: Email address of the recipient
            username: Username of the new user

        Returns:
            Notification object with welcome email content
        """
        subject = "Welcome to Our Service!"
        body = f"""Hello {username},

Welcome to our service! We're excited to have you on board.

If you have any questions, feel free to reach out to our support team.

Best regards,
The Team"""
        html_body = f"""<html>
<body>
<h1>Hello {username},</h1>
<p>Welcome to our service! We're excited to have you on board.</p>
<p>If you have any questions, feel free to reach out to our support team.</p>
<p>Best regards,<br>The Team</p>
</body>
</html>"""
        return Notification(
            recipient=recipient,
            subject=subject,
            body=body,
            html_body=html_body,
            notification_type=NotificationType.EMAIL,
        )

    @staticmethod
    def password_reset_email(
        recipient: str, username: str, reset_token: str, reset_url: str
    ) -> Notification:
        """Create a password reset email notification.

        Args:
            recipient: Email address of the recipient
            username: Username of the user
            reset_token: Password reset token
            reset_url: Base URL for password reset

        Returns:
            Notification object with password reset email content
        """
        reset_link = f"{reset_url}?token={reset_token}"
        subject = "Password Reset Request"
        body = f"""Hello {username},

We received a request to reset your password. Click the link below to reset it:

{reset_link}

If you didn't request this, please ignore this email.

This link will expire in 24 hours.

Best regards,
The Team"""
        html_body = f"""<html>
<body>
<h1>Hello {username},</h1>
<p>We received a request to reset your password.</p>
<p><a href="{reset_link}">Click here to reset your password</a></p>
<p>If you didn't request this, please ignore this email.</p>
<p><em>This link will expire in 24 hours.</em></p>
<p>Best regards,<br>The Team</p>
</body>
</html>"""
        return Notification(
            recipient=recipient,
            subject=subject,
            body=body,
            html_body=html_body,
            notification_type=NotificationType.EMAIL,
            metadata={"reset_token": reset_token},
        )

    @staticmethod
    def verification_email(
        recipient: str, username: str, verification_token: str, verification_url: str
    ) -> Notification:
        """Create an email verification notification.

        Args:
            recipient: Email address of the recipient
            username: Username of the user
            verification_token: Email verification token
            verification_url: Base URL for email verification

        Returns:
            Notification object with verification email content
        """
        verify_link = f"{verification_url}?token={verification_token}"
        subject = "Verify Your Email Address"
        body = f"""Hello {username},

Please verify your email address by clicking the link below:

{verify_link}

If you didn't create an account, please ignore this email.

Best regards,
The Team"""
        html_body = f"""<html>
<body>
<h1>Hello {username},</h1>
<p>Please verify your email address by clicking the button below:</p>
<p><a href="{verify_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
<p>If you didn't create an account, please ignore this email.</p>
<p>Best regards,<br>The Team</p>
</body>
</html>"""
        return Notification(
            recipient=recipient,
            subject=subject,
            body=body,
            html_body=html_body,
            notification_type=NotificationType.EMAIL,
            metadata={"verification_token": verification_token},
        )
