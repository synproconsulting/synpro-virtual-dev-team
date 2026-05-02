"""
Tests for JWT utilities with hardened secret key handling.

Tests SDT1-63: Harden JWT secret key handling
"""

import pytest
import os
import secrets
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
import jwt as pyjwt

from jwt_utils import (
    JWTManager,
    JWTConfigError,
    JWTValidationError,
    get_jwt_secret,
    get_jwt_algorithm,
    get_jwt_expiry_hours,
    _validate_secret_strength,
    _is_production_environment,
    MIN_SECRET_LENGTH_BYTES,
    WEAK_SECRETS,
)


class TestSecretValidation:
    """Test JWT secret validation logic."""
    
    def test_weak_known_secrets_rejected(self):
        """Known weak secrets should be rejected."""
        for weak_secret in WEAK_SECRETS:
            with pytest.raises(JWTConfigError, match="known weak secret"):
                _validate_secret_strength(weak_secret)
    
    def test_short_secret_rejected(self):
        """Secrets shorter than minimum length should be rejected."""
        short_secret = "short"
        with pytest.raises(JWTConfigError, match="too short"):
            _validate_secret_strength(short_secret)
    
    def test_repetitive_secret_rejected_in_production(self):
        """Repetitive secrets should be rejected in production."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            repetitive = "a" * 50
            with pytest.raises(JWTConfigError, match="repetitive"):
                _validate_secret_strength(repetitive)
    
    def test_strong_secret_accepted(self):
        """Strong secrets should pass validation."""
        strong_secret = secrets.token_urlsafe(32)
        # Should not raise
        _validate_secret_strength(strong_secret)
    
    def test_minimum_length_secret_accepted(self):
        """Secret at minimum length should be accepted."""
        min_secret = "a" * MIN_SECRET_LENGTH_BYTES
        # In development, this should pass
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            _validate_secret_strength(min_secret)


class TestEnvironmentDetection:
    """Test environment detection logic."""
    
    def test_production_environment_detected(self):
        """Production environment should be detected."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            assert _is_production_environment() is True
    
    def test_development_environment_detected(self):
        """Development environment should be detected."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            assert _is_production_environment() is False
    
    def test_default_is_production(self):
        """Default environment should be production."""
        with patch.dict(os.environ, {}, clear=True):
            assert _is_production_environment() is True


class TestGetJWTSecret:
    """Test get_jwt_secret function."""
    
    def test_missing_secret_in_production_raises_error(self):
        """Missing JWT_SECRET in production should raise error."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
            with pytest.raises(JWTConfigError, match="required in production"):
                get_jwt_secret()
    
    def test_missing_secret_in_development_generates_temporary(self):
        """Missing JWT_SECRET in development should generate temporary secret."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            secret = get_jwt_secret()
            assert len(secret) >= MIN_SECRET_LENGTH_BYTES
    
    def test_weak_secret_rejected(self):
        """Weak JWT_SECRET should be rejected."""
        with patch.dict(os.environ, {"JWT_SECRET": "secret", "ENVIRONMENT": "production"}):
            with pytest.raises(JWTConfigError, match="known weak secret"):
                get_jwt_secret()
    
    def test_strong_secret_accepted(self):
        """Strong JWT_SECRET should be accepted."""
        strong_secret = secrets.token_urlsafe(32)
        with patch.dict(os.environ, {"JWT_SECRET": strong_secret, "ENVIRONMENT": "production"}):
            secret = get_jwt_secret()
            assert secret == strong_secret


class TestGetJWTAlgorithm:
    """Test get_jwt_algorithm function."""
    
    def test_default_algorithm_is_hs256(self):
        """Default algorithm should be HS256."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_jwt_algorithm() == "HS256"
    
    def test_allowed_algorithms_accepted(self):
        """Allowed algorithms should be accepted."""
        for alg in ["HS256", "HS384", "HS512"]:
            with patch.dict(os.environ, {"JWT_ALGORITHM": alg}):
                assert get_jwt_algorithm() == alg
    
    def test_disallowed_algorithm_rejected(self):
        """Disallowed algorithms should be rejected."""
        with patch.dict(os.environ, {"JWT_ALGORITHM": "none"}):
            with pytest.raises(JWTConfigError, match="not allowed"):
                get_jwt_algorithm()
        
        with patch.dict(os.environ, {"JWT_ALGORITHM": "RS256"}):
            with pytest.raises(JWTConfigError, match="not allowed"):
                get_jwt_algorithm()


