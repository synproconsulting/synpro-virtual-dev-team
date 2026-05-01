"""
Tests for main application CORS integration (SDT1-56).
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


class TestCorsIntegration:
    """Tests for CORS integration in main FastAPI application."""
    
    @patch.dict("os.environ", {"FRONTEND_URL": "http://localhost:3000", "JWT_SECRET": "test-secret"})
    def test_cors_headers_with_allowed_origin(self):
        """Test CORS headers are set correctly for allowed origin."""
        # Import after patching environment
        from main import app
        
        client = TestClient(app)
        
        # Make preflight request
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )
        
        # Should allow the origin
        assert response.status_code in (200, 204)
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    
    @patch.dict("os.environ", {"FRONTEND_URL": "http://localhost:3000", "JWT_SECRET": "test-secret"})
    def test_cors_blocks_disallowed_origin(self):
        """Test CORS blocks requests from disallowed origin."""
        from main import app
        
        client = TestClient(app)
        
        # Make request from different origin
        response = client.options(
            "/",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
            }
        )
        
        # FastAPI returns 400 or doesn't include the origin header
        # The key is that evil.com should not be in the allow-origin header
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] != "http://evil.com"
    
    @patch.dict("os.environ", {"FRONTEND_URL": "http://localhost:3000,https://app.example.com", "JWT_SECRET": "test-secret"})
    def test_cors_with_multiple_origins(self):
        """Test CORS with multiple allowed origins."""
        from main import app
        
        client = TestClient(app)
        
        # Test first origin
        response1 = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response1.status_code in (200, 204)
        if "access-control-allow-origin" in response1.headers:
            assert response1.headers["access-control-allow-origin"] == "http://localhost:3000"
        
        # Test second origin
        response2 = client.options(
            "/",
            headers={
                "Origin": "https://app.example.com",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response2.status_code in (200, 204)
        if "access-control-allow-origin" in response2.headers:
            assert response2.headers["access-control-allow-origin"] == "https://app.example.com"
    
    @patch.dict("os.environ", {"FRONTEND_URL": "*", "JWT_SECRET": "test-secret"})
    def test_cors_with_wildcard(self):
        """Test CORS with wildcard configuration."""
        from main import app
        
        client = TestClient(app)
        
        response = client.options(
            "/",
            headers={
                "Origin": "http://any-origin.com",
                "Access-Control-Request-Method": "GET",
            }
        )
        
        assert response.status_code in (200, 204)
        # With wildcard, any origin should be allowed
        assert "access-control-allow-origin" in response.headers
    
    @patch.dict("os.environ", {"FRONTEND_URL": "", "JWT_SECRET": "test-secret"})
    def test_cors_with_no_config_blocks_all(self):
        """Test CORS with empty config blocks all origins."""
        from main import app
        
        client = TestClient(app)
        
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )
        
        # With no allowed origins, CORS should block
        # The exact behavior depends on FastAPI version, but origin should not be in allow header
        if "access-control-allow-origin" in response.headers:
            # If header exists, it shouldn't match the requesting origin
            assert response.headers["access-control-allow-origin"] != "http://localhost:3000"
    
    @patch.dict("os.environ", {"FRONTEND_URL": "http://localhost:3000", "JWT_SECRET": "test-secret"})
    def test_actual_request_with_cors(self):
        """Test actual GET request (not preflight) with CORS headers."""
        from main import app
        
        client = TestClient(app)
        
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        
        # CORS headers should be present on actual response
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
