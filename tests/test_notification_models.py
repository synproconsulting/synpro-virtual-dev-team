"""
Unit tests for notification data models.
"""

import pytest
from datetime import datetime, timedelta
from uuid import UUID

from src.notifications.models import (
    Notification,
    NotificationCreate,
    NotificationUpdate,
    NotificationStatus,
    NotificationType,
)


class TestNotificationStatus:
    """Tests for NotificationStatus enum."""
    
    def test_notification_status_values(self):
        """Test that NotificationStatus has the expected values."""
        assert NotificationStatus.UNREAD.value == "unread"
        assert NotificationStatus.READ.value == "read"
        assert NotificationStatus.ARCHIVED.value == "archived"


class TestNotificationType:
    """Tests for NotificationType enum."""
    
    def test_notification_type_values(self):
        """Test that NotificationType has the expected values."""
        assert NotificationType.INFO.value == "info"
        assert NotificationType.SUCCESS.value == "success"
        assert NotificationType.WARNING.value == "warning"
        assert NotificationType.ERROR.value == "error"
        assert NotificationType.SYSTEM.value == "system"
        assert NotificationType.USER_ACTION.value == "user_action"
        assert NotificationType.REMINDER.value == "reminder"


class TestNotification:
    """Tests for Notification model."""
    
    def test_create_notification_with_required_fields(self):
        """Test creating a notification with only required fields."""
        notification = Notification(
            user_id="user_123",
            notification_type=NotificationType.INFO,
            title="Test Notification",
            message="This is a test message",
        )
        
        assert isinstance(notification.id, UUID)
        assert notification.user_id == "user_123"
        assert notification.notification_type == NotificationType.INFO
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test message"
        assert notification.status == NotificationStatus.UNREAD
        assert isinstance(notification.created_at, datetime)
        assert notification.read_at is None
        assert notification.archived_at is None
        assert notification.metadata == {}
        assert notification.action_url is None
        assert notification.expires_at is None
    
    def test_create_notification_with_all_fields(self):
        """Test creating a notification with all fields."""
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        notification = Notification(
            user_id="user_456",
            notification_type=NotificationType.WARNING,
            title="Important Update",
            message="Please review your settings",
            status=NotificationStatus.READ,
            metadata={"priority": "high", "category": "security"},
            action_url="https://example.com/settings",
            expires_at=expires_at,
        )
        
        assert notification.user_id == "user_456"
        assert notification.notification_type == NotificationType.WARNING
        assert notification.status == NotificationStatus.READ
        assert notification.metadata == {"priority": "high", "category": "security"}
        assert notification.action_url == "https://example.com/settings"
        assert notification.expires_at == expires_at
    
    def test_mark_as_read(self):
        """Test marking a notification as read."""
        notification = Notification(
            user_id="user_123",
            notification_type=NotificationType.INFO,
            title="Test",
            message="Test message",
        )
        
        assert notification.status == NotificationStatus.UNREAD
        assert notification.read_at is None
        
        notification.mark_as_read()
        
        assert notification.status == NotificationStatus.READ
        assert isinstance(notification.read_at, datetime)
    
    def test_mark_as_read_idempotent(self):
        """Test that marking as read multiple times doesn't change the status."""
        notification = Notification(
            user_id="user_123",
            notification_type=NotificationType.INFO,
            title="Test",
            message="Test message",
        )
        
        notification.mark_as_read()
        first_read_at = notification.read_at
        
        # Try to mark as read again
        notification.mark_as_read()
        
        # Status should stay the same, read_at shouldn't change
        assert notification.status == NotificationStatus.READ
        assert notification.read_at == first_read_at
    
    def test_mark_as_archived(self):
        """Test marking a notification as archived."""
        notification = Notification(
            user_id="user_123",
            notification_type=NotificationType.INFO,
            title="Test",
            message="Test message",
        )
        
        assert notification.archived_at is None
        
        notification.mark_as_archived()
        
        assert notification.status == NotificationStatus.ARCHIVED
        assert isinstance(notification.archived_at, datetime)
    
    def test_is_expired_no_expiration(self):
        """Test is_expired returns False when no expiration is set."""
        notification = Notification(
            user_id="user_123",
            notification_type=NotificationType.INFO,
            title="Test",
            message="Test message",
        )
        
        assert notification.is_expired() is False
    
    def test_is_expired_not_yet_expired(self):
        """Test is_expired returns False when notification hasn't expired yet."""
        future_date = datetime.utcnow() + timedelta(days=1)
        
        notification = Notification(
            user_id="user_123",
            notification_type=NotificationType.INFO,
            title="Test",
            message="Test message",
            expires_at=future_date,
        )
        
        assert notification.is_expired() is False
    
    def test_is_expired_already_expired(self):
        """Test is_expired returns True when notification has expired."""
        past_date = datetime.utcnow() - timedelta(days=1)
        
        notification = Notification(
            user_id="user_123",
            notification_type=NotificationType.INFO,
            title="Test",
            message="Test message",
            expires_at=past_date,
        )
        
        assert notification.is_expired() is True
    
    def test_to_dict(self):
        """Test converting notification to dictionary."""
        notification = Notification(
            user_id="user_123",
            notification_type=NotificationType.SUCCESS,
            title="Success",
            message="Operation completed",
            metadata={"key": "value"},
        )
        
        result = notification.to_dict()
        
        assert isinstance(result, dict)
        assert result["user_id"] == "user_123"
        assert result["notification_type"] == "success"
        assert result["title"] == "Success"
        assert result["message"] == "Operation completed"
        assert result["status"] == "unread"
        assert result["metadata"] == {"key": "value"}
        assert result["read_at"] is None
        assert result["archived_at"] is None
        assert isinstance(result["id"], str)
        assert isinstance(result["created_at"], str)


class TestNotificationCreate:
    """Tests for NotificationCreate schema."""
    
    def test_create_schema_with_required_fields(self):
        """Test creating NotificationCreate with required fields."""
        data = NotificationCreate(
            user_id="user_123",
            notification_type=NotificationType.INFO,
            title="Test",
            message="Test message",
        )
        
        assert data.user_id == "user_123"
        assert data.notification_type == NotificationType.INFO
        assert data.title == "Test"
        assert data.message == "Test message"
        assert data.metadata == {}
        assert data.action_url is None
        assert data.expires_at is None
    
    def test_create_schema_with_all_fields(self):
        """Test creating NotificationCreate with all fields."""
        expires_at = datetime.utcnow() + timedelta(days=1)
        
        data = NotificationCreate(
            user_id="user_456",
            notification_type=NotificationType.ERROR,
            title="Error",
            message="An error occurred",
            metadata={"error_code": 500},
            action_url="https://example.com/help",
            expires_at=expires_at,
        )
        
        assert data.metadata == {"error_code": 500}
        assert data.action_url == "https://example.com/help"
        assert data.expires_at == expires_at


class TestNotificationUpdate:
    """Tests for NotificationUpdate schema."""
    
    def test_update_schema_all_optional(self):
        """Test that all fields in NotificationUpdate are optional."""
        data = NotificationUpdate()
        
        assert data.status is None
        assert data.title is None
        assert data.message is None
        assert data.metadata is None
        assert data.action_url is None
    
    def test_update_schema_partial_update(self):
        """Test partial update with some fields."""
        data = NotificationUpdate(
            status=NotificationStatus.READ,
            title="Updated Title",
        )
        
        assert data.status == NotificationStatus.READ
        assert data.title == "Updated Title"
        assert data.message is None
        assert data.metadata is None
