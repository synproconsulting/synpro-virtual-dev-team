"""
tools/tests/test_jira_sprint_start.py
──────────────────────────────────────
Tests for the Jira sprint starting functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from tools import jira_client


class TestStartSprint:
    """Test cases for start_sprint function."""

    @patch("tools.jira_client._get_client")
    def test_start_sprint_success(self, mock_get_client):
        """Test successfully starting a future sprint."""
        # Setup mock Jira client
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        # Mock sprint object in 'future' state
        mock_sprint = Mock()
        mock_sprint.id = 123
        mock_sprint.name = "Sprint 1"
        mock_sprint.state = "future"
        
        # Mock updated sprint after starting
        mock_updated_sprint = Mock()
        mock_updated_sprint.id = 123
        mock_updated_sprint.name = "Sprint 1"
        mock_updated_sprint.state = "active"
        mock_updated_sprint.startDate = "2025-05-01T09:00:00.000Z"
        mock_updated_sprint.endDate = "2025-05-15T09:00:00.000Z"
        mock_updated_sprint.goal = "Complete authentication features"
        
        # Setup mock responses
        mock_jira.sprint.side_effect = [mock_sprint, mock_updated_sprint]
        
        # Mock the REST API session
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.put.return_value = mock_response
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://test.atlassian.net"}
        
        # Call the function
        result = jira_client.start_sprint(123)
        
        # Verify the result
        assert result["id"] == 123
        assert result["name"] == "Sprint 1"
        assert result["state"] == "active"
        assert result["start_date"] == "2025-05-01T09:00:00.000Z"
        assert result["end_date"] == "2025-05-15T09:00:00.000Z"
        assert result["goal"] == "Complete authentication features"
        
        # Verify API calls
        assert mock_jira.sprint.call_count == 2
        mock_session.put.assert_called_once()
        
        # Verify the PUT request payload
        call_args = mock_session.put.call_args
        assert call_args[0][0] == "https://test.atlassian.net/rest/agile/1.0/sprint/123"
        assert call_args[1]["json"] == {"state": "active"}

    @patch("tools.jira_client._get_client")
    def test_start_sprint_already_active(self, mock_get_client):
        """Test error when trying to start an already active sprint."""
        # Setup mock Jira client
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        # Mock sprint object in 'active' state
        mock_sprint = Mock()
        mock_sprint.id = 123
        mock_sprint.name = "Sprint 1"
        mock_sprint.state = "active"
        
        mock_jira.sprint.return_value = mock_sprint
        
        # Call the function and expect an error
        with pytest.raises(ValueError, match="already active"):
            jira_client.start_sprint(123)
        
        # Verify sprint was checked but not modified
        mock_jira.sprint.assert_called_once_with(123)

    @patch("tools.jira_client._get_client")
    def test_start_sprint_closed_sprint(self, mock_get_client):
        """Test error when trying to start a closed sprint."""
        # Setup mock Jira client
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        # Mock sprint object in 'closed' state
        mock_sprint = Mock()
        mock_sprint.id = 123
        mock_sprint.name = "Sprint 1"
        mock_sprint.state = "closed"
        
        mock_jira.sprint.return_value = mock_sprint
        
        # Call the function and expect an error
        with pytest.raises(ValueError, match="closed and cannot be started"):
            jira_client.start_sprint(123)

    @patch("tools.jira_client._get_client")
    def test_start_sprint_api_error(self, mock_get_client):
        """Test error handling when API request fails."""
        # Setup mock Jira client
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        # Mock sprint object in 'future' state
        mock_sprint = Mock()
        mock_sprint.id = 123
        mock_sprint.name = "Sprint 1"
        mock_sprint.state = "future"
        
        mock_jira.sprint.return_value = mock_sprint
        
        # Mock failed REST API response
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad request: sprint has no issues"
        mock_session.put.return_value = mock_response
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://test.atlassian.net"}
        
        # Call the function and expect an error
        with pytest.raises(ValueError, match="Failed to start sprint 123"):
            jira_client.start_sprint(123)

    @patch("tools.jira_client._get_client")
    def test_start_sprint_minimal_fields(self, mock_get_client):
        """Test starting sprint when sprint has minimal fields."""
        # Setup mock Jira client
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        # Mock sprint object with minimal fields
        mock_sprint = Mock()
        mock_sprint.id = 456
        mock_sprint.name = "Sprint 2"
        mock_sprint.state = "future"
        
        # Mock updated sprint with minimal fields (no dates or goal)
        mock_updated_sprint = Mock()
        mock_updated_sprint.id = 456
        mock_updated_sprint.name = "Sprint 2"
        mock_updated_sprint.state = "active"
        # Using spec to ensure getattr returns None for missing attributes
        del mock_updated_sprint.startDate
        del mock_updated_sprint.endDate
        del mock_updated_sprint.goal
        
        mock_jira.sprint.side_effect = [mock_sprint, mock_updated_sprint]
        
        # Mock the REST API session
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.put.return_value = mock_response
        mock_jira._session = mock_session
        mock_jira._options = {"server": "https://test.atlassian.net"}
        
        # Call the function
        result = jira_client.start_sprint(456)
        
        # Verify the result with None for missing fields
        assert result["id"] == 456
        assert result["name"] == "Sprint 2"
        assert result["state"] == "active"
        assert result["start_date"] is None
        assert result["end_date"] is None
        assert result["goal"] == ""


class TestStartSprintTool:
    """Test cases for the StartSprintTool wrapper."""

    @patch("tools.jira_client.start_sprint")
    def test_start_sprint_tool_success(self, mock_start_sprint):
        """Test StartSprintTool with successful execution."""
        from tools.pm_tools import StartSprintTool
        
        # Mock successful sprint start
        mock_start_sprint.return_value = {
            "id": 123,
            "name": "Sprint 1",
            "state": "active",
            "start_date": "2025-05-01T09:00:00.000Z",
            "end_date": "2025-05-15T09:00:00.000Z",
        }
        
        # Create tool and run
        tool = StartSprintTool()
        result = tool._run(sprint_id=123)
        
        # Verify result
        assert "✓ Sprint started successfully" in result
        assert "Sprint 1" in result
        assert "ID: 123" in result
        assert "State: active" in result
        
        # Verify mock was called
        mock_start_sprint.assert_called_once_with(123)

    @patch("tools.jira_client.start_sprint")
    def test_start_sprint_tool_value_error(self, mock_start_sprint):
        """Test StartSprintTool handling ValueError."""
        from tools.pm_tools import StartSprintTool
        
        # Mock ValueError
        mock_start_sprint.side_effect = ValueError("Sprint 123 is already active")
        
        # Create tool and run
        tool = StartSprintTool()
        result = tool._run(sprint_id=123)
        
        # Verify error message
        assert "✗ Failed to start sprint 123" in result
        assert "already active" in result

    @patch("tools.jira_client.start_sprint")
    def test_start_sprint_tool_unexpected_error(self, mock_start_sprint):
        """Test StartSprintTool handling unexpected errors."""
        from tools.pm_tools import StartSprintTool
        
        # Mock unexpected exception
        mock_start_sprint.side_effect = ConnectionError("Network error")
        
        # Create tool and run
        tool = StartSprintTool()
        result = tool._run(sprint_id=123)
        
        # Verify error message
        assert "✗ Unexpected error starting sprint 123" in result
        assert "Network error" in result


class TestSprintToolsIntegration:
    """Integration tests for sprint workflow."""

    @patch("tools.jira_client._get_client")
    def test_complete_sprint_workflow(self, mock_get_client):
        """Test complete workflow: create, populate, and start sprint."""
        from tools.pm_tools import CreateSprintTool, AddToSprintTool, StartSprintTool
        
        # Setup mock Jira client
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        # Mock board ID
        with patch("tools.jira_client._get_board_id", return_value=1):
            # Step 1: Create sprint
            mock_created_sprint = Mock()
            mock_created_sprint.id = 123
            mock_created_sprint.name = "Sprint 1"
            mock_created_sprint.state = "future"
            mock_jira.create_sprint.return_value = mock_created_sprint
            
            create_tool = CreateSprintTool()
            create_result = create_tool._run(
                name="Sprint 1",
                goal="Complete authentication",
                start_date="2025-05-01T09:00:00.000Z",
                end_date="2025-05-15T09:00:00.000Z"
            )
            
            assert "Sprint created: ID=123" in create_result
            
            # Step 2: Add issues to sprint
            add_tool = AddToSprintTool()
            add_result = add_tool._run(
                sprint_id=123,
                issue_keys=["SDT1-1", "SDT1-2", "SDT1-3"]
            )
            
            assert "Added ['SDT1-1', 'SDT1-2', 'SDT1-3'] to sprint 123" in add_result
            mock_jira.add_issues_to_sprint.assert_called_once()
            
            # Step 3: Start sprint
            mock_sprint_to_start = Mock()
            mock_sprint_to_start.id = 123
            mock_sprint_to_start.state = "future"
            
            mock_started_sprint = Mock()
            mock_started_sprint.id = 123
            mock_started_sprint.name = "Sprint 1"
            mock_started_sprint.state = "active"
            mock_started_sprint.startDate = "2025-05-01T09:00:00.000Z"
            mock_started_sprint.endDate = "2025-05-15T09:00:00.000Z"
            mock_started_sprint.goal = "Complete authentication"
            
            mock_jira.sprint.side_effect = [mock_sprint_to_start, mock_started_sprint]
            
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_session.put.return_value = mock_response
            mock_jira._session = mock_session
            mock_jira._options = {"server": "https://test.atlassian.net"}
            
            start_tool = StartSprintTool()
            start_result = start_tool._run(sprint_id=123)
            
            assert "✓ Sprint started successfully" in start_result
            assert "Sprint 1" in start_result
            assert "State: active" in start_result
