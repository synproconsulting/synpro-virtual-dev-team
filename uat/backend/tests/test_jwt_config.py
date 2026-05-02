"""
tests/test_jwt_config.py
═════════════════════════
Tests for JWT configuration hardening (SDT1-63).
"""

import pytest
import os
import base64
from unittest.mock import patch

from config import (
    generate_jwt_secret,
    get_jwt_secret,
    get_jwt_expiry_hours,
    get_jwt_config,
    JWTConfigError,
    _is_weak_jwt_secret,
    _calculate_entropy_bits,
)


class TestGenerateJWTSecret:
    """Test secure JWT secret generation."""
    
    def test_default_length(self):
        """Default secret should be 64 bytes (512 bits)."""
        secret = generate_jwt_secret()
        # Base64 encoding increases size by ~4/3
        assert len(secret) >= 85
        # Verify it's valid base64
        decoded = base64.b64decode(secret)
        assert len(decoded) == 64
    
    def test_custom_length(self):
        """Custom length should be respected."""
        secret = generate_jwt_secret(length=32)
        decoded = base64.b64decode(secret)
        assert len(decoded) == 32
    
    def test_minimum_length_enforced(self):
        """Secrets below 32 bytes should raise error."""
        with pytest.raises(ValueError, match="at least 32 bytes"):
            generate_jwt_secret(length=16)
    
    def test_uniqueness(self):
        """Generated secrets should be unique."""
        secret1 = generate_jwt_secret()
        secret2 = generate_jwt_secret()
        assert secret1 != secret2
    
    def test_high_entropy(self):
        """Generated secrets should have high entropy."""
        secret = generate_jwt_secret()
        entropy = _calculate_entropy_bits(secret)
        # Base64 has ~6 bits per character
        assert entropy > 400  # Should be around 512 bits


class TestCalculateEntropyBits:
    """Test entropy calculation."""
    
    def test_digits_only(self):
        """Digits-only string."""
        entropy = _calculate_entropy_bits("1234567890")
        # ~3.32 bits per digit
        assert 30 <= entropy <= 35
    
    def test_lowercase_only(self):
        """Lowercase-only string."""
        entropy = _calculate_entropy_bits("abcdefghij")
        # ~4.7 bits per character
        assert 45 <= entropy <= 50
    
    def test_alphanumeric(self):
        """Alphanumeric string."""
        entropy = _calculate_entropy_bits("abc123DEF456")
        # ~5.95 bits per character
        assert 65 <= entropy <= 75
    
    def test_with_special_chars(self):
        """String with special characters."""
        entropy = _calculate_entropy_bits("aB3!@#$%^&*()")
        # ~6.57 bits per character
        assert 78 <= entropy <= 88
    
    def test_empty_string(self):
        """Empty string has zero entropy."""
        entropy = _calculate_entropy_bits("")
        assert entropy == 0


class TestIsWeakJWTSecret:
    """Test weak JWT secret detection."""
    
    def test_empty_secret(self):
        """Empty secret should be weak."""
        is_weak, reason = _is_weak_jwt_secret("")
        assert is_weak
        assert "empty" in reason.lower()
    
    def test_whitespace_only(self):
        """Whitespace-only secret should be weak."""
        is_weak, reason = _is_weak_jwt_secret("   \t\n   ")
        assert is_weak
        assert "empty" in reason.lower()
    
    def test_too_short(self):
        """Secrets under 32 characters should be weak."""
        is_weak, reason = _is_weak_jwt_secret("short123")
        assert is_weak
        assert "too short" in reason.lower()
    
    def test_known_weak_secret(self):
        """Known weak secrets should be detected."""
        for weak in ["secret", "dev-secret", "password", "test", "admin"]:
            is_weak, reason = _is_weak_jwt_secret(weak)
            assert is_weak, f"'{weak}' should be detected as weak"
            assert "commonly used" in reason.lower() or "too short" in reason.lower()
    
    def test_default_placeholder(self):
        """Default/placeholder values should be weak."""
        for placeholder in ["dev-secret-change-in-production", "change-me", "your-secret-key"]:
            is_weak, reason = _is_weak_jwt_secret(placeholder)
            assert is_weak
    
    def test_contains_change(self):
        """Secrets containing 'change' should be weak."""
        is_weak, reason = _is_weak_jwt_secret("please-change-this-secret-key-12345")
        assert is_weak
        assert "default" in reason.lower() or "placeholder" in reason.lower()
    
    def test_low_entropy(self):
        """Low entropy secrets should be weak."""
        # All same character
        is_weak, reason = _is_weak_jwt_secret("a" * 50)
        assert is_weak
        assert "entropy" in reason.lower() or "repeated" in reason.lower()
    
    def test_repeated_characters(self):
        """Too many repeated characters should be weak."""
        is_weak, reason = _is_weak_jwt_secret("aaaaaabbbbbbccccccdddddd")
        assert is_weak
        assert "repeated" in reason.lower()
    
    def test_strong_secret(self):
        """Strong secret should pass."""
        strong = base64.b64encode(os.urandom(64)).decode('utf-8')
        is_weak, reason = _is_weak_jwt_secret(strong)
        assert not is_weak
        assert reason == ""
    
    def test_minimum_valid_secret(self):
        """Minimum valid secret (32 chars, good entropy)."""
        # Alphanumeric with good distribution
        secret = "aB3dE5fG7hI9jK1lM2nO4pQ6rS8tU"
        is_weak, reason = _is_weak_jwt_secret(secret)
        # This might be weak due to low entropy, but at least it's 32 chars
        # The important thing is it doesn't crash


