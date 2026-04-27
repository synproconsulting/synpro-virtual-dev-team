"""Tests for email provider."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.auth.email_provider import EmailConfig, SMTPEmailProvider
from src.auth.notification_service import Notification, NotificationType


@pytest.fixture
def email_config() -> EmailConfig:
    """Create test email configuration."""
    return EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        username="test@example.com",
        password="test_password",
        from_email="noreply@example.com",
        use_tls=True,
    )


@pytest.fixture
def email_provider(email_config: EmailConfig) -> SMTPEmailProvider:
    """Create SMTP email provider."""
    return SMTPEmailProvider(email_config)


@pytest.fixture
def sample_notification() -> Notification:
    """Create sample email notification."""
    return Notification(
        recipient="recipient@example.com",
        subject="Test Email",
        body="This is a test email body.",
        notification_type=NotificationType.EMAIL,
    )


@pytest.mark.asyncio
@patch("src.auth.email_provider.smtplib.SMTP")
async def test_send_email_success(
    mock_smtp, email_provider: SMTPEmailProvider, sample_notification: Notification
):
    """Test successfully sending an email."""
    mock_server = MagicMock()
    mock_smtp.return_value = mock_server

    result = await email_provider.send(sample_notification)

    assert result is True
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with(
        email_provider.config.username, email_provider.config.password
    )
    mock_server.send_message.assert_called_once()
    mock_server.quit.assert_called_once()


@pytest.mark.asyncio
@patch("src.auth.email_provider.smtplib.SMTP")
async def test_send_email_with_html(
    mock_smtp, email_provider: SMTPEmailProvider
):
    """Test sending email with HTML body."""
    mock_server = MagicMock()
    mock_smtp.return_value = mock_server

    notification = Notification(
        recipient="recipient@example.com",
        subject="Test",
        body="Plain text",
        html_body="<p>HTML content</p>",
        notification_type=NotificationType.EMAIL,
    )

    result = await email_provider.send(notification)
    assert result is True


@pytest.mark.asyncio
@patch("src.auth.email_provider.smtplib.SMTP")
async def test_send_email_smtp_error(
    mock_smtp, email_provider: SMTPEmailProvider, sample_notification: Notification
):
    """Test handling SMTP error."""
    mock_smtp.side_effect = Exception("SMTP connection failed")

    result = await email_provider.send(sample_notification)
    assert result is False


@pytest.mark.asyncio
@patch("src.auth.email_provider.smtplib.SMTP_SSL")
async def test_send_email_with_ssl(sample_notification: Notification):
    """Test sending email with SSL."""
    config = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=465,
        username="test@example.com",
        password="test_password",
        from_email="noreply@example.com",
        use_ssl=True,
        use_tls=False,
    )
    provider = SMTPEmailProvider(config)

    mock_server = MagicMock()
    with patch("src.auth.email_provider.smtplib.SMTP_SSL") as mock_smtp_ssl:
        mock_smtp_ssl.return_value = mock_server
        result = await provider.send(sample_notification)

    assert result is True
    mock_smtp_ssl.assert_called_once_with(config.smtp_host, config.smtp_port)
