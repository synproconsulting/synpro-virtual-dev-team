"""
Unit tests for JWT token generation and validation.
"""

import os
import time
from datetime import timedelta

import pytest
from jose import JWTError
from jose.exceptions import ExpiredSignatureError

from src.auth.jwt_handler import JWTHandler


@pytest.fixture
def jwt_handler():
    """Create a JWT handler instance for testing."""
    return JWTHandler(
        secret_key="test-secret-key-12345",
        algorithm="HS256",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7,
    )


@pytest.fixture
def jwt_handler_short_expiry():
    """Create a JWT handler with short expiry for testing token expiration."""
    return JWTHandler(
        secret_key="test-secret-key-12345",
        algorithm="HS256",
        access_token_expire_minutes=0,  # Will be overridden with seconds
        refresh_token_expire_days=0,
    )


class TestJWTHandlerInitialization:
    """Tests for JWT handler initialization."""

    def test_initialization_with_secret_key(self):
        """Test that handler initializes correctly with a secret key."""
        handler = JWTHandler(secret_key="my-secret")
        assert handler.secret_key == "my-secret"
        assert handler.algorithm == "HS256"
        assert handler.access_token_expire_minutes == 30
        assert handler.refresh_token_expire_days == 7

    def test_initialization_with_env_var(self, monkeypatch):
        """Test that handler reads secret key from environment variable."""
        monkeypatch.setenv("SECRET_KEY", "env-secret-key")
        handler = JWTHandler()
        assert handler.secret_key == "env-secret-key"

    def test_initialization_without_secret_key_raises_error(self, monkeypatch):
        """Test that initialization fails without secret key."""
        monkeypatch.delenv("SECRET_KEY", raising=False)
        with pytest.raises(ValueError, match="SECRET_KEY must be provided"):
            JWTHandler()

    def test_custom_configuration(self):
        """Test handler with custom configuration."""
        handler = JWTHandler(
            secret_key="custom-secret",
            algorithm="HS512",
            access_token_expire_minutes=60,
            refresh_token_expire_days=14,
        )
        assert handler.algorithm == "HS512"
        assert handler.access_token_expire_minutes == 60
        assert handler.refresh_token_expire_days == 14


class TestAccessTokenGeneration:
    """Tests for access token generation."""

    def test_create_access_token(self, jwt_handler):
        """Test creating a basic access token."""
        token = jwt_handler.create_access_token(subject="user123")
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_contains_subject(self, jwt_handler):
        """Test that access token contains the correct subject."""
        token = jwt_handler.create_access_token(subject="user123")
        payload = jwt_handler.decode_token(token)
        assert payload["sub"] == "user123"

    def test_access_token_contains_type(self, jwt_handler):
        """Test that access token has correct type claim."""
        token = jwt_handler.create_access_token(subject="user123")
        payload = jwt_handler.decode_token(token)
        assert payload["type"] == "access"

    def test_access_token_with_additional_claims(self, jwt_handler):
        """Test creating access token with additional claims."""
        additional_claims = {"role": "admin", "permissions": ["read", "write"]}
        token = jwt_handler.create_access_token(
            subject="user123",
            additional_claims=additional_claims
        )
        payload = jwt_handler.decode_token(token)
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]

    def test_access_token_with_custom_expiry(self, jwt_handler):
        """Test creating access token with custom expiration."""
        custom_delta = timedelta(minutes=60)
        token = jwt_handler.create_access_token(
            subject="user123",
            expires_delta=custom_delta
        )
        payload = jwt_handler.decode_token(token)
        assert "exp" in payload


class TestRefreshTokenGeneration:
    """Tests for refresh token generation."""

    def test_create_refresh_token(self, jwt_handler):
        """Test creating a basic refresh token."""
        token = jwt_handler.create_refresh_token(subject="user123")
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_refresh_token_contains_subject(self, jwt_handler):
        """Test that refresh token contains the correct subject."""
        token = jwt_handler.create_refresh_token(subject="user123")
        payload = jwt_handler.decode_token(token)
        assert payload["sub"] == "user123"

    def test_refresh_token_contains_type(self, jwt_handler):
        """Test that refresh token has correct type claim."""
        token = jwt_handler.create_refresh_token(subject="user123")
        payload = jwt_handler.decode_token(token)
        assert payload["type"] == "refresh"

    def test_refresh_token_with_additional_claims(self, jwt_handler):
        """Test creating refresh token with additional claims."""
        additional_claims = {"device_id": "device-123"}
        token = jwt_handler.create_refresh_token(
            subject="user123",
            additional_claims=additional_claims
        )
        payload = jwt_handler.decode_token(token)
        assert payload["device_id"] == "device-123"


