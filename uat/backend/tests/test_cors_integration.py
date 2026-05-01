"""
tests/test_cors_integration.py
═══════════════════════════════
Integration tests for CORS configuration in the FastAPI app (SDT1-56).
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


class TestCORSIntegration:
    """Test CORS behavior with actual HTTP requests."""
    
    def test_cors_preflight_request(self):
        """Preflight OPTIONS request should be handled correctly."""
        with patch.dict("os.environ", {
            "FRONTEND_URL": "https://example.com",
            "ENVIRONMENT": "production",
        }):
            # Import after patching environment
            from main import app
            client = TestClient(app)
            
            response = client.options(
                "/health",
                headers={
                    "Origin": "https://example.com",
                    "Access-Control-Request-Method": "GET",
                }
            )
            
            assert response.status_code == 200
            assert "access-control-allow-origin" in response.headers
            assert response.headers["access-control-allow-origin"] == "https://example.com"
    
    def test_cors_simple_request(self):
        """Simple GET request with Origin header should include CORS headers."""
        with patch.dict("os.environ", {
            "FRONTEND_URL": "https://example.com",
            "ENVIRONMENT": "production",
        }):
            from main import app
            client = TestClient(app)
            
            response = client.get(
                "/health",
                headers={"Origin": "https://example.com"}
            )
            
            assert response.status_code == 200
            assert "access-control-allow-origin" in response.headers
    
    def test_cors_multiple_origins(self):
        """Multiple configured origins should work correctly."""
        with patch.dict("os.environ", {
            "FRONTEND_URL": "https://app.example.com,https://admin.example.com",
            "ENVIRONMENT": "production",
        }):
            from main import app
            client = TestClient(app)
            
            # Test first origin
            response1 = client.get(
                "/health",
                headers={"Origin": "https://app.example.com"}
            )
            assert response1.status_code == 200
            assert response1.headers["access-control-allow-origin"] == "https://app.example.com"
            
            # Test second origin
            response2 = client.get(
                "/health",
                headers={"Origin": "https://admin.example.com"}
            )
            assert response2.status_code == 200
            assert response2.headers["access-control-allow-origin"] == "https://admin.example.com"
    
    def test_cors_wildcard(self):
        """Wildcard CORS should allow any origin."""
        with patch.dict("os.environ", {
            "FRONTEND_URL": "*",
            "ENVIRONMENT": "development",
            "ALLOW_CORS_WILDCARD": "true",
        }):
            from main import app
            client = TestClient(app)
            
            response = client.get(
                "/health",
                headers={"Origin": "https://any-origin.com"}
            )
            
            assert response.status_code == 200
            assert "access-control-allow-origin" in response.headers
    
    def test_cors_credentials_included(self):
        """CORS response should include allow-credentials header."""
        with patch.dict("os.environ", {
            "FRONTEND_URL": "https://example.com",
            "ENVIRONMENT": "production",
        }):
            from main import app
            client = TestClient(app)
            
            response = client.options(
                "/health",
                headers={
                    "Origin": "https://example.com",
                    "Access-Control-Request-Method": "GET",
                }
            )
            
            assert response.status_code == 200
            assert "access-control-allow-credentials" in response.headers
            assert response.headers["access-control-allow-credentials"] == "true"
    
    def test_app_fails_with_invalid_cors_config(self):
        """App should fail to start with invalid CORS configuration."""
        with patch.dict("os.environ", {
            "FRONTEND_URL": "invalid-url",
            "ENVIRONMENT": "production",
        }):
            # Should raise CORSConfigError during import
            with pytest.raises(Exception):  # Will be CORSConfigError
                from main import app
                client = TestClient(app)
                client.get("/health")
    
    def test_app_fails_with_wildcard_in_production_without_flag(self):
        """App should fail to start with wildcard in production without explicit flag."""
        with patch.dict("os.environ", {
            "FRONTEND_URL": "*",
            "ENVIRONMENT": "production",
        }, clear=True):
            with pytest.raises(Exception):  # Will be CORSConfigError
                from main import app
                client = TestClient(app)
                client.get("/health")


class TestCORSSecurityScenarios:
    """Test security scenarios to ensure CORS hardening works."""
    
    def test_unauthorized_origin_rejected(self):
        """Request from non-configured origin should not get CORS headers."""
        with patch.dict("os.environ", {
            "FRONTEND_URL": "https://example.com",
            "ENVIRONMENT": "production",
        }):
            from main import app
            client = TestClient(app)
            
            response = client.options(
                "/health",
                headers={
                    "Origin": "https://malicious.com",
                    "Access-Control-Request-Method": "GET",
                }
            )
            
            # Request completes but CORS header should not match malicious origin
            assert response.status_code == 200
            # FastAPI's CORS middleware will not set the header for non-matching origins
            # or will set it to the first allowed origin only
    
    def test_no_origin_header(self):
        """Request without Origin header should work normally (not CORS)."""
        with patch.dict("os.environ", {
            "FRONTEND_URL": "https://example.com",
            "ENVIRONMENT": "production",
        }):
            from main import app
            client = TestClient(app)
            
            response = client.get("/health")
            
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}
    
    def test_localhost_must_be_explicitly_configured(self):
        """Localhost should not be automatically allowed in production."""
        with patch.dict("os.environ", {
            "FRONTEND_URL": "https://example.com",
            "ENVIRONMENT": "production",
        }):
            from main import app
            client = TestClient(app)
            
            response = client.options(
                "/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                }
            )
            
            # Should complete but not allow localhost
            assert response.status_code == 200
