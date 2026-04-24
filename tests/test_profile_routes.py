"""
Unit tests for profile routes.

Tests for profile API endpoints and route handlers.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from src.auth.profile import ProfileData, ProfileUpdateRequest, ProfileService
from src.auth.profile_routes import (
    get_profile_page,
    get_profile_edit_form,
    update_profile,
    delete_profile,
    preview_profile_changes
)


class TestGetProfilePage:
    """Tests for get_profile_page endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_profile_page_success(self):
        """Test successful profile page retrieval."""
        mock_service = Mock(spec=ProfileService)
        mock_profile = ProfileData(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            full_name="John Doe",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_service.get_profile = AsyncMock(return_value=mock_profile)
        
        result = await get_profile_page("user123", mock_service)
        
        assert result["success"] is True
        assert result["profile"]["user_id"] == "user123"
        assert result["profile"]["username"] == "johndoe"
        assert "ui" in result
        assert result["ui"]["layout"] == "profile-page"
    
    @pytest.mark.asyncio
    async def test_get_profile_page_not_found(self):
        """Test profile page retrieval when profile doesn't exist."""
        mock_service = Mock(spec=ProfileService)
        mock_service.get_profile = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_profile_page("user123", mock_service)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Profile not found"


class TestGetProfileEditForm:
    """Tests for get_profile_edit_form endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_edit_form_success(self):
        """Test successful edit form retrieval."""
        mock_service = Mock(spec=ProfileService)
        mock_profile = ProfileData(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_service.get_profile = AsyncMock(return_value=mock_profile)
        
        result = await get_profile_edit_form("user123", "user123", mock_service)
        
        assert result["success"] is True
        assert result["profile"]["user_id"] == "user123"
        assert "form" in result
        assert result["form"]["form"] == "profile-edit"
    
    @pytest.mark.asyncio
    async def test_get_edit_form_unauthorized(self):
        """Test edit form retrieval for different user."""
        mock_service = Mock(spec=ProfileService)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_profile_edit_form("user123", "user456", mock_service)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Cannot edit another user's profile"
    
    @pytest.mark.asyncio
    async def test_get_edit_form_not_found(self):
        """Test edit form retrieval when profile doesn't exist."""
        mock_service = Mock(spec=ProfileService)
        mock_service.get_profile = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_profile_edit_form("user123", "user123", mock_service)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Profile not found"


class TestUpdateProfile:
    """Tests for update_profile endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_profile_success(self):
        """Test successful profile update."""
        mock_service = Mock(spec=ProfileService)
        updated_profile = ProfileData(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            full_name="John Updated",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_service.update_profile = AsyncMock(return_value=updated_profile)
        
        update_data = ProfileUpdateRequest(full_name="John Updated")
        result = await update_profile("user123", update_data, "user123", mock_service)
        
        assert result["success"] is True
        assert result["message"] == "Profile updated successfully"
        assert result["profile"]["full_name"] == "John Updated"
    
    @pytest.mark.asyncio
    async def test_update_profile_unauthorized(self):
        """Test profile update for different user."""
        mock_service = Mock(spec=ProfileService)
        update_data = ProfileUpdateRequest(full_name="John Updated")
        
        with pytest.raises(HTTPException) as exc_info:
            await update_profile("user123", update_data, "user456", mock_service)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Cannot update another user's profile"
    
    @pytest.mark.asyncio
    async def test_update_profile_failed(self):
        """Test profile update failure."""
        mock_service = Mock(spec=ProfileService)
        mock_service.update_profile = AsyncMock(return_value=None)
        
        update_data = ProfileUpdateRequest(full_name="John Updated")
        
        with pytest.raises(HTTPException) as exc_info:
            await update_profile("user123", update_data, "user123", mock_service)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Failed to update profile"
    
    @pytest.mark.asyncio
    async def test_update_profile_multiple_fields(self):
        """Test updating multiple profile fields."""
        mock_service = Mock(spec=ProfileService)
        updated_profile = ProfileData(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            full_name="John Updated",
            bio="New bio",
            location="San Francisco, USA",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_service.update_profile = AsyncMock(return_value=updated_profile)
        
        update_data = ProfileUpdateRequest(
            full_name="John Updated",
            bio="New bio",
            location="San Francisco, USA"
        )
        result = await update_profile("user123", update_data, "user123", mock_service)
        
        assert result["success"] is True
        assert result["profile"]["full_name"] == "John Updated"
        assert result["profile"]["bio"] == "New bio"
        assert result["profile"]["location"] == "San Francisco, USA"


class TestDeleteProfile:
    """Tests for delete_profile endpoint."""
    
    @pytest.mark.asyncio
    async def test_delete_profile_success(self):
        """Test successful profile deletion."""
        mock_service = Mock(spec=ProfileService)
        mock_service.delete_profile = AsyncMock(return_value=True)
        
        result = await delete_profile("user123", "user123", mock_service)
        
        assert result["success"] is True
        assert result["message"] == "Profile deleted successfully"
    
    @pytest.mark.asyncio
    async def test_delete_profile_unauthorized(self):
        """Test profile deletion for different user."""
        mock_service = Mock(spec=ProfileService)
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_profile("user123", "user456", mock_service)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Cannot delete another user's profile"
    
    @pytest.mark.asyncio
    async def test_delete_profile_failed(self):
        """Test profile deletion failure."""
        mock_service = Mock(spec=ProfileService)
        mock_service.delete_profile = AsyncMock(return_value=False)
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_profile("user123", "user123", mock_service)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Failed to delete profile"


class TestPreviewProfileChanges:
    """Tests for preview_profile_changes endpoint."""
    
    @pytest.mark.asyncio
    async def test_preview_changes_success(self):
        """Test successful preview of profile changes."""
        mock_service = Mock(spec=ProfileService)
        current_profile = ProfileData(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            full_name="John Doe",
            bio="Original bio",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_service.get_profile = AsyncMock(return_value=current_profile)
        
        result = await preview_profile_changes(
            user_id="user123",
            full_name="John Updated",
            bio="New bio",
            current_user_id="user123",
            profile_service=mock_service
        )
        
        assert result["success"] is True
        assert result["preview"] is True
        assert result["profile"]["full_name"] == "John Updated"
        assert result["profile"]["bio"] == "New bio"
        assert "ui" in result
    
    @pytest.mark.asyncio
    async def test_preview_changes_unauthorized(self):
        """Test preview for different user."""
        mock_service = Mock(spec=ProfileService)
        
        with pytest.raises(HTTPException) as exc_info:
            await preview_profile_changes(
                user_id="user123",
                full_name="John Updated",
                current_user_id="user456",
                profile_service=mock_service
            )
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Cannot preview another user's profile"
    
    @pytest.mark.asyncio
    async def test_preview_changes_not_found(self):
        """Test preview when profile doesn't exist."""
        mock_service = Mock(spec=ProfileService)
        mock_service.get_profile = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await preview_profile_changes(
                user_id="user123",
                full_name="John Updated",
                current_user_id="user123",
                profile_service=mock_service
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Profile not found"
    
    @pytest.mark.asyncio
    async def test_preview_partial_changes(self):
        """Test preview with only some fields changed."""
        mock_service = Mock(spec=ProfileService)
        current_profile = ProfileData(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            full_name="John Doe",
            bio="Original bio",
            location="New York",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_service.get_profile = AsyncMock(return_value=current_profile)
        
        result = await preview_profile_changes(
            user_id="user123",
            bio="Updated bio",
            current_user_id="user123",
            profile_service=mock_service
        )
        
        assert result["success"] is True
        assert result["profile"]["full_name"] == "John Doe"  # Unchanged
        assert result["profile"]["bio"] == "Updated bio"  # Changed
        assert result["profile"]["location"] == "New York"  # Unchanged
    
    @pytest.mark.asyncio
    async def test_preview_no_changes(self):
        """Test preview with no changes provided."""
        mock_service = Mock(spec=ProfileService)
        current_profile = ProfileData(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            full_name="John Doe",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_service.get_profile = AsyncMock(return_value=current_profile)
        
        result = await preview_profile_changes(
            user_id="user123",
            current_user_id="user123",
            profile_service=mock_service
        )
        
        assert result["success"] is True
        assert result["profile"]["full_name"] == "John Doe"
        assert result["profile"]["username"] == "johndoe"


class TestRouteIntegration:
    """Integration tests for route flows."""
    
    @pytest.mark.asyncio
    async def test_view_edit_update_flow(self):
        """Test complete flow: view -> edit form -> update."""
        mock_service = Mock(spec=ProfileService)
        
        # Initial profile
        initial_profile = ProfileData(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            full_name="John Doe",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Updated profile
        updated_profile = ProfileData(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            full_name="John Updated",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_service.get_profile = AsyncMock(return_value=initial_profile)
        mock_service.update_profile = AsyncMock(return_value=updated_profile)
        
        # Step 1: View profile
        view_result = await get_profile_page("user123", mock_service)
        assert view_result["success"] is True
        
        # Step 2: Get edit form
        form_result = await get_profile_edit_form("user123", "user123", mock_service)
        assert form_result["success"] is True
        
        # Step 3: Update profile
        update_data = ProfileUpdateRequest(full_name="John Updated")
        update_result = await update_profile("user123", update_data, "user123", mock_service)
        assert update_result["success"] is True
        assert update_result["profile"]["full_name"] == "John Updated"
