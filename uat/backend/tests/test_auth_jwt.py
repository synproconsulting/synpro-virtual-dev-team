"""
Tests for authentication endpoints with hardened JWT handling (SDT1-63).

Tests auth.py endpoints with focus on JWT security.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
import jwt as pyjwt

from jwt_config import generate_secure_secret


@pytest.fixture
def strong_jwt_secret():
    """Generate a strong JWT secret for testing."""
    return generate_secure_secret()


@pytest.fixture
def mock_env(strong_jwt_secret):
    """Mock environment variables with strong JWT secret."""
    env = {
        "JWT_SECRET": strong_jwt_secret,
        "JWT_EXPIRY_HOURS": "24",
        "DATABASE_URL": "postgresql://test:test@localhost/test",
    }
    return env


@pytest.fixture
def client(mock_env):
    """Create FastAPI test client with mocked environment."""
    with patch.dict("os.environ", mock_env, clear=True):
        # Import after patching environment
        import sys
        # Clear module cache to force reload with new env
        if "auth" in sys.modules:
            del sys.modules["auth"]
        if "jwt_config" in sys.modules:
            del sys.modules["jwt_config"]
        
        from auth import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        
        yield TestClient(app)


class TestJWTInRegistration:
    """Test JWT handling in user registration."""
    
    def test_register_returns_valid_jwt(self, client, mock_env, mocker):
        """Registration returns a valid JWT token."""
        # Mock database
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # Email doesn't exist
        mock_db.cursor.return_value = mock_cursor
        
        mocker.patch("auth.get_db", return_value=iter([mock_db]))
        
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "Test123!@#",
            "username": "testuser"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Decode token to verify it's valid
        token = data["access_token"]
        payload = pyjwt.decode(
            token,
            mock_env["JWT_SECRET"],
            algorithms=["HS256"]
        )
        
        assert payload["email"] == "test@example.com"
        assert "sub" in payload
        assert "exp" in payload
        assert "iat" in payload
    
    def test_register_token_expires_correctly(self, client, mock_env, mocker):
        """Registration token has correct expiry."""
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db.cursor.return_value = mock_cursor
        
        mocker.patch("auth.get_db", return_value=iter([mock_db]))
        
        before = datetime.now(timezone.utc)
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "Test123!@#"
        })
        after = datetime.now(timezone.utc)
        
        token = response.json()["access_token"]
        payload = pyjwt.decode(
            token,
            mock_env["JWT_SECRET"],
            algorithms=["HS256"]
        )
        
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_exp_min = before + timedelta(hours=24)
        expected_exp_max = after + timedelta(hours=24)
        
        assert expected_exp_min <= exp <= expected_exp_max


class TestJWTInLogin:
    """Test JWT handling in user login."""
    
    def test_login_returns_valid_jwt(self, client, mock_env, mocker):
        """Login returns a valid JWT token."""
        # Mock database with existing user
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        
        # Import here after env is patched
        from auth import hash_password
        
        mock_cursor.fetchone.return_value = {
            "id": "user123",
            "email": "test@example.com",
            "username": "testuser",
            "password_hash": hash_password("Test123!@#"),
            "created_at": datetime.now(timezone.utc)
        }
        mock_db.cursor.return_value = mock_cursor
        
        mocker.patch("auth.get_db", return_value=iter([mock_db]))
        
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "Test123!@#"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        
        # Verify token
        token = data["access_token"]
        payload = pyjwt.decode(
            token,
            mock_env["JWT_SECRET"],
            algorithms=["HS256"]
        )
        
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"


class TestJWTInGetCurrentUser:
    """Test JWT validation in /me endpoint."""
    
    def test_get_me_with_valid_token(self, client, mock_env, mocker):
        """Valid JWT token returns user info."""
        # Create a valid token
        from jwt_config import JWTConfig
        config = JWTConfig()
        token = config.create_token("user123", "test@example.com")
        
        # Mock database
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": "user123",
            "email": "test@example.com",
            "username": "testuser",
            "created_at": datetime.now(timezone.utc)
        }
        mock_db.cursor.return_value = mock_cursor
        
        mocker.patch("auth.get_db", return_value=iter([mock_db]))
        
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "user123"
        assert data["email"] == "test@example.com"
    
    def test_get_me_with_expired_token(self, client, mock_env, mocker):
        """Expired JWT token returns 401."""
        # Create expired token
        past = datetime.now(timezone.utc) - timedelta(hours=25)
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "iat": past,
            "exp": past + timedelta(hours=1)
        }
        expired_token = pyjwt.encode(
            payload,
            mock_env["JWT_SECRET"],
            algorithm="HS256"
        )
        
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()
    
    def test_get_me_with_invalid_token(self, client, mocker):
        """Invalid JWT token returns 401."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_get_me_with_wrong_secret(self, client, mocker):
        """Token signed with wrong secret returns 401."""
        # Create token with different secret
        wrong_secret = generate_secure_secret()
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        bad_token = pyjwt.encode(payload, wrong_secret, algorithm="HS256")
        
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {bad_token}"}
        )
        
        assert response.status_code == 401
    
    def test_get_me_without_bearer_prefix(self, client, mocker):
        """Token without Bearer prefix returns 401."""
        from jwt_config import JWTConfig
        config = JWTConfig()
        token = config.create_token("user123", "test@example.com")
        
        response = client.get(
            "/auth/me",
            headers={"Authorization": token}  # Missing "Bearer "
        )
        
        assert response.status_code == 401
    
    def test_get_me_without_authorization_header(self, client, mocker):
        """Request without Authorization header returns 401."""
        response = client.get("/auth/me")
        assert response.status_code == 401


