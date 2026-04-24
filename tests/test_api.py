"""
Unit tests for profile management API endpoints.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime
import jwt

from src.auth.api import (
    get_current_user_id,
    get_my_profile,
    update_my_profile,
    change_password,
    deactivate_my_profile,
    get_user_profile,
)
from src.auth.profile import (
    ProfileUpdate,
    ProfileResponse,
    PasswordChangeRequest,
    ProfileService,
)


class TestGetCurrentUserId:
    """Test JWT token extraction and validation."""
    
    def test_valid_token(self):
        """Test extracting user ID from valid token."""
        user_id = "user123"
        secret_key = "test-secret-key"
        
        # Create a valid JWT token
        token = jwt.encode(
            {"sub": user_id, "exp": datetime.utcnow().timestamp() + 3600},
            secret_key,
            algorithm="HS256"
        )
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        with patch.dict("os.environ", {"JWT_SECRET_KEY": secret_key}):
            result = get_current_user_id(credentials)
            assert result == user_id
    
    def test_token_without_sub(self):
        """Test token without 'sub' claim raises exception."""
        secret_key = "test-secret-key"
        
        # Create token without 'sub'
        token = jwt.encode(
            {"user": "user123", "exp": datetime.utcnow().timestamp() + 3600},
            secret_key,
            algorithm="HS256"
        )
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        with patch.dict("os.environ", {"JWT_SECRET_KEY": secret_key}):
            with pytest.raises(HTTPException) as exc_info:
                get_current_user_id(credentials)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid authentication credentials" in exc_info.value.detail
    
    def test_invalid_token(self):
        """Test invalid token raises exception."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token.here"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id(credentials)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in exc_info.value.detail
    
    def test_expired_token(self):
        """Test expired token raises exception."""
        user_id = "user123"
        secret_key = "test-secret-key"
        
        # Create an expired token
        token = jwt.encode(
            {"sub": user_id, "exp": datetime.utcnow().timestamp() - 3600},
            secret_key,
            algorithm="HS256"
        )
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        with patch.dict("os.environ", {"JWT_SECRET_KEY": secret_key}):
            with pytest.raises(HTTPException) as exc_info:
                get_current_user_id(credentials)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Token has expired" in exc_info.value.detail


