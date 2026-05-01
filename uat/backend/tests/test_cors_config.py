"""
Tests for CORS configuration hardening (SDT1-56).
"""

import pytest
from unittest.mock import patch
from cors_config import (
    _is_valid_url,
    _parse_cors_origins,
    get_cors_origins,
    format_cors_origins_for_middleware,
)


class TestUrlValidation:
    """Tests for URL validation."""
    
    def test_valid_http_localhost(self):
        """Test valid localhost HTTP URL."""
        assert _is_valid_url("http://localhost:3000") is True
    
    def test_valid_https_localhost(self):
        """Test valid localhost HTTPS URL."""
        assert _is_valid_url("https://localhost:3000") is True
    
    def test_valid_domain(self):
        """Test valid domain URL."""
        assert _is_valid_url("https://app.example.com") is True
    
    def test_valid_subdomain(self):
        """Test valid subdomain URL."""
        assert _is_valid_url("https://staging.app.example.com") is True
    
    def test_valid_ip_address(self):
        """Test valid IP address URL."""
        assert _is_valid_url("http://127.0.0.1:8080") is True
    
    def test_wildcard(self):
        """Test wildcard is considered valid."""
        assert _is_valid_url("*") is True
    
    def test_invalid_no_scheme(self):
        """Test URL without scheme is invalid."""
        assert _is_valid_url("localhost:3000") is False
        assert _is_valid_url("example.com") is False
    
    def test_invalid_wrong_scheme(self):
        """Test URL with wrong scheme is invalid."""
        assert _is_valid_url("ftp://example.com") is False
        assert _is_valid_url("ws://example.com") is False
    
    def test_invalid_no_domain(self):
        """Test URL without domain is invalid."""
        assert _is_valid_url("http://") is False
        assert _is_valid_url("https://") is False
    
    def test_invalid_with_credentials(self):
        """Test URL with username/password is invalid."""
        assert _is_valid_url("http://user:pass@example.com") is False
    
    def test_invalid_empty_string(self):
        """Test empty string is invalid."""
        assert _is_valid_url("") is False
    
    def test_invalid_malformed(self):
        """Test malformed URLs are invalid."""
        assert _is_valid_url("not a url") is False
        assert _is_valid_url("http://invalid domain.com") is False


class TestCorsOriginParsing:
    """Tests for CORS origin parsing."""
    
    def test_single_valid_origin(self, capsys):
        """Test parsing single valid origin."""
        result = _parse_cors_origins("http://localhost:3000")
        assert result == ["http://localhost:3000"]
        
        captured = capsys.readouterr()
        assert "✓ CORS configured for origin: http://localhost:3000" in captured.out
    
    def test_multiple_valid_origins(self, capsys):
        """Test parsing multiple valid origins."""
        result = _parse_cors_origins(
            "http://localhost:3000,https://staging.example.com,https://app.example.com"
        )
        assert len(result) == 3
        assert "http://localhost:3000" in result
        assert "https://staging.example.com" in result
        assert "https://app.example.com" in result
        
        captured = capsys.readouterr()
        assert "✓ CORS configured for 3 origins:" in captured.out
    
    def test_wildcard_origin(self, capsys):
        """Test wildcard origin with warning."""
        result = _parse_cors_origins("*")
        assert result == ["*"]
        
        captured = capsys.readouterr()
        assert "WARNING: CORS configured with wildcard (*)" in captured.out
        assert "INSECURE for production" in captured.out
    
    def test_empty_string(self, capsys):
        """Test empty FRONTEND_URL."""
        result = _parse_cors_origins("")
        assert result == []
        
        captured = capsys.readouterr()
        assert "WARNING: FRONTEND_URL not set" in captured.out
    
    def test_whitespace_only(self, capsys):
        """Test whitespace-only FRONTEND_URL."""
        result = _parse_cors_origins("   ")
        assert result == []
        
        captured = capsys.readouterr()
        assert "WARNING: FRONTEND_URL not set" in captured.out
    
    def test_trailing_slashes_removed(self):
        """Test trailing slashes are removed from origins."""
        result = _parse_cors_origins("http://localhost:3000/")
        assert result == ["http://localhost:3000"]
        
        result = _parse_cors_origins("https://app.example.com/,https://staging.example.com/")
        assert "https://app.example.com" in result
        assert "https://staging.example.com" in result
        assert "https://app.example.com/" not in result
    
    def test_mixed_valid_invalid_origins(self, capsys):
        """Test mix of valid and invalid origins."""
        result = _parse_cors_origins(
            "http://localhost:3000,invalid-url,https://app.example.com,not-a-url"
        )
        assert len(result) == 2
        assert "http://localhost:3000" in result
        assert "https://app.example.com" in result
        
        captured = capsys.readouterr()
        assert "WARNING: Invalid CORS origins ignored:" in captured.out
        assert "invalid-url" in captured.out
        assert "not-a-url" in captured.out
    
    def test_empty_items_in_list(self):
        """Test comma-separated list with empty items."""
        result = _parse_cors_origins("http://localhost:3000,,https://app.example.com,")
        assert len(result) == 2
        assert "http://localhost:3000" in result
        assert "https://app.example.com" in result
    
    def test_whitespace_in_list(self):
        """Test origins with whitespace are trimmed."""
        result = _parse_cors_origins(
            " http://localhost:3000 , https://app.example.com "
        )
        assert len(result) == 2
        assert "http://localhost:3000" in result
        assert "https://app.example.com" in result


