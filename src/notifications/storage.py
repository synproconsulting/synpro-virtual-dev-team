"""
Storage layer for in-app notifications with support for various backends.
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from src.notifications.models import (
    Notification,
    NotificationCreate,
    NotificationUpdate,
    NotificationStatus,
    NotificationType,
)


class NotificationStorageInterface(ABC):
    """Abstract interface for notification storage implementations."""
    
    @abstractmethod
    async def create(self, notification_data: NotificationCreate) -> Notification:
        """Create a new notification."""
        pass
    
    @abstractmethod
    async def get_by_id(self, notification_id: UUID) -> Optional[Notification]:
        """Retrieve a notification by its ID."""
        pass
    
    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: str,
        status: Optional[NotificationStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """Retrieve notifications for a specific user."""
        pass
    
    @abstractmethod
    async def update(
        self,
        notification_id: UUID,
        notification_data: NotificationUpdate,
    ) -> Optional[Notification]:
        """Update an existing notification."""
        pass
    
    @abstractmethod
    async def delete(self, notification_id: UUID) -> bool:
        """Delete a notification."""
        pass
    
    @abstractmethod
    async def mark_as_read(self, notification_id: UUID) -> Optional[Notification]:
        """Mark a notification as read."""
        pass
    
    @abstractmethod
    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications for a user as read."""
        pass
    
    @abstractmethod
    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user."""
        pass
    
    @abstractmethod
    async def delete_expired(self) -> int:
        """Delete all expired notifications."""
        pass


class InMemoryNotificationStorage(NotificationStorageInterface):
    """
    In-memory implementation of notification storage for development and testing.
    """
    
    def __init__(self) -> None:
        """Initialize the in-memory storage."""
        self._notifications: Dict[UUID, Notification] = {}
    
    async def create(self, notification_data: NotificationCreate) -> Notification:
        """
        Create a new notification in memory.
        
        Args:
            notification_data: Data for creating the notification
            
        Returns:
            The created notification
        """
        notification = Notification(
            user_id=notification_data.user_id,
            notification_type=notification_data.notification_type,
            title=notification_data.title,
            message=notification_data.message,
            metadata=notification_data.metadata,
            action_url=notification_data.action_url,
            expires_at=notification_data.expires_at,
        )
        self._notifications[notification.id] = notification
        return notification
    
    async def get_by_id(self, notification_id: UUID) -> Optional[Notification]:
        """
        Retrieve a notification by its ID.
        
        Args:
            notification_id: The notification ID
            
        Returns:
            The notification if found, None otherwise
        """
        return self._notifications.get(notification_id)
    
    async def get_by_user_id(
        self,
        user_id: str,
        status: Optional[NotificationStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """
        Retrieve notifications for a specific user.
        
        Args:
            user_id: The user ID
            status: Optional status filter
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip
            
        Returns:
            List of notifications matching the criteria
        """
        notifications = [
            n for n in self._notifications.values()
            if n.user_id == user_id and (status is None or n.status == status)
        ]
        # Sort by created_at descending
        notifications.sort(key=lambda x: x.created_at, reverse=True)
        return notifications[offset:offset + limit]
    
    async def update(
        self,
        notification_id: UUID,
        notification_data: NotificationUpdate,
    ) -> Optional[Notification]:
        """
        Update an existing notification.
        
        Args:
            notification_id: The notification ID
            notification_data: Data to update
            
        Returns:
            The updated notification if found, None otherwise
        """
        notification = self._notifications.get(notification_id)
        if notification is None:
            return None
        
        update_dict = notification_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(notification, field, value)
        
        return notification
    
    async def delete(self, notification_id: UUID) -> bool:
        """
        Delete a notification.
        
        Args:
            notification_id: The notification ID
            
        Returns:
            True if deleted, False if not found
        """
        if notification_id in self._notifications:
            del self._notifications[notification_id]
            return True
        return False
    
    async def mark_as_read(self, notification_id: UUID) -> Optional[Notification]:
        """
        Mark a notification as read.
        
        Args:
            notification_id: The notification ID
            
        Returns:
            The updated notification if found, None otherwise
        """
        notification = self._notifications.get(notification_id)
        if notification is None:
            return None
        
        notification.mark_as_read()
        return notification
    
    async def mark_all_as_read(self, user_id: str) -> int:
        """
        Mark all notifications for a user as read.
        
        Args:
            user_id: The user ID
            
        Returns:
            Number of notifications marked as read
        """
        count = 0
        for notification in self._notifications.values():
            if (
                notification.user_id == user_id
                and notification.status == NotificationStatus.UNREAD
            ):
                notification.mark_as_read()
                count += 1
        return count
    
    async def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            Count of unread notifications
        """
        return sum(
            1 for n in self._notifications.values()
            if n.user_id == user_id and n.status == NotificationStatus.UNREAD
        )
    
    async def delete_expired(self) -> int:
        """
        Delete all expired notifications.
        
        Returns:
            Number of notifications deleted
        """
        expired_ids = [
            notification_id
            for notification_id, notification in self._notifications.items()
            if notification.is_expired()
        ]
        
        for notification_id in expired_ids:
            del self._notifications[notification_id]
        
        return len(expired_ids)


