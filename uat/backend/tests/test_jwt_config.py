"""
Tests for JWT configuration module (SDT1-63).

Tests hardened JWT secret key handling, validation, and key rotation.
"""

import pytest
import os
import jwt as pyjwt
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from jwt_config import (
    JWTConfig,
    JWTConfigError,
    JWTKeyValidationError,
    get_jwt_config,
    generate_secure_secret,
    _validate_jwt_secret,
    _calculate_entropy,
)


class TestEntropyCalculation:
    """Test entropy calculation for secret validation."""
    
    def test_entropy_empty_string(self):
        """Empty string has zero entropy."""
        assert _calculate_entropy("") == 0.0
    
    def test_entropy_single_char(self):
        """Single repeated character has zero entropy."""
        assert _calculate_entropy("aaaaaaaaaa") == 0.0
    
    def test_entropy_random_string(self):
        """Random string has high entropy."""
        random = "aB3$xY9#mK2@pQ7!"
        entropy = _calculate_entropy(random)
        assert entropy > 3.0  # Should be reasonably high
    
    def test_entropy_sequential(self):
        """Sequential characters have moderate entropy."""
        sequential = "abcdefghijklmnop"
        entropy = _calculate_entropy(sequential)
        assert entropy > 2.0


class TestSecretValidation:
    """Test JWT secret key validation."""
    
    def test_empty_secret_rejected(self):
        """Empty secret is rejected."""
        with pytest.raises(JWTKeyValidationError, match="cannot be empty"):
            _validate_jwt_secret("")
    
    def test_short_secret_rejected(self):
        """Secret shorter than minimum length is rejected."""
        with pytest.raises(JWTKeyValidationError, match="at least 32 characters"):
            _validate_jwt_secret("short")
    
    def test_weak_secret_rejected(self):
        """Common weak secrets are rejected."""
        weak_secrets = [
            "secret1234567890123456789012345",
            "dev-secret-change-in-production1234",
            "test-secret123456789012345678901",
        ]
        for weak in weak_secrets:
            with pytest.raises(JWTKeyValidationError, match="weak/common pattern"):
                _validate_jwt_secret(weak)
    
    def test_low_diversity_rejected(self):
        """Secret with low character diversity is rejected."""
        with pytest.raises(JWTKeyValidationError, match="character diversity"):
            _validate_jwt_secret("a" * 50)
    
    def test_strong_secret_accepted(self):
        """Strong random secret is accepted."""
        strong = generate_secure_secret()
        # Should not raise
        _validate_jwt_secret(strong)
    
    def test_custom_min_length(self):
        """Custom minimum length can be specified."""
        secret = "a" * 15 + "B3$xY9#mK2@pQ7!"
        # Fails with default min_length=32
        with pytest.raises(JWTKeyValidationError):
            _validate_jwt_secret(secret, min_length=32)
        # Passes with min_length=16
        _validate_jwt_secret(secret, min_length=16)


class TestSecretGeneration:
    """Test secure secret generation."""
    
    def test_generate_default_length(self):
        """Default secret generation produces valid secret."""
        secret = generate_secure_secret()
        assert len(secret) >= 32
        _validate_jwt_secret(secret)
    
    def test_generate_custom_length(self):
        """Custom length secret generation."""
        secret = generate_secure_secret(length=64)
        assert len(secret) >= 64
        _validate_jwt_secret(secret)
    
    def test_generate_unique(self):
        """Generated secrets are unique."""
        secrets = [generate_secure_secret() for _ in range(10)]
        assert len(set(secrets)) == 10


class TestJWTConfigInitialization:
    """Test JWT configuration initialization."""
    
    def test_missing_secret_fails(self):
        """Missing JWT_SECRET raises error."""
        with patch.dict(os.environ, {"JWT_SECRET": ""}, clear=True):
            with pytest.raises(JWTConfigError, match="JWT_SECRET environment variable is required"):
                JWTConfig()
    
    def test_weak_secret_fails(self):
        """Weak JWT_SECRET raises error."""
        with patch.dict(os.environ, {"JWT_SECRET": "weak-secret"}, clear=True):
            with pytest.raises(JWTKeyValidationError):
                JWTConfig()
    
    def test_valid_secret_succeeds(self):
        """Valid JWT_SECRET initializes successfully."""
        strong_secret = generate_secure_secret()
        with patch.dict(os.environ, {"JWT_SECRET": strong_secret}, clear=True):
            config = JWTConfig()
            assert config.primary_secret == strong_secret
            assert config.algorithm == "HS256"
            assert config.expiry_hours == 24  # default
    
    def test_custom_expiry(self):
        """Custom JWT expiry can be configured."""
        strong_secret = generate_secure_secret()
        with patch.dict(os.environ, {
            "JWT_SECRET": strong_secret,
            "JWT_EXPIRY_HOURS": "12"
        }, clear=True):
            config = JWTConfig()
            assert config.expiry_hours == 12
    
    def test_invalid_expiry_uses_default(self):
        """Invalid expiry value uses default."""
        strong_secret = generate_secure_secret()
        with patch.dict(os.environ, {
            "JWT_SECRET": strong_secret,
            "JWT_EXPIRY_HOURS": "invalid"
        }, clear=True):
            config = JWTConfig()
            assert config.expiry_hours == 24
    
    def test_too_short_expiry_fails(self):
        """Expiry less than 1 hour fails."""
        strong_secret = generate_secure_secret()
        with patch.dict(os.environ, {
            "JWT_SECRET": strong_secret,
            "JWT_EXPIRY_HOURS": "0"
        }, clear=True):
            with pytest.raises(JWTConfigError, match="at least 1 hour"):
                JWTConfig()


