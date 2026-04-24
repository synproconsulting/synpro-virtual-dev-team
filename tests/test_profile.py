"""Tests for profile management module."""

import pytest
from datetime import datetime
from src.auth.profile import ProfileManager, UserProfile


class TestUserProfile:
    """Test cases for UserProfile dataclass."""
    
    def test_user_profile_creation(self):
        """Test creating a UserProfile instance."""
        profile = UserProfile(
            user_id="user123",
            email="test@example.com",
            display_name="Test User"
        )
        
        assert profile.user_id == "user123"
        assert profile.email == "test@example.com"
        assert profile.display_name == "Test User"
        assert profile.avatar_url is None
        assert isinstance(profile.created_at, datetime)
        assert isinstance(profile.updated_at, datetime)
    
    def test_user_profile_with_avatar(self):
        """Test creating a UserProfile with avatar URL."""
        avatar_url = "https://example.com/avatar.png"
        profile = UserProfile(
            user_id="user123",
            email="test@example.com",
            display_name="Test User",
            avatar_url=avatar_url
        )
        
        assert profile.avatar_url == avatar_url


class TestProfileManager:
    """Test cases for ProfileManager class."""
    
    @pytest.fixture
    def manager(self):
        """Create a fresh ProfileManager instance for each test."""
        return ProfileManager()
    
    @pytest.fixture
    def sample_profile(self, manager):
        """Create a sample profile for testing."""
        return manager.create_profile(
            user_id="user123",
            email="test@example.com",
            display_name="Test User"
        )
    
    def test_create_profile(self, manager):
        """Test creating a new profile."""
        profile = manager.create_profile(
            user_id="user123",
            email="test@example.com",
            display_name="Test User"
        )
        
        assert profile.user_id == "user123"
        assert profile.email == "test@example.com"
        assert profile.display_name == "Test User"
        assert profile.avatar_url is not None
        assert "gravatar.com" in profile.avatar_url
    
    def test_create_profile_without_display_name(self, manager):
        """Test creating a profile without display name defaults to email."""
        profile = manager.create_profile(
            user_id="user123",
            email="test@example.com"
        )
        
        assert profile.display_name == "test@example.com"
    
    def test_create_duplicate_profile_raises_error(self, manager, sample_profile):
        """Test that creating a duplicate profile raises ValueError."""
        with pytest.raises(ValueError, match="Profile already exists"):
            manager.create_profile(
                user_id="user123",
                email="another@example.com"
            )
    
    def test_get_profile(self, manager, sample_profile):
        """Test retrieving an existing profile."""
        profile = manager.get_profile("user123")
        
        assert profile is not None
        assert profile.user_id == "user123"
        assert profile.email == "test@example.com"
    
    def test_get_nonexistent_profile(self, manager):
        """Test retrieving a non-existent profile returns None."""
        profile = manager.get_profile("nonexistent")
        assert profile is None
    
    def test_update_display_name(self, manager, sample_profile):
        """Test updating a user's display name."""
        original_updated_at = sample_profile.updated_at
        
        updated_profile = manager.update_display_name("user123", "New Name")
        
        assert updated_profile.display_name == "New Name"
        assert updated_profile.updated_at > original_updated_at
    
    def test_update_display_name_strips_whitespace(self, manager, sample_profile):
        """Test that updating display name strips whitespace."""
        updated_profile = manager.update_display_name("user123", "  Spaced Name  ")
        assert updated_profile.display_name == "Spaced Name"
    
    def test_update_display_name_empty_raises_error(self, manager, sample_profile):
        """Test that empty display name raises ValueError."""
        with pytest.raises(ValueError, match="Display name cannot be empty"):
            manager.update_display_name("user123", "")
        
        with pytest.raises(ValueError, match="Display name cannot be empty"):
            manager.update_display_name("user123", "   ")
    
    def test_update_display_name_nonexistent_user_raises_error(self, manager):
        """Test updating display name for non-existent user raises ValueError."""
        with pytest.raises(ValueError, match="Profile not found"):
            manager.update_display_name("nonexistent", "New Name")
    
    def test_get_avatar_url(self, manager, sample_profile):
        """Test retrieving avatar URL for a user."""
        avatar_url = manager.get_avatar_url("user123")
        
        assert avatar_url is not None
        assert "gravatar.com" in avatar_url
    
    def test_get_avatar_url_nonexistent_user(self, manager):
        """Test getting avatar URL for non-existent user returns None."""
        avatar_url = manager.get_avatar_url("nonexistent")
        assert avatar_url is None
    
    def test_update_avatar_url(self, manager, sample_profile):
        """Test updating avatar URL."""
        new_url = "https://example.com/new-avatar.png"
        updated_profile = manager.update_avatar_url("user123", new_url)
        
        assert updated_profile.avatar_url == new_url
        assert manager.get_avatar_url("user123") == new_url
    
    def test_update_avatar_url_nonexistent_user_raises_error(self, manager):
        """Test updating avatar URL for non-existent user raises ValueError."""
        with pytest.raises(ValueError, match="Profile not found"):
            manager.update_avatar_url("nonexistent", "https://example.com/avatar.png")
    
    def test_generate_gravatar_url(self, manager):
        """Test Gravatar URL generation."""
        url = manager._generate_gravatar_url("test@example.com")
        
        assert url.startswith("https://www.gravatar.com/avatar/")
        assert "s=200" in url
        assert "d=identicon" in url
    
    def test_generate_gravatar_url_case_insensitive(self, manager):
        """Test that Gravatar URL generation is case-insensitive."""
        url1 = manager._generate_gravatar_url("Test@Example.COM")
        url2 = manager._generate_gravatar_url("test@example.com")
        
        assert url1 == url2
    
    def test_delete_profile(self, manager, sample_profile):
        """Test deleting a profile."""
        result = manager.delete_profile("user123")
        
        assert result is True
        assert manager.get_profile("user123") is None
    
    def test_delete_nonexistent_profile(self, manager):
        """Test deleting a non-existent profile returns False."""
        result = manager.delete_profile("nonexistent")
        assert result is False
    
    def test_list_profiles(self, manager):
        """Test listing all profiles."""
        manager.create_profile("user1", "user1@example.com", "User 1")
        manager.create_profile("user2", "user2@example.com", "User 2")
        manager.create_profile("user3", "user3@example.com", "User 3")
        
        profiles = manager.list_profiles()
        
        assert len(profiles) == 3
        user_ids = {p.user_id for p in profiles}
        assert user_ids == {"user1", "user2", "user3"}
    
    def test_list_profiles_empty(self, manager):
        """Test listing profiles when none exist."""
        profiles = manager.list_profiles()
        assert profiles == []
    
    def test_profile_timestamps_update(self, manager, sample_profile):
        """Test that profile timestamps are properly updated."""
        original_created = sample_profile.created_at
        original_updated = sample_profile.updated_at
        
        # Update display name
        manager.update_display_name("user123", "Updated Name")
        updated_profile = manager.get_profile("user123")
        
        assert updated_profile.created_at == original_created
        assert updated_profile.updated_at > original_updated
