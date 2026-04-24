"""
Unit tests for notification preferences management module.
"""

import pytest
from datetime import datetime

from src.auth.notification_preferences import (
    NotificationPreferencesManager,
    NotificationPreference,
    NotificationPreferencesProfile,
    NotificationType,
    EventCategory,
    InMemoryStorage
)


class TestNotificationPreference:
    """Test cases for NotificationPreference model."""
    
    def test_create_notification_preference(self):
        """Test creating a notification preference."""
        pref = NotificationPreference(
            user_id="user123",
            event_category=EventCategory.SECURITY,
            notification_type=NotificationType.EMAIL,
            enabled=True
        )
        
        assert pref.user_id == "user123"
        assert pref.event_category == EventCategory.SECURITY
        assert pref.notification_type == NotificationType.EMAIL
        assert pref.enabled is True
        assert isinstance(pref.created_at, datetime)
        assert isinstance(pref.updated_at, datetime)
    
    def test_notification_preference_defaults(self):
        """Test default values for notification preference."""
        pref = NotificationPreference(
            user_id="user123",
            event_category=EventCategory.ACCOUNT,
            notification_type=NotificationType.PUSH
        )
        
        assert pref.enabled is True  # Default should be True


class TestNotificationPreferencesProfile:
    """Test cases for NotificationPreferencesProfile model."""
    
    def test_create_profile(self):
        """Test creating a notification preferences profile."""
        profile = NotificationPreferencesProfile(
            user_id="user123",
            preferences=[],
            global_mute=False
        )
        
        assert profile.user_id == "user123"
        assert profile.preferences == []
        assert profile.global_mute is False
        assert profile.timezone == "UTC"
    
    def test_profile_with_quiet_hours(self):
        """Test profile with quiet hours enabled."""
        profile = NotificationPreferencesProfile(
            user_id="user123",
            quiet_hours_enabled=True,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00"
        )
        
        assert profile.quiet_hours_enabled is True
        assert profile.quiet_hours_start == "22:00"
        assert profile.quiet_hours_end == "08:00"
    
    def test_profile_quiet_hours_validation_error(self):
        """Test that quiet hours validation fails when times are missing."""
        with pytest.raises(ValueError):
            NotificationPreferencesProfile(
                user_id="user123",
                quiet_hours_enabled=True,
                quiet_hours_start="22:00"
                # Missing quiet_hours_end
            )
    
    def test_profile_invalid_time_format(self):
        """Test that invalid time format raises validation error."""
        with pytest.raises(ValueError):
            NotificationPreferencesProfile(
                user_id="user123",
                quiet_hours_enabled=True,
                quiet_hours_start="25:00",  # Invalid hour
                quiet_hours_end="08:00"
            )


