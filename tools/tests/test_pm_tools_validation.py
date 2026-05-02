"""
tools/tests/test_pm_tools_validation.py
────────────────────────────────────────
Integration tests for PM tools validation.
Tests that validation warnings are properly surfaced through the tool layer.
"""

import pytest
from unittest.mock import Mock, patch
from tools.pm_tools import CreateStoryTool


class TestCreateStoryToolValidation:
    """Tests for validation warnings in CreateStoryTool."""

    @patch('tools.pm_tools.jira')
    def test_story_with_execution_order_no_warning(self, mock_jira):
        """Story with execution_order should not produce a warning."""
        # Setup mock
        mock_jira.create_story.return_value = {"key": "SDT1-123", "id": "12345"}
        
        # Create tool and run
        tool = CreateStoryTool()
        result = tool._run(
            summary="Test story",
            description="Test description",
            epic_key="SDT1-1",
            story_points=5,
            priority="High",
            execution_order=1,
        )
        
        # Verify result doesn't contain warnings
        assert "SDT1-123" in result
        assert "⚠️  WARNING" not in result
        assert "execution order: 1" in result

    @patch('tools.pm_tools.jira')
    def test_story_without_execution_order_produces_warning(self, mock_jira):
        """Story without execution_order should produce a warning in the response."""
        # Setup mock
        mock_jira.create_story.return_value = {"key": "SDT1-124", "id": "12346"}
        
        # Create tool and run
        tool = CreateStoryTool()
        result = tool._run(
            summary="Test story without order",
            description="Test description",
            epic_key="SDT1-1",
            story_points=3,
            priority="Medium",
            execution_order=None,
        )
        
        # Verify result contains warning
        assert "SDT1-124" in result
        assert "⚠️  WARNING" in result
        assert "execution_order not set" in result
        assert "Orchestrator" in result

    @patch('tools.pm_tools.jira')
    def test_story_without_epic_produces_info(self, mock_jira):
        """Story without epic should produce an informational message."""
        # Setup mock
        mock_jira.create_story.return_value = {"key": "SDT1-125", "id": "12347"}
        
        # Create tool and run
        tool = CreateStoryTool()
        result = tool._run(
            summary="Test story",
            description="Test description",
            epic_key=None,
            story_points=2,
            priority="Low",
            execution_order=5,
        )
        
        # Verify result contains info about epic
        assert "SDT1-125" in result
        assert "ℹ️  INFO" in result
        assert "Epic" in result

    @patch('tools.pm_tools.jira')
    def test_story_with_long_summary_produces_info(self, mock_jira):
        """Story with long summary should produce an informational message."""
        # Setup mock
        mock_jira.create_story.return_value = {"key": "SDT1-126", "id": "12348"}
        
        # Create tool and run
        long_summary = "A" * 120
        tool = CreateStoryTool()
        result = tool._run(
            summary=long_summary,
            description="Test description",
            epic_key="SDT1-1",
            story_points=8,
            priority="High",
            execution_order=2,
        )
        
        # Verify result contains info about summary length
        assert "SDT1-126" in result
        assert "ℹ️  INFO" in result
        assert "120 characters" in result

    @patch('tools.pm_tools.jira')
    def test_story_with_multiple_issues_shows_all_warnings(self, mock_jira):
        """Story with multiple issues should show all warnings."""
        # Setup mock
        mock_jira.create_story.return_value = {"key": "SDT1-127", "id": "12349"}
        
        # Create tool and run with multiple issues
        long_summary = "B" * 150
        tool = CreateStoryTool()
        result = tool._run(
            summary=long_summary,
            description="Test description",
            epic_key=None,
            story_points=13,
            priority="Highest",
            execution_order=None,
        )
        
        # Verify result contains multiple warnings
        assert "SDT1-127" in result
        assert "⚠️  WARNING" in result
        assert "execution_order" in result
        assert "ℹ️  INFO" in result
        assert "Epic" in result
        assert "150 characters" in result

    @patch('tools.pm_tools.jira')
    def test_jira_create_story_called_with_correct_params(self, mock_jira):
        """Verify that validation doesn't interfere with Jira API calls."""
        # Setup mock
        mock_jira.create_story.return_value = {"key": "SDT1-128", "id": "12350"}
        
        # Create tool and run
        tool = CreateStoryTool()
        tool._run(
            summary="Test story",
            description="Test desc",
            epic_key="SDT1-5",
            story_points=3,
            priority="Medium",
            execution_order=7,
        )
        
        # Verify create_story was called with correct parameters
        mock_jira.create_story.assert_called_once_with(
            "Test story",
            "Test desc",
            "SDT1-5",
            3,
            "Medium",
            7,
        )

    @patch('tools.pm_tools.jira')
    def test_zero_execution_order_is_valid(self, mock_jira):
        """Execution order of 0 should be treated as valid."""
        # Setup mock
        mock_jira.create_story.return_value = {"key": "SDT1-129", "id": "12351"}
        
        # Create tool and run
        tool = CreateStoryTool()
        result = tool._run(
            summary="Test story",
            description="Test description",
            epic_key="SDT1-1",
            story_points=1,
            priority="High",
            execution_order=0,
        )
        
        # Verify no warning for execution_order
        assert "SDT1-129" in result
        assert "execution order: 0" in result
        # Should not have execution_order warning (but may have others like Epic)
        assert "execution_order not set" not in result
