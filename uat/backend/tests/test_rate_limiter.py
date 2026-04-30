"""
backend/tests/test_rate_limiter.py
Tests for rate limiting functionality.
"""

import pytest
from fastapi import FastAPI, Request, Depends
from fastapi.testclient import TestClient
from rate_limiter import get_limiter, rate_limit_strict, rate_limit_moderate
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import time


@pytest.fixture
def app():
    """Create a test FastAPI application with rate limiting."""
    test_app = FastAPI()
    limiter = get_limiter()
    test_app.state.limiter = limiter
    test_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    @test_app.get("/strict")
    @limiter.limit("3/minute")
    def strict_endpoint():
        return {"message": "strict"}
    
    @test_app.get("/moderate")
    @limiter.limit("10/minute")
    def moderate_endpoint():
        return {"message": "moderate"}
    
    @test_app.get("/no-limit")
    def no_limit_endpoint():
        return {"message": "no limit"}
    
    return test_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


def test_rate_limit_allows_requests_under_limit(client):
    """Test that requests under the limit are allowed."""
    # Make 3 requests (under the 3/minute limit)
    for i in range(3):
        response = client.get("/strict")
        assert response.status_code == 200
        assert response.json() == {"message": "strict"}


def test_rate_limit_blocks_requests_over_limit(client):
    """Test that requests over the limit are blocked."""
    # Make 3 requests (at the limit)
    for i in range(3):
        response = client.get("/strict")
        assert response.status_code == 200
    
    # 4th request should be rate limited
    response = client.get("/strict")
    assert response.status_code == 429  # Too Many Requests


def test_rate_limit_headers_present(client):
    """Test that rate limit headers are present in response."""
    response = client.get("/strict")
    
    # slowapi should add these headers
    assert "X-RateLimit-Limit" in response.headers or "RateLimit-Limit" in response.headers
    assert response.status_code == 200


def test_different_endpoints_have_independent_limits(client):
    """Test that different endpoints have independent rate limits."""
    # Exhaust strict endpoint
    for i in range(3):
        response = client.get("/strict")
        assert response.status_code == 200
    
    # Strict endpoint should be limited
    response = client.get("/strict")
    assert response.status_code == 429
    
    # Moderate endpoint should still work
    response = client.get("/moderate")
    assert response.status_code == 200
    assert response.json() == {"message": "moderate"}


def test_no_limit_endpoint_unrestricted(client):
    """Test that endpoints without limits are unrestricted."""
    # Make many requests
    for i in range(20):
        response = client.get("/no-limit")
        assert response.status_code == 200
        assert response.json() == {"message": "no limit"}


def test_rate_limit_key_generation():
    """Test rate limit key generation."""
    from rate_limiter import get_rate_limit_key
    from unittest.mock import MagicMock
    
    # Test with IP address
    request = MagicMock()
    request.client.host = "127.0.0.1"
    request.state = MagicMock()
    request.state.user_id = None
    
    key = get_rate_limit_key(request)
    assert key.startswith("ip:")
    
    # Test with user ID
    request.state.user_id = "user123"
    key = get_rate_limit_key(request)
    assert key == "user:user123"


def test_moderate_rate_limit_higher_than_strict(client):
    """Test that moderate limit allows more requests than strict."""
    # Moderate should allow at least 10 requests
    for i in range(10):
        response = client.get("/moderate")
        assert response.status_code == 200
    
    # 11th request should be limited
    response = client.get("/moderate")
    assert response.status_code == 429
