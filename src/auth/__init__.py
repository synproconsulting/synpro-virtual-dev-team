"""Authentication module for email notifications."""

from .email_notifications import EmailNotificationService

__all__ = ["EmailNotificationService"]
from src.auth.notification_preferences import NotificationPreferences
from src.auth.notification_preferences import NotificationPreferenceService
from src.auth.notification_preferences import NotificationCategory
from src.auth.notification_preferences import NotificationChannel
from src.auth.notification_preferences import ChannelPreference
from src.auth.notification_preferences import InMemoryPreferenceStore
from src.auth.notification_preferences import PreferenceStore
