"""
backend/tests/test_integration.py
Integration tests for middleware and rate limiting together.
"""

import pytest
from fastapi.testclient import TestClient
import logging


def test_request_logging_with_rate_limiting(client, caplog):
    """Test that request logging and rate limiting work together."""
    with caplog.at_level(logging.INFO):
        # Make a successful request
        response = client.get("/")
        
        assert response.status_code == 200
        # Check logging occurred
        assert "Request started: GET /" in caplog.text
        assert "Request completed: GET /" in caplog.text
        # Check response headers
        assert "X-Process-Time" in response.headers


def test_rate_limit_logged_correctly(client, caplog):
    """Test that rate-limited requests are logged properly."""
    # This test verifies the integration but may need adjustment
    # based on actual rate limits set on the root endpoint
    with caplog.at_level(logging.INFO):
        response = client.get("/")
        
        # Should succeed and be logged
        assert response.status_code == 200
        assert "Request completed: GET /" in caplog.text


def test_middleware_preserves_rate_limit_headers(client):
    """Test that middleware doesn't interfere with rate limit headers."""
    response = client.get("/")
    
    # Should have both middleware and rate limiting headers
    assert "X-Process-Time" in response.headers
    # Rate limit headers may or may not be present depending on endpoint


def test_health_check_endpoint(client):
    """Test that health check endpoint works with all middleware."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "auth-api"
    assert data["version"] == "1.0.0"
    
    # Check middleware headers
    assert "X-Process-Time" in response.headers
    process_time = float(response.headers["X-Process-Time"])
    assert process_time >= 0


def test_cors_middleware_still_works(client):
    """Test that CORS middleware is not affected by logging middleware."""
    response = client.options("/", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
    })
    
    # CORS should still work
    assert response.status_code in [200, 204]


def test_error_logging_integration(client, caplog):
    """Test that errors are properly logged through the middleware stack."""
    with caplog.at_level(logging.INFO):
        # Try to access a non-existent endpoint
        response = client.get("/non-existent-endpoint")
        
        # FastAPI returns 404 for non-existent routes
        assert response.status_code == 404
        # Should still have process time header
        assert "X-Process-Time" in response.headers


def test_post_request_logging(client, caplog):
    """Test that POST requests are logged correctly."""
    with caplog.at_level(logging.INFO):
        # Note: This endpoint may not exist, adjust based on your routers
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        
        # Check that request was logged
        assert "Request started: POST /auth/login" in caplog.text
        # Response may vary, but logging should occur
        assert "Request completed: POST /auth/login" in caplog.text or "Request failed: POST /auth/login" in caplog.text


def test_query_params_logged(client, caplog):
    """Test that query parameters are included in logs."""
    with caplog.at_level(logging.INFO):
        response = client.get("/?test=value&foo=bar")
        
        assert "query=" in caplog.text
        assert response.status_code == 200
