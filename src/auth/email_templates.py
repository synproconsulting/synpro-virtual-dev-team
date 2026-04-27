"""Email templates for authentication-related notifications."""

from typing import Optional

from src.auth.notification_service import NotificationMessage, NotificationType


class EmailTemplates:
    """Pre-defined email templates for authentication flows."""

    @staticmethod
    def welcome_email(
        recipient: str, username: str, sender: Optional[str] = None
    ) -> NotificationMessage:
        """Create a welcome email for new users.

        Args:
            recipient: Email address of the recipient
            username: Username of the new user
            sender: Optional sender email address

        Returns:
            NotificationMessage configured for welcome email
        """
        subject = "Welcome to Our Platform!"
        body = f"""Hello {username},

Welcome to our platform! We're excited to have you on board.

If you have any questions, feel free to reach out to our support team.

Best regards,
The Team"""
        html_body = f"""<html>
<body>
<h2>Hello {username},</h2>
<p>Welcome to our platform! We're excited to have you on board.</p>
<p>If you have any questions, feel free to reach out to our support team.</p>
<p>Best regards,<br>The Team</p>
</body>
</html>"""
        return NotificationMessage(
            recipient=recipient,
            subject=subject,
            body=body,
            html_body=html_body,
            notification_type=NotificationType.EMAIL,
            sender=sender,
        )

    @staticmethod
    def password_reset_email(
        recipient: str, reset_token: str, sender: Optional[str] = None
    ) -> NotificationMessage:
        """Create a password reset email.

        Args:
            recipient: Email address of the recipient
            reset_token: Password reset token
            sender: Optional sender email address

        Returns:
            NotificationMessage configured for password reset
        """
        subject = "Password Reset Request"
        body = f"""Hello,

You requested a password reset. Use the following token to reset your password:

{reset_token}

This token will expire in 1 hour.

If you didn't request this, please ignore this email.

Best regards,
The Team"""
        html_body = f"""<html>
<body>
<h2>Password Reset Request</h2>
<p>You requested a password reset. Use the following token to reset your password:</p>
<p><strong>{reset_token}</strong></p>
<p>This token will expire in 1 hour.</p>
<p>If you didn't request this, please ignore this email.</p>
<p>Best regards,<br>The Team</p>
</body>
</html>"""
        return NotificationMessage(
            recipient=recipient,
            subject=subject,
            body=body,
            html_body=html_body,
            notification_type=NotificationType.EMAIL,
            sender=sender,
        )

    @staticmethod
    def verification_email(
        recipient: str, verification_code: str, sender: Optional[str] = None
    ) -> NotificationMessage:
        """Create an email verification message.

        Args:
            recipient: Email address of the recipient
            verification_code: Verification code
            sender: Optional sender email address

        Returns:
            NotificationMessage configured for email verification
        """
        subject = "Verify Your Email Address"
        body = f"""Hello,

Please verify your email address using the following code:

{verification_code}

This code will expire in 24 hours.

Best regards,
The Team"""
        html_body = f"""<html>
<body>
<h2>Verify Your Email Address</h2>
<p>Please verify your email address using the following code:</p>
<p><strong style="font-size: 24px;">{verification_code}</strong></p>
<p>This code will expire in 24 hours.</p>
<p>Best regards,<br>The Team</p>
</body>
</html>"""
        return NotificationMessage(
            recipient=recipient,
            subject=subject,
            body=body,
            html_body=html_body,
            notification_type=NotificationType.EMAIL,
            sender=sender,
        )
