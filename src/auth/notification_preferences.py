"""Notification preferences management for user accounts."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
import json


class NotificationChannel(Enum):
    """Available notification channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationType(Enum):
    """Types of notifications."""
    SECURITY_ALERT = "security_alert"
    ACCOUNT_UPDATE = "account_update"
    MARKETING = "marketing"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    ACTIVITY_DIGEST = "activity_digest"


@dataclass
class ChannelPreference:
    """Preference settings for a specific notification channel."""
    enabled: bool = True
    verified: bool = False
    destination: Optional[str] = None  # email address, phone number, etc.
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class NotificationPreferences:
    """User notification preferences across channels and types."""
    user_id: str
    channels: Dict[NotificationChannel, ChannelPreference] = field(default_factory=dict)
    type_preferences: Dict[NotificationType, List[NotificationChannel]] = field(default_factory=dict)
    quiet_hours_start: Optional[int] = None  # Hour in 24h format (0-23)
    quiet_hours_end: Optional[int] = None
    timezone: str = "UTC"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Initialize default preferences if not provided."""
        if not self.channels:
            self.channels = {
                NotificationChannel.EMAIL: ChannelPreference(enabled=True),
                NotificationChannel.IN_APP: ChannelPreference(enabled=True),
            }
        if not self.type_preferences:
            self.type_preferences = {
                NotificationType.SECURITY_ALERT: [NotificationChannel.EMAIL, NotificationChannel.IN_APP],
                NotificationType.ACCOUNT_UPDATE: [NotificationChannel.EMAIL],
            }


class NotificationPreferencesManager:
    """Manager for handling notification preferences operations."""

    def __init__(self, storage: Optional[Dict[str, NotificationPreferences]] = None):
        """Initialize the preferences manager.
        
        Args:
            storage: Optional storage backend for preferences. Defaults to in-memory dict.
        """
        self._storage = storage if storage is not None else {}

    def create_preferences(self, user_id: str) -> NotificationPreferences:
        """Create default notification preferences for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            NotificationPreferences object with defaults
            
        Raises:
            ValueError: If preferences already exist for user
        """
        if user_id in self._storage:
            raise ValueError(f"Preferences already exist for user {user_id}")
        
        prefs = NotificationPreferences(user_id=user_id)
        self._storage[user_id] = prefs
        return prefs

    def get_preferences(self, user_id: str) -> Optional[NotificationPreferences]:
        """Retrieve notification preferences for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            NotificationPreferences if found, None otherwise
        """
        return self._storage.get(user_id)

    def update_channel(self, user_id: str, channel: NotificationChannel, 
                      enabled: Optional[bool] = None, 
                      destination: Optional[str] = None) -> NotificationPreferences:
        """Update channel-specific preferences.
        
        Args:
            user_id: Unique identifier for the user
            channel: Channel to update
            enabled: Whether the channel is enabled
            destination: Destination address for the channel
            
        Returns:
            Updated NotificationPreferences
            
        Raises:
            KeyError: If user preferences don't exist
        """
        prefs = self._storage.get(user_id)
        if not prefs:
            raise KeyError(f"No preferences found for user {user_id}")
        
        if channel not in prefs.channels:
            prefs.channels[channel] = ChannelPreference()
        
        if enabled is not None:
            prefs.channels[channel].enabled = enabled
        if destination is not None:
            prefs.channels[channel].destination = destination
        
        prefs.channels[channel].updated_at = datetime.utcnow()
        prefs.updated_at = datetime.utcnow()
        
        return prefs

    def set_type_channels(self, user_id: str, notification_type: NotificationType,
                         channels: List[NotificationChannel]) -> NotificationPreferences:
        """Set which channels receive a specific notification type.
        
        Args:
            user_id: Unique identifier for the user
            notification_type: Type of notification
            channels: List of channels to use for this type
            
        Returns:
            Updated NotificationPreferences
            
        Raises:
            KeyError: If user preferences don't exist
        """
        prefs = self._storage.get(user_id)
        if not prefs:
            raise KeyError(f"No preferences found for user {user_id}")
        
        prefs.type_preferences[notification_type] = channels
        prefs.updated_at = datetime.utcnow()
        
        return prefs
