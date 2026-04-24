"""
Tests for notification models.
"""

import pytest
from datetime import datetime

from src.notifications.models import (
    EmailMessage,
    NotificationStatus,
    NotificationRecord
)


class TestEmailMessage:
    """Tests for EmailMessage model."""
    
    def test_valid_email_message(self):
        """Test creating a valid email message."""
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test Subject",
            body="Test Body",
            from_email="sender@example.com"
        )
        
        assert message.to == ["recipient@example.com"]
        assert message.subject == "Test Subject"
        assert message.body == "Test Body"
        assert message.from_email == "sender@example.com"
        assert message.cc is None
        assert message.bcc is None
        assert message.html is False
        assert message.reply_to is None
        assert message.attachments is None
    
    def test_email_message_with_optional_fields(self):
        """Test email message with all optional fields."""
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test Subject",
            body="<html><body>Test</body></html>",
            from_email="sender@example.com",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            html=True,
            reply_to="reply@example.com",
            attachments=["/path/to/file.pdf"]
        )
        
        assert message.cc == ["cc@example.com"]
        assert message.bcc == ["bcc@example.com"]
        assert message.html is True
        assert message.reply_to == "reply@example.com"
        assert message.attachments == ["/path/to/file.pdf"]
    
    def test_empty_recipients(self):
        """Test that empty recipients raises ValueError."""
        with pytest.raises(ValueError, match="At least one recipient is required"):
            EmailMessage(
                to=[],
                subject="Test Subject",
                body="Test Body",
                from_email="sender@example.com"
            )
    
    def test_empty_subject(self):
        """Test that empty subject raises ValueError."""
        with pytest.raises(ValueError, match="Subject is required"):
            EmailMessage(
                to=["recipient@example.com"],
                subject="",
                body="Test Body",
                from_email="sender@example.com"
            )
    
    def test_empty_body(self):
        """Test that empty body raises ValueError."""
        with pytest.raises(ValueError, match="Body is required"):
            EmailMessage(
                to=["recipient@example.com"],
                subject="Test Subject",
                body="",
                from_email="sender@example.com"
            )
    
    def test_empty_from_email(self):
        """Test that empty from_email raises ValueError."""
        with pytest.raises(ValueError, match="From email is required"):
            EmailMessage(
                to=["recipient@example.com"],
                subject="Test Subject",
                body="Test Body",
                from_email=""
            )


class TestNotificationStatus:
    """Tests for NotificationStatus enum."""
    
    def test_status_values(self):
        """Test notification status enum values."""
        assert NotificationStatus.PENDING == "pending"
        assert NotificationStatus.SENT == "sent"
        assert NotificationStatus.FAILED == "failed"
        assert NotificationStatus.QUEUED == "queued"


class TestNotificationRecord:
    """Tests for NotificationRecord model."""
    
    def test_valid_notification_record(self):
        """Test creating a valid notification record."""
        created_at = datetime.utcnow()
        sent_at = datetime.utcnow()
        
        record = NotificationRecord(
            id="123",
            notification_type="email",
            recipient="user@example.com",
            status=NotificationStatus.SENT,
            created_at=created_at,
            sent_at=sent_at
        )
        
        assert record.id == "123"
        assert record.notification_type == "email"
        assert record.recipient == "user@example.com"
        assert record.status == NotificationStatus.SENT
        assert record.created_at == created_at
        assert record.sent_at == sent_at
        assert record.error_message is None
        assert record.metadata is None
    
    def test_failed_notification_record(self):
        """Test creating a failed notification record."""
        created_at = datetime.utcnow()
        
        record = NotificationRecord(
            id="456",
            notification_type="email",
            recipient="user@example.com",
            status=NotificationStatus.FAILED,
            created_at=created_at,
            error_message="SMTP connection failed"
        )
        
        assert record.status == NotificationStatus.FAILED
        assert record.error_message == "SMTP connection failed"
        assert record.sent_at is None
    
    def test_notification_record_with_metadata(self):
        """Test notification record with metadata."""
        created_at = datetime.utcnow()
        metadata = {"template": "welcome", "user_id": "789"}
        
        record = NotificationRecord(
            id="789",
            notification_type="email",
            recipient="user@example.com",
            status=NotificationStatus.SENT,
            created_at=created_at,
            metadata=metadata
        )
        
        assert record.metadata == metadata
        assert record.metadata["template"] == "welcome"
        assert record.metadata["user_id"] == "789"