class TestKeyRotation:
    """Test JWT key rotation support."""
    
    def test_old_secrets_parsed(self):
        """Old secrets are parsed from environment."""
        primary = generate_secure_secret()
        old1 = generate_secure_secret()
        old2 = generate_secure_secret()
        
        with patch.dict(os.environ, {
            "JWT_SECRET": primary,
            "JWT_SECRET_OLD": f"{old1},{old2}"
        }, clear=True):
            config = JWTConfig()
            assert config.primary_secret == primary
            assert len(config.old_secrets) == 2
            assert old1 in config.old_secrets
            assert old2 in config.old_secrets
    
    def test_token_validates_with_old_secret(self):
        """Token created with old secret still validates."""
        primary = generate_secure_secret()
        old_secret = generate_secure_secret()
        
        # Create token with old secret
        old_payload = {
            "sub": "user123",
            "email": "test@example.com",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        old_token = pyjwt.encode(old_payload, old_secret, algorithm="HS256")
        
        # Validate with new config that has old secret
        with patch.dict(os.environ, {
            "JWT_SECRET": primary,
            "JWT_SECRET_OLD": old_secret
        }, clear=True):
            config = JWTConfig()
            payload = config.decode_token(old_token)
            assert payload["sub"] == "user123"
            assert payload["email"] == "test@example.com"
    
    def test_new_tokens_use_primary_secret(self):
        """New tokens are created with primary secret."""
        primary = generate_secure_secret()
        old_secret = generate_secure_secret()
        
        with patch.dict(os.environ, {
            "JWT_SECRET": primary,
            "JWT_SECRET_OLD": old_secret
        }, clear=True):
            config = JWTConfig()
            token = config.create_token("user123", "test@example.com")
            
            # Should validate with primary secret
            payload = pyjwt.decode(token, primary, algorithms=["HS256"])
            assert payload["sub"] == "user123"


class TestTokenCreation:
    """Test JWT token creation."""
    
    @pytest.fixture
    def config(self):
        """Create a test JWT config."""
        strong_secret = generate_secure_secret()
        with patch.dict(os.environ, {"JWT_SECRET": strong_secret}, clear=True):
            return JWTConfig()
    
    def test_create_basic_token(self, config):
        """Create a basic JWT token."""
        token = config.create_token("user123", "test@example.com")
        
        # Decode without verification to check structure
        payload = pyjwt.decode(token, options={"verify_signature": False})
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert "iat" in payload
        assert "exp" in payload
    
    def test_token_expiry_set_correctly(self, config):
        """Token expiry is set correctly."""
        token = config.create_token("user123", "test@example.com")
        payload = pyjwt.decode(token, options={"verify_signature": False})
        
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        
        # Should be approximately expiry_hours apart
        delta = exp - iat
        assert abs(delta.total_seconds() - config.expiry_hours * 3600) < 5
    
    def test_create_token_with_extra_claims(self, config):
        """Create token with extra claims."""
        token = config.create_token(
            "user123",
            "test@example.com",
            extra_claims={"role": "admin", "tier": "premium"}
        )
        
        payload = pyjwt.decode(token, options={"verify_signature": False})
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "admin"
        assert payload["tier"] == "premium"


class TestTokenDecoding:
    """Test JWT token decoding and validation."""
    
    @pytest.fixture
    def config(self):
        """Create a test JWT config."""
        strong_secret = generate_secure_secret()
        with patch.dict(os.environ, {"JWT_SECRET": strong_secret}, clear=True):
            return JWTConfig()
    
    def test_decode_valid_token(self, config):
        """Decode a valid token."""
        token = config.create_token("user123", "test@example.com")
        payload = config.decode_token(token)
        
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
    
    def test_decode_expired_token_fails(self, config):
        """Expired token raises ExpiredSignatureError."""
        # Create token that expired 1 hour ago
        past = datetime.now(timezone.utc) - timedelta(hours=2)
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "iat": past,
            "exp": past + timedelta(hours=1)
        }
        expired_token = pyjwt.encode(payload, config.primary_secret, algorithm="HS256")
        
        with pytest.raises(pyjwt.ExpiredSignatureError):
            config.decode_token(expired_token)
    
    def test_decode_invalid_signature_fails(self, config):
        """Token with invalid signature fails."""
        wrong_secret = generate_secure_secret()
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        bad_token = pyjwt.encode(payload, wrong_secret, algorithm="HS256")
        
        with pytest.raises(pyjwt.InvalidTokenError):
            config.decode_token(bad_token)
    
    def test_decode_malformed_token_fails(self, config):
        """Malformed token fails."""
        with pytest.raises(pyjwt.InvalidTokenError):
            config.decode_token("not.a.valid.token")
    
    def test_decode_without_verification(self, config):
        """Decode without verification skips checks."""
        # Create expired token
        past = datetime.now(timezone.utc) - timedelta(hours=2)
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "iat": past,
            "exp": past + timedelta(hours=1)
        }
        expired_token = pyjwt.encode(payload, config.primary_secret, algorithm="HS256")
        
        # Should work with verify=False
        decoded = config.decode_token(expired_token, verify=False)
        assert decoded["sub"] == "user123"


