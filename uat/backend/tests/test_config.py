"""
tests/test_config.py
════════════════════
Tests for configuration module, especially CORS hardening (SDT1-56).
"""

import pytest
import os
from unittest.mock import patch

from config import (
    get_cors_origins,
    get_cors_config,
    CORSConfigError,
    _is_valid_origin,
    _validate_cors_origins,
)


class TestIsValidOrigin:
    """Test origin URL validation."""
    
    def test_valid_http_origin(self):
        """Valid HTTP origin should pass."""
        assert _is_valid_origin("http://localhost:3000")
    
    def test_valid_https_origin(self):
        """Valid HTTPS origin should pass."""
        assert _is_valid_origin("https://example.com")
    
    def test_valid_with_port(self):
        """Valid origin with port should pass."""
        assert _is_valid_origin("https://example.com:8080")
    
    def test_valid_with_subdomain(self):
        """Valid origin with subdomain should pass."""
        assert _is_valid_origin("https://app.example.com")
    
    def test_wildcard(self):
        """Wildcard should be valid."""
        assert _is_valid_origin("*")
    
    def test_invalid_no_scheme(self):
        """Origin without scheme should fail."""
        assert not _is_valid_origin("example.com")
    
    def test_invalid_no_netloc(self):
        """Origin without netloc should fail."""
        assert not _is_valid_origin("http://")
    
    def test_invalid_scheme(self):
        """Origin with invalid scheme should fail."""
        assert not _is_valid_origin("ftp://example.com")
    
    def test_with_path(self):
        """Origin with path should be valid (will log warning)."""
        # Paths are technically valid but unusual
        assert _is_valid_origin("http://localhost:3000/app")


class TestValidateCorsOrigins:
    """Test CORS origins validation."""
    
    def test_valid_single_origin(self):
        """Single valid origin should pass."""
        origins = ["https://example.com"]
        _validate_cors_origins(origins, allow_wildcard=False)
    
    def test_valid_multiple_origins(self):
        """Multiple valid origins should pass."""
        origins = [
            "https://app.example.com",
            "https://admin.example.com",
            "http://localhost:3000",
        ]
        _validate_cors_origins(origins, allow_wildcard=False)
    
    def test_wildcard_not_allowed(self):
        """Wildcard without allow_wildcard flag should raise error."""
        origins = ["*"]
        with pytest.raises(CORSConfigError, match="Wildcard.*detected"):
            _validate_cors_origins(origins, allow_wildcard=False)
    
    def test_wildcard_allowed(self):
        """Wildcard with allow_wildcard flag should pass with warning."""
        origins = ["*"]
        _validate_cors_origins(origins, allow_wildcard=True)
    
    def test_wildcard_with_others(self):
        """Wildcard mixed with specific origins should fail."""
        origins = ["*", "https://example.com"]
        with pytest.raises(CORSConfigError, match="Cannot mix wildcard"):
            _validate_cors_origins(origins, allow_wildcard=True)
    
    def test_invalid_origin_format(self):
        """Invalid origin format should raise error."""
        origins = ["not-a-valid-url"]
        with pytest.raises(CORSConfigError, match="Invalid CORS origin format"):
            _validate_cors_origins(origins, allow_wildcard=False)
    
    def test_empty_list(self):
        """Empty origins list should raise error."""
        with pytest.raises(CORSConfigError, match="No CORS origins configured"):
            _validate_cors_origins([], allow_wildcard=False)


class TestGetCorsOrigins:
    """Test CORS origins retrieval from environment."""
    
    def test_single_origin(self):
        """Single FRONTEND_URL should return single origin."""
        with patch.dict(os.environ, {
            "FRONTEND_URL": "https://example.com",
            "ENVIRONMENT": "production",
        }):
            origins = get_cors_origins()
            assert origins == ["https://example.com"]
    
    def test_multiple_origins_comma_separated(self):
        """Comma-separated FRONTEND_URL should return multiple origins."""
        with patch.dict(os.environ, {
            "FRONTEND_URL": "https://app.example.com,https://admin.example.com",
            "ENVIRONMENT": "production",
        }):
            origins = get_cors_origins()
            assert origins == ["https://app.example.com", "https://admin.example.com"]
    
    def test_multiple_origins_with_spaces(self):
        """Comma-separated with spaces should trim properly."""
        with patch.dict(os.environ, {
            "FRONTEND_URL": "https://app.example.com, https://admin.example.com , https://staging.example.com",
            "ENVIRONMENT": "production",
        }):
            origins = get_cors_origins()
            assert origins == [
                "https://app.example.com",
                "https://admin.example.com",
                "https://staging.example.com",
            ]
    
    def test_wildcard_in_development(self):
        """Wildcard in development with flag should work."""
        with patch.dict(os.environ, {
            "FRONTEND_URL": "*",
            "ENVIRONMENT": "development",
            "ALLOW_CORS_WILDCARD": "true",
        }):
            origins = get_cors_origins()
            assert origins == ["*"]
    
    def test_wildcard_in_production_without_flag(self):
        """Wildcard in production without flag should fail."""
        with patch.dict(os.environ, {
            "FRONTEND_URL": "*",
            "ENVIRONMENT": "production",
        }):
            with pytest.raises(CORSConfigError, match="Wildcard.*detected.*production"):
                get_cors_origins()
    
    def test_wildcard_in_production_with_flag(self):
        """Wildcard in production with explicit flag should work."""
        with patch.dict(os.environ, {
            "FRONTEND_URL": "*",
            "ENVIRONMENT": "production",
            "ALLOW_CORS_WILDCARD": "true",
        }):
            origins = get_cors_origins()
            assert origins == ["*"]
    
    def test_no_frontend_url_production(self):
        """No FRONTEND_URL in production should fail."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
        }, clear=True):
            with pytest.raises(CORSConfigError, match="FRONTEND_URL must be configured"):
                get_cors_origins()
    
    def test_no_frontend_url_development(self):
        """No FRONTEND_URL in development should default to localhost."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
        }, clear=True):
            origins = get_cors_origins()
            assert origins == ["http://localhost:3000"]
    
    def test_empty_frontend_url(self):
        """Empty FRONTEND_URL should raise error."""
        with patch.dict(os.environ, {
            "FRONTEND_URL": "   ",
            "ENVIRONMENT": "production",
        }):
            with pytest.raises(CORSConfigError, match="FRONTEND_URL must be configured"):
                get_cors_origins()
    
    def test_invalid_origin_format(self):
        """Invalid origin format should raise error."""
        with patch.dict(os.environ, {
            "FRONTEND_URL": "not-a-url",
            "ENVIRONMENT": "production",
        }):
            with pytest.raises(CORSConfigError, match="Invalid CORS origin format"):
                get_cors_origins()
    
    def test_mixed_valid_and_invalid_origins(self):
        """Mix of valid and invalid origins should fail."""
        with patch.dict(os.environ, {
            "FRONTEND_URL": "https://valid.com,not-valid,https://another-valid.com",
            "ENVIRONMENT": "production",
        }):
            with pytest.raises(CORSConfigError, match="Invalid CORS origin format"):
                get_cors_origins()


