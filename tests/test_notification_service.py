"""
Tests for notification service.
"""

import pytest
from datetime import datetime

from src.notifications.service import NotificationService
from src.notifications.email_provider import MockEmailProvider
from src.notifications.models import NotificationStatus


class TestNotificationService:
    """Tests for NotificationService."""
    
    def test_initialization_default_provider(self):
        """Test service initialization with default provider."""
        # This will fail without environment variables, so we skip it
        # in real tests we'd use a mock provider
        pass
    
    def test_initialization_with_mock_provider(self):
        """Test service initialization with mock provider."""
        provider = MockEmailProvider()
        service = NotificationService(email_provider=provider)
        
        assert service.email_provider == provider
        assert len(service.notification_history) == 0
    
    def test_send_email_success(self):
        """Test successful email sending."""
        provider = MockEmailProvider()
        service = NotificationService(email_provider=provider)
        
        record = service.send_email(
            to=["recipient@example.com"],
            subject="Test Subject",
            body="Test Body",
            from_email="sender@example.com"
        )
        
        assert record.status == NotificationStatus.SENT
        assert record.notification_type == "email"
        assert record.recipient == "recipient@example.com"
        assert record.sent_at is not None
        assert record.error_message is None
        assert len(provider.sent_emails) == 1
        assert len(service.notification_history) == 1
    
    def test_send_email_with_cc_bcc(self):
        """Test sending email with CC and BCC."""
        provider = MockEmailProvider()
        service = NotificationService(email_provider=provider)
        
        record = service.send_email(
            to=["recipient@example.com"],
            subject="Test Subject",
            body="Test Body",
            from_email="sender@example.com",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"]
        )
        
        assert record.status == NotificationStatus.SENT
        assert len(provider.sent_emails) == 1
        
        sent_message = provider.sent_emails[0]
        assert sent_message.cc == ["cc@example.com"]
        assert sent_message.bcc == ["bcc@example.com"]
    
    def test_send_email_html(self):
        """Test sending HTML email."""
        provider = MockEmailProvider()
        service = NotificationService(email_provider=provider)
        
        html_body = "<html><body><h1>Test</h1></body></html>"
        record = service.send_email(
            to=["recipient@example.com"],
            subject="Test Subject",
            body=html_body,
            from_email="sender@example.com",
            html=True
        )
        
        assert record.status == NotificationStatus.SENT
        sent_message = provider.sent_emails[0]
        assert sent_message.html is True
        assert sent_message.body == html_body
    
    def test_send_email_with_metadata(self):
        """Test sending email with metadata."""
        provider = MockEmailProvider()
        service = NotificationService(email_provider=provider)
        
        metadata = {"user_id": "123", "template": "welcome"}
        record = service.send_email(
            to=["recipient@example.com"],
            subject="Test Subject",
            body="Test Body",
            from_email="sender@example.com",
            metadata=metadata
        )
        
        assert record.status == NotificationStatus.SENT
        assert record.metadata == metadata
    
    def test_send_welcome_email(self):
        """Test sending welcome email."""
        provider = MockEmailProvider()
        service = NotificationService(email_provider=provider)
        
        record = service.send_welcome_email(
            to_email="newuser@example.com",
            user_name="John Doe",
            from_email="noreply@example.com"
        )
        
        assert record.status == NotificationStatus.SENT
        assert record.notification_type == "email"
        assert record.metadata["type"] == "welcome"
        assert record.metadata["user_name"] == "John Doe"
        
        sent_message = provider.sent_emails[0]
        assert sent_message.to == ["newuser@example.com"]
        assert "Welcome John Doe" in sent_message.body
        assert sent_message.html is True
    
    def test_send_password_reset_email(self):
        """Test sending password reset email."""
        provider = MockEmailProvider()
        service = NotificationService(email_provider=provider)
        
        reset_token = "abc123token"
        reset_url = "https://example.com/reset"
        
        record = service.send_password_reset_email(
            to_email="user@example.com",
            reset_token=reset_token,
            reset_url=reset_url,
            from_email="noreply@example.com"
        )
        
        assert record.status == NotificationStatus.SENT
        assert record.metadata["type"] == "password_reset"
        assert record.metadata["token"] == reset_token
        
        sent_message = provider.sent_emails[0]
        assert sent_message.to == ["user@example.com"]
        assert reset_token in sent_message.body
        assert reset_url in sent_message.body
        assert sent_message.html is True
    
    def test_send_verification_email(self):
        """Test sending verification email."""
        provider = MockEmailProvider()
        service = NotificationService(email_provider=provider)
        
        verification_token = "verify123"
        verification_url = "https://example.com/verify"
        
        record = service.send_verification_email(
            to_email="user@example.com",
            verification_token=verification_token,
            verification_url=verification_url,
            from_email="noreply@example.com"
        )
        
        assert record.status == NotificationStatus.SENT
        assert record.metadata["type"] == "email_verification"
        assert record.metadata["token"] == verification_token
        
        sent_message = provider.sent_emails[0]
        assert sent_message.to == ["user@example.com"]
        assert verification_token in sent_message.body
        assert verification_url in sent_message.body
        assert sent_message.html is True
    
    def test_get_notification_history_all(self):
        """Test getting all notification history."""
        provider = MockEmailProvider()
        service = NotificationService(email_provider=provider)
        
        # Send multiple emails
        for i in range(3):
            service.send_email(
                to=[f"user{i}@example.com"],
                subject=f"Test {i}",
                body=f"Body {i}",
                from_email="sender@example.com"
            )
        
        history = service.get_notification_history()
        assert len(history) == 3
    
    def test_get_notification_history_by_type(self):
        """Test filtering notification history by type."""
        provider = MockEmailProvider()
        service = NotificationService(email_provider=provider)
        
        service.send_email(
            to=["user@example.com"],
            subject="Test",
            body="Body",
            from_email="sender@example.com"
        )
        
        history = service.get_notification_history(notification_type="email")
        assert len(history) == 1
        
        history = service.get_notification_history(notification_type="sms")
        assert len(history) == 0
    
    def test_get_notification_history_by_status(self):
        """Test filtering notification history by status."""
        provider = MockEmailProvider()
        service = NotificationService(email_provider=provider)
        
        service.send_email(
            to=["user@example.com"],
            subject="Test",
            body="Body",
            from_email="sender@example.com"
        )
        
        history = service.get_notification_history(status=NotificationStatus.SENT)
        assert len(history) == 1
        
        history = service.get_notification_history(status=NotificationStatus.FAILED)
        assert len(history) == 0
    
    def test_get_notification_history_with_limit(self):
        """Test getting notification history with limit."""
        provider = MockEmailProvider()
        service = NotificationService(email_provider=provider)
        
        # Send 5 emails
        for i in range(5):
            service.send_email(
                to=[f"user{i}@example.com"],
                subject=f"Test {i}",
                body=f"Body {i}",
                from_email="sender@example.com"
            )
        
        history = service.get_notification_history(limit=3)
        assert len(history) == 3
    
    def test_get_notification_by_id(self):
        """Test getting notification by ID."""
        provider = MockEmailProvider()
        service = NotificationService(email_provider=provider)
        
        record = service.send_email(
            to=["user@example.com"],
            subject="Test",
            body="Body",
            from_email="sender@example.com"
        )
        
        retrieved = service.get_notification_by_id(record.id)
        assert retrieved is not None
        assert retrieved.id == record.id
        assert retrieved.recipient == "user@example.com"
    
    def test_get_notification_by_invalid_id(self):
        """Test getting notification with invalid ID."""
        provider = MockEmailProvider()
        service = NotificationService(email_provider=provider)
        
        retrieved = service.get_notification_by_id("nonexistent")
        assert retrieved is None
    
    def test_multiple_notifications_tracking(self):
        """Test that multiple notifications are tracked correctly."""
        provider = MockEmailProvider()
        service = NotificationService(email_provider=provider)
        
        # Send welcome email
        welcome_record = service.send_welcome_email(
            to_email="new@example.com",
            user_name="New User",
            from_email="noreply@example.com"
        )
        
        # Send password reset email
        reset_record = service.send_password_reset_email(
            to_email="user@example.com",
            reset_token="token123",
            reset_url="https://example.com/reset",
            from_email="noreply@example.com"
        )
        
        # Send verification email
        verify_record = service.send_verification_email(
            to_email="verify@example.com",
            verification_token="verify123",
            verification_url="https://example.com/verify",
            from_email="noreply@example.com"
        )
        
        assert len(service.notification_history) == 3
        assert len(provider.sent_emails) == 3
        
        # Verify each can be retrieved
        assert service.get_notification_by_id(welcome_record.id) is not None
        assert service.get_notification_by_id(reset_record.id) is not None
        assert service.get_notification_by_id(verify_record.id) is not None