class TestTokenValidation:
    """Test high-level token validation method."""
    
    @pytest.fixture
    def config(self):
        """Create a test JWT config."""
        strong_secret = generate_secure_secret()
        with patch.dict(os.environ, {"JWT_SECRET": strong_secret}, clear=True):
            return JWTConfig()
    
    def test_validate_valid_token(self, config):
        """Valid token returns success."""
        token = config.create_token("user123", "test@example.com")
        is_valid, payload, error = config.validate_token(token)
        
        assert is_valid is True
        assert payload["sub"] == "user123"
        assert error is None
    
    def test_validate_expired_token(self, config):
        """Expired token returns error."""
        past = datetime.now(timezone.utc) - timedelta(hours=2)
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "iat": past,
            "exp": past + timedelta(hours=1)
        }
        expired_token = pyjwt.encode(payload, config.primary_secret, algorithm="HS256")
        
        is_valid, payload, error = config.validate_token(expired_token)
        assert is_valid is False
        assert payload is None
        assert "expired" in error.lower()
    
    def test_validate_invalid_token(self, config):
        """Invalid token returns error."""
        is_valid, payload, error = config.validate_token("invalid.token.here")
        assert is_valid is False
        assert payload is None
        assert "invalid" in error.lower()


class TestGlobalConfig:
    """Test global JWT config singleton."""
    
    def test_get_jwt_config_singleton(self):
        """get_jwt_config returns singleton instance."""
        strong_secret = generate_secure_secret()
        with patch.dict(os.environ, {"JWT_SECRET": strong_secret}, clear=True):
            config1 = get_jwt_config()
            config2 = get_jwt_config()
            assert config1 is config2
    
    def test_get_jwt_config_validates(self):
        """get_jwt_config validates configuration."""
        with patch.dict(os.environ, {"JWT_SECRET": "weak"}, clear=True):
            with pytest.raises(JWTKeyValidationError):
                get_jwt_config()


class TestSecurityFeatures:
    """Test security-related features."""
    
    def test_different_users_get_different_tokens(self):
        """Different users get different tokens."""
        strong_secret = generate_secure_secret()
        with patch.dict(os.environ, {"JWT_SECRET": strong_secret}, clear=True):
            config = JWTConfig()
            
            token1 = config.create_token("user1", "user1@example.com")
            token2 = config.create_token("user2", "user2@example.com")
            
            assert token1 != token2
    
    def test_same_user_gets_different_tokens_over_time(self):
        """Same user gets different tokens due to iat timestamp."""
        strong_secret = generate_secure_secret()
        with patch.dict(os.environ, {"JWT_SECRET": strong_secret}, clear=True):
            config = JWTConfig()
            
            token1 = config.create_token("user1", "user1@example.com")
            import time
            time.sleep(0.01)  # Ensure different timestamp
            token2 = config.create_token("user1", "user1@example.com")
            
            assert token1 != token2
    
    def test_token_cannot_be_modified(self):
        """Modified token fails validation."""
        strong_secret = generate_secure_secret()
        with patch.dict(os.environ, {"JWT_SECRET": strong_secret}, clear=True):
            config = JWTConfig()
            
            token = config.create_token("user1", "user1@example.com")
            
            # Decode without verification
            payload = pyjwt.decode(token, options={"verify_signature": False})
            # Modify payload
            payload["sub"] = "attacker"
            # Re-encode with same secret (to test signature verification)
            modified = pyjwt.encode(payload, "wrong-secret", algorithm="HS256")
            
            # Should fail validation
            with pytest.raises(pyjwt.InvalidTokenError):
                config.decode_token(modified)
