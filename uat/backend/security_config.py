"""
backend/security_config.py
══════════════════════════
Security configuration module with hardened JWT secret key handling.
Implements SDT1-63: Harden JWT secret key handling.
"""

import os
import logging
import secrets
import hashlib
from typing import Optional

logger = logging.getLogger(__name__)


class SecurityConfigError(Exception):
    """Raised when security configuration is invalid."""
    pass


def _calculate_entropy(secret: str) -> float:
    """
    Calculate the Shannon entropy of a string to measure randomness.
    
    Args:
        secret: The secret string to analyze
        
    Returns:
        Entropy value in bits per character (0-8 for byte strings)
    """
    if not secret:
        return 0.0
    
    # Calculate frequency of each byte
    byte_counts = {}
    for char in secret:
        byte_counts[char] = byte_counts.get(char, 0) + 1
    
    # Calculate entropy
    entropy = 0.0
    length = len(secret)
    for count in byte_counts.values():
        probability = count / length
        if probability > 0:
            entropy -= probability * (probability.bit_length() - 1)
    
    return entropy


def _validate_jwt_secret(secret: str, environment: str) -> None:
    """
    Validate JWT secret key for security requirements.
    
    Args:
        secret: The JWT secret key to validate
        environment: The environment (development/production)
        
    Raises:
        SecurityConfigError: If secret doesn't meet security requirements
    """
    if not secret:
        raise SecurityConfigError("JWT_SECRET cannot be empty")
    
    # Check for insecure default/placeholder values
    insecure_patterns = [
        "secret",
        "changeme",
        "change-in-production",
        "dev-secret",
        "default",
        "test",
        "password",
        "12345",
        "example",
        "placeholder",
    ]
    
    secret_lower = secret.lower()
    for pattern in insecure_patterns:
        if pattern in secret_lower:
            if environment == "production":
                raise SecurityConfigError(
                    f"JWT_SECRET contains insecure pattern '{pattern}'. "
                    "In production, use a cryptographically secure random secret."
                )
            else:
                logger.warning(
                    f"⚠️  JWT_SECRET contains pattern '{pattern}'. "
                    "This is acceptable in development but should never be used in production."
                )
    
    # Minimum length requirement (NIST recommends at least 112 bits = 14 bytes for HMAC)
    # For HS256, we want at least 256 bits = 32 bytes
    min_length = 32
    if len(secret) < min_length:
        if environment == "production":
            raise SecurityConfigError(
                f"JWT_SECRET must be at least {min_length} characters long for security. "
                f"Current length: {len(secret)} characters. "
                "Use a cryptographically secure random string."
            )
        else:
            logger.warning(
                f"⚠️  JWT_SECRET is only {len(secret)} characters. "
                f"Recommended minimum: {min_length} characters."
            )
    
    # Check entropy in production
    if environment == "production":
        entropy = _calculate_entropy(secret)
        min_entropy = 4.0  # Should have good randomness
        if entropy < min_entropy:
            logger.warning(
                f"⚠️  JWT_SECRET has low entropy ({entropy:.2f} bits/char). "
                f"Consider using a more random secret (minimum {min_entropy} bits/char recommended). "
                "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(48))'"
            )


def _generate_development_secret() -> str:
    """
    Generate a secure random secret for development use.
    
    Returns:
        A cryptographically secure random string
    """
    return secrets.token_urlsafe(48)


def get_jwt_secret() -> str:
    """
    Get and validate JWT secret from environment variables.
    
    Environment variables:
        JWT_SECRET: The secret key used for JWT signing (required in production)
        ENVIRONMENT: Set to 'development' or 'production' (default: production)
        ALLOW_INSECURE_JWT_SECRET: Set to 'true' to bypass validation (NOT RECOMMENDED)
    
    Returns:
        Validated JWT secret string
        
    Raises:
        SecurityConfigError: If JWT_SECRET is missing or insecure in production
    
    Examples:
        # Production - must set a secure secret
        JWT_SECRET=<generated-secure-random-string>
        ENVIRONMENT=production
        
        # Development - can use auto-generated or custom
        ENVIRONMENT=development
        JWT_SECRET=dev-secret-for-testing  # Optional
        
        # Generate a secure secret:
        python -c 'import secrets; print(secrets.token_urlsafe(48))'
    """
    jwt_secret = os.environ.get("JWT_SECRET", "").strip()
    environment = os.environ.get("ENVIRONMENT", "production").lower()
    allow_insecure = os.environ.get("ALLOW_INSECURE_JWT_SECRET", "false").lower() == "true"
    
    # Production requires explicit JWT_SECRET
    if not jwt_secret:
        if environment == "production":
            raise SecurityConfigError(
                "JWT_SECRET must be set in production environment. "
                "Generate a secure secret with: "
                "python -c 'import secrets; print(secrets.token_urlsafe(48))'"
            )
        else:
            # Auto-generate for development
            logger.warning(
                "⚠️  No JWT_SECRET configured. Auto-generating a random secret for development. "
                "This secret will change on each restart. Set JWT_SECRET to persist sessions."
            )
            jwt_secret = _generate_development_secret()
            logger.info(f"Generated JWT_SECRET: {jwt_secret[:16]}... (truncated)")
    
    # Validate secret (unless explicitly bypassed)
    if not allow_insecure:
        _validate_jwt_secret(jwt_secret, environment)
    else:
        logger.warning(
            "⚠️  JWT_SECRET validation bypassed (ALLOW_INSECURE_JWT_SECRET=true). "
            "This should NEVER be used in production!"
        )
    
    return jwt_secret


def get_jwt_config() -> dict:
    """
    Get complete JWT configuration.
    
    Environment variables:
        JWT_SECRET: The secret key (validated)
        JWT_EXPIRY_HOURS: Token expiry in hours (default: 24)
        JWT_ALGORITHM: Algorithm to use (default: HS256)
    
    Returns:
        Dictionary with JWT configuration parameters
    """
    jwt_secret = get_jwt_secret()
    jwt_expiry = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))
    jwt_algorithm = os.environ.get("JWT_ALGORITHM", "HS256")
    
    # Validate algorithm (only allow HMAC algorithms for symmetric signing)
    allowed_algorithms = ["HS256", "HS384", "HS512"]
    if jwt_algorithm not in allowed_algorithms:
        raise SecurityConfigError(
            f"JWT_ALGORITHM must be one of {allowed_algorithms}. "
            f"Got: {jwt_algorithm}"
        )
    
    # Validate expiry
    if jwt_expiry < 1:
        raise SecurityConfigError("JWT_EXPIRY_HOURS must be at least 1 hour")
    if jwt_expiry > 168:  # 7 days
        logger.warning(
            f"⚠️  JWT_EXPIRY_HOURS is set to {jwt_expiry} hours (>{jwt_expiry/24:.1f} days). "
            "Long-lived tokens pose a security risk if compromised."
        )
    
    return {
        "secret": jwt_secret,
        "expiry_hours": jwt_expiry,
        "algorithm": jwt_algorithm,
    }


def generate_secure_secret() -> str:
    """
    Generate a cryptographically secure secret suitable for JWT signing.
    
    Returns:
        A URL-safe base64-encoded random string (64 characters)
    """
    return secrets.token_urlsafe(48)
