"""
Authentication and Notification Management Package

This package provides authentication-related functionality including
notification preferences management.
"""

from .notification_preferences import (
    NotificationPreferencesManager,
    NotificationPreference,
    NotificationPreferencesProfile,
    NotificationType,
    EventCategory,
    StorageBackend,
    InMemoryStorage
)

from .notification_api import router as notification_router

__all__ = [
    'NotificationPreferencesManager',
    'NotificationPreference',
    'NotificationPreferencesProfile',
    'NotificationType',
    'EventCategory',
    'StorageBackend',
    'InMemoryStorage',
    'notification_router'
]
