"""
tools/test_pm_validation.py
───────────────────────────
Tests for PM Agent validation utilities.
"""

import pytest
from unittest.mock import Mock, MagicMock
from tools.pm_validation import (
    PMValidator,
    ValidationWarning,
    validate_story_creation,
    get_validator,
)


class TestValidationWarning:
    """Tests for ValidationWarning class."""
    
    def test_warning_without_issue_key(self):
        """Test warning formatting without issue key."""
        warning = ValidationWarning("ERROR", "Something went wrong")
        assert str(warning) == "[ERROR] Something went wrong"
    
    def test_warning_with_issue_key(self):
        """Test warning formatting with issue key."""
        warning = ValidationWarning("WARNING", "Missing points", "SDT1-42")
        assert str(warning) == "[WARNING] [SDT1-42] Missing points"
    
    def test_warning_properties(self):
        """Test warning properties are set correctly."""
        warning = ValidationWarning("INFO", "Test message", "KEY-1")
        assert warning.severity == "INFO"
        assert warning.message == "Test message"
        assert warning.issue_key == "KEY-1"


class TestPMValidator:
    """Tests for PMValidator class."""
    
    def test_clear_warnings(self):
        """Test clearing accumulated warnings."""
        validator = PMValidator()
        validator.add_warning("ERROR", "Test error")
        assert len(validator.get_warnings()) == 1
        
        validator.clear_warnings()
        assert len(validator.get_warnings()) == 0
    
    def test_add_warning(self):
        """Test adding warnings."""
        validator = PMValidator()
        validator.add_warning("WARNING", "Test warning", "SDT1-1")
        
        warnings = validator.get_warnings()
        assert len(warnings) == 1
        assert warnings[0].severity == "WARNING"
        assert warnings[0].message == "Test warning"
        assert warnings[0].issue_key == "SDT1-1"
    
    def test_has_errors(self):
        """Test error detection."""
        validator = PMValidator()
        assert not validator.has_errors()
        
        validator.add_warning("WARNING", "Just a warning")
        assert not validator.has_errors()
        
        validator.add_warning("ERROR", "Critical error")
        assert validator.has_errors()
    
    def test_format_warnings_empty(self):
        """Test formatting with no warnings."""
        validator = PMValidator()
        result = validator.format_warnings()
        assert result == "No validation warnings."
    
    def test_format_warnings_with_content(self):
        """Test formatting with warnings."""
        validator = PMValidator()
        validator.add_warning("ERROR", "Error 1", "KEY-1")
        validator.add_warning("WARNING", "Warning 1")
        
        result = validator.format_warnings()
        assert "Validation Warnings:" in result
        assert "[ERROR] [KEY-1] Error 1" in result
        assert "[WARNING] Warning 1" in result