class TestGetJWTExpiry:
    """Test get_jwt_expiry_hours function."""
    
    def test_default_expiry_is_24_hours(self):
        """Default expiry should be 24 hours."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_jwt_expiry_hours() == 24
    
    def test_custom_expiry_accepted(self):
        """Custom expiry values should be accepted."""
        with patch.dict(os.environ, {"JWT_EXPIRY_HOURS": "48"}):
            assert get_jwt_expiry_hours() == 48
    
    def test_invalid_expiry_rejected(self):
        """Invalid expiry values should be rejected."""
        with patch.dict(os.environ, {"JWT_EXPIRY_HOURS": "invalid"}):
            with pytest.raises(JWTConfigError, match="must be an integer"):
                get_jwt_expiry_hours()
        
        with patch.dict(os.environ, {"JWT_EXPIRY_HOURS": "0"}):
            with pytest.raises(JWTConfigError, match="at least 1 hour"):
                get_jwt_expiry_hours()


class TestJWTManager:
    """Test JWTManager class."""
    
    @pytest.fixture
    def jwt_manager(self):
        """Create a JWT manager with a test secret."""
        test_secret = secrets.token_urlsafe(32)
        with patch.dict(os.environ, {
            "JWT_SECRET": test_secret,
            "ENVIRONMENT": "development",
            "JWT_EXPIRY_HOURS": "1",
        }):
            return JWTManager()
    
    def test_create_token(self, jwt_manager):
        """Should create a valid JWT token."""
        user_id = "user123"
        email = "test@example.com"
        
        token = jwt_manager.create_token(user_id, email)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify
        payload = pyjwt.decode(
            token,
            jwt_manager.secret,
            algorithms=[jwt_manager.algorithm]
        )
        assert payload["sub"] == user_id
        assert payload["email"] == email
        assert "iat" in payload
        assert "exp" in payload
    
    def test_create_token_with_extra_claims(self, jwt_manager):
        """Should create token with extra claims."""
        user_id = "user123"
        email = "test@example.com"
        extra_claims = {"role": "admin", "permissions": ["read", "write"]}
        
        token = jwt_manager.create_token(user_id, email, **extra_claims)
        
        payload = pyjwt.decode(
            token,
            jwt_manager.secret,
            algorithms=[jwt_manager.algorithm]
        )
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]
    
    def test_decode_token(self, jwt_manager):
        """Should decode a valid token."""
        user_id = "user123"
        email = "test@example.com"
        
        token = jwt_manager.create_token(user_id, email)
        payload = jwt_manager.decode_token(token)
        
        assert payload["sub"] == user_id
        assert payload["email"] == email
    
    def test_decode_expired_token_raises_error(self, jwt_manager):
        """Expired token should raise JWTValidationError."""
        # Create an expired token
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "iat": past_time,
            "exp": past_time + timedelta(hours=1),
        }
        token = pyjwt.encode(payload, jwt_manager.secret, algorithm=jwt_manager.algorithm)
        
        with pytest.raises(JWTValidationError, match="expired"):
            jwt_manager.decode_token(token)
    
    def test_decode_invalid_token_raises_error(self, jwt_manager):
        """Invalid token should raise JWTValidationError."""
        invalid_token = "not.a.valid.token"
        
        with pytest.raises(JWTValidationError, match="Invalid token"):
            jwt_manager.decode_token(invalid_token)
    
    def test_decode_tampered_token_raises_error(self, jwt_manager):
        """Tampered token should raise JWTValidationError."""
        token = jwt_manager.create_token("user123", "test@example.com")
        
        # Tamper with the token
        parts = token.split(".")
        tampered_token = f"{parts[0]}.{parts[1]}.tampered"
        
        with pytest.raises(JWTValidationError, match="Invalid token"):
            jwt_manager.decode_token(tampered_token)
    
    def test_refresh_token(self, jwt_manager):
        """Should refresh a valid token."""
        user_id = "user123"
        email = "test@example.com"
        
        old_token = jwt_manager.create_token(user_id, email)
        new_token = jwt_manager.refresh_token(old_token)
        
        # Tokens should be different
        assert old_token != new_token
        
        # New token should have same claims
        new_payload = jwt_manager.decode_token(new_token)
        assert new_payload["sub"] == user_id
        assert new_payload["email"] == email
        
        # New token should have newer expiry
        old_payload = jwt_manager.decode_token(old_token)
        assert new_payload["exp"] > old_payload["exp"]
    
    def test_refresh_expired_token_allowed(self, jwt_manager):
        """Should allow refreshing an expired token."""
        # Create an expired token
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "iat": past_time,
            "exp": past_time + timedelta(hours=1),
        }
        expired_token = pyjwt.encode(
            payload,
            jwt_manager.secret,
            algorithm=jwt_manager.algorithm
        )
        
        # Should be able to refresh expired token
        new_token = jwt_manager.refresh_token(expired_token)
        new_payload = jwt_manager.decode_token(new_token)
        
        assert new_payload["sub"] == "user123"
        assert new_payload["email"] == "test@example.com"
    
    def test_refresh_invalid_token_raises_error(self, jwt_manager):
        """Refreshing invalid token should raise error."""
        invalid_token = "not.a.valid.token"
        
        with pytest.raises(JWTValidationError):
            jwt_manager.refresh_token(invalid_token)


class TestKeyRotation:
    """Test JWT key rotation functionality."""
    
    def test_decode_with_old_secret(self):
        """Should decode tokens signed with old secret during rotation."""
        old_secret = secrets.token_urlsafe(32)
        new_secret = secrets.token_urlsafe(32)
        
        # Create token with old secret
        old_manager = JWTManager()
        old_manager.secret = old_secret
        old_manager.algorithm = "HS256"
        old_manager.expiry_hours = 1
        
        token = old_manager.create_token("user123", "test@example.com")
        
        # Create new manager with both secrets
        with patch.dict(os.environ, {
            "JWT_SECRET": new_secret,
            "JWT_SECRET_OLD": old_secret,
            "ENVIRONMENT": "development",
        }):
            new_manager = JWTManager()
            
            # Should be able to decode token signed with old secret
            payload = new_manager.decode_token(token)
            assert payload["sub"] == "user123"
    
    def test_invalid_old_secret_ignored(self):
        """Invalid old secret should be ignored (not break the manager)."""
        new_secret = secrets.token_urlsafe(32)
        
        with patch.dict(os.environ, {
            "JWT_SECRET": new_secret,
            "JWT_SECRET_OLD": "weak",  # Invalid old secret
            "ENVIRONMENT": "development",
        }):
            # Should not raise, just log warning
            manager = JWTManager()
            assert manager.old_secret == ""  # Should be cleared


class TestSecurityProperties:
    """Test security properties of JWT implementation."""
    
    def test_algorithm_confusion_prevention(self, jwt_manager=None):
        """Should prevent algorithm confusion attacks."""
        if jwt_manager is None:
            test_secret = secrets.token_urlsafe(32)
            with patch.dict(os.environ, {
                "JWT_SECRET": test_secret,
                "ENVIRONMENT": "development",
            }):
                jwt_manager = JWTManager()
        
        # Create a token
        token = jwt_manager.create_token("user123", "test@example.com")
        
        # Try to decode with different algorithm
        with pytest.raises(JWTValidationError):
            # Manually create token with 'none' algorithm
            payload = {"sub": "attacker", "email": "attacker@example.com"}
            fake_token = pyjwt.encode(payload, "", algorithm="none")
            jwt_manager.decode_token(fake_token)
    
    def test_token_expiry_enforced(self):
        """Token expiry should be enforced by default."""
        test_secret = secrets.token_urlsafe(32)
        with patch.dict(os.environ, {
            "JWT_SECRET": test_secret,
            "ENVIRONMENT": "development",
            "JWT_EXPIRY_HOURS": "1",
        }):
            jwt_manager = JWTManager()
        
        # Create expired token
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "iat": past_time,
            "exp": past_time + timedelta(hours=1),
        }
        token = pyjwt.encode(payload, jwt_manager.secret, algorithm="HS256")
        
        # Should raise error when decoding expired token
        with pytest.raises(JWTValidationError, match="expired"):
            jwt_manager.decode_token(token)
    
    def test_signature_verification_enforced(self):
        """Signature verification should always be enforced."""
        test_secret = secrets.token_urlsafe(32)
        wrong_secret = secrets.token_urlsafe(32)
        
        with patch.dict(os.environ, {
            "JWT_SECRET": test_secret,
            "ENVIRONMENT": "development",
        }):
            jwt_manager = JWTManager()
        
        # Create token with different secret
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = pyjwt.encode(payload, wrong_secret, algorithm="HS256")
        
        # Should raise error due to signature mismatch
        with pytest.raises(JWTValidationError, match="Invalid token"):
            jwt_manager.decode_token(token)


class TestIntegration:
    """Integration tests for JWT workflow."""
    
    def test_full_token_lifecycle(self):
        """Test complete token lifecycle: create, decode, refresh."""
        test_secret = secrets.token_urlsafe(32)
        with patch.dict(os.environ, {
            "JWT_SECRET": test_secret,
            "ENVIRONMENT": "development",
            "JWT_EXPIRY_HOURS": "24",
        }):
            jwt_manager = JWTManager()
        
        # Create token
        user_id = "user123"
        email = "test@example.com"
        token = jwt_manager.create_token(user_id, email, role="admin")
        
        # Decode token
        payload = jwt_manager.decode_token(token)
        assert payload["sub"] == user_id
        assert payload["email"] == email
        assert payload["role"] == "admin"
        
        # Refresh token
        new_token = jwt_manager.refresh_token(token)
        new_payload = jwt_manager.decode_token(new_token)
        assert new_payload["sub"] == user_id
        assert new_payload["email"] == email
        assert new_payload["role"] == "admin"
        assert new_payload["exp"] > payload["exp"]
