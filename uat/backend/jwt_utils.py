"""
JWT utilities with hardened secret key handling.

Implements SDT1-63: Harden JWT secret key handling
- Validates JWT secret key strength
- Prevents use of weak default secrets in production
- Provides secure JWT encoding/decoding with fixed algorithms
- Supports key rotation mechanisms
"""

import os
import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import jwt

logger = logging.getLogger(__name__)


class JWTConfigError(Exception):
    """Raised when JWT configuration is invalid or insecure."""
    pass


class JWTValidationError(Exception):
    """Raised when JWT validation fails."""
    pass


# Minimum key length in bytes for production (256 bits = 32 bytes)
MIN_SECRET_LENGTH_BYTES = 32

# Known weak secrets that should never be used
WEAK_SECRETS = {
    "dev-secret-change-in-production",
    "secret",
    "secret123",
    "changeme",
    "password",
    "jwt_secret",
    "your-secret-key",
    "my-secret",
    "test-secret",
}


def _is_production_environment() -> bool:
    """
    Check if running in production environment.
    
    Returns:
        True if ENVIRONMENT is set to 'production' or not set (defaults to production)
    """
    env = os.environ.get("ENVIRONMENT", "production").lower()
    return env == "production"


def _validate_secret_strength(secret: str) -> None:
    """
    Validate that the JWT secret meets security requirements.
    
    Args:
        secret: The JWT secret to validate
        
    Raises:
        JWTConfigError: If secret doesn't meet security requirements
    """
    # Check for weak known secrets
    if secret.lower() in WEAK_SECRETS:
        raise JWTConfigError(
            f"Weak or default JWT secret detected. "
            f"The secret '{secret}' is a known weak secret and must not be used. "
            f"Generate a strong secret using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    
    # Check minimum length
    if len(secret) < MIN_SECRET_LENGTH_BYTES:
        raise JWTConfigError(
            f"JWT secret is too short ({len(secret)} characters). "
            f"Minimum required length is {MIN_SECRET_LENGTH_BYTES} characters. "
            f"Generate a strong secret using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    
    # Check for weak patterns in production
    if _is_production_environment():
        # Warn if secret appears to be sequential or repetitive
        if secret == secret[0] * len(secret):  # All same character
            raise JWTConfigError(
                "JWT secret appears to be repetitive (all same character). "
                "Use a cryptographically random secret."
            )
        
        # Check for common patterns
        weak_patterns = ["12345", "abcde", "qwerty", "password"]
        if any(pattern in secret.lower() for pattern in weak_patterns):
            logger.warning(
                "JWT secret contains common weak patterns. "
                "Consider regenerating with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )


def get_jwt_secret() -> str:
    """
    Get and validate the JWT secret from environment.
    
    Environment variables:
        JWT_SECRET: The secret key for signing JWTs (required in production)
        ENVIRONMENT: Set to 'development' or 'production' (default: production)
    
    Returns:
        Validated JWT secret string
        
    Raises:
        JWTConfigError: If JWT_SECRET is not set or doesn't meet security requirements
        
    Examples:
        # Generate a secure secret:
        $ python -c 'import secrets; print(secrets.token_urlsafe(32))'
        
        # Set in environment:
        $ export JWT_SECRET='your-generated-secret-here'
    """
    secret = os.environ.get("JWT_SECRET", "").strip()
    is_production = _is_production_environment()
    
    # JWT_SECRET is required in production
    if not secret:
        if is_production:
            raise JWTConfigError(
                "JWT_SECRET environment variable is required in production. "
                "Generate a secure secret using: "
                "python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        else:
            # In development, generate a temporary secret and warn
            logger.warning(
                "⚠️  JWT_SECRET not set in development environment. "
                "Generating a temporary secret for this session. "
                "Set JWT_SECRET for consistent tokens across restarts."
            )
            secret = secrets.token_urlsafe(32)
            logger.info(f"Generated temporary JWT secret: {secret[:8]}...")
            return secret
    
    # Validate secret strength
    _validate_secret_strength(secret)
    
    if is_production:
        logger.info("✓ JWT secret validated successfully")
    else:
        logger.info("✓ JWT secret validated for development environment")
    
    return secret


def get_jwt_algorithm() -> str:
    """
    Get the JWT signing algorithm to use.
    
    Environment variables:
        JWT_ALGORITHM: Algorithm to use (default: HS256)
        
    Returns:
        JWT algorithm string
        
    Raises:
        JWTConfigError: If specified algorithm is not allowed
    """
    # Allowed symmetric algorithms (we use shared secret)
    ALLOWED_ALGORITHMS = ["HS256", "HS384", "HS512"]
    
    algorithm = os.environ.get("JWT_ALGORITHM", "HS256").upper()
    
    if algorithm not in ALLOWED_ALGORITHMS:
        raise JWTConfigError(
            f"JWT algorithm '{algorithm}' is not allowed. "
            f"Allowed algorithms: {', '.join(ALLOWED_ALGORITHMS)}"
        )
    
    return algorithm


def get_jwt_expiry_hours() -> int:
    """
    Get JWT token expiry time in hours.
    
    Environment variables:
        JWT_EXPIRY_HOURS: Token expiry in hours (default: 24)
        
    Returns:
        Token expiry in hours
        
    Raises:
        JWTConfigError: If expiry value is invalid
    """
    try:
        expiry = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))
    except ValueError:
        raise JWTConfigError("JWT_EXPIRY_HOURS must be an integer")
    
    if expiry < 1:
        raise JWTConfigError("JWT_EXPIRY_HOURS must be at least 1 hour")
    
    if expiry > 168:  # 7 days
        logger.warning(
            f"JWT_EXPIRY_HOURS is set to {expiry} hours ({expiry/24:.1f} days). "
            f"Consider shorter expiry times for better security."
        )
    
    return expiry


class JWTManager:
    """
    Centralized JWT token management with hardened security.
    
    This class provides secure JWT encoding/decoding with:
    - Validated secret keys
    - Fixed algorithm enforcement
    - Key rotation support
    - Proper error handling
    """
    
    def __init__(self) -> None:
        """Initialize JWT manager with validated configuration."""
        self.secret = get_jwt_secret()
        self.algorithm = get_jwt_algorithm()
        self.expiry_hours = get_jwt_expiry_hours()
        
        # Support for key rotation (optional)
        self.old_secret = os.environ.get("JWT_SECRET_OLD", "").strip()
        if self.old_secret:
            try:
                _validate_secret_strength(self.old_secret)
                logger.info("✓ Old JWT secret configured for key rotation")
            except JWTConfigError as e:
                logger.warning(f"JWT_SECRET_OLD validation failed: {e}")
                self.old_secret = ""  # Disable rotation if old key is invalid
    
    def create_token(self, user_id: str, email: str, **extra_claims) -> str:
        """
        Create a JWT token for a user.
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            **extra_claims: Additional claims to include in the token
            
        Returns:
            Encoded JWT token string
            
        Example:
            >>> manager = JWTManager()
            >>> token = manager.create_token("user123", "user@example.com")
        """
        now = datetime.now(timezone.utc)
        
        payload = {
            "sub": user_id,
            "email": email,
            "iat": now,
            "exp": now + timedelta(hours=self.expiry_hours),
            **extra_claims,
        }
        
        try:
            token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
            logger.debug(f"Created JWT token for user {user_id}")
            return token
        except Exception as e:
            logger.error(f"Failed to create JWT token: {e}")
            raise JWTConfigError(f"Failed to encode JWT token: {e}")
    
    def decode_token(self, token: str, verify_exp: bool = True) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: The JWT token to decode
            verify_exp: Whether to verify token expiration (default: True)
            
        Returns:
            Decoded token payload as dictionary
            
        Raises:
            JWTValidationError: If token is invalid, expired, or tampered with
            
        Example:
            >>> manager = JWTManager()
            >>> payload = manager.decode_token(token)
            >>> user_id = payload["sub"]
        """
        options = {
            "verify_signature": True,
            "verify_exp": verify_exp,
            "verify_nbf": False,
            "verify_iat": True,
            "verify_aud": False,
        }
        
        # Try to decode with current secret
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                options=options,
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise JWTValidationError("Token has expired")
        except jwt.InvalidTokenError as e:
            # If we have an old secret, try that (for key rotation)
            if self.old_secret:
                try:
                    logger.debug("Attempting to decode with old secret (key rotation)")
                    payload = jwt.decode(
                        token,
                        self.old_secret,
                        algorithms=[self.algorithm],
                        options=options,
                    )
                    logger.info(f"Token decoded with old secret for user {payload.get('sub')}")
                    return payload
                except jwt.ExpiredSignatureError:
                    raise JWTValidationError("Token has expired")
                except jwt.InvalidTokenError:
                    pass  # Fall through to raise original error
            
            # If we get here, token is invalid
            logger.warning(f"Invalid JWT token: {str(e)}")
            raise JWTValidationError(f"Invalid token: {str(e)}")
    
    def refresh_token(self, old_token: str) -> str:
        """
        Refresh an existing JWT token with a new expiry.
        
        Args:
            old_token: The existing JWT token to refresh
            
        Returns:
            New JWT token with extended expiry
            
        Raises:
            JWTValidationError: If old token is invalid
        """
        # Decode old token (verify_exp=False to allow expired tokens to be refreshed)
        try:
            payload = self.decode_token(old_token, verify_exp=False)
        except JWTValidationError:
            raise JWTValidationError("Cannot refresh invalid token")
        
        # Extract core claims
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id or not email:
            raise JWTValidationError("Token missing required claims")
        
        # Create new token with same claims
        extra_claims = {
            k: v for k, v in payload.items()
            if k not in ["sub", "email", "iat", "exp", "nbf"]
        }
        
        return self.create_token(user_id, email, **extra_claims)


# Module-level singleton instance
_jwt_manager: Optional[JWTManager] = None


def get_jwt_manager() -> JWTManager:
    """
    Get the singleton JWT manager instance.
    
    Returns:
        Initialized JWTManager instance
    """
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = JWTManager()
    return _jwt_manager
