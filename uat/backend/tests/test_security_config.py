"""
Tests for security_config module (SDT1-63: Harden JWT secret key handling).
"""

import pytest
import os
from unittest.mock import patch
from security_config import (
    get_jwt_secret,
    get_jwt_config,
    generate_secure_secret,
    _calculate_entropy,
    _validate_jwt_secret,
    SecurityConfigError,
)


class TestEntropyCalculation:
    """Test entropy calculation for secret validation."""
    
    def test_empty_string_entropy(self):
        """Empty string should have zero entropy."""
        assert _calculate_entropy("") == 0.0
    
    def test_single_character_entropy(self):
        """Single repeated character has zero entropy."""
        assert _calculate_entropy("aaaa") == 0.0
    
    def test_high_entropy_string(self):
        """Random-looking string should have high entropy."""
        random_string = "aB3!xY7@mK9#pQ2$"
        entropy = _calculate_entropy(random_string)
        assert entropy > 3.0  # Should have good randomness


class TestJWTSecretValidation:
    """Test JWT secret validation logic."""
    
    def test_empty_secret_raises_error(self):
        """Empty secret should raise SecurityConfigError."""
        with pytest.raises(SecurityConfigError, match="cannot be empty"):
            _validate_jwt_secret("", "production")
    
    def test_insecure_patterns_in_production(self):
        """Insecure patterns should raise error in production."""
        insecure_secrets = [
            "secret",
            "changeme",
            "dev-secret-change-in-production",
            "default-password",
            "test12345",
        ]
        
        for secret in insecure_secrets:
            with pytest.raises(SecurityConfigError, match="insecure pattern"):
                _validate_jwt_secret(secret, "production")
    
    def test_insecure_patterns_allowed_in_development(self):
        """Insecure patterns should only warn in development."""
        # Should not raise, just log warning
        _validate_jwt_secret("dev-secret-for-testing", "development")
    
    def test_short_secret_in_production(self):
        """Secret shorter than 32 chars should fail in production."""
        with pytest.raises(SecurityConfigError, match="at least 32 characters"):
            _validate_jwt_secret("short", "production")
    
    def test_short_secret_allowed_in_development(self):
        """Short secret should only warn in development."""
        # Should not raise, just log warning
        _validate_jwt_secret("short", "development")
    
    def test_secure_secret_passes(self):
        """Properly generated secret should pass validation."""
        secure_secret = generate_secure_secret()
        # Should not raise
        _validate_jwt_secret(secure_secret, "production")


class TestGetJWTSecret:
    """Test get_jwt_secret function with various configurations."""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_secret_in_production_raises_error(self):
        """Missing JWT_SECRET in production should raise error."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            with pytest.raises(SecurityConfigError, match="must be set in production"):
                get_jwt_secret()
    
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_secret_in_development_generates_one(self):
        """Missing JWT_SECRET in development should auto-generate."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            secret = get_jwt_secret()
            assert secret  # Should have a value
            assert len(secret) >= 32  # Should be reasonably long
    
    @patch.dict(os.environ, {}, clear=True)
    def test_valid_secret_in_production(self):
        """Valid JWT_SECRET in production should return the secret."""
        secure_secret = generate_secure_secret()
        with patch.dict(os.environ, {
            "JWT_SECRET": secure_secret,
            "ENVIRONMENT": "production"
        }):
            secret = get_jwt_secret()
            assert secret == secure_secret
    
    @patch.dict(os.environ, {}, clear=True)
    def test_insecure_secret_with_bypass_flag(self):
        """Insecure secret with bypass flag should be allowed."""
        with patch.dict(os.environ, {
            "JWT_SECRET": "weak",
            "ENVIRONMENT": "production",
            "ALLOW_INSECURE_JWT_SECRET": "true"
        }):
            secret = get_jwt_secret()
            assert secret == "weak"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_whitespace_trimming(self):
        """JWT_SECRET should be trimmed of whitespace."""
        secure_secret = generate_secure_secret()
        with patch.dict(os.environ, {
            "JWT_SECRET": f"  {secure_secret}  ",
            "ENVIRONMENT": "production"
        }):
            secret = get_jwt_secret()
            assert secret == secure_secret
            assert secret == secret.strip()


