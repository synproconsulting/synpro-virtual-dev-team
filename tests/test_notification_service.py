"""Tests for the notification service."""

import pytest

from src.auth.notification_service import (
    Notification,
    NotificationProvider,
    NotificationService,
    NotificationType,
)


class MockEmailProvider(NotificationProvider):
    """Mock email provider for testing."""

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.sent_notifications: list[Notification] = []

    async def send(self, notification: Notification) -> bool:
        if self.should_fail:
            raise Exception("Mock failure")
        self.sent_notifications.append(notification)
        return True


@pytest.fixture
def notification_service() -> NotificationService:
    """Create a notification service instance."""
    return NotificationService()


@pytest.fixture
def mock_email_provider() -> MockEmailProvider:
    """Create a mock email provider."""
    return MockEmailProvider()


def test_register_provider(notification_service: NotificationService) -> None:
    """Test registering a notification provider."""
    provider = MockEmailProvider()
    notification_service.register_provider(NotificationType.EMAIL, provider)
    assert NotificationType.EMAIL in notification_service._providers


@pytest.mark.asyncio
async def test_send_notification_success(
    notification_service: NotificationService, mock_email_provider: MockEmailProvider
) -> None:
    """Test successfully sending a notification."""
    notification_service.register_provider(
        NotificationType.EMAIL, mock_email_provider
    )
    notification = Notification(
        recipient="test@example.com",
        subject="Test Subject",
        body="Test Body",
        notification_type=NotificationType.EMAIL,
    )

    result = await notification_service.send_notification(notification)

    assert result is True
    assert len(mock_email_provider.sent_notifications) == 1
    assert mock_email_provider.sent_notifications[0] == notification


@pytest.mark.asyncio
async def test_send_notification_no_provider(
    notification_service: NotificationService,
) -> None:
    """Test sending a notification without a registered provider."""
    notification = Notification(
        recipient="test@example.com",
        subject="Test Subject",
        body="Test Body",
        notification_type=NotificationType.EMAIL,
    )

    with pytest.raises(ValueError, match="No provider registered"):
        await notification_service.send_notification(notification)


@pytest.mark.asyncio
async def test_send_notification_failure(
    notification_service: NotificationService,
) -> None:
    """Test handling notification send failures."""
    failing_provider = MockEmailProvider(should_fail=True)
    notification_service.register_provider(NotificationType.EMAIL, failing_provider)
    notification = Notification(
        recipient="test@example.com",
        subject="Test Subject",
        body="Test Body",
        notification_type=NotificationType.EMAIL,
    )

    result = await notification_service.send_notification(notification)

    assert result is False


@pytest.mark.asyncio
async def test_send_email_convenience_method(
    notification_service: NotificationService, mock_email_provider: MockEmailProvider
) -> None:
    """Test the send_email convenience method."""
    notification_service.register_provider(
        NotificationType.EMAIL, mock_email_provider
    )

    result = await notification_service.send_email(
        recipient="test@example.com",
        subject="Test Subject",
        body="Test Body",
        html_body="<p>Test Body</p>",
        metadata={"user_id": 123},
    )

    assert result is True
    assert len(mock_email_provider.sent_notifications) == 1
    sent = mock_email_provider.sent_notifications[0]
    assert sent.recipient == "test@example.com"
    assert sent.subject == "Test Subject"
    assert sent.body == "Test Body"
    assert sent.html_body == "<p>Test Body</p>"
    assert sent.metadata == {"user_id": 123}
