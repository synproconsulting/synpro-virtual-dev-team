"""Tests for email service functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

from email_service import send_email, send_password_reset_email


@pytest.mark.asyncio
async def test_send_email_success():
    """Test successful email sending."""
    # Mock aiosmtplib.send
    with patch("email_service.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = None
        
        # Mock SMTP credentials
        with patch("email_service.SMTP_USERNAME", "test@example.com"), \
             patch("email_service.SMTP_PASSWORD", "password"):
            
            result = await send_email(
                to_email="recipient@example.com",
                subject="Test Subject",
                html_content="<p>Test HTML</p>",
                text_content="Test Text"
            )
            
            assert result is True
            assert mock_send.called


@pytest.mark.asyncio
async def test_send_email_no_credentials():
    """Test email sending without SMTP credentials."""
    # Mock empty credentials
    with patch("email_service.SMTP_USERNAME", ""), \
         patch("email_service.SMTP_PASSWORD", ""):
        
        result = await send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_content="<p>Test HTML</p>"
        )
        
        assert result is False


@pytest.mark.asyncio
async def test_send_email_smtp_failure():
    """Test email sending when SMTP fails."""
    # Mock aiosmtplib.send to raise exception
    with patch("email_service.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = Exception("SMTP connection failed")
        
        # Mock SMTP credentials
        with patch("email_service.SMTP_USERNAME", "test@example.com"), \
             patch("email_service.SMTP_PASSWORD", "password"):
            
            result = await send_email(
                to_email="recipient@example.com",
                subject="Test Subject",
                html_content="<p>Test HTML</p>"
            )
            
            assert result is False


@pytest.mark.asyncio
async def test_send_email_html_only():
    """Test sending email with HTML content only (no text)."""
    # Mock aiosmtplib.send
    with patch("email_service.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = None
        
        # Mock SMTP credentials
        with patch("email_service.SMTP_USERNAME", "test@example.com"), \
             patch("email_service.SMTP_PASSWORD", "password"):
            
            result = await send_email(
                to_email="recipient@example.com",
                subject="Test Subject",
                html_content="<p>Test HTML</p>"
            )
            
            assert result is True
            assert mock_send.called


@pytest.mark.asyncio
async def test_send_password_reset_email():
    """Test sending password reset email."""
    token = str(uuid.uuid4())
    email = "user@example.com"
    
    # Mock send_email function
    with patch("email_service.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        
        result = await send_password_reset_email(email, token)
        
        assert result is True
        assert mock_send.called
        
        # Verify call arguments
        call_args = mock_send.call_args
        assert call_args[0][0] == email  # to_email
        assert "Reset Your Password" in call_args[0][1]  # subject
        assert token in call_args[0][2]  # html_content contains token
        assert token in call_args[0][3]  # text_content contains token


@pytest.mark.asyncio
async def test_send_password_reset_email_contains_reset_url():
    """Test that password reset email contains proper reset URL."""
    token = str(uuid.uuid4())
    email = "user@example.com"
    
    # Mock send_email function
    with patch("email_service.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        
        # Mock FRONTEND_URL
        with patch("email_service.FRONTEND_URL", "https://example.com"):
            await send_password_reset_email(email, token)
            
            call_args = mock_send.call_args
            html_content = call_args[0][2]
            text_content = call_args[0][3]
            
            expected_url = f"https://example.com/reset-password?token={token}"
            assert expected_url in html_content
            assert expected_url in text_content


@pytest.mark.asyncio
async def test_send_password_reset_email_failure():
    """Test password reset email when sending fails."""
    token = str(uuid.uuid4())
    email = "user@example.com"
    
    # Mock send_email function to fail
    with patch("email_service.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = False
        
        result = await send_password_reset_email(email, token)
        
        assert result is False


@pytest.mark.asyncio
async def test_email_contains_security_warnings():
    """Test that password reset email contains security warnings."""
    token = str(uuid.uuid4())
    email = "user@example.com"
    
    # Mock send_email function
    with patch("email_service.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        
        await send_password_reset_email(email, token)
        
        call_args = mock_send.call_args
        html_content = call_args[0][2]
        text_content = call_args[0][3]
        
        # Check for security-related content
        assert "expire" in html_content.lower()
        assert "expire" in text_content.lower()
        assert "1 hour" in html_content or "1 hour" in text_content
        
        # Check warnings about not sharing
        assert "never share" in html_content.lower() or "never share" in text_content.lower()


@pytest.mark.asyncio
async def test_send_email_message_structure():
    """Test that email message is properly structured."""
    with patch("email_service.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = None
        
        with patch("email_service.SMTP_USERNAME", "test@example.com"), \
             patch("email_service.SMTP_PASSWORD", "password"), \
             patch("email_service.SMTP_FROM_EMAIL", "noreply@example.com"), \
             patch("email_service.SMTP_FROM_NAME", "Test Service"):
            
            await send_email(
                to_email="recipient@example.com",
                subject="Test Subject",
                html_content="<p>Test HTML</p>",
                text_content="Test Text"
            )
            
            # Verify send was called with correct parameters
            assert mock_send.called
            call_kwargs = mock_send.call_args[1]
            
            # Check SMTP configuration
            assert call_kwargs["hostname"] == "smtp.gmail.com"
            assert call_kwargs["port"] == 587
            assert call_kwargs["username"] == "test@example.com"
            assert call_kwargs["password"] == "password"
            assert call_kwargs["start_tls"] is True
