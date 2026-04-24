"""
Unit tests for profile management functionality.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.auth.profile import (
    ProfileUpdate,
    PasswordChangeRequest,
    ProfileResponse,
    hash_password,
    verify_password,
    ProfileService,
)


class TestProfileModels:
    """Test profile data models."""
    
    def test_profile_update_valid(self):
        """Test valid profile update data."""
        profile_data = ProfileUpdate(
            email="user@example.com",
            full_name="John Doe",
            phone_number="+1-234-567-8900",
            bio="Software developer",
        )
        
        assert profile_data.email == "user@example.com"
        assert profile_data.full_name == "John Doe"
        assert profile_data.phone_number == "+1-234-567-8900"
        assert profile_data.bio == "Software developer"
    
    def test_profile_update_invalid_email(self):
        """Test profile update with invalid email."""
        with pytest.raises(ValidationError):
            ProfileUpdate(email="not-an-email")
    
    def test_profile_update_invalid_phone(self):
        """Test profile update with invalid phone number."""
        with pytest.raises(ValidationError):
            ProfileUpdate(phone_number="abc-def-ghij")
    
    def test_profile_update_partial(self):
        """Test partial profile update."""
        profile_data = ProfileUpdate(full_name="Jane Smith")
        
        assert profile_data.full_name == "Jane Smith"
        assert profile_data.email is None
        assert profile_data.phone_number is None
    
    def test_profile_response_model(self):
        """Test profile response model."""
        response = ProfileResponse(
            user_id="123",
            username="johndoe",
            email="john@example.com",
            full_name="John Doe",
            phone_number="+1234567890",
            bio="Developer",
            avatar_url="https://example.com/avatar.jpg",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True,
        )
        
        assert response.user_id == "123"
        assert response.username == "johndoe"
        assert response.is_active is True


class TestPasswordChangeRequest:
    """Test password change request model."""
    
    def test_valid_password_change(self):
        """Test valid password change request."""
        request = PasswordChangeRequest(
            current_password="OldPass123",
            new_password="NewPass456",
            confirm_password="NewPass456",
        )
        
        assert request.current_password == "OldPass123"
        assert request.new_password == "NewPass456"
        assert request.confirm_password == "NewPass456"
    
    def test_password_too_short(self):
        """Test password change with short password."""
        with pytest.raises(ValidationError):
            PasswordChangeRequest(
                current_password="OldPass123",
                new_password="Short1",
                confirm_password="Short1",
            )
    
    def test_passwords_do_not_match(self):
        """Test password change with mismatched passwords."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(
                current_password="OldPass123",
                new_password="NewPass456",
                confirm_password="DifferentPass789",
            )
        
        assert "Passwords do not match" in str(exc_info.value)
    
    def test_same_as_current_password(self):
        """Test new password same as current password."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(
                current_password="SamePass123",
                new_password="SamePass123",
                confirm_password="SamePass123",
            )
        
        assert "must be different from current password" in str(exc_info.value)
    
    def test_password_no_uppercase(self):
        """Test password without uppercase letter."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(
                current_password="OldPass123",
                new_password="newpass456",
                confirm_password="newpass456",
            )
        
        assert "uppercase" in str(exc_info.value)
    
    def test_password_no_lowercase(self):
        """Test password without lowercase letter."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(
                current_password="OldPass123",
                new_password="NEWPASS456",
                confirm_password="NEWPASS456",
            )
        
        assert "lowercase" in str(exc_info.value)
    
    def test_password_no_digit(self):
        """Test password without digit."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(
                current_password="OldPass123",
                new_password="NewPassword",
                confirm_password="NewPassword",
            )
        
        assert "digit" in str(exc_info.value)


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "SecurePass123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt prefix
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "SecurePass123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "SecurePass123"
        wrong_password = "WrongPass456"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_hash_produces_different_hashes(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "SecurePass123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestProfileService:
    """Test ProfileService class."""
    
    def test_service_initialization(self):
        """Test ProfileService initialization."""
        service = ProfileService(database_connection=None)
        assert service.db is None
    
    @pytest.mark.asyncio
    async def test_get_profile_not_implemented(self):
        """Test get_profile raises NotImplementedError without database."""
        service = ProfileService(database_connection=None)
        
        with pytest.raises(NotImplementedError):
            await service.get_profile("user123")
    
    @pytest.mark.asyncio
    async def test_update_profile_not_implemented(self):
        """Test update_profile raises NotImplementedError without database."""
        service = ProfileService(database_connection=None)
        profile_data = ProfileUpdate(full_name="John Doe")
        
        with pytest.raises(NotImplementedError):
            await service.update_profile("user123", profile_data)
    
    @pytest.mark.asyncio
    async def test_change_password_not_implemented(self):
        """Test change_password raises NotImplementedError without database."""
        service = ProfileService(database_connection=None)
        password_change = PasswordChangeRequest(
            current_password="OldPass123",
            new_password="NewPass456",
            confirm_password="NewPass456",
        )
        
        with pytest.raises(NotImplementedError):
            await service.change_password("user123", password_change)
    
    @pytest.mark.asyncio
    async def test_deactivate_profile_not_implemented(self):
        """Test deactivate_profile raises NotImplementedError without database."""
        service = ProfileService(database_connection=None)
        
        with pytest.raises(NotImplementedError):
            await service.deactivate_profile("user123")


class TestPhoneNumberValidation:
    """Test phone number validation."""
    
    def test_valid_phone_formats(self):
        """Test various valid phone number formats."""
        valid_phones = [
            "+1234567890",
            "123-456-7890",
            "123 456 7890",
            "+1-234-567-8900",
            "1234567890",
        ]
        
        for phone in valid_phones:
            profile = ProfileUpdate(phone_number=phone)
            assert profile.phone_number == phone
    
    def test_invalid_phone_with_letters(self):
        """Test phone number with letters is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            ProfileUpdate(phone_number="123-ABC-7890")
        
        assert "must contain only digits" in str(exc_info.value)


class TestBioValidation:
    """Test bio field validation."""
    
    def test_bio_within_limit(self):
        """Test bio within character limit."""
        bio = "A" * 500
        profile = ProfileUpdate(bio=bio)
        assert len(profile.bio) == 500
    
    def test_bio_exceeds_limit(self):
        """Test bio exceeding character limit."""
        bio = "A" * 501
        with pytest.raises(ValidationError):
            ProfileUpdate(bio=bio)
    
    def test_bio_empty(self):
        """Test empty bio is allowed."""
        profile = ProfileUpdate(bio="")
        assert profile.bio == ""
