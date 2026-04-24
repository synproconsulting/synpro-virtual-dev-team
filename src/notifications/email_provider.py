"""
Email provider implementations for sending emails.
"""

import logging
import smtplib
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional
import os

from .models import EmailMessage

logger = logging.getLogger(__name__)


class EmailProvider(ABC):
    """Abstract base class for email providers."""
    
    @abstractmethod
    def send_email(self, message: EmailMessage) -> bool:
        """
        Send an email message.
        
        Args:
            message: EmailMessage object containing email details
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        pass


class SMTPEmailProvider(EmailProvider):
    """
    SMTP email provider implementation.
    
    Sends emails using SMTP protocol. Configuration is loaded from environment variables:
    - SMTP_HOST: SMTP server hostname
    - SMTP_PORT: SMTP server port (default: 587)
    - SMTP_USERNAME: SMTP authentication username
    - SMTP_PASSWORD: SMTP authentication password
    - SMTP_USE_TLS: Whether to use TLS (default: true)
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True
    ) -> None:
        """
        Initialize SMTP email provider.
        
        Args:
            host: SMTP server hostname (defaults to SMTP_HOST env var)
            port: SMTP server port (defaults to SMTP_PORT env var or 587)
            username: SMTP username (defaults to SMTP_USERNAME env var)
            password: SMTP password (defaults to SMTP_PASSWORD env var)
            use_tls: Whether to use TLS encryption (defaults to SMTP_USE_TLS env var or True)
        """
        self.host = host or os.getenv("SMTP_HOST")
        self.port = port or int(os.getenv("SMTP_PORT", "587"))
        self.username = username or os.getenv("SMTP_USERNAME")
        self.password = password or os.getenv("SMTP_PASSWORD")
        self.use_tls = use_tls if use_tls is not None else os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        if not self.host:
            raise ValueError("SMTP host is required")
        if not self.username:
            raise ValueError("SMTP username is required")
        if not self.password:
            raise ValueError("SMTP password is required")
    
    def send_email(self, message: EmailMessage) -> bool:
        """
        Send an email via SMTP.
        
        Args:
            message: EmailMessage object containing email details
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Create message container
            msg = MIMEMultipart()
            msg["From"] = message.from_email
            msg["To"] = ", ".join(message.to)
            msg["Subject"] = message.subject
            
            if message.cc:
                msg["Cc"] = ", ".join(message.cc)
            
            if message.reply_to:
                msg["Reply-To"] = message.reply_to
            
            # Attach body
            if message.html:
                msg.attach(MIMEText(message.body, "html"))
            else:
                msg.attach(MIMEText(message.body, "plain"))
            
            # Attach files if any
            if message.attachments:
                for filepath in message.attachments:
                    self._attach_file(msg, filepath)
            
            # Prepare recipient list
            recipients = message.to.copy()
            if message.cc:
                recipients.extend(message.cc)
            if message.bcc:
                recipients.extend(message.bcc)
            
            # Connect and send
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                
                server.login(self.username, self.password)
                server.send_message(msg, from_addr=message.from_email, to_addrs=recipients)
            
            logger.info(f"Email sent successfully to {', '.join(message.to)}")
            return True
            
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            return False
    
    def _attach_file(self, msg: MIMEMultipart, filepath: str) -> None:
        """
        Attach a file to the email message.
        
        Args:
            msg: MIMEMultipart message object
            filepath: Path to file to attach
        """
        try:
            with open(filepath, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            
            encoders.encode_base64(part)
            filename = os.path.basename(filepath)
            part.add_header("Content-Disposition", f"attachment; filename= {filename}")
            msg.attach(part)
            
        except Exception as e:
            logger.warning(f"Failed to attach file {filepath}: {str(e)}")


class MockEmailProvider(EmailProvider):
    """
    Mock email provider for testing.
    
    Does not actually send emails, but logs them and stores them in memory.
    """
    
    def __init__(self) -> None:
        """Initialize mock email provider."""
        self.sent_emails: list[EmailMessage] = []
    
    def send_email(self, message: EmailMessage) -> bool:
        """
        Mock send email - stores email in memory.
        
        Args:
            message: EmailMessage object containing email details
            
        Returns:
            Always returns True
        """
        self.sent_emails.append(message)
        logger.info(f"Mock email sent to {', '.join(message.to)}: {message.subject}")
        return True
    
    def clear(self) -> None:
        """Clear all sent emails from memory."""
        self.sent_emails.clear()