class TestTokenDecoding:
    """Tests for token decoding."""

    def test_decode_valid_token(self, jwt_handler):
        """Test decoding a valid token."""
        token = jwt_handler.create_access_token(subject="user123")
        payload = jwt_handler.decode_token(token)
        assert payload["sub"] == "user123"
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_invalid_token_raises_error(self, jwt_handler):
        """Test that decoding an invalid token raises JWTError."""
        with pytest.raises(JWTError):
            jwt_handler.decode_token("invalid.token.here")

    def test_decode_expired_token_raises_error(self, jwt_handler_short_expiry):
        """Test that decoding an expired token raises ExpiredSignatureError."""
        token = jwt_handler_short_expiry.create_access_token(
            subject="user123",
            expires_delta=timedelta(seconds=1)
        )
        time.sleep(2)
        with pytest.raises(ExpiredSignatureError):
            jwt_handler_short_expiry.decode_token(token)

    def test_decode_token_with_wrong_secret(self, jwt_handler):
        """Test that decoding with wrong secret fails."""
        token = jwt_handler.create_access_token(subject="user123")
        wrong_handler = JWTHandler(secret_key="wrong-secret")
        with pytest.raises(JWTError):
            wrong_handler.decode_token(token)


class TestTokenValidation:
    """Tests for token validation."""

    def test_validate_valid_token(self, jwt_handler):
        """Test validating a valid token."""
        token = jwt_handler.create_access_token(subject="user123")
        assert jwt_handler.validate_token(token) is True

    def test_validate_invalid_token(self, jwt_handler):
        """Test validating an invalid token."""
        assert jwt_handler.validate_token("invalid.token.here") is False

    def test_validate_expired_token(self, jwt_handler_short_expiry):
        """Test that expired token validation returns False."""
        token = jwt_handler_short_expiry.create_access_token(
            subject="user123",
            expires_delta=timedelta(seconds=1)
        )
        time.sleep(2)
        assert jwt_handler_short_expiry.validate_token(token) is False

    def test_validate_token_with_type_check(self, jwt_handler):
        """Test validating token with type verification."""
        access_token = jwt_handler.create_access_token(subject="user123")
        refresh_token = jwt_handler.create_refresh_token(subject="user123")
        
        assert jwt_handler.validate_token(access_token, token_type="access") is True
        assert jwt_handler.validate_token(access_token, token_type="refresh") is False
        assert jwt_handler.validate_token(refresh_token, token_type="refresh") is True
        assert jwt_handler.validate_token(refresh_token, token_type="access") is False


class TestTokenSubjectExtraction:
    """Tests for extracting subject from tokens."""

    def test_get_token_subject(self, jwt_handler):
        """Test extracting subject from a valid token."""
        token = jwt_handler.create_access_token(subject="user123")
        subject = jwt_handler.get_token_subject(token)
        assert subject == "user123"

    def test_get_token_subject_from_invalid_token(self, jwt_handler):
        """Test that extracting subject from invalid token returns None."""
        subject = jwt_handler.get_token_subject("invalid.token.here")
        assert subject is None

    def test_get_token_subject_from_expired_token(self, jwt_handler_short_expiry):
        """Test that extracting subject from expired token returns None."""
        token = jwt_handler_short_expiry.create_access_token(
            subject="user123",
            expires_delta=timedelta(seconds=1)
        )
        time.sleep(2)
        subject = jwt_handler_short_expiry.get_token_subject(token)
        assert subject is None


class TestRefreshAccessToken:
    """Tests for refreshing access tokens."""

    def test_refresh_access_token_with_valid_refresh_token(self, jwt_handler):
        """Test generating new access token from valid refresh token."""
        refresh_token = jwt_handler.create_refresh_token(subject="user123")
        new_access_token = jwt_handler.refresh_access_token(refresh_token)
        
        assert new_access_token is not None
        payload = jwt_handler.decode_token(new_access_token)
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"

    def test_refresh_access_token_with_invalid_token(self, jwt_handler):
        """Test that refreshing with invalid token returns None."""
        new_access_token = jwt_handler.refresh_access_token("invalid.token.here")
        assert new_access_token is None

    def test_refresh_access_token_with_access_token(self, jwt_handler):
        """Test that refreshing with access token (not refresh) returns None."""
        access_token = jwt_handler.create_access_token(subject="user123")
        new_access_token = jwt_handler.refresh_access_token(access_token)
        assert new_access_token is None

    def test_refresh_access_token_with_expired_refresh_token(self, jwt_handler_short_expiry):
        """Test that refreshing with expired refresh token returns None."""
        refresh_token = jwt_handler_short_expiry.create_refresh_token(
            subject="user123",
            expires_delta=timedelta(seconds=1)
        )
        time.sleep(2)
        new_access_token = jwt_handler_short_expiry.refresh_access_token(refresh_token)
        assert new_access_token is None
