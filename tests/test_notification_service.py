"""Tests for notification preference service."""

import pytest

from src.auth.notification_service import (
    NotificationPreferenceService,
    InMemoryPreferenceStore
)
from src.auth.notification_preferences import (
    NotificationCategory,
    NotificationChannel
)


class TestInMemoryPreferenceStore:
    """Tests for in-memory preference store."""

    def test_get_nonexistent_user(self):
        """Test retrieving preferences for non-existent user."""
        store = InMemoryPreferenceStore()
        result = store.get("user123")
        assert result is None

    def test_save_and_get(self):
        """Test saving and retrieving preferences."""
        from src.auth.notification_preferences import NotificationPreferences
        
        store = InMemoryPreferenceStore()
        prefs = NotificationPreferences(user_id="user123")
        store.save(prefs)
        
        retrieved = store.get("user123")
        assert retrieved is not None
        assert retrieved.user_id == "user123"

    def test_delete_existing_user(self):
        """Test deleting existing user preferences."""
        from src.auth.notification_preferences import NotificationPreferences
        
        store = InMemoryPreferenceStore()
        prefs = NotificationPreferences(user_id="user123")
        store.save(prefs)
        
        result = store.delete("user123")
        assert result is True
        assert store.get("user123") is None

    def test_delete_nonexistent_user(self):
        """Test deleting non-existent user returns False."""
        store = InMemoryPreferenceStore()
        result = store.delete("user123")
        assert result is False


class TestNotificationPreferenceService:
    """Tests for notification preference service."""

    def test_get_preferences_creates_defaults(self):
        """Test getting preferences creates defaults for new users."""
        store = InMemoryPreferenceStore()
        service = NotificationPreferenceService(store)
        
        prefs = service.get_preferences("user123")
        assert prefs.user_id == "user123"
        assert len(prefs.preferences) > 0

    def test_get_preferences_returns_existing(self):
        """Test getting preferences returns existing data."""
        from src.auth.notification_preferences import NotificationPreferences
        
        store = InMemoryPreferenceStore()
        service = NotificationPreferenceService(store)
        
        # Create and save preferences
        original = NotificationPreferences(user_id="user123")
        original.global_mute = True
        store.save(original)
        
        # Retrieve and verify
        prefs = service.get_preferences("user123")
        assert prefs.global_mute is True

    def test_update_channel_preference(self):
        """Test updating a channel preference."""
        store = InMemoryPreferenceStore()
        service = NotificationPreferenceService(store)
        
        prefs = service.update_channel_preference(
            "user123",
            NotificationCategory.MARKETING,
            NotificationChannel.EMAIL,
            enabled=True
        )
        
        assert prefs.user_id == "user123"
        pref = prefs.get_channel_preference(
            NotificationCategory.MARKETING,
            NotificationChannel.EMAIL
        )
        assert pref.enabled is True

    def test_set_global_mute(self):
        """Test setting global mute."""
        store = InMemoryPreferenceStore()
        service = NotificationPreferenceService(store)
        
        prefs = service.set_global_mute("user123", muted=True)
        assert prefs.global_mute is True
        assert prefs.updated_at is not None

    def test_set_quiet_hours(self):
        """Test setting quiet hours."""
        store = InMemoryPreferenceStore()
        service = NotificationPreferenceService(store)
        
        prefs = service.set_quiet_hours(
            "user123",
            start_hour=22,
            end_hour=8,
            timezone="America/New_York"
        )
        
        assert prefs.quiet_hours_start == 22
        assert prefs.quiet_hours_end == 8
        assert prefs.timezone == "America/New_York"

    def test_verify_channel(self):
        """Test verifying a notification channel."""
        store = InMemoryPreferenceStore()
        service = NotificationPreferenceService(store)
        
        prefs = service.verify_channel(
            "user123",
            NotificationCategory.SECURITY,
            NotificationChannel.EMAIL,
            "user@example.com"
        )
        
        pref = prefs.get_channel_preference(
            NotificationCategory.SECURITY,
            NotificationChannel.EMAIL
        )
        assert pref.verified is True
        assert pref.address == "user@example.com"
        assert pref.verified_at is not None
