"""Tests for the email provider."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.auth.email_provider import SMTPEmailProvider
from src.auth.notification_service import Notification, NotificationType


@pytest.fixture
def email_provider() -> SMTPEmailProvider:
    """Create an SMTP email provider instance."""
    return SMTPEmailProvider(
        host="smtp.example.com",
        port=587,
        username="user@example.com",
        password="password123",
        from_address="noreply@example.com",
    )


@pytest.fixture
def sample_notification() -> Notification:
    """Create a sample notification."""
    return Notification(
        recipient="recipient@example.com",
        subject="Test Email",
        body="This is a test email.",
        notification_type=NotificationType.EMAIL,
        html_body="<p>This is a test email.</p>",
    )


def test_smtp_provider_initialization_with_params() -> None:
    """Test SMTP provider initialization with explicit parameters."""
    provider = SMTPEmailProvider(
        host="smtp.test.com",
        port=465,
        username="test@test.com",
        password="testpass",
        from_address="from@test.com",
    )

    assert provider.host == "smtp.test.com"
    assert provider.port == 465
    assert provider.username == "test@test.com"
    assert provider.password == "testpass"
    assert provider.from_address == "from@test.com"


def test_smtp_provider_initialization_from_env() -> None:
    """Test SMTP provider initialization from environment variables."""
    with patch.dict(
        os.environ,
        {
            "SMTP_HOST": "env.smtp.com",
            "SMTP_PORT": "2525",
            "SMTP_USERNAME": "env@example.com",
            "SMTP_PASSWORD": "envpass",
            "SMTP_FROM_ADDRESS": "env-from@example.com",
        },
    ):
        provider = SMTPEmailProvider()

        assert provider.host == "env.smtp.com"
        assert provider.port == 2525
        assert provider.username == "env@example.com"
        assert provider.password == "envpass"
        assert provider.from_address == "env-from@example.com"


def test_create_message(
    email_provider: SMTPEmailProvider, sample_notification: Notification
) -> None:
    """Test MIME message creation."""
    message = email_provider._create_message(sample_notification)

    assert message["Subject"] == "Test Email"
    assert message["From"] == "noreply@example.com"
    assert message["To"] == "recipient@example.com"
    assert message.is_multipart()


@pytest.mark.asyncio
async def test_send_email_success(
    email_provider: SMTPEmailProvider, sample_notification: Notification
) -> None:
    """Test successfully sending an email."""
    with patch("aiosmtplib.SMTP") as mock_smtp_class:
        mock_smtp = AsyncMock()
        mock_smtp_class.return_value = mock_smtp
        mock_smtp.__aenter__.return_value = mock_smtp
        mock_smtp.__aexit__.return_value = AsyncMock()

        result = await email_provider.send(sample_notification)

        assert result is True
        mock_smtp.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_email_failure(
    email_provider: SMTPEmailProvider, sample_notification: Notification
) -> None:
    """Test handling email send failures."""
    with patch("aiosmtplib.SMTP") as mock_smtp_class:
        mock_smtp = AsyncMock()
        mock_smtp_class.return_value = mock_smtp
        mock_smtp.__aenter__.return_value = mock_smtp
        mock_smtp.__aexit__.return_value = AsyncMock()
        mock_smtp.send_message.side_effect = Exception("SMTP error")

        result = await email_provider.send(sample_notification)

        assert result is False
