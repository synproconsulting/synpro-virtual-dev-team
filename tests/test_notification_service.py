"""Tests for notification service."""

import pytest

from src.auth.notification_service import (
    Notification,
    NotificationProvider,
    NotificationService,
    NotificationType,
)


class MockEmailProvider(NotificationProvider):
    """Mock email provider for testing."""

    def __init__(self, should_succeed: bool = True) -> None:
        self.should_succeed = should_succeed
        self.sent_notifications: list[Notification] = []

    async def send(self, notification: Notification) -> bool:
        self.sent_notifications.append(notification)
        return self.should_succeed


@pytest.fixture
def notification_service() -> NotificationService:
    """Create a notification service instance."""
    return NotificationService()


@pytest.fixture
def mock_provider() -> MockEmailProvider:
    """Create a mock email provider."""
    return MockEmailProvider()


@pytest.fixture
def sample_notification() -> Notification:
    """Create a sample notification."""
    return Notification(
        recipient="test@example.com",
        subject="Test Subject",
        body="Test body",
        notification_type=NotificationType.EMAIL,
    )


def test_register_provider(notification_service, mock_provider):
    """Test registering a notification provider."""
    notification_service.register_provider(NotificationType.EMAIL, mock_provider)
    assert notification_service.get_provider(NotificationType.EMAIL) == mock_provider


@pytest.mark.asyncio
async def test_send_notification_success(
    notification_service, mock_provider, sample_notification
):
    """Test successfully sending a notification."""
    notification_service.register_provider(NotificationType.EMAIL, mock_provider)
    result = await notification_service.send(sample_notification)
    assert result is True
    assert len(mock_provider.sent_notifications) == 1
    assert mock_provider.sent_notifications[0] == sample_notification


@pytest.mark.asyncio
async def test_send_notification_failure(
    notification_service, sample_notification
):
    """Test sending notification with failing provider."""
    failing_provider = MockEmailProvider(should_succeed=False)
    notification_service.register_provider(NotificationType.EMAIL, failing_provider)
    result = await notification_service.send(sample_notification)
    assert result is False


@pytest.mark.asyncio
async def test_send_notification_no_provider(
    notification_service, sample_notification
):
    """Test sending notification without registered provider."""
    with pytest.raises(ValueError, match="No provider registered"):
        await notification_service.send(sample_notification)


def test_notification_with_html_body():
    """Test creating notification with HTML body."""
    notification = Notification(
        recipient="test@example.com",
        subject="Test",
        body="Plain text",
        html_body="<p>HTML text</p>",
        notification_type=NotificationType.EMAIL,
    )
    assert notification.html_body == "<p>HTML text</p>"


def test_notification_with_metadata():
    """Test creating notification with metadata."""
    metadata = {"user_id": 123, "action": "password_reset"}
    notification = Notification(
        recipient="test@example.com",
        subject="Test",
        body="Test",
        notification_type=NotificationType.EMAIL,
        metadata=metadata,
    )
    assert notification.metadata == metadata