class TestStoryValidation:
    """Tests for story creation validation."""
    
    def test_valid_story_passes(self):
        """Test that a well-formed story passes validation."""
        validator = PMValidator()
        validator.clear_warnings()
        
        result = validator.validate_story_creation(
            summary="Implement user login",
            description="As a user, I want to log in so that I can access my account. Acceptance criteria: 1. User can enter credentials. 2. Valid login redirects to dashboard. 3. Invalid login shows error.",
            epic_key="SDT1-1",
            story_points=3,
            priority="High",
            execution_order=1,
        )
        
        assert result is True
        assert not validator.has_errors()
        assert len(validator.get_warnings()) == 0
    
    def test_missing_execution_order_is_critical(self):
        """Test that missing execution_order is flagged as critical error."""
        validator = PMValidator()
        validator.clear_warnings()
        
        result = validator.validate_story_creation(
            summary="Test story",
            description="A test story with good content for testing purposes.",
            epic_key="SDT1-1",
            story_points=3,
            execution_order=None,  # Missing!
        )
        
        assert result is False
        assert validator.has_errors()
        
        warnings = validator.get_warnings()
        error_messages = [w.message for w in warnings if w.severity == "ERROR"]
        assert any("execution_order" in msg for msg in error_messages)
        assert any("Orchestrator" in msg for msg in error_messages)
    
    def test_invalid_execution_order_negative(self):
        """Test that negative execution_order is invalid."""
        validator = PMValidator()
        validator.clear_warnings()
        
        result = validator.validate_story_creation(
            summary="Test story",
            description="A test story with good content.",
            execution_order=0,
        )
        
        assert result is False
        assert validator.has_errors()
    
    def test_invalid_execution_order_zero(self):
        """Test that zero execution_order is invalid."""
        validator = PMValidator()
        validator.clear_warnings()
        
        result = validator.validate_story_creation(
            summary="Test story",
            description="A test story with good content.",
            execution_order=0,
        )
        
        assert result is False
        assert validator.has_errors()
    
    def test_missing_epic_warns(self):
        """Test that missing epic link generates warning."""
        validator = PMValidator()
        validator.clear_warnings()
        
        validator.validate_story_creation(
            summary="Test story",
            description="A test story with good content.",
            epic_key=None,  # Missing!
            story_points=3,
            execution_order=1,
        )
        
        warnings = validator.get_warnings()
        warning_messages = [w.message for w in warnings if w.severity == "WARNING"]
        assert any("Epic" in msg for msg in warning_messages)
    
    def test_missing_story_points_warns(self):
        """Test that missing story points generates warning."""
        validator = PMValidator()
        validator.clear_warnings()
        
        validator.validate_story_creation(
            summary="Test story",
            description="A test story with good content.",
            epic_key="SDT1-1",
            story_points=None,  # Missing!
            execution_order=1,
        )
        
        warnings = validator.get_warnings()
        warning_messages = [w.message for w in warnings if w.severity == "WARNING"]
        assert any("story points" in msg.lower() for msg in warning_messages)
    
    def test_high_story_points_warns(self):
        """Test that story points > 8 generates warning."""
        validator = PMValidator()
        validator.clear_warnings()
        
        validator.validate_story_creation(
            summary="Test story",
            description="A test story with good content.",
            epic_key="SDT1-1",
            story_points=13,  # Too high!
            execution_order=1,
        )
        
        warnings = validator.get_warnings()
        warning_messages = [w.message for w in warnings if w.severity == "WARNING"]
        assert any("exceed" in msg.lower() or "splitting" in msg.lower() for msg in warning_messages)
    
    def test_long_summary_warns(self):
        """Test that long summary generates warning."""
        validator = PMValidator()
        validator.clear_warnings()
        
        long_summary = "A" * 150  # Over 100 chars
        
        validator.validate_story_creation(
            summary=long_summary,
            description="A test story with good content.",
            epic_key="SDT1-1",
            story_points=3,
            execution_order=1,
        )
        
        warnings = validator.get_warnings()
        warning_messages = [w.message for w in warnings if w.severity == "WARNING"]
        assert any("Summary" in msg and "characters" in msg for msg in warning_messages)
    
    def test_short_description_warns(self):
        """Test that short/missing description generates warning."""
        validator = PMValidator()
        validator.clear_warnings()
        
        validator.validate_story_creation(
            summary="Test story",
            description="Short",  # Too short!
            epic_key="SDT1-1",
            story_points=3,
            execution_order=1,
        )
        
        warnings = validator.get_warnings()
        warning_messages = [w.message for w in warnings if w.severity == "WARNING"]
        assert any("description" in msg.lower() for msg in warning_messages)
    
    def test_empty_description_warns(self):
        """Test that empty description generates warning."""
        validator = PMValidator()
        validator.clear_warnings()
        
        validator.validate_story_creation(
            summary="Test story",
            description="",  # Empty!
            epic_key="SDT1-1",
            story_points=3,
            execution_order=1,
        )
        
        warnings = validator.get_warnings()
        warning_messages = [w.message for w in warnings if w.severity == "WARNING"]
        assert any("description" in msg.lower() for msg in warning_messages)


