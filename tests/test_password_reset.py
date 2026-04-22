"""
Unit tests for password reset functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from src.auth.password_reset import (
    PasswordResetToken,
    TokenStorage,
    EmailService,
    PasswordResetService,
    create_password_reset_service
)


class TestPasswordResetToken:
    """Tests for PasswordResetToken class."""
    
    def test_token_is_valid_when_not_used_and_not_expired(self):
        """Test that a fresh token is valid."""
        token = PasswordResetToken(
            token="test_token",
            user_email="user@example.com",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_used=False
        )
        assert token.is_valid() is True
    
    def test_token_is_invalid_when_used(self):
        """Test that a used token is invalid."""
        token = PasswordResetToken(
            token="test_token",
            user_email="user@example.com",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_used=True
        )
        assert token.is_valid() is False
    
    def test_token_is_invalid_when_expired(self):
        """Test that an expired token is invalid."""
        token = PasswordResetToken(
            token="test_token",
            user_email="user@example.com",
            created_at=datetime.utcnow() - timedelta(hours=2),
            expires_at=datetime.utcnow() - timedelta(hours=1),
            is_used=False
        )
        assert token.is_valid() is False


class TestTokenStorage:
    """Tests for TokenStorage class."""
    
    def test_store_and_retrieve_token(self):
        """Test storing and retrieving a token."""
        storage = TokenStorage()
        token = PasswordResetToken(
            token="test_token",
            user_email="user@example.com",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        storage.store(token)
        retrieved = storage.get("test_token")
        
        assert retrieved is not None
        assert retrieved.token == "test_token"
        assert retrieved.user_email == "user@example.com"
    
    def test_get_nonexistent_token_returns_none(self):
        """Test that getting a non-existent token returns None."""
        storage = TokenStorage()
        assert storage.get("nonexistent") is None
    
    def test_mark_token_as_used(self):
        """Test marking a token as used."""
        storage = TokenStorage()
        token = PasswordResetToken(
            token="test_token",
            user_email="user@example.com",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        storage.store(token)
        result = storage.mark_as_used("test_token")
        
        assert result is True
        assert storage.get("test_token").is_used is True
    
    def test_mark_nonexistent_token_as_used_returns_false(self):
        """Test that marking a non-existent token returns False."""
        storage = TokenStorage()
        assert storage.mark_as_used("nonexistent") is False
    
    def test_cleanup_expired_tokens(self):
        """Test that expired tokens are removed during cleanup."""
        storage = TokenStorage()
        
        # Add valid token
        valid_token = PasswordResetToken(
            token="valid_token",
            user_email="user@example.com",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        storage.store(valid_token)
        
        # Add expired token
        expired_token = PasswordResetToken(
            token="expired_token",
            user_email="user2@example.com",
            created_at=datetime.utcnow() - timedelta(hours=2),
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        storage.store(expired_token)
        
        storage.cleanup_expired()
        
        assert storage.get("valid_token") is not None
        assert storage.get("expired_token") is None


class TestEmailService:
    """Tests for EmailService class."""
    
    @patch('src.auth.password_reset.smtplib.SMTP')
    def test_send_reset_email_success(self, mock_smtp):
        """Test successful email sending."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="password",
            from_email="noreply@example.com"
        )
        
        result = service.send_reset_email(
            to_email="recipient@example.com",
            reset_token="test_token_123",
            reset_url_base="https://example.com/reset"
        )
        
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user@example.com", "password")
        mock_server.send_message.assert_called_once()
    
    @patch('src.auth.password_reset.smtplib.SMTP')
    def test_send_reset_email_failure(self, mock_smtp):
        """Test email sending failure."""
        mock_smtp.side_effect = Exception("SMTP error")
        
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="password",
            from_email="noreply@example.com"
        )
        
        result = service.send_reset_email(
            to_email="recipient@example.com",
            reset_token="test_token_123",
            reset_url_base="https://example.com/reset"
        )
        
        assert result is False


