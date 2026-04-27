"""Notification preferences management interface."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime


class NotificationChannel(Enum):
    """Supported notification channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NotificationCategory(Enum):
    """Notification categories for preference management."""
    SECURITY = "security"
    ACCOUNT = "account"
    MARKETING = "marketing"
    UPDATES = "updates"
    ALERTS = "alerts"
    SOCIAL = "social"


@dataclass
class ChannelPreference:
    """Preference settings for a specific notification channel."""
    enabled: bool = True
    verified: bool = False
    verified_at: Optional[datetime] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class CategoryPreferences:
    """Notification preferences for a specific category."""
    category: NotificationCategory
    channels: Dict[NotificationChannel, ChannelPreference] = field(default_factory=dict)
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None

    def is_channel_enabled(self, channel: NotificationChannel) -> bool:
        """Check if a specific channel is enabled for this category."""
        if channel not in self.channels:
            return False
        return self.channels[channel].enabled


class NotificationPreferencesManager:
    """Manager for user notification preferences."""

    def __init__(self, user_id: str) -> None:
        """Initialize preferences manager for a user.
        
        Args:
            user_id: Unique identifier for the user
        """
        self.user_id = user_id
        self._preferences: Dict[NotificationCategory, CategoryPreferences] = {}
        self._global_channels: Dict[NotificationChannel, ChannelPreference] = {}
        self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        """Initialize default preferences for all categories."""
        for category in NotificationCategory:
            self._preferences[category] = CategoryPreferences(category=category)

    def set_category_channel(
        self,
        category: NotificationCategory,
        channel: NotificationChannel,
        enabled: bool
    ) -> None:
        """Set channel preference for a specific category.
        
        Args:
            category: The notification category
            channel: The notification channel
            enabled: Whether the channel is enabled
        """
        if category not in self._preferences:
            self._preferences[category] = CategoryPreferences(category=category)
        
        if channel not in self._preferences[category].channels:
            self._preferences[category].channels[channel] = ChannelPreference()
        
        self._preferences[category].channels[channel].enabled = enabled

    def set_global_channel(self, channel: NotificationChannel, enabled: bool) -> None:
        """Set global channel preference across all categories.
        
        Args:
            channel: The notification channel
            enabled: Whether the channel is globally enabled
        """
        if channel not in self._global_channels:
            self._global_channels[channel] = ChannelPreference()
        self._global_channels[channel].enabled = enabled

    def is_notification_enabled(
        self,
        category: NotificationCategory,
        channel: NotificationChannel
    ) -> bool:
        """Check if notifications are enabled for category and channel.
        
        Args:
            category: The notification category
            channel: The notification channel
            
        Returns:
            True if notifications are enabled, False otherwise
        """
        # Check global channel preference first
        if channel in self._global_channels and not self._global_channels[channel].enabled:
            return False
        
        # Check category-specific preference
        if category not in self._preferences:
            return False
        
        return self._preferences[category].is_channel_enabled(channel)

    def set_quiet_hours(
        self,
        category: NotificationCategory,
        enabled: bool,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> None:
        """Configure quiet hours for a category.
        
        Args:
            category: The notification category
            enabled: Whether quiet hours are enabled
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
        """
        if category not in self._preferences:
            self._preferences[category] = CategoryPreferences(category=category)
        
        prefs = self._preferences[category]
        prefs.quiet_hours_enabled = enabled
        prefs.quiet_hours_start = start_time
        prefs.quiet_hours_end = end_time

    def get_preferences(self, category: NotificationCategory) -> Optional[CategoryPreferences]:
        """Get preferences for a specific category.
        
        Args:
            category: The notification category
            
        Returns:
            CategoryPreferences object or None if not found
        """
        return self._preferences.get(category)

    def get_all_preferences(self) -> Dict[NotificationCategory, CategoryPreferences]:
        """Get all notification preferences.
        
        Returns:
            Dictionary mapping categories to their preferences
        """
        return self._preferences.copy()