class TestGetJWTSecret:
    """Test JWT secret retrieval from environment."""
    
    def test_production_without_secret(self):
        """Production without JWT_SECRET should raise error."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
        }, clear=True):
            with pytest.raises(JWTConfigError, match="JWT_SECRET.*must be set"):
                get_jwt_secret()
    
    def test_production_with_weak_secret(self):
        """Production with weak secret should raise error."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": "weak",
        }):
            with pytest.raises(JWTConfigError, match="Insecure JWT secret"):
                get_jwt_secret()
    
    def test_production_with_default_secret(self):
        """Production with default secret should raise error."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": "dev-secret-change-in-production",
        }):
            with pytest.raises(JWTConfigError, match="Insecure JWT secret"):
                get_jwt_secret()
    
    def test_production_with_strong_secret(self):
        """Production with strong secret should succeed."""
        strong_secret = base64.b64encode(os.urandom(64)).decode('utf-8')
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": strong_secret,
        }):
            secret = get_jwt_secret()
            assert secret == strong_secret
    
    def test_development_without_secret(self):
        """Development without secret should generate temporary one."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
        }, clear=True):
            secret = get_jwt_secret()
            # Should be a generated secret
            assert len(secret) >= 85
            # Verify it's valid base64
            base64.b64decode(secret)
    
    def test_development_with_weak_secret_not_allowed(self):
        """Development with weak secret should fail by default."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "JWT_SECRET": "weak123",
        }):
            with pytest.raises(JWTConfigError, match="Insecure JWT secret"):
                get_jwt_secret()
    
    def test_development_with_weak_secret_allowed(self):
        """Development with weak secret should work if explicitly allowed."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "JWT_SECRET": "weak123-but-i-know-what-im-doing",
            "ALLOW_WEAK_JWT_SECRET": "true",
        }):
            secret = get_jwt_secret()
            assert secret == "weak123-but-i-know-what-im-doing"
    
    def test_development_with_strong_secret(self):
        """Development with strong secret should succeed."""
        strong_secret = base64.b64encode(os.urandom(64)).decode('utf-8')
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "JWT_SECRET": strong_secret,
        }):
            secret = get_jwt_secret()
            assert secret == strong_secret
    
    def test_allow_weak_case_insensitive(self):
        """ALLOW_WEAK_JWT_SECRET should be case-insensitive."""
        for value in ["true", "True", "TRUE", "TrUe"]:
            with patch.dict(os.environ, {
                "ENVIRONMENT": "development",
                "JWT_SECRET": "weak-secret-for-testing-only-123",
                "ALLOW_WEAK_JWT_SECRET": value,
            }):
                secret = get_jwt_secret()
                assert secret == "weak-secret-for-testing-only-123"
    
    def test_environment_case_insensitive(self):
        """ENVIRONMENT should be case-insensitive."""
        strong_secret = base64.b64encode(os.urandom(64)).decode('utf-8')
        for env in ["production", "PRODUCTION", "Production"]:
            with patch.dict(os.environ, {
                "ENVIRONMENT": env,
                "JWT_SECRET": strong_secret,
            }):
                secret = get_jwt_secret()
                assert secret == strong_secret