class TestJWTKeyRotation:
    """Test JWT key rotation support."""
    
    def test_old_token_validates_after_key_rotation(self, mocker):
        """Token created with old secret validates after rotation."""
        old_secret = generate_secure_secret()
        new_secret = generate_secure_secret()
        
        # Create token with old secret
        with patch.dict("os.environ", {
            "JWT_SECRET": old_secret,
            "DATABASE_URL": "postgresql://test:test@localhost/test"
        }, clear=True):
            import sys
            if "jwt_config" in sys.modules:
                del sys.modules["jwt_config"]
            if "auth" in sys.modules:
                del sys.modules["auth"]
            
            from jwt_config import JWTConfig
            old_config = JWTConfig()
            old_token = old_config.create_token("user123", "test@example.com")
        
        # Validate with new config that includes old secret
        with patch.dict("os.environ", {
            "JWT_SECRET": new_secret,
            "JWT_SECRET_OLD": old_secret,
            "DATABASE_URL": "postgresql://test:test@localhost/test"
        }, clear=True):
            import sys
            if "jwt_config" in sys.modules:
                del sys.modules["jwt_config"]
            if "auth" in sys.modules:
                del sys.modules["auth"]
            
            from jwt_config import JWTConfig
            new_config = JWTConfig()
            
            # Should validate successfully
            payload = new_config.decode_token(old_token)
            assert payload["sub"] == "user123"
    
    def test_new_tokens_use_new_secret(self, mocker):
        """New tokens are signed with new secret after rotation."""
        old_secret = generate_secure_secret()
        new_secret = generate_secure_secret()
        
        with patch.dict("os.environ", {
            "JWT_SECRET": new_secret,
            "JWT_SECRET_OLD": old_secret,
            "DATABASE_URL": "postgresql://test:test@localhost/test"
        }, clear=True):
            import sys
            if "jwt_config" in sys.modules:
                del sys.modules["jwt_config"]
            
            from jwt_config import JWTConfig
            config = JWTConfig()
            token = config.create_token("user123", "test@example.com")
            
            # Should validate with new secret only
            payload = pyjwt.decode(token, new_secret, algorithms=["HS256"])
            assert payload["sub"] == "user123"
            
            # Should NOT validate with old secret alone
            with pytest.raises(pyjwt.InvalidTokenError):
                pyjwt.decode(token, old_secret, algorithms=["HS256"])


class TestJWTSecurityLogging:
    """Test security-related logging for JWT operations."""
    
    def test_failed_login_logs_warning(self, client, mocker, caplog):
        """Failed login attempts are logged."""
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # User not found
        mock_db.cursor.return_value = mock_cursor
        
        mocker.patch("auth.get_db", return_value=iter([mock_db]))
        
        import logging
        with caplog.at_level(logging.WARNING):
            response = client.post("/auth/login", json={
                "email": "nonexistent@example.com",
                "password": "Test123!@#"
            })
        
        assert response.status_code == 401
        # Check that warning was logged
        assert any("Failed login attempt" in record.message for record in caplog.records)
    
    def test_successful_login_logs_info(self, client, mocker, caplog):
        """Successful login is logged."""
        from auth import hash_password
        
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": "user123",
            "email": "test@example.com",
            "username": "testuser",
            "password_hash": hash_password("Test123!@#"),
            "created_at": datetime.now(timezone.utc)
        }
        mock_db.cursor.return_value = mock_cursor
        
        mocker.patch("auth.get_db", return_value=iter([mock_db]))
        
        import logging
        with caplog.at_level(logging.INFO):
            response = client.post("/auth/login", json={
                "email": "test@example.com",
                "password": "Test123!@#"
            })
        
        assert response.status_code == 200
        assert any("User logged in" in record.message for record in caplog.records)
