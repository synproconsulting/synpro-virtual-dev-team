"""
Profile management module for user profile operations.

This module provides functions for managing user profiles including
retrieval, updates, and password changes.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
from passlib.context import CryptContext


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ProfileBase(BaseModel):
    """Base profile model with common fields."""
    
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    
    @validator('phone_number')
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v is not None:
            # Remove spaces and dashes for validation
            cleaned = v.replace(' ', '').replace('-', '')
            if not cleaned.replace('+', '').isdigit():
                raise ValueError('Phone number must contain only digits, spaces, dashes, and optional + prefix')
        return v


class ProfileUpdate(ProfileBase):
    """Model for profile update requests."""
    pass


class ProfileResponse(ProfileBase):
    """Model for profile response with additional metadata."""
    
    user_id: str
    username: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class PasswordChangeRequest(BaseModel):
    """Model for password change requests."""
    
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_new_password(cls, v: str, values: Dict[str, Any]) -> str:
        """Validate new password requirements."""
        if 'current_password' in values and v == values['current_password']:
            raise ValueError('New password must be different from current password')
        
        # Check password complexity
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v: str, values: Dict[str, Any]) -> str:
        """Validate that passwords match."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class ProfileService:
    """Service class for profile management operations."""
    
    def __init__(self, database_connection: Any):
        """
        Initialize the profile service.
        
        Args:
            database_connection: Database connection or session object
        """
        self.db = database_connection
    
    async def get_profile(self, user_id: str) -> Optional[ProfileResponse]:
        """
        Retrieve user profile by user ID.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            ProfileResponse object if found, None otherwise
        """
        # In a real implementation, this would query the database
        # Example: user = await self.db.query(User).filter(User.id == user_id).first()
        raise NotImplementedError("Database integration required")
    
    async def update_profile(
        self, 
        user_id: str, 
        profile_data: ProfileUpdate
    ) -> ProfileResponse:
        """
        Update user profile with provided data.
        
        Args:
            user_id: The unique identifier of the user
            profile_data: Profile update data
            
        Returns:
            Updated ProfileResponse object
            
        Raises:
            ValueError: If user not found
        """
        # In a real implementation, this would update the database
        # Example:
        # user = await self.db.query(User).filter(User.id == user_id).first()
        # if not user:
        #     raise ValueError("User not found")
        # for field, value in profile_data.dict(exclude_unset=True).items():
        #     setattr(user, field, value)
        # user.updated_at = datetime.utcnow()
        # await self.db.commit()
        # return ProfileResponse.from_orm(user)
        raise NotImplementedError("Database integration required")
    
    async def change_password(
        self, 
        user_id: str, 
        password_change: PasswordChangeRequest
    ) -> bool:
        """
        Change user password after validating current password.
        
        Args:
            user_id: The unique identifier of the user
            password_change: Password change request data
            
        Returns:
            True if password changed successfully
            
        Raises:
            ValueError: If current password is incorrect or user not found
        """
        # In a real implementation:
        # user = await self.db.query(User).filter(User.id == user_id).first()
        # if not user:
        #     raise ValueError("User not found")
        # if not verify_password(password_change.current_password, user.hashed_password):
        #     raise ValueError("Current password is incorrect")
        # user.hashed_password = hash_password(password_change.new_password)
        # user.updated_at = datetime.utcnow()
        # await self.db.commit()
        # return True
        raise NotImplementedError("Database integration required")
    
    async def deactivate_profile(self, user_id: str) -> bool:
        """
        Deactivate user profile (soft delete).
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            True if profile deactivated successfully
            
        Raises:
            ValueError: If user not found
        """
        # In a real implementation:
        # user = await self.db.query(User).filter(User.id == user_id).first()
        # if not user:
        #     raise ValueError("User not found")
        # user.is_active = False
        # user.updated_at = datetime.utcnow()
        # await self.db.commit()
        # return True
        raise NotImplementedError("Database integration required")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)
