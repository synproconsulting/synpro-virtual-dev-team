"""Email notification service for account registration events."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Protocol


logger = logging.getLogger(__name__)


@dataclass
class RegistrationEvent:
    """Represents an account registration event."""
    
    user_email: str
    user_name: str
    registration_time: datetime
    verification_token: str | None = None
    user_id: str | None = None


class EmailProvider(Protocol):
    """Protocol for email sending implementations."""
    
    def send_email(
        self,
        to_address: str,
        subject: str,
        body_html: str,
        body_text: str,
    ) -> bool:
        """Send an email message.
        
        Args:
            to_address: Recipient email address
            subject: Email subject line
            body_html: HTML version of email body
            body_text: Plain text version of email body
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        ...


class EmailTemplate(ABC):
    """Base class for email templates."""
    
    @abstractmethod
    def render_html(self, event: RegistrationEvent) -> str:
        """Render HTML version of the email."""
        pass
    
    @abstractmethod
    def render_text(self, event: RegistrationEvent) -> str:
        """Render plain text version of the email."""
        pass
    
    @abstractmethod
    def get_subject(self, event: RegistrationEvent) -> str:
        """Get email subject line."""
        pass


class WelcomeEmailTemplate(EmailTemplate):
    """Welcome email template for new registrations."""
    
    def __init__(self, app_name: str = "Our Application", base_url: str = ""):
        self.app_name = app_name
        self.base_url = base_url
    
    def get_subject(self, event: RegistrationEvent) -> str:
        return f"Welcome to {self.app_name}!"
    
    def render_html(self, event: RegistrationEvent) -> str:
        verification_link = (
            f'{self.base_url}/verify?token={event.verification_token}'
            if event.verification_token else ""
        )
        
        html = f"""
        <html>
          <body>
            <h1>Welcome to {self.app_name}, {event.user_name}!</h1>
            <p>Thank you for registering your account.</p>
        """
        
        if verification_link:
            html += f"""
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_link}">Verify Email</a></p>
            """
        
        html += """
          </body>
        </html>
        """
        return html
    
    def render_text(self, event: RegistrationEvent) -> str:
        text = f"""Welcome to {self.app_name}, {event.user_name}!

Thank you for registering your account.
"""
        
        if event.verification_token:
            verification_link = f'{self.base_url}/verify?token={event.verification_token}'
            text += f"\nPlease verify your email address by visiting: {verification_link}\n"
        
        return text


class RegistrationEmailNotifier:
    """Handles email notifications for account registration events."""
    
    def __init__(
        self,
        email_provider: EmailProvider,
        template: EmailTemplate | None = None,
    ):
        """Initialize the notifier.
        
        Args:
            email_provider: Implementation of email sending
            template: Email template to use (defaults to WelcomeEmailTemplate)
        """
        self.email_provider = email_provider
        self.template = template or WelcomeEmailTemplate()
    
    def notify(self, event: RegistrationEvent) -> bool:
        """Send registration notification email.
        
        Args:
            event: Registration event details
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            subject = self.template.get_subject(event)
            body_html = self.template.render_html(event)
            body_text = self.template.render_text(event)
            
            success = self.email_provider.send_email(
                to_address=event.user_email,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
            )
            
            if success:
                logger.info(f"Registration email sent to {event.user_email}")
            else:
                logger.error(f"Failed to send registration email to {event.user_email}")
            
            return success
            
        except Exception as e:
            logger.exception(f"Error sending registration email: {e}")
            return False
