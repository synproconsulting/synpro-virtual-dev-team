"""Tests for email templates."""

import pytest

from src.auth.email_templates import EmailTemplates
from src.auth.notification_service import NotificationType


def test_welcome_email() -> None:
    """Test welcome email template."""
    message = EmailTemplates.welcome_email(
        recipient="user@example.com", username="testuser"
    )

    assert message.recipient == "user@example.com"
    assert message.notification_type == NotificationType.EMAIL
    assert "Welcome" in message.subject
    assert "testuser" in message.body
    assert "testuser" in message.html_body
    assert message.html_body is not None


def test_password_reset_email() -> None:
    """Test password reset email template."""
    message = EmailTemplates.password_reset_email(
        recipient="user@example.com", reset_token="abc123xyz"
    )

    assert message.recipient == "user@example.com"
    assert message.notification_type == NotificationType.EMAIL
    assert "Password Reset" in message.subject
    assert "abc123xyz" in message.body
    assert "abc123xyz" in message.html_body
    assert "1 hour" in message.body


def test_verification_email() -> None:
    """Test verification email template."""
    message = EmailTemplates.verification_email(
        recipient="user@example.com", verification_code="123456"
    )

    assert message.recipient == "user@example.com"
    assert message.notification_type == NotificationType.EMAIL
    assert "Verify" in message.subject
    assert "123456" in message.body
    assert "123456" in message.html_body
    assert "24 hours" in message.body


def test_email_with_custom_sender() -> None:
    """Test email template with custom sender."""
    message = EmailTemplates.welcome_email(
        recipient="user@example.com",
        username="testuser",
        sender="custom@example.com",
    )

    assert message.sender == "custom@example.com"