class TestGetMyProfile:
    """Test GET /me endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_profile_success(self):
        """Test successful profile retrieval."""
        user_id = "user123"
        
        mock_profile = ProfileResponse(
            user_id=user_id,
            username="johndoe",
            email="john@example.com",
            full_name="John Doe",
            phone_number="+1234567890",
            bio="Developer",
            avatar_url=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True,
        )
        
        mock_service = Mock(spec=ProfileService)
        mock_service.get_profile = AsyncMock(return_value=mock_profile)
        
        result = await get_my_profile(user_id, mock_service)
        
        assert result == mock_profile
        mock_service.get_profile.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_get_profile_not_found(self):
        """Test profile not found raises 404."""
        user_id = "user123"
        
        mock_service = Mock(spec=ProfileService)
        mock_service.get_profile = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_my_profile(user_id, mock_service)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Profile not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_profile_not_implemented(self):
        """Test get_profile with NotImplementedError raises 501."""
        user_id = "user123"
        
        mock_service = Mock(spec=ProfileService)
        mock_service.get_profile = AsyncMock(side_effect=NotImplementedError())
        
        with pytest.raises(HTTPException) as exc_info:
            await get_my_profile(user_id, mock_service)
        
        assert exc_info.value.status_code == status.HTTP_501_NOT_IMPLEMENTED


class TestUpdateMyProfile:
    """Test PUT /me endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_profile_success(self):
        """Test successful profile update."""
        user_id = "user123"
        
        profile_data = ProfileUpdate(
            full_name="Jane Doe",
            bio="Updated bio",
        )
        
        mock_response = ProfileResponse(
            user_id=user_id,
            username="janedoe",
            email="jane@example.com",
            full_name="Jane Doe",
            phone_number=None,
            bio="Updated bio",
            avatar_url=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True,
        )
        
        mock_service = Mock(spec=ProfileService)
        mock_service.update_profile = AsyncMock(return_value=mock_response)
        
        result = await update_my_profile(profile_data, user_id, mock_service)
        
        assert result == mock_response
        mock_service.update_profile.assert_called_once_with(user_id, profile_data)
    
    @pytest.mark.asyncio
    async def test_update_profile_not_found(self):
        """Test update profile when user not found."""
        user_id = "user123"
        profile_data = ProfileUpdate(full_name="Jane Doe")
        
        mock_service = Mock(spec=ProfileService)
        mock_service.update_profile = AsyncMock(
            side_effect=ValueError("User not found")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await update_my_profile(profile_data, user_id, mock_service)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_update_profile_not_implemented(self):
        """Test update_profile with NotImplementedError raises 501."""
        user_id = "user123"
        profile_data = ProfileUpdate(full_name="Jane Doe")
        
        mock_service = Mock(spec=ProfileService)
        mock_service.update_profile = AsyncMock(side_effect=NotImplementedError())
        
        with pytest.raises(HTTPException) as exc_info:
            await update_my_profile(profile_data, user_id, mock_service)
        
        assert exc_info.value.status_code == status.HTTP_501_NOT_IMPLEMENTED


class TestChangePassword:
    """Test POST /me/change-password endpoint."""
    
    @pytest.mark.asyncio
    async def test_change_password_success(self):
        """Test successful password change."""
        user_id = "user123"
        
        password_change = PasswordChangeRequest(
            current_password="OldPass123",
            new_password="NewPass456",
            confirm_password="NewPass456",
        )
        
        mock_service = Mock(spec=ProfileService)
        mock_service.change_password = AsyncMock(return_value=True)
        
        result = await change_password(password_change, user_id, mock_service)
        
        assert result["message"] == "Password changed successfully"
        assert "changed_at" in result
        mock_service.change_password.assert_called_once_with(user_id, password_change)
    
    @pytest.mark.asyncio
    async def test_change_password_incorrect_current(self):
        """Test password change with incorrect current password."""
        user_id = "user123"
        
        password_change = PasswordChangeRequest(
            current_password="WrongPass123",
            new_password="NewPass456",
            confirm_password="NewPass456",
        )
        
        mock_service = Mock(spec=ProfileService)
        mock_service.change_password = AsyncMock(
            side_effect=ValueError("Current password is incorrect")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await change_password(password_change, user_id, mock_service)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Current password is incorrect" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_change_password_not_implemented(self):
        """Test change_password with NotImplementedError raises 501."""
        user_id = "user123"
        
        password_change = PasswordChangeRequest(
            current_password="OldPass123",
            new_password="NewPass456",
            confirm_password="NewPass456",
        )
        
        mock_service = Mock(spec=ProfileService)
        mock_service.change_password = AsyncMock(side_effect=NotImplementedError())
        
        with pytest.raises(HTTPException) as exc_info:
            await change_password(password_change, user_id, mock_service)
        
        assert exc_info.value.status_code == status.HTTP_501_NOT_IMPLEMENTED


class TestDeactivateMyProfile:
    """Test DELETE /me endpoint."""
    
    @pytest.mark.asyncio
    async def test_deactivate_profile_success(self):
        """Test successful profile deactivation."""
        user_id = "user123"
        
        mock_service = Mock(spec=ProfileService)
        mock_service.deactivate_profile = AsyncMock(return_value=True)
        
        result = await deactivate_my_profile(user_id, mock_service)
        
        assert result["message"] == "Profile deactivated successfully"
        assert "deactivated_at" in result
        mock_service.deactivate_profile.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_deactivate_profile_not_found(self):
        """Test deactivate profile when user not found."""
        user_id = "user123"
        
        mock_service = Mock(spec=ProfileService)
        mock_service.deactivate_profile = AsyncMock(
            side_effect=ValueError("User not found")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await deactivate_my_profile(user_id, mock_service)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_deactivate_profile_not_implemented(self):
        """Test deactivate_profile with NotImplementedError raises 501."""
        user_id = "user123"
        
        mock_service = Mock(spec=ProfileService)
        mock_service.deactivate_profile = AsyncMock(side_effect=NotImplementedError())
        
        with pytest.raises(HTTPException) as exc_info:
            await deactivate_my_profile(user_id, mock_service)
        
        assert exc_info.value.status_code == status.HTTP_501_NOT_IMPLEMENTED


class TestGetUserProfile:
    """Test GET /{user_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_user_profile_self(self):
        """Test getting own profile by ID."""
        user_id = "user123"
        
        mock_profile = ProfileResponse(
            user_id=user_id,
            username="johndoe",
            email="john@example.com",
            full_name="John Doe",
            phone_number=None,
            bio=None,
            avatar_url=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True,
        )
        
        mock_service = Mock(spec=ProfileService)
        mock_service.get_profile = AsyncMock(return_value=mock_profile)
        
        result = await get_user_profile(user_id, user_id, mock_service)
        
        assert result == mock_profile
        mock_service.get_profile.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_get_user_profile_other_forbidden(self):
        """Test getting another user's profile is forbidden."""
        current_user_id = "user123"
        target_user_id = "user456"
        
        mock_service = Mock(spec=ProfileService)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_user_profile(target_user_id, current_user_id, mock_service)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_user_profile_not_found(self):
        """Test getting profile that doesn't exist."""
        user_id = "user123"
        
        mock_service = Mock(spec=ProfileService)
        mock_service.get_profile = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_user_profile(user_id, user_id, mock_service)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Profile not found" in exc_info.value.detail
