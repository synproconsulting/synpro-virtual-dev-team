"""
backend/middleware.py
Request logging middleware for the UAT environment.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import json

# Configure logger
logger = logging.getLogger("uvicorn.access")
logger.setLevel(logging.INFO)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and responses.
    
    Logs:
    - Request method, path, client IP
    - Request headers (excluding sensitive data)
    - Response status code
    - Request processing time
    """
    
    SENSITIVE_HEADERS = {
        "authorization",
        "cookie",
        "x-api-key",
        "x-auth-token",
    }
    
    def __init__(self, app: ASGIApp) -> None:
        """Initialize the middleware."""
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log details.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response from the handler
        """
        start_time = time.time()
        
        # Extract request details
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""
        
        # Log sanitized headers
        headers = self._sanitize_headers(dict(request.headers))
        
        # Log request
        logger.info(
            f"Request started: {method} {path} from {client_ip}"
            + (f" query={query_params}" if query_params else "")
        )
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed: {method} {path} "
                f"status={response.status_code} "
                f"duration={process_time:.3f}s"
            )
            
            # Add custom header with processing time
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {method} {path} "
                f"error={str(e)} "
                f"duration={process_time:.3f}s"
            )
            raise
    
    def _sanitize_headers(self, headers: dict) -> dict:
        """
        Remove sensitive headers from logging.
        
        Args:
            headers: Dictionary of headers
            
        Returns:
            Sanitized headers dictionary
        """
        return {
            k: "***REDACTED***" if k.lower() in self.SENSITIVE_HEADERS else v
            for k, v in headers.items()
        }
