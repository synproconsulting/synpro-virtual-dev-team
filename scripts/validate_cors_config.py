#!/usr/bin/env python3
"""
Validation script for CORS configuration (SDT1-56).

This script validates CORS environment variables without starting the application.
Useful for CI/CD pipelines and pre-deployment checks.

Usage:
    python scripts/validate_cors_config.py
    
    # With custom environment
    ENVIRONMENT=production FRONTEND_URL=https://app.example.com python scripts/validate_cors_config.py
    
Exit codes:
    0 - Configuration valid
    1 - Configuration invalid
"""

import sys
import os
from typing import List, Tuple


def validate_url_format(url: str, environment: str) -> Tuple[bool, str]:
    """
    Validate a single CORS origin URL.
    
    Args:
        url: The URL to validate
        environment: The deployment environment
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    from urllib.parse import urlparse
    
    url = url.strip()
    
    # Check wildcard
    if url == "*":
        if environment.lower() in ("production", "prod"):
            return False, "Wildcard '*' is not allowed in production"
        return True, ""
    
    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Invalid URL format: {e}"
    
    # Validate scheme
    if not parsed.scheme:
        return False, "URL must include scheme (http:// or https://)"
    
    if parsed.scheme not in ("http", "https"):
        return False, f"URL must use http or https scheme, not '{parsed.scheme}'"
    
    # Validate netloc
    if not parsed.netloc:
        return False, "URL must include a domain or host"
    
    # Check for path/query/fragment
    if parsed.path and parsed.path != "/":
        return False, f"URL should not include path: {parsed.path}"
    
    if parsed.query:
        return False, f"URL should not include query string: {parsed.query}"
    
    if parsed.fragment:
        return False, f"URL should not include fragment: {parsed.fragment}"
    
    # Check HTTP in production
    if parsed.scheme == "http" and environment.lower() in ("production", "prod"):
        if parsed.hostname not in ("localhost", "127.0.0.1"):
            return False, "HTTP URLs not allowed in production (use HTTPS)"
    
    return True, ""


def validate_cors_configuration() -> Tuple[bool, List[str]]:
    """
    Validate complete CORS configuration.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Get environment variables
    environment = os.getenv("ENVIRONMENT", "development").strip()
    frontend_url = os.getenv("FRONTEND_URL", "").strip()
    jwt_secret = os.getenv("JWT_SECRET", "").strip()
    
    print(f"Validating CORS configuration for environment: {environment}")
    print(f"FRONTEND_URL: {frontend_url if frontend_url else '(not set)'}")
    print()
    
    # Validate JWT_SECRET (required)
    if not jwt_secret:
        errors.append("JWT_SECRET must be set")
    
    # Validate FRONTEND_URL based on environment
    if environment.lower() in ("production", "prod"):
        if not frontend_url:
            errors.append("FRONTEND_URL must be set in production environment")
            return False, errors
    elif environment.lower() in ("staging",):
        if not frontend_url:
            errors.append(f"FRONTEND_URL must be set in {environment} environment")
            return False, errors
    elif environment.lower() in ("development", "dev", "local"):
        if not frontend_url:
            print("ℹ️  FRONTEND_URL not set - will use localhost defaults")
            print("   Default origins:")
            print("   - http://localhost:3000")
            print("   - http://localhost:5173")
            print("   - http://127.0.0.1:3000")
            print("   - http://127.0.0.1:5173")
            return len(errors) == 0, errors
    else:
        print(f"⚠️  Unknown environment '{environment}' - treating as staging")
        if not frontend_url:
            errors.append(f"FRONTEND_URL must be set in {environment} environment")
            return False, errors
    
    # Parse and validate URLs
    urls = [u.strip() for u in frontend_url.split(",") if u.strip()]
    
    if not urls:
        errors.append("FRONTEND_URL contains no valid URLs")
        return False, errors
    
    print(f"Found {len(urls)} origin(s) to validate:")
    
    all_valid = True
    for i, url in enumerate(urls, 1):
        is_valid, error = validate_url_format(url, environment)
        
        if is_valid:
            print(f"  {i}. ✅ {url}")
        else:
            print(f"  {i}. ❌ {url}")
            print(f"      Error: {error}")
            errors.append(f"Invalid origin '{url}': {error}")
            all_valid = False
    
    return all_valid and len(errors) == 0, errors


def main():
    """Main validation entry point."""
    print("=" * 70)
    print("CORS Configuration Validator (SDT1-56)")
    print("=" * 70)
    print()
    
    is_valid, errors = validate_cors_configuration()
    
    print()
    print("=" * 70)
    
    if is_valid:
        print("✅ CORS configuration is VALID")
        print("=" * 70)
        return 0
    else:
        print("❌ CORS configuration is INVALID")
        print("=" * 70)
        print()
        print("Errors found:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        print()
        print("Please fix the errors and try again.")
        print("See docs/CORS_SECURITY.md for detailed guidance.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
