"""
backend/config.py
═════════════════
Configuration module with hardened CORS settings and validation.
Implements SDT1-56: Harden CORS FRONTEND_URL configuration.
"""

import os
import logging
from typing import List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class CORSConfigError(Exception):
    """Raised when CORS configuration is invalid."""
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
