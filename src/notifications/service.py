"""
Business logic layer for notification operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import Notification, NotificationStatus, NotificationType
from .repository import NotificationRepository


class NotificationService:
    """
    Service layer for notification business logic.
    """
    
    def __init__(self, repository: Optional[NotificationRepository] = None) -> None:
        """
        Initialize the notification service.
        
        Args:
            repository: Optional notification repository instance
        """
        self.repository = repository or NotificationRepository()
    
    def create_notification(
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
        return self.repository.create(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            metadata=metadata,
        )
    
    def get_notification_history(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[NotificationStatus] = None,
        notification_type: Optional[NotificationType] = None,
    ) -> Dict[str, Any]:
        """
        Get paginated notification history for a user.
        
        Args:
            user_id: User identifier
            page: Page number (1-indexed)
            page_size: Number of items per page
            status: Optional status filter
            notification_type: Optional type filter
            
        Returns:
            Dictionary with notifications, pagination info, and metadata
        """
        offset = (page - 1) * page_size
        
        notifications = self.repository.get_by_user_id(
            user_id=user_id,
            limit=page_size,
            offset=offset,
            status=status,
            notification_type=notification_type,
        )
        
        total_count = self.repository.count_by_user_id(
            user_id=user_id,
            status=status,
            notification_type=notification_type,
        )
        
        unread_count = self.repository.get_unread_count(user_id)
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "notifications": [n.to_dict() for n in notifications],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
            "metadata": {
                "unread_count": unread_count,
            },
        }
    
    def mark_as_read(self, notification_id: str, user_id: str) -> Optional[Notification]:
        """
        Mark a notification as read.
        
        Args:
            notification_id: Notification identifier
            user_id: User identifier (for authorization)
            
        Returns:
            Updated notification or None if not found/unauthorized
        """
        notification = self.repository.get_by_id(notification_id)
        
        if not notification or notification.user_id != user_id:
            return None
        
        notification.mark_as_read()
        return self.repository.update(notification)
    
    def mark_all_as_read(self, user_id: str) -> int:
        """
        Mark all unread notifications as read for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Count of notifications marked as read
        """
        notifications = self.repository.get_by_user_id(
            user_id=user_id,
            limit=1000,  # Process in batches if needed
        )
        
        count = 0
        for notification in notifications:
            if notification.status != NotificationStatus.READ:
                notification.mark_as_read()
                self.repository.update(notification)
                count += 1
        
        return count
    
    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """
        Delete a notification.
        
        Args:
            notification_id: Notification identifier
            user_id: User identifier (for authorization)
            
        Returns:
            True if deleted, False if not found/unauthorized
        """
        notification = self.repository.get_by_id(notification_id)
        
        if not notification or notification.user_id != user_id:
            return False
        
        return self.repository.delete(notification_id)
    
    def get_notification_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get notification statistics for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with notification statistics
        """
        total_count = self.repository.count_by_user_id(user_id)
        unread_count = self.repository.get_unread_count(user_id)
        
        stats_by_type = {}
        for notification_type in NotificationType:
            count = self.repository.count_by_user_id(
                user_id=user_id,
                notification_type=notification_type,
            )
            stats_by_type[notification_type.value] = count
        
        stats_by_status = {}
        for status in NotificationStatus:
            count = self.repository.count_by_user_id(
                user_id=user_id,
                status=status,
            )
            stats_by_status[status.value] = count
        
        return {
            "total_count": total_count,
            "unread_count": unread_count,
            "by_type": stats_by_type,
            "by_status": stats_by_status,
        }
