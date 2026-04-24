"""
Notification Preferences Management Module

This module provides functionality for managing user notification preferences,
including email, SMS, and push notification settings across different event types.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator
import json


class NotificationType(str, Enum):
    """Enumeration of supported notification types."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class EventCategory(str, Enum):
    """Enumeration of event categories that can trigger notifications."""
    SECURITY = "security"
    ACCOUNT = "account"
    MARKETING = "marketing"
    PRODUCT_UPDATES = "product_updates"
    SYSTEM = "system"
    SOCIAL = "social"


class NotificationPreference(BaseModel):
    """Model representing a single notification preference setting."""
    
    user_id: str = Field(..., description="Unique identifier for the user")
    event_category: EventCategory = Field(..., description="Category of events")
    notification_type: NotificationType = Field(..., description="Type of notification")
    enabled: bool = Field(default=True, description="Whether this notification is enabled")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class NotificationPreferencesProfile(BaseModel):
    """Complete notification preferences profile for a user."""
    
    user_id: str
    preferences: List[NotificationPreference] = Field(default_factory=list)
    global_mute: bool = Field(default=False, description="Mute all notifications")
    quiet_hours_enabled: bool = Field(default=False)
    quiet_hours_start: Optional[str] = Field(default=None, pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    quiet_hours_end: Optional[str] = Field(default=None, pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    timezone: str = Field(default="UTC")
    
    @validator('quiet_hours_end')
    def validate_quiet_hours(cls, v, values):
        """Ensure quiet hours are properly configured."""
        if values.get('quiet_hours_enabled'):
            if not values.get('quiet_hours_start') or not v:
                raise ValueError("Quiet hours start and end times must be set when enabled")
        return v


class NotificationPreferencesManager:
    """
    Manager class for handling notification preferences operations.
    
    This class provides methods to create, read, update, and delete
    notification preferences for users.
    """
    
    def __init__(self, storage_backend: Optional['StorageBackend'] = None):
        """
        Initialize the notification preferences manager.
        
        Args:
            storage_backend: Optional storage backend for persistence.
                           Defaults to in-memory storage.
        """
        self.storage = storage_backend or InMemoryStorage()
    
    def get_user_preferences(self, user_id: str) -> NotificationPreferencesProfile:
        """
        Retrieve notification preferences for a user.
        
        Args:
            user_id: The unique identifier for the user
            
        Returns:
            NotificationPreferencesProfile containing all user preferences
            
        Raises:
            ValueError: If user_id is empty or invalid
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id cannot be empty")
        
        profile = self.storage.get_profile(user_id)
        if not profile:
            # Return default profile for new users
            profile = self._create_default_profile(user_id)
        
        return profile
    
    def update_preference(
        self,
        user_id: str,
        event_category: EventCategory,
        notification_type: NotificationType,
        enabled: bool
    ) -> NotificationPreference:
        """
        Update a specific notification preference.
        
        Args:
            user_id: The unique identifier for the user
            event_category: Category of events
            notification_type: Type of notification
            enabled: Whether the notification should be enabled
            
        Returns:
            Updated NotificationPreference object
        """
        profile = self.get_user_preferences(user_id)
        
        # Find existing preference or create new one
        preference = None
        for pref in profile.preferences:
            if (pref.event_category == event_category and 
                pref.notification_type == notification_type):
                preference = pref
                break
        
        if preference:
            preference.enabled = enabled
            preference.updated_at = datetime.utcnow()
        else:
            preference = NotificationPreference(
                user_id=user_id,
                event_category=event_category,
                notification_type=notification_type,
                enabled=enabled
            )
            profile.preferences.append(preference)
        
        self.storage.save_profile(profile)
        return preference
    
    def update_global_settings(
        self,
        user_id: str,
        global_mute: Optional[bool] = None,
        quiet_hours_enabled: Optional[bool] = None,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None,
        timezone: Optional[str] = None
    ) -> NotificationPreferencesProfile:
        """
        Update global notification settings for a user.
        
        Args:
            user_id: The unique identifier for the user
            global_mute: Whether to mute all notifications
            quiet_hours_enabled: Whether quiet hours are enabled
            quiet_hours_start: Start time for quiet hours (HH:MM format)
            quiet_hours_end: End time for quiet hours (HH:MM format)
            timezone: User's timezone
            
        Returns:
            Updated NotificationPreferencesProfile
        """
        profile = self.get_user_preferences(user_id)
        
        if global_mute is not None:
            profile.global_mute = global_mute
        if quiet_hours_enabled is not None:
            profile.quiet_hours_enabled = quiet_hours_enabled
        if quiet_hours_start is not None:
            profile.quiet_hours_start = quiet_hours_start
        if quiet_hours_end is not None:
            profile.quiet_hours_end = quiet_hours_end
        if timezone is not None:
            profile.timezone = timezone
        
        # Validate the updated profile
        profile = NotificationPreferencesProfile(**profile.dict())
        self.storage.save_profile(profile)
        return profile
    
    def bulk_update_preferences(
        self,
        user_id: str,
        preferences: List[Dict]
    ) -> NotificationPreferencesProfile:
        """
        Update multiple notification preferences at once.
        
        Args:
            user_id: The unique identifier for the user
            preferences: List of preference dictionaries with keys:
                        event_category, notification_type, enabled
            
        Returns:
            Updated NotificationPreferencesProfile
        """
        for pref_data in preferences:
            self.update_preference(
                user_id=user_id,
                event_category=EventCategory(pref_data['event_category']),
                notification_type=NotificationType(pref_data['notification_type']),
                enabled=pref_data['enabled']
            )
        
        return self.get_user_preferences(user_id)
    
    def is_notification_allowed(
        self,
        user_id: str,
        event_category: EventCategory,
        notification_type: NotificationType,
        current_time: Optional[datetime] = None
    ) -> bool:
        """
        Check if a notification is allowed based on user preferences.
        
        Args:
            user_id: The unique identifier for the user
            event_category: Category of the event
            notification_type: Type of notification to send
            current_time: Current time (defaults to now)
            
        Returns:
            True if notification is allowed, False otherwise
        """
        profile = self.get_user_preferences(user_id)
        
        # Check global mute
        if profile.global_mute:
            return False
        
        # Check quiet hours
        if profile.quiet_hours_enabled and current_time:
            if self._is_in_quiet_hours(profile, current_time):
                return False
        
        # Check specific preference
        for pref in profile.preferences:
            if (pref.event_category == event_category and 
                pref.notification_type == notification_type):
                return pref.enabled
        
        # Default to enabled if no specific preference exists
        return True
    
    def _create_default_profile(self, user_id: str) -> NotificationPreferencesProfile:
        """Create a default notification preferences profile."""
        preferences = []
        
        # Create default preferences: all enabled except marketing
        for category in EventCategory:
            for notification_type in NotificationType:
                enabled = category != EventCategory.MARKETING
                preferences.append(NotificationPreference(
                    user_id=user_id,
                    event_category=category,
                    notification_type=notification_type,
                    enabled=enabled
                ))
        
        profile = NotificationPreferencesProfile(
            user_id=user_id,
            preferences=preferences
        )
        self.storage.save_profile(profile)
        return profile
    
    def _is_in_quiet_hours(
        self,
        profile: NotificationPreferencesProfile,
        current_time: datetime
    ) -> bool:
        """Check if current time is within quiet hours."""
        if not profile.quiet_hours_start or not profile.quiet_hours_end:
            return False
        
        current_hour_min = current_time.strftime("%H:%M")
        start = profile.quiet_hours_start
        end = profile.quiet_hours_end
        
        # Handle quiet hours spanning midnight
        if start <= end:
            return start <= current_hour_min <= end
        else:
            return current_hour_min >= start or current_hour_min <= end


class StorageBackend:
    """Abstract base class for storage backends."""
    
    def get_profile(self, user_id: str) -> Optional[NotificationPreferencesProfile]:
        """Retrieve a user's notification preferences profile."""
        raise NotImplementedError
    
    def save_profile(self, profile: NotificationPreferencesProfile) -> None:
        """Save a user's notification preferences profile."""
        raise NotImplementedError


class InMemoryStorage(StorageBackend):
    """In-memory storage backend for notification preferences."""
    
    def __init__(self):
        """Initialize in-memory storage."""
        self._storage: Dict[str, NotificationPreferencesProfile] = {}
    
    def get_profile(self, user_id: str) -> Optional[NotificationPreferencesProfile]:
        """Retrieve a user's notification preferences profile."""
        return self._storage.get(user_id)
    
    def save_profile(self, profile: NotificationPreferencesProfile) -> None:
        """Save a user's notification preferences profile."""
        self._storage[profile.user_id] = profile
