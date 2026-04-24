"""Tests for notification preferences management."""

import pytest
from datetime import datetime

from src.auth.notification_preferences import (
    NotificationPreferences,
    NotificationCategory,
    NotificationChannel,
    ChannelPreference
)


class TestChannelPreference:
    """Tests for ChannelPreference dataclass."""

    def test_default_values(self):
        """Test default channel preference values."""
        pref = ChannelPreference()
        assert pref.enabled is True
        assert pref.verified is False
        assert pref.address is None
        assert pref.verified_at is None

    def test_to_dict(self):
        """Test conversion to dictionary."""
        verified_at = datetime(2024, 1, 1, 12, 0, 0)
        pref = ChannelPreference(
            enabled=True,
            verified=True,
            address="test@example.com",
            verified_at=verified_at
        )
        result = pref.to_dict()
        assert result["enabled"] is True
        assert result["verified"] is True
        assert result["address"] == "test@example.com"
        assert result["verified_at"] == verified_at.isoformat()


class TestNotificationPreferences:
    """Tests for NotificationPreferences."""

    def test_initialization_with_defaults(self):
        """Test preferences are initialized with defaults."""
        prefs = NotificationPreferences(user_id="user123")
        assert prefs.user_id == "user123"
        assert prefs.global_mute is False
        assert len(prefs.preferences) > 0
        
        # Security notifications should be enabled by default
        security_email = prefs.get_channel_preference(
            NotificationCategory.SECURITY,
            NotificationChannel.EMAIL
        )
        assert security_email.enabled is True

    def test_set_channel_preference(self):
        """Test setting a channel preference."""
        prefs = NotificationPreferences(user_id="user123")
        prefs.set_channel_preference(
            NotificationCategory.MARKETING,
            NotificationChannel.EMAIL,
            enabled=True
        )
        
        pref = prefs.get_channel_preference(
            NotificationCategory.MARKETING,
            NotificationChannel.EMAIL
        )
        assert pref.enabled is True
        assert prefs.updated_at is not None

    def test_get_nonexistent_preference(self):
        """Test getting a preference that doesn't exist."""
        prefs = NotificationPreferences(user_id="user123", preferences={})
        pref = prefs.get_channel_preference(
            NotificationCategory.BILLING,
            NotificationChannel.SMS
        )
        assert pref.enabled is False

    def test_set_quiet_hours(self):
        """Test setting quiet hours."""
        prefs = NotificationPreferences(user_id="user123")
        prefs.set_quiet_hours(22, 8)
        assert prefs.quiet_hours_start == 22
        assert prefs.quiet_hours_end == 8
        assert prefs.updated_at is not None

    def test_set_quiet_hours_invalid(self):
        """Test setting invalid quiet hours raises error."""
        prefs = NotificationPreferences(user_id="user123")
        with pytest.raises(ValueError, match="Hours must be between 0 and 23"):
            prefs.set_quiet_hours(25, 8)

    def test_is_in_quiet_hours_simple_range(self):
        """Test quiet hours check with simple range."""
        prefs = NotificationPreferences(user_id="user123")
        prefs.set_quiet_hours(22, 8)
        
        assert prefs._is_in_quiet_hours(23) is True
        assert prefs._is_in_quiet_hours(7) is True
        assert prefs._is_in_quiet_hours(10) is False

    def test_is_in_quiet_hours_no_overlap(self):
        """Test quiet hours check without day overlap."""
        prefs = NotificationPreferences(user_id="user123")
        prefs.set_quiet_hours(9, 17)
        
        assert prefs._is_in_quiet_hours(12) is True
        assert prefs._is_in_quiet_hours(8) is False
        assert prefs._is_in_quiet_hours(18) is False

    def test_should_send_notification_global_mute(self):
        """Test notifications blocked when globally muted."""
        prefs = NotificationPreferences(user_id="user123")
        prefs.global_mute = True
        
        result = prefs.should_send_notification(
            NotificationCategory.SECURITY,
            NotificationChannel.EMAIL
        )
        assert result is False

    def test_should_send_notification_quiet_hours(self):
        """Test notifications during quiet hours."""
        prefs = NotificationPreferences(user_id="user123")
        prefs.set_quiet_hours(22, 8)
        prefs.set_channel_preference(
            NotificationCategory.MARKETING,
            NotificationChannel.EMAIL,
            enabled=True
        )
        pref = prefs.get_channel_preference(
            NotificationCategory.MARKETING,
            NotificationChannel.EMAIL
        )
        pref.verified = True
        
        # Marketing blocked during quiet hours
        result = prefs.should_send_notification(
            NotificationCategory.MARKETING,
            NotificationChannel.EMAIL,
            current_hour=23
        )
        assert result is False
        
        # Security bypasses quiet hours
        security_pref = prefs.get_channel_preference(
            NotificationCategory.SECURITY,
            NotificationChannel.EMAIL
        )
        security_pref.verified = True
        result = prefs.should_send_notification(
            NotificationCategory.SECURITY,
            NotificationChannel.EMAIL,
            current_hour=23
        )
        assert result is True

    def test_to_dict(self):
        """Test conversion to dictionary."""
        prefs = NotificationPreferences(user_id="user123")
        result = prefs.to_dict()
        
        assert result["user_id"] == "user123"
        assert result["global_mute"] is False
        assert "preferences" in result
        assert result["timezone"] == "UTC"
