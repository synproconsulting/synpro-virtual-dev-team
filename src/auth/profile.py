"""
Profile page UI/UX handler module.

This module provides the backend logic for rendering and managing
the user profile page, including data retrieval, validation, and updates.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
import os


class UserProfile(BaseModel):
    """
    User profile data model for UI rendering.
    
    Attributes:
        user_id: Unique identifier for the user
        username: User's username
        email: User's email address
        full_name: User's full name
        bio: User biography/description
        avatar_url: URL to user's profile picture
        created_at: Account creation timestamp
        updated_at: Last profile update timestamp
        is_verified: Email verification status
        phone_number: Optional phone number
        location: Optional user location
        website: Optional website URL
    """
    
    user_id: str
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_verified: bool = False
    phone_number: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    
    @validator('bio')
    def validate_bio(cls, value: Optional[str]) -> Optional[str]:
        """Validate and sanitize bio text."""
        if value:
            # Remove excessive whitespace
            value = ' '.join(value.split())
        return value
    
    @validator('website')
    def validate_website(cls, value: Optional[str]) -> Optional[str]:
        """Validate website URL format."""
        if value and not value.startswith(('http://', 'https://')):
            raise ValueError('Website URL must start with http:// or https://')
        return value


class ProfileUpdateRequest(BaseModel):
    """
    Request model for profile updates.
    
    Only includes fields that users are allowed to update.
    """
    
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    phone_number: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=200)
    
    @validator('phone_number')
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if value:
            # Remove common separators
            cleaned = ''.join(c for c in value if c.isdigit() or c == '+')
            if len(cleaned) < 10:
                raise ValueError('Phone number must be at least 10 digits')
        return value


class ProfileService:
    """
    Service class for profile management operations.
    
    Handles profile retrieval, updates, and avatar management.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize profile service.
        
        Args:
            database_url: Database connection URL (from env if not provided)
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
    
    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Retrieve user profile by user ID.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            UserProfile object if found, None otherwise
        """
        # Database query would go here
        # This is a placeholder for the actual implementation
        pass
    
    async def update_profile(
        self,
        user_id: str,
        update_data: ProfileUpdateRequest
    ) -> UserProfile:
        """
        Update user profile with provided data.
        
        Args:
            user_id: Unique user identifier
            update_data: Profile fields to update
            
        Returns:
            Updated UserProfile object
            
        Raises:
            ValueError: If user not found or validation fails
        """
        # Database update would go here
        # This is a placeholder for the actual implementation
        pass
    
    async def upload_avatar(
        self,
        user_id: str,
        file_data: bytes,
        content_type: str
    ) -> str:
        """
        Upload user avatar image.
        
        Args:
            user_id: Unique user identifier
            file_data: Binary image data
            content_type: MIME type of the image
            
        Returns:
            URL of the uploaded avatar
            
        Raises:
            ValueError: If file type is invalid or upload fails
        """
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        if content_type not in allowed_types:
            raise ValueError(f"Invalid file type. Allowed: {', '.join(allowed_types)}")
        
        max_size = 5 * 1024 * 1024  # 5MB
        if len(file_data) > max_size:
            raise ValueError("File size exceeds 5MB limit")
        
        # Upload logic would go here (S3, CloudStorage, etc.)
        # This is a placeholder for the actual implementation
        pass
    
    async def delete_avatar(self, user_id: str) -> None:
        """
        Delete user avatar and reset to default.
        
        Args:
            user_id: Unique user identifier
        """
        # Avatar deletion logic would go here
        pass


class ProfileUIRenderer:
    """
    UI rendering helper for profile pages.
    
    Provides methods to format profile data for frontend consumption.
    """
    
    @staticmethod
    def format_profile_for_display(profile: UserProfile) -> Dict[str, Any]:
        """
        Format profile data for UI display.
        
        Args:
            profile: UserProfile object
            
        Returns:
            Dictionary with formatted profile data
        """
        return {
            'userId': profile.user_id,
            'username': profile.username,
            'email': profile.email,
            'fullName': profile.full_name or profile.username,
            'bio': profile.bio or '',
            'avatarUrl': profile.avatar_url or ProfileUIRenderer._get_default_avatar(),
            'memberSince': profile.created_at.strftime('%B %Y'),
            'lastUpdated': profile.updated_at.strftime('%Y-%m-%d'),
            'verified': profile.is_verified,
            'contactInfo': {
                'phone': profile.phone_number,
                'location': profile.location,
                'website': profile.website
            }
        }
    
    @staticmethod
    def _get_default_avatar() -> str:
        """
        Get default avatar URL.
        
        Returns:
            URL to default avatar image
        """
        return os.getenv('DEFAULT_AVATAR_URL', '/static/images/default-avatar.png')
    
    @staticmethod
    def get_profile_sections() -> Dict[str, Any]:
        """
        Get UI section configuration for profile page.
        
        Returns:
            Dictionary defining profile page sections and layout
        """
        return {
            'sections': [
                {
                    'id': 'header',
                    'type': 'profile-header',
                    'fields': ['avatarUrl', 'username', 'fullName', 'verified'],
                    'editable': False
                },
                {
                    'id': 'about',
                    'type': 'profile-section',
                    'title': 'About',
                    'fields': ['bio', 'location', 'website', 'memberSince'],
                    'editable': True
                },
                {
                    'id': 'contact',
                    'type': 'profile-section',
                    'title': 'Contact Information',
                    'fields': ['email', 'phone'],
                    'editable': True
                },
                {
                    'id': 'activity',
                    'type': 'profile-section',
                    'title': 'Activity',
                    'fields': ['lastUpdated'],
                    'editable': False
                }
            ],
            'theme': {
                'primaryColor': os.getenv('THEME_PRIMARY_COLOR', '#007bff'),
                'secondaryColor': os.getenv('THEME_SECONDARY_COLOR', '#6c757d'),
                'accentColor': os.getenv('THEME_ACCENT_COLOR', '#28a745')
            }
        }
