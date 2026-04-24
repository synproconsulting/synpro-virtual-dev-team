"""
Unit tests for notification service.
"""

import pytest
from src.notifications.service import NotificationService
from src.notifications.repository import NotificationRepository
from src.notifications.models import NotificationStatus, NotificationType


@pytest.fixture
def service():
    """Create a fresh service with repository for each test."""
    repository = NotificationRepository()
    return NotificationService(repository)


def test_create_notification(service):
    """Test creating a notification through service."""
    notification = service.create_notification(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Welcome",
        message="Welcome to our platform!",
        metadata={"source": "registration"},
    )
    
    assert notification.id is not None
    assert notification.user_id == "user-123"
    assert notification.type == NotificationType.EMAIL
    assert notification.status == NotificationStatus.PENDING
    assert notification.metadata["source"] == "registration"


def test_get_notification_history(service):
    """Test getting notification history."""
    # Create some notifications
    for i in range(5):
        service.create_notification(
            user_id="user-123",
            notification_type=NotificationType.EMAIL,
            title=f"Notification {i}",
            message=f"Message {i}",
        )
    
    history = service.get_notification_history("user-123", page=1, page_size=3)
    
    assert len(history["notifications"]) == 3
    assert history["pagination"]["page"] == 1
    assert history["pagination"]["page_size"] == 3
    assert history["pagination"]["total_count"] == 5
    assert history["pagination"]["total_pages"] == 2
    assert history["pagination"]["has_next"] is True
    assert history["pagination"]["has_previous"] is False


def test_get_notification_history_pagination(service):
    """Test pagination of notification history."""
    # Create 10 notifications
    for i in range(10):
        service.create_notification(
            user_id="user-123",
            notification_type=NotificationType.EMAIL,
            title=f"Notification {i}",
            message=f"Message {i}",
        )
    
    # Get first page
    page1 = service.get_notification_history("user-123", page=1, page_size=4)
    assert len(page1["notifications"]) == 4
    assert page1["pagination"]["has_next"] is True
    assert page1["pagination"]["has_previous"] is False
    
    # Get second page
    page2 = service.get_notification_history("user-123", page=2, page_size=4)
    assert len(page2["notifications"]) == 4
    assert page2["pagination"]["has_next"] is True
    assert page2["pagination"]["has_previous"] is True
    
    # Get last page
    page3 = service.get_notification_history("user-123", page=3, page_size=4)
    assert len(page3["notifications"]) == 2
    assert page3["pagination"]["has_next"] is False
    assert page3["pagination"]["has_previous"] is True


def test_get_notification_history_with_filters(service):
    """Test filtering notification history."""
    # Create notifications of different types
    service.create_notification(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Email 1",
        message="Message 1",
    )
    service.create_notification(
        user_id="user-123",
        notification_type=NotificationType.SMS,
        title="SMS 1",
        message="Message 2",
    )
    
    # Filter by type
    email_history = service.get_notification_history(
        "user-123",
        notification_type=NotificationType.EMAIL
    )
    
    assert len(email_history["notifications"]) == 1
    assert email_history["notifications"][0]["type"] == "email"


def test_mark_as_read(service):
    """Test marking notification as read."""
    notification = service.create_notification(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Test",
        message="Test message",
    )
    
    assert notification.status == NotificationStatus.PENDING
    
    # Mark as read
    updated = service.mark_as_read(notification.id, "user-123")
    
    assert updated is not None
    assert updated.status == NotificationStatus.READ
    assert updated.read_at is not None


def test_mark_as_read_unauthorized(service):
    """Test marking notification as read with wrong user."""
    notification = service.create_notification(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Test",
        message="Test message",
    )
    
    # Try to mark as read with different user
    result = service.mark_as_read(notification.id, "user-456")
    
    assert result is None


def test_mark_as_read_not_found(service):
    """Test marking non-existent notification as read."""
    result = service.mark_as_read("non-existent-id", "user-123")
    assert result is None


def test_mark_all_as_read(service):
    """Test marking all notifications as read."""
    # Create multiple notifications
    for i in range(5):
        service.create_notification(
            user_id="user-123",
            notification_type=NotificationType.EMAIL,
            title=f"Notification {i}",
            message=f"Message {i}",
        )
    
    # Mark all as read
    count = service.mark_all_as_read("user-123")
    
    assert count == 5
    
    # Verify unread count is 0
    history = service.get_notification_history("user-123")
    assert history["metadata"]["unread_count"] == 0


def test_mark_all_as_read_partial(service):
    """Test marking all as read when some already read."""
    # Create notifications
    for i in range(3):
        notif = service.create_notification(
            user_id="user-123",
            notification_type=NotificationType.EMAIL,
            title=f"Notification {i}",
            message=f"Message {i}",
        )
        
        # Mark first one as read
        if i == 0:
            service.mark_as_read(notif.id, "user-123")
    
    # Mark all as read
    count = service.mark_all_as_read("user-123")
    
    assert count == 2  # Only 2 were unread


def test_delete_notification(service):
    """Test deleting a notification."""
    notification = service.create_notification(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="To delete",
        message="This will be deleted",
    )
    
    # Delete the notification
    result = service.delete_notification(notification.id, "user-123")
    assert result is True
    
    # Verify it's gone
    history = service.get_notification_history("user-123")
    assert len(history["notifications"]) == 0


def test_delete_notification_unauthorized(service):
    """Test deleting notification with wrong user."""
    notification = service.create_notification(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Test",
        message="Test message",
    )
    
    # Try to delete with different user
    result = service.delete_notification(notification.id, "user-456")
    assert result is False


def test_delete_notification_not_found(service):
    """Test deleting non-existent notification."""
    result = service.delete_notification("non-existent-id", "user-123")
    assert result is False


def test_get_notification_stats(service):
    """Test getting notification statistics."""
    # Create various notifications
    service.create_notification(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Email 1",
        message="Message 1",
    )
    notif2 = service.create_notification(
        user_id="user-123",
        notification_type=NotificationType.SMS,
        title="SMS 1",
        message="Message 2",
    )
    service.create_notification(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Email 2",
        message="Message 3",
    )
    
    # Mark one as read
    service.mark_as_read(notif2.id, "user-123")
    
    stats = service.get_notification_stats("user-123")
    
    assert stats["total_count"] == 3
    assert stats["unread_count"] == 2
    assert stats["by_type"]["email"] == 2
    assert stats["by_type"]["sms"] == 1
    assert stats["by_status"]["pending"] == 2
    assert stats["by_status"]["read"] == 1


def test_get_notification_stats_empty(service):
    """Test getting stats for user with no notifications."""
    stats = service.get_notification_stats("user-123")
    
    assert stats["total_count"] == 0
    assert stats["unread_count"] == 0


def test_metadata_in_history(service):
    """Test that metadata is included in history."""
    service.create_notification(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Test",
        message="Test message",
        metadata={"campaign": "summer-sale", "priority": "high"},
    )
    
    history = service.get_notification_history("user-123")
    
    assert len(history["notifications"]) == 1
    assert history["notifications"][0]["metadata"]["campaign"] == "summer-sale"
    assert history["notifications"][0]["metadata"]["priority"] == "high"
