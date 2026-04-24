"""Tests for profile page UI/UX functionality."""

import pytest
from datetime import datetime
from src.auth.profile import (
    ProfileData,
    ProfileSection,
    ProfileService,
    ProfileSettings,
    ProfileTheme,
    ProfileVisibility,
)


class TestProfileData:
    """Test ProfileData model."""

    def test_profile_data_creation(self):
        """Test creating a basic profile."""
        profile = ProfileData(
            user_id="user123",
            username="testuser",
            email="test@example.com",
        )
        assert profile.user_id == "user123"
        assert profile.username == "testuser"
        assert profile.email == "test@example.com"
        assert profile.display_name is None
        assert isinstance(profile.settings, ProfileSettings)

    def test_profile_data_with_optional_fields(self):
        """Test profile with all optional fields."""
        profile = ProfileData(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            display_name="Test User",
            bio="Software developer",
            location="San Francisco",
            website="https://example.com",
        )
        assert profile.display_name == "Test User"
        assert profile.bio == "Software developer"
        assert profile.location == "San Francisco"
        assert profile.website == "https://example.com"

    def test_profile_to_dict_respects_privacy_settings(self):
        """Test that to_dict respects privacy settings."""
        profile = ProfileData(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            joined_date=datetime(2024, 1, 1),
            last_login=datetime(2024, 1, 15),
        )
        profile.settings.show_email = False
        profile.settings.show_last_login = False
        profile.settings.show_join_date = False

        data = profile.to_dict()
        assert data["email"] is None
        assert data["last_login"] is None
        assert data["joined_date"] is None

    def test_profile_to_dict_shows_data_when_enabled(self):
        """Test that to_dict shows data when privacy settings allow."""
        profile = ProfileData(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            joined_date=datetime(2024, 1, 1),
            last_login=datetime(2024, 1, 15),
        )
        profile.settings.show_email = True
        profile.settings.show_last_login = True
        profile.settings.show_join_date = True

        data = profile.to_dict()
        assert data["email"] == "test@example.com"
        assert data["last_login"] is not None
        assert data["joined_date"] is not None

    def test_profile_sections_sorted_by_order(self):
        """Test that sections are sorted by order in to_dict."""
        profile = ProfileData(
            user_id="user123",
            username="testuser",
            email="test@example.com",
        )
        profile.sections = [
            ProfileSection("sec3", "Third", "Content 3", order=3),
            ProfileSection("sec1", "First", "Content 1", order=1),
            ProfileSection("sec2", "Second", "Content 2", order=2),
        ]

        data = profile.to_dict()
        assert len(data["sections"]) == 3
        assert data["sections"][0]["id"] == "sec1"
        assert data["sections"][1]["id"] == "sec2"
        assert data["sections"][2]["id"] == "sec3"

    def test_profile_hides_invisible_sections(self):
        """Test that invisible sections are not included."""
        profile = ProfileData(
            user_id="user123",
            username="testuser",
            email="test@example.com",
        )
        profile.sections = [
            ProfileSection("sec1", "Visible", "Content 1", is_visible=True),
            ProfileSection("sec2", "Hidden", "Content 2", is_visible=False),
        ]

        data = profile.to_dict()
        assert len(data["sections"]) == 1
        assert data["sections"][0]["id"] == "sec1"

    def test_profile_hides_stats_when_activity_disabled(self):
        """Test that stats are hidden when show_activity is False."""
        profile = ProfileData(
            user_id="user123",
            username="testuser",
            email="test@example.com",
        )
        profile.stats = {"posts": 42, "followers": 100}
        profile.settings.show_activity = False

        data = profile.to_dict()
        assert data["stats"] == {}


class TestProfileSettings:
    """Test ProfileSettings model."""

    def test_default_settings(self):
        """Test default profile settings."""
        settings = ProfileSettings()
        assert settings.theme == ProfileTheme.AUTO
        assert settings.visibility == ProfileVisibility.PUBLIC
        assert settings.show_email is False
        assert settings.show_last_login is True
        assert settings.show_join_date is True
        assert settings.show_activity is True
        assert settings.enable_notifications is True

    def test_custom_settings(self):
        """Test creating custom settings."""
        settings = ProfileSettings(
            theme=ProfileTheme.DARK,
            visibility=ProfileVisibility.PRIVATE,
            show_email=True,
        )
        assert settings.theme == ProfileTheme.DARK
        assert settings.visibility == ProfileVisibility.PRIVATE
        assert settings.show_email is True


