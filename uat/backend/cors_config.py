"""
CORS configuration with hardened security for FRONTEND_URL.

This module provides secure CORS origin parsing and validation.
"""

import os
import re
from typing import List
from urllib.parse import urlparse


def _is_valid_url(url: str) -> bool:
    """
    Validate that a URL has proper structure.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    if url == "*":
        return True
    
    try:
        parsed = urlparse(url)
        
        # Must have scheme (http/https)
        if parsed.scheme not in ("http", "https"):
            return False
        
        # Must have netloc (domain)
        if not parsed.netloc:
            return False
        
        # Should not have username/password
        if parsed.username or parsed.password:
            return False
        
        # Validate domain format
        domain = parsed.netloc.split(":")[0]  # Remove port if present
        if not domain or domain == "":
            return False
        
        # Basic domain validation - allow localhost and proper domains
        if domain == "localhost" or domain == "127.0.0.1":
            return True
        
        # Check for valid domain format (basic check)
        domain_pattern = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
        )
        if not domain_pattern.match(domain):
            return False
        
        return True
    except Exception:
        return False


def _parse_cors_origins(frontend_url_env: str) -> List[str]:
    """
    Parse FRONTEND_URL environment variable into list of valid origins.
    
    Supports:
    - Single URL: "http://localhost:3000"
    - Multiple URLs (comma-separated): "http://localhost:3000,https://app.example.com"
    - Wildcard (insecure, logs warning): "*"
    
    Args:
        frontend_url_env: Raw FRONTEND_URL value from environment
        
    Returns:
        List of validated origin URLs
    """
    if not frontend_url_env or frontend_url_env.strip() == "":
        print("⚠️  WARNING: FRONTEND_URL not set. CORS will block all origins.")
        print("   Set FRONTEND_URL to enable cross-origin requests.")
        return []
    
    # Handle wildcard (insecure)
    if frontend_url_env.strip() == "*":
        print("⚠️  WARNING: CORS configured with wildcard (*) - INSECURE for production!")
        print("   Set FRONTEND_URL to specific origin(s) for production deployment.")
        return ["*"]
    
    # Parse comma-separated origins
    raw_origins = [origin.strip() for origin in frontend_url_env.split(",")]
    valid_origins = []
    invalid_origins = []
    
    for origin in raw_origins:
        if not origin:
            continue
            
        # Normalize: remove trailing slash
        origin = origin.rstrip("/")
        
        if _is_valid_url(origin):
            valid_origins.append(origin)
        else:
            invalid_origins.append(origin)
    
    # Report invalid origins
    if invalid_origins:
        print(f"⚠️  WARNING: Invalid CORS origins ignored: {', '.join(invalid_origins)}")
        print("   Origins must be valid URLs with http:// or https:// scheme.")
    
    # Report valid configuration
    if valid_origins:
        if len(valid_origins) == 1:
            print(f"✓ CORS configured for origin: {valid_origins[0]}")
        else:
            print(f"✓ CORS configured for {len(valid_origins)} origins:")
            for origin in valid_origins:
                print(f"  - {origin}")
    
    return valid_origins


def get_cors_origins() -> List[str]:
    """
    Get validated CORS origins from FRONTEND_URL environment variable.
    
    Returns:
        List of allowed origin URLs for CORS middleware
    """
    frontend_url = os.getenv("FRONTEND_URL", "")
    return _parse_cors_origins(frontend_url)


def format_cors_origins_for_middleware(origins: List[str]) -> List[str]:
    """
    Format origins list for FastAPI CORSMiddleware.
    
    FastAPI's CORSMiddleware expects either ["*"] or a list of specific origins.
    
    Args:
        origins: List of origin URLs
        
    Returns:
        Formatted list suitable for CORSMiddleware allow_origins parameter
    """
    if not origins:
        # No origins = block all cross-origin requests (most secure default)
        return []
    
    if "*" in origins:
        # Wildcard must be alone in list
        return ["*"]
    
    return origins
