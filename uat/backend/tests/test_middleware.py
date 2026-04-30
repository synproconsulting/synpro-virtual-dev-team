"""
backend/tests/test_middleware.py
Tests for request logging middleware.
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from middleware import RequestLoggingMiddleware
import logging


@pytest.fixture
def app():
    """Create a test FastAPI application."""
    test_app = FastAPI()
    test_app.add_middleware(RequestLoggingMiddleware)
    
    @test_app.get("/test")
    def test_endpoint():
        return {"message": "success"}
    
    @test_app.get("/error")
    def error_endpoint():
        raise ValueError("Test error")
    
    @test_app.post("/echo")
    def echo_endpoint(data: dict):
        return data
    
    return test_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


def test_middleware_logs_successful_request(app, client, caplog):
    """Test that middleware logs successful requests."""
    with caplog.at_level(logging.INFO):
        response = client.get("/test")
    
    assert response.status_code == 200
    assert "Request started: GET /test" in caplog.text
    assert "Request completed: GET /test status=200" in caplog.text


def test_middleware_adds_process_time_header(client):
    """Test that middleware adds X-Process-Time header."""
    response = client.get("/test")
    
    assert "X-Process-Time" in response.headers
    process_time = float(response.headers["X-Process-Time"])
    assert process_time >= 0


def test_middleware_logs_request_with_query_params(client, caplog):
    """Test that middleware logs query parameters."""
    with caplog.at_level(logging.INFO):
        response = client.get("/test?foo=bar&baz=qux")
    
    assert response.status_code == 200
    assert "query=" in caplog.text


def test_middleware_logs_failed_request(app, client, caplog):
    """Test that middleware logs failed requests."""
    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError):
            client.get("/error")
    
    assert "Request failed: GET /error" in caplog.text


def test_middleware_sanitizes_sensitive_headers(client, caplog):
    """Test that sensitive headers are redacted in logs."""
    with caplog.at_level(logging.INFO):
        headers = {
            "Authorization": "Bearer secret-token",
            "X-Api-Key": "api-key-123",
            "Content-Type": "application/json",
        }
        response = client.get("/test", headers=headers)
    
    assert response.status_code == 200
    # Sensitive headers should be redacted
    assert "secret-token" not in caplog.text
    assert "api-key-123" not in caplog.text


def test_middleware_handles_post_requests(client, caplog):
    """Test that middleware handles POST requests."""
    with caplog.at_level(logging.INFO):
        response = client.post("/echo", json={"test": "data"})
    
    assert response.status_code == 200
    assert "Request started: POST /echo" in caplog.text
    assert "Request completed: POST /echo status=200" in caplog.text


def test_middleware_measures_duration(client):
    """Test that middleware measures request duration."""
    response = client.get("/test")
    
    process_time = float(response.headers["X-Process-Time"])
    # Should be a small but measurable time
    assert 0 <= process_time < 1.0
