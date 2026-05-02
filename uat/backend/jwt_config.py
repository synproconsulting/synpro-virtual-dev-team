"""
JWT configuration module with hardened secret key handling.

Implements SDT1-63: Harden JWT secret key handling
- Secret key validation (minimum length, entropy)
- Key rotation support for zero-downtime updates
- Secure key storage and access patterns
- Comprehensive error handling and logging
"""

import os
import secrets
import logging
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import jwt

logger = logging.getLogger(__name__)


class JWTConfigError(Exception):
    """Raised when JWT configuration is invalid or insecure."""
    pass


class JWTKeyValidationError(JWTConfigError):
    """Raised when JWT secret key fails security validation."""
    pass


def _calculate_entropy(key: str) -> float:
    """
    Calculate the Shannon entropy of a string.
    
    Args:
        key: The string to analyze
        
    Returns:
        Entropy value in bits per character
    """
    if not key:
        return 0.0
    
    from math import log2
    from collections import Counter
    
    counts = Counter(key)
    length = len(key)
    
    return -sum(count / length * log2(count / length) for count in counts.values())


def _validate_jwt_secret(secret: str, min_length: int = 32, min_entropy: float = 3.5) -> None:
    """
    Validate that a JWT secret meets security requirements.
    
    Args:
        secret: The secret key to validate
        min_length: Minimum required length (default: 32 chars)
        min_entropy: Minimum Shannon entropy (default: 3.5 bits/char)
        
    Raises:
        JWTKeyValidationError: If the secret doesn't meet security requirements
    """
    if not secret:
        raise JWTKeyValidationError("JWT secret cannot be empty")
    
    # Check minimum length
    if len(secret) < min_length:
        raise JWTKeyValidationError(
            f"JWT secret must be at least {min_length} characters long. "
            f"Current length: {len(secret)}. "
            f"Use a cryptographically random string generated with 'openssl rand -base64 32' or similar."
        )
    
    # Check for common weak secrets
    weak_secrets = [
        "secret",
        "dev-secret",
        "dev-secret-change-in-production",
        "change-me",
        "changeme",
        "test-secret",
        "jwt-secret",
        "your-secret-key",
        "your-jwt-secret",
        "supersecret",
        "password",
        "12345678",
        "abcdefgh",
    ]
    
    secret_lower = secret.lower()
    for weak in weak_secrets:
        if weak in secret_lower:
            raise JWTKeyValidationError(
                f"JWT secret contains weak/common pattern: '{weak}'. "
                f"Generate a strong random secret with 'openssl rand -base64 32' or 'python -c \"import secrets; print(secrets.token_urlsafe(32))\"'"
            )
    
    # Check entropy
    entropy = _calculate_entropy(secret)
    if entropy < min_entropy:
        logger.warning(
            f"JWT secret has low entropy ({entropy:.2f} bits/char < {min_entropy} recommended). "
            f"Consider using a more random secret."
        )
    
    # Check for at least some character diversity
    if len(set(secret)) < min_length / 4:
        raise JWTKeyValidationError(
            f"JWT secret has insufficient character diversity. "
            f"Use a cryptographically random string."
        )


