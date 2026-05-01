"""
backend/config.py
Configuration settings for the UAT environment.
"""

import os
from typing import Optional, List
from cors_config import get_cors_origins, format_cors_origins_for_middleware


class Settings:
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Frontend - use hardened CORS configuration
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
    
    @classmethod
    def get_cors_origins(cls) -> List[str]:
        """
        Get validated and parsed CORS origins.
        
        Returns:
            List of allowed origin URLs
        """
        origins = get_cors_origins()
        return format_cors_origins_for_middleware(origins)
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate required settings are present.
        
        Raises:
            ValueError: If required settings are missing
        """
        required = {
            "JWT_SECRET": cls.JWT_SECRET,
        }
        
        missing = [key for key, value in required.items() if not value]
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )


settings = Settings()