class TestPasswordResetService:
    """Tests for PasswordResetService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.token_storage = TokenStorage()
        self.email_service = Mock(spec=EmailService)
        self.service = PasswordResetService(
            token_storage=self.token_storage,
            email_service=self.email_service,
            token_expiry_hours=1
        )
    
    def test_generate_reset_token(self):
        """Test that generated tokens are non-empty and unique."""
        token1 = self.service.generate_reset_token()
        token2 = self.service.generate_reset_token()
        
        assert len(token1) > 0
        assert len(token2) > 0
        assert token1 != token2
    
    def test_request_password_reset_success(self):
        """Test successful password reset request."""
        self.email_service.send_reset_email.return_value = True
        
        result = self.service.request_password_reset(
            user_email="user@example.com",
            reset_url_base="https://example.com/reset"
        )
        
        assert result["success"] is True
        assert "token" in result
        assert result["message"] == "Password reset email sent successfully"
        
        # Verify email was sent
        self.email_service.send_reset_email.assert_called_once()
        
        # Verify token was stored
        token = result["token"]
        stored_token = self.token_storage.get(token)
        assert stored_token is not None
        assert stored_token.user_email == "user@example.com"
    
    def test_request_password_reset_invalid_email(self):
        """Test password reset with invalid email."""
        result = self.service.request_password_reset(
            user_email="invalid_email",
            reset_url_base="https://example.com/reset"
        )
        
        assert result["success"] is False
        assert result["message"] == "Invalid email address"
        self.email_service.send_reset_email.assert_not_called()
    
    def test_request_password_reset_empty_email(self):
        """Test password reset with empty email."""
        result = self.service.request_password_reset(
            user_email="",
            reset_url_base="https://example.com/reset"
        )
        
        assert result["success"] is False
        assert result["message"] == "Invalid email address"
    
    def test_request_password_reset_email_failure(self):
        """Test password reset when email fails to send."""
        self.email_service.send_reset_email.return_value = False
        
        result = self.service.request_password_reset(
            user_email="user@example.com",
            reset_url_base="https://example.com/reset"
        )
        
        assert result["success"] is False
        assert result["message"] == "Failed to send reset email"
    
    def test_validate_reset_token_valid(self):
        """Test validating a valid token."""
        # Create and store a token
        token = PasswordResetToken(
            token="valid_token",
            user_email="user@example.com",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_used=False
        )
        self.token_storage.store(token)
        
        result = self.service.validate_reset_token("valid_token")
        
        assert result["valid"] is True
        assert result["user_email"] == "user@example.com"
        assert result["message"] == "Token is valid"
    
    def test_validate_reset_token_nonexistent(self):
        """Test validating a non-existent token."""
        result = self.service.validate_reset_token("nonexistent_token")
        
        assert result["valid"] is False
        assert result["message"] == "Invalid token"
    
    def test_validate_reset_token_expired(self):
        """Test validating an expired token."""
        token = PasswordResetToken(
            token="expired_token",
            user_email="user@example.com",
            created_at=datetime.utcnow() - timedelta(hours=2),
            expires_at=datetime.utcnow() - timedelta(hours=1),
            is_used=False
        )
        self.token_storage.store(token)
        
        result = self.service.validate_reset_token("expired_token")
        
        assert result["valid"] is False
        assert result["message"] == "Token has expired or already been used"
    
    def test_validate_reset_token_already_used(self):
        """Test validating a token that has already been used."""
        token = PasswordResetToken(
            token="used_token",
            user_email="user@example.com",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_used=True
        )
        self.token_storage.store(token)
        
        result = self.service.validate_reset_token("used_token")
        
        assert result["valid"] is False
        assert result["message"] == "Token has expired or already been used"
    
    def test_mark_token_used(self):
        """Test marking a token as used."""
        token = PasswordResetToken(
            token="test_token",
            user_email="user@example.com",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_used=False
        )
        self.token_storage.store(token)
        
        result = self.service.mark_token_used("test_token")
        
        assert result is True
        assert self.token_storage.get("test_token").is_used is True


class TestCreatePasswordResetService:
    """Tests for the factory function."""
    
    @patch.dict('os.environ', {
        'SMTP_HOST': 'smtp.test.com',
        'SMTP_PORT': '587',
        'SMTP_USER': 'test@test.com',
        'SMTP_PASSWORD': 'testpass',
        'FROM_EMAIL': 'noreply@test.com',
        'TOKEN_EXPIRY_HOURS': '2'
    })
    def test_create_password_reset_service_with_env_vars(self):
        """Test creating service with environment variables."""
        service = create_password_reset_service()
        
        assert isinstance(service, PasswordResetService)
        assert service.token_expiry_hours == 2
        assert service.email_service.smtp_host == 'smtp.test.com'
        assert service.email_service.smtp_port == 587
    
    @patch.dict('os.environ', {}, clear=True)
    def test_create_password_reset_service_with_defaults(self):
        """Test creating service with default values."""
        service = create_password_reset_service()
        
        assert isinstance(service, PasswordResetService)
        assert service.token_expiry_hours == 1
        assert service.email_service.smtp_host == 'smtp.gmail.com'
        assert service.email_service.smtp_port == 587
