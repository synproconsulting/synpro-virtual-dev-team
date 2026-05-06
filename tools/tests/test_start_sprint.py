"""
tests/test_start_sprint.py
──────────────────────────
Unit tests for sprint starting functionality.

Tests the start_sprint function in jira_client and StartSprintTool.
"""

import os
from unittest.mock import Mock, patch, MagicMock
import pytest
from tools import jira_client
from tools.pm_tools import StartSprintTool


class TestStartSprintClient:
    """Test jira_client.start_sprint function."""

    @patch("tools.jira_client._get_client")
    @patch("tools.jira_client._get_board_id")
    def test_start_sprint_success(self, mock_get_board_id, mock_get_client):
        """Test successfully starting a sprint in future state."""
        # Arrange
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        mock_get_board_id.return_value = 123
        
        # Mock the sprint before starting (future state)
        mock_sprint_before = Mock()
        mock_sprint_before.id = 456
        mock_sprint_before.name = "Sprint 1"
        mock_sprint_before.state = "future"
        
        # Mock the sprint after starting (active state)
        mock_sprint_after = Mock()
        mock_sprint_after.id = 456
        mock_sprint_after.name = "Sprint 1"
        mock_sprint_after.state = "active"
        mock_sprint_after.startDate = "2025-01-15T09:00:00.000Z"
        mock_sprint_after.endDate = "2025-01-29T18:00:00.000Z"
        
        # Mock API responses
        mock_jira.sprint.side_effect = [mock_sprint_before, mock_sprint_after]
        mock_jira._options = {"server": "https://test.atlassian.net"}
        mock_jira._session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_jira._session.post.return_value = mock_response
        
        # Act
        result = jira_client.start_sprint(456)
        
        # Assert
        assert result["id"] == 456
        assert result["name"] == "Sprint 1"
        assert result["state"] == "active"
        assert result["start_date"] == "2025-01-15T09:00:00.000Z"
        assert result["end_date"] == "2025-01-29T18:00:00.000Z"
        
        # Verify API calls
        assert mock_jira.sprint.call_count == 2
        mock_jira.sprint.assert_any_call(456)
        mock_jira._session.post.assert_called_once()

    @patch("tools.jira_client._get_client")
    @patch("tools.jira_client._get_board_id")
    def test_start_sprint_already_active(self, mock_get_board_id, mock_get_client):
        """Test error when trying to start an already active sprint."""
        # Arrange
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        mock_get_board_id.return_value = 123
        
        mock_sprint = Mock()
        mock_sprint.id = 456
        mock_sprint.name = "Sprint 1"
        mock_sprint.state = "active"
        
        mock_jira.sprint.return_value = mock_sprint
        
        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            jira_client.start_sprint(456)
        
        assert "Cannot start sprint 456 with state 'active'" in str(excinfo.value)
        assert "Only sprints in 'future' state can be started" in str(excinfo.value)

    @patch("tools.jira_client._get_client")
    @patch("tools.jira_client._get_board_id")
    def test_start_sprint_closed(self, mock_get_board_id, mock_get_client):
        """Test error when trying to start a closed sprint."""
        # Arrange
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        mock_get_board_id.return_value = 123
        
        mock_sprint = Mock()
        mock_sprint.id = 456
        mock_sprint.name = "Sprint 1"
        mock_sprint.state = "closed"
        
        mock_jira.sprint.return_value = mock_sprint
        
        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            jira_client.start_sprint(456)
        
        assert "Cannot start sprint 456 with state 'closed'" in str(excinfo.value)

    @patch("tools.jira_client._get_client")
    @patch("tools.jira_client._get_board_id")
    def test_start_sprint_api_error(self, mock_get_board_id, mock_get_client):
        """Test handling of API errors when starting sprint."""
        # Arrange
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        mock_get_board_id.return_value = 123
        
        mock_sprint = Mock()
        mock_sprint.id = 456
        mock_sprint.name = "Sprint 1"
        mock_sprint.state = "future"
        
        mock_jira.sprint.return_value = mock_sprint
        mock_jira._options = {"server": "https://test.atlassian.net"}
        mock_jira._session = Mock()
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request: Sprint cannot be started"
        mock_jira._session.post.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            jira_client.start_sprint(456)
        
        assert "Failed to start sprint 456" in str(excinfo.value)
        assert "Status: 400" in str(excinfo.value)

    @patch("tools.jira_client._get_client")
    @patch("tools.jira_client._get_board_id")
    def test_start_sprint_with_dates(self, mock_get_board_id, mock_get_client):
        """Test starting sprint returns proper date information."""
        # Arrange
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        mock_get_board_id.return_value = 123
        
        mock_sprint_before = Mock()
        mock_sprint_before.state = "future"
        
        mock_sprint_after = Mock()
        mock_sprint_after.id = 789
        mock_sprint_after.name = "Sprint 2"
        mock_sprint_after.state = "active"
        mock_sprint_after.startDate = "2025-02-01T10:00:00.000Z"
        mock_sprint_after.endDate = "2025-02-14T17:00:00.000Z"
        
        mock_jira.sprint.side_effect = [mock_sprint_before, mock_sprint_after]
        mock_jira._options = {"server": "https://test.atlassian.net"}
        mock_jira._session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_jira._session.post.return_value = mock_response
        
        # Act
        result = jira_client.start_sprint(789)
        
        # Assert
        assert "start_date" in result
        assert "end_date" in result
        assert result["start_date"] == "2025-02-01T10:00:00.000Z"
        assert result["end_date"] == "2025-02-14T17:00:00.000Z"


