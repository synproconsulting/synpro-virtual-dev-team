"""
Password reset request functionality module.

This module provides functionality for handling password reset requests,
including token generation, email sending, and token validation.
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib


@dataclass
class PasswordResetToken:
    """Data class representing a password reset token."""
    
    token: str
    user_email: str
    created_at: datetime
    expires_at: datetime
    is_used: bool = False
    
    def is_valid(self) -> bool:
        """
        Check if the token is still valid.
        
        Returns:
            bool: True if token is valid and not expired, False otherwise
        """
        return not self.is_used and datetime.utcnow() < self.expires_at


class TokenStorage:
    """In-memory token storage. In production, use a database or Redis."""
    
    def __init__(self):
        self._tokens: Dict[str, PasswordResetToken] = {}
    
    def store(self, token: PasswordResetToken) -> None:
        """Store a password reset token."""
        self._tokens[token.token] = token
    
    def get(self, token: str) -> Optional[PasswordResetToken]:
        """Retrieve a token by its value."""
        return self._tokens.get(token)
    
    def mark_as_used(self, token: str) -> bool:
        """Mark a token as used."""
        if token in self._tokens:
            self._tokens[token].is_used = True
            return True
        return False
    
    def cleanup_expired(self) -> None:
        """Remove expired tokens from storage."""
        now = datetime.utcnow()
        self._tokens = {
            k: v for k, v in self._tokens.items()
            if v.expires_at > now
        }


class EmailService:
    """Service for sending password reset emails."""
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str
    ):
        """
        Initialize email service.
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP authentication username
            smtp_password: SMTP authentication password
            from_email: Email address to send from
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
    
    def send_reset_email(
        self,
        to_email: str,
        reset_token: str,
        reset_url_base: str
    ) -> bool:
        """
        Send password reset email to user.
        
        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            reset_url_base: Base URL for password reset page
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            reset_url = f"{reset_url_base}?token={reset_token}"
            
            message = MIMEMultipart("alternative")
            message["Subject"] = "Password Reset Request"
            message["From"] = self.from_email
            message["To"] = to_email
            
            text_content = f"""
            Hello,
            
            You have requested to reset your password.
            
            Please click the following link to reset your password:
            {reset_url}
            
            This link will expire in 1 hour.
            
            If you did not request this password reset, please ignore this email.
            
            Best regards,
            The Team
            """
            
            html_content = f"""
            <html>
              <body>
                <p>Hello,</p>
                <p>You have requested to reset your password.</p>
                <p>Please click the link below to reset your password:</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                <p>This link will expire in 1 hour.</p>
                <p>If you did not request this password reset, please ignore this email.</p>
                <p>Best regards,<br>The Team</p>
              </body>
            </html>
            """
            
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            
            message.attach(part1)
            message.attach(part2)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)
            
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False


class PasswordResetService:
    """Service for handling password reset requests."""
    
    def __init__(
        self,
        token_storage: TokenStorage,
        email_service: EmailService,
        token_expiry_hours: int = 1
    ):
        """
        Initialize password reset service.
        
        Args:
            token_storage: Storage for reset tokens
            email_service: Service for sending emails
            token_expiry_hours: Hours until token expires (default: 1)
        """
        self.token_storage = token_storage
        self.email_service = email_service
        self.token_expiry_hours = token_expiry_hours
    
    def generate_reset_token(self) -> str:
        """
        Generate a cryptographically secure reset token.
        
        Returns:
            str: Secure random token
        """
        return secrets.token_urlsafe(32)
    
    def request_password_reset(
        self,
        user_email: str,
        reset_url_base: str
    ) -> Dict[str, Any]:
        """
        Create a password reset request and send email.
        
        Args:
            user_email: Email address of the user requesting reset
            reset_url_base: Base URL for the password reset page
            
        Returns:
            dict: Result containing success status and message
        """
        if not user_email or "@" not in user_email:
            return {
                "success": False,
                "message": "Invalid email address"
            }
        
        # Generate token
        token = self.generate_reset_token()
        
        # Create token object
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=self.token_expiry_hours)
        
        reset_token = PasswordResetToken(
            token=token,
            user_email=user_email,
            created_at=now,
            expires_at=expires_at,
            is_used=False
        )
        
        # Store token
        self.token_storage.store(reset_token)
        
        # Send email
        email_sent = self.email_service.send_reset_email(
            to_email=user_email,
            reset_token=token,
            reset_url_base=reset_url_base
        )
        
        if not email_sent:
            return {
                "success": False,
                "message": "Failed to send reset email"
            }
        
        return {
            "success": True,
            "message": "Password reset email sent successfully",
            "token": token  # In production, don't return token in response
        }
    
    def validate_reset_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a password reset token.
        
        Args:
            token: The reset token to validate
            
        Returns:
            dict: Validation result with user email if valid
        """
        reset_token = self.token_storage.get(token)
        
        if not reset_token:
            return {
                "valid": False,
                "message": "Invalid token"
            }
        
        if not reset_token.is_valid():
            return {
                "valid": False,
                "message": "Token has expired or already been used"
            }
        
        return {
            "valid": True,
            "user_email": reset_token.user_email,
            "message": "Token is valid"
        }
    
    def mark_token_used(self, token: str) -> bool:
        """
        Mark a token as used after password reset.
        
        Args:
            token: The token to mark as used
            
        Returns:
            bool: True if marked successfully, False otherwise
        """
        return self.token_storage.mark_as_used(token)


def create_password_reset_service() -> PasswordResetService:
    """
    Factory function to create a configured PasswordResetService.
    
    Returns:
        PasswordResetService: Configured service instance
    """
    # Load configuration from environment variables
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    from_email = os.getenv("FROM_EMAIL", smtp_user)
    token_expiry_hours = int(os.getenv("TOKEN_EXPIRY_HOURS", "1"))
    
    # Create dependencies
    token_storage = TokenStorage()
    email_service = EmailService(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        from_email=from_email
    )
    
    # Create and return service
    return PasswordResetService(
        token_storage=token_storage,
        email_service=email_service,
        token_expiry_hours=token_expiry_hours
    )
