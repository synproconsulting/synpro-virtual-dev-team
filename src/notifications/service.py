"""
Notification service for managing and sending notifications.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from .models import EmailMessage, NotificationStatus, NotificationRecord
from .email_provider import EmailProvider, SMTPEmailProvider

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending notifications via various channels.
    
    Currently supports email notifications with extensible architecture
    for adding more notification types (SMS, push, etc.).
    """
    
    def __init__(self, email_provider: Optional[EmailProvider] = None) -> None:
        """
        Initialize notification service.
        
        Args:
            email_provider: Email provider to use for sending emails.
                           If not provided, uses SMTPEmailProvider with env vars.
        """
        self.email_provider = email_provider or SMTPEmailProvider()
        self.notification_history: List[NotificationRecord] = []
    
    def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        from_email: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False,
        reply_to: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationRecord:
        """
        Send an email notification.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            from_email: Sender email address
            cc: List of CC recipients
            bcc: List of BCC recipients
            html: Whether body is HTML
            reply_to: Reply-to address
            attachments: List of file paths to attach
            metadata: Additional metadata to store with notification
            
        Returns:
            NotificationRecord containing status and details
        """
        notification_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        try:
            # Create email message
            message = EmailMessage(
                to=to,
                subject=subject,
                body=body,
                from_email=from_email,
                cc=cc,
                bcc=bcc,
                html=html,
                reply_to=reply_to,
                attachments=attachments
            )
            
            # Send email
            success = self.email_provider.send_email(message)
            
            # Create notification record
            if success:
                record = NotificationRecord(
                    id=notification_id,
                    notification_type="email",
                    recipient=", ".join(to),
                    status=NotificationStatus.SENT,
                    created_at=created_at,
                    sent_at=datetime.utcnow(),
                    metadata=metadata
                )
                logger.info(f"Email notification {notification_id} sent successfully")
            else:
                record = NotificationRecord(
                    id=notification_id,
                    notification_type="email",
                    recipient=", ".join(to),
                    status=NotificationStatus.FAILED,
                    created_at=created_at,
                    error_message="Failed to send email",
                    metadata=metadata
                )
                logger.error(f"Email notification {notification_id} failed to send")
            
            self.notification_history.append(record)
            return record
            
        except Exception as e:
            error_message = f"Error sending email: {str(e)}"
            logger.error(f"Notification {notification_id}: {error_message}")
            
            record = NotificationRecord(
                id=notification_id,
                notification_type="email",
                recipient=", ".join(to),
                status=NotificationStatus.FAILED,
                created_at=created_at,
                error_message=error_message,
                metadata=metadata
            )
            self.notification_history.append(record)
            return record
    
    def send_welcome_email(
        self,
        to_email: str,
        user_name: str,
        from_email: str
    ) -> NotificationRecord:
        """
        Send a welcome email to a new user.
        
        Args:
            to_email: Recipient email address
            user_name: Name of the user
            from_email: Sender email address
            
        Returns:
            NotificationRecord containing status and details
        """
        subject = "Welcome to Our Platform!"
        body = f"""
        <html>
        <body>
            <h2>Welcome {user_name}!</h2>
            <p>Thank you for joining our platform. We're excited to have you on board.</p>
            <p>If you have any questions, feel free to reach out to our support team.</p>
            <p>Best regards,<br>The Team</p>
        </body>
        </html>
        """
        
        return self.send_email(
            to=[to_email],
            subject=subject,
            body=body,
            from_email=from_email,
            html=True,
            metadata={"type": "welcome", "user_name": user_name}
        )
    
    def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        reset_url: str,
        from_email: str
    ) -> NotificationRecord:
        """
        Send a password reset email.
        
        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            reset_url: Base URL for password reset
            from_email: Sender email address
            
        Returns:
            NotificationRecord containing status and details
        """
        reset_link = f"{reset_url}?token={reset_token}"
        subject = "Password Reset Request"
        body = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You requested to reset your password. Click the link below to proceed:</p>
            <p><a href="{reset_link}">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this, please ignore this email.</p>
            <p>Best regards,<br>The Team</p>
        </body>
        </html>
        """
        
        return self.send_email(
            to=[to_email],
            subject=subject,
            body=body,
            from_email=from_email,
            html=True,
            metadata={"type": "password_reset", "token": reset_token}
        )
    
    def send_verification_email(
        self,
        to_email: str,
        verification_token: str,
        verification_url: str,
        from_email: str
    ) -> NotificationRecord:
        """
        Send an email verification email.
        
        Args:
            to_email: Recipient email address
            verification_token: Email verification token
            verification_url: Base URL for email verification
            from_email: Sender email address
            
        Returns:
            NotificationRecord containing status and details
        """
        verification_link = f"{verification_url}?token={verification_token}"
        subject = "Verify Your Email Address"
        body = f"""
        <html>
        <body>
            <h2>Verify Your Email</h2>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_link}">Verify Email</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account, please ignore this email.</p>
            <p>Best regards,<br>The Team</p>
        </body>
        </html>
        """
        
        return self.send_email(
            to=[to_email],
            subject=subject,
            body=body,
            from_email=from_email,
            html=True,
            metadata={"type": "email_verification", "token": verification_token}
        )
    
    def get_notification_history(
        self,
        notification_type: Optional[str] = None,
        status: Optional[NotificationStatus] = None,
        limit: Optional[int] = None
    ) -> List[NotificationRecord]:
        """
        Get notification history with optional filters.
        
        Args:
            notification_type: Filter by notification type
            status: Filter by status
            limit: Maximum number of records to return
            
        Returns:
            List of NotificationRecord objects
        """
        results = self.notification_history
        
        if notification_type:
            results = [r for r in results if r.notification_type == notification_type]
        
        if status:
            results = [r for r in results if r.status == status]
        
        if limit:
            results = results[-limit:]
        
        return results
    
    def get_notification_by_id(self, notification_id: str) -> Optional[NotificationRecord]:
        """
        Get a specific notification by ID.
        
        Args:
            notification_id: Notification ID
            
        Returns:
            NotificationRecord if found, None otherwise
        """
        for record in self.notification_history:
            if record.id == notification_id:
                return record
        return None