class TestGetCorsOrigins:
    """Tests for get_cors_origins function."""
    
    @patch.dict("os.environ", {"FRONTEND_URL": "http://localhost:3000"})
    def test_get_from_environment(self):
        """Test reading FRONTEND_URL from environment."""
        result = get_cors_origins()
        assert result == ["http://localhost:3000"]
    
    @patch.dict("os.environ", {}, clear=True)
    def test_get_with_no_env_var(self):
        """Test with no FRONTEND_URL in environment."""
        result = get_cors_origins()
        assert result == []
    
    @patch.dict("os.environ", {"FRONTEND_URL": "http://localhost:3000,https://app.example.com"})
    def test_get_multiple_from_environment(self):
        """Test reading multiple origins from environment."""
        result = get_cors_origins()
        assert len(result) == 2
        assert "http://localhost:3000" in result
        assert "https://app.example.com" in result


class TestFormatCorsOriginsForMiddleware:
    """Tests for formatting origins for FastAPI middleware."""
    
    def test_format_empty_list(self):
        """Test formatting empty list."""
        result = format_cors_origins_for_middleware([])
        assert result == []
    
    def test_format_single_origin(self):
        """Test formatting single origin."""
        result = format_cors_origins_for_middleware(["http://localhost:3000"])
        assert result == ["http://localhost:3000"]
    
    def test_format_multiple_origins(self):
        """Test formatting multiple origins."""
        origins = [
            "http://localhost:3000",
            "https://staging.example.com",
            "https://app.example.com",
        ]
        result = format_cors_origins_for_middleware(origins)
        assert result == origins
    
    def test_format_wildcard(self):
        """Test wildcard is preserved."""
        result = format_cors_origins_for_middleware(["*"])
        assert result == ["*"]
    
    def test_format_wildcard_with_others(self):
        """Test wildcard with other origins returns only wildcard."""
        # This shouldn't happen in practice, but ensure safe behavior
        result = format_cors_origins_for_middleware(["*", "http://localhost:3000"])
        assert result == ["*"]


class TestIntegration:
    """Integration tests for full CORS configuration flow."""
    
    @patch.dict("os.environ", {"FRONTEND_URL": "http://localhost:3000,https://app.example.com"})
    def test_full_flow_multiple_origins(self):
        """Test complete flow from env var to middleware format."""
        origins = get_cors_origins()
        formatted = format_cors_origins_for_middleware(origins)
        
        assert len(formatted) == 2
        assert "http://localhost:3000" in formatted
        assert "https://app.example.com" in formatted
    
    @patch.dict("os.environ", {"FRONTEND_URL": "*"})
    def test_full_flow_wildcard(self):
        """Test complete flow with wildcard."""
        origins = get_cors_origins()
        formatted = format_cors_origins_for_middleware(origins)
        
        assert formatted == ["*"]
    
    @patch.dict("os.environ", {}, clear=True)
    def test_full_flow_no_config(self):
        """Test complete flow with no configuration."""
        origins = get_cors_origins()
        formatted = format_cors_origins_for_middleware(origins)
        
        assert formatted == []
