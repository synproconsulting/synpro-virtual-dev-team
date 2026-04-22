"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common attributes."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user registration request."""
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserResponse(UserBase):
    """Schema for user data in responses."""
    id: int
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Schema for login request."""
    username: str = Field(..., description="Email address")
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded token data."""
    email: Optional[str] = None


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=8, description="New password must be at least 8 characters")


class MessageResponse(BaseModel):
    """Generic message response schema."""
    message: str
