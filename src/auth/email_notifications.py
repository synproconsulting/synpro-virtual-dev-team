"""
Email notification service for account registration events.

This module provides functionality to send email notifications when users
register for new accounts. It supports templated emails and uses SMTP for delivery.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailConfig:
    """Configuration for email service."""
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ):
        """
        Initialize email configuration.
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_username: SMTP authentication username
            smtp_password: SMTP authentication password
            from_email: Sender email address
            from_name: Sender display name
        """
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = smtp_username or os.getenv("SMTP_USERNAME", "")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD", "")
        self.from_email = from_email or os.getenv("FROM_EMAIL", "noreply@example.com")
        self.from_name = from_name or os.getenv("FROM_NAME", "Registration Service")


class RegistrationEmailService:
    """Service for sending registration-related email notifications."""
    
    def __init__(self, config: Optional[EmailConfig] = None):
        """
        Initialize the email service.
        
        Args:
            config: Email configuration. If None, uses default from environment.
        """
        self.config = config or EmailConfig()
        
    def _create_connection(self) -> smtplib.SMTP:
        """
        Create and authenticate SMTP connection.
        
        Returns:
            Authenticated SMTP connection
            
        Raises:
            smtplib.SMTPException: If connection or authentication fails
        """
        smtp = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
        smtp.starttls()
        
        if self.config.smtp_username and self.config.smtp_password:
            smtp.login(self.config.smtp_username, self.config.smtp_password)
            
        return smtp
    
    def _generate_welcome_email_html(
        self,
        user_name: str,
        user_email: str,
        registration_date: datetime,
    ) -> str:
        """
        Generate HTML content for welcome email.
        
        Args:
            user_name: Name of the registered user
            user_email: Email of the registered user
            registration_date: Date and time of registration
            
        Returns:
            HTML email content
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Our Platform!</h1>
                </div>
                <div class="content">
                    <h2>Hello {user_name}!</h2>
                    <p>Thank you for registering with us. Your account has been successfully created.</p>
                    <p><strong>Account Details:</strong></p>
                    <ul>
                        <li>Email: {user_email}</li>
                        <li>Registration Date: {registration_date.strftime("%Y-%m-%d %H:%M:%S UTC")}</li>
                    </ul>
                    <p>You can now log in and start using our services.</p>
                    <p>If you did not create this account, please contact our support team immediately.</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} Our Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _generate_welcome_email_text(
        self,
        user_name: str,
        user_email: str,
        registration_date: datetime,
    ) -> str:
        """
        Generate plain text content for welcome email.
        
        Args:
            user_name: Name of the registered user
            user_email: Email of the registered user
            registration_date: Date and time of registration
            
        Returns:
            Plain text email content
        """
        return f"""
Welcome to Our Platform!

Hello {user_name}!

Thank you for registering with us. Your account has been successfully created.

Account Details:
- Email: {user_email}
- Registration Date: {registration_date.strftime("%Y-%m-%d %H:%M:%S UTC")}

You can now log in and start using our services.

If you did not create this account, please contact our support team immediately.

© {datetime.now().year} Our Platform. All rights reserved.
        """.strip()
    
    def send_welcome_email(
        self,
        user_name: str,
        user_email: str,
        registration_date: Optional[datetime] = None,
    ) -> bool:
        """
        Send welcome email to newly registered user.
        
        Args:
            user_name: Name of the registered user
            user_email: Email address of the registered user
            registration_date: Date and time of registration. Defaults to now.
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        if registration_date is None:
            registration_date = datetime.utcnow()
            
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = "Welcome to Our Platform - Registration Successful"
            message["From"] = f"{self.config.from_name} <{self.config.from_email}>"
            message["To"] = user_email
            
            text_content = self._generate_welcome_email_text(
                user_name, user_email, registration_date
            )
            html_content = self._generate_welcome_email_html(
                user_name, user_email, registration_date
            )
            
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            
            message.attach(part1)
            message.attach(part2)
            
            with self._create_connection() as smtp:
                smtp.send_message(message)
                
            logger.info(f"Welcome email sent successfully to {user_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user_email}: {str(e)}")
            return False
    
    def send_admin_notification(
        self,
        user_name: str,
        user_email: str,
        registration_date: datetime,
        admin_email: str,
    ) -> bool:
        """
        Send notification to admin about new user registration.
        
        Args:
            user_name: Name of the registered user
            user_email: Email of the registered user
            registration_date: Date and time of registration
            admin_email: Email address of the administrator
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = f"New User Registration: {user_name}"
            message["From"] = f"{self.config.from_name} <{self.config.from_email}>"
            message["To"] = admin_email
            
            text_content = f"""
New User Registration

A new user has registered on the platform.

User Details:
- Name: {user_name}
- Email: {user_email}
- Registration Date: {registration_date.strftime("%Y-%m-%d %H:%M:%S UTC")}
            """.strip()
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #2196F3; color: white; padding: 20px; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>New User Registration</h2>
                    </div>
                    <div class="content">
                        <p>A new user has registered on the platform.</p>
                        <p><strong>User Details:</strong></p>
                        <ul>
                            <li>Name: {user_name}</li>
                            <li>Email: {user_email}</li>
                            <li>Registration Date: {registration_date.strftime("%Y-%m-%d %H:%M:%S UTC")}</li>
                        </ul>
                    </div>
                </div>
            </body>
            </html>
            """
            
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            
            message.attach(part1)
            message.attach(part2)
            
            with self._create_connection() as smtp:
                smtp.send_message(message)
                
            logger.info(f"Admin notification sent successfully to {admin_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send admin notification to {admin_email}: {str(e)}")
            return False


def send_registration_notification(
    user_name: str,
    user_email: str,
    admin_email: Optional[str] = None,
    registration_date: Optional[datetime] = None,
) -> dict[str, bool]:
    """
    Send all registration-related notifications.
    
    This is a convenience function that sends both welcome email to the user
    and optional admin notification.
    
    Args:
        user_name: Name of the registered user
        user_email: Email of the registered user
        admin_email: Optional email address of administrator to notify
        registration_date: Date and time of registration. Defaults to now.
        
    Returns:
        Dictionary with 'user_email' and 'admin_email' keys indicating success
    """
    if registration_date is None:
        registration_date = datetime.utcnow()
        
    service = RegistrationEmailService()
    
    results = {
        "user_email": service.send_welcome_email(user_name, user_email, registration_date)
    }
    
    if admin_email:
        results["admin_email"] = service.send_admin_notification(
            user_name, user_email, registration_date, admin_email
        )
    
    return results