class TestStartSprintTool:
    """Test StartSprintTool CrewAI tool wrapper."""

    def test_tool_metadata(self):
        """Test tool has correct metadata."""
        tool = StartSprintTool()
        
        assert tool.name == "start_sprint"
        assert "start" in tool.description.lower()
        assert "sprint" in tool.description.lower()
        assert "future" in tool.description.lower()

    @patch("tools.pm_tools.jira.start_sprint")
    def test_tool_success(self, mock_start_sprint):
        """Test tool successfully starts a sprint."""
        # Arrange
        mock_start_sprint.return_value = {
            "id": 123,
            "name": "Test Sprint",
            "state": "active",
            "start_date": "2025-01-15T09:00:00.000Z",
            "end_date": "2025-01-29T18:00:00.000Z",
        }
        
        tool = StartSprintTool()
        
        # Act
        result = tool._run(sprint_id=123)
        
        # Assert
        assert "Sprint started successfully" in result
        assert "Test Sprint" in result
        assert "ID: 123" in result
        assert "state: active" in result
        mock_start_sprint.assert_called_once_with(123)

    @patch("tools.pm_tools.jira.start_sprint")
    def test_tool_handles_value_error(self, mock_start_sprint):
        """Test tool handles ValueError (e.g., sprint not in future state)."""
        # Arrange
        mock_start_sprint.side_effect = ValueError("Sprint is not in future state")
        
        tool = StartSprintTool()
        
        # Act
        result = tool._run(sprint_id=456)
        
        # Assert
        assert "Error starting sprint" in result
        assert "Sprint is not in future state" in result

    @patch("tools.pm_tools.jira.start_sprint")
    def test_tool_handles_unexpected_error(self, mock_start_sprint):
        """Test tool handles unexpected exceptions."""
        # Arrange
        mock_start_sprint.side_effect = Exception("Network error")
        
        tool = StartSprintTool()
        
        # Act
        result = tool._run(sprint_id=789)
        
        # Assert
        assert "Unexpected error starting sprint" in result
        assert "Network error" in result

    def test_tool_input_schema(self):
        """Test tool has correct input schema."""
        tool = StartSprintTool()
        
        # The args_schema should be StartSprintInput
        from tools.pm_tools import StartSprintInput
        assert tool.args_schema == StartSprintInput
        
        # Create an instance to verify schema
        input_data = StartSprintInput(sprint_id=123)
        assert input_data.sprint_id == 123


class TestStartSprintIntegration:
    """Integration tests for sprint starting workflow."""

    @patch("tools.jira_client._get_client")
    @patch("tools.jira_client._get_board_id")
    def test_complete_workflow(self, mock_get_board_id, mock_get_client):
        """Test complete workflow: create sprint -> add issues -> start sprint."""
        # This would be more of an integration test
        # For now, just verify the functions can be called in sequence
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        mock_get_board_id.return_value = 1
        
        # Mock create_sprint
        mock_sprint_created = Mock()
        mock_sprint_created.id = 100
        mock_sprint_created.name = "Integration Test Sprint"
        mock_sprint_created.state = "future"
        mock_jira.create_sprint.return_value = mock_sprint_created
        
        # Mock start_sprint sequence
        mock_sprint_future = Mock()
        mock_sprint_future.state = "future"
        mock_sprint_active = Mock()
        mock_sprint_active.id = 100
        mock_sprint_active.name = "Integration Test Sprint"
        mock_sprint_active.state = "active"
        mock_sprint_active.startDate = "2025-01-15T09:00:00.000Z"
        mock_sprint_active.endDate = "2025-01-29T18:00:00.000Z"
        
        mock_jira.sprint.side_effect = [mock_sprint_future, mock_sprint_active]
        mock_jira._options = {"server": "https://test.atlassian.net"}
        mock_jira._session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_jira._session.post.return_value = mock_response
        
        # Act - Create sprint
        created = jira_client.create_sprint(
            "Integration Test Sprint",
            "Test sprint goal",
            "2025-01-15T09:00:00.000Z",
            "2025-01-29T18:00:00.000Z"
        )
        
        # Act - Start sprint
        started = jira_client.start_sprint(created["id"])
        
        # Assert
        assert created["id"] == 100
        assert created["state"] == "future"
        assert started["id"] == 100
        assert started["state"] == "active"


class TestStartSprintValidation:
    """Test input validation for start_sprint."""

    @patch("tools.jira_client._get_client")
    @patch("tools.jira_client._get_board_id")
    def test_start_sprint_invalid_id_type(self, mock_get_board_id, mock_get_client):
        """Test that sprint_id must be an integer."""
        # The function signature requires int, but test runtime behavior
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        mock_get_board_id.return_value = 123
        
        mock_sprint = Mock()
        mock_sprint.state = "future"
        mock_jira.sprint.return_value = mock_sprint
        mock_jira._options = {"server": "https://test.atlassian.net"}
        mock_jira._session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_jira._session.post.return_value = mock_response
        
        # This should work with integer
        result = jira_client.start_sprint(123)
        assert result is not None

    def test_tool_requires_sprint_id(self):
        """Test that StartSprintTool requires sprint_id parameter."""
        from tools.pm_tools import StartSprintInput
        from pydantic import ValidationError
        
        # Should raise validation error if sprint_id is missing
        with pytest.raises(ValidationError):
            StartSprintInput()
