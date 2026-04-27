"""Tests for notification preferences management."""

import pytest
from datetime import datetime
from src.auth.notification_preferences import (
    NotificationChannel,
    NotificationType,
    ChannelPreference,
    NotificationPreferences,
    NotificationPreferencesManager,
)


class TestChannelPreference:
    """Test ChannelPreference dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        pref = ChannelPreference()
        assert pref.enabled is True
        assert pref.verified is False
        assert pref.destination is None
        assert isinstance(pref.updated_at, datetime)

    def test_custom_values(self):
        """Test custom values can be set."""
        pref = ChannelPreference(
            enabled=False,
            verified=True,
            destination="user@example.com"
        )
        assert pref.enabled is False
        assert pref.verified is True
        assert pref.destination == "user@example.com"


class TestNotificationPreferences:
    """Test NotificationPreferences dataclass."""

    def test_initialization_with_defaults(self):
        """Test default initialization."""
        prefs = NotificationPreferences(user_id="user123")
        assert prefs.user_id == "user123"
        assert NotificationChannel.EMAIL in prefs.channels
        assert NotificationChannel.IN_APP in prefs.channels
        assert NotificationType.SECURITY_ALERT in prefs.type_preferences
        assert prefs.timezone == "UTC"

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        custom_channels = {
            NotificationChannel.SMS: ChannelPreference(enabled=True, destination="+1234567890")
        }
        prefs = NotificationPreferences(
            user_id="user456",
            channels=custom_channels,
            quiet_hours_start=22,
            quiet_hours_end=7
        )
        assert prefs.user_id == "user456"
        assert NotificationChannel.SMS in prefs.channels
        assert prefs.quiet_hours_start == 22
        assert prefs.quiet_hours_end == 7


class TestNotificationPreferencesManager:
    """Test NotificationPreferencesManager class."""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager instance."""
        return NotificationPreferencesManager()

    def test_create_preferences(self, manager):
        """Test creating new preferences."""
        prefs = manager.create_preferences("user123")
        assert prefs.user_id == "user123"
        assert isinstance(prefs, NotificationPreferences)

    def test_create_duplicate_preferences_raises_error(self, manager):
        """Test that creating duplicate preferences raises ValueError."""
        manager.create_preferences("user123")
        with pytest.raises(ValueError, match="already exist"):
            manager.create_preferences("user123")

    def test_get_preferences(self, manager):
        """Test retrieving preferences."""
        manager.create_preferences("user123")
        prefs = manager.get_preferences("user123")
        assert prefs is not None
        assert prefs.user_id == "user123"

    def test_get_nonexistent_preferences(self, manager):
        """Test retrieving non-existent preferences returns None."""
        prefs = manager.get_preferences("nonexistent")
        assert prefs is None

    def test_update_channel_enabled(self, manager):
        """Test updating channel enabled status."""
        manager.create_preferences("user123")
        prefs = manager.update_channel("user123", NotificationChannel.EMAIL, enabled=False)
        assert prefs.channels[NotificationChannel.EMAIL].enabled is False

    def test_update_channel_destination(self, manager):
        """Test updating channel destination."""
        manager.create_preferences("user123")
        prefs = manager.update_channel(
            "user123",
            NotificationChannel.SMS,
            destination="+1234567890"
        )
        assert prefs.channels[NotificationChannel.SMS].destination == "+1234567890"

    def test_update_channel_nonexistent_user_raises_error(self, manager):
        """Test updating channel for non-existent user raises KeyError."""
        with pytest.raises(KeyError):
            manager.update_channel("nonexistent", NotificationChannel.EMAIL, enabled=False)

    def test_set_type_channels(self, manager):
        """Test setting channels for notification type."""
        manager.create_preferences("user123")
        channels = [NotificationChannel.EMAIL, NotificationChannel.PUSH]
        prefs = manager.set_type_channels(
            "user123",
            NotificationType.MARKETING,
            channels
        )
        assert prefs.type_preferences[NotificationType.MARKETING] == channels

    def test_set_type_channels_nonexistent_user_raises_error(self, manager):
        """Test setting type channels for non-existent user raises KeyError."""
        with pytest.raises(KeyError):
            manager.set_type_channels(
                "nonexistent",
                NotificationType.MARKETING,
                [NotificationChannel.EMAIL]
            )

    def test_updated_at_changes_on_update(self, manager):
        """Test that updated_at timestamp changes on updates."""
        prefs = manager.create_preferences("user123")
        original_time = prefs.updated_at
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        updated_prefs = manager.update_channel("user123", NotificationChannel.EMAIL, enabled=False)
        assert updated_prefs.updated_at > original_time
