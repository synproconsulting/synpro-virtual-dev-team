"""
Unit tests for change password functionality.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from src.auth.change_password import (
    PasswordChangeRequest,
    PasswordChangeResponse,
    PasswordChangeService,
)
from src.auth.user_repository import InMemoryUserRepository


class TestPasswordChangeRequest:
    """Test cases for PasswordChangeRequest model."""
    
    def test_valid_password_change_request(self):
        """Test creating a valid password change request."""
        request = PasswordChangeRequest(
            user_id="user123",
            current_password="OldPass123!",
            new_password="NewPass456@",
            confirm_password="NewPass456@"
        )
        
        assert request.user_id == "user123"
        assert request.current_password == "OldPass123!"
        assert request.new_password == "NewPass456@"
        assert request.confirm_password == "NewPass456@"
    
    def test_password_too_short(self):
        """Test that password must be at least 8 characters."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(
                user_id="user123",
                current_password="OldPass123!",
                new_password="Short1!",
                confirm_password="Short1!"
            )
        
        assert "at least 8 characters" in str(exc_info.value)
    
    def test_password_missing_uppercase(self):
        """Test that password must contain uppercase letter."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(
                user_id="user123",
                current_password="OldPass123!",
                new_password="newpass123!",
                confirm_password="newpass123!"
            )
        
        assert "uppercase letter" in str(exc_info.value)
    
    def test_password_missing_lowercase(self):
        """Test that password must contain lowercase letter."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(
                user_id="user123",
                current_password="OldPass123!",
                new_password="NEWPASS123!",
                confirm_password="NEWPASS123!"
            )
        
        assert "lowercase letter" in str(exc_info.value)
    
    def test_password_missing_digit(self):
        """Test that password must contain digit."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(
                user_id="user123",
                current_password="OldPass123!",
                new_password="NewPassword!",
                confirm_password="NewPassword!"
            )
        
        assert "digit" in str(exc_info.value)
    
    def test_password_missing_special_character(self):
        """Test that password must contain special character."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(
                user_id="user123",
                current_password="OldPass123!",
                new_password="NewPass123",
                confirm_password="NewPass123"
            )
        
        assert "special character" in str(exc_info.value)
    
    def test_passwords_dont_match(self):
        """Test that new password and confirmation must match."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(
                user_id="user123",
                current_password="OldPass123!",
                new_password="NewPass456@",
                confirm_password="DifferentPass789#"
            )
        
        assert "do not match" in str(exc_info.value)


class TestPasswordChangeService:
    """Test cases for PasswordChangeService."""
    
    @pytest.fixture
    def user_repository(self):
        """Create a fresh user repository for each test."""
        repo = InMemoryUserRepository()
        yield repo
        repo.clear()
    
    @pytest.fixture
    def password_service(self, user_repository):
        """Create a password change service with repository."""
        return PasswordChangeService(user_repository=user_repository)
    
    @pytest.fixture
    def test_user(self, user_repository, password_service):
        """Create a test user."""
        user_id = "test_user_123"
        password_hash = password_service.hash_password("OldPassword123!")
        user = user_repository.create_user(
            user_id=user_id,
            password_hash=password_hash,
            email="test@example.com"
        )
        return user
    
    def test_hash_password(self, password_service):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = password_service.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert password_service.verify_password(password, hashed)
    
    def test_verify_password_correct(self, password_service):
        """Test verifying correct password."""
        password = "TestPassword123!"
        hashed = password_service.hash_password(password)
        
        assert password_service.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self, password_service):
        """Test verifying incorrect password."""
        password = "TestPassword123!"
        hashed = password_service.hash_password(password)
        
        assert password_service.verify_password("WrongPassword!", hashed) is False
    
    def test_successful_password_change(self, password_service, test_user):
        """Test successful password change."""
        request = PasswordChangeRequest(
            user_id=test_user["user_id"],
            current_password="OldPassword123!",
            new_password="NewPassword456@",
            confirm_password="NewPassword456@"
        )
        
        response = password_service.change_password(request)
        
        assert response.success is True
        assert "successfully" in response.message
        assert response.changed_at is not None
        assert isinstance(response.changed_at, datetime)
    
    def test_change_password_wrong_current_password(self, password_service, test_user):
        """Test password change with incorrect current password."""
        request = PasswordChangeRequest(
            user_id=test_user["user_id"],
            current_password="WrongPassword123!",
            new_password="NewPassword456@",
            confirm_password="NewPassword456@"
        )
        
        response = password_service.change_password(request)
        
        assert response.success is False
        assert "incorrect" in response.message.lower()
    
    def test_change_password_user_not_found(self, password_service):
        """Test password change for non-existent user."""
        request = PasswordChangeRequest(
            user_id="nonexistent_user",
            current_password="OldPassword123!",
            new_password="NewPassword456@",
            confirm_password="NewPassword456@"
        )
        
        response = password_service.change_password(request)
        
        assert response.success is False
        assert "not found" in response.message.lower()
    
    def test_change_password_same_as_current(self, password_service, test_user):
        """Test that new password cannot be same as current."""
        request = PasswordChangeRequest(
            user_id=test_user["user_id"],
            current_password="OldPassword123!",
            new_password="OldPassword123!",
            confirm_password="OldPassword123!"
        )
        
        response = password_service.change_password(request)
        
        assert response.success is False
        assert "different from current" in response.message.lower()
    
    def test_password_history_check(self, password_service, test_user, user_repository):
        """Test that recently used passwords cannot be reused."""
        # Change password first time
        request1 = PasswordChangeRequest(
            user_id=test_user["user_id"],
            current_password="OldPassword123!",
            new_password="NewPassword456@",
            confirm_password="NewPassword456@"
        )
        response1 = password_service.change_password(request1)
        assert response1.success is True
        
        # Try to change back to old password
        request2 = PasswordChangeRequest(
            user_id=test_user["user_id"],
            current_password="NewPassword456@",
            new_password="OldPassword123!",
            confirm_password="OldPassword123!"
        )
        response2 = password_service.change_password(request2)
        
        assert response2.success is False
        assert "recently used" in response2.message.lower()
    
    def test_check_password_in_history(self, password_service, test_user):
        """Test checking if password exists in history."""
        # The initial password should be in history
        in_history = password_service.check_password_in_history(
            test_user["user_id"], 
            "OldPassword123!"
        )
        
        assert in_history is True
        
        # A new password should not be in history
        not_in_history = password_service.check_password_in_history(
            test_user["user_id"], 
            "BrandNewPassword789#"
        )
        
        assert not_in_history is False
    
    def test_should_force_password_change_never_changed(self, password_service, user_repository):
        """Test force password change for user with no password_changed_at."""
        user = user_repository.create_user(
            user_id="new_user",
            password_hash="hash",
            email="new@example.com"
        )
        
        # Remove password_changed_at to simulate never changed
        user_repository._users["new_user"]["password_changed_at"] = None
        
        should_force = password_service.should_force_password_change("new_user")
        assert should_force is True
    
    def test_should_force_password_change_too_old(self, password_service, user_repository):
        """Test force password change for expired password."""
        user = user_repository.create_user(
            user_id="old_user",
            password_hash="hash",
            email="old@example.com"
        )
        
        # Set password change date to 91 days ago (default max age is 90)
        old_date = datetime.utcnow() - timedelta(days=91)
        user_repository._users["old_user"]["password_changed_at"] = old_date
        
        should_force = password_service.should_force_password_change("old_user")
        assert should_force is True
    
    def test_should_not_force_password_change_recent(self, password_service, test_user):
        """Test that recent password change doesn't force change."""
        should_force = password_service.should_force_password_change(test_user["user_id"])
        assert should_force is False
    
    def test_password_updated_in_repository(self, password_service, test_user, user_repository):
        """Test that password is actually updated in repository."""
        new_password = "NewPassword456@"
        
        request = PasswordChangeRequest(
            user_id=test_user["user_id"],
            current_password="OldPassword123!",
            new_password=new_password,
            confirm_password=new_password
        )
        
        response = password_service.change_password(request)
        assert response.success is True
        
        # Verify password was updated
        updated_user = user_repository.get_user_by_id(test_user["user_id"])
        assert password_service.verify_password(new_password, updated_user["password_hash"])
    
    def test_service_without_repository(self):
        """Test service behavior without repository."""
        service = PasswordChangeService(user_repository=None)
        
        request = PasswordChangeRequest(
            user_id="user123",
            current_password="OldPass123!",
            new_password="NewPass456@",
            confirm_password="NewPass456@"
        )
        
        with pytest.raises(ValueError) as exc_info:
            service.change_password(request)
        
        assert "not configured" in str(exc_info.value)


class TestPasswordChangeResponse:
    """Test cases for PasswordChangeResponse model."""
    
    def test_success_response(self):
        """Test creating a success response."""
        response = PasswordChangeResponse(
            success=True,
            message="Password changed successfully",
            changed_at=datetime.utcnow()
        )
        
        assert response.success is True
        assert "successfully" in response.message
        assert response.changed_at is not None
    
    def test_failure_response(self):
        """Test creating a failure response."""
        response = PasswordChangeResponse(
            success=False,
            message="Current password is incorrect"
        )
        
        assert response.success is False
        assert "incorrect" in response.message
        assert response.changed_at is None
