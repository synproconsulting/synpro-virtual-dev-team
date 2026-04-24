"""
Profile management API endpoints.

This module provides FastAPI endpoints for user profile operations including
retrieval, updates, password changes, and profile deactivation.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import jwt
from datetime import datetime

from .profile import (
    ProfileService,
    ProfileResponse,
    ProfileUpdate,
    PasswordChangeRequest,
)


# Security scheme
security = HTTPBearer()

# Router for profile endpoints
router = APIRouter(
    prefix="/api/v1/profile",
    tags=["profile"],
)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract and validate user ID from JWT token.
    
    Args:
        credentials: HTTP Authorization credentials containing JWT token
        
    Returns:
        User ID extracted from token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        token = credentials.credentials
        secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        user_id: Optional[str] = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        
        return user_id
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


def get_profile_service() -> ProfileService:
    """
    Dependency to get ProfileService instance.
    
    Returns:
        ProfileService instance
    """
    # In production, this would return a service with actual database connection
    # For now, returning a placeholder that will need database integration
    return ProfileService(database_connection=None)


@router.get(
    "/me",
    response_model=ProfileResponse,
    summary="Get current user profile",
    description="Retrieve the profile information for the currently authenticated user",
)
async def get_my_profile(
    user_id: str = Depends(get_current_user_id),
    profile_service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    """
    Get current user's profile.
    
    Args:
        user_id: Current user's ID from JWT token
        profile_service: ProfileService instance
        
    Returns:
        User profile data
        
    Raises:
        HTTPException: If profile not found
    """
    try:
        profile = await profile_service.get_profile(user_id)
        
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )
        
        return profile
    
    except NotImplementedError:
        # Temporary response for demonstration
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Database integration required",
        )


@router.put(
    "/me",
    response_model=ProfileResponse,
    summary="Update current user profile",
    description="Update profile information for the currently authenticated user",
)
async def update_my_profile(
    profile_data: ProfileUpdate,
    user_id: str = Depends(get_current_user_id),
    profile_service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    """
    Update current user's profile.
    
    Args:
        profile_data: Profile update data
        user_id: Current user's ID from JWT token
        profile_service: ProfileService instance
        
    Returns:
        Updated user profile data
        
    Raises:
        HTTPException: If profile not found or update fails
    """
    try:
        updated_profile = await profile_service.update_profile(user_id, profile_data)
        return updated_profile
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Database integration required",
        )


@router.post(
    "/me/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change user password",
    description="Change password for the currently authenticated user",
)
async def change_password(
    password_change: PasswordChangeRequest,
    user_id: str = Depends(get_current_user_id),
    profile_service: ProfileService = Depends(get_profile_service),
) -> dict:
    """
    Change current user's password.
    
    Args:
        password_change: Password change request data
        user_id: Current user's ID from JWT token
        profile_service: ProfileService instance
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If password change fails
    """
    try:
        success = await profile_service.change_password(user_id, password_change)
        
        if success:
            return {
                "message": "Password changed successfully",
                "changed_at": datetime.utcnow().isoformat(),
            }
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to change password",
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Database integration required",
        )


@router.delete(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Deactivate user profile",
    description="Deactivate (soft delete) the currently authenticated user's profile",
)
async def deactivate_my_profile(
    user_id: str = Depends(get_current_user_id),
    profile_service: ProfileService = Depends(get_profile_service),
) -> dict:
    """
    Deactivate current user's profile.
    
    Args:
        user_id: Current user's ID from JWT token
        profile_service: ProfileService instance
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If deactivation fails
    """
    try:
        success = await profile_service.deactivate_profile(user_id)
        
        if success:
            return {
                "message": "Profile deactivated successfully",
                "deactivated_at": datetime.utcnow().isoformat(),
            }
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to deactivate profile",
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Database integration required",
        )


@router.get(
    "/{user_id}",
    response_model=ProfileResponse,
    summary="Get user profile by ID",
    description="Retrieve profile information for a specific user (admin or self only)",
)
async def get_user_profile(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    profile_service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    """
    Get user profile by ID.
    
    Args:
        user_id: Target user's ID
        current_user_id: Current user's ID from JWT token
        profile_service: ProfileService instance
        
    Returns:
        User profile data
        
    Raises:
        HTTPException: If not authorized or profile not found
    """
    # Only allow users to view their own profile (in production, add admin check)
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this profile",
        )
    
    try:
        profile = await profile_service.get_profile(user_id)
        
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )
        
        return profile
    
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Database integration required",
        )
