"""
Unit tests for profile module.

Tests for profile data models, service class, and UI renderer.
"""

import pytest
from datetime import datetime
from typing import Dict, Any
from pydantic import ValidationError

from src.auth.profile import (
    ProfileData,
    ProfileUpdateRequest,
    ProfileService,
    ProfileUIRenderer
)


class TestProfileData:
    """Tests for ProfileData model."""
    
    def test_valid_profile_data(self):
        """Test creating valid profile data."""
        profile = ProfileData(
            user_id="user123",
            username="john_doe",
            email="john@example.com",
            full_name="John Doe",
            bio="Software developer",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert profile.user_id == "user123"
        assert profile.username == "john_doe"
        assert profile.email == "john@example.com"
        assert profile.is_active is True
    
    def test_username_validation_lowercase(self):
        """Test username is converted to lowercase."""
        profile = ProfileData(
            user_id="user123",
            username="JohnDoe",
            email="john@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert profile.username == "johndoe"
    
    def test_invalid_username_special_chars(self):
        """Test username validation rejects special characters."""
        with pytest.raises(ValidationError):
            ProfileData(
                user_id="user123",
                username="john@doe",
                email="john@example.com",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
    
    def test_valid_username_with_underscore_hyphen(self):
        """Test username accepts underscores and hyphens."""
        profile = ProfileData(
            user_id="user123",
            username="john_doe-123",
            email="john@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert profile.username == "john_doe-123"
    
    def test_invalid_email(self):
        """Test email validation."""
        with pytest.raises(ValidationError):
            ProfileData(
                user_id="user123",
                username="johndoe",
                email="invalid-email",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
    
    def test_website_validation_requires_protocol(self):
        """Test website URL must have http/https protocol."""
        with pytest.raises(ValidationError):
            ProfileData(
                user_id="user123",
                username="johndoe",
                email="john@example.com",
                website="example.com",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
    
    def test_valid_website_url(self):
        """Test valid website URL."""
        profile = ProfileData(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            website="https://example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert profile.website == "https://example.com"
    
    def test_optional_fields(self):
        """Test optional fields can be None."""
        profile = ProfileData(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert profile.full_name is None
        assert profile.bio is None
        assert profile.avatar_url is None
        assert profile.phone is None
        assert profile.location is None
        assert profile.website is None


class TestProfileUpdateRequest:
    """Tests for ProfileUpdateRequest model."""
    
    def test_valid_update_request(self):
        """Test creating valid profile update request."""
        update = ProfileUpdateRequest(
            full_name="John Doe",
            bio="Updated bio",
            phone="+1234567890",
            location="New York, USA",
            website="https://johndoe.com"
        )
        
        assert update.full_name == "John Doe"
        assert update.bio == "Updated bio"
        assert update.website == "https://johndoe.com"
    
    def test_partial_update_request(self):
        """Test update request with only some fields."""
        update = ProfileUpdateRequest(
            full_name="John Doe"
        )
        
        assert update.full_name == "John Doe"
        assert update.bio is None
        assert update.phone is None
    
    def test_empty_update_request(self):
        """Test empty update request."""
        update = ProfileUpdateRequest()
        
        assert update.full_name is None
        assert update.bio is None
        assert update.phone is None
        assert update.location is None
        assert update.website is None
    
    def test_website_validation(self):
        """Test website validation in update request."""
        with pytest.raises(ValidationError):
            ProfileUpdateRequest(
                website="invalid-url"
            )
    
    def test_max_length_validation(self):
        """Test field max length validation."""
        with pytest.raises(ValidationError):
            ProfileUpdateRequest(
                full_name="a" * 101  # Exceeds max length of 100
            )
        
        with pytest.raises(ValidationError):
            ProfileUpdateRequest(
                bio="a" * 501  # Exceeds max length of 500
            )


class TestProfileService:
    """Tests for ProfileService class."""
    
    def test_profile_service_initialization(self):
        """Test ProfileService initialization."""
        service = ProfileService()
        assert service.db is None
        
        mock_db = {"connection": "mock"}
        service_with_db = ProfileService(database_connection=mock_db)
        assert service_with_db.db == mock_db
    
    @pytest.mark.asyncio
    async def test_get_profile_no_database(self):
        """Test get_profile returns None without database."""
        service = ProfileService()
        result = await service.get_profile("user123")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_profile_no_database(self):
        """Test update_profile returns None without database."""
        service = ProfileService()
        update_data = ProfileUpdateRequest(full_name="John Doe")
        result = await service.update_profile("user123", update_data)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_profile_no_database(self):
        """Test delete_profile returns False without database."""
        service = ProfileService()
        result = await service.delete_profile("user123")
        assert result is False


class TestProfileUIRenderer:
    """Tests for ProfileUIRenderer class."""
    
    def test_render_profile_layout(self):
        """Test profile layout rendering."""
        profile = ProfileData(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            full_name="John Doe",
            bio="Software developer",
            phone="+1234567890",
            location="New York, USA",
            website="https://johndoe.com",
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2024, 1, 1)
        )
        
        layout = ProfileUIRenderer.render_profile_layout(profile)
        
        assert layout["layout"] == "profile-page"
        assert layout["theme"] == "modern"
        assert layout["responsive"] is True
        assert len(layout["sections"]) == 4
        
        # Check header section
        header = layout["sections"][0]
        assert header["type"] == "header"
        assert header["data"]["username"] == "johndoe"
        assert header["data"]["full_name"] == "John Doe"
        assert header["data"]["bio"] == "Software developer"
        
        # Check stats section
        stats = layout["sections"][1]
        assert stats["type"] == "stats"
        assert "member_since" in stats["data"]
        assert "last_updated" in stats["data"]
        
        # Check contact info section
        contact = layout["sections"][2]
        assert contact["type"] == "contact_info"
        assert contact["data"]["email"] == "john@example.com"
        assert contact["data"]["phone"] == "+1234567890"
        assert contact["data"]["location"] == "New York, USA"
        assert contact["data"]["website"] == "https://johndoe.com"
        
        # Check actions section
        actions = layout["sections"][3]
        assert actions["type"] == "actions"
        assert actions["data"]["can_edit"] is True
        assert actions["data"]["edit_url"] == "/profile/user123/edit"
    
    def test_render_profile_layout_with_defaults(self):
        """Test profile layout rendering with default values."""
        profile = ProfileData(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2024, 1, 1)
        )
        
        layout = ProfileUIRenderer.render_profile_layout(profile)
        
        header = layout["sections"][0]
        assert header["data"]["avatar"] == "/static/default-avatar.png"
        assert header["data"]["full_name"] == "johndoe"
        assert header["data"]["bio"] == ""
    
    def test_render_edit_form(self):
        """Test profile edit form rendering."""
        profile = ProfileData(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            full_name="John Doe",
            bio="Software developer",
            phone="+1234567890",
            location="New York, USA",
            website="https://johndoe.com",
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2024, 1, 1)
        )
        
        form = ProfileUIRenderer.render_edit_form(profile)
        
        assert form["form"] == "profile-edit"
        assert form["method"] == "POST"
        assert form["action"] == "/api/profile/user123"
        assert len(form["fields"]) == 5
        
        # Check field names
        field_names = [field["name"] for field in form["fields"]]
        assert "full_name" in field_names
        assert "bio" in field_names
        assert "phone" in field_names
        assert "location" in field_names
        assert "website" in field_names
        
        # Check full_name field
        full_name_field = next(f for f in form["fields"] if f["name"] == "full_name")
        assert full_name_field["type"] == "text"
        assert full_name_field["value"] == "John Doe"
        assert full_name_field["maxlength"] == 100
        assert full_name_field["required"] is False
        
        # Check bio field
        bio_field = next(f for f in form["fields"] if f["name"] == "bio")
        assert bio_field["type"] == "textarea"
        assert bio_field["value"] == "Software developer"
        assert bio_field["maxlength"] == 500
        assert bio_field["rows"] == 4
        
        # Check buttons
        assert form["submit_button"]["text"] == "Save Changes"
        assert form["submit_button"]["style"] == "primary"
        assert form["cancel_button"]["text"] == "Cancel"
        assert form["cancel_button"]["url"] == "/profile/user123"
        assert form["cancel_button"]["style"] == "secondary"
    
    def test_render_edit_form_empty_values(self):
        """Test edit form rendering with empty optional values."""
        profile = ProfileData(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2024, 1, 1)
        )
        
        form = ProfileUIRenderer.render_edit_form(profile)
        
        full_name_field = next(f for f in form["fields"] if f["name"] == "full_name")
        assert full_name_field["value"] == ""
        
        bio_field = next(f for f in form["fields"] if f["name"] == "bio")
        assert bio_field["value"] == ""


class TestProfileIntegration:
    """Integration tests for profile components."""
    
    def test_profile_data_to_ui_layout_flow(self):
        """Test complete flow from ProfileData to UI layout."""
        profile = ProfileData(
            user_id="user123",
            username="johndoe",
            email="john@example.com",
            full_name="John Doe",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        layout = ProfileUIRenderer.render_profile_layout(profile)
        form = ProfileUIRenderer.render_edit_form(profile)
        
        assert layout is not None
        assert form is not None
        assert isinstance(layout, dict)
        assert isinstance(form, dict)
    
    def test_update_request_dict_conversion(self):
        """Test ProfileUpdateRequest converts to dict correctly."""
        update = ProfileUpdateRequest(
            full_name="John Doe",
            bio="Updated bio"
        )
        
        data = update.dict(exclude_unset=True)
        assert "full_name" in data
        assert "bio" in data
        assert "phone" not in data
        assert "location" not in data
        assert "website" not in data
