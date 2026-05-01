"""
backend/config.py
Configuration settings for the UAT environment.
"""

import os
from typing import Optional, List
from urllib.parse import urlparse


class Settings:
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "")
    
    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")
    RATE_LIMIT_STORAGE_URI: str = os.getenv("RATE_LIMIT_STORAGE_URI", "memory://")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    @classmethod
    def get_allowed_origins(cls) -> List[str]:
        """
        Get validated allowed CORS origins.
        
        Returns:
            List of allowed origin URLs. Returns ["*"] only in development 
            when FRONTEND_URL is not set.
            
        Raises:
            ValueError: If FRONTEND_URL contains invalid URLs in production
        """
        frontend_url = cls.FRONTEND_URL.strip()
        
        # In production, FRONTEND_URL must be set
        if cls.ENVIRONMENT.lower() in ("production", "prod"):
            if not frontend_url:
                raise ValueError(
                    "FRONTEND_URL must be set in production environment. "
                    "Using '*' is not allowed for security reasons."
                )
        
        # If not set and not production, allow localhost in development
        if not frontend_url:
            if cls.ENVIRONMENT.lower() in ("development", "dev", "local"):
                return [
                    "http://localhost:3000",
                    "http://localhost:5173",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:5173"
                ]
            else:
                raise ValueError(
                    f"FRONTEND_URL must be set in {cls.ENVIRONMENT} environment"
                )
        
        # Parse comma-separated URLs
        urls = [url.strip() for url in frontend_url.split(",") if url.strip()]
        
        if not urls:
            raise ValueError("FRONTEND_URL is set but contains no valid URLs")
        
        # Validate each URL
        validated_origins = []
        for url in urls:
            validated = cls._validate_origin_url(url)
            validated_origins.append(validated)
        
        return validated_origins
    
    @staticmethod
    def _validate_origin_url(url: str) -> str:
        """
        Validate a CORS origin URL.
        
        Args:
            url: The origin URL to validate
            
        Returns:
            The validated and normalized origin URL
            
        Raises:
            ValueError: If the URL is invalid or insecure
        """
        url = url.strip()
        
        # Reject wildcard in production
        if url == "*":
            if Settings.ENVIRONMENT.lower() in ("production", "prod"):
                raise ValueError(
                    "Wildcard '*' origin is not allowed in production. "
                    "Specify explicit frontend URLs."
                )
            return url
        
        # Parse and validate URL structure
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ValueError(f"Invalid URL format '{url}': {e}")
        
        # Must have scheme
        if not parsed.scheme:
            raise ValueError(
                f"URL '{url}' must include scheme (http:// or https://)"
            )
        
        # Validate scheme
        if parsed.scheme not in ("http", "https"):
            raise ValueError(
                f"URL '{url}' must use http or https scheme, not '{parsed.scheme}'"
            )
        
        # Must have netloc (domain/host)
        if not parsed.netloc:
            raise ValueError(f"URL '{url}' must include a domain or host")
        
        # Should not have path, query, or fragment for CORS origin
        if parsed.path and parsed.path != "/":
            raise ValueError(
                f"CORS origin '{url}' should not include path. "
                f"Use only scheme and domain: {parsed.scheme}://{parsed.netloc}"
            )
        
        if parsed.query or parsed.fragment:
            raise ValueError(
                f"CORS origin '{url}' should not include query or fragment. "
                f"Use only scheme and domain: {parsed.scheme}://{parsed.netloc}"
            )
        
        # Warn about http in production
        if parsed.scheme == "http" and Settings.ENVIRONMENT.lower() in ("production", "prod"):
            # Allow http://localhost for local testing scenarios
            if not (parsed.hostname in ("localhost", "127.0.0.1")):
                raise ValueError(
                    f"URL '{url}' uses http scheme in production. "
                    "Use https for security."
                )
        
        # Return normalized origin (scheme + netloc only)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate required settings are present.
        
        Raises:
            ValueError: If required settings are missing or invalid
        """
        required = {
            "JWT_SECRET": cls.JWT_SECRET,
        }
        
        missing = [key for key, value in required.items() if not value]
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        
        # Validate CORS origins configuration
        try:
            origins = cls.get_allowed_origins()
            if not origins:
                raise ValueError("No valid CORS origins configured")
        except ValueError as e:
            raise ValueError(f"CORS configuration error: {e}")


settings = Settings()
