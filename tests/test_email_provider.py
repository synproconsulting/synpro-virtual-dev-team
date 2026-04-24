"""
Tests for email provider implementations.
"""

import pytest
from unittest.mock import patch, MagicMock
import os

from src.notifications.email_provider import (
    SMTPEmailProvider,
    MockEmailProvider,
    EmailProvider
)
from src.notifications.models import EmailMessage


class TestSMTPEmailProvider:
    """Tests for SMTP email provider."""
    
    def test_initialization_with_params(self):
        """Test SMTP provider initialization with parameters."""
        provider = SMTPEmailProvider(
            host="smtp.example.com",
            port=587,
            username="user@example.com",
            password="password123",
            use_tls=True
        )
        
        assert provider.host == "smtp.example.com"
        assert provider.port == 587
        assert provider.username == "user@example.com"
        assert provider.password == "password123"
        assert provider.use_tls is True
    
    def test_initialization_from_env(self):
        """Test SMTP provider initialization from environment variables."""
        with patch.dict(os.environ, {
            "SMTP_HOST": "smtp.test.com",
            "SMTP_PORT": "465",
            "SMTP_USERNAME": "test@test.com",
            "SMTP_PASSWORD": "testpass",
            "SMTP_USE_TLS": "false"
        }):
            provider = SMTPEmailProvider()
            
            assert provider.host == "smtp.test.com"
            assert provider.port == 465
            assert provider.username == "test@test.com"
            assert provider.password == "testpass"
            assert provider.use_tls is False
    
    def test_initialization_missing_host(self):
        """Test that missing host raises ValueError."""
        with pytest.raises(ValueError, match="SMTP host is required"):
            SMTPEmailProvider(
                host=None,
                username="user@example.com",
                password="password123"
            )
    
    def test_initialization_missing_username(self):
        """Test that missing username raises ValueError."""
        with pytest.raises(ValueError, match="SMTP username is required"):
            SMTPEmailProvider(
                host="smtp.example.com",
                username=None,
                password="password123"
            )
    
    def test_initialization_missing_password(self):
        """Test that missing password raises ValueError."""
        with pytest.raises(ValueError, match="SMTP password is required"):
            SMTPEmailProvider(
                host="smtp.example.com",
                username="user@example.com",
                password=None
            )
    
    @patch('src.notifications.email_provider.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        provider = SMTPEmailProvider(
            host="smtp.example.com",
            username="user@example.com",
            password="password123"
        )
        
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test Subject",
            body="Test Body",
            from_email="sender@example.com"
        )
        
        result = provider.send_email(message)
        
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user@example.com", "password123")
        mock_server.send_message.assert_called_once()
    
    @patch('src.notifications.email_provider.smtplib.SMTP')
    def test_send_email_with_cc_bcc(self, mock_smtp):
        """Test email sending with CC and BCC."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        provider = SMTPEmailProvider(
            host="smtp.example.com",
            username="user@example.com",
            password="password123"
        )
        
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test Subject",
            body="Test Body",
            from_email="sender@example.com",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"]
        )
        
        result = provider.send_email(message)
        
        assert result is True
        mock_server.send_message.assert_called_once()
    
    @patch('src.notifications.email_provider.smtplib.SMTP')
    def test_send_email_html(self, mock_smtp):
        """Test sending HTML email."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        provider = SMTPEmailProvider(
            host="smtp.example.com",
            username="user@example.com",
            password="password123"
        )
        
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test Subject",
            body="<html><body>Test Body</body></html>",
            from_email="sender@example.com",
            html=True
        )
        
        result = provider.send_email(message)
        
        assert result is True
    
    @patch('src.notifications.email_provider.smtplib.SMTP')
    def test_send_email_smtp_failure(self, mock_smtp):
        """Test email sending with SMTP failure."""
        mock_smtp.return_value.__enter__.side_effect = Exception("SMTP Error")
        
        provider = SMTPEmailProvider(
            host="smtp.example.com",
            username="user@example.com",
            password="password123"
        )
        
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test Subject",
            body="Test Body",
            from_email="sender@example.com"
        )
        
        result = provider.send_email(message)
        
        assert result is False


class TestMockEmailProvider:
    """Tests for mock email provider."""
    
    def test_send_email(self):
        """Test mock email sending."""
        provider = MockEmailProvider()
        
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test Subject",
            body="Test Body",
            from_email="sender@example.com"
        )
        
        result = provider.send_email(message)
        
        assert result is True
        assert len(provider.sent_emails) == 1
        assert provider.sent_emails[0] == message
    
    def test_send_multiple_emails(self):
        """Test sending multiple mock emails."""
        provider = MockEmailProvider()
        
        for i in range(3):
            message = EmailMessage(
                to=[f"recipient{i}@example.com"],
                subject=f"Test Subject {i}",
                body=f"Test Body {i}",
                from_email="sender@example.com"
            )
            provider.send_email(message)
        
        assert len(provider.sent_emails) == 3
    
    def test_clear_emails(self):
        """Test clearing sent emails."""
        provider = MockEmailProvider()
        
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test Subject",
            body="Test Body",
            from_email="sender@example.com"
        )
        provider.send_email(message)
        
        assert len(provider.sent_emails) == 1
        
        provider.clear()
        
        assert len(provider.sent_emails) == 0