class TestProfileSection:
    """Test ProfileSection model."""

    def test_section_creation(self):
        """Test creating a profile section."""
        section = ProfileSection(
            section_id="about",
            title="About Me",
            content="I'm a developer",
            icon="user",
            order=1,
        )
        assert section.section_id == "about"
        assert section.title == "About Me"
        assert section.content == "I'm a developer"
        assert section.icon == "user"
        assert section.order == 1
        assert section.is_visible is True


class TestProfileService:
    """Test ProfileService."""

    @pytest.fixture
    def service(self):
        """Create a profile service instance."""
        return ProfileService()

    def test_create_profile(self, service):
        """Test creating a new profile."""
        profile = service.create_profile(
            user_id="user123",
            username="testuser",
            email="test@example.com",
        )
        assert profile.user_id == "user123"
        assert profile.username == "testuser"
        assert profile.email == "test@example.com"
        assert profile.joined_date is not None

    def test_get_profile(self, service):
        """Test retrieving a profile."""
        service.create_profile(
            user_id="user123",
            username="testuser",
            email="test@example.com",
        )
        profile = service.get_profile("user123")
        assert profile is not None
        assert profile.username == "testuser"

    def test_get_nonexistent_profile(self, service):
        """Test retrieving a non-existent profile."""
        profile = service.get_profile("nonexistent")
        assert profile is None

    def test_update_profile(self, service):
        """Test updating profile fields."""
        service.create_profile(
            user_id="user123",
            username="testuser",
            email="test@example.com",
        )
        updated = service.update_profile(
            user_id="user123",
            bio="New bio",
            location="New York",
        )
        assert updated is not None
        assert updated.bio == "New bio"
        assert updated.location == "New York"

    def test_update_nonexistent_profile(self, service):
        """Test updating a non-existent profile."""
        result = service.update_profile("nonexistent", bio="Test")
        assert result is None

    def test_update_settings(self, service):
        """Test updating profile settings."""
        service.create_profile(
            user_id="user123",
            username="testuser",
            email="test@example.com",
        )
        settings = service.update_settings(
            user_id="user123",
            theme=ProfileTheme.DARK,
            show_email=True,
        )
        assert settings is not None
        assert settings.theme == ProfileTheme.DARK
        assert settings.show_email is True

    def test_add_section(self, service):
        """Test adding a section to profile."""
        service.create_profile(
            user_id="user123",
            username="testuser",
            email="test@example.com",
        )
        section = ProfileSection(
            section_id="about",
            title="About",
            content="Test content",
        )
        result = service.add_section("user123", section)
        assert result is True

        profile = service.get_profile("user123")
        assert len(profile.sections) == 1
        assert profile.sections[0].section_id == "about"

    def test_add_section_to_nonexistent_profile(self, service):
        """Test adding section to non-existent profile."""
        section = ProfileSection("test", "Test", "Content")
        result = service.add_section("nonexistent", section)
        assert result is False

    def test_remove_section(self, service):
        """Test removing a section from profile."""
        service.create_profile(
            user_id="user123",
            username="testuser",
            email="test@example.com",
        )
        section = ProfileSection("about", "About", "Content")
        service.add_section("user123", section)

        result = service.remove_section("user123", "about")
        assert result is True

        profile = service.get_profile("user123")
        assert len(profile.sections) == 0

    def test_remove_section_from_nonexistent_profile(self, service):
        """Test removing section from non-existent profile."""
        result = service.remove_section("nonexistent", "test")
        assert result is False

    def test_update_stats(self, service):
        """Test updating profile statistics."""
        service.create_profile(
            user_id="user123",
            username="testuser",
            email="test@example.com",
        )
        result = service.update_stats(
            "user123",
            {"posts": 42, "followers": 100},
        )
        assert result is True

        profile = service.get_profile("user123")
        assert profile.stats["posts"] == 42
        assert profile.stats["followers"] == 100

    def test_update_stats_merges_existing(self, service):
        """Test that updating stats merges with existing stats."""
        service.create_profile(
            user_id="user123",
            username="testuser",
            email="test@example.com",
        )
        service.update_stats("user123", {"posts": 42})
        service.update_stats("user123", {"followers": 100})

        profile = service.get_profile("user123")
        assert profile.stats["posts"] == 42
        assert profile.stats["followers"] == 100

    def test_update_stats_for_nonexistent_profile(self, service):
        """Test updating stats for non-existent profile."""
        result = service.update_stats("nonexistent", {"posts": 1})
        assert result is False