class TestBacklogValidation:
    """Tests for backlog health validation."""
    
    def test_empty_backlog(self):
        """Test validation of empty backlog."""
        validator = PMValidator()
        validator.clear_warnings()
        
        results = validator.validate_backlog_health([])
        
        assert results["statistics"]["total_stories"] == 0
        assert results["statistics"]["missing_execution_order"] == 0
    
    def test_story_without_execution_order(self):
        """Test that story without execution_order is flagged."""
        validator = PMValidator()
        validator.clear_warnings()
        
        # Mock issue
        issue = Mock()
        issue.key = "SDT1-42"
        issue.fields = Mock()
        issue.fields.issuetype = Mock()
        issue.fields.issuetype.name = "Story"
        issue.fields.summary = "Test story"
        issue.fields.customfield_10071 = None  # Missing execution_order!
        issue.fields.customfield_10014 = None
        issue.fields.parent = Mock()
        issue.fields.parent.key = "SDT1-1"
        issue.fields.customfield_10016 = 3
        issue.fields.description = "A good description with enough content."
        
        results = validator.validate_backlog_health([issue])
        
        assert results["statistics"]["total_stories"] == 1
        assert results["statistics"]["missing_execution_order"] == 1
        assert "SDT1-42" in results["issues_missing_execution_order"]
        assert validator.has_errors()
    
    def test_story_with_all_fields(self):
        """Test that well-formed story passes validation."""
        validator = PMValidator()
        validator.clear_warnings()
        
        # Mock issue
        issue = Mock()
        issue.key = "SDT1-42"
        issue.fields = Mock()
        issue.fields.issuetype = Mock()
        issue.fields.issuetype.name = "Story"
        issue.fields.summary = "Test story"
        issue.fields.customfield_10071 = 1  # Has execution_order
        issue.fields.customfield_10014 = None
        issue.fields.parent = Mock()
        issue.fields.parent.key = "SDT1-1"
        issue.fields.customfield_10016 = 3
        issue.fields.description = "A good description with enough content."
        
        results = validator.validate_backlog_health([issue])
        
        assert results["statistics"]["total_stories"] == 1
        assert results["statistics"]["missing_execution_order"] == 0
        assert not validator.has_errors()
    
    def test_non_story_issues_ignored(self):
        """Test that non-story issue types are ignored."""
        validator = PMValidator()
        validator.clear_warnings()
        
        # Mock epic (not a story)
        epic = Mock()
        epic.key = "SDT1-1"
        epic.fields = Mock()
        epic.fields.issuetype = Mock()
        epic.fields.issuetype.name = "Epic"
        
        results = validator.validate_backlog_health([epic])
        
        assert results["statistics"]["total_stories"] == 0
    
    def test_multiple_issues_statistics(self):
        """Test statistics for multiple issues with various problems."""
        validator = PMValidator()
        validator.clear_warnings()
        
        # Issue 1: Missing execution_order
        issue1 = Mock()
        issue1.key = "SDT1-1"
        issue1.fields = Mock()
        issue1.fields.issuetype = Mock()
        issue1.fields.issuetype.name = "Story"
        issue1.fields.customfield_10071 = None
        issue1.fields.customfield_10014 = None
        issue1.fields.parent = None
        issue1.fields.customfield_10016 = None
        issue1.fields.description = "Short"
        
        # Issue 2: All good
        issue2 = Mock()
        issue2.key = "SDT1-2"
        issue2.fields = Mock()
        issue2.fields.issuetype = Mock()
        issue2.fields.issuetype.name = "Story"
        issue2.fields.customfield_10071 = 1
        issue2.fields.customfield_10014 = None
        issue2.fields.parent = Mock()
        issue2.fields.parent.key = "SDT1-10"
        issue2.fields.customfield_10016 = 5
        issue2.fields.description = "A good description with plenty of content."
        
        # Issue 3: Over-estimated
        issue3 = Mock()
        issue3.key = "SDT1-3"
        issue3.fields = Mock()
        issue3.fields.issuetype = Mock()
        issue3.fields.issuetype.name = "Story"
        issue3.fields.customfield_10071 = 2
        issue3.fields.customfield_10014 = None
        issue3.fields.parent = Mock()
        issue3.fields.parent.key = "SDT1-10"
        issue3.fields.customfield_10016 = 13  # Over 8
        issue3.fields.description = "A good description."
        
        results = validator.validate_backlog_health([issue1, issue2, issue3])
        
        stats = results["statistics"]
        assert stats["total_stories"] == 3
        assert stats["missing_execution_order"] == 1
        assert stats["missing_epic"] == 1
        assert stats["missing_points"] == 1
        assert stats["over_estimated"] == 1


class TestConvenienceFunction:
    """Tests for convenience function."""
    
    def test_validate_story_creation_function(self):
        """Test the convenience function."""
        result = validate_story_creation(
            summary="Test",
            description="A good description.",
            execution_order=1,
        )
        
        assert "Validation" in result
    
    def test_validate_story_creation_with_errors(self):
        """Test convenience function with errors."""
        result = validate_story_creation(
            summary="Test",
            description="Good",
            execution_order=None,  # Missing!
        )
        
        assert "FAILED" in result
        assert "execution_order" in result
    
    def test_validate_story_creation_with_warnings(self):
        """Test convenience function with warnings only."""
        result = validate_story_creation(
            summary="Test",
            description="Good desc",
            execution_order=1,
            story_points=None,  # Missing - warning only
        )
        
        assert "WARNINGS" in result or "passed" in result.lower()
    
    def test_validate_story_creation_success(self):
        """Test convenience function with no issues."""
        result = validate_story_creation(
            summary="Test",
            description="A comprehensive description with all the details.",
            epic_key="SDT1-1",
            story_points=3,
            execution_order=1,
        )
        
        assert "passed" in result.lower() or "✅" in result


class TestGlobalValidator:
    """Tests for global validator singleton."""
    
    def test_get_validator_returns_same_instance(self):
        """Test that get_validator returns the same instance."""
        v1 = get_validator()
        v2 = get_validator()
        assert v1 is v2
    
    def test_global_validator_is_cleared_between_calls(self):
        """Test that validator can be cleared for independent validations."""
        validator = get_validator()
        
        # First validation
        validator.clear_warnings()
        validator.add_warning("ERROR", "Test 1")
        assert len(validator.get_warnings()) == 1
        
        # Clear for next validation
        validator.clear_warnings()
        assert len(validator.get_warnings()) == 0
        
        # Second validation
        validator.add_warning("WARNING", "Test 2")
        assert len(validator.get_warnings()) == 1
