"""Tests for notification service."""

import pytest

from src.auth.notification_service import (
    NotificationMessage,
    NotificationProvider,
    NotificationService,
    NotificationType,
)


class MockProvider(NotificationProvider):
    """Mock notification provider for testing."""

    def __init__(self, should_succeed: bool = True) -> None:
        self.should_succeed = should_succeed
        self.sent_messages: list[NotificationMessage] = []

    async def send(self, message: NotificationMessage) -> bool:
        self.sent_messages.append(message)
        return self.should_succeed


@pytest.fixture
def notification_service() -> NotificationService:
    """Create a notification service for testing."""
    return NotificationService()


@pytest.fixture
def mock_provider() -> MockProvider:
    """Create a mock provider for testing."""
    return MockProvider()


@pytest.mark.asyncio
async def test_register_provider(
    notification_service: NotificationService, mock_provider: MockProvider
) -> None:
    """Test registering a notification provider."""
    notification_service.register_provider(NotificationType.EMAIL, mock_provider)
    assert notification_service.has_provider(NotificationType.EMAIL)
    assert not notification_service.has_provider(NotificationType.SMS)


@pytest.mark.asyncio
async def test_send_notification_success(
    notification_service: NotificationService, mock_provider: MockProvider
) -> None:
    """Test sending a notification successfully."""
    notification_service.register_provider(NotificationType.EMAIL, mock_provider)
    message = NotificationMessage(
        recipient="test@example.com",
        subject="Test",
        body="Test body",
        notification_type=NotificationType.EMAIL,
    )
    result = await notification_service.send_notification(message)
    assert result is True
    assert len(mock_provider.sent_messages) == 1
    assert mock_provider.sent_messages[0].recipient == "test@example.com"


@pytest.mark.asyncio
async def test_send_notification_no_provider(
    notification_service: NotificationService,
) -> None:
    """Test sending a notification without a registered provider."""
    message = NotificationMessage(
        recipient="test@example.com",
        subject="Test",
        body="Test body",
        notification_type=NotificationType.EMAIL,
    )
    with pytest.raises(ValueError, match="No provider registered"):
        await notification_service.send_notification(message)


@pytest.mark.asyncio
async def test_send_notification_failure(
    notification_service: NotificationService,
) -> None:
    """Test handling notification send failure."""
    failing_provider = MockProvider(should_succeed=False)
    notification_service.register_provider(NotificationType.EMAIL, failing_provider)
    message = NotificationMessage(
        recipient="test@example.com",
        subject="Test",
        body="Test body",
        notification_type=NotificationType.EMAIL,
    )
    result = await notification_service.send_notification(message)
    assert result is False
