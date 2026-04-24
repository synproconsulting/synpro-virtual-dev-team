"""Profile management module for user profile data and avatar handling."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import hashlib


@dataclass
class UserProfile:
    """User profile data structure."""
    
    user_id: str
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class ProfileManager:
    """Manages user profiles with in-memory storage.
    
    Provides functionality to retrieve and update user profile information
    including display names and avatar URLs.
    """
    
    def __init__(self) -> None:
        """Initialize ProfileManager with empty in-memory storage."""
        self._profiles: dict[str, UserProfile] = {}
    
    def create_profile(
        self,
        user_id: str,
        email: str,
        display_name: Optional[str] = None
    ) -> UserProfile:
        """Create a new user profile.
        
        Args:
            user_id: Unique identifier for the user
            email: User's email address
            display_name: Optional display name (defaults to email if not provided)
        
        Returns:
            UserProfile: The created profile
        
        Raises:
            ValueError: If profile already exists for user_id
        """
        if user_id in self._profiles:
            raise ValueError(f"Profile already exists for user_id: {user_id}")
        
        profile = UserProfile(
            user_id=user_id,
            email=email,
            display_name=display_name or email,
            avatar_url=self._generate_gravatar_url(email)
        )
        self._profiles[user_id] = profile
        return profile
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Retrieve a user profile by user ID.
        
        Args:
            user_id: The unique identifier for the user
        
        Returns:
            UserProfile if found, None otherwise
        """
        return self._profiles.get(user_id)
    
    def update_display_name(self, user_id: str, display_name: str) -> UserProfile:
        """Update the display name for a user profile.
        
        Args:
            user_id: The unique identifier for the user
            display_name: New display name to set
        
        Returns:
            UserProfile: The updated profile
        
        Raises:
            ValueError: If profile not found or display_name is empty
        """
        if not display_name or not display_name.strip():
            raise ValueError("Display name cannot be empty")
        
        profile = self._profiles.get(user_id)
        if profile is None:
            raise ValueError(f"Profile not found for user_id: {user_id}")
        
        profile.display_name = display_name.strip()
        profile.updated_at = datetime.utcnow()
        return profile
    
    def get_avatar_url(self, user_id: str) -> Optional[str]:
        """Get the avatar URL for a user.
        
        Args:
            user_id: The unique identifier for the user
        
        Returns:
            Avatar URL if profile exists, None otherwise
        """
        profile = self._profiles.get(user_id)
        return profile.avatar_url if profile else None
    
    def update_avatar_url(self, user_id: str, avatar_url: str) -> UserProfile:
        """Update the avatar URL for a user profile.
        
        Args:
            user_id: The unique identifier for the user
            avatar_url: New avatar URL to set
        
        Returns:
            UserProfile: The updated profile
        
        Raises:
            ValueError: If profile not found
        """
        profile = self._profiles.get(user_id)
        if profile is None:
            raise ValueError(f"Profile not found for user_id: {user_id}")
        
        profile.avatar_url = avatar_url
        profile.updated_at = datetime.utcnow()
        return profile
    
    def _generate_gravatar_url(self, email: str, size: int = 200) -> str:
        """Generate a Gravatar URL based on email address.
        
        Args:
            email: User's email address
            size: Avatar size in pixels (default: 200)
        
        Returns:
            Gravatar URL string
        """
        email_hash = hashlib.md5(email.lower().strip().encode('utf-8')).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon"
    
    def delete_profile(self, user_id: str) -> bool:
        """Delete a user profile.
        
        Args:
            user_id: The unique identifier for the user
        
        Returns:
            True if profile was deleted, False if not found
        """
        if user_id in self._profiles:
            del self._profiles[user_id]
            return True
        return False
    
    def list_profiles(self) -> list[UserProfile]:
        """List all user profiles.
        
        Returns:
            List of all UserProfile objects
        """
        return list(self._profiles.values())