class TestGetCorsConfig:
    """Test complete CORS configuration."""
    
    def test_config_structure(self):
        """Config should have all required fields."""
        with patch.dict(os.environ, {
            "FRONTEND_URL": "https://example.com",
            "ENVIRONMENT": "production",
        }):
            config = get_cors_config()
            
            assert "allow_origins" in config
            assert "allow_credentials" in config
            assert "allow_methods" in config
            assert "allow_headers" in config
            assert "expose_headers" in config
            assert "max_age" in config
    
    def test_config_values(self):
        """Config should have correct values."""
        with patch.dict(os.environ, {
            "FRONTEND_URL": "https://example.com,https://admin.example.com",
            "ENVIRONMENT": "production",
        }):
            config = get_cors_config()
            
            assert config["allow_origins"] == ["https://example.com", "https://admin.example.com"]
            assert config["allow_credentials"] is True
            assert "GET" in config["allow_methods"]
            assert "POST" in config["allow_methods"]
            assert "PUT" in config["allow_methods"]
            assert "DELETE" in config["allow_methods"]
            assert config["allow_headers"] == ["*"]
            assert isinstance(config["max_age"], int)
    
    def test_config_with_wildcard(self):
        """Config with wildcard should work when allowed."""
        with patch.dict(os.environ, {
            "FRONTEND_URL": "*",
            "ENVIRONMENT": "development",
            "ALLOW_CORS_WILDCARD": "true",
        }):
            config = get_cors_config()
            assert config["allow_origins"] == ["*"]


class TestEdgeCases:
    """Test edge cases and security scenarios."""
    
    def test_trailing_slashes_preserved(self):
        """Trailing slashes should be preserved (user's choice)."""
        with patch.dict(os.environ, {
            "FRONTEND_URL": "https://example.com/",
            "ENVIRONMENT": "production",
        }):
            origins = get_cors_origins()
            assert origins == ["https://example.com/"]
    
    def test_case_sensitivity(self):
        """Origin URLs should be case-sensitive (as per spec)."""
        with patch.dict(os.environ, {
            "FRONTEND_URL": "https://Example.COM",
            "ENVIRONMENT": "production",
        }):
            origins = get_cors_origins()
            assert origins == ["https://Example.COM"]
    
    def test_localhost_variants(self):
        """Different localhost formats should be valid."""
        with patch.dict(os.environ, {
            "FRONTEND_URL": "http://localhost:3000,http://127.0.0.1:3000,http://[::1]:3000",
            "ENVIRONMENT": "production",
        }):
            origins = get_cors_origins()
            assert len(origins) == 3
            assert "http://localhost:3000" in origins
            assert "http://127.0.0.1:3000" in origins
            assert "http://[::1]:3000" in origins
    
    def test_allow_cors_wildcard_case_insensitive(self):
        """ALLOW_CORS_WILDCARD should be case-insensitive."""
        for value in ["true", "True", "TRUE", "TrUe"]:
            with patch.dict(os.environ, {
                "FRONTEND_URL": "*",
                "ENVIRONMENT": "development",
                "ALLOW_CORS_WILDCARD": value,
            }):
                origins = get_cors_origins()
                assert origins == ["*"]
    
    def test_environment_case_insensitive(self):
        """ENVIRONMENT should be case-insensitive."""
        for env in ["development", "DEVELOPMENT", "Development"]:
            with patch.dict(os.environ, {
                "FRONTEND_URL": "*",
                "ENVIRONMENT": env,
                "ALLOW_CORS_WILDCARD": "true",
            }):
                origins = get_cors_origins()
                assert origins == ["*"]
