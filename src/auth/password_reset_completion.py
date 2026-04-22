"""
Password reset completion module.

This module handles the completion of password reset flows by validating
reset tokens and updating user passwords securely.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, field_validator


class PasswordResetRequest(BaseModel):
    """Request model for password reset completion."""
    
    token: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        """
        Validate password meets minimum security requirements.
        
        Args:
            value: The password to validate
            
        Returns:
            The validated password
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if len(value) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isupper() for char in value):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in value):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char.isdigit() for char in value):
            raise ValueError('Password must contain at least one digit')
        return value


class PasswordResetResponse(BaseModel):
    """Response model for password reset completion."""
    
    success: bool
    message: str
    email: Optional[EmailStr] = None


class PasswordResetCompletionService:
    """Service for handling password reset completion operations."""
    
    def __init__(self, secret_key: Optional[str] = None, token_expiry_hours: int = 24):
        """
        Initialize the password reset completion service.
        
        Args:
            secret_key: JWT secret key for token validation (defaults to env var)
            token_expiry_hours: Number of hours before reset token expires
        """
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY')
        if not self.secret_key:
            raise ValueError('JWT_SECRET_KEY must be set in environment or provided')
        
        self.token_expiry_hours = token_expiry_hours
        self.pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
        self.algorithm = 'HS256'
    
    def verify_reset_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a password reset token.
        
        Args:
            token: The JWT reset token to verify
            
        Returns:
            Decoded token payload containing user information
            
        Raises:
            jwt.ExpiredSignatureError: If token has expired
            jwt.InvalidTokenError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Validate token type
            if payload.get('type') != 'password_reset':
                raise jwt.InvalidTokenError('Invalid token type')
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError('Password reset token has expired')
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(f'Invalid reset token: {str(e)}')
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password string
        """
        return self.pwd_context.hash(password)
    
    def complete_password_reset(
        self,
        request: PasswordResetRequest,
        update_callback: callable
    ) -> PasswordResetResponse:
        """
        Complete the password reset process.
        
        Args:
            request: Password reset request containing token and new password
            update_callback: Callback function to update user password in database
                           Should accept (user_id, hashed_password) and return bool
            
        Returns:
            PasswordResetResponse with operation result
        """
        try:
            # Verify the reset token
            payload = self.verify_reset_token(request.token)
            
            user_id = payload.get('user_id')
            email = payload.get('email')
            
            if not user_id:
                return PasswordResetResponse(
                    success=False,
                    message='Invalid token: missing user information'
                )
            
            # Hash the new password
            hashed_password = self.hash_password(request.new_password)
            
            # Update password via callback
            success = update_callback(user_id, hashed_password)
            
            if success:
                return PasswordResetResponse(
                    success=True,
                    message='Password has been reset successfully',
                    email=email
                )
            else:
                return PasswordResetResponse(
                    success=False,
                    message='Failed to update password'
                )
                
        except jwt.ExpiredSignatureError:
            return PasswordResetResponse(
                success=False,
                message='Reset token has expired. Please request a new password reset.'
            )
        except jwt.InvalidTokenError as e:
            return PasswordResetResponse(
                success=False,
                message=f'Invalid reset token: {str(e)}'
            )
        except ValueError as e:
            return PasswordResetResponse(
                success=False,
                message=str(e)
            )
        except Exception as e:
            return PasswordResetResponse(
                success=False,
                message=f'An error occurred: {str(e)}'
            )
    
    def generate_reset_token(self, user_id: str, email: str) -> str:
        """
        Generate a password reset token.
        
        Args:
            user_id: Unique identifier for the user
            email: User's email address
            
        Returns:
            JWT reset token string
        """
        expiry = datetime.now(timezone.utc) + timedelta(hours=self.token_expiry_hours)
        
        payload = {
            'user_id': user_id,
            'email': email,
            'type': 'password_reset',
            'exp': expiry,
            'iat': datetime.now(timezone.utc)
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
