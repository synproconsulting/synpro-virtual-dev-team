"""
Tests for CORS configuration hardening.
"""

import pytest
import os
from unittest.mock import patch
from config import Settings


class TestCORSConfiguration:
    """Test suite for hardened CORS configuration."""
    
    def test_validate_origin_url_valid_https(self):
        """Test validation of valid HTTPS URLs."""
        with patch.object(Settings, 'ENVIRONMENT', 'production'):
            url = "https://app.example.com"
            result = Settings._validate_origin_url(url)
            assert result == "https://app.example.com"
    
    def test_validate_origin_url_valid_http_localhost(self):
        """Test validation of HTTP localhost URLs."""
        urls = [
            "http://localhost:3000",
            "http://127.0.0.1:5173",
        ]
        for url in urls:
            result = Settings._validate_origin_url(url)
            assert result == url
    
    def test_validate_origin_url_strips_path(self):
        """Test that paths are rejected from origin URLs."""
        with patch.object(Settings, 'ENVIRONMENT', 'production'):
            with pytest.raises(ValueError, match="should not include path"):
                Settings._validate_origin_url("https://app.example.com/path")
    
    def test_validate_origin_url_strips_query(self):
        """Test that query strings are rejected from origin URLs."""
        with patch.object(Settings, 'ENVIRONMENT', 'production'):
            with pytest.raises(ValueError, match="should not include query"):
                Settings._validate_origin_url("https://app.example.com?query=1")
    
    def test_validate_origin_url_strips_fragment(self):
        """Test that fragments are rejected from origin URLs."""
        with patch.object(Settings, 'ENVIRONMENT', 'production'):
            with pytest.raises(ValueError, match="should not include.*fragment"):
                Settings._validate_origin_url("https://app.example.com#fragment")
    
    def test_validate_origin_url_requires_scheme(self):
        """Test that URLs without scheme are rejected."""
        with pytest.raises(ValueError, match="must include scheme"):
            Settings._validate_origin_url("app.example.com")
    
    def test_validate_origin_url_requires_valid_scheme(self):
        """Test that only http/https schemes are allowed."""
        with pytest.raises(ValueError, match="must use http or https"):
            Settings._validate_origin_url("ftp://app.example.com")
    
    def test_validate_origin_url_requires_netloc(self):
        """Test that URLs must have a domain/host."""
        with pytest.raises(ValueError, match="must include a domain or host"):
            Settings._validate_origin_url("https://")
    
    def test_validate_origin_url_rejects_http_in_production(self):
        """Test that HTTP is rejected in production (except localhost)."""
        with patch.object(Settings, 'ENVIRONMENT', 'production'):
            with pytest.raises(ValueError, match="uses http scheme in production"):
                Settings._validate_origin_url("http://app.example.com")
    
    def test_validate_origin_url_allows_http_localhost_in_production(self):
        """Test that HTTP localhost is allowed even in production."""
        with patch.object(Settings, 'ENVIRONMENT', 'production'):
            result = Settings._validate_origin_url("http://localhost:3000")
            assert result == "http://localhost:3000"
    
    def test_validate_origin_url_wildcard_rejected_in_production(self):
        """Test that wildcard is rejected in production."""
        with patch.object(Settings, 'ENVIRONMENT', 'production'):
            with pytest.raises(ValueError, match="Wildcard.*not allowed in production"):
                Settings._validate_origin_url("*")
    
    def test_validate_origin_url_wildcard_allowed_in_dev(self):
        """Test that wildcard is allowed in development."""
        with patch.object(Settings, 'ENVIRONMENT', 'development'):
            result = Settings._validate_origin_url("*")
            assert result == "*"
    
    def test_get_allowed_origins_single_url(self):
        """Test getting allowed origins with a single URL."""
        with patch.object(Settings, 'FRONTEND_URL', 'https://app.example.com'):
            with patch.object(Settings, 'ENVIRONMENT', 'production'):
                origins = Settings.get_allowed_origins()
                assert origins == ["https://app.example.com"]
    
    def test_get_allowed_origins_multiple_urls(self):
        """Test getting allowed origins with multiple comma-separated URLs."""
        frontend_urls = "https://app.example.com,https://staging.example.com,https://admin.example.com"
        with patch.object(Settings, 'FRONTEND_URL', frontend_urls):
            with patch.object(Settings, 'ENVIRONMENT', 'production'):
                origins = Settings.get_allowed_origins()
                assert len(origins) == 3
                assert "https://app.example.com" in origins
                assert "https://staging.example.com" in origins
                assert "https://admin.example.com" in origins
    
    def test_get_allowed_origins_strips_whitespace(self):
        """Test that whitespace is properly stripped from URLs."""
        frontend_urls = " https://app.example.com , https://staging.example.com "
        with patch.object(Settings, 'FRONTEND_URL', frontend_urls):
            with patch.object(Settings, 'ENVIRONMENT', 'production'):
                origins = Settings.get_allowed_origins()
                assert len(origins) == 2
                assert "https://app.example.com" in origins
                assert "https://staging.example.com" in origins
    
    def test_get_allowed_origins_empty_raises_in_production(self):
        """Test that empty FRONTEND_URL raises error in production."""
        with patch.object(Settings, 'FRONTEND_URL', ''):
            with patch.object(Settings, 'ENVIRONMENT', 'production'):
                with pytest.raises(ValueError, match="FRONTEND_URL must be set in production"):
                    Settings.get_allowed_origins()
    
    def test_get_allowed_origins_defaults_localhost_in_dev(self):
        """Test that development defaults to localhost origins."""
        with patch.object(Settings, 'FRONTEND_URL', ''):
            with patch.object(Settings, 'ENVIRONMENT', 'development'):
                origins = Settings.get_allowed_origins()
                assert len(origins) > 0
                assert "http://localhost:3000" in origins
                assert "http://localhost:5173" in origins
    
    def test_get_allowed_origins_empty_raises_in_staging(self):
        """Test that empty FRONTEND_URL raises error in staging."""
        with patch.object(Settings, 'FRONTEND_URL', ''):
            with patch.object(Settings, 'ENVIRONMENT', 'staging'):
                with pytest.raises(ValueError, match="FRONTEND_URL must be set"):
                    Settings.get_allowed_origins()
    
    def test_get_allowed_origins_invalid_url_raises(self):
        """Test that invalid URLs raise appropriate errors."""
        with patch.object(Settings, 'FRONTEND_URL', 'not-a-valid-url'):
            with patch.object(Settings, 'ENVIRONMENT', 'production'):
                with pytest.raises(ValueError, match="must include scheme"):
                    Settings.get_allowed_origins()
    
    def test_get_allowed_origins_empty_list_after_parse(self):
        """Test that empty string list raises error."""
        with patch.object(Settings, 'FRONTEND_URL', ',,,'):
            with patch.object(Settings, 'ENVIRONMENT', 'production'):
                with pytest.raises(ValueError, match="contains no valid URLs"):
                    Settings.get_allowed_origins()
    
    def test_settings_validate_includes_cors_check(self):
        """Test that Settings.validate() checks CORS configuration."""
        with patch.object(Settings, 'JWT_SECRET', 'test-secret'):
            with patch.object(Settings, 'FRONTEND_URL', ''):
                with patch.object(Settings, 'ENVIRONMENT', 'production'):
                    with pytest.raises(ValueError, match="CORS configuration error"):
                        Settings.validate()
    
    def test_settings_validate_success_with_valid_config(self):
        """Test that validation passes with valid configuration."""
        with patch.object(Settings, 'JWT_SECRET', 'test-secret'):
            with patch.object(Settings, 'FRONTEND_URL', 'https://app.example.com'):
                with patch.object(Settings, 'ENVIRONMENT', 'production'):
                    # Should not raise
                    Settings.validate()
    
    def test_normalize_urls_with_trailing_slash(self):
        """Test that trailing slashes are handled correctly."""
        # Trailing slash in root path is acceptable
        with patch.object(Settings, 'ENVIRONMENT', 'production'):
            result = Settings._validate_origin_url("https://app.example.com/")
            # Should still be normalized to without trailing slash
            assert result == "https://app.example.com"
    
    def test_urls_with_ports(self):
        """Test that URLs with explicit ports are handled correctly."""
        test_cases = [
            ("https://app.example.com:8443", "https://app.example.com:8443"),
            ("http://localhost:3000", "http://localhost:3000"),
            ("https://staging.example.com:443", "https://staging.example.com:443"),
        ]
        
        for input_url, expected in test_cases:
            with patch.object(Settings, 'ENVIRONMENT', 'development'):
                result = Settings._validate_origin_url(input_url)
                assert result == expected
    
    def test_subdomains_allowed(self):
        """Test that subdomains are properly validated."""
        test_cases = [
            "https://api.app.example.com",
            "https://staging.api.app.example.com",
            "https://v2.example.com",
        ]
        
        with patch.object(Settings, 'ENVIRONMENT', 'production'):
            for url in test_cases:
                result = Settings._validate_origin_url(url)
                assert result == url
    
    def test_mixed_valid_invalid_urls_raises(self):
        """Test that one invalid URL in list causes failure."""
        frontend_urls = "https://good.example.com,not-valid,https://another.example.com"
        with patch.object(Settings, 'FRONTEND_URL', frontend_urls):
            with patch.object(Settings, 'ENVIRONMENT', 'production'):
                with pytest.raises(ValueError):
                    Settings.get_allowed_origins()
