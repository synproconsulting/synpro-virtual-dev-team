"""
Data models for in-app notifications.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict


class NotificationStatus(str, Enum):
    """Enumeration of notification statuses."""
    
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"


class NotificationType(str, Enum):
    """Enumeration of notification types."""
    
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SYSTEM = "system"
    USER_ACTION = "user_action"
    REMINDER = "reminder"


class Notification(BaseModel):
    """
    Notification data model representing an in-app notification.
    
    Attributes:
        id: Unique identifier for the notification
        user_id: ID of the user who receives this notification
        notification_type: Type/category of the notification
        title: Short title of the notification
        message: Main content of the notification
        status: Current status of the notification
        created_at: Timestamp when the notification was created
        read_at: Timestamp when the notification was marked as read
        archived_at: Timestamp when the notification was archived
        metadata: Additional custom data associated with the notification
        action_url: Optional URL for action button/link
        expires_at: Optional expiration timestamp for time-sensitive notifications
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user_123",
                "notification_type": "info",
                "title": "New Feature Available",
                "message": "Check out our new dashboard analytics feature!",
                "status": "unread",
                "created_at": "2024-01-15T10:30:00Z",
                "metadata": {"feature_id": "analytics_v2"}
            }
        }
    )
    
    id: UUID = Field(default_factory=uuid4, description="Unique notification identifier")
    user_id: str = Field(..., description="User identifier who receives the notification")
    notification_type: NotificationType = Field(..., description="Type of notification")
    title: str = Field(..., min_length=1, max_length=200, description="Notification title")
    message: str = Field(..., min_length=1, max_length=1000, description="Notification content")
    status: NotificationStatus = Field(
        default=NotificationStatus.UNREAD,
        description="Current status of the notification"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp"
    )
    read_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when notification was read"
    )
    archived_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when notification was archived"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom metadata"
    )
    action_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="URL for notification action"
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Expiration timestamp for time-sensitive notifications"
    )
    
    def mark_as_read(self) -> None:
        """Mark the notification as read."""
        if self.status == NotificationStatus.UNREAD:
            self.status = NotificationStatus.READ
            self.read_at = datetime.utcnow()
    
    def mark_as_archived(self) -> None:
        """Mark the notification as archived."""
        self.status = NotificationStatus.ARCHIVED
        self.archived_at = datetime.utcnow()
    
    def is_expired(self) -> bool:
        """
        Check if the notification has expired.
        
        Returns:
            True if notification has an expiration date and it has passed, False otherwise
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert notification to dictionary representation.
        
        Returns:
            Dictionary representation of the notification
        """
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "notification_type": self.notification_type.value,
            "title": self.title,
            "message": self.message,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "metadata": self.metadata,
            "action_url": self.action_url,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class NotificationCreate(BaseModel):
    """Schema for creating a new notification."""
    
    user_id: str = Field(..., description="User identifier who receives the notification")
    notification_type: NotificationType = Field(..., description="Type of notification")
    title: str = Field(..., min_length=1, max_length=200, description="Notification title")
    message: str = Field(..., min_length=1, max_length=1000, description="Notification content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional custom metadata")
    action_url: Optional[str] = Field(default=None, max_length=500, description="URL for notification action")
    expires_at: Optional[datetime] = Field(default=None, description="Expiration timestamp")


class NotificationUpdate(BaseModel):
    """Schema for updating an existing notification."""
    
    status: Optional[NotificationStatus] = Field(default=None, description="Updated status")
    title: Optional[str] = Field(default=None, min_length=1, max_length=200, description="Updated title")
    message: Optional[str] = Field(default=None, min_length=1, max_length=1000, description="Updated message")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Updated metadata")
    action_url: Optional[str] = Field(default=None, max_length=500, description="Updated action URL")
