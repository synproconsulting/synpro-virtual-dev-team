"""Tests for feature brief submission UI."""

from datetime import datetime
import pytest

from src.auth.feature_brief_ui import (
    FeatureBrief,
    FeatureBriefUI,
    FeatureStatus,
    Priority,
)


class TestFeatureBrief:
    """Test cases for FeatureBrief model."""

    def test_validate_success(self):
        """Test validation passes with valid data."""
        brief = FeatureBrief(
            title="New Chat Feature",
            description="This is a detailed description of the new chat feature that we want to build.",
            priority=Priority.HIGH,
            user_id="user123",
            created_at=datetime.utcnow()
        )
        
        errors = brief.validate()
        assert len(errors) == 0

    def test_validate_title_too_short(self):
        """Test validation fails with short title."""
        brief = FeatureBrief(
            title="Hi",
            description="This is a detailed description of the feature.",
            priority=Priority.MEDIUM,
            user_id="user123",
            created_at=datetime.utcnow()
        )
        
        errors = brief.validate()
        assert any("Title must be at least 5 characters" in e for e in errors)

    def test_validate_description_too_short(self):
        """Test validation fails with short description."""
        brief = FeatureBrief(
            title="Valid Title",
            description="Too short",
            priority=Priority.LOW,
            user_id="user123",
            created_at=datetime.utcnow()
        )
        
        errors = brief.validate()
        assert any("Description must be at least 20 characters" in e for e in errors)

    def test_validate_title_too_long(self):
        """Test validation fails with overly long title."""
        brief = FeatureBrief(
            title="A" * 201,
            description="This is a valid description with enough characters.",
            priority=Priority.CRITICAL,
            user_id="user123",
            created_at=datetime.utcnow()
        )
        
        errors = brief.validate()
        assert any("Title must not exceed 200 characters" in e for e in errors)


class TestFeatureBriefUI:
    """Test cases for FeatureBriefUI."""

    def test_create_brief_success(self):
        """Test successful brief creation."""
        ui = FeatureBriefUI()
        
        brief, errors = ui.create_brief(
            title="Implement Dark Mode",
            description="Add dark mode support to improve user experience in low-light environments.",
            priority=Priority.MEDIUM,
            user_id="pm001"
        )
        
        assert brief is not None
        assert len(errors) == 0
        assert brief.brief_id is not None
        assert brief.status == FeatureStatus.DRAFT

    def test_create_brief_validation_failure(self):
        """Test brief creation with invalid data."""
        ui = FeatureBriefUI()
        
        brief, errors = ui.create_brief(
            title="Hi",
            description="Short",
            priority=Priority.LOW,
            user_id="pm001"
        )
        
        assert brief is None
        assert len(errors) > 0

    def test_submit_brief_success(self):
        """Test successful brief submission."""
        ui = FeatureBriefUI()
        
        brief, _ = ui.create_brief(
            title="Export Feature",
            description="Allow users to export their data in multiple formats including CSV and JSON.",
            priority=Priority.HIGH,
            user_id="pm002"
        )
        
        success, message = ui.submit_brief(brief.brief_id)
        
        assert success is True
        assert "successfully" in message.lower()
        assert brief.status == FeatureStatus.SUBMITTED
        assert brief.updated_at is not None

    def test_submit_brief_not_found(self):
        """Test submitting non-existent brief."""
        ui = FeatureBriefUI()
        
        success, message = ui.submit_brief("INVALID-ID")
        
        assert success is False
        assert "not found" in message.lower()

    def test_submit_brief_wrong_status(self):
        """Test submitting already submitted brief."""
        ui = FeatureBriefUI()
        
        brief, _ = ui.create_brief(
            title="Analytics Dashboard",
            description="Create comprehensive analytics dashboard with real-time metrics and insights.",
            priority=Priority.CRITICAL,
            user_id="pm003"
        )
        
        ui.submit_brief(brief.brief_id)
        success, message = ui.submit_brief(brief.brief_id)
        
        assert success is False
        assert "Cannot submit" in message

    def test_get_brief(self):
        """Test retrieving a brief by ID."""
        ui = FeatureBriefUI()
        
        created_brief, _ = ui.create_brief(
            title="Search Enhancement",
            description="Improve search functionality with fuzzy matching and advanced filters.",
            priority=Priority.MEDIUM,
            user_id="pm004"
        )
        
        retrieved_brief = ui.get_brief(created_brief.brief_id)
        
        assert retrieved_brief is not None
        assert retrieved_brief.title == "Search Enhancement"

    def test_list_briefs_all(self):
        """Test listing all briefs."""
        ui = FeatureBriefUI()
        
        ui.create_brief("Feature 1", "A" * 30, Priority.LOW, "user1")
        ui.create_brief("Feature 2", "B" * 30, Priority.HIGH, "user2")
        
        briefs = ui.list_briefs()
        
        assert len(briefs) == 2

    def test_list_briefs_filtered(self):
        """Test listing briefs filtered by user."""
        ui = FeatureBriefUI()
        
        ui.create_brief("Feature 1", "A" * 30, Priority.LOW, "user1")
        ui.create_brief("Feature 2", "B" * 30, Priority.HIGH, "user2")
        ui.create_brief("Feature 3", "C" * 30, Priority.MEDIUM, "user1")
        
        briefs = ui.list_briefs(user_id="user1")
        
        assert len(briefs) == 2
        assert all(b.user_id == "user1" for b in briefs)
