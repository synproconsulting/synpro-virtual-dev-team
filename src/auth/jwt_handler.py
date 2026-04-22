"""
JWT token generation and validation module.

This module provides utilities for creating and validating JWT tokens
for authentication and authorization purposes.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError


class JWTHandler:
    """
    Handler for JWT token generation and validation.
    
    This class provides methods to create access tokens and refresh tokens,
    as well as validate and decode them.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ):
        """
        Initialize the JWT handler.

        Args:
            secret_key: Secret key for signing tokens. If None, reads from SECRET_KEY env var.
            algorithm: Algorithm to use for encoding/decoding (default: HS256).
            access_token_expire_minutes: Expiration time for access tokens in minutes.
            refresh_token_expire_days: Expiration time for refresh tokens in days.

        Raises:
            ValueError: If secret_key is not provided and SECRET_KEY env var is not set.
        """
        self.secret_key = secret_key or os.getenv("SECRET_KEY")
        if not self.secret_key:
            raise ValueError("SECRET_KEY must be provided or set as environment variable")
        
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    def create_access_token(
        self,
        subject: str,
        additional_claims: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a JWT access token.

        Args:
            subject: The subject (usually user ID or username) for the token.
            additional_claims: Additional claims to include in the token payload.
            expires_delta: Custom expiration time delta. If None, uses default.

        Returns:
            Encoded JWT token as a string.
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)

        to_encode = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        }

        if additional_claims:
            to_encode.update(additional_claims)

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(
        self,
        subject: str,
        additional_claims: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a JWT refresh token.

        Args:
            subject: The subject (usually user ID or username) for the token.
            additional_claims: Additional claims to include in the token payload.
            expires_delta: Custom expiration time delta. If None, uses default.

        Returns:
            Encoded JWT token as a string.
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)

        to_encode = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
        }

        if additional_claims:
            to_encode.update(additional_claims)

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.

        Args:
            token: The JWT token to decode.

        Returns:
            Dictionary containing the token payload.

        Raises:
            JWTError: If the token is invalid or cannot be decoded.
            ExpiredSignatureError: If the token has expired.
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except ExpiredSignatureError:
            raise ExpiredSignatureError("Token has expired")
        except JWTError as e:
            raise JWTError(f"Invalid token: {str(e)}")

    def validate_token(self, token: str, token_type: Optional[str] = None) -> bool:
        """
        Validate a JWT token.

        Args:
            token: The JWT token to validate.
            token_type: Expected token type ('access' or 'refresh'). If None, any type is valid.

        Returns:
            True if the token is valid, False otherwise.
        """
        try:
            payload = self.decode_token(token)
            
            if token_type and payload.get("type") != token_type:
                return False
            
            return True
        except (JWTError, ExpiredSignatureError):
            return False

    def get_token_subject(self, token: str) -> Optional[str]:
        """
        Extract the subject from a JWT token.

        Args:
            token: The JWT token to extract the subject from.

        Returns:
            The subject (sub claim) from the token, or None if extraction fails.
        """
        try:
            payload = self.decode_token(token)
            return payload.get("sub")
        except (JWTError, ExpiredSignatureError):
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Generate a new access token from a valid refresh token.

        Args:
            refresh_token: The refresh token to use for generating a new access token.

        Returns:
            A new access token if the refresh token is valid, None otherwise.
        """
        if not self.validate_token(refresh_token, token_type="refresh"):
            return None

        subject = self.get_token_subject(refresh_token)
        if not subject:
            return None

        return self.create_access_token(subject)
