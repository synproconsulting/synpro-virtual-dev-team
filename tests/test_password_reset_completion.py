"""
Unit tests for password reset completion functionality.
"""

import os
import pytest
from datetime import datetime, timedelta
import jwt
from pydantic import ValidationError

from src.auth.password_reset_completion import (
    PasswordResetCompletionService,
    PasswordResetRequest,
    PasswordResetResponse,
)


@pytest.fixture
def secret_key():
    """Fixture providing a test secret key."""
    return "test-secret-key-for-password-reset-testing-only"


@pytest.fixture
def service(secret_key):
    """Fixture providing a configured password reset service."""
    return PasswordResetCompletionService(secret_key=secret_key, token_expiry_hours=24)


@pytest.fixture
def mock_update_success():
    """Fixture providing a mock successful update callback."""
    def callback(user_id: str, hashed_password: str) -> bool:
        return True
    return callback


@pytest.fixture
def mock_update_failure():
    """Fixture providing a mock failed update callback."""
    def callback(user_id: str, hashed_password: str) -> bool:
        return False
    return callback


class TestPasswordResetRequest:
    """Tests for PasswordResetRequest model."""
    
    def test_valid_password_reset_request(self):
        """Test creating a valid password reset request."""
        request = PasswordResetRequest(
            token="valid-token",
            new_password="SecurePass123"
        )
        assert request.token == "valid-token"
        assert request.new_password == "SecurePass123"
    
    def test_password_too_short(self):
        """Test validation fails for passwords under 8 characters."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordResetRequest(
                token="valid-token",
                new_password="Short1"
            )
        assert "at least 8 characters" in str(exc_info.value)
    
    def test_password_no_uppercase(self):
        """Test validation fails when password lacks uppercase."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordResetRequest(
                token="valid-token",
                new_password="lowercase123"
            )
        assert "uppercase letter" in str(exc_info.value)
    
    def test_password_no_lowercase(self):
        """Test validation fails when password lacks lowercase."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordResetRequest(
                token="valid-token",
                new_password="UPPERCASE123"
            )
        assert "lowercase letter" in str(exc_info.value)
    
    def test_password_no_digit(self):
        """Test validation fails when password lacks digits."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordResetRequest(
                token="valid-token",
                new_password="NoDigitsHere"
            )
        assert "digit" in str(exc_info.value)


