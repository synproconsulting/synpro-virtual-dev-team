"""
tests/test_auth_integration.py
═══════════════════════════════
Integration tests for JWT authentication with hardened secret handling (SDT1-63).
"""

import pytest
import os
import base64
from unittest.mock import patch, MagicMock
import jwt
from datetime import datetime, timezone, timedelta

from auth import create_jwt, router
from config import generate_jwt_secret, get_jwt_config, JWTConfigError
from fastapi.testclient import TestClient
from fastapi import FastAPI


@pytest.fixture
def strong_secret():
    """Generate a strong JWT secret for testing."""
    return generate_jwt_secret()


@pytest.fixture
def app_with_strong_secret(strong_secret):
    """Create a FastAPI app with strong JWT secret."""
    with patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "JWT_SECRET": strong_secret,
        "DATABASE_URL": "postgresql://test:test@localhost/test",
    }):
        # Re-import to pick up new config
        from auth import router as auth_router
        
        app = FastAPI()
        app.include_router(auth_router)
        return app


class TestJWTCreationWithHardenedConfig:
    """Test JWT creation with hardened configuration."""
    
    def test_jwt_created_with_validated_secret(self, strong_secret):
        """JWT should be created with validated secret."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": strong_secret,
        }):
            # Force reload of config
            from config import get_jwt_config
            from importlib import reload
            import auth
            reload(auth)
            
            # Create a JWT
            user_id = "test-user-123"
            email = "test@example.com"
            
            token = auth.create_jwt(user_id, email)
            
            # Verify it can be decoded
            payload = jwt.decode(token, strong_secret, algorithms=["HS256"])
            
            assert payload["sub"] == user_id
            assert payload["email"] == email
            assert "exp" in payload
            assert "iat" in payload
    
    def test_jwt_cannot_be_decoded_with_wrong_secret(self, strong_secret):
        """JWT created with one secret cannot be decoded with another."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": strong_secret,
        }):
            from importlib import reload
            import auth
            reload(auth)
            
            token = auth.create_jwt("user-123", "test@example.com")
            
            # Try to decode with different secret
            wrong_secret = generate_jwt_secret()
            
            with pytest.raises(jwt.InvalidTokenError):
                jwt.decode(token, wrong_secret, algorithms=["HS256"])
    
    def test_expired_jwt_rejected(self, strong_secret):
        """Expired JWTs should be rejected."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": strong_secret,
        }):
            # Create an expired token
            payload = {
                "sub": "user-123",
                "email": "test@example.com",
                "iat": datetime.now(timezone.utc) - timedelta(hours=25),
                "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            }
            token = jwt.encode(payload, strong_secret, algorithm="HS256")
            
            with pytest.raises(jwt.ExpiredSignatureError):
                jwt.decode(token, strong_secret, algorithms=["HS256"])


class TestProductionSecurityEnforcement:
    """Test that production environment enforces security."""
    
    def test_production_rejects_missing_secret(self):
        """Production should reject missing JWT secret."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
        }, clear=True):
            with pytest.raises(JWTConfigError, match="JWT_SECRET.*must be set"):
                get_jwt_config()
    
    def test_production_rejects_weak_secret(self):
        """Production should reject weak JWT secrets."""
        weak_secrets = [
            "secret",
            "weak123",
            "dev-secret-change-in-production",
            "password",
            "test",
        ]
        
        for weak_secret in weak_secrets:
            with patch.dict(os.environ, {
                "ENVIRONMENT": "production",
                "JWT_SECRET": weak_secret,
            }):
                with pytest.raises(JWTConfigError, match="Insecure JWT secret"):
                    get_jwt_config()
    
    def test_production_accepts_strong_secret(self, strong_secret):
        """Production should accept strong JWT secrets."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": strong_secret,
        }):
            config = get_jwt_config()
            assert config["secret"] == strong_secret
            assert config["algorithm"] == "HS256"
            assert config["expiry_hours"] == 24


class TestDevelopmentFlexibility:
    """Test that development environment is more flexible."""
    
    def test_development_auto_generates_secret(self):
        """Development should auto-generate secret if missing."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
        }, clear=True):
            config = get_jwt_config()
            
            # Should have generated a secret
            assert len(config["secret"]) >= 85
            # Verify it's valid base64
            base64.b64decode(config["secret"])
    
    def test_development_rejects_weak_by_default(self):
        """Development should reject weak secrets by default."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "JWT_SECRET": "weak123",
        }):
            with pytest.raises(JWTConfigError, match="Insecure JWT secret"):
                get_jwt_config()
    
    def test_development_accepts_weak_with_flag(self):
        """Development can accept weak secrets with explicit flag."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "JWT_SECRET": "weak-but-allowed-for-testing-123",
            "ALLOW_WEAK_JWT_SECRET": "true",
        }):
            config = get_jwt_config()
            assert config["secret"] == "weak-but-allowed-for-testing-123"


