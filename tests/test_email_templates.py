"""Tests for email templates."""

import pytest

from src.auth.email_templates import EmailTemplates
from src.auth.notification_service import NotificationType


def test_welcome_email():
    """Test welcome email template."""
    notification = EmailTemplates.welcome_email(
        recipient="user@example.com", username="testuser"
    )

    assert notification.recipient == "user@example.com"
    assert notification.subject == "Welcome to Our Service!"
    assert "testuser" in notification.body
    assert notification.html_body is not None
    assert "testuser" in notification.html_body
    assert notification.notification_type == NotificationType.EMAIL


def test_password_reset_email():
    """Test password reset email template."""
    notification = EmailTemplates.password_reset_email(
        recipient="user@example.com",
        username="testuser",
        reset_token="abc123",
        reset_url="https://example.com/reset",
    )

    assert notification.recipient == "user@example.com"
    assert notification.subject == "Password Reset Request"
    assert "testuser" in notification.body
    assert "abc123" in notification.body
    assert "https://example.com/reset?token=abc123" in notification.body
    assert notification.html_body is not None
    assert "abc123" in notification.html_body
    assert notification.metadata is not None
    assert notification.metadata["reset_token"] == "abc123"


def test_verification_email():
    """Test verification email template."""
    notification = EmailTemplates.verification_email(
        recipient="user@example.com",
        username="testuser",
        verification_token="xyz789",
        verification_url="https://example.com/verify",
    )

    assert notification.recipient == "user@example.com"
    assert notification.subject == "Verify Your Email Address"
    assert "testuser" in notification.body
    assert "xyz789" in notification.body
    assert "https://example.com/verify?token=xyz789" in notification.body
    assert notification.html_body is not None
    assert "Verify Email" in notification.html_body
    assert notification.metadata is not None
    assert notification.metadata["verification_token"] == "xyz789"


def test_welcome_email_html_contains_username():
    """Test that HTML version of welcome email contains username."""
    notification = EmailTemplates.welcome_email(
        recipient="user@example.com", username="JohnDoe"
    )

    assert "JohnDoe" in notification.html_body
    assert "<html>" in notification.html_body
    assert "</html>" in notification.html_body


def test_password_reset_link_format():
    """Test password reset link has correct format."""
    notification = EmailTemplates.password_reset_email(
        recipient="user@example.com",
        username="testuser",
        reset_token="token123",
        reset_url="https://app.example.com/reset-password",
    )

    expected_link = "https://app.example.com/reset-password?token=token123"
    assert expected_link in notification.body
    assert expected_link in notification.html_body
