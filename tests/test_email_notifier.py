"""Tests for email notification service."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from src.auth.email_notifier import (
    EmailTemplate,
    RegistrationEmailNotifier,
    RegistrationEvent,
    WelcomeEmailTemplate,
)


class MockEmailProvider:
    """Mock email provider for testing."""
    
    def __init__(self, should_succeed: bool = True):
        self.should_succeed = should_succeed
        self.sent_emails = []
    
    def send_email(
        self,
        to_address: str,
        subject: str,
        body_html: str,
        body_text: str,
    ) -> bool:
        self.sent_emails.append({
            'to': to_address,
            'subject': subject,
            'html': body_html,
            'text': body_text,
        })
        return self.should_succeed


@pytest.fixture
def registration_event():
    """Create a sample registration event."""
    return RegistrationEvent(
        user_email="test@example.com",
        user_name="Test User",
        registration_time=datetime(2024, 1, 1, 12, 0, 0),
        verification_token="abc123xyz",
        user_id="user_001",
    )


@pytest.fixture
def mock_email_provider():
    """Create a mock email provider."""
    return MockEmailProvider()


class TestWelcomeEmailTemplate:
    """Tests for WelcomeEmailTemplate."""
    
    def test_get_subject(self, registration_event):
        template = WelcomeEmailTemplate(app_name="TestApp")
        subject = template.get_subject(registration_event)
        assert subject == "Welcome to TestApp!"
    
    def test_render_html_with_verification(self, registration_event):
        template = WelcomeEmailTemplate(
            app_name="TestApp",
            base_url="https://example.com"
        )
        html = template.render_html(registration_event)
        
        assert "Welcome to TestApp, Test User!" in html
        assert "verify?token=abc123xyz" in html
        assert "<html>" in html
    
    def test_render_html_without_verification(self, registration_event):
        registration_event.verification_token = None
        template = WelcomeEmailTemplate(app_name="TestApp")
        html = template.render_html(registration_event)
        
        assert "Welcome to TestApp, Test User!" in html
        assert "verify?token" not in html
    
    def test_render_text_with_verification(self, registration_event):
        template = WelcomeEmailTemplate(
            app_name="TestApp",
            base_url="https://example.com"
        )
        text = template.render_text(registration_event)
        
        assert "Welcome to TestApp, Test User!" in text
        assert "verify?token=abc123xyz" in text
        assert "<html>" not in text
    
    def test_render_text_without_verification(self, registration_event):
        registration_event.verification_token = None
        template = WelcomeEmailTemplate(app_name="TestApp")
        text = template.render_text(registration_event)
        
        assert "Welcome to TestApp, Test User!" in text
        assert "verify" not in text


class TestRegistrationEmailNotifier:
    """Tests for RegistrationEmailNotifier."""
    
    def test_notify_success(self, registration_event, mock_email_provider):
        notifier = RegistrationEmailNotifier(mock_email_provider)
        result = notifier.notify(registration_event)
        
        assert result is True
        assert len(mock_email_provider.sent_emails) == 1
        
        sent = mock_email_provider.sent_emails[0]
        assert sent['to'] == "test@example.com"
        assert "Welcome" in sent['subject']
        assert "Test User" in sent['html']
        assert "Test User" in sent['text']
    
    def test_notify_failure(self, registration_event):
        failing_provider = MockEmailProvider(should_succeed=False)
        notifier = RegistrationEmailNotifier(failing_provider)
        result = notifier.notify(registration_event)
        
        assert result is False
        assert len(failing_provider.sent_emails) == 1
    
    def test_notify_with_custom_template(self, registration_event, mock_email_provider):
        custom_template = Mock(spec=EmailTemplate)
        custom_template.get_subject.return_value = "Custom Subject"
        custom_template.render_html.return_value = "<p>Custom HTML</p>"
        custom_template.render_text.return_value = "Custom Text"
        
        notifier = RegistrationEmailNotifier(mock_email_provider, custom_template)
        result = notifier.notify(registration_event)
        
        assert result is True
        sent = mock_email_provider.sent_emails[0]
        assert sent['subject'] == "Custom Subject"
        assert sent['html'] == "<p>Custom HTML</p>"
        assert sent['text'] == "Custom Text"
    
    def test_notify_handles_exceptions(self, registration_event):
        bad_provider = Mock()
        bad_provider.send_email.side_effect = Exception("Connection error")
        
        notifier = RegistrationEmailNotifier(bad_provider)
        result = notifier.notify(registration_event)
        
        assert result is False
