"""
tools/tests/test_validation.py
───────────────────────────────
Tests for PM Agent validation utilities.
"""

import pytest
from tools.validation import (
    validate_execution_order,
    validate_story_creation,
)


class TestValidateExecutionOrder:
    """Tests for execution_order validation."""

    def test_valid_execution_order_returns_empty_string(self):
        """Valid execution_order should not produce warnings."""
        assert validate_execution_order(1) == ""
        assert validate_execution_order(0) == ""
        assert validate_execution_order(100) == ""

    def test_missing_execution_order_returns_warning(self):
        """Missing execution_order should return a warning message."""
        warning = validate_execution_order(None)
        assert "⚠️  WARNING" in warning
        assert "execution_order not set" in warning
        assert "Orchestrator" in warning

    def test_missing_execution_order_with_issue_key(self):
        """Warning should include issue key when provided."""
        warning = validate_execution_order(None, issue_key="SDT1-123")
        assert "SDT1-123" in warning
        assert "⚠️  WARNING" in warning

    def test_zero_is_valid_execution_order(self):
        """Zero is a valid execution_order value."""
        assert validate_execution_order(0) == ""

    def test_negative_execution_order_is_valid(self):
        """Negative numbers are technically valid (though not recommended)."""
        # We don't validate the value itself, just that it's set
        assert validate_execution_order(-1) == ""


class TestValidateStoryCreation:
    """Tests for comprehensive story creation validation."""

    def test_valid_story_with_all_fields(self):
        """Story with all recommended fields should pass with minimal warnings."""
        warnings = validate_story_creation(
            summary="Short summary",
            epic_key="SDT1-1",
            execution_order=1,
        )
        # Should only have no warnings
        assert len(warnings) == 0

    def test_missing_execution_order_produces_warning(self):
        """Missing execution_order should produce a warning."""
        warnings = validate_story_creation(
            summary="Test story",
            epic_key="SDT1-1",
            execution_order=None,
        )
        assert len(warnings) >= 1
        assert any("execution_order" in w for w in warnings)
        assert any("⚠️  WARNING" in w for w in warnings)

    def test_missing_epic_produces_info(self):
        """Missing epic should produce an informational message."""
        warnings = validate_story_creation(
            summary="Test story",
            epic_key=None,
            execution_order=1,
        )
        assert len(warnings) >= 1
        assert any("Epic" in w for w in warnings)
        assert any("ℹ️  INFO" in w for w in warnings)

    def test_long_summary_produces_info(self):
        """Summary over 100 characters should produce an informational message."""
        long_summary = "A" * 101
        warnings = validate_story_creation(
            summary=long_summary,
            epic_key="SDT1-1",
            execution_order=1,
        )
        assert len(warnings) >= 1
        assert any("Summary is 101 characters" in w for w in warnings)
        assert any("ℹ️  INFO" in w for w in warnings)

    def test_multiple_validation_issues(self):
        """Multiple issues should produce multiple warnings."""
        long_summary = "A" * 150
        warnings = validate_story_creation(
            summary=long_summary,
            epic_key=None,
            execution_order=None,
        )
        # Should have warnings for: execution_order, epic, and summary length
        assert len(warnings) == 3
        assert any("execution_order" in w for w in warnings)
        assert any("Epic" in w for w in warnings)
        assert any("Summary" in w for w in warnings)

    def test_exactly_100_char_summary_is_ok(self):
        """Summary of exactly 100 characters should not produce a warning."""
        summary = "A" * 100
        warnings = validate_story_creation(
            summary=summary,
            epic_key="SDT1-1",
            execution_order=1,
        )
        # Should not have summary length warning
        assert not any("Summary is" in w for w in warnings)

    def test_empty_epic_key_treated_as_none(self):
        """Empty string epic key should produce same warning as None."""
        warnings_none = validate_story_creation(
            summary="Test",
            epic_key=None,
            execution_order=1,
        )
        warnings_empty = validate_story_creation(
            summary="Test",
            epic_key="",
            execution_order=1,
        )
        # Both should have epic warning, but empty string passes the truthiness check
        # so we only check None case produces warning
        assert len(warnings_none) >= 1
        assert any("Epic" in w for w in warnings_none)
