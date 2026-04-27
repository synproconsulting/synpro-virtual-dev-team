"""Tests for notification preferences management."""

import pytest
from src.auth.notification_preferences import (
    NotificationPreferencesManager,
    NotificationChannel,
    NotificationCategory,
    ChannelPreference,
    CategoryPreferences,
)


class TestNotificationPreferencesManager:
    """Test cases for NotificationPreferencesManager."""

    def test_initialization(self):
        """Test manager initialization with defaults."""
        manager = NotificationPreferencesManager(user_id="user123")
        assert manager.user_id == "user123"
        assert len(manager._preferences) == len(NotificationCategory)

    def test_set_category_channel_enabled(self):
        """Test enabling a channel for a specific category."""
        manager = NotificationPreferencesManager(user_id="user123")
        manager.set_category_channel(
            NotificationCategory.SECURITY,
            NotificationChannel.EMAIL,
            True
        )
        assert manager.is_notification_enabled(
            NotificationCategory.SECURITY,
            NotificationChannel.EMAIL
        )

    def test_set_category_channel_disabled(self):
        """Test disabling a channel for a specific category."""
        manager = NotificationPreferencesManager(user_id="user123")
        manager.set_category_channel(
            NotificationCategory.MARKETING,
            NotificationChannel.SMS,
            False
        )
        assert not manager.is_notification_enabled(
            NotificationCategory.MARKETING,
            NotificationChannel.SMS
        )

    def test_global_channel_override(self):
        """Test that global channel settings override category settings."""
        manager = NotificationPreferencesManager(user_id="user123")
        manager.set_category_channel(
            NotificationCategory.ALERTS,
            NotificationChannel.PUSH,
            True
        )
        manager.set_global_channel(NotificationChannel.PUSH, False)
        
        assert not manager.is_notification_enabled(
            NotificationCategory.ALERTS,
            NotificationChannel.PUSH
        )

    def test_set_quiet_hours(self):
        """Test setting quiet hours for a category."""
        manager = NotificationPreferencesManager(user_id="user123")
        manager.set_quiet_hours(
            NotificationCategory.SOCIAL,
            enabled=True,
            start_time="22:00",
            end_time="08:00"
        )
        
        prefs = manager.get_preferences(NotificationCategory.SOCIAL)
        assert prefs is not None
        assert prefs.quiet_hours_enabled is True
        assert prefs.quiet_hours_start == "22:00"
        assert prefs.quiet_hours_end == "08:00"

    def test_get_preferences(self):
        """Test retrieving preferences for a category."""
        manager = NotificationPreferencesManager(user_id="user123")
        prefs = manager.get_preferences(NotificationCategory.ACCOUNT)
        assert isinstance(prefs, CategoryPreferences)
        assert prefs.category == NotificationCategory.ACCOUNT

    def test_get_all_preferences(self):
        """Test retrieving all preferences."""
        manager = NotificationPreferencesManager(user_id="user123")
        all_prefs = manager.get_all_preferences()
        assert len(all_prefs) == len(NotificationCategory)
        assert NotificationCategory.SECURITY in all_prefs

    def test_multiple_channels_per_category(self):
        """Test setting multiple channels for one category."""
        manager = NotificationPreferencesManager(user_id="user123")
        manager.set_category_channel(
            NotificationCategory.UPDATES,
            NotificationChannel.EMAIL,
            True
        )
        manager.set_category_channel(
            NotificationCategory.UPDATES,
            NotificationChannel.PUSH,
            True
        )
        manager.set_category_channel(
            NotificationCategory.UPDATES,
            NotificationChannel.SMS,
            False
        )
        
        assert manager.is_notification_enabled(
            NotificationCategory.UPDATES,
            NotificationChannel.EMAIL
        )
        assert manager.is_notification_enabled(
            NotificationCategory.UPDATES,
            NotificationChannel.PUSH
        )
        assert not manager.is_notification_enabled(
            NotificationCategory.UPDATES,
            NotificationChannel.SMS
        )

    def test_channel_preference_metadata(self):
        """Test channel preference metadata storage."""
        manager = NotificationPreferencesManager(user_id="user123")
        manager.set_category_channel(
            NotificationCategory.SECURITY,
            NotificationChannel.WEBHOOK,
            True
        )
        
        prefs = manager.get_preferences(NotificationCategory.SECURITY)
        assert prefs is not None
        prefs.channels[NotificationChannel.WEBHOOK].metadata["url"] = "https://example.com/hook"
        
        assert prefs.channels[NotificationChannel.WEBHOOK].metadata["url"] == "https://example.com/hook"
