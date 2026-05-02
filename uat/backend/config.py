"""
backend/config.py
═════════════════
Configuration module with hardened CORS settings and JWT secret validation.
Implements SDT1-56: Harden CORS FRONTEND_URL configuration.
Implements SDT1-63: Harden JWT secret key handling.
"""

import os
import logging
import secrets
import base64
from typing import List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class CORSConfigError(Exception):
    """Raised when CORS configuration is invalid."""
    pass


class JWTConfigError(Exception):
    """Raised when JWT configuration is invalid or insecure."""
    pass


def _is_valid_origin(origin: str) -> bool:
    """
    Validate that an origin is properly formatted.
    
    Args:
        origin: The origin URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    if origin == "*":
        return True
    
    try:
        parsed = urlparse(origin)
        # Must have a scheme (http/https)
        if not parsed.scheme:
            return False
        # Must have a netloc (domain)
        if not parsed.netloc:
            return False
        # Scheme must be http or https
        if parsed.scheme not in ["http", "https"]:
            return False
        # Should not have fragments or query strings
        if parsed.fragment or parsed.query:
            logger.warning(f"Origin {origin} contains fragment or query string, which is unusual")
        return True
    except Exception as e:
        logger.error(f"Failed to parse origin {origin}: {e}")
        return False


def _validate_cors_origins(origins: List[str], allow_wildcard: bool = False) -> None:
    """
    Validate CORS origins for security.
    
    Args:
        origins: List of origin URLs
        allow_wildcard: Whether to allow "*" wildcard
        
    Raises:
        CORSConfigError: If configuration is invalid
    """
    if not origins:
        raise CORSConfigError("No CORS origins configured")
    
    if "*" in origins:
        if not allow_wildcard:
            raise CORSConfigError(
                "Wildcard '*' origin detected in production environment. "
                "Set ALLOW_CORS_WILDCARD=true to explicitly allow this (not recommended)."
            )
        if len(origins) > 1:
            raise CORSConfigError(
                "Cannot mix wildcard '*' with specific origins. "
                "Use either '*' or a list of specific origins."
            )
        logger.warning(
            "⚠️  CORS wildcard '*' is enabled. This allows requests from ANY origin. "
            "This should only be used in development environments."
        )
    
    # Validate each origin
    for origin in origins:
        if origin == "*":
            continue
        if not _is_valid_origin(origin):
            raise CORSConfigError(f"Invalid CORS origin format: {origin}")


def get_cors_origins() -> List[str]:
    """
    Get and validate CORS origins from environment variables.
    
    Environment variables:
        FRONTEND_URL: Single URL or comma-separated list of frontend URLs
        ALLOW_CORS_WILDCARD: Set to 'true' to explicitly allow wildcard in production
        ENVIRONMENT: Set to 'development' or 'production' (default: production)
    
    Returns:
        List of validated CORS origin URLs
        
    Raises:
        CORSConfigError: If CORS configuration is invalid or insecure
    
    Examples:
        # Single origin
        FRONTEND_URL=https://app.example.com
        
        # Multiple origins
        FRONTEND_URL=https://app.example.com,https://admin.example.com
        
        # Development with wildcard
        FRONTEND_URL=*
        ALLOW_CORS_WILDCARD=true
    """
    frontend_url_raw = os.environ.get("FRONTEND_URL", "").strip()
    environment = os.environ.get("ENVIRONMENT", "production").lower()
    allow_wildcard = os.environ.get("ALLOW_CORS_WILDCARD", "false").lower() == "true"
    
    # If no FRONTEND_URL is set, check if wildcard is explicitly allowed
    if not frontend_url_raw:
        if environment == "development":
            logger.warning(
                "No FRONTEND_URL configured in development environment. "
                "Defaulting to localhost:3000"
            )
            return ["http://localhost:3000"]
        else:
            raise CORSConfigError(
                "FRONTEND_URL must be configured. "
                "Set FRONTEND_URL to a comma-separated list of allowed origins."
            )
    
    # Parse origins (comma-separated)
    origins = [origin.strip() for origin in frontend_url_raw.split(",") if origin.strip()]
    
    if not origins:
        raise CORSConfigError("FRONTEND_URL is empty after parsing")
    
    # Validate origins
    _validate_cors_origins(origins, allow_wildcard=allow_wildcard)
    
    # Log configured origins (for debugging)
    if "*" not in origins:
        logger.info(f"CORS configured with {len(origins)} origin(s): {', '.join(origins)}")
    
    return origins


def get_cors_config() -> dict:
    """
    Get complete CORS middleware configuration.
    
    Returns:
        Dictionary with CORS configuration parameters for FastAPI CORSMiddleware
    """
    origins = get_cors_origins()
    
    return {
        "allow_origins": origins,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "allow_headers": ["*"],
        "expose_headers": ["*"],
        "max_age": 600,  # Cache preflight requests for 10 minutes
    }


# ── JWT Configuration ─────────────────────────────────────────────────────────────────


# Known weak secrets that should never be used in production
WEAK_SECRETS = {
    "secret",
    "dev-secret",
    "dev-secret-change-in-production",
    "change-me",
    "changeme",
    "test",
    "testing",
    "development",
    "dev",
    "password",
    "123456",
    "admin",
    "default",
    "example",
    "sample",
    "your-secret-key",
    "your-jwt-secret",
    "jwt-secret-key",
}


def generate_jwt_secret(length: int = 64) -> str:
    """
    Generate a cryptographically secure JWT secret key.
    
    Args:
        length: Number of bytes of entropy (default: 64, which is 512 bits)
        
    Returns:
        Base64-encoded secret key suitable for JWT signing
        
    Examples:
        >>> secret = generate_jwt_secret()
        >>> len(secret) >= 85  # Base64 encoding of 64 bytes
        True
        
    Note:
        Save the generated secret to your environment variables:
        export JWT_SECRET="<generated-secret>"
    """
    if length < 32:
        raise ValueError("JWT secret must be at least 32 bytes (256 bits) for security")
    
    # Generate cryptographically secure random bytes
    secret_bytes = secrets.token_bytes(length)
    
    # Encode as base64 for easy storage in environment variables
    secret_b64 = base64.b64encode(secret_bytes).decode('utf-8')
    
    return secret_b64


def _calculate_entropy_bits(secret: str) -> float:
    """
    Calculate approximate entropy bits of a secret string.
    
    Args:
        secret: The secret string to analyze
        
    Returns:
        Approximate entropy in bits
        
    Note:
        This is a conservative estimate. Real entropy may be lower if
        the string follows predictable patterns.
    """
    import math
    
    # Count unique characters
    unique_chars = len(set(secret))
    
    # Estimate bits per character based on character set
    if unique_chars <= 10:
        # Likely only digits
        bits_per_char = math.log2(10)
    elif unique_chars <= 26:
        # Likely only lowercase or only uppercase
        bits_per_char = math.log2(26)
    elif unique_chars <= 36:
        # Likely alphanumeric (case-insensitive)
        bits_per_char = math.log2(36)
    elif unique_chars <= 62:
        # Likely alphanumeric (case-sensitive)
        bits_per_char = math.log2(62)
    else:
        # Includes special characters
        bits_per_char = math.log2(95)  # Printable ASCII
    
    # Total entropy (conservative estimate)
    return len(secret) * bits_per_char


def _is_weak_jwt_secret(secret: str) -> tuple[bool, str]:
    """
    Check if a JWT secret is weak or insecure.
    
    Args:
        secret: The JWT secret to validate
        
    Returns:
        Tuple of (is_weak, reason)
        
    Examples:
        >>> _is_weak_jwt_secret("secret")
        (True, "Secret is in the list of commonly used weak secrets")
        
        >>> _is_weak_jwt_secret("abc123")
        (True, "Secret is too short (minimum 32 characters recommended)")
    """
    # Check if empty
    if not secret or not secret.strip():
        return True, "JWT secret is empty"
    
    # Check minimum length
    if len(secret) < 32:
        return True, f"Secret is too short (minimum 32 characters recommended, got {len(secret)})"
    
    # Check against known weak secrets
    if secret.lower() in WEAK_SECRETS:
        return True, "Secret is in the list of commonly used weak secrets"
    
    # Check if it's just the default value
    if "change" in secret.lower() or "default" in secret.lower() or "example" in secret.lower():
        return True, "Secret appears to be a default/placeholder value"
    
    # Check entropy (should have at least 128 bits for HS256)
    entropy = _calculate_entropy_bits(secret)
    if entropy < 128:
        return True, f"Secret has low entropy ({entropy:.0f} bits, recommended minimum: 128 bits)"
    
    # Check for repeated characters (e.g., "aaaaaaaaaaaaa...")
    if len(set(secret)) < len(secret) / 4:
        return True, "Secret has too many repeated characters"
    
    return False, ""


def get_jwt_secret() -> str:
    """
    Get and validate JWT secret from environment variables.
    
    Environment variables:
        JWT_SECRET: Secret key for JWT signing (required in production)
        ENVIRONMENT: Set to 'development' or 'production' (default: production)
        ALLOW_WEAK_JWT_SECRET: Set to 'true' to explicitly allow weak secrets in development
        
    Returns:
        Validated JWT secret key
        
    Raises:
        JWTConfigError: If JWT secret is missing, weak, or insecure
        
    Examples:
        # Generate a secure secret (run once, save to environment):
        >>> from config import generate_jwt_secret
        >>> secret = generate_jwt_secret()
        >>> # export JWT_SECRET="<generated-secret>"
        
        # In production (environment variable must be set):
        JWT_SECRET=<your-secure-secret>
        
        # In development (optional, will use a generated secret):
        ENVIRONMENT=development
    """
    environment = os.environ.get("ENVIRONMENT", "production").lower()
    secret = os.environ.get("JWT_SECRET", "").strip()
    allow_weak = os.environ.get("ALLOW_WEAK_JWT_SECRET", "false").lower() == "true"
    
    # In production, JWT_SECRET must be explicitly set
    if not secret:
        if environment == "production":
            raise JWTConfigError(
                "JWT_SECRET environment variable must be set in production. "
                "Generate a secure secret using: python -c \"from config import generate_jwt_secret; print(generate_jwt_secret())\""
            )
        else:
            # In development, generate a temporary secret
            logger.warning(
                "⚠️  No JWT_SECRET configured in development environment. "
                "Generating a temporary secret (tokens will be invalid after restart)."
            )
            return generate_jwt_secret()
    
    # Validate the secret
    is_weak, reason = _is_weak_jwt_secret(secret)
    
    if is_weak:
        if environment == "production":
            raise JWTConfigError(
                f"Insecure JWT secret detected in production: {reason}. "
                "Generate a secure secret using: python -c \"from config import generate_jwt_secret; print(generate_jwt_secret())\""
            )
        elif not allow_weak:
            raise JWTConfigError(
                f"Insecure JWT secret detected: {reason}. "
                "Set ALLOW_WEAK_JWT_SECRET=true to explicitly allow this in development (not recommended), "
                "or generate a secure secret using: python -c \"from config import generate_jwt_secret; print(generate_jwt_secret())\""
            )
        else:
            logger.warning(
                f"⚠️  Weak JWT secret in use: {reason}. "
                "This should only be used in development environments."
            )
    
    logger.info(f"✓ JWT secret configured ({len(secret)} characters, ~{_calculate_entropy_bits(secret):.0f} bits entropy)")
    return secret


def get_jwt_expiry_hours() -> int:
    """
    Get JWT token expiry time in hours from environment variables.
    
    Environment variables:
        JWT_EXPIRY_HOURS: Token expiry time in hours (default: 24)
        
    Returns:
        Token expiry time in hours
        
    Raises:
        JWTConfigError: If JWT_EXPIRY_HOURS is invalid
    """
    expiry_str = os.environ.get("JWT_EXPIRY_HOURS", "24").strip()
    
    try:
        expiry_hours = int(expiry_str)
    except ValueError:
        raise JWTConfigError(f"JWT_EXPIRY_HOURS must be an integer, got: {expiry_str}")
    
    if expiry_hours <= 0:
        raise JWTConfigError(f"JWT_EXPIRY_HOURS must be positive, got: {expiry_hours}")
    
    if expiry_hours > 720:  # 30 days
        logger.warning(
            f"⚠️  JWT_EXPIRY_HOURS is set to {expiry_hours} hours ({expiry_hours / 24:.1f} days). "
            "Long-lived tokens may pose a security risk. Consider using refresh tokens for extended sessions."
        )
    
    return expiry_hours


def get_jwt_config() -> dict:
    """
    Get complete JWT configuration.
    
    Returns:
        Dictionary with JWT configuration parameters
    """
    return {
        "secret": get_jwt_secret(),
        "expiry_hours": get_jwt_expiry_hours(),
        "algorithm": "HS256",
    }
