"""Profile page UI/UX models and services.

This module provides data models and services for rendering user profile pages
with a clean, intuitive UI/UX design.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class ProfileTheme(str, Enum):
    """Available theme options for profile customization."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class ProfileVisibility(str, Enum):
    """Profile visibility settings."""
    PUBLIC = "public"
    PRIVATE = "private"
    CONNECTIONS_ONLY = "connections_only"


@dataclass
class ProfileSection:
    """Represents a customizable section in the user profile."""
    section_id: str
    title: str
    content: str
    is_visible: bool = True
    order: int = 0
    icon: Optional[str] = None


@dataclass
class ProfileSettings:
    """User profile display and privacy settings."""
    theme: ProfileTheme = ProfileTheme.AUTO
    visibility: ProfileVisibility = ProfileVisibility.PUBLIC
    show_email: bool = False
    show_last_login: bool = True
    show_join_date: bool = True
    show_activity: bool = True
    enable_notifications: bool = True


@dataclass
class ProfileData:
    """Complete user profile data structure for UI rendering."""
    user_id: str
    username: str
    email: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    joined_date: Optional[datetime] = None
    last_login: Optional[datetime] = None
    settings: ProfileSettings = field(default_factory=ProfileSettings)
    sections: list[ProfileSection] = field(default_factory=list)
    social_links: dict[str, str] = field(default_factory=dict)
    stats: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert profile data to dictionary for API responses."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email if self.settings.show_email else None,
            "display_name": self.display_name or self.username,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "cover_image_url": self.cover_image_url,
            "location": self.location,
            "website": self.website,
            "joined_date": self.joined_date.isoformat() if self.joined_date and self.settings.show_join_date else None,
            "last_login": self.last_login.isoformat() if self.last_login and self.settings.show_last_login else None,
            "settings": {
                "theme": self.settings.theme.value,
                "visibility": self.settings.visibility.value,
            },
            "sections": [
                {
                    "id": section.section_id,
                    "title": section.title,
                    "content": section.content,
                    "icon": section.icon,
                    "order": section.order,
                }
                for section in sorted(self.sections, key=lambda s: s.order)
                if section.is_visible
            ],
            "social_links": self.social_links,
            "stats": self.stats if self.settings.show_activity else {},
        }


class ProfileService:
    """Service for managing user profile data and operations."""

    def __init__(self):
        """Initialize the profile service."""
        self._profiles: dict[str, ProfileData] = {}

    def create_profile(
        self,
        user_id: str,
        username: str,
        email: str,
        **kwargs,
    ) -> ProfileData:
        """Create a new user profile.

        Args:
            user_id: Unique user identifier
            username: User's username
            email: User's email address
            **kwargs: Additional profile fields

        Returns:
            ProfileData: The created profile
        """
        profile = ProfileData(
            user_id=user_id,
            username=username,
            email=email,
            joined_date=datetime.utcnow(),
            **kwargs,
        )
        self._profiles[user_id] = profile
        return profile

    def get_profile(self, user_id: str) -> Optional[ProfileData]:
        """Retrieve a user profile by ID.

        Args:
            user_id: User identifier

        Returns:
            ProfileData if found, None otherwise
        """
        return self._profiles.get(user_id)

    def update_profile(
        self,
        user_id: str,
        **updates,
    ) -> Optional[ProfileData]:
        """Update profile fields.

        Args:
            user_id: User identifier
            **updates: Fields to update

        Returns:
            Updated ProfileData if found, None otherwise
        """
        profile = self._profiles.get(user_id)
        if not profile:
            return None

        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        return profile

    def update_settings(
        self,
        user_id: str,
        **settings,
    ) -> Optional[ProfileSettings]:
        """Update profile settings.

        Args:
            user_id: User identifier
            **settings: Settings to update

        Returns:
            Updated ProfileSettings if found, None otherwise
        """
        profile = self._profiles.get(user_id)
        if not profile:
            return None

        for key, value in settings.items():
            if hasattr(profile.settings, key):
                setattr(profile.settings, key, value)

        return profile.settings

    def add_section(
        self,
        user_id: str,
        section: ProfileSection,
    ) -> bool:
        """Add a custom section to the profile.

        Args:
            user_id: User identifier
            section: Section to add

        Returns:
            True if added, False if profile not found
        """
        profile = self._profiles.get(user_id)
        if not profile:
            return False

        profile.sections.append(section)
        return True

    def remove_section(
        self,
        user_id: str,
        section_id: str,
    ) -> bool:
        """Remove a section from the profile.

        Args:
            user_id: User identifier
            section_id: Section identifier to remove

        Returns:
            True if removed, False if not found
        """
        profile = self._profiles.get(user_id)
        if not profile:
            return False

        profile.sections = [
            s for s in profile.sections if s.section_id != section_id
        ]
        return True

    def update_stats(
        self,
        user_id: str,
        stats: dict[str, int],
    ) -> bool:
        """Update profile statistics.

        Args:
            user_id: User identifier
            stats: Statistics to update/add

        Returns:
            True if updated, False if profile not found
        """
        profile = self._profiles.get(user_id)
        if not profile:
            return False

        profile.stats.update(stats)
        return True