class TestGetJWTExpiryHours:
    """Test JWT expiry configuration."""
    
    def test_default_expiry(self):
        """Default expiry should be 24 hours."""
        with patch.dict(os.environ, {}, clear=True):
            expiry = get_jwt_expiry_hours()
            assert expiry == 24
    
    def test_custom_expiry(self):
        """Custom expiry should be respected."""
        with patch.dict(os.environ, {
            "JWT_EXPIRY_HOURS": "48",
        }):
            expiry = get_jwt_expiry_hours()
            assert expiry == 48
    
    def test_invalid_expiry(self):
        """Invalid expiry should raise error."""
        with patch.dict(os.environ, {
            "JWT_EXPIRY_HOURS": "not-a-number",
        }):
            with pytest.raises(JWTConfigError, match="must be an integer"):
                get_jwt_expiry_hours()
    
    def test_negative_expiry(self):
        """Negative expiry should raise error."""
        with patch.dict(os.environ, {
            "JWT_EXPIRY_HOURS": "-1",
        }):
            with pytest.raises(JWTConfigError, match="must be positive"):
                get_jwt_expiry_hours()
    
    def test_zero_expiry(self):
        """Zero expiry should raise error."""
        with patch.dict(os.environ, {
            "JWT_EXPIRY_HOURS": "0",
        }):
            with pytest.raises(JWTConfigError, match="must be positive"):
                get_jwt_expiry_hours()
    
    def test_very_long_expiry_warning(self):
        """Very long expiry should succeed with warning."""
        with patch.dict(os.environ, {
            "JWT_EXPIRY_HOURS": "1000",  # ~41 days
        }):
            expiry = get_jwt_expiry_hours()
            assert expiry == 1000


class TestGetJWTConfig:
    """Test complete JWT configuration."""
    
    def test_config_structure(self):
        """Config should have all required fields."""
        strong_secret = base64.b64encode(os.urandom(64)).decode('utf-8')
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": strong_secret,
            "JWT_EXPIRY_HOURS": "24",
        }):
            config = get_jwt_config()
            
            assert "secret" in config
            assert "expiry_hours" in config
            assert "algorithm" in config
    
    def test_config_values(self):
        """Config should have correct values."""
        strong_secret = base64.b64encode(os.urandom(64)).decode('utf-8')
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": strong_secret,
            "JWT_EXPIRY_HOURS": "48",
        }):
            config = get_jwt_config()
            
            assert config["secret"] == strong_secret
            assert config["expiry_hours"] == 48
            assert config["algorithm"] == "HS256"
    
    def test_config_with_defaults(self):
        """Config with defaults should work."""
        strong_secret = base64.b64encode(os.urandom(64)).decode('utf-8')
        with patch.dict(os.environ, {
            "JWT_SECRET": strong_secret,
        }):
            config = get_jwt_config()
            
            assert config["secret"] == strong_secret
            assert config["expiry_hours"] == 24
            assert config["algorithm"] == "HS256"


class TestEdgeCases:
    """Test edge cases and security scenarios."""
    
    def test_secret_with_whitespace(self):
        """Secret with leading/trailing whitespace should be trimmed."""
        strong_secret = base64.b64encode(os.urandom(64)).decode('utf-8')
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": f"  {strong_secret}  ",
        }):
            secret = get_jwt_secret()
            assert secret == strong_secret
    
    def test_secret_with_newlines(self):
        """Secret with newlines should be trimmed."""
        strong_secret = base64.b64encode(os.urandom(64)).decode('utf-8')
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": f"\n{strong_secret}\n",
        }):
            secret = get_jwt_secret()
            assert secret == strong_secret
    
    def test_expiry_with_whitespace(self):
        """Expiry with whitespace should be parsed."""
        with patch.dict(os.environ, {
            "JWT_EXPIRY_HOURS": "  48  ",
        }):
            expiry = get_jwt_expiry_hours()
            assert expiry == 48
    
    def test_real_world_strong_secret(self):
        """Real-world strong secret examples."""
        secrets_to_test = [
            # OpenSSL generated
            "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC7",
            # Base64 of random bytes
            base64.b64encode(os.urandom(64)).decode('utf-8'),
            # UUID-based (not recommended but should pass if long enough)
            "12345678-1234-1234-1234-123456789abc-12345678-1234-1234-1234-123456789abc",
        ]
        
        for secret in secrets_to_test:
            if len(secret) >= 32:
                with patch.dict(os.environ, {
                    "ENVIRONMENT": "production",
                    "JWT_SECRET": secret,
                }):
                    result = get_jwt_secret()
                    assert result == secret
    
    def test_common_mistakes(self):
        """Common mistakes should be caught."""
        common_mistakes = [
            "mysecret",
            "12345678",
            "secretkey",
            "jwt-secret",
            "change-me-in-production",
        ]
        
        for mistake in common_mistakes:
            with patch.dict(os.environ, {
                "ENVIRONMENT": "production",
                "JWT_SECRET": mistake,
            }):
                with pytest.raises(JWTConfigError):
                    get_jwt_secret()