class TestJWTExpiryConfiguration:
    """Test JWT expiry configuration."""
    
    def test_default_expiry(self, strong_secret):
        """Default expiry should be 24 hours."""
        with patch.dict(os.environ, {
            "JWT_SECRET": strong_secret,
        }):
            config = get_jwt_config()
            assert config["expiry_hours"] == 24
    
    def test_custom_expiry(self, strong_secret):
        """Custom expiry should be respected."""
        with patch.dict(os.environ, {
            "JWT_SECRET": strong_secret,
            "JWT_EXPIRY_HOURS": "48",
        }):
            config = get_jwt_config()
            assert config["expiry_hours"] == 48
    
    def test_token_expiry_matches_config(self, strong_secret):
        """Created tokens should have expiry matching config."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": strong_secret,
            "JWT_EXPIRY_HOURS": "12",
        }):
            from importlib import reload
            import auth
            reload(auth)
            
            now = datetime.now(timezone.utc)
            token = auth.create_jwt("user-123", "test@example.com")
            
            payload = jwt.decode(token, strong_secret, algorithms=["HS256"])
            
            exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
            
            # Expiry should be 12 hours after issued time
            delta = exp - iat
            assert abs(delta.total_seconds() - 12 * 3600) < 5  # Allow 5 second tolerance


class TestSecretRotation:
    """Test secret rotation scenarios."""
    
    def test_old_tokens_invalid_after_secret_rotation(self, strong_secret):
        """Tokens should be invalid after secret rotation."""
        # Create token with old secret
        old_secret = strong_secret
        token = jwt.encode(
            {
                "sub": "user-123",
                "email": "test@example.com",
                "exp": datetime.now(timezone.utc) + timedelta(hours=24),
            },
            old_secret,
            algorithm="HS256"
        )
        
        # Verify it works with old secret
        payload = jwt.decode(token, old_secret, algorithms=["HS256"])
        assert payload["sub"] == "user-123"
        
        # Rotate to new secret
        new_secret = generate_jwt_secret()
        
        # Token should not work with new secret
        with pytest.raises(jwt.InvalidTokenError):
            jwt.decode(token, new_secret, algorithms=["HS256"])


class TestCrossEnvironmentIsolation:
    """Test that different environments are isolated."""
    
    def test_different_secrets_per_environment(self):
        """Each environment should have different secrets."""
        dev_secret = generate_jwt_secret()
        prod_secret = generate_jwt_secret()
        
        # Create token in dev
        dev_token = jwt.encode(
            {"sub": "user-123", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            dev_secret,
            algorithm="HS256"
        )
        
        # Should not work in prod
        with pytest.raises(jwt.InvalidTokenError):
            jwt.decode(dev_token, prod_secret, algorithms=["HS256"])


class TestErrorMessages:
    """Test that error messages are helpful."""
    
    def test_missing_secret_error_includes_help(self):
        """Error should tell user how to generate secret."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
        }, clear=True):
            try:
                get_jwt_config()
                pytest.fail("Should have raised JWTConfigError")
            except JWTConfigError as e:
                error_message = str(e)
                assert "JWT_SECRET" in error_message
                assert "must be set" in error_message
                assert "generate" in error_message.lower()
    
    def test_weak_secret_error_includes_help(self):
        """Error should tell user how to fix weak secret."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": "weak",
        }):
            try:
                get_jwt_config()
                pytest.fail("Should have raised JWTConfigError")
            except JWTConfigError as e:
                error_message = str(e)
                assert "Insecure" in error_message
                assert "generate" in error_message.lower()


class TestBackwardsCompatibility:
    """Test backwards compatibility with existing deployments."""
    
    def test_existing_strong_secrets_still_work(self):
        """Existing deployments with strong secrets should continue working."""
        # Simulate an existing strong secret (e.g., from before this change)
        existing_secret = base64.b64encode(os.urandom(64)).decode('utf-8')
        
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": existing_secret,
        }):
            config = get_jwt_config()
            assert config["secret"] == existing_secret
    
    def test_env_var_names_unchanged(self):
        """Environment variable names should remain the same."""
        strong_secret = generate_jwt_secret()
        
        with patch.dict(os.environ, {
            "JWT_SECRET": strong_secret,  # Original name
            "JWT_EXPIRY_HOURS": "24",     # Original name
        }):
            config = get_jwt_config()
            assert config["secret"] == strong_secret
            assert config["expiry_hours"] == 24
