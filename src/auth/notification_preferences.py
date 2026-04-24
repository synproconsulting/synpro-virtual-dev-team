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


class NotificationCategory(Enum):
    """Categories of notifications."""
    SECURITY = "security"
    PRODUCT_UPDATES = "product_updates"
    MARKETING = "marketing"
    BILLING = "billing"
    SYSTEM = "system"


@dataclass
class ChannelPreference:
    """Preference settings for a specific notification channel."""
    enabled: bool = True
    verified: bool = False
    address: Optional[str] = None
    verified_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "enabled": self.enabled,
            "verified": self.verified,
            "address": self.address,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None
        }


@dataclass
class NotificationPreferences:
    """User notification preferences across channels and categories."""
    user_id: str
    preferences: Dict[NotificationCategory, Dict[NotificationChannel, ChannelPreference]] = field(default_factory=dict)
    global_mute: bool = False
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None
    timezone: str = "UTC"
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Initialize default preferences if not provided."""
        if not self.preferences:
            self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        """Set default preferences for all categories and channels."""
        for category in NotificationCategory:
            self.preferences[category] = {}
            for channel in NotificationChannel:
                # Security notifications enabled by default
                enabled = category == NotificationCategory.SECURITY
                self.preferences[category][channel] = ChannelPreference(enabled=enabled)

    def set_channel_preference(
        self,
        category: NotificationCategory,
        channel: NotificationChannel,
        enabled: bool
    ) -> None:
        """Set notification preference for a specific category and channel."""
        if category not in self.preferences:
            self.preferences[category] = {}
        
        if channel not in self.preferences[category]:
            self.preferences[category][channel] = ChannelPreference()
        
        self.preferences[category][channel].enabled = enabled
        self.updated_at = datetime.utcnow()

    def get_channel_preference(
        self,
        category: NotificationCategory,
        channel: NotificationChannel
    ) -> ChannelPreference:
        """Get notification preference for a specific category and channel."""
        if category not in self.preferences or channel not in self.preferences[category]:
            return ChannelPreference(enabled=False)
        return self.preferences[category][channel]

    def set_quiet_hours(self, start_hour: int, end_hour: int) -> None:
        """Set quiet hours (0-23) when notifications are suppressed."""
        if not (0 <= start_hour <= 23 and 0 <= end_hour <= 23):
            raise ValueError("Hours must be between 0 and 23")
        self.quiet_hours_start = start_hour
        self.quiet_hours_end = end_hour
        self.updated_at = datetime.utcnow()

    def should_send_notification(
        self,
        category: NotificationCategory,
        channel: NotificationChannel,
        current_hour: Optional[int] = None
    ) -> bool:
        """Determine if a notification should be sent based on preferences."""
        if self.global_mute:
            return False

        if current_hour is not None and self.quiet_hours_start is not None:
            if self._is_in_quiet_hours(current_hour):
                # Security notifications bypass quiet hours
                if category != NotificationCategory.SECURITY:
                    return False

        pref = self.get_channel_preference(category, channel)
        return pref.enabled and pref.verified

    def _is_in_quiet_hours(self, current_hour: int) -> bool:
        """Check if current hour falls within quiet hours."""
        if self.quiet_hours_start is None or self.quiet_hours_end is None:
            return False
        
        start = self.quiet_hours_start
        end = self.quiet_hours_end
        
        if start <= end:
            return start <= current_hour < end
        else:
            return current_hour >= start or current_hour < end

    def to_dict(self) -> Dict:
        """Convert preferences to dictionary representation."""
        return {
            "user_id": self.user_id,
            "preferences": {
                cat.value: {ch.value: pref.to_dict() for ch, pref in channels.items()}
                for cat, channels in self.preferences.items()
            },
            "global_mute": self.global_mute,
            "quiet_hours_start": self.quiet_hours_start,
            "quiet_hours_end": self.quiet_hours_end,
            "timezone": self.timezone,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
