"""
Unit tests for JWT token refresh mechanism.
"""

import os
from datetime import datetime, timedelta
from time import sleep

import pytest
from jose import jwt

from src.auth.jwt_refresh import JWTTokenManager, TokenRefreshError


class TestJWTTokenManager:
    """Test suite for JWTTokenManager class."""
    
    @pytest.fixture
    def token_manager(self):
        """Create a JWTTokenManager instance for testing."""
        return JWTTokenManager(
            secret_key="test_secret_key_12345",
            access_token_expire_minutes=15,
            refresh_token_expire_days=7
        )
    
    def test_initialization_with_secret_key(self):
        """Test manager initialization with explicit secret key."""
        manager = JWTTokenManager(secret_key="test_key")
        assert manager.secret_key == "test_key"
        assert manager.algorithm == "HS256"
    
    def test_initialization_with_env_var(self, monkeypatch):
        """Test manager initialization with environment variable."""
        monkeypatch.setenv("JWT_SECRET_KEY", "env_secret_key")
        manager = JWTTokenManager()
        assert manager.secret_key == "env_secret_key"
    
    def test_initialization_without_secret_raises_error(self, monkeypatch):
        """Test that initialization fails without secret key."""
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
        with pytest.raises(ValueError, match="Secret key must be provided"):
            JWTTokenManager()
    
    def test_create_access_token(self, token_manager):
        """Test access token creation."""
        token = token_manager.create_access_token("user123")
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify
        payload = jwt.decode(
            token, 
            "test_secret_key_12345", 
            algorithms=["HS256"]
        )
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_access_token_with_additional_claims(self, token_manager):
        """Test access token creation with additional claims."""
        additional_claims = {"role": "admin", "email": "user@example.com"}
        token = token_manager.create_access_token("user123", additional_claims)
        
        payload = jwt.decode(
            token, 
            "test_secret_key_12345", 
            algorithms=["HS256"]
        )
        assert payload["sub"] == "user123"
        assert payload["role"] == "admin"
        assert payload["email"] == "user@example.com"
    
    def test_create_refresh_token(self, token_manager):
        """Test refresh token creation."""
        token = token_manager.create_refresh_token("user123")
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify
        payload = jwt.decode(
            token, 
            "test_secret_key_12345", 
            algorithms=["HS256"]
        )
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_refresh_token_with_additional_claims(self, token_manager):
        """Test refresh token creation with additional claims."""
        additional_claims = {"role": "admin"}
        token = token_manager.create_refresh_token("user123", additional_claims)
        
        payload = jwt.decode(
            token, 
            "test_secret_key_12345", 
            algorithms=["HS256"]
        )
        assert payload["sub"] == "user123"
        assert payload["role"] == "admin"
    
    def test_create_token_pair(self, token_manager):
        """Test creating both access and refresh tokens."""
        access_token, refresh_token = token_manager.create_token_pair("user123")
        
        assert access_token is not None
        assert refresh_token is not None
        
        # Verify access token
        access_payload = jwt.decode(
            access_token, 
            "test_secret_key_12345", 
            algorithms=["HS256"]
        )
        assert access_payload["type"] == "access"
        
        # Verify refresh token
        refresh_payload = jwt.decode(
            refresh_token, 
            "test_secret_key_12345", 
            algorithms=["HS256"]
        )
        assert refresh_payload["type"] == "refresh"
    
    def test_decode_token(self, token_manager):
        """Test token decoding."""
        token = token_manager.create_access_token("user123")
        payload = token_manager.decode_token(token)
        
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"
    
    def test_decode_invalid_token_raises_error(self, token_manager):
        """Test that decoding invalid token raises error."""
        with pytest.raises(TokenRefreshError, match="Invalid token"):
            token_manager.decode_token("invalid_token")
    
    def test_decode_token_with_wrong_secret_raises_error(self, token_manager):
        """Test that decoding with wrong secret raises error."""
        # Create token with different manager
        other_manager = JWTTokenManager(secret_key="different_secret")
        token = other_manager.create_access_token("user123")
        
        with pytest.raises(TokenRefreshError, match="Invalid token"):
            token_manager.decode_token(token)
    
    def test_verify_refresh_token(self, token_manager):
        """Test refresh token verification."""
        refresh_token = token_manager.create_refresh_token("user123")
        subject = token_manager.verify_refresh_token(refresh_token)
        
        assert subject == "user123"
    
    def test_verify_access_token_as_refresh_raises_error(self, token_manager):
        """Test that verifying access token as refresh token raises error."""
        access_token = token_manager.create_access_token("user123")
        
        with pytest.raises(TokenRefreshError, match="not a refresh token"):
            token_manager.verify_refresh_token(access_token)
    
    def test_refresh_access_token(self, token_manager):
        """Test refreshing access token using refresh token."""
        refresh_token = token_manager.create_refresh_token("user123")
        new_access_token = token_manager.refresh_access_token(refresh_token)
        
        payload = token_manager.decode_token(new_access_token)
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"
    
    def test_refresh_access_token_preserves_claims(self, token_manager):
        """Test that refreshing preserves additional claims."""
        refresh_token = token_manager.create_refresh_token(
            "user123", 
            {"role": "admin"}
        )
        new_access_token = token_manager.refresh_access_token(refresh_token)
        
        payload = token_manager.decode_token(new_access_token)
        assert payload["sub"] == "user123"
        assert payload["role"] == "admin"
    
    def test_refresh_access_token_with_new_claims(self, token_manager):
        """Test refreshing with new additional claims."""
        refresh_token = token_manager.create_refresh_token("user123")
        new_access_token = token_manager.refresh_access_token(
            refresh_token, 
            {"role": "editor"}
        )
        
        payload = token_manager.decode_token(new_access_token)
        assert payload["sub"] == "user123"
        assert payload["role"] == "editor"
    
    def test_refresh_token_pair(self, token_manager):
        """Test refreshing both access and refresh tokens."""
        old_refresh_token = token_manager.create_refresh_token("user123")
        new_access, new_refresh = token_manager.refresh_token_pair(
            old_refresh_token
        )
        
        # Verify new access token
        access_payload = token_manager.decode_token(new_access)
        assert access_payload["sub"] == "user123"
        assert access_payload["type"] == "access"
        
        # Verify new refresh token
        refresh_payload = token_manager.decode_token(new_refresh)
        assert refresh_payload["sub"] == "user123"
        assert refresh_payload["type"] == "refresh"
    
    def test_get_token_expiry(self, token_manager):
        """Test getting token expiration time."""
        token = token_manager.create_access_token("user123")
        expiry = token_manager.get_token_expiry(token)
        
        assert isinstance(expiry, datetime)
        # Should expire in approximately 15 minutes
        expected_expiry = datetime.utcnow() + timedelta(minutes=15)
        assert abs((expiry - expected_expiry).total_seconds()) < 5
    
    def test_is_token_expired_with_valid_token(self, token_manager):
        """Test checking if valid token is expired."""
        token = token_manager.create_access_token("user123")
        assert not token_manager.is_token_expired(token)
    
    def test_is_token_expired_with_expired_token(self):
        """Test checking if expired token is expired."""
        # Create manager with very short expiration
        manager = JWTTokenManager(
            secret_key="test_secret_key_12345",
            access_token_expire_minutes=0  # Expires immediately
        )
        token = manager.create_access_token("user123")
        
        # Wait a moment to ensure expiration
        sleep(1)
        
        assert manager.is_token_expired(token)
    
    def test_is_token_expired_with_invalid_token(self, token_manager):
        """Test that invalid token is considered expired."""
        assert token_manager.is_token_expired("invalid_token")
    
    def test_access_token_expiry_time(self, token_manager):
        """Test that access token has correct expiration time."""
        token = token_manager.create_access_token("user123")
        payload = token_manager.decode_token(token)
        
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        
        diff = exp_time - iat_time
        # Should be approximately 15 minutes
        assert abs(diff.total_seconds() - (15 * 60)) < 5
    
    def test_refresh_token_expiry_time(self, token_manager):
        """Test that refresh token has correct expiration time."""
        token = token_manager.create_refresh_token("user123")
        payload = token_manager.decode_token(token)
        
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        
        diff = exp_time - iat_time
        # Should be approximately 7 days
        expected_seconds = 7 * 24 * 60 * 60
        assert abs(diff.total_seconds() - expected_seconds) < 5
    
    def test_custom_expiration_times(self):
        """Test creating manager with custom expiration times."""
        manager = JWTTokenManager(
            secret_key="test_secret_key_12345",
            access_token_expire_minutes=30,
            refresh_token_expire_days=14
        )
        
        access_token = manager.create_access_token("user123")
        refresh_token = manager.create_refresh_token("user123")
        
        access_payload = manager.decode_token(access_token)
        refresh_payload = manager.decode_token(refresh_token)
        
        # Verify access token expiration
        access_exp = datetime.fromtimestamp(access_payload["exp"])
        access_iat = datetime.fromtimestamp(access_payload["iat"])
        access_diff = access_exp - access_iat
        assert abs(access_diff.total_seconds() - (30 * 60)) < 5
        
        # Verify refresh token expiration
        refresh_exp = datetime.fromtimestamp(refresh_payload["exp"])
        refresh_iat = datetime.fromtimestamp(refresh_payload["iat"])
        refresh_diff = refresh_exp - refresh_iat
        assert abs(refresh_diff.total_seconds() - (14 * 24 * 60 * 60)) < 5
