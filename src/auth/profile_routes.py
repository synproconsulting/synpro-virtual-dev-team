"""
FastAPI routes for profile page endpoints.

This module defines the REST API endpoints for profile operations
including viewing, updating, and avatar management.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.auth.profile import (
    ProfileService,
    ProfileUIRenderer,
    UserProfile,
    ProfileUpdateRequest
)


router = APIRouter(prefix="/api/profile", tags=["profile"])


def get_profile_service() -> ProfileService:
    """
    Dependency injection for ProfileService.
    
    Returns:
        ProfileService instance
    """
    return ProfileService()


def get_current_user_id() -> str:
    """
    Get current authenticated user ID from token.
    
    This is a placeholder - actual implementation would decode JWT token.
    
    Returns:
        User ID string
        
    Raises:
        HTTPException: If user is not authenticated
    """
    # TODO: Implement actual JWT token validation
    # For now, this is a placeholder
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated"
    )


@router.get("/{user_id}", response_model=dict)
async def get_profile(
    user_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """
    Get user profile by user ID.
    
    Args:
        user_id: User identifier
        service: ProfileService instance (injected)
        
    Returns:
        Formatted profile data for UI display
        
    Raises:
        HTTPException: If profile not found
    """
    profile = await service.get_profile(user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile not found for user {user_id}"
        )
    
    return ProfileUIRenderer.format_profile_for_display(profile)


@router.get("/me", response_model=dict)
async def get_my_profile(
    current_user_id: str = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service)
):
    """
    Get current authenticated user's profile.
    
    Args:
        current_user_id: Current user ID (injected from auth)
        service: ProfileService instance (injected)
        
    Returns:
        Formatted profile data for UI display
        
    Raises:
        HTTPException: If profile not found
    """
    profile = await service.get_profile(current_user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return ProfileUIRenderer.format_profile_for_display(profile)


@router.put("/me", response_model=dict)
async def update_my_profile(
    update_data: ProfileUpdateRequest,
    current_user_id: str = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service)
):
    """
    Update current user's profile.
    
    Args:
        update_data: Profile fields to update
        current_user_id: Current user ID (injected from auth)
        service: ProfileService instance (injected)
        
    Returns:
        Updated profile data
        
    Raises:
        HTTPException: If update fails or validation errors
    """
    try:
        updated_profile = await service.update_profile(current_user_id, update_data)
        return ProfileUIRenderer.format_profile_for_display(updated_profile)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/me/avatar", response_model=dict)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service)
):
    """
    Upload user avatar image.
    
    Args:
        file: Uploaded image file
        current_user_id: Current user ID (injected from auth)
        service: ProfileService instance (injected)
        
    Returns:
        New avatar URL
        
    Raises:
        HTTPException: If file type is invalid or upload fails
    """
    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content type is required"
        )
    
    try:
        file_data = await file.read()
        avatar_url = await service.upload_avatar(
            current_user_id,
            file_data,
            file.content_type
        )
        
        return {
            "message": "Avatar uploaded successfully",
            "avatarUrl": avatar_url
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/me/avatar", status_code=status.HTTP_204_NO_CONTENT)
async def delete_avatar(
    current_user_id: str = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service)
):
    """
    Delete user avatar and reset to default.
    
    Args:
        current_user_id: Current user ID (injected from auth)
        service: ProfileService instance (injected)
    """
    await service.delete_avatar(current_user_id)


@router.get("/ui/layout", response_model=dict)
async def get_profile_layout():
    """
    Get profile page UI layout configuration.
    
    Returns:
        UI section configuration for rendering the profile page
    """
    return ProfileUIRenderer.get_profile_sections()
