"""Tests for email notification service."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.auth.email_notifications import EmailNotificationService
import smtplib
from email.mime.multipart import MIMEMultipart


class TestEmailNotificationService:
    """Test cases for EmailNotificationService."""

    @pytest.fixture
    def service(self):
        """Create email notification service for testing."""
        return EmailNotificationService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="test@example.com",
            smtp_password="password",
            from_email="noreply@example.com",
            use_tls=True,
        )

    @pytest.fixture
    def mock_smtp(self):
        """Create mock SMTP server."""
        with patch("smtplib.SMTP") as mock:
            smtp_instance = MagicMock()
            mock.return_value = smtp_instance
            smtp_instance.__enter__ = Mock(return_value=smtp_instance)
            smtp_instance.__exit__ = Mock(return_value=False)
            yield smtp_instance

    def test_initialization_with_parameters(self):
        """Test service initialization with explicit parameters."""
        service = EmailNotificationService(
            smtp_host="smtp.test.com",
            smtp_port=465,
            smtp_username="user@test.com",
            smtp_password="pass123",
            from_email="sender@test.com",
            use_tls=False,
        )

        assert service.smtp_host == "smtp.test.com"
        assert service.smtp_port == 465
        assert service.smtp_username == "user@test.com"
        assert service.smtp_password == "pass123"
        assert service.from_email == "sender@test.com"
        assert service.use_tls is False

    def test_initialization_with_env_vars(self, monkeypatch):
        """Test service initialization with environment variables."""
        monkeypatch.setenv("SMTP_HOST", "env.smtp.com")
        monkeypatch.setenv("SMTP_PORT", "2525")
        monkeypatch.setenv("SMTP_USERNAME", "env_user")
        monkeypatch.setenv("SMTP_PASSWORD", "env_pass")
        monkeypatch.setenv("FROM_EMAIL", "env@test.com")

        service = EmailNotificationService()

        assert service.smtp_host == "env.smtp.com"
        assert service.smtp_port == 2525
        assert service.smtp_username == "env_user"
        assert service.smtp_password == "env_pass"
        assert service.from_email == "env@test.com"

    def test_create_smtp_connection_with_tls(self, service, mock_smtp):
        """Test SMTP connection creation with TLS."""
        with patch("smtplib.SMTP") as mock_smtp_class:
            mock_instance = MagicMock()
            mock_smtp_class.return_value = mock_instance

            service._create_smtp_connection()

            mock_smtp_class.assert_called_once_with("smtp.example.com", 587)
            mock_instance.starttls.assert_called_once()
            mock_instance.login.assert_called_once_with(
                "test@example.com", "password"
            )

    def test_create_smtp_connection_without_tls(self):
        """Test SMTP connection creation without TLS."""
        service = EmailNotificationService(
            smtp_host="smtp.example.com",
            smtp_port=25,
            use_tls=False,
        )

        with patch("smtplib.SMTP") as mock_smtp_class:
            mock_instance = MagicMock()
            mock_smtp_class.return_value = mock_instance

            service._create_smtp_connection()

            mock_smtp_class.assert_called_once_with("smtp.example.com", 25)
            mock_instance.starttls.assert_not_called()
            mock_instance.login.assert_not_called()

    def test_send_registration_email_success(self, service, mock_smtp):
        """Test successful registration email sending."""
        with patch.object(service, "_create_smtp_connection") as mock_conn:
            mock_conn.return_value.__enter__ = Mock(return_value=mock_smtp)
            mock_conn.return_value.__exit__ = Mock(return_value=False)

            result = service.send_registration_email(
                user_email="newuser@example.com",
                user_name="John Doe",
            )

            assert result is True
            mock_smtp.send_message.assert_called_once()
            
            # Verify the message structure
            call_args = mock_smtp.send_message.call_args[0][0]
            assert call_args["To"] == "newuser@example.com"
            assert call_args["From"] == "noreply@example.com"
            assert "Welcome" in call_args["Subject"]

    def test_send_registration_email_with_additional_data(self, service, mock_smtp):
        """Test registration email with additional data."""
        with patch.object(service, "_create_smtp_connection") as mock_conn:
            mock_conn.return_value.__enter__ = Mock(return_value=mock_smtp)
            mock_conn.return_value.__exit__ = Mock(return_value=False)

            result = service.send_registration_email(
                user_email="user@example.com",
                user_name="Jane Smith",
                additional_data={"plan": "premium", "referral": "friend123"},
            )

            assert result is True

    def test_send_registration_email_failure(self, service):
        """Test registration email sending failure."""
        with patch.object(service, "_create_smtp_connection") as mock_conn:
            mock_smtp = MagicMock()
            mock_smtp.send_message.side_effect = smtplib.SMTPException("Connection failed")
            mock_conn.return_value.__enter__ = Mock(return_value=mock_smtp)
            mock_conn.return_value.__exit__ = Mock(return_value=False)

            result = service.send_registration_email(
                user_email="user@example.com",
                user_name="John Doe",
            )

            assert result is False

    def test_send_registration_notification_to_admin_success(self, service, mock_smtp):
        """Test successful admin notification sending."""
        with patch.object(service, "_create_smtp_connection") as mock_conn:
            mock_conn.return_value.__enter__ = Mock(return_value=mock_smtp)
            mock_conn.return_value.__exit__ = Mock(return_value=False)

            result = service.send_registration_notification_to_admin(
                admin_email="admin@example.com",
                user_email="newuser@example.com",
                user_name="John Doe",
                user_id="user_12345",
            )

            assert result is True
            mock_smtp.send_message.assert_called_once()
            
            call_args = mock_smtp.send_message.call_args[0][0]
            assert call_args["To"] == "admin@example.com"
            assert "New User Registration" in call_args["Subject"]
            assert "John Doe" in call_args["Subject"]

    def test_send_registration_notification_without_user_id(self, service, mock_smtp):
        """Test admin notification without user ID."""
        with patch.object(service, "_create_smtp_connection") as mock_conn:
            mock_conn.return_value.__enter__ = Mock(return_value=mock_smtp)
            mock_conn.return_value.__exit__ = Mock(return_value=False)

            result = service.send_registration_notification_to_admin(
                admin_email="admin@example.com",
                user_email="newuser@example.com",
                user_name="Jane Smith",
            )

            assert result is True
            mock_smtp.send_message.assert_called_once()

    def test_send_registration_notification_to_admin_failure(self, service):
        """Test admin notification sending failure."""
        with patch.object(service, "_create_smtp_connection") as mock_conn:
            mock_smtp = MagicMock()
            mock_smtp.send_message.side_effect = Exception("Network error")
            mock_conn.return_value.__enter__ = Mock(return_value=mock_smtp)
            mock_conn.return_value.__exit__ = Mock(return_value=False)

            result = service.send_registration_notification_to_admin(
                admin_email="admin@example.com",
                user_email="user@example.com",
                user_name="John Doe",
            )

            assert result is False

    def test_send_email_plain_text_only(self, service, mock_smtp):
        """Test sending plain text email without HTML."""
        with patch.object(service, "_create_smtp_connection") as mock_conn:
            mock_conn.return_value.__enter__ = Mock(return_value=mock_smtp)
            mock_conn.return_value.__exit__ = Mock(return_value=False)

            result = service._send_email(
                to_email="test@example.com",
                subject="Test Subject",
                body_text="Plain text body",
            )

            assert result is True
            mock_smtp.send_message.assert_called_once()

    def test_send_email_with_html(self, service, mock_smtp):
        """Test sending email with both plain text and HTML."""
        with patch.object(service, "_create_smtp_connection") as mock_conn:
            mock_conn.return_value.__enter__ = Mock(return_value=mock_smtp)
            mock_conn.return_value.__exit__ = Mock(return_value=False)

            result = service._send_email(
                to_email="test@example.com",
                subject="Test Subject",
                body_text="Plain text body",
                body_html="<html><body>HTML body</body></html>",
            )

            assert result is True
            mock_smtp.send_message.assert_called_once()

    def test_email_content_includes_user_details(self, service, mock_smtp):
        """Test that registration email includes user details."""
        with patch.object(service, "_create_smtp_connection") as mock_conn:
            mock_conn.return_value.__enter__ = Mock(return_value=mock_smtp)
            mock_conn.return_value.__exit__ = Mock(return_value=False)

            service.send_registration_email(
                user_email="user@example.com",
                user_name="Test User",
            )

            call_args = mock_smtp.send_message.call_args[0][0]
            message_str = call_args.as_string()
            
            assert "Test User" in message_str
            assert "user@example.com" in message_str

    @pytest.mark.parametrize(
        "user_name,user_email",
        [
            ("Alice Johnson", "alice@example.com"),
            ("Bob Smith", "bob.smith@company.org"),
            ("Charlie O'Brien", "charlie+test@domain.co.uk"),
        ],
    )
    def test_send_registration_email_various_users(self, service, mock_smtp, user_name, user_email):
        """Test registration email with various user data."""
        with patch.object(service, "_create_smtp_connection") as mock_conn:
            mock_conn.return_value.__enter__ = Mock(return_value=mock_smtp)
            mock_conn.return_value.__exit__ = Mock(return_value=False)

            result = service.send_registration_email(
                user_email=user_email,
                user_name=user_name,
            )

            assert result is True
            call_args = mock_smtp.send_message.call_args[0][0]
            assert call_args["To"] == user_email
