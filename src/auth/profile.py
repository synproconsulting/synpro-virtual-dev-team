"""
Profile page module for user profile management.

This module provides the backend functionality for rendering and managing
user profile pages, including profile data retrieval, updates, and validation.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
import os


class ProfileData(BaseModel):
    """User profile data model."""
    
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=200)
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    
    @validator('username')
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()
    
    @validator('website')
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        """Validate website URL format."""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Website must be a valid URL starting with http:// or https://')
        return v


class ProfileUpdateRequest(BaseModel):
    """Request model for profile updates."""
    
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=200)
    
    @validator('website')
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        """Validate website URL format."""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Website must be a valid URL starting with http:// or https://')
        return v


class ProfileService:
    """Service class for profile management operations."""
    
    def __init__(self, database_connection: Any = None):
        """
        Initialize the ProfileService.
        
        Args:
            database_connection: Database connection instance
        """
        self.db = database_connection
    
    async def get_profile(self, user_id: str) -> Optional[ProfileData]:
        """
        Retrieve user profile by user ID.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            ProfileData object if found, None otherwise
        """
        # In production, this would query the database
        # For now, returning a mock implementation structure
        if not self.db:
            return None
        
        # Example query structure
        query = "SELECT * FROM user_profiles WHERE user_id = %s AND is_active = TRUE"
        result = await self._execute_query(query, (user_id,))
        
        if result:
            return ProfileData(**result)
        return None
    
    async def update_profile(
        self, 
        user_id: str, 
        update_data: ProfileUpdateRequest
    ) -> Optional[ProfileData]:
        """
        Update user profile information.
        
        Args:
            user_id: Unique user identifier
            update_data: Profile update data
            
        Returns:
            Updated ProfileData object if successful, None otherwise
        """
        if not self.db:
            return None
        
        update_fields = update_data.dict(exclude_unset=True)
        if not update_fields:
            return await self.get_profile(user_id)
        
        update_fields['updated_at'] = datetime.utcnow()
        
        # Build dynamic update query
        set_clause = ", ".join([f"{key} = %s" for key in update_fields.keys()])
        query = f"UPDATE user_profiles SET {set_clause} WHERE user_id = %s"
        values = list(update_fields.values()) + [user_id]
        
        await self._execute_query(query, tuple(values))
        
        return await self.get_profile(user_id)
    
    async def delete_profile(self, user_id: str) -> bool:
        """
        Soft delete user profile (set is_active to False).
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db:
            return False
        
        query = "UPDATE user_profiles SET is_active = FALSE, updated_at = %s WHERE user_id = %s"
        result = await self._execute_query(query, (datetime.utcnow(), user_id))
        
        return result is not None
    
    async def _execute_query(self, query: str, params: tuple) -> Optional[Dict[str, Any]]:
        """
        Execute database query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result as dictionary or None
        """
        # Placeholder for actual database execution
        # In production, this would use actual database connection
        pass


class ProfileUIRenderer:
    """Handles profile page UI rendering and layout structure."""
    
    @staticmethod
    def render_profile_layout(profile: ProfileData) -> Dict[str, Any]:
        """
        Generate profile page layout structure.
        
        Args:
            profile: ProfileData object
            
        Returns:
            Dictionary containing UI layout structure
        """
        return {
            "layout": "profile-page",
            "sections": [
                {
                    "type": "header",
                    "data": {
                        "avatar": profile.avatar_url or "/static/default-avatar.png",
                        "username": profile.username,
                        "full_name": profile.full_name or profile.username,
                        "bio": profile.bio or "",
                    }
                },
                {
                    "type": "stats",
                    "data": {
                        "member_since": profile.created_at.strftime("%B %Y"),
                        "last_updated": profile.updated_at.strftime("%B %d, %Y"),
                    }
                },
                {
                    "type": "contact_info",
                    "data": {
                        "email": profile.email,
                        "phone": profile.phone,
                        "location": profile.location,
                        "website": profile.website,
                    }
                },
                {
                    "type": "actions",
                    "data": {
                        "can_edit": True,
                        "edit_url": f"/profile/{profile.user_id}/edit",
                    }
                }
            ],
            "theme": "modern",
            "responsive": True
        }
    
    @staticmethod
    def render_edit_form(profile: ProfileData) -> Dict[str, Any]:
        """
        Generate profile edit form structure.
        
        Args:
            profile: ProfileData object
            
        Returns:
            Dictionary containing edit form structure
        """
        return {
            "form": "profile-edit",
            "method": "POST",
            "action": f"/api/profile/{profile.user_id}",
            "fields": [
                {
                    "name": "full_name",
                    "type": "text",
                    "label": "Full Name",
                    "value": profile.full_name or "",
                    "placeholder": "Enter your full name",
                    "maxlength": 100,
                    "required": False
                },
                {
                    "name": "bio",
                    "type": "textarea",
                    "label": "Bio",
                    "value": profile.bio or "",
                    "placeholder": "Tell us about yourself",
                    "maxlength": 500,
                    "rows": 4,
                    "required": False
                },
                {
                    "name": "phone",
                    "type": "tel",
                    "label": "Phone Number",
                    "value": profile.phone or "",
                    "placeholder": "+1 (555) 123-4567",
                    "maxlength": 20,
                    "required": False
                },
                {
                    "name": "location",
                    "type": "text",
                    "label": "Location",
                    "value": profile.location or "",
                    "placeholder": "City, Country",
                    "maxlength": 100,
                    "required": False
                },
                {
                    "name": "website",
                    "type": "url",
                    "label": "Website",
                    "value": profile.website or "",
                    "placeholder": "https://example.com",
                    "maxlength": 200,
                    "required": False
                }
            ],
            "submit_button": {
                "text": "Save Changes",
                "style": "primary"
            },
            "cancel_button": {
                "text": "Cancel",
                "url": f"/profile/{profile.user_id}",
                "style": "secondary"
            }
        }
