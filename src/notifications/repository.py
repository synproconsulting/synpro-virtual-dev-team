"""
Repository layer for notification data access.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from .models import Notification, NotificationStatus, NotificationType


class NotificationRepository:
    """
    Repository for managing notification persistence.
    
    This is an in-memory implementation for demonstration.
    In production, this would interact with a database.
    """
    
    def __init__(self) -> None:
        """Initialize the notification repository."""
        self._notifications: Dict[str, Notification] = {}
    
    def create(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        metadata: Optional[dict] = None,
    ) -> Notification:
        """
        Create a new notification.
        
        Args:
            user_id: ID of the user to notify
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            metadata: Optional metadata dictionary
            
        Returns:
            Created notification object
        """
        notification_id = str(uuid.uuid4())
        notification = Notification(
            id=notification_id,
            user_id=user_id,
            type=notification_type,
            status=NotificationStatus.PENDING,
            title=title,
            message=message,
            metadata=metadata or {},
        )
        self._notifications[notification_id] = notification
        return notification
    
    def get_by_id(self, notification_id: str) -> Optional[Notification]:
        """
        Retrieve a notification by ID.
        
        Args:
            notification_id: Unique notification identifier
            
        Returns:
            Notification object if found, None otherwise
        """
        return self._notifications.get(notification_id)
    
    def get_by_user_id(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        status: Optional[NotificationStatus] = None,
        notification_type: Optional[NotificationType] = None,
    ) -> List[Notification]:
        """
        Retrieve notifications for a specific user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip
            status: Optional status filter
            notification_type: Optional type filter
            
        Returns:
            List of notification objects
        """
        notifications = [
            n for n in self._notifications.values()
            if n.user_id == user_id
        ]
        
        if status:
            notifications = [n for n in notifications if n.status == status]
        
        if notification_type:
            notifications = [n for n in notifications if n.type == notification_type]
        
        # Sort by created_at descending (newest first)
        notifications.sort(key=lambda x: x.created_at, reverse=True)
        
        return notifications[offset:offset + limit]
    
    def update(self, notification: Notification) -> Notification:
        """
        Update an existing notification.
        
        Args:
            notification: Notification object with updated fields
            
        Returns:
            Updated notification object
        """
        notification.updated_at = datetime.utcnow()
        self._notifications[notification.id] = notification
        return notification
    
    def delete(self, notification_id: str) -> bool:
        """
        Delete a notification.
        
        Args:
            notification_id: Unique notification identifier
            
        Returns:
            True if deleted, False if not found
        """
        if notification_id in self._notifications:
            del self._notifications[notification_id]
            return True
        return False
    
    def count_by_user_id(
        self,
        user_id: str,
        status: Optional[NotificationStatus] = None,
        notification_type: Optional[NotificationType] = None,
    ) -> int:
        """
        Count notifications for a user.
        
        Args:
            user_id: User identifier
            status: Optional status filter
            notification_type: Optional type filter
            
        Returns:
            Count of matching notifications
        """
        notifications = [
            n for n in self._notifications.values()
            if n.user_id == user_id
        ]
        
        if status:
            notifications = [n for n in notifications if n.status == status]
        
        if notification_type:
            notifications = [n for n in notifications if n.type == notification_type]
        
        return len(notifications)
    
    def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Count of unread notifications
        """
        return sum(
            1 for n in self._notifications.values()
            if n.user_id == user_id and n.status != NotificationStatus.READ
        )
