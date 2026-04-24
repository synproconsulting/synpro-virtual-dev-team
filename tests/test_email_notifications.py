"""
Unit tests for email notification service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.auth.email_notifications import EmailNotificationService


class TestEmailNotificationService:
    """Test suite for EmailNotificationService."""

    @pytest.fixture
    def email_service(self):
        """Create an EmailNotificationService instance for testing."""
        return EmailNotificationService(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_username="test@test.com",
            smtp_password="testpass",
            from_email="noreply@test.com",
        )

    @pytest.fixture
    def mock_smtp(self):
        """Mock SMTP server."""
        with patch("src.auth.email_notifications.smtplib.SMTP") as mock:
            smtp_instance = MagicMock()
            mock.return_value.__enter__.return_value = smtp_instance
            yield smtp_instance

    def test_init_with_parameters(self):
        """Test initialization with explicit parameters."""
        service = EmailNotificationService(
            smtp_host="custom.smtp.com",
            smtp_port=465,
            smtp_username="user@example.com",
            smtp_password="password123",
            from_email="sender@example.com",
        )

        assert service.smtp_host == "custom.smtp.com"
        assert service.smtp_port == 465
        assert service.smtp_username == "user@example.com"
        assert service.smtp_password == "password123"
        assert service.from_email == "sender@example.com"

    def test_init_with_environment_variables(self):
        """Test initialization with environment variables."""
        with patch.dict(
            "os.environ",
            {
                "SMTP_HOST": "env.smtp.com",
                "SMTP_PORT": "2525",
                "SMTP_USERNAME": "env_user",
                "SMTP_PASSWORD": "env_pass",
                "FROM_EMAIL": "env@example.com",
            },
        ):
            service = EmailNotificationService()

            assert service.smtp_host == "env.smtp.com"
            assert service.smtp_port == 2525
            assert service.smtp_username == "env_user"
            assert service.smtp_password == "env_pass"
            assert service.from_email == "env@example.com"

    def test_send_password_reset_email_success(self, email_service, mock_smtp):
        """Test successful password reset email sending."""
        result = email_service.send_password_reset_email(
            to_email="user@example.com",
            reset_token="abc123token",
            reset_url_base="https://example.com/reset",
        )

        assert result is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("test@test.com", "testpass")
        mock_smtp.sendmail.assert_called_once()

        # Verify sendmail was called with correct parameters
        call_args = mock_smtp.sendmail.call_args[0]
        assert call_args[0] == "noreply@test.com"
        assert call_args[1] == "user@example.com"
        assert "abc123token" in call_args[2]

    def test_send_password_reset_email_contains_token(self, email_service, mock_smtp):
        """Test that password reset email contains the reset token."""
        reset_token = "unique_reset_token_123"
        email_service.send_password_reset_email(
            to_email="user@example.com",
            reset_token=reset_token,
        )

        call_args = mock_smtp.sendmail.call_args[0]
        email_content = call_args[2]
        assert reset_token in email_content

    def test_send_password_reset_email_failure(self, email_service, mock_smtp):
        """Test password reset email sending failure."""
        mock_smtp.sendmail.side_effect = Exception("SMTP error")

        result = email_service.send_password_reset_email(
            to_email="user@example.com",
            reset_token="abc123token",
        )

        assert result is False

    def test_send_login_alert_email_success(self, email_service, mock_smtp):
        """Test successful login alert email sending."""
        login_time = datetime(2024, 1, 15, 10, 30, 0)
        result = email_service.send_login_alert_email(
            to_email="user@example.com",
            login_time=login_time,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            location="New York, USA",
        )

        assert result is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("test@test.com", "testpass")
        mock_smtp.sendmail.assert_called_once()

        # Verify content
        call_args = mock_smtp.sendmail.call_args[0]
        email_content = call_args[2]
        assert "192.168.1.1" in email_content
        assert "New York, USA" in email_content
        assert "Mozilla/5.0" in email_content

    def test_send_login_alert_email_with_defaults(self, email_service, mock_smtp):
        """Test login alert email with default values."""
        result = email_service.send_login_alert_email(
            to_email="user@example.com"
        )

        assert result is True
        call_args = mock_smtp.sendmail.call_args[0]
        email_content = call_args[2]
        assert "Unknown" in email_content

    def test_send_login_alert_email_failure(self, email_service, mock_smtp):
        """Test login alert email sending failure."""
        mock_smtp.sendmail.side_effect = Exception("SMTP error")

        result = email_service.send_login_alert_email(
            to_email="user@example.com",
            ip_address="192.168.1.1",
        )

        assert result is False

    def test_send_password_changed_email_success(self, email_service, mock_smtp):
        """Test successful password changed email sending."""
        result = email_service.send_password_changed_email(
            to_email="user@example.com"
        )

        assert result is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("test@test.com", "testpass")
        mock_smtp.sendmail.assert_called_once()

        # Verify content
        call_args = mock_smtp.sendmail.call_args[0]
        email_content = call_args[2]
        assert "password has been changed" in email_content.lower()

    def test_send_password_changed_email_failure(self, email_service, mock_smtp):
        """Test password changed email sending failure."""
        mock_smtp.sendmail.side_effect = Exception("SMTP error")

        result = email_service.send_password_changed_email(
            to_email="user@example.com"
        )

        assert result is False

    def test_email_format_multipart(self, email_service, mock_smtp):
        """Test that emails are sent in multipart format (text and HTML)."""
        email_service.send_password_reset_email(
            to_email="user@example.com",
            reset_token="token123",
        )

        call_args = mock_smtp.sendmail.call_args[0]
        email_content = call_args[2]

        # Check for multipart indicators
        assert "Content-Type: multipart/alternative" in email_content
        assert "Content-Type: text/plain" in email_content
        assert "Content-Type: text/html" in email_content

    def test_smtp_connection_without_credentials(self, mock_smtp):
        """Test SMTP connection without username and password."""
        service = EmailNotificationService(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_username="",
            smtp_password="",
            from_email="noreply@test.com",
        )

        service.send_password_reset_email(
            to_email="user@example.com",
            reset_token="token123",
        )

        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_not_called()

    def test_password_reset_url_from_environment(self, email_service, mock_smtp):
        """Test password reset URL taken from environment variable."""
        with patch.dict(
            "os.environ",
            {"PASSWORD_RESET_URL": "https://custom.com/reset-pwd"},
        ):
            email_service.send_password_reset_email(
                to_email="user@example.com",
                reset_token="token123",
            )

            call_args = mock_smtp.sendmail.call_args[0]
            email_content = call_args[2]
            assert "https://custom.com/reset-pwd" in email_content

    def test_email_headers(self, email_service, mock_smtp):
        """Test that emails have proper headers."""
        email_service.send_login_alert_email(
            to_email="recipient@example.com"
        )

        call_args = mock_smtp.sendmail.call_args[0]
        email_content = call_args[2]

        assert "From: noreply@test.com" in email_content
        assert "To: recipient@example.com" in email_content
        assert "Subject: New Login Alert" in email_content

    def test_login_alert_time_formatting(self, email_service, mock_smtp):
        """Test that login time is properly formatted."""
        login_time = datetime(2024, 3, 15, 14, 30, 45)
        email_service.send_login_alert_email(
            to_email="user@example.com",
            login_time=login_time,
        )

        call_args = mock_smtp.sendmail.call_args[0]
        email_content = call_args[2]
        assert "2024-03-15 14:30:45 UTC" in email_content
