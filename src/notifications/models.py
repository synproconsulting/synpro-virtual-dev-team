"""
Data models for notification system.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field


class NotificationStatus(str, Enum):
    """Status of a notification."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class NotificationType(str, Enum):
    """Type of notification."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


@dataclass
class Notification:
    """
    Represents a notification record in the system.
    
    Attributes:
        id: Unique identifier for the notification
        user_id: ID of the user who should receive the notification
        type: Type of notification (email, SMS, push, etc.)
        status: Current status of the notification
        title: Short title/subject of the notification
        message: Full message content
        metadata: Additional metadata as key-value pairs
        created_at: Timestamp when notification was created
        updated_at: Timestamp when notification was last updated
        sent_at: Timestamp when notification was sent
        delivered_at: Timestamp when notification was delivered
        read_at: Timestamp when notification was read
        error_message: Error message if notification failed
    """
    id: str
    user_id: str
    type: NotificationType
    status: NotificationStatus
    title: str
    message: str
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def mark_as_sent(self) -> None:
        """Mark notification as sent."""
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_as_delivered(self) -> None:
        """Mark notification as delivered."""
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_as_read(self) -> None:
        """Mark notification as read."""
        self.status = NotificationStatus.READ
        self.read_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_as_failed(self, error_message: str) -> None:
        """Mark notification as failed with an error message."""
        self.status = NotificationStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert notification to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type.value,
            "status": self.status.value,
            "title": self.title,
            "message": self.message,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "error_message": self.error_message,
        }