class TestPasswordResetCompletionService:
    """Tests for PasswordResetCompletionService."""
    
    def test_service_initialization(self, secret_key):
        """Test service initializes correctly with provided key."""
        service = PasswordResetCompletionService(secret_key=secret_key)
        assert service.secret_key == secret_key
        assert service.token_expiry_hours == 24
    
    def test_service_initialization_from_env(self, monkeypatch, secret_key):
        """Test service initializes from environment variable."""
        monkeypatch.setenv('JWT_SECRET_KEY', secret_key)
        service = PasswordResetCompletionService()
        assert service.secret_key == secret_key
    
    def test_service_initialization_no_key(self, monkeypatch):
        """Test service raises error when no secret key available."""
        monkeypatch.delenv('JWT_SECRET_KEY', raising=False)
        with pytest.raises(ValueError) as exc_info:
            PasswordResetCompletionService()
        assert "JWT_SECRET_KEY must be set" in str(exc_info.value)
    
    def test_generate_reset_token(self, service):
        """Test generating a valid reset token."""
        user_id = "user123"
        email = "test@example.com"
        
        token = service.generate_reset_token(user_id, email)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token can be decoded
        payload = jwt.decode(token, service.secret_key, algorithms=[service.algorithm])
        assert payload['user_id'] == user_id
        assert payload['email'] == email
        assert payload['type'] == 'password_reset'
    
    def test_verify_valid_token(self, service):
        """Test verifying a valid reset token."""
        user_id = "user123"
        email = "test@example.com"
        
        token = service.generate_reset_token(user_id, email)
        payload = service.verify_reset_token(token)
        
        assert payload['user_id'] == user_id
        assert payload['email'] == email
        assert payload['type'] == 'password_reset'
    
    def test_verify_expired_token(self, service, secret_key):
        """Test verifying an expired token raises error."""
        # Create expired token
        expiry = datetime.utcnow() - timedelta(hours=1)
        payload = {
            'user_id': 'user123',
            'email': 'test@example.com',
            'type': 'password_reset',
            'exp': expiry
        }
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        with pytest.raises(jwt.ExpiredSignatureError):
            service.verify_reset_token(token)
    
    def test_verify_invalid_token(self, service):
        """Test verifying an invalid token raises error."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(jwt.InvalidTokenError):
            service.verify_reset_token(invalid_token)
    
    def test_verify_wrong_token_type(self, service, secret_key):
        """Test verifying a token with wrong type raises error."""
        payload = {
            'user_id': 'user123',
            'email': 'test@example.com',
            'type': 'access_token',  # Wrong type
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        with pytest.raises(jwt.InvalidTokenError) as exc_info:
            service.verify_reset_token(token)
        assert "Invalid token type" in str(exc_info.value)
    
    def test_hash_password(self, service):
        """Test password hashing produces valid bcrypt hash."""
        password = "SecurePassword123"
        hashed = service.hash_password(password)
        
        assert hashed != password
        assert hashed.startswith('$2b$')  # bcrypt prefix
        assert service.pwd_context.verify(password, hashed)
    
    def test_complete_password_reset_success(self, service, mock_update_success):
        """Test successful password reset completion."""
        user_id = "user123"
        email = "test@example.com"
        token = service.generate_reset_token(user_id, email)
        
        request = PasswordResetRequest(
            token=token,
            new_password="NewSecure123"
        )
        
        response = service.complete_password_reset(request, mock_update_success)
        
        assert response.success is True
        assert "successfully" in response.message
        assert response.email == email
    
    def test_complete_password_reset_update_failure(self, service, mock_update_failure):
        """Test password reset when database update fails."""
        user_id = "user123"
        email = "test@example.com"
        token = service.generate_reset_token(user_id, email)
        
        request = PasswordResetRequest(
            token=token,
            new_password="NewSecure123"
        )
        
        response = service.complete_password_reset(request, mock_update_failure)
        
        assert response.success is False
        assert "Failed to update password" in response.message
    
    def test_complete_password_reset_expired_token(self, service, secret_key, mock_update_success):
        """Test password reset with expired token."""
        expiry = datetime.utcnow() - timedelta(hours=1)
        payload = {
            'user_id': 'user123',
            'email': 'test@example.com',
            'type': 'password_reset',
            'exp': expiry
        }
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        request = PasswordResetRequest(
            token=token,
            new_password="NewSecure123"
        )
        
        response = service.complete_password_reset(request, mock_update_success)
        
        assert response.success is False
        assert "expired" in response.message.lower()
    
    def test_complete_password_reset_invalid_token(self, service, mock_update_success):
        """Test password reset with invalid token."""
        request = PasswordResetRequest(
            token="invalid.token.string",
            new_password="NewSecure123"
        )
        
        response = service.complete_password_reset(request, mock_update_success)
        
        assert response.success is False
        assert "Invalid reset token" in response.message
    
    def test_complete_password_reset_weak_password(self, service, mock_update_success):
        """Test password reset with weak password."""
        user_id = "user123"
        email = "test@example.com"
        token = service.generate_reset_token(user_id, email)
        
        # This should fail validation before even creating request
        with pytest.raises(ValidationError):
            request = PasswordResetRequest(
                token=token,
                new_password="weak"
            )
    
    def test_complete_password_reset_missing_user_id(self, service, secret_key, mock_update_success):
        """Test password reset with token missing user_id."""
        payload = {
            'email': 'test@example.com',
            'type': 'password_reset',
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        request = PasswordResetRequest(
            token=token,
            new_password="NewSecure123"
        )
        
        response = service.complete_password_reset(request, mock_update_success)
        
        assert response.success is False
        assert "missing user information" in response.message
    
    def test_password_hash_uniqueness(self, service):
        """Test that same password produces different hashes (salt)."""
        password = "SamePassword123"
        hash1 = service.hash_password(password)
        hash2 = service.hash_password(password)
        
        assert hash1 != hash2
        assert service.pwd_context.verify(password, hash1)
        assert service.pwd_context.verify(password, hash2)
