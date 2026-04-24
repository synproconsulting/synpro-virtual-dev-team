"""
Data models for notification service.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List


class NotificationStatus(str, Enum):
    """Status of a notification."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    QUEUED = "queued"


@dataclass
class EmailMessage:
    """
    Email message data model.
    
    Attributes:
        to: List of recipient email addresses
        subject: Email subject line
        body: Email body content (plain text or HTML)
        from_email: Sender email address
        cc: List of CC email addresses
        bcc: List of BCC email addresses
        html: Whether the body is HTML
        reply_to: Reply-to email address
        attachments: List of attachment file paths
    """
    to: List[str]
    subject: str
    body: str
    from_email: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    html: bool = False
    reply_to: Optional[str] = None
    attachments: Optional[List[str]] = None
    
    def __post_init__(self) -> None:
        """Validate email message data."""
        if not self.to:
            raise ValueError("At least one recipient is required")
        if not self.subject:
            raise ValueError("Subject is required")
        if not self.body:
            raise ValueError("Body is required")
        if not self.from_email:
            raise ValueError("From email is required")


@dataclass
class NotificationRecord:
    """
    Record of a sent notification.
    
    Attributes:
        id: Unique identifier
        notification_type: Type of notification (email, sms, etc.)
        recipient: Recipient identifier
        status: Current status
        created_at: Timestamp when notification was created
        sent_at: Timestamp when notification was sent
        error_message: Error message if failed
        metadata: Additional metadata
    """
    id: str
    notification_type: str
    recipient: str
    status: NotificationStatus
    created_at: datetime
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[dict] = None
