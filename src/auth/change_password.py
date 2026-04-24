"""
Change password functionality for user authentication system.

This module provides secure password change operations with proper
validation and password hashing.
"""

import os
from typing import Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from pydantic import BaseModel, Field, validator


# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordChangeRequest(BaseModel):
    """Request model for password change operation."""
    
    user_id: str = Field(..., description="Unique identifier for the user")
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Password confirmation")
    
    @validator('new_password')
    def validate_password_strength(cls, value: str) -> str:
        """
        Validate password meets security requirements.
        
        Args:
            value: The password to validate
            
        Returns:
            The validated password
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(char.islower() for char in value):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit")
        
        if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in value):
            raise ValueError("Password must contain at least one special character")
        
        return value
    
    @validator('confirm_password')
    def passwords_match(cls, value: str, values: dict) -> str:
        """
        Validate that new password and confirmation match.
        
        Args:
            value: The confirmation password
            values: Dictionary containing other field values
            
        Returns:
            The validated confirmation password
            
        Raises:
            ValueError: If passwords don't match
        """
        if 'new_password' in values and value != values['new_password']:
            raise ValueError("Passwords do not match")
        return value


class PasswordChangeResponse(BaseModel):
    """Response model for password change operation."""
    
    success: bool
    message: str
    changed_at: Optional[datetime] = None


class PasswordChangeService:
    """Service class for handling password change operations."""
    
    def __init__(self, user_repository=None):
        """
        Initialize the password change service.
        
        Args:
            user_repository: Repository for user data operations
        """
        self.user_repository = user_repository
        self.max_password_age_days = int(os.getenv("MAX_PASSWORD_AGE_DAYS", "90"))
        self.password_history_count = int(os.getenv("PASSWORD_HISTORY_COUNT", "5"))
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password string
        """
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def check_password_in_history(
        self, 
        user_id: str, 
        new_password: str
    ) -> bool:
        """
        Check if password was recently used.
        
        Args:
            user_id: User identifier
            new_password: New password to check
            
        Returns:
            True if password is in history, False otherwise
        """
        if not self.user_repository:
            return False
        
        password_history = self.user_repository.get_password_history(
            user_id, 
            limit=self.password_history_count
        )
        
        for historical_hash in password_history:
            if self.verify_password(new_password, historical_hash):
                return True
        
        return False
    
    def change_password(
        self, 
        request: PasswordChangeRequest
    ) -> PasswordChangeResponse:
        """
        Change user password with validation.
        
        Args:
            request: Password change request containing user credentials
            
        Returns:
            PasswordChangeResponse indicating success or failure
            
        Raises:
            ValueError: If validation fails
        """
        # Get user from repository
        if not self.user_repository:
            raise ValueError("User repository not configured")
        
        user = self.user_repository.get_user_by_id(request.user_id)
        if not user:
            return PasswordChangeResponse(
                success=False,
                message="User not found"
            )
        
        # Verify current password
        if not self.verify_password(request.current_password, user.get("password_hash", "")):
            return PasswordChangeResponse(
                success=False,
                message="Current password is incorrect"
            )
        
        # Check if new password same as current
        if self.verify_password(request.new_password, user.get("password_hash", "")):
            return PasswordChangeResponse(
                success=False,
                message="New password must be different from current password"
            )
        
        # Check password history
        if self.check_password_in_history(request.user_id, request.new_password):
            return PasswordChangeResponse(
                success=False,
                message=f"Password was recently used. Please choose a different password."
            )
        
        # Hash new password
        new_password_hash = self.hash_password(request.new_password)
        
        # Update password in repository
        changed_at = datetime.utcnow()
        self.user_repository.update_password(
            user_id=request.user_id,
            password_hash=new_password_hash,
            changed_at=changed_at
        )
        
        # Add to password history
        self.user_repository.add_to_password_history(
            user_id=request.user_id,
            password_hash=new_password_hash
        )
        
        return PasswordChangeResponse(
            success=True,
            message="Password changed successfully",
            changed_at=changed_at
        )
    
    def should_force_password_change(self, user_id: str) -> bool:
        """
        Check if user should be forced to change password.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if password change should be forced, False otherwise
        """
        if not self.user_repository:
            return False
        
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            return False
        
        last_changed = user.get("password_changed_at")
        if not last_changed:
            return True  # Force change if never changed
        
        # Check if password is too old
        age_threshold = datetime.utcnow() - timedelta(days=self.max_password_age_days)
        if last_changed < age_threshold:
            return True
        
        return False
