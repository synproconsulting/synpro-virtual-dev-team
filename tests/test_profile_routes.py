"""
Unit tests for profile API routes.

Tests for FastAPI profile endpoints including GET, PUT, POST, and DELETE operations.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from src.auth.profile import UserProfile, ProfileUpdateRequest, ProfileService
from src.auth.profile_routes import (
    router,
    get_profile_service,
    get_current_user_id
)


@pytest.fixture
def mock_profile():
    """Fixture providing a mock UserProfile."""
    return UserProfile(
        user_id="user123",
        username="johndoe",
        email="john@example.com",
        full_name="John Doe",
        bio="Software developer",
        avatar_url="https://example.com/avatar.jpg",
        created_at=datetime(2023, 1, 15),
        updated_at=datetime(2024, 2, 20),
        is_verified=True,
        phone_number="+1234567890",
        location="San Francisco, CA",
        website="https://johndoe.com"
    )


@pytest.fixture
def mock_profile_service():
    """Fixture providing a mock ProfileService."""
    service = Mock(spec=ProfileService)
    service.get_profile = AsyncMock()
    service.update_profile = AsyncMock()
    service.upload_avatar = AsyncMock()
    service.delete_avatar = AsyncMock()
    return service


class TestGetProfile:
    """Test cases for GET /api/profile/{user_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_profile_success(self, mock_profile, mock_profile_service):
        """Test successful profile retrieval."""
        mock_profile_service.get_profile.return_value = mock_profile
        
        from src.auth.profile_routes import get_profile
        
        result = await get_profile(
            user_id="user123",
            service=mock_profile_service
        )
        
        assert result['userId'] == "user123"
        assert result['username'] == "johndoe"
        assert result['email'] == "john@example.com"
        mock_profile_service.get_profile.assert_called_once_with("user123")
    
    @pytest.mark.asyncio
    async def test_get_profile_not_found(self, mock_profile_service):
        """Test profile not found returns 404."""
        mock_profile_service.get_profile.return_value = None
        
        from src.auth.profile_routes import get_profile
        
        with pytest.raises(HTTPException) as exc_info:
            await get_profile(
                user_id="nonexistent",
                service=mock_profile_service
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in str(exc_info.value.detail).lower()


class TestGetMyProfile:
    """Test cases for GET /api/profile/me endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_my_profile_success(self, mock_profile, mock_profile_service):
        """Test successful retrieval of current user's profile."""
        mock_profile_service.get_profile.return_value = mock_profile
        
        from src.auth.profile_routes import get_my_profile
        
        result = await get_my_profile(
            current_user_id="user123",
            service=mock_profile_service
        )
        
        assert result['userId'] == "user123"
        assert result['username'] == "johndoe"
        mock_profile_service.get_profile.assert_called_once_with("user123")
    
    @pytest.mark.asyncio
    async def test_get_my_profile_not_found(self, mock_profile_service):
        """Test current user profile not found returns 404."""
        mock_profile_service.get_profile.return_value = None
        
        from src.auth.profile_routes import get_my_profile
        
        with pytest.raises(HTTPException) as exc_info:
            await get_my_profile(
                current_user_id="user123",
                service=mock_profile_service
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateMyProfile:
    """Test cases for PUT /api/profile/me endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_my_profile_success(self, mock_profile, mock_profile_service):
        """Test successful profile update."""
        update_data = ProfileUpdateRequest(
            full_name="John Updated Doe",
            bio="Updated bio"
        )
        
        mock_profile_service.update_profile.return_value = mock_profile
        
        from src.auth.profile_routes import update_my_profile
        
        result = await update_my_profile(
            update_data=update_data,
            current_user_id="user123",
            service=mock_profile_service
        )
        
        assert result['userId'] == "user123"
        mock_profile_service.update_profile.assert_called_once_with("user123", update_data)
    
    @pytest.mark.asyncio
    async def test_update_my_profile_validation_error(self, mock_profile_service):
        """Test profile update with validation error."""
        from pydantic import ValidationError
        
        update_data = ProfileUpdateRequest(full_name="John Doe")
        mock_profile_service.update_profile.side_effect = ValidationError.from_exception_data(
            "test",
            []
        )
        
        from src.auth.profile_routes import update_my_profile
        
        with pytest.raises(HTTPException) as exc_info:
            await update_my_profile(
                update_data=update_data,
                current_user_id="user123",
                service=mock_profile_service
            )
        
        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_update_my_profile_value_error(self, mock_profile_service):
        """Test profile update with value error."""
        update_data = ProfileUpdateRequest(full_name="John Doe")
        mock_profile_service.update_profile.side_effect = ValueError("Invalid data")
        
        from src.auth.profile_routes import update_my_profile
        
        with pytest.raises(HTTPException) as exc_info:
            await update_my_profile(
                update_data=update_data,
                current_user_id="user123",
                service=mock_profile_service
            )
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid data" in str(exc_info.value.detail)


class TestUploadAvatar:
    """Test cases for POST /api/profile/me/avatar endpoint."""
    
    @pytest.mark.asyncio
    async def test_upload_avatar_success(self, mock_profile_service):
        """Test successful avatar upload."""
        mock_file = Mock()
        mock_file.content_type = "image/jpeg"
        mock_file.read = AsyncMock(return_value=b"fake_image_data")
        
        mock_profile_service.upload_avatar.return_value = "https://example.com/new-avatar.jpg"
        
        from src.auth.profile_routes import upload_avatar
        
        result = await upload_avatar(
            file=mock_file,
            current_user_id="user123",
            service=mock_profile_service
        )
        
        assert result['message'] == "Avatar uploaded successfully"
        assert result['avatarUrl'] == "https://example.com/new-avatar.jpg"
        mock_profile_service.upload_avatar.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_avatar_no_content_type(self, mock_profile_service):
        """Test avatar upload without content type."""
        mock_file = Mock()
        mock_file.content_type = None
        
        from src.auth.profile_routes import upload_avatar
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_avatar(
                file=mock_file,
                current_user_id="user123",
                service=mock_profile_service
            )
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "content type is required" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_upload_avatar_invalid_file_type(self, mock_profile_service):
        """Test avatar upload with invalid file type."""
        mock_file = Mock()
        mock_file.content_type = "image/jpeg"
        mock_file.read = AsyncMock(return_value=b"fake_image_data")
        
        mock_profile_service.upload_avatar.side_effect = ValueError("Invalid file type")
        
        from src.auth.profile_routes import upload_avatar
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_avatar(
                file=mock_file,
                current_user_id="user123",
                service=mock_profile_service
            )
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


class TestDeleteAvatar:
    """Test cases for DELETE /api/profile/me/avatar endpoint."""
    
    @pytest.mark.asyncio
    async def test_delete_avatar_success(self, mock_profile_service):
        """Test successful avatar deletion."""
        mock_profile_service.delete_avatar.return_value = None
        
        from src.auth.profile_routes import delete_avatar
        
        result = await delete_avatar(
            current_user_id="user123",
            service=mock_profile_service
        )
        
        assert result is None
        mock_profile_service.delete_avatar.assert_called_once_with("user123")


class TestGetProfileLayout:
    """Test cases for GET /api/profile/ui/layout endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_profile_layout(self):
        """Test getting profile UI layout configuration."""
        from src.auth.profile_routes import get_profile_layout
        
        result = await get_profile_layout()
        
        assert 'sections' in result
        assert 'theme' in result
        assert len(result['sections']) > 0
        
        # Verify section structure
        for section in result['sections']:
            assert 'id' in section
            assert 'type' in section
            assert 'fields' in section
            assert 'editable' in section


class TestDependencies:
    """Test cases for dependency injection functions."""
    
    def test_get_profile_service(self):
        """Test get_profile_service dependency."""
        # This would need DATABASE_URL environment variable
        # In real scenario, we'd mock the environment
        pass
    
    def test_get_current_user_id_not_authenticated(self):
        """Test get_current_user_id raises 401 when not authenticated."""
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id()
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "not authenticated" in str(exc_info.value.detail).lower()