class NotificationStorage:
    """
    Main notification storage class that delegates to the configured backend.
    """
    
    def __init__(self, storage_backend: Optional[NotificationStorageInterface] = None) -> None:
        """
        Initialize notification storage with a specific backend.
        
        Args:
            storage_backend: The storage backend to use. If None, uses in-memory storage.
        """
        if storage_backend is None:
            self._backend = InMemoryNotificationStorage()
        else:
            self._backend = storage_backend
    
    async def create_notification(
        self,
        notification_data: NotificationCreate,
    ) -> Notification:
        """
        Create a new notification.
        
        Args:
            notification_data: Data for creating the notification
            
        Returns:
            The created notification
        """
        return await self._backend.create(notification_data)
    
    async def get_notification(self, notification_id: UUID) -> Optional[Notification]:
        """
        Retrieve a notification by its ID.
        
        Args:
            notification_id: The notification ID
            
        Returns:
            The notification if found, None otherwise
        """
        return await self._backend.get_by_id(notification_id)
    
    async def get_user_notifications(
        self,
        user_id: str,
        status: Optional[NotificationStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """
        Retrieve notifications for a specific user.
        
        Args:
            user_id: The user ID
            status: Optional status filter
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip
            
        Returns:
            List of notifications matching the criteria
        """
        return await self._backend.get_by_user_id(user_id, status, limit, offset)
    
    async def update_notification(
        self,
        notification_id: UUID,
        notification_data: NotificationUpdate,
    ) -> Optional[Notification]:
        """
        Update an existing notification.
        
        Args:
            notification_id: The notification ID
            notification_data: Data to update
            
        Returns:
            The updated notification if found, None otherwise
        """
        return await self._backend.update(notification_id, notification_data)
    
    async def delete_notification(self, notification_id: UUID) -> bool:
        """
        Delete a notification.
        
        Args:
            notification_id: The notification ID
            
        Returns:
            True if deleted, False if not found
        """
        return await self._backend.delete(notification_id)
    
    async def mark_notification_as_read(
        self,
        notification_id: UUID,
    ) -> Optional[Notification]:
        """
        Mark a notification as read.
        
        Args:
            notification_id: The notification ID
            
        Returns:
            The updated notification if found, None otherwise
        """
        return await self._backend.mark_as_read(notification_id)
    
    async def mark_all_user_notifications_as_read(self, user_id: str) -> int:
        """
        Mark all notifications for a user as read.
        
        Args:
            user_id: The user ID
            
        Returns:
            Number of notifications marked as read
        """
        return await self._backend.mark_all_as_read(user_id)
    
    async def get_user_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            Count of unread notifications
        """
        return await self._backend.get_unread_count(user_id)
    
    async def cleanup_expired_notifications(self) -> int:
        """
        Delete all expired notifications.
        
        Returns:
            Number of notifications deleted
        """
        return await self._backend.delete_expired()