class TestNotificationPreferencesManager:
    """Test cases for NotificationPreferencesManager."""
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = NotificationPreferencesManager()
        assert manager.storage is not None
        assert isinstance(manager.storage, InMemoryStorage)
    
    def test_get_user_preferences_creates_default(self):
        """Test getting preferences for new user creates default profile."""
        manager = NotificationPreferencesManager()
        profile = manager.get_user_preferences("user123")
        
        assert profile.user_id == "user123"
        assert len(profile.preferences) > 0
        assert profile.global_mute is False
    
    def test_get_user_preferences_invalid_user_id(self):
        """Test that empty user_id raises ValueError."""
        manager = NotificationPreferencesManager()
        
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            manager.get_user_preferences("")
    
    def test_update_preference(self):
        """Test updating a single preference."""
        manager = NotificationPreferencesManager()
        
        pref = manager.update_preference(
            user_id="user123",
            event_category=EventCategory.SECURITY,
            notification_type=NotificationType.EMAIL,
            enabled=False
        )
        
        assert pref.user_id == "user123"
        assert pref.event_category == EventCategory.SECURITY
        assert pref.notification_type == NotificationType.EMAIL
        assert pref.enabled is False
    
    def test_update_existing_preference(self):
        """Test updating an existing preference modifies it."""
        manager = NotificationPreferencesManager()
        
        # First update
        pref1 = manager.update_preference(
            user_id="user123",
            event_category=EventCategory.SECURITY,
            notification_type=NotificationType.EMAIL,
            enabled=True
        )
        created_at_1 = pref1.created_at
        
        # Second update should modify existing
        pref2 = manager.update_preference(
            user_id="user123",
            event_category=EventCategory.SECURITY,
            notification_type=NotificationType.EMAIL,
            enabled=False
        )
        
        assert pref2.enabled is False
        assert pref2.updated_at > pref1.updated_at
        
        # Verify only one preference exists
        profile = manager.get_user_preferences("user123")
        security_email_prefs = [
            p for p in profile.preferences
            if p.event_category == EventCategory.SECURITY
            and p.notification_type == NotificationType.EMAIL
        ]
        assert len(security_email_prefs) == 1
    
    def test_update_global_settings(self):
        """Test updating global settings."""
        manager = NotificationPreferencesManager()
        
        profile = manager.update_global_settings(
            user_id="user123",
            global_mute=True,
            timezone="America/New_York"
        )
        
        assert profile.global_mute is True
        assert profile.timezone == "America/New_York"
    
    def test_update_global_settings_quiet_hours(self):
        """Test updating quiet hours settings."""
        manager = NotificationPreferencesManager()
        
        profile = manager.update_global_settings(
            user_id="user123",
            quiet_hours_enabled=True,
            quiet_hours_start="22:00",
            quiet_hours_end="07:00"
        )
        
        assert profile.quiet_hours_enabled is True
        assert profile.quiet_hours_start == "22:00"
        assert profile.quiet_hours_end == "07:00"
    
    def test_bulk_update_preferences(self):
        """Test bulk updating multiple preferences."""
        manager = NotificationPreferencesManager()
        
        preferences = [
            {
                'event_category': EventCategory.SECURITY.value,
                'notification_type': NotificationType.EMAIL.value,
                'enabled': False
            },
            {
                'event_category': EventCategory.MARKETING.value,
                'notification_type': NotificationType.SMS.value,
                'enabled': True
            }
        ]
        
        profile = manager.bulk_update_preferences("user123", preferences)
        
        # Verify updates were applied
        security_email = next(
            (p for p in profile.preferences
             if p.event_category == EventCategory.SECURITY
             and p.notification_type == NotificationType.EMAIL),
            None
        )
        assert security_email is not None
        assert security_email.enabled is False
        
        marketing_sms = next(
            (p for p in profile.preferences
             if p.event_category == EventCategory.MARKETING
             and p.notification_type == NotificationType.SMS),
            None
        )
        assert marketing_sms is not None
        assert marketing_sms.enabled is True
    
    def test_is_notification_allowed_global_mute(self):
        """Test that global mute blocks all notifications."""
        manager = NotificationPreferencesManager()
        
        manager.update_global_settings(user_id="user123", global_mute=True)
        
        allowed = manager.is_notification_allowed(
            user_id="user123",
            event_category=EventCategory.SECURITY,
            notification_type=NotificationType.EMAIL
        )
        
        assert allowed is False
    
    def test_is_notification_allowed_specific_preference(self):
        """Test notification allowed based on specific preference."""
        manager = NotificationPreferencesManager()
        
        manager.update_preference(
            user_id="user123",
            event_category=EventCategory.SECURITY,
            notification_type=NotificationType.EMAIL,
            enabled=False
        )
        
        allowed = manager.is_notification_allowed(
            user_id="user123",
            event_category=EventCategory.SECURITY,
            notification_type=NotificationType.EMAIL
        )
        
        assert allowed is False
    
    def test_is_notification_allowed_quiet_hours(self):
        """Test that quiet hours block notifications."""
        manager = NotificationPreferencesManager()
        
        manager.update_global_settings(
            user_id="user123",
            quiet_hours_enabled=True,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00"
        )
        
        # Test during quiet hours (23:30)
        test_time = datetime.strptime("23:30", "%H:%M")
        allowed = manager.is_notification_allowed(
            user_id="user123",
            event_category=EventCategory.SECURITY,
            notification_type=NotificationType.EMAIL,
            current_time=test_time
        )
        
        assert allowed is False
    
    def test_is_notification_allowed_outside_quiet_hours(self):
        """Test that notifications are allowed outside quiet hours."""
        manager = NotificationPreferencesManager()
        
        manager.update_global_settings(
            user_id="user123",
            quiet_hours_enabled=True,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00"
        )
        
        # Test outside quiet hours (10:00)
        test_time = datetime.strptime("10:00", "%H:%M")
        allowed = manager.is_notification_allowed(
            user_id="user123",
            event_category=EventCategory.SECURITY,
            notification_type=NotificationType.EMAIL,
            current_time=test_time
        )
        
        assert allowed is True
    
    def test_is_notification_allowed_default_enabled(self):
        """Test that notifications are allowed by default."""
        manager = NotificationPreferencesManager()
        
        # Get preferences to initialize default profile
        manager.get_user_preferences("user123")
        
        allowed = manager.is_notification_allowed(
            user_id="user123",
            event_category=EventCategory.SECURITY,
            notification_type=NotificationType.EMAIL
        )
        
        assert allowed is True
    
    def test_default_profile_marketing_disabled(self):
        """Test that marketing notifications are disabled by default."""
        manager = NotificationPreferencesManager()
        profile = manager.get_user_preferences("user123")
        
        # Check that marketing preferences exist and are disabled
        marketing_prefs = [
            p for p in profile.preferences
            if p.event_category == EventCategory.MARKETING
        ]
        
        assert len(marketing_prefs) > 0
        for pref in marketing_prefs:
            assert pref.enabled is False
    
    def test_quiet_hours_spanning_midnight(self):
        """Test quiet hours that span midnight."""
        manager = NotificationPreferencesManager()
        
        manager.update_global_settings(
            user_id="user123",
            quiet_hours_enabled=True,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00"
        )
        
        profile = manager.get_user_preferences("user123")
        
        # Test time after start (23:00)
        time1 = datetime.strptime("23:00", "%H:%M")
        assert manager._is_in_quiet_hours(profile, time1) is True
        
        # Test time before end (07:00)
        time2 = datetime.strptime("07:00", "%H:%M")
        assert manager._is_in_quiet_hours(profile, time2) is True
        
        # Test time outside range (15:00)
        time3 = datetime.strptime("15:00", "%H:%M")
        assert manager._is_in_quiet_hours(profile, time3) is False


