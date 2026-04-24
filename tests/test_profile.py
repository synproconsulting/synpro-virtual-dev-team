"""
Unit tests for profile module.

Tests for UserProfile model, ProfileUpdateRequest validation,
ProfileService operations, and ProfileUIRenderer formatting.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.auth.profile import (
    UserProfile,
    ProfileUpdateRequest,
    ProfileService,
    ProfileUIRenderer
)


class TestUserProfile:
    """Test cases for UserProfile model."""
    
    def test_user_profile_creation_valid(self):
        """Test creating a valid user profile."""
        profile = UserProfile(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            full_name="John Doe",
            bio="Software developer",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_verified=True
        )
        
        assert profile.user_id == "user123"
        assert profile.username == "johndoe"
        assert profile.email == "john@example.com"
        assert profile.full_name == "John Doe"
        assert profile.is_verified is True
    
    def test_user_profile_optional_fields(self):
        """Test user profile with minimal required fields."""
        profile = UserProfile(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert profile.full_name is None
        assert profile.bio is None
        assert profile.avatar_url is None
        assert profile.is_verified is False
    
    def test_user_profile_invalid_email(self):
        """Test user profile with invalid email."""
        with pytest.raises(ValidationError):
            UserProfile(
                user_id="user123",
                username="johndoe",
                email="invalid-email",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
    
    def test_bio_validation_removes_excess_whitespace(self):
        """Test bio validation removes excessive whitespace."""
        profile = UserProfile(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            bio="This   has    too     much    whitespace",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert profile.bio == "This has too much whitespace"
    
    def test_bio_max_length(self):
        """Test bio field respects maximum length."""
        long_bio = "a" * 501
        with pytest.raises(ValidationError):
            UserProfile(
                user_id="user123",
                username="johndoe",
                email="john@example.com",
                bio=long_bio,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
    
    def test_website_validation_requires_protocol(self):
        """Test website URL must start with http:// or https://."""
        with pytest.raises(ValidationError):
            UserProfile(
                user_id="user123",
                username="johndoe",
                email="john@example.com",
                website="example.com",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
    
    def test_website_validation_accepts_valid_url(self):
        """Test website accepts valid URLs."""
        profile = UserProfile(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            website="https://example.com",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert profile.website == "https://example.com"


class TestProfileUpdateRequest:
    """Test cases for ProfileUpdateRequest model."""
    
    def test_profile_update_request_valid(self):
        """Test creating a valid profile update request."""
        update = ProfileUpdateRequest(
            full_name="Jane Doe",
            bio="Updated bio",
            phone_number="+1234567890",
            location="New York, NY",
            website="https://janedoe.com"
        )
        
        assert update.full_name == "Jane Doe"
        assert update.bio == "Updated bio"
        assert update.phone_number == "+1234567890"
    
    def test_profile_update_request_optional(self):
        """Test profile update with partial fields."""
        update = ProfileUpdateRequest(
            full_name="Jane Doe"
        )
        
        assert update.full_name == "Jane Doe"
        assert update.bio is None
        assert update.phone_number is None
    
    def test_phone_number_validation_min_length(self):
        """Test phone number validation requires minimum digits."""
        with pytest.raises(ValidationError):
            ProfileUpdateRequest(
                phone_number="123"
            )
    
    def test_phone_number_validation_accepts_valid(self):
        """Test phone number accepts valid format."""
        update = ProfileUpdateRequest(
            phone_number="+1 (555) 123-4567"
        )
        
        assert update.phone_number == "+1 (555) 123-4567"
    
    def test_full_name_max_length(self):
        """Test full name respects maximum length."""
        long_name = "a" * 101
        with pytest.raises(ValidationError):
            ProfileUpdateRequest(
                full_name=long_name
            )


class TestProfileService:
    """Test cases for ProfileService."""
    
    def test_profile_service_requires_database_url(self):
        """Test ProfileService raises error without database URL."""
        with pytest.raises(ValueError, match="DATABASE_URL environment variable is required"):
            ProfileService(database_url=None)
    
    def test_profile_service_initialization(self):
        """Test ProfileService initializes with database URL."""
        service = ProfileService(database_url="postgresql://localhost/test")
        assert service.database_url == "postgresql://localhost/test"
    
    @pytest.mark.asyncio
    async def test_upload_avatar_validates_content_type(self):
        """Test avatar upload validates content type."""
        service = ProfileService(database_url="postgresql://localhost/test")
        
        with pytest.raises(ValueError, match="Invalid file type"):
            await service.upload_avatar(
                user_id="user123",
                file_data=b"fake_image_data",
                content_type="application/pdf"
            )
    
    @pytest.mark.asyncio
    async def test_upload_avatar_validates_file_size(self):
        """Test avatar upload validates file size."""
        service = ProfileService(database_url="postgresql://localhost/test")
        
        # Create file data larger than 5MB
        large_file = b"0" * (6 * 1024 * 1024)
        
        with pytest.raises(ValueError, match="File size exceeds 5MB limit"):
            await service.upload_avatar(
                user_id="user123",
                file_data=large_file,
                content_type="image/jpeg"
            )


class TestProfileUIRenderer:
    """Test cases for ProfileUIRenderer."""
    
    def test_format_profile_for_display(self):
        """Test formatting profile for UI display."""
        profile = UserProfile(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            full_name="John Doe",
            bio="Software developer",
            avatar_url="https://example.com/avatar.jpg",
            created_at=datetime(2023, 1, 15, 10, 30),
            updated_at=datetime(2024, 2, 20, 14, 45),
            is_verified=True,
            phone_number="+1234567890",
            location="San Francisco, CA",
            website="https://johndoe.com"
        )
        
        formatted = ProfileUIRenderer.format_profile_for_display(profile)
        
        assert formatted['userId'] == "user123"
        assert formatted['username'] == "johndoe"
        assert formatted['fullName'] == "John Doe"
        assert formatted['bio'] == "Software developer"
        assert formatted['verified'] is True
        assert formatted['memberSince'] == "January 2023"
        assert formatted['lastUpdated'] == "2024-02-20"
        assert formatted['contactInfo']['phone'] == "+1234567890"
        assert formatted['contactInfo']['location'] == "San Francisco, CA"
    
    def test_format_profile_defaults_fullname_to_username(self):
        """Test formatting uses username when full_name is None."""
        profile = UserProfile(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        formatted = ProfileUIRenderer.format_profile_for_display(profile)
        
        assert formatted['fullName'] == "johndoe"
    
    def test_format_profile_uses_default_avatar(self):
        """Test formatting uses default avatar when none provided."""
        profile = UserProfile(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        formatted = ProfileUIRenderer.format_profile_for_display(profile)
        
        assert formatted['avatarUrl'] == "/static/images/default-avatar.png"
    
    def test_get_profile_sections(self):
        """Test getting profile UI sections configuration."""
        sections = ProfileUIRenderer.get_profile_sections()
        
        assert 'sections' in sections
        assert 'theme' in sections
        assert len(sections['sections']) == 4
        
        # Check header section
        header = sections['sections'][0]
        assert header['id'] == 'header'
        assert header['type'] == 'profile-header'
        assert header['editable'] is False
        
        # Check about section
        about = sections['sections'][1]
        assert about['id'] == 'about'
        assert about['title'] == 'About'
        assert about['editable'] is True
        
        # Check theme
        assert 'primaryColor' in sections['theme']
        assert 'secondaryColor' in sections['theme']
        assert 'accentColor' in sections['theme']
