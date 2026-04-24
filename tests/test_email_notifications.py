"""
Unit tests for email notification service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.auth.email_notifications import (
    EmailConfig,
    RegistrationEmailService,
    send_registration_notification,
)


class TestEmailConfig:
    """Tests for EmailConfig class."""
    
    def test_default_initialization(self):
        """Test EmailConfig initialization with defaults."""
        config = EmailConfig()
        assert config.smtp_host == "localhost"
        assert config.smtp_port == 587
        assert config.from_email == "noreply@example.com"
        assert config.from_name == "Registration Service"
    
    def test_custom_initialization(self):
        """Test EmailConfig initialization with custom values."""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=465,
            smtp_username="user@example.com",
            smtp_password="password123",
            from_email="info@example.com",
            from_name="Custom Service",
        )
        assert config.smtp_host == "smtp.example.com"
        assert config.smtp_port == 465
        assert config.smtp_username == "user@example.com"
        assert config.smtp_password == "password123"
        assert config.from_email == "info@example.com"
        assert config.from_name == "Custom Service"
    
    @patch.dict("os.environ", {
        "SMTP_HOST": "env.smtp.com",
        "SMTP_PORT": "2525",
        "SMTP_USERNAME": "env_user",
        "SMTP_PASSWORD": "env_pass",
        "FROM_EMAIL": "env@example.com",
        "FROM_NAME": "Env Service",
    })
    def test_environment_variable_initialization(self):
        """Test EmailConfig reads from environment variables."""
        config = EmailConfig()
        assert config.smtp_host == "env.smtp.com"
        assert config.smtp_port == 2525
        assert config.smtp_username == "env_user"
        assert config.smtp_password == "env_pass"
        assert config.from_email == "env@example.com"
        assert config.from_name == "Env Service"


class TestRegistrationEmailService:
    """Tests for RegistrationEmailService class."""
    
    @pytest.fixture
    def email_service(self):
        """Create email service instance for testing."""
        config = EmailConfig(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_username="test@example.com",
            smtp_password="testpass",
            from_email="noreply@test.com",
            from_name="Test Service",
        )
        return RegistrationEmailService(config)
    
    @pytest.fixture
    def mock_smtp(self):
        """Create mock SMTP object."""
        with patch("src.auth.email_notifications.smtplib.SMTP") as mock:
            smtp_instance = MagicMock()
            mock.return_value = smtp_instance
            yield smtp_instance
    
    def test_initialization(self, email_service):
        """Test RegistrationEmailService initialization."""
        assert email_service.config.smtp_host == "smtp.test.com"
        assert email_service.config.smtp_port == 587
    
    def test_generate_welcome_email_text(self, email_service):
        """Test plain text welcome email generation."""
        user_name = "John Doe"
        user_email = "john@example.com"
        reg_date = datetime(2024, 1, 15, 10, 30, 0)
        
        text = email_service._generate_welcome_email_text(
            user_name, user_email, reg_date
        )
        
        assert "John Doe" in text
        assert "john@example.com" in text
        assert "2024-01-15" in text
        assert "Welcome to Our Platform!" in text
    
    def test_generate_welcome_email_html(self, email_service):
        """Test HTML welcome email generation."""
        user_name = "John Doe"
        user_email = "john@example.com"
        reg_date = datetime(2024, 1, 15, 10, 30, 0)
        
        html = email_service._generate_welcome_email_html(
            user_name, user_email, reg_date
        )
        
        assert "John Doe" in html
        assert "john@example.com" in html
        assert "2024-01-15" in html
        assert "<html>" in html
        assert "</html>" in html
    
    def test_send_welcome_email_success(self, email_service, mock_smtp):
        """Test successful welcome email sending."""
        user_name = "Jane Smith"
        user_email = "jane@example.com"
        reg_date = datetime(2024, 1, 15, 10, 30, 0)
        
        result = email_service.send_welcome_email(
            user_name, user_email, reg_date
        )
        
        assert result is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("test@example.com", "testpass")
        mock_smtp.send_message.assert_called_once()
    
    def test_send_welcome_email_with_default_date(self, email_service, mock_smtp):
        """Test welcome email sending with default registration date."""
        user_name = "Jane Smith"
        user_email = "jane@example.com"
        
        result = email_service.send_welcome_email(user_name, user_email)
        
        assert result is True
        mock_smtp.send_message.assert_called_once()
    
    def test_send_welcome_email_failure(self, email_service, mock_smtp):
        """Test welcome email sending failure handling."""
        mock_smtp.send_message.side_effect = Exception("SMTP error")
        
        user_name = "Jane Smith"
        user_email = "jane@example.com"
        reg_date = datetime(2024, 1, 15, 10, 30, 0)
        
        result = email_service.send_welcome_email(
            user_name, user_email, reg_date
        )
        
        assert result is False
    
    def test_send_admin_notification_success(self, email_service, mock_smtp):
        """Test successful admin notification sending."""
        user_name = "New User"
        user_email = "newuser@example.com"
        admin_email = "admin@example.com"
        reg_date = datetime(2024, 1, 15, 10, 30, 0)
        
        result = email_service.send_admin_notification(
            user_name, user_email, reg_date, admin_email
        )
        
        assert result is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.send_message.assert_called_once()
    
    def test_send_admin_notification_failure(self, email_service, mock_smtp):
        """Test admin notification sending failure handling."""
        mock_smtp.send_message.side_effect = Exception("SMTP error")
        
        user_name = "New User"
        user_email = "newuser@example.com"
        admin_email = "admin@example.com"
        reg_date = datetime(2024, 1, 15, 10, 30, 0)
        
        result = email_service.send_admin_notification(
            user_name, user_email, reg_date, admin_email
        )
        
        assert result is False
    
    def test_connection_without_credentials(self):
        """Test SMTP connection without authentication credentials."""
        config = EmailConfig(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_username="",
            smtp_password="",
        )
        service = RegistrationEmailService(config)
        
        with patch("src.auth.email_notifications.smtplib.SMTP") as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value = mock_smtp
            
            connection = service._create_connection()
            
            mock_smtp.starttls.assert_called_once()
            mock_smtp.login.assert_not_called()


class TestSendRegistrationNotification:
    """Tests for send_registration_notification convenience function."""
    
    @pytest.fixture
    def mock_smtp(self):
        """Create mock SMTP object."""
        with patch("src.auth.email_notifications.smtplib.SMTP") as mock:
            smtp_instance = MagicMock()
            mock.return_value = smtp_instance
            yield smtp_instance
    
    def test_send_user_email_only(self, mock_smtp):
        """Test sending notification to user only."""
        user_name = "Test User"
        user_email = "test@example.com"
        reg_date = datetime(2024, 1, 15, 10, 30, 0)
        
        results = send_registration_notification(
            user_name, user_email, registration_date=reg_date
        )
        
        assert "user_email" in results
        assert results["user_email"] is True
        assert "admin_email" not in results
        assert mock_smtp.send_message.call_count == 1
    
    def test_send_user_and_admin_emails(self, mock_smtp):
        """Test sending notifications to both user and admin."""
        user_name = "Test User"
        user_email = "test@example.com"
        admin_email = "admin@example.com"
        reg_date = datetime(2024, 1, 15, 10, 30, 0)
        
        results = send_registration_notification(
            user_name, user_email, admin_email, reg_date
        )
        
        assert "user_email" in results
        assert results["user_email"] is True
        assert "admin_email" in results
        assert results["admin_email"] is True
        assert mock_smtp.send_message.call_count == 2
    
    def test_send_with_default_date(self, mock_smtp):
        """Test sending notification with default registration date."""
        user_name = "Test User"
        user_email = "test@example.com"
        
        results = send_registration_notification(user_name, user_email)
        
        assert results["user_email"] is True
        mock_smtp.send_message.assert_called_once()
    
    def test_partial_failure(self, mock_smtp):
        """Test handling partial failure when one email fails."""
        user_name = "Test User"
        user_email = "test@example.com"
        admin_email = "admin@example.com"
        reg_date = datetime(2024, 1, 15, 10, 30, 0)
        
        # Make the second call (admin email) fail
        mock_smtp.send_message.side_effect = [None, Exception("SMTP error")]
        
        results = send_registration_notification(
            user_name, user_email, admin_email, reg_date
        )
        
        assert results["user_email"] is True
        assert results["admin_email"] is False
