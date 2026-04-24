"""
Unit tests for notification storage layer.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.notifications.models import (
    NotificationCreate,
    NotificationUpdate,
    NotificationStatus,
    NotificationType,
)
from src.notifications.storage import (
    InMemoryNotificationStorage,
    NotificationStorage,
)


@pytest.fixture
def storage():
    """Create an in-memory storage instance for testing."""
    return InMemoryNotificationStorage()


@pytest.fixture
def notification_storage():
    """Create a NotificationStorage instance for testing."""
    return NotificationStorage()


@pytest.fixture
def sample_notification_data():
    """Create sample notification data for testing."""
    return NotificationCreate(
        user_id="user_123",
        notification_type=NotificationType.INFO,
        title="Test Notification",
        message="This is a test notification message",
        metadata={"test": "data"},
    )


class TestInMemoryNotificationStorage:
    """Tests for InMemoryNotificationStorage."""
    
    @pytest.mark.asyncio
    async def test_create_notification(self, storage, sample_notification_data):
        """Test creating a notification."""
        notification = await storage.create(sample_notification_data)
        
        assert notification.user_id == "user_123"
        assert notification.notification_type == NotificationType.INFO
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test notification message"
        assert notification.status == NotificationStatus.UNREAD
        assert notification.metadata == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_get_by_id_existing(self, storage, sample_notification_data):
        """Test retrieving an existing notification by ID."""
        created = await storage.create(sample_notification_data)
        
        retrieved = await storage.get_by_id(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.user_id == created.user_id
    
    @pytest.mark.asyncio
    async def test_get_by_id_non_existing(self, storage):
        """Test retrieving a non-existing notification returns None."""
        non_existing_id = uuid4()
        
        result = await storage.get_by_id(non_existing_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_user_id(self, storage):
        """Test retrieving notifications for a specific user."""
        # Create notifications for different users
        data1 = NotificationCreate(
            user_id="user_1",
            notification_type=NotificationType.INFO,
            title="Notification 1",
            message="Message 1",
        )
        data2 = NotificationCreate(
            user_id="user_1",
            notification_type=NotificationType.SUCCESS,
            title="Notification 2",
            message="Message 2",
        )
        data3 = NotificationCreate(
            user_id="user_2",
            notification_type=NotificationType.WARNING,
            title="Notification 3",
            message="Message 3",
        )
        
        await storage.create(data1)
        await storage.create(data2)
        await storage.create(data3)
        
        user_1_notifications = await storage.get_by_user_id("user_1")
        
        assert len(user_1_notifications) == 2
        assert all(n.user_id == "user_1" for n in user_1_notifications)
    
    @pytest.mark.asyncio
    async def test_get_by_user_id_with_status_filter(self, storage):
        """Test retrieving notifications with status filter."""
        data1 = NotificationCreate(
            user_id="user_1",
            notification_type=NotificationType.INFO,
            title="Notification 1",
            message="Message 1",
        )
        data2 = NotificationCreate(
            user_id="user_1",
            notification_type=NotificationType.INFO,
            title="Notification 2",
            message="Message 2",
        )
        
        notif1 = await storage.create(data1)
        notif2 = await storage.create(data2)
        
        # Mark one as read
        notif1.mark_as_read()
        
        unread_notifications = await storage.get_by_user_id(
            "user_1",
            status=NotificationStatus.UNREAD
        )
        
        assert len(unread_notifications) == 1
        assert unread_notifications[0].id == notif2.id
    
    @pytest.mark.asyncio
    async def test_get_by_user_id_with_pagination(self, storage):
        """Test retrieving notifications with pagination."""
        # Create 5 notifications
        for i in range(5):
            data = NotificationCreate(
                user_id="user_1",
                notification_type=NotificationType.INFO,
                title=f"Notification {i}",
                message=f"Message {i}",
            )
            await storage.create(data)
        
        # Get first 2
        page1 = await storage.get_by_user_id("user_1", limit=2, offset=0)
        assert len(page1) == 2
        
        # Get next 2
        page2 = await storage.get_by_user_id("user_1", limit=2, offset=2)
        assert len(page2) == 2
        
        # Ensure they're different
        page1_ids = {n.id for n in page1}
        page2_ids = {n.id for n in page2}
        assert page1_ids.isdisjoint(page2_ids)
    
    @pytest.mark.asyncio
    async def test_update_notification(self, storage, sample_notification_data):
        """Test updating a notification."""
        notification = await storage.create(sample_notification_data)
        
        update_data = NotificationUpdate(
            title="Updated Title",
            message="Updated Message",
        )
        
        updated = await storage.update(notification.id, update_data)
        
        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.message == "Updated Message"
        assert updated.user_id == "user_123"  # Unchanged fields remain
    
    @pytest.mark.asyncio
    async def test_update_non_existing_notification(self, storage):
        """Test updating a non-existing notification returns None."""
        non_existing_id = uuid4()
        update_data = NotificationUpdate(title="New Title")
        
        result = await storage.update(non_existing_id, update_data)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_notification(self, storage, sample_notification_data):
        """Test deleting a notification."""
        notification = await storage.create(sample_notification_data)
        
        result = await storage.delete(notification.id)
        
        assert result is True
        
        # Verify it's deleted
        retrieved = await storage.get_by_id(notification.id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_delete_non_existing_notification(self, storage):
        """Test deleting a non-existing notification returns False."""
        non_existing_id = uuid4()
        
        result = await storage.delete(non_existing_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_mark_as_read(self, storage, sample_notification_data):
        """Test marking a notification as read."""
        notification = await storage.create(sample_notification_data)
        
        assert notification.status == NotificationStatus.UNREAD
        
        updated = await storage.mark_as_read(notification.id)
        
        assert updated is not None
        assert updated.status == NotificationStatus.READ
        assert updated.read_at is not None
    
    @pytest.mark.asyncio
    async def test_mark_as_read_non_existing(self, storage):
        """Test marking a non-existing notification as read returns None."""
        non_existing_id = uuid4()
        
        result = await storage.mark_as_read(non_existing_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_mark_all_as_read(self, storage):
        """Test marking all user notifications as read."""
        # Create multiple unread notifications
        for i in range(3):
            data = NotificationCreate(
                user_id="user_1",
                notification_type=NotificationType.INFO,
                title=f"Notification {i}",
                message=f"Message {i}",
            )
            await storage.create(data)
        
        count = await storage.mark_all_as_read("user_1")
        
        assert count == 3
        
        # Verify all are read
        notifications = await storage.get_by_user_id("user_1")
        assert all(n.status == NotificationStatus.READ for n in notifications)
    
    @pytest.mark.asyncio
    async def test_get_unread_count(self, storage):
        """Test getting count of unread notifications."""
        # Create notifications with different statuses
        data1 = NotificationCreate(
            user_id="user_1",
            notification_type=NotificationType.INFO,
            title="Notification 1",
            message="Message 1",
        )
        data2 = NotificationCreate(
            user_id="user_1",
            notification_type=NotificationType.INFO,
            title="Notification 2",
            message="Message 2",
        )
        
        notif1 = await storage.create(data1)
        await storage.create(data2)
        
        # Mark one as read
        await storage.mark_as_read(notif1.id)
        
        unread_count = await storage.get_unread_count("user_1")
        
        assert unread_count == 1
    
    @pytest.mark.asyncio
    async def test_delete_expired(self, storage):
        """Test deleting expired notifications."""
        # Create expired notification
        past_date = datetime.utcnow() - timedelta(days=1)
        expired_data = NotificationCreate(
            user_id="user_1",
            notification_type=NotificationType.INFO,
            title="Expired",
            message="This is expired",
            expires_at=past_date,
        )
        
        # Create non-expired notification
        future_date = datetime.utcnow() + timedelta(days=1)
        valid_data = NotificationCreate(
            user_id="user_1",
            notification_type=NotificationType.INFO,
            title="Valid",
            message="This is valid",
            expires_at=future_date,
        )
        
        await storage.create(expired_data)
        await storage.create(valid_data)
        
        deleted_count = await storage.delete_expired()
        
        assert deleted_count == 1
        
        # Verify only valid notification remains
        remaining = await storage.get_by_user_id("user_1")
        assert len(remaining) == 1
        assert remaining[0].title == "Valid"


class TestNotificationStorage:
    """Tests for NotificationStorage wrapper."""
    
    @pytest.mark.asyncio
    async def test_create_notification(
        self,
        notification_storage,
        sample_notification_data
    ):
        """Test creating a notification through the wrapper."""
        notification = await notification_storage.create_notification(
            sample_notification_data
        )
        
        assert notification.user_id == "user_123"
        assert notification.title == "Test Notification"
    
    @pytest.mark.asyncio
    async def test_get_notification(
        self,
        notification_storage,
        sample_notification_data
    ):
        """Test retrieving a notification through the wrapper."""
        created = await notification_storage.create_notification(
            sample_notification_data
        )
        
        retrieved = await notification_storage.get_notification(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
    
    @pytest.mark.asyncio
    async def test_get_user_notifications(self, notification_storage):
        """Test retrieving user notifications through the wrapper."""
        data = NotificationCreate(
            user_id="user_123",
            notification_type=NotificationType.INFO,
            title="Test",
            message="Test message",
        )
        
        await notification_storage.create_notification(data)
        
        notifications = await notification_storage.get_user_notifications("user_123")
        
        assert len(notifications) == 1
        assert notifications[0].user_id == "user_123"
    
    @pytest.mark.asyncio
    async def test_mark_notification_as_read(
        self,
        notification_storage,
        sample_notification_data
    ):
        """Test marking notification as read through the wrapper."""
        notification = await notification_storage.create_notification(
            sample_notification_data
        )
        
        updated = await notification_storage.mark_notification_as_read(
            notification.id
        )
        
        assert updated is not None
        assert updated.status == NotificationStatus.READ
    
    @pytest.mark.asyncio
    async def test_get_user_unread_count(self, notification_storage):
        """Test getting unread count through the wrapper."""
        data = NotificationCreate(
            user_id="user_123",
            notification_type=NotificationType.INFO,
            title="Test",
            message="Test message",
        )
        
        await notification_storage.create_notification(data)
        
        count = await notification_storage.get_user_unread_count("user_123")
        
        assert count == 1
