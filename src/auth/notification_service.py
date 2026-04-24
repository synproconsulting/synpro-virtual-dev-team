"""Service layer for managing notification preferences."""

from typing import Dict, Optional, Protocol
from datetime import datetime

from .notification_preferences import (
    NotificationPreferences,
    NotificationCategory,
    NotificationChannel,
    ChannelPreference
)


class PreferenceStore(Protocol):
    """Protocol for notification preference storage backend."""

    def get(self, user_id: str) -> Optional[NotificationPreferences]:
        """Retrieve preferences for a user."""
        ...

    def save(self, preferences: NotificationPreferences) -> None:
        """Save user preferences."""
        ...

    def delete(self, user_id: str) -> bool:
        """Delete user preferences."""
        ...


class InMemoryPreferenceStore:
    """In-memory implementation of preference storage."""

    def __init__(self) -> None:
        self._store: Dict[str, NotificationPreferences] = {}

    def get(self, user_id: str) -> Optional[NotificationPreferences]:
        """Retrieve preferences for a user."""
        return self._store.get(user_id)

    def save(self, preferences: NotificationPreferences) -> None:
        """Save user preferences."""
        self._store[preferences.user_id] = preferences

    def delete(self, user_id: str) -> bool:
        """Delete user preferences."""
        if user_id in self._store:
            del self._store[user_id]
            return True
        return False


class NotificationPreferenceService:
    """Service for managing user notification preferences."""

    def __init__(self, store: PreferenceStore) -> None:
        """Initialize service with a preference store.
        
        Args:
            store: Storage backend for preferences
        """
        self._store = store

    def get_preferences(self, user_id: str) -> NotificationPreferences:
        """Get notification preferences for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            User's notification preferences
        """
        preferences = self._store.get(user_id)
        if preferences is None:
            preferences = NotificationPreferences(user_id=user_id)
            self._store.save(preferences)
        return preferences

    def update_channel_preference(
        self,
        user_id: str,
        category: NotificationCategory,
        channel: NotificationChannel,
        enabled: bool
    ) -> NotificationPreferences:
        """Update a specific channel preference.
        
        Args:
            user_id: User identifier
            category: Notification category
            channel: Notification channel
            enabled: Whether to enable notifications
            
        Returns:
            Updated preferences
        """
        preferences = self.get_preferences(user_id)
        preferences.set_channel_preference(category, channel, enabled)
        self._store.save(preferences)
        return preferences

    def set_global_mute(self, user_id: str, muted: bool) -> NotificationPreferences:
        """Set global mute status for all notifications.
        
        Args:
            user_id: User identifier
            muted: Whether to mute all notifications
            
        Returns:
            Updated preferences
        """
        preferences = self.get_preferences(user_id)
        preferences.global_mute = muted
        preferences.updated_at = datetime.utcnow()
        self._store.save(preferences)
        return preferences

    def set_quiet_hours(
        self,
        user_id: str,
        start_hour: int,
        end_hour: int,
        timezone: str = "UTC"
    ) -> NotificationPreferences:
        """Configure quiet hours for a user.
        
        Args:
            user_id: User identifier
            start_hour: Start hour (0-23)
            end_hour: End hour (0-23)
            timezone: User's timezone
            
        Returns:
            Updated preferences
        """
        preferences = self.get_preferences(user_id)
        preferences.set_quiet_hours(start_hour, end_hour)
        preferences.timezone = timezone
        self._store.save(preferences)
        return preferences

    def verify_channel(
        self,
        user_id: str,
        category: NotificationCategory,
        channel: NotificationChannel,
        address: str
    ) -> NotificationPreferences:
        """Mark a notification channel as verified.
        
        Args:
            user_id: User identifier
            category: Notification category
            channel: Notification channel
            address: Contact address (email, phone, etc.)
            
        Returns:
            Updated preferences
        """
        preferences = self.get_preferences(user_id)
        pref = preferences.get_channel_preference(category, channel)
        pref.verified = True
        pref.address = address
        pref.verified_at = datetime.utcnow()
        preferences.updated_at = datetime.utcnow()
        self._store.save(preferences)
        return preferences