class TestInMemoryStorage:
    """Test cases for InMemoryStorage backend."""
    
    def test_storage_initialization(self):
        """Test storage initialization."""
        storage = InMemoryStorage()
        assert storage._storage == {}
    
    def test_save_and_get_profile(self):
        """Test saving and retrieving a profile."""
        storage = InMemoryStorage()
        
        profile = NotificationPreferencesProfile(
            user_id="user123",
            global_mute=True
        )
        
        storage.save_profile(profile)
        retrieved = storage.get_profile("user123")
        
        assert retrieved is not None
        assert retrieved.user_id == "user123"
        assert retrieved.global_mute is True
    
    def test_get_nonexistent_profile(self):
        """Test getting a profile that doesn't exist."""
        storage = InMemoryStorage()
        profile = storage.get_profile("nonexistent")
        
        assert profile is None
    
    def test_overwrite_existing_profile(self):
        """Test that saving overwrites existing profile."""
        storage = InMemoryStorage()
        
        profile1 = NotificationPreferencesProfile(
            user_id="user123",
            global_mute=False
        )
        storage.save_profile(profile1)
        
        profile2 = NotificationPreferencesProfile(
            user_id="user123",
            global_mute=True
        )
        storage.save_profile(profile2)
        
        retrieved = storage.get_profile("user123")
        assert retrieved.global_mute is True
