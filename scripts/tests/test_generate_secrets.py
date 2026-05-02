"""
scripts/tests/test_generate_secrets.py
======================================
Unit tests for secret generation utilities.

Run with:
    pytest scripts/tests/test_generate_secrets.py -v
"""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generate_secrets import SecretGenerator


class TestSecretGenerator:
    """Test suite for SecretGenerator class."""
    
    def test_generate_jwt_secret_default_length(self):
        """Test JWT secret generation with default length."""
        secret = SecretGenerator.generate_jwt_secret()
        
        # Should be base64 encoded, so length is roughly 1.33x bytes
        assert len(secret) >= 85  # 64 bytes * 1.33
        assert isinstance(secret, str)
    
    def test_generate_jwt_secret_custom_length(self):
        """Test JWT secret generation with custom length."""
        secret = SecretGenerator.generate_jwt_secret(length=48)
        
        assert len(secret) >= 64  # 48 bytes * 1.33
        assert isinstance(secret, str)
    
    def test_generate_jwt_secret_minimum_length(self):
        """Test JWT secret rejects too-short length."""
        with pytest.raises(ValueError, match="at least 32 bytes"):
            SecretGenerator.generate_jwt_secret(length=16)
    
    def test_generate_jwt_secret_uniqueness(self):
        """Test that generated secrets are unique."""
        secret1 = SecretGenerator.generate_jwt_secret()
        secret2 = SecretGenerator.generate_jwt_secret()
        
        assert secret1 != secret2
    
    def test_generate_database_password_default(self):
        """Test database password generation with default settings."""
        password = SecretGenerator.generate_database_password()
        
        assert len(password) == 32
        assert any(c.isupper() for c in password)
        assert any(c.islower() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(c in '!@#$%^&*()-_=+[]{}|;:,.<>?' for c in password)
    
    def test_generate_database_password_custom_length(self):
        """Test database password with custom length."""
        password = SecretGenerator.generate_database_password(length=48)
        
        assert len(password) == 48
    
    def test_generate_database_password_minimum_length(self):
        """Test database password rejects too-short length."""
        with pytest.raises(ValueError, match="at least 16 characters"):
            SecretGenerator.generate_database_password(length=8)
    
    def test_generate_database_password_complexity(self):
        """Test that database password meets complexity requirements."""
        # Generate multiple passwords to ensure consistency
        for _ in range(10):
            password = SecretGenerator.generate_database_password()
            
            has_upper = any(c.isupper() for c in password)
            has_lower = any(c.islower() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_special = any(c in '!@#$%^&*()-_=+[]{}|;:,.<>?' for c in password)
            
            assert has_upper, "Password should contain uppercase"
            assert has_lower, "Password should contain lowercase"
            assert has_digit, "Password should contain digit"
            assert has_special, "Password should contain special character"
    
    def test_generate_api_token_default(self):
        """Test API token generation with default length."""
        token = SecretGenerator.generate_api_token()
        
        # URL-safe base64 tokens
        assert len(token) >= 64  # 48 bytes * 1.33
        assert isinstance(token, str)
        # Should not contain +, /, or =
        assert '+' not in token
        assert '/' not in token
    
    def test_generate_api_token_custom_length(self):
        """Test API token with custom length."""
        token = SecretGenerator.generate_api_token(length=64)
        
        assert len(token) >= 85
    
    def test_generate_api_token_minimum_length(self):
        """Test API token rejects too-short length."""
        with pytest.raises(ValueError, match="at least 32 bytes"):
            SecretGenerator.generate_api_token(length=16)
    
    def test_generate_symmetric_key_default(self):
        """Test symmetric key generation (AES-256)."""
        key = SecretGenerator.generate_symmetric_key()
        
        # 32 bytes = 64 hex characters
        assert len(key) == 64
        assert all(c in '0123456789abcdef' for c in key)
    
    def test_generate_symmetric_key_aes128(self):
        """Test symmetric key generation for AES-128."""
        key = SecretGenerator.generate_symmetric_key(length=16)
        
        # 16 bytes = 32 hex characters
        assert len(key) == 32
    
    def test_generate_symmetric_key_aes192(self):
        """Test symmetric key generation for AES-192."""
        key = SecretGenerator.generate_symmetric_key(length=24)
        
        # 24 bytes = 48 hex characters
        assert len(key) == 48
    
    def test_generate_symmetric_key_invalid_length(self):
        """Test symmetric key rejects invalid lengths."""
        with pytest.raises(ValueError, match="must be 16, 24, or 32 bytes"):
            SecretGenerator.generate_symmetric_key(length=20)
    
    def test_generate_random_string_default(self):
        """Test random string generation with default charset."""
        random_str = SecretGenerator.generate_random_string()
        
        assert len(random_str) == 32
        assert random_str.isalnum()  # Should be alphanumeric only
    
    def test_generate_random_string_custom_charset(self):
        """Test random string with custom charset."""
        charset = '0123456789'
        random_str = SecretGenerator.generate_random_string(length=16, charset=charset)
        
        assert len(random_str) == 16
        assert all(c in charset for c in random_str)
    
    def test_generate_otp_secret(self):
        """Test OTP/TOTP secret generation."""
        secret = SecretGenerator.generate_otp_secret()
        
        # Base32 encoded (no lowercase, no padding)
        assert len(secret) >= 51  # 32 bytes * 1.6
        assert secret.isupper()
        assert '=' not in secret  # Should strip padding
    
    def test_generate_csrf_token(self):
        """Test CSRF token generation."""
        token = SecretGenerator.generate_csrf_token()
        
        # URL-safe base64
        assert len(token) >= 43  # 32 bytes * 1.33
        assert '+' not in token
        assert '/' not in token
    
    def test_all_generators_return_strings(self):
        """Test that all generators return strings."""
        generators = [
            SecretGenerator.generate_jwt_secret,
            SecretGenerator.generate_database_password,
            SecretGenerator.generate_api_token,
            SecretGenerator.generate_symmetric_key,
            SecretGenerator.generate_random_string,
            SecretGenerator.generate_otp_secret,
            SecretGenerator.generate_csrf_token,
        ]
        
        for generator in generators:
            result = generator()
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_secrets_are_random(self):
        """Test that secrets are truly random (not sequential)."""
        secrets = [SecretGenerator.generate_jwt_secret() for _ in range(5)]
        
        # All should be unique
        assert len(set(secrets)) == 5
        
        # No obvious patterns (basic check)
        for i in range(len(secrets) - 1):
            # Hamming distance should be high (many differences)
            differences = sum(c1 != c2 for c1, c2 in zip(secrets[i], secrets[i + 1]))
            # At least 80% of characters should differ
            assert differences > len(secrets[i]) * 0.8


class TestEntropyCalculation:
    """Test entropy calculation (if exposed)."""
    
    def test_entropy_increases_with_length(self):
        """Test that longer secrets have higher entropy."""
        short_secret = SecretGenerator.generate_jwt_secret(length=32)
        long_secret = SecretGenerator.generate_jwt_secret(length=64)
        
        # Longer secret should be longer (obvious but sanity check)
        assert len(long_secret) > len(short_secret)
    
    def test_entropy_increases_with_charset(self):
        """Test that larger charsets increase entropy."""
        digits_only = SecretGenerator.generate_random_string(length=32, charset='0123456789')
        alphanumeric = SecretGenerator.generate_random_string(length=32)
        
        # Both should be same length
        assert len(digits_only) == len(alphanumeric)
        
        # Alphanumeric should use more unique characters
        assert len(set(alphanumeric)) >= len(set(digits_only))


class TestSecurityProperties:
    """Test security properties of generated secrets."""
    
    def test_secrets_not_empty(self):
        """Test that no generator returns empty strings."""
        generators = [
            SecretGenerator.generate_jwt_secret,
            SecretGenerator.generate_database_password,
            SecretGenerator.generate_api_token,
            SecretGenerator.generate_symmetric_key,
            SecretGenerator.generate_random_string,
            SecretGenerator.generate_otp_secret,
            SecretGenerator.generate_csrf_token,
        ]
        
        for generator in generators:
            result = generator()
            assert result, f"{generator.__name__} returned empty string"
            assert len(result) > 0
    
    def test_no_predictable_patterns(self):
        """Test that secrets don't contain obvious patterns."""
        for _ in range(10):
            password = SecretGenerator.generate_database_password(length=32)
            
            # Should not be all same character
            assert len(set(password)) > 1
            
            # Should not be sequential
            assert password != ''.join(chr(i) for i in range(ord('a'), ord('a') + 32))
    
    def test_jwt_secret_sufficient_length(self):
        """Test that JWT secrets meet minimum security requirements."""
        secret = SecretGenerator.generate_jwt_secret()
        
        # For HS256, minimum 256 bits (32 bytes) recommended
        # We use 64 bytes (512 bits) by default
        # Base64 encoding: 64 bytes -> ~85 characters
        assert len(secret) >= 85


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
