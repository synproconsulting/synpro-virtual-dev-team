"""
Unit tests for notification repository.
"""

import pytest
from src.notifications.repository import NotificationRepository
from src.notifications.models import NotificationStatus, NotificationType


@pytest.fixture
def repository():
    """Create a fresh repository for each test."""
    return NotificationRepository()


def test_create_notification(repository):
    """Test creating a notification."""
    notification = repository.create(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Welcome",
        message="Welcome to our platform!",
    )
    
    assert notification.id is not None
    assert notification.user_id == "user-123"
    assert notification.type == NotificationType.EMAIL
    assert notification.status == NotificationStatus.PENDING
    assert notification.title == "Welcome"
    assert notification.message == "Welcome to our platform!"


def test_get_by_id(repository):
    """Test retrieving notification by ID."""
    created = repository.create(
        user_id="user-123",
        notification_type=NotificationType.SMS,
        title="Test",
        message="Test message",
    )
    
    retrieved = repository.get_by_id(created.id)
    
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.user_id == created.user_id


def test_get_by_id_not_found(repository):
    """Test retrieving non-existent notification."""
    result = repository.get_by_id("non-existent-id")
    assert result is None


def test_get_by_user_id(repository):
    """Test retrieving notifications for a user."""
    # Create multiple notifications
    repository.create(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Notification 1",
        message="Message 1",
    )
    repository.create(
        user_id="user-123",
        notification_type=NotificationType.SMS,
        title="Notification 2",
        message="Message 2",
    )
    repository.create(
        user_id="user-456",
        notification_type=NotificationType.PUSH,
        title="Other user notification",
        message="Message 3",
    )
    
    notifications = repository.get_by_user_id("user-123")
    
    assert len(notifications) == 2
    assert all(n.user_id == "user-123" for n in notifications)


def test_get_by_user_id_with_status_filter(repository):
    """Test filtering notifications by status."""
    notif1 = repository.create(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Test 1",
        message="Message 1",
    )
    notif2 = repository.create(
        user_id="user-123",
        notification_type=NotificationType.SMS,
        title="Test 2",
        message="Message 2",
    )
    
    # Mark one as read
    notif1.mark_as_read()
    repository.update(notif1)
    
    # Get only pending notifications
    pending = repository.get_by_user_id(
        "user-123",
        status=NotificationStatus.PENDING
    )
    
    assert len(pending) == 1
    assert pending[0].id == notif2.id


def test_get_by_user_id_with_type_filter(repository):
    """Test filtering notifications by type."""
    repository.create(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Email notification",
        message="Message 1",
    )
    repository.create(
        user_id="user-123",
        notification_type=NotificationType.SMS,
        title="SMS notification",
        message="Message 2",
    )
    
    # Get only email notifications
    emails = repository.get_by_user_id(
        "user-123",
        notification_type=NotificationType.EMAIL
    )
    
    assert len(emails) == 1
    assert emails[0].type == NotificationType.EMAIL


def test_get_by_user_id_pagination(repository):
    """Test pagination of notifications."""
    # Create 5 notifications
    for i in range(5):
        repository.create(
            user_id="user-123",
            notification_type=NotificationType.EMAIL,
            title=f"Notification {i}",
            message=f"Message {i}",
        )
    
    # Get first page (2 items)
    page1 = repository.get_by_user_id("user-123", limit=2, offset=0)
    assert len(page1) == 2
    
    # Get second page (2 items)
    page2 = repository.get_by_user_id("user-123", limit=2, offset=2)
    assert len(page2) == 2
    
    # Ensure no overlap
    page1_ids = {n.id for n in page1}
    page2_ids = {n.id for n in page2}
    assert page1_ids.isdisjoint(page2_ids)


def test_update_notification(repository):
    """Test updating a notification."""
    notification = repository.create(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Original",
        message="Original message",
    )
    
    original_updated_at = notification.updated_at
    
    # Modify and update
    notification.mark_as_sent()
    updated = repository.update(notification)
    
    assert updated.status == NotificationStatus.SENT
    assert updated.sent_at is not None
    assert updated.updated_at > original_updated_at


def test_delete_notification(repository):
    """Test deleting a notification."""
    notification = repository.create(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="To delete",
        message="This will be deleted",
    )
    
    # Delete the notification
    result = repository.delete(notification.id)
    assert result is True
    
    # Verify it's gone
    retrieved = repository.get_by_id(notification.id)
    assert retrieved is None


def test_delete_non_existent_notification(repository):
    """Test deleting a non-existent notification."""
    result = repository.delete("non-existent-id")
    assert result is False


def test_count_by_user_id(repository):
    """Test counting notifications for a user."""
    # Create 3 notifications
    for i in range(3):
        repository.create(
            user_id="user-123",
            notification_type=NotificationType.EMAIL,
            title=f"Notification {i}",
            message=f"Message {i}",
        )
    
    count = repository.count_by_user_id("user-123")
    assert count == 3


def test_count_by_user_id_with_filters(repository):
    """Test counting with filters."""
    repository.create(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Email 1",
        message="Message 1",
    )
    repository.create(
        user_id="user-123",
        notification_type=NotificationType.SMS,
        title="SMS 1",
        message="Message 2",
    )
    
    email_count = repository.count_by_user_id(
        "user-123",
        notification_type=NotificationType.EMAIL
    )
    assert email_count == 1


def test_get_unread_count(repository):
    """Test getting unread notification count."""
    notif1 = repository.create(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Unread 1",
        message="Message 1",
    )
    notif2 = repository.create(
        user_id="user-123",
        notification_type=NotificationType.SMS,
        title="To be read",
        message="Message 2",
    )
    
    # Initially all unread
    unread_count = repository.get_unread_count("user-123")
    assert unread_count == 2
    
    # Mark one as read
    notif1.mark_as_read()
    repository.update(notif1)
    
    unread_count = repository.get_unread_count("user-123")
    assert unread_count == 1


def test_create_with_metadata(repository):
    """Test creating notification with metadata."""
    metadata = {"campaign_id": "camp-123", "priority": "high"}
    
    notification = repository.create(
        user_id="user-123",
        notification_type=NotificationType.EMAIL,
        title="Test",
        message="Test message",
        metadata=metadata,
    )
    
    assert notification.metadata == metadata
    
    # Retrieve and verify
    retrieved = repository.get_by_id(notification.id)
    assert retrieved.metadata == metadata
