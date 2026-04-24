"""
Notification Preferences API Module

This module provides RESTful API endpoints for managing notification preferences.
Designed to work with FastAPI or similar frameworks.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from .notification_preferences import (
    NotificationPreferencesManager,
    NotificationType,
    EventCategory,
    NotificationPreferencesProfile,
    NotificationPreference
)


# Request/Response Models
class UpdatePreferenceRequest(BaseModel):
    """Request model for updating a single notification preference."""
    event_category: EventCategory
    notification_type: NotificationType
    enabled: bool


class BulkUpdateRequest(BaseModel):
    """Request model for bulk updating notification preferences."""
    preferences: List[UpdatePreferenceRequest]


class GlobalSettingsUpdateRequest(BaseModel):
    """Request model for updating global notification settings."""
    global_mute: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    quiet_hours_end: Optional[str] = Field(None, pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    timezone: Optional[str] = None


class NotificationCheckRequest(BaseModel):
    """Request model for checking if a notification is allowed."""
    event_category: EventCategory
    notification_type: NotificationType


class NotificationCheckResponse(BaseModel):
    """Response model for notification check."""
    allowed: bool
    user_id: str
    event_category: EventCategory
    notification_type: NotificationType


class APIResponse(BaseModel):
    """Generic API response wrapper."""
    success: bool
    message: str
    data: Optional[Dict] = None


# Router setup
router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["notification-preferences"]
)


# Dependency for getting the notification manager
def get_notification_manager() -> NotificationPreferencesManager:
    """
    Dependency injection for notification preferences manager.
    
    In production, this should be configured to use a persistent storage backend.
    """
    return NotificationPreferencesManager()


# Dependency for getting current user (placeholder)
def get_current_user() -> str:
    """
    Get the current authenticated user ID.
    
    This is a placeholder. In production, this should integrate with
    your authentication system to extract the user ID from JWT token
    or session.
    """
    # TODO: Implement actual authentication
    return "current_user_id"


@router.get("/preferences", response_model=NotificationPreferencesProfile)
async def get_user_preferences(
    user_id: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    manager: NotificationPreferencesManager = Depends(get_notification_manager)
) -> NotificationPreferencesProfile:
    """
    Get notification preferences for a user.
    
    Args:
        user_id: Optional user ID (admins only). If not provided, returns current user's preferences.
        current_user: Current authenticated user ID
        manager: Notification preferences manager instance
        
    Returns:
        NotificationPreferencesProfile containing all preferences
    """
    # Use current user if no user_id provided
    target_user_id = user_id or current_user
    
    # TODO: Add authorization check - only allow users to access their own preferences
    # unless they have admin role
    
    try:
        return manager.get_user_preferences(target_user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/preferences/single", response_model=NotificationPreference)
async def update_single_preference(
    request: UpdatePreferenceRequest,
    user_id: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    manager: NotificationPreferencesManager = Depends(get_notification_manager)
) -> NotificationPreference:
    """
    Update a single notification preference.
    
    Args:
        request: Update preference request data
        user_id: Optional user ID (admins only)
        current_user: Current authenticated user ID
        manager: Notification preferences manager instance
        
    Returns:
        Updated NotificationPreference
    """
    target_user_id = user_id or current_user
    
    try:
        return manager.update_preference(
            user_id=target_user_id,
            event_category=request.event_category,
            notification_type=request.notification_type,
            enabled=request.enabled
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/preferences/bulk", response_model=NotificationPreferencesProfile)
async def bulk_update_preferences(
    request: BulkUpdateRequest,
    user_id: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    manager: NotificationPreferencesManager = Depends(get_notification_manager)
) -> NotificationPreferencesProfile:
    """
    Update multiple notification preferences at once.
    
    Args:
        request: Bulk update request with list of preferences
        user_id: Optional user ID (admins only)
        current_user: Current authenticated user ID
        manager: Notification preferences manager instance
        
    Returns:
        Updated NotificationPreferencesProfile
    """
    target_user_id = user_id or current_user
    
    preferences_data = [
        {
            'event_category': pref.event_category,
            'notification_type': pref.notification_type,
            'enabled': pref.enabled
        }
        for pref in request.preferences
    ]
    
    try:
        return manager.bulk_update_preferences(target_user_id, preferences_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/preferences/global", response_model=NotificationPreferencesProfile)
async def update_global_settings(
    request: GlobalSettingsUpdateRequest,
    user_id: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    manager: NotificationPreferencesManager = Depends(get_notification_manager)
) -> NotificationPreferencesProfile:
    """
    Update global notification settings (mute, quiet hours, etc.).
    
    Args:
        request: Global settings update request
        user_id: Optional user ID (admins only)
        current_user: Current authenticated user ID
        manager: Notification preferences manager instance
        
    Returns:
        Updated NotificationPreferencesProfile
    """
    target_user_id = user_id or current_user
    
    try:
        return manager.update_global_settings(
            user_id=target_user_id,
            global_mute=request.global_mute,
            quiet_hours_enabled=request.quiet_hours_enabled,
            quiet_hours_start=request.quiet_hours_start,
            quiet_hours_end=request.quiet_hours_end,
            timezone=request.timezone
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/check", response_model=NotificationCheckResponse)
async def check_notification_allowed(
    request: NotificationCheckRequest,
    user_id: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    manager: NotificationPreferencesManager = Depends(get_notification_manager)
) -> NotificationCheckResponse:
    """
    Check if a notification is allowed for a user.
    
    This endpoint can be used by notification services to verify
    if a notification should be sent based on user preferences.
    
    Args:
        request: Notification check request
        user_id: Optional user ID (for service accounts)
        current_user: Current authenticated user ID
        manager: Notification preferences manager instance
        
    Returns:
        NotificationCheckResponse indicating if notification is allowed
    """
    target_user_id = user_id or current_user
    
    try:
        allowed = manager.is_notification_allowed(
            user_id=target_user_id,
            event_category=request.event_category,
            notification_type=request.notification_type
        )
        
        return NotificationCheckResponse(
            allowed=allowed,
            user_id=target_user_id,
            event_category=request.event_category,
            notification_type=request.notification_type
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/categories", response_model=List[str])
async def get_event_categories() -> List[str]:
    """
    Get list of all available event categories.
    
    Returns:
        List of event category values
    """
    return [category.value for category in EventCategory]


@router.get("/types", response_model=List[str])
async def get_notification_types() -> List[str]:
    """
    Get list of all available notification types.
    
    Returns:
        List of notification type values
    """
    return [notification_type.value for notification_type in NotificationType]
