"""
Profile page routes and API endpoints.

This module defines the FastAPI routes for profile page operations
including viewing, editing, and updating user profiles.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from datetime import datetime

from .profile import ProfileService, ProfileData, ProfileUpdateRequest, ProfileUIRenderer


router = APIRouter(prefix="/api/profile", tags=["profile"])


async def get_profile_service() -> ProfileService:
    """
    Dependency injection for ProfileService.
    
    Returns:
        ProfileService instance
    """
    # In production, this would inject the actual database connection
    return ProfileService()


async def get_current_user_id() -> str:
    """
    Get current authenticated user ID from session/token.
    
    Returns:
        User ID string
        
    Raises:
        HTTPException: If user is not authenticated
    """
    # In production, this would extract user ID from JWT token or session
    # For now, this is a placeholder
    user_id = None  # Would come from token validation
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return user_id


@router.get("/{user_id}", response_model=dict)
async def get_profile_page(
    user_id: str,
    profile_service: ProfileService = Depends(get_profile_service)
) -> dict:
    """
    Get user profile page data and layout.
    
    Args:
        user_id: User identifier
        profile_service: Profile service instance
        
    Returns:
        Profile page layout and data
        
    Raises:
        HTTPException: If profile not found
    """
    profile = await profile_service.get_profile(user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    layout = ProfileUIRenderer.render_profile_layout(profile)
    
    return {
        "success": True,
        "profile": profile.dict(),
        "ui": layout
    }


@router.get("/{user_id}/edit", response_model=dict)
async def get_profile_edit_form(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    profile_service: ProfileService = Depends(get_profile_service)
) -> dict:
    """
    Get profile edit form structure.
    
    Args:
        user_id: User identifier
        current_user_id: Current authenticated user ID
        profile_service: Profile service instance
        
    Returns:
        Profile edit form structure
        
    Raises:
        HTTPException: If unauthorized or profile not found
    """
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot edit another user's profile"
        )
    
    profile = await profile_service.get_profile(user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    form = ProfileUIRenderer.render_edit_form(profile)
    
    return {
        "success": True,
        "profile": profile.dict(),
        "form": form
    }


@router.put("/{user_id}", response_model=dict)
async def update_profile(
    user_id: str,
    update_data: ProfileUpdateRequest,
    current_user_id: str = Depends(get_current_user_id),
    profile_service: ProfileService = Depends(get_profile_service)
) -> dict:
    """
    Update user profile information.
    
    Args:
        user_id: User identifier
        update_data: Profile update data
        current_user_id: Current authenticated user ID
        profile_service: Profile service instance
        
    Returns:
        Updated profile data
        
    Raises:
        HTTPException: If unauthorized or update fails
    """
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update another user's profile"
        )
    
    updated_profile = await profile_service.update_profile(user_id, update_data)
    
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update profile"
        )
    
    return {
        "success": True,
        "message": "Profile updated successfully",
        "profile": updated_profile.dict()
    }


@router.delete("/{user_id}", response_model=dict)
async def delete_profile(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    profile_service: ProfileService = Depends(get_profile_service)
) -> dict:
    """
    Delete (deactivate) user profile.
    
    Args:
        user_id: User identifier
        current_user_id: Current authenticated user ID
        profile_service: Profile service instance
        
    Returns:
        Deletion confirmation
        
    Raises:
        HTTPException: If unauthorized or deletion fails
    """
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete another user's profile"
        )
    
    success = await profile_service.delete_profile(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete profile"
        )
    
    return {
        "success": True,
        "message": "Profile deleted successfully"
    }


@router.get("/{user_id}/preview", response_model=dict)
async def preview_profile_changes(
    user_id: str,
    full_name: Optional[str] = None,
    bio: Optional[str] = None,
    phone: Optional[str] = None,
    location: Optional[str] = None,
    website: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id),
    profile_service: ProfileService = Depends(get_profile_service)
) -> dict:
    """
    Preview profile changes without saving.
    
    Args:
        user_id: User identifier
        full_name: Updated full name
        bio: Updated bio
        phone: Updated phone
        location: Updated location
        website: Updated website
        current_user_id: Current authenticated user ID
        profile_service: Profile service instance
        
    Returns:
        Preview of profile with proposed changes
        
    Raises:
        HTTPException: If unauthorized or profile not found
    """
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot preview another user's profile"
        )
    
    profile = await profile_service.get_profile(user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # Create preview data by merging current profile with proposed changes
    preview_data = profile.dict()
    if full_name is not None:
        preview_data['full_name'] = full_name
    if bio is not None:
        preview_data['bio'] = bio
    if phone is not None:
        preview_data['phone'] = phone
    if location is not None:
        preview_data['location'] = location
    if website is not None:
        preview_data['website'] = website
    
    preview_profile = ProfileData(**preview_data)
    layout = ProfileUIRenderer.render_profile_layout(preview_profile)
    
    return {
        "success": True,
        "preview": True,
        "profile": preview_profile.dict(),
        "ui": layout
    }
