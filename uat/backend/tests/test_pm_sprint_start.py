"""
uat/backend/tests/test_pm_sprint_start.py
──────────────────────────────────────────
Tests for PM Agent sprint start functionality (SDT1-73).

Tests cover:
- Starting a sprint via Jira client
- StartSprintTool integration
- Error handling for invalid sprint states
- PM Agent workflow for sprint approval and activation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from tools import jira_client
from tools.pm_tools import StartSprintTool


class TestJiraClientStartSprint:
    """Test the jira_client.start_sprint function."""

    @patch('tools.jira_client._get_client')
    def test_start_sprint_success(self, mock_get_client):
        """Test successfully starting a future sprint."""
        # Arrange
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        # Mock sprint object in 'future' state
        mock_sprint = Mock()
        mock_sprint.id = 123
        mock_sprint.name = "Sprint 1"
        mock_sprint.state = "future"
        mock_sprint.goal = "Complete feature X"
        mock_sprint.startDate = "2025-01-15T09:00:00.000Z"
        mock_sprint.endDate = "2025-01-29T17:00:00.000Z"
        
        # Mock updated sprint object in 'active' state
        mock_updated_sprint = Mock()
        mock_updated_sprint.id = 123
        mock_updated_sprint.name = "Sprint 1"
        mock_updated_sprint.state = "active"
        mock_updated_sprint.goal = "Complete feature X"
        mock_updated_sprint.startDate = "2025-01-15T09:00:00.000Z"
        mock_updated_sprint.endDate = "2025-01-29T17:00:00.000Z"
        
        mock_jira.sprint.side_effect = [mock_sprint, mock_updated_sprint]
        mock_jira.update_sprint.return_value = None
        
        # Act
        result = jira_client.start_sprint(123)
        
        # Assert
        assert result["id"] == 123
        assert result["name"] == "Sprint 1"
        assert result["state"] == "active"
        assert result["goal"] == "Complete feature X"
        mock_jira.update_sprint.assert_called_once_with(123, state="active")

    @patch('tools.jira_client._get_client')
    def test_start_sprint_already_active(self, mock_get_client):
        """Test error when trying to start an already active sprint."""
        # Arrange
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        mock_sprint = Mock()
        mock_sprint.id = 123
        mock_sprint.state = "active"
        
        mock_jira.sprint.return_value = mock_sprint
        
        # Act & Assert
        with pytest.raises(ValueError, match="Sprint 123 is already active"):
            jira_client.start_sprint(123)
        
        mock_jira.update_sprint.assert_not_called()

    @patch('tools.jira_client._get_client')
    def test_start_sprint_closed(self, mock_get_client):
        """Test error when trying to start a closed sprint."""
        # Arrange
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        mock_sprint = Mock()
        mock_sprint.id = 123
        mock_sprint.state = "closed"
        
        mock_jira.sprint.return_value = mock_sprint
        
        # Act & Assert
        with pytest.raises(ValueError, match="Sprint 123 is closed and cannot be started"):
            jira_client.start_sprint(123)
        
        mock_jira.update_sprint.assert_not_called()

    @patch('tools.jira_client._get_client')
    def test_start_sprint_no_goal(self, mock_get_client):
        """Test starting a sprint with no goal set."""
        # Arrange
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        mock_sprint = Mock()
        mock_sprint.id = 123
        mock_sprint.name = "Sprint 1"
        mock_sprint.state = "future"
        # No goal attribute
        
        mock_updated_sprint = Mock()
        mock_updated_sprint.id = 123
        mock_updated_sprint.name = "Sprint 1"
        mock_updated_sprint.state = "active"
        
        mock_jira.sprint.side_effect = [mock_sprint, mock_updated_sprint]
        
        # Act
        result = jira_client.start_sprint(123)
        
        # Assert
        assert result["goal"] == ""


class TestStartSprintTool:
    """Test the StartSprintTool CrewAI tool wrapper."""

    def test_start_sprint_tool_success(self):
        """Test StartSprintTool with successful sprint start."""
        # Arrange
        tool = StartSprintTool()
        
        with patch('tools.jira_client.start_sprint') as mock_start:
            mock_start.return_value = {
                "id": 123,
                "name": "Sprint 1",
                "state": "active",
                "goal": "Complete feature X",
            }
            
            # Act
            result = tool._run(sprint_id=123)
            
            # Assert
            assert "✓ Sprint started successfully!" in result
            assert "Sprint ID: 123" in result
            assert "Name: Sprint 1" in result
            assert "State: active" in result
            assert "Goal: Complete feature X" in result

    def test_start_sprint_tool_already_active(self):
        """Test StartSprintTool with already active sprint."""
        # Arrange
        tool = StartSprintTool()
        
        with patch('tools.jira_client.start_sprint') as mock_start:
            mock_start.side_effect = ValueError("Sprint 123 is already active")
            
            # Act
            result = tool._run(sprint_id=123)
            
            # Assert
            assert "✗ Failed to start sprint:" in result
            assert "already active" in result

    def test_start_sprint_tool_closed_sprint(self):
        """Test StartSprintTool with closed sprint."""
        # Arrange
        tool = StartSprintTool()
        
        with patch('tools.jira_client.start_sprint') as mock_start:
            mock_start.side_effect = ValueError("Sprint 123 is closed and cannot be started")
            
            # Act
            result = tool._run(sprint_id=123)
            
            # Assert
            assert "✗ Failed to start sprint:" in result
            assert "closed" in result

    def test_start_sprint_tool_api_error(self):
        """Test StartSprintTool with Jira API error."""
        # Arrange
        tool = StartSprintTool()
        
        with patch('tools.jira_client.start_sprint') as mock_start:
            mock_start.side_effect = Exception("Jira API connection failed")
            
            # Act
            result = tool._run(sprint_id=123)
            
            # Assert
            assert "✗ Error starting sprint:" in result
            assert "connection failed" in result

    def test_start_sprint_tool_no_goal(self):
        """Test StartSprintTool with sprint that has no goal."""
        # Arrange
        tool = StartSprintTool()
        
        with patch('tools.jira_client.start_sprint') as mock_start:
            mock_start.return_value = {
                "id": 123,
                "name": "Sprint 1",
                "state": "active",
                "goal": "",
            }
            
            # Act
            result = tool._run(sprint_id=123)
            
            # Assert
            assert "✓ Sprint started successfully!" in result
            assert "Goal: No goal set" in result


class TestPMAgentSprintWorkflow:
    """Integration tests for PM Agent sprint start workflow."""

    @patch('tools.jira_client._get_client')
    def test_list_sprints_shows_future_sprint(self, mock_get_client):
        """Test that list_sprints shows future sprints that can be started."""
        # Arrange
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        mock_jira._get_board_id = Mock(return_value=10)
        
        with patch('tools.jira_client._get_board_id', return_value=10):
            mock_sprint = Mock()
            mock_sprint.id = 123
            mock_sprint.name = "Sprint 1"
            mock_sprint.state = "future"
            mock_sprint.goal = "Complete feature X"
            mock_sprint.startDate = "2025-01-15T09:00:00.000Z"
            mock_sprint.endDate = "2025-01-29T17:00:00.000Z"
            
            mock_jira.sprints.return_value = [mock_sprint]
            
            # Act
            result = jira_client.list_sprints()
            
            # Assert
            assert len(result) == 1
            assert result[0]["id"] == 123
            assert result[0]["state"] == "future"

    def test_sprint_tools_included_in_all_pm_tools(self):
        """Test that StartSprintTool is available in ALL_PM_TOOLS."""
        from tools.pm_tools import ALL_PM_TOOLS, SPRINT_TOOLS
        
        # Check that StartSprintTool is in SPRINT_TOOLS
        tool_names = [tool.name for tool in SPRINT_TOOLS]
        assert "start_sprint" in tool_names
        
        # Check that StartSprintTool is in ALL_PM_TOOLS
        all_tool_names = [tool.name for tool in ALL_PM_TOOLS]
        assert "start_sprint" in all_tool_names

    def test_pm_agent_has_sprint_start_in_backstory(self):
        """Test that PM Agent backstory mentions sprint starting capability."""
        from agents.pm_agent import PM_AGENT_BACKSTORY
        
        # Check that the backstory includes sprint activation guidance
        assert "SPRINT ACTIVATION" in PM_AGENT_BACKSTORY
        assert "start_sprint" in PM_AGENT_BACKSTORY.lower()
        assert "approved" in PM_AGENT_BACKSTORY.lower()

    def test_pm_agent_goal_includes_sprint_start(self):
        """Test that PM Agent goal includes starting sprints."""
        from agents.pm_agent import build_pm_agent
        
        agent = build_pm_agent(verbose=False, tools=[])
        
        # Check that the goal mentions starting sprints
        assert "start" in agent.goal.lower()
        assert "sprint" in agent.goal.lower()


class TestSprintStartValidation:
    """Tests for sprint start validation and error handling."""

    @patch('tools.jira_client._get_client')
    def test_start_sprint_validates_state_before_update(self, mock_get_client):
        """Test that start_sprint checks sprint state before attempting update."""
        # Arrange
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        mock_sprint = Mock()
        mock_sprint.id = 123
        mock_sprint.state = "active"
        
        mock_jira.sprint.return_value = mock_sprint
        
        # Act & Assert
        with pytest.raises(ValueError):
            jira_client.start_sprint(123)
        
        # Ensure update_sprint was never called
        mock_jira.update_sprint.assert_not_called()

    @patch('tools.jira_client._get_client')
    def test_start_sprint_returns_updated_state(self, mock_get_client):
        """Test that start_sprint returns the updated sprint state."""
        # Arrange
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        mock_sprint = Mock()
        mock_sprint.id = 123
        mock_sprint.state = "future"
        
        mock_updated_sprint = Mock()
        mock_updated_sprint.id = 123
        mock_updated_sprint.name = "Sprint 1"
        mock_updated_sprint.state = "active"
        mock_updated_sprint.goal = "Test goal"
        mock_updated_sprint.startDate = "2025-01-15T09:00:00.000Z"
        mock_updated_sprint.endDate = "2025-01-29T17:00:00.000Z"
        
        # First call returns future sprint, second returns active sprint
        mock_jira.sprint.side_effect = [mock_sprint, mock_updated_sprint]
        
        # Act
        result = jira_client.start_sprint(123)
        
        # Assert
        assert result["state"] == "active"
        # Verify sprint was fetched twice (before and after update)
        assert mock_jira.sprint.call_count == 2
