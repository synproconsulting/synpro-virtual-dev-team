"""
JWT Token Refresh Mechanism

This module provides functionality for handling JWT token refresh operations,
including access token and refresh token generation, validation, and renewal.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from jose import JWTError, jwt
from passlib.context import CryptContext


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenRefreshError(Exception):
    """Raised when token refresh operations fail."""
    pass


class JWTTokenManager:
    """
    Manages JWT access and refresh tokens.
    
    Handles creation, validation, and refresh of JWT tokens with configurable
    expiration times and secret keys from environment variables.
    """
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7
    ):
        """
        Initialize the JWT Token Manager.
        
        Args:
            secret_key: Secret key for JWT encoding/decoding. 
                       Defaults to JWT_SECRET_KEY env var.
            algorithm: JWT algorithm to use. Defaults to HS256.
            access_token_expire_minutes: Access token expiration in minutes.
            refresh_token_expire_days: Refresh token expiration in days.
        
        Raises:
            ValueError: If secret_key is not provided and JWT_SECRET_KEY 
                       env var is not set.
        """
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY")
        if not self.secret_key:
            raise ValueError(
                "Secret key must be provided or JWT_SECRET_KEY "
                "environment variable must be set"
            )
        
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
    
    def create_access_token(
        self, 
        subject: str, 
        additional_claims: Optional[Dict] = None
    ) -> str:
        """
        Create a new access token.
        
        Args:
            subject: The subject (typically user ID or username).
            additional_claims: Optional additional claims to include.
        
        Returns:
            Encoded JWT access token string.
        """
        expire = datetime.utcnow() + timedelta(
            minutes=self.access_token_expire_minutes
        )
        
        to_encode = {
            "sub": subject,
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow()
        }
        
        if additional_claims:
            to_encode.update(additional_claims)
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        return encoded_jwt
    
    def create_refresh_token(
        self, 
        subject: str, 
        additional_claims: Optional[Dict] = None
    ) -> str:
        """
        Create a new refresh token.
        
        Args:
            subject: The subject (typically user ID or username).
            additional_claims: Optional additional claims to include.
        
        Returns:
            Encoded JWT refresh token string.
        """
        expire = datetime.utcnow() + timedelta(
            days=self.refresh_token_expire_days
        )
        
        to_encode = {
            "sub": subject,
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow()
        }
        
        if additional_claims:
            to_encode.update(additional_claims)
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        return encoded_jwt
    
    def create_token_pair(
        self, 
        subject: str, 
        additional_claims: Optional[Dict] = None
    ) -> Tuple[str, str]:
        """
        Create both access and refresh tokens.
        
        Args:
            subject: The subject (typically user ID or username).
            additional_claims: Optional additional claims to include.
        
        Returns:
            Tuple of (access_token, refresh_token).
        """
        access_token = self.create_access_token(subject, additional_claims)
        refresh_token = self.create_refresh_token(subject, additional_claims)
        return access_token, refresh_token
    
    def decode_token(self, token: str) -> Dict:
        """
        Decode and validate a JWT token.
        
        Args:
            token: The JWT token string to decode.
        
        Returns:
            Dictionary containing the token payload.
        
        Raises:
            TokenRefreshError: If token is invalid or expired.
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except JWTError as e:
            raise TokenRefreshError(f"Invalid token: {str(e)}")
    
    def verify_refresh_token(self, refresh_token: str) -> str:
        """
        Verify a refresh token and extract the subject.
        
        Args:
            refresh_token: The refresh token to verify.
        
        Returns:
            The subject from the token.
        
        Raises:
            TokenRefreshError: If token is invalid, expired, or not a refresh token.
        """
        payload = self.decode_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise TokenRefreshError("Token is not a refresh token")
        
        subject = payload.get("sub")
        if not subject:
            raise TokenRefreshError("Token missing subject")
        
        return subject
    
    def refresh_access_token(
        self, 
        refresh_token: str, 
        additional_claims: Optional[Dict] = None
    ) -> str:
        """
        Generate a new access token using a valid refresh token.
        
        Args:
            refresh_token: Valid refresh token.
            additional_claims: Optional additional claims for the new access token.
        
        Returns:
            New access token string.
        
        Raises:
            TokenRefreshError: If refresh token is invalid.
        """
        subject = self.verify_refresh_token(refresh_token)
        
        # Preserve additional claims from original refresh token if none provided
        if additional_claims is None:
            payload = self.decode_token(refresh_token)
            additional_claims = {
                k: v for k, v in payload.items() 
                if k not in ["sub", "exp", "type", "iat"]
            }
        
        return self.create_access_token(subject, additional_claims)
    
    def refresh_token_pair(
        self, 
        refresh_token: str, 
        additional_claims: Optional[Dict] = None
    ) -> Tuple[str, str]:
        """
        Generate both new access and refresh tokens using a valid refresh token.
        
        Args:
            refresh_token: Valid refresh token.
            additional_claims: Optional additional claims for the new tokens.
        
        Returns:
            Tuple of (new_access_token, new_refresh_token).
        
        Raises:
            TokenRefreshError: If refresh token is invalid.
        """
        subject = self.verify_refresh_token(refresh_token)
        
        # Preserve additional claims from original refresh token if none provided
        if additional_claims is None:
            payload = self.decode_token(refresh_token)
            additional_claims = {
                k: v for k, v in payload.items() 
                if k not in ["sub", "exp", "type", "iat"]
            }
        
        return self.create_token_pair(subject, additional_claims)
    
    def get_token_expiry(self, token: str) -> datetime:
        """
        Get the expiration time of a token.
        
        Args:
            token: The JWT token.
        
        Returns:
            Datetime object representing token expiration.
        
        Raises:
            TokenRefreshError: If token is invalid.
        """
        payload = self.decode_token(token)
        exp_timestamp = payload.get("exp")
        
        if not exp_timestamp:
            raise TokenRefreshError("Token missing expiration")
        
        return datetime.fromtimestamp(exp_timestamp)
    
    def is_token_expired(self, token: str) -> bool:
        """
        Check if a token is expired.
        
        Args:
            token: The JWT token.
        
        Returns:
            True if token is expired, False otherwise.
        """
        try:
            expiry = self.get_token_expiry(token)
            return datetime.utcnow() > expiry
        except TokenRefreshError:
            return True
