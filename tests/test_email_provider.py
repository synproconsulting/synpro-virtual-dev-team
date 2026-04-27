"""Tests for email provider."""

from unittest.mock import MagicMock, patch

import pytest

from src.auth.email_provider import EmailProvider
from src.auth.notification_service import NotificationMessage, NotificationType


@pytest.fixture
def email_provider() -> EmailProvider:
    """Create an email provider for testing."""
    return EmailProvider(
        smtp_host="smtp.example.com",
        smtp_port=587,
        username="test@example.com",
        password="password123",
        use_tls=True,
        default_sender="noreply@example.com",
    )


@pytest.fixture
def notification_message() -> NotificationMessage:
    """Create a test notification message."""
    return NotificationMessage(
        recipient="recipient@example.com",
        subject="Test Subject",
        body="Test body content",
        notification_type=NotificationType.EMAIL,
        html_body="<p>Test body content</p>",
    )


@pytest.mark.asyncio
@patch("src.auth.email_provider.smtplib.SMTP")
async def test_send_email_success(
    mock_smtp: MagicMock,
    email_provider: EmailProvider,
    notification_message: NotificationMessage,
) -> None:
    """Test sending an email successfully."""
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    result = await email_provider.send(notification_message)

    assert result is True
    mock_smtp.assert_called_once_with("smtp.example.com", 587)
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("test@example.com", "password123")
    mock_server.send_message.assert_called_once()


@pytest.mark.asyncio
@patch("src.auth.email_provider.smtplib.SMTP")
async def test_send_email_failure(
    mock_smtp: MagicMock,
    email_provider: EmailProvider,
    notification_message: NotificationMessage,
) -> None:
    """Test handling email send failure."""
    mock_smtp.side_effect = Exception("SMTP error")

    result = await email_provider.send(notification_message)

    assert result is False


def test_create_email(
    email_provider: EmailProvider, notification_message: NotificationMessage
) -> None:
    """Test creating a MIME email message."""
    msg = email_provider._create_email(notification_message)

    assert msg["Subject"] == "Test Subject"
    assert msg["To"] == "recipient@example.com"
    assert msg["From"] == "noreply@example.com"
    assert len(msg.get_payload()) == 2  # Text and HTML parts
