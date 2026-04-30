"""
backend/rate_limiter.py
Rate limiting functionality for the UAT environment.
"""

import os
from typing import Callable
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request


def get_rate_limit_key(request: Request) -> str:
    """
    Generate a rate limit key based on client IP or user ID.
    
    For authenticated requests, uses user ID from request state.
    For unauthenticated requests, uses IP address.
    
    Args:
        request: FastAPI request object
        
    Returns:
        String key for rate limiting
    """
    # Try to get user ID from request state (set by auth middleware)
    if hasattr(request.state, "user_id") and request.state.user_id:
        return f"user:{request.state.user_id}"
    
    # Fall back to IP address
    return f"ip:{get_remote_address(request)}"


# Configure rate limiter
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[
        os.getenv("RATE_LIMIT_DEFAULT", "100/minute"),
    ],
    storage_uri=os.getenv("RATE_LIMIT_STORAGE_URI", "memory://"),
    strategy="fixed-window",
)


def get_limiter() -> Limiter:
    """
    Get the configured rate limiter instance.
    
    Returns:
        Limiter instance
    """
    return limiter


# Common rate limit decorators
def rate_limit_strict(func: Callable) -> Callable:
    """
    Strict rate limit decorator for sensitive endpoints.
    
    Limit: 10 requests per minute
    """
    return limiter.limit("10/minute")(func)


def rate_limit_moderate(func: Callable) -> Callable:
    """
    Moderate rate limit decorator for standard endpoints.
    
    Limit: 50 requests per minute
    """
    return limiter.limit("50/minute")(func)


def rate_limit_relaxed(func: Callable) -> Callable:
    """
    Relaxed rate limit decorator for high-traffic endpoints.
    
    Limit: 200 requests per minute
    """
    return limiter.limit("200/minute")(func)
