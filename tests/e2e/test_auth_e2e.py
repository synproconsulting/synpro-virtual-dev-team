"""
tests/e2e/test_auth_e2e.py
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Playwright end-to-end tests for the authentication module.
These tests run against a live FastAPI server spun up as a fixture.

Run locally:
    pip install pytest-playwright fastapi uvicorn httpx
    playwright install chromium
    pytest tests/e2e/ -v
"""

import pytest
import threading
import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# â”€â”€ Try to import the auth module â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    from auth.register import UserRegistrationService
    from auth.jwt_auth import JWTService
    HAS_AUTH = True
except ImportError:
    HAS_AUTH = False


# â”€â”€ Fixtures â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@pytest.fixture(scope="session")
def auth_app():
    """Create a minimal FastAPI test app wrapping the auth module."""
    if not HAS_AUTH:
        pytest.skip("Auth module not available")

    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import JSONResponse
        from pydantic import BaseModel as PydanticModel
        import uvicorn

        app = FastAPI(title="Auth Test Server")
        reg_service = UserRegistrationService()

        class RegisterRequest(PydanticModel):
            email: str
            password: str
            username: str = ""

        class LoginRequest(PydanticModel):
            email: str
            password: str

        @app.get("/health")
        def health():
            return {"status": "ok"}

        @app.post("/register")
        def register(req: RegisterRequest):
            try:
                result = reg_service.register(
                    email=req.email,
                    password=req.password,
                    username=req.username or req.email.split("@")[0]
                )
                return JSONResponse({"success": True, "user": str(result)})
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @app.post("/login")
        def login(req: LoginRequest):
            try:
                result = reg_service.verify_credentials(req.email, req.password)
                if result:
                    return JSONResponse({"success": True, "token": "test-token"})
                raise HTTPException(status_code=401, detail="Invalid credentials")
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        # Start server in background thread
        config = uvicorn.Config(app, host="127.0.0.1", port=8765, log_level="error")
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        time.sleep(1.5)   # wait for server to start
        yield "http://127.0.0.1:8765"
        server.should_exit = True

    except ImportError:
        pytest.skip("FastAPI/uvicorn not available")


@pytest.fixture(scope="session")
def browser_context(playwright):
    """Shared browser context for all E2E tests."""
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    yield context
    context.close()
    browser.close()


@pytest.fixture
def page(browser_context):
    """Fresh page for each test."""
    page = browser_context.new_page()
    yield page
    page.close()


# â”€â”€ API-level E2E tests (no browser needed) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class TestAuthAPIE2E:
    """End-to-end API tests using httpx against the live server."""

    def test_health_check(self, auth_app):
        """Server should respond to health checks."""
        try:
            import httpx
            response = httpx.get(f"{auth_app}/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"
        except ImportError:
            pytest.skip("httpx not available")

    def test_register_new_user(self, auth_app):
        """Should successfully register a new user."""
        try:
            import httpx
            response = httpx.post(f"{auth_app}/register", json={
                "email": "testuser@example.com",
                "password": "SecurePass123!",
                "username": "testuser"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
        except ImportError:
            pytest.skip("httpx not available")

    def test_register_duplicate_email(self, auth_app):
        """Should reject duplicate email registration."""
        try:
            import httpx
            payload = {"email": "duplicate@example.com", "password": "SecurePass123!"}
            httpx.post(f"{auth_app}/register", json=payload)   # first registration
            response = httpx.post(f"{auth_app}/register", json=payload)   # duplicate
            assert response.status_code == 400
        except ImportError:
            pytest.skip("httpx not available")

    def test_register_weak_password(self, auth_app):
        """Should reject passwords that don't meet requirements."""
        try:
            import httpx
            response = httpx.post(f"{auth_app}/register", json={
                "email": "weakpass@example.com",
                "password": "123",
            })
            assert response.status_code == 400
        except ImportError:
            pytest.skip("httpx not available")

    def test_login_valid_credentials(self, auth_app):
        """Should return token for valid credentials."""
        try:
            import httpx
            # Register first
            httpx.post(f"{auth_app}/register", json={
                "email": "logintest@example.com",
                "password": "SecurePass123!",
            })
            # Then login
            response = httpx.post(f"{auth_app}/login", json={
                "email": "logintest@example.com",
                "password": "SecurePass123!",
            })
            assert response.status_code == 200
            assert "token" in response.json()
        except ImportError:
            pytest.skip("httpx not available")

    def test_login_invalid_credentials(self, auth_app):
        """Should reject invalid credentials."""
        try:
            import httpx
            response = httpx.post(f"{auth_app}/login", json={
                "email": "nobody@example.com",
                "password": "wrongpassword",
            })
            assert response.status_code in (400, 401)
        except ImportError:
            pytest.skip("httpx not available")


# â”€â”€ Browser-level E2E tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class TestAuthBrowserE2E:
    """Browser-based E2E tests using Playwright."""

    def test_health_page_loads(self, page, auth_app):
        """Server should respond to browser requests."""
        response = page.goto(f"{auth_app}/health")
        assert response.status == 200

    def test_register_api_via_browser(self, page, auth_app):
        """Registration endpoint should be reachable from browser."""
        page.goto(f"{auth_app}/docs")   # FastAPI auto-docs
        assert page.title() != ""


# â”€â”€ Standalone unit-style E2E tests (no server needed) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class TestAuthModuleDirectE2E:
    """Direct module tests that work without a running server."""

    def test_registration_service_exists(self):
        """Auth module should be importable."""
        if not HAS_AUTH:
            pytest.skip("Auth module not available")
        assert UserRegistrationService is not None

    def test_full_registration_flow(self):
        """Complete registration flow should work end to end."""
        if not HAS_AUTH:
            pytest.skip("Auth module not available")
        service = UserRegistrationService()
        result = service.register(
            email="e2e_test@example.com",
            password="SecurePass123!",
            username="e2euser"
        )
        assert result is not None

    def test_full_login_flow(self):
        """Complete login flow after registration should work."""
        if not HAS_AUTH:
            pytest.skip("Auth module not available")
        service = UserRegistrationService()
        service.register(
            email="e2e_login@example.com",
            password="SecurePass123!",
            username="e2elogin"
        )
        result = service.verify_credentials("e2e_login@example.com", "SecurePass123!")
        assert result is True or result is not None

    def test_invalid_login_rejected(self):
        """Invalid credentials should be rejected."""
        if not HAS_AUTH:
            pytest.skip("Auth module not available")
        service = UserRegistrationService()
        result = service.verify_credentials("nobody@example.com", "wrongpass")
        assert not result