def _get_jwt_secrets() -> tuple[str, List[str]]:
    """
    Get JWT secrets with support for key rotation.
    
    Returns primary secret and list of old secrets for validation.
    
    Environment variables:
        JWT_SECRET: Primary secret for signing new tokens (required)
        JWT_SECRET_OLD: Comma-separated list of old secrets for validation during rotation
        
    Returns:
        Tuple of (primary_secret, old_secrets_list)
        
    Raises:
        JWTConfigError: If JWT_SECRET is not configured
        JWTKeyValidationError: If secrets don't meet security requirements
    """
    primary = os.environ.get("JWT_SECRET", "").strip()
    
    if not primary:
        raise JWTConfigError(
            "JWT_SECRET environment variable is required. "
            "Generate a secure secret with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    
    # Validate primary secret
    _validate_jwt_secret(primary)
    
    # Get old secrets for rotation support
    old_secrets_raw = os.environ.get("JWT_SECRET_OLD", "").strip()
    old_secrets = []
    
    if old_secrets_raw:
        old_secrets = [s.strip() for s in old_secrets_raw.split(",") if s.strip()]
        # Validate old secrets too
        for i, old_secret in enumerate(old_secrets):
            try:
                _validate_jwt_secret(old_secret)
            except JWTKeyValidationError as e:
                logger.warning(f"Old JWT secret #{i+1} failed validation: {e}")
    
    return primary, old_secrets


class JWTConfig:
    """
    JWT configuration with hardened secret key handling.
    
    Features:
        - Automatic secret validation on initialization
        - Key rotation support (validate tokens with old keys)
        - Configurable token expiry
        - Secure defaults
    """
    
    def __init__(self):
        """Initialize JWT configuration and validate secrets."""
        self.primary_secret, self.old_secrets = _get_jwt_secrets()
        self.algorithm = "HS256"
        
        # Get token expiry (hours)
        try:
            self.expiry_hours = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))
        except ValueError:
            logger.warning("Invalid JWT_EXPIRY_HOURS value, defaulting to 24 hours")
            self.expiry_hours = 24
        
        # Validate expiry is reasonable
        if self.expiry_hours < 1:
            raise JWTConfigError("JWT_EXPIRY_HOURS must be at least 1 hour")
        if self.expiry_hours > 168:  # 1 week
            logger.warning(
                f"JWT_EXPIRY_HOURS is set to {self.expiry_hours} hours (>{7} days). "
                "Long-lived tokens increase security risk. Consider shorter expiry with refresh tokens."
            )
        
        logger.info(f"✓ JWT configuration initialized (expiry: {self.expiry_hours}h)")
        if self.old_secrets:
            logger.info(f"✓ JWT key rotation enabled ({len(self.old_secrets)} old key(s) configured)")
    
    def create_token(self, user_id: str, email: str, extra_claims: Optional[dict] = None) -> str:
        """
        Create a new JWT token.
        
        Args:
            user_id: User ID to include in token
            email: User email to include in token
            extra_claims: Optional additional claims to include
            
        Returns:
            Encoded JWT token string
            
        Raises:
            JWTConfigError: If token creation fails
        """
        try:
            now = datetime.now(timezone.utc)
            payload = {
                "sub": user_id,
                "email": email,
                "iat": now,
                "exp": now + timedelta(hours=self.expiry_hours),
            }
            
            # Add any extra claims
            if extra_claims:
                payload.update(extra_claims)
            
            token = jwt.encode(payload, self.primary_secret, algorithm=self.algorithm)
            logger.debug(f"Created JWT token for user {user_id}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to create JWT token: {e}")
            raise JWTConfigError(f"Token creation failed: {e}")
    
    def decode_token(self, token: str, verify: bool = True) -> dict:
        """
        Decode and validate a JWT token.
        
        Supports key rotation: tries primary secret first, then old secrets.
        
        Args:
            token: JWT token string to decode
            verify: Whether to verify signature and expiry (default: True)
            
        Returns:
            Decoded token payload
            
        Raises:
            jwt.ExpiredSignatureError: If token has expired
            jwt.InvalidTokenError: If token is invalid
            JWTConfigError: If all decoding attempts fail
        """
        # Try primary secret first
        secrets_to_try = [self.primary_secret] + self.old_secrets
        
        last_error = None
        for i, secret in enumerate(secrets_to_try):
            try:
                payload = jwt.decode(
                    token,
                    secret,
                    algorithms=[self.algorithm],
                    options={"verify_signature": verify, "verify_exp": verify}
                )
                
                # Log if we used an old secret (indicates key rotation in progress)
                if i > 0:
                    logger.info(f"Token validated with old secret #{i} (user: {payload.get('sub')})")
                
                return payload
                
            except jwt.ExpiredSignatureError:
                # Don't try other secrets if token is expired
                logger.debug("Token expired")
                raise
                
            except jwt.InvalidTokenError as e:
                # Try next secret
                last_error = e
                continue
        
        # All secrets failed
        logger.warning(f"Failed to decode token with any configured secret")
        raise last_error or jwt.InvalidTokenError("Invalid token")
    
    def validate_token(self, token: str) -> tuple[bool, Optional[dict], Optional[str]]:
        """
        Validate a JWT token and return result.
        
        This is a higher-level validation method that doesn't raise exceptions,
        instead returning a tuple with validation result and error message.
        
        Args:
            token: JWT token string to validate
            
        Returns:
            Tuple of (is_valid, payload_or_none, error_message_or_none)
            
        Examples:
            >>> is_valid, payload, error = jwt_config.validate_token(token)
            >>> if is_valid:
            ...     user_id = payload["sub"]
            >>> else:
            ...     print(f"Invalid token: {error}")
        """
        try:
            payload = self.decode_token(token)
            return True, payload, None
        except jwt.ExpiredSignatureError:
            return False, None, "Token expired"
        except jwt.InvalidTokenError as e:
            return False, None, f"Invalid token: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error validating token: {e}")
            return False, None, "Token validation failed"
    
    def get_token_expiry(self) -> timedelta:
        """Get the token expiry duration."""
        return timedelta(hours=self.expiry_hours)


# Global JWT config instance (initialized on first import)
_jwt_config: Optional[JWTConfig] = None


def get_jwt_config() -> JWTConfig:
    """
    Get the global JWT configuration instance.
    
    Returns:
        Initialized JWTConfig instance
        
    Raises:
        JWTConfigError: If JWT configuration is invalid
    """
    global _jwt_config
    
    if _jwt_config is None:
        _jwt_config = JWTConfig()
    
    return _jwt_config


def generate_secure_secret(length: int = 32) -> str:
    """
    Generate a cryptographically secure random secret.
    
    Utility function for generating new JWT secrets.
    
    Args:
        length: Length in bytes (default: 32, produces ~43 char base64 string)
        
    Returns:
        URL-safe base64 encoded random string
        
    Example:
        >>> secret = generate_secure_secret()
        >>> print(f"JWT_SECRET={secret}")
    """
    return secrets.token_urlsafe(length)
