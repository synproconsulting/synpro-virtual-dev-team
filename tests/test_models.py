"""
Unit tests for notification models.
"""

import pytest
from datetime import datetime
from src.notifications.models import (
    Notification,
    NotificationStatus,
    NotificationType,
)


def test_notification_creation():
    """Test creating a notification instance."""
    notification = Notification(
        id="test-123",
        user_id="user-456",
        type=NotificationType.EMAIL,
        status=NotificationStatus.PENDING,
        title="Test Notification",
        message="This is a test message",
    )
    
    assert notification.id == "test-123"
    assert notification.user_id == "user-456"
    assert notification.type == NotificationType.EMAIL
    assert notification.status == NotificationStatus.PENDING
    assert notification.title == "Test Notification"
    assert notification.message == "This is a test message"
    assert notification.metadata == {}
    assert notification.error_message is None


def test_notification_mark_as_sent():
    """Test marking notification as sent."""
    notification = Notification(
        id="test-123",
        user_id="user-456",
        type=NotificationType.SMS,
        status=NotificationStatus.PENDING,
        title="Test",
        message="Test message",
    )
    
    assert notification.sent_at is None
    notification.mark_as_sent()
    
    assert notification.status == NotificationStatus.SENT
    assert notification.sent_at is not None
    assert isinstance(notification.sent_at, datetime)


def test_notification_mark_as_delivered():
    """Test marking notification as delivered."""
    notification = Notification(
        id="test-123",
        user_id="user-456",
        type=NotificationType.PUSH,
        status=NotificationStatus.SENT,
        title="Test",
        message="Test message",
    )
    
    notification.mark_as_delivered()
    
    assert notification.status == NotificationStatus.DELIVERED
    assert notification.delivered_at is not None


def test_notification_mark_as_read():
    """Test marking notification as read."""
    notification = Notification(
        id="test-123",
        user_id="user-456",
        type=NotificationType.IN_APP,
        status=NotificationStatus.DELIVERED,
        title="Test",
        message="Test message",
    )
    
    notification.mark_as_read()
    
    assert notification.status == NotificationStatus.READ
    assert notification.read_at is not None


def test_notification_mark_as_failed():
    """Test marking notification as failed."""
    notification = Notification(
        id="test-123",
        user_id="user-456",
        type=NotificationType.EMAIL,
        status=NotificationStatus.PENDING,
        title="Test",
        message="Test message",
    )
    
    error_msg = "SMTP server connection failed"
    notification.mark_as_failed(error_msg)
    
    assert notification.status == NotificationStatus.FAILED
    assert notification.error_message == error_msg


def test_notification_to_dict():
    """Test converting notification to dictionary."""
    notification = Notification(
        id="test-123",
        user_id="user-456",
        type=NotificationType.EMAIL,
        status=NotificationStatus.PENDING,
        title="Test Notification",
        message="This is a test message",
        metadata={"priority": "high"},
    )
    
    notification_dict = notification.to_dict()
    
    assert notification_dict["id"] == "test-123"
    assert notification_dict["user_id"] == "user-456"
    assert notification_dict["type"] == "email"
    assert notification_dict["status"] == "pending"
    assert notification_dict["title"] == "Test Notification"
    assert notification_dict["message"] == "This is a test message"
    assert notification_dict["metadata"] == {"priority": "high"}


def test_notification_status_enum():
    """Test NotificationStatus enum values."""
    assert NotificationStatus.PENDING.value == "pending"
    assert NotificationStatus.SENT.value == "sent"
    assert NotificationStatus.DELIVERED.value == "delivered"
    assert NotificationStatus.FAILED.value == "failed"
    assert NotificationStatus.READ.value == "read"


def test_notification_type_enum():
    """Test NotificationType enum values."""
    assert NotificationType.EMAIL.value == "email"
    assert NotificationType.SMS.value == "sms"
    assert NotificationType.PUSH.value == "push"
    assert NotificationType.IN_APP.value == "in_app"
    assert NotificationType.WEBHOOK.value == "webhook"


def test_notification_with_metadata():
    """Test notification with custom metadata."""
    metadata = {
        "campaign_id": "camp-123",
        "priority": "high",
        "tags": ["urgent", "security"],
    }
    
    notification = Notification(
        id="test-123",
        user_id="user-456",
        type=NotificationType.EMAIL,
        status=NotificationStatus.PENDING,
        title="Security Alert",
        message="Your account was accessed from a new device",
        metadata=metadata,
    )
    
    assert notification.metadata == metadata
    assert notification.metadata["campaign_id"] == "camp-123"
    assert "urgent" in notification.metadata["tags"]