class TestGetJWTConfig:
    """Test get_jwt_config function."""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_default_config_in_development(self):
        """Should return default config in development."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            config = get_jwt_config()
            assert "secret" in config
            assert config["expiry_hours"] == 24
            assert config["algorithm"] == "HS256"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_custom_expiry(self):
        """Should respect custom JWT_EXPIRY_HOURS."""
        secure_secret = generate_secure_secret()
        with patch.dict(os.environ, {
            "JWT_SECRET": secure_secret,
            "JWT_EXPIRY_HOURS": "48",
            "ENVIRONMENT": "production"
        }):
            config = get_jwt_config()
            assert config["expiry_hours"] == 48
    
    @patch.dict(os.environ, {}, clear=True)
    def test_custom_algorithm(self):
        """Should respect custom JWT_ALGORITHM."""
        secure_secret = generate_secure_secret()
        with patch.dict(os.environ, {
            "JWT_SECRET": secure_secret,
            "JWT_ALGORITHM": "HS512",
            "ENVIRONMENT": "production"
        }):
            config = get_jwt_config()
            assert config["algorithm"] == "HS512"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_invalid_algorithm_raises_error(self):
        """Invalid algorithm should raise error."""
        secure_secret = generate_secure_secret()
        with patch.dict(os.environ, {
            "JWT_SECRET": secure_secret,
            "JWT_ALGORITHM": "RS256",  # RSA not supported
            "ENVIRONMENT": "production"
        }):
            with pytest.raises(SecurityConfigError, match="JWT_ALGORITHM must be one of"):
                get_jwt_config()
    
    @patch.dict(os.environ, {}, clear=True)
    def test_invalid_expiry_raises_error(self):
        """Expiry less than 1 hour should raise error."""
        secure_secret = generate_secure_secret()
        with patch.dict(os.environ, {
            "JWT_SECRET": secure_secret,
            "JWT_EXPIRY_HOURS": "0",
            "ENVIRONMENT": "production"
        }):
            with pytest.raises(SecurityConfigError, match="at least 1 hour"):
                get_jwt_config()


class TestGenerateSecureSecret:
    """Test secure secret generation."""
    
    def test_generates_non_empty_secret(self):
        """Should generate a non-empty secret."""
        secret = generate_secure_secret()
        assert secret
        assert len(secret) > 0
    
    def test_generates_long_enough_secret(self):
        """Should generate a secret of sufficient length."""
        secret = generate_secure_secret()
        assert len(secret) >= 32
    
    def test_generates_unique_secrets(self):
        """Should generate different secrets each time."""
        secret1 = generate_secure_secret()
        secret2 = generate_secure_secret()
        assert secret1 != secret2
    
    def test_generated_secret_is_url_safe(self):
        """Generated secret should be URL-safe."""
        secret = generate_secure_secret()
        # URL-safe base64 uses: A-Z, a-z, 0-9, -, _
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
        assert all(c in allowed_chars for c in secret)
    
    def test_generated_secret_has_high_entropy(self):
        """Generated secret should have high entropy."""
        secret = generate_secure_secret()
        entropy = _calculate_entropy(secret)
        assert entropy > 4.0  # Should have good randomness


class TestIntegration:
    """Integration tests for the security config module."""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_production_startup_with_valid_config(self):
        """Production startup should succeed with valid config."""
        secure_secret = generate_secure_secret()
        with patch.dict(os.environ, {
            "JWT_SECRET": secure_secret,
            "JWT_EXPIRY_HOURS": "24",
            "JWT_ALGORITHM": "HS256",
            "ENVIRONMENT": "production"
        }):
            config = get_jwt_config()
            assert config["secret"] == secure_secret
            assert config["expiry_hours"] == 24
            assert config["algorithm"] == "HS256"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_production_startup_fails_without_secret(self):
        """Production startup should fail without JWT_SECRET."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            with pytest.raises(SecurityConfigError):
                get_jwt_config()
    
    @patch.dict(os.environ, {}, clear=True)
    def test_development_startup_succeeds_without_secret(self):
        """Development startup should succeed without JWT_SECRET."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            config = get_jwt_config()
            assert config["secret"]  # Should have auto-generated secret
            assert len(config["secret"]) >= 32
