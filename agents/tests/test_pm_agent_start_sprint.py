"""
tests/test_pm_agent_start_sprint.py
───────────────────────────────────
Integration tests for PM Agent sprint starting capability.

Tests that the PM Agent can successfully use the start_sprint tool
after creating and populating a sprint.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.pm_agent import build_pm_agent, PM_AGENT_BACKSTORY
from tools.pm_tools import StartSprintTool, SPRINT_TOOLS


class TestPMAgentStartSprint:
    """Test PM Agent's ability to start sprints."""

    def test_pm_agent_has_start_sprint_tool(self):
        """Test that PM Agent has access to start_sprint tool in SPRINT_TOOLS."""
        # Check that StartSprintTool is in SPRINT_TOOLS
        tool_names = [tool.name for tool in SPRINT_TOOLS]
        assert "start_sprint" in tool_names

    def test_pm_agent_backstory_includes_sprint_activation(self):
        """Test that PM Agent's backstory includes sprint activation instructions."""
        assert "SPRINT ACTIVATION" in PM_AGENT_BACKSTORY
        assert "start_sprint" in PM_AGENT_BACKSTORY
        assert "future" in PM_AGENT_BACKSTORY
        assert "activate" in PM_AGENT_BACKSTORY.lower()

    def test_pm_agent_goal_includes_start_sprints(self):
        """Test that PM Agent's goal includes starting sprints."""
        agent = build_pm_agent(verbose=False)
        assert "start sprints" in agent.goal.lower()

    def test_build_pm_agent_with_sprint_tools(self):
        """Test building PM Agent with sprint tools including start_sprint."""
        agent = build_pm_agent(verbose=False, tools=SPRINT_TOOLS)
        
        # Agent should have access to tools
        assert agent.tools is not None
        assert len(agent.tools) > 0
        
        # Check that start_sprint is in the tools
        tool_names = [tool.name for tool in agent.tools]
        assert "start_sprint" in tool_names

    @patch("tools.jira_client._get_client")
    @patch("tools.jira_client._get_board_id")
    def test_pm_agent_can_call_start_sprint_tool(
        self, mock_get_board_id, mock_get_client
    ):
        """Test that start_sprint tool can be called successfully."""
        # Arrange
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        mock_get_board_id.return_value = 123
        
        # Mock sprint states
        mock_sprint_before = Mock()
        mock_sprint_before.id = 456
        mock_sprint_before.name = "Test Sprint"
        mock_sprint_before.state = "future"
        
        mock_sprint_after = Mock()
        mock_sprint_after.id = 456
        mock_sprint_after.name = "Test Sprint"
        mock_sprint_after.state = "active"
        mock_sprint_after.startDate = "2025-01-15T09:00:00.000Z"
        mock_sprint_after.endDate = "2025-01-29T18:00:00.000Z"
        
        mock_jira.sprint.side_effect = [mock_sprint_before, mock_sprint_after]
        mock_jira._options = {"server": "https://test.atlassian.net"}
        mock_jira._session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_jira._session.post.return_value = mock_response
        
        # Get the start_sprint tool
        start_sprint_tool = None
        for tool in SPRINT_TOOLS:
            if tool.name == "start_sprint":
                start_sprint_tool = tool
                break
        
        assert start_sprint_tool is not None
        
        # Act
        result = start_sprint_tool._run(sprint_id=456)
        
        # Assert
        assert "Sprint started successfully" in result
        assert "Test Sprint" in result
        assert "active" in result

    def test_sprint_tools_order(self):
        """Test that sprint tools are in logical order."""
        tool_names = [tool.name for tool in SPRINT_TOOLS]
        
        # Check expected tools are present
        expected_tools = [
            "list_sprints",
            "create_sprint",
            "start_sprint",
            "add_issues_to_sprint",
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    def test_pm_agent_backstory_sprint_workflow(self):
        """Test that backstory describes the complete sprint workflow."""
        backstory = PM_AGENT_BACKSTORY
        
        # Check for complete workflow steps
        assert "SPRINT PLANNING" in backstory
        assert "SPRINT ACTIVATION" in backstory
        assert "create" in backstory.lower()
        assert "populate" in backstory.lower()
        assert "start" in backstory.lower()
        
        # Check for state validation
        assert "future" in backstory
        assert "active" not in backstory or "completed" not in backstory  # Should not start active/completed

    @patch("tools.jira_client._get_client")
    @patch("tools.jira_client._get_board_id")
    def test_start_sprint_error_handling_in_context(
        self, mock_get_board_id, mock_get_client
    ):
        """Test that errors are properly surfaced to the agent."""
        # Arrange
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        mock_get_board_id.return_value = 123
        
        # Mock an already active sprint
        mock_sprint = Mock()
        mock_sprint.id = 789
        mock_sprint.name = "Active Sprint"
        mock_sprint.state = "active"
        
        mock_jira.sprint.return_value = mock_sprint
        
        # Get the tool
        start_sprint_tool = None
        for tool in SPRINT_TOOLS:
            if tool.name == "start_sprint":
                start_sprint_tool = tool
                break
        
        # Act
        result = start_sprint_tool._run(sprint_id=789)
        
        # Assert - error should be returned, not raised
        assert "Error starting sprint" in result
        assert "active" in result.lower() or "future" in result.lower()


class TestPMAgentSprintWorkflow:
    """Test complete PM Agent sprint workflow including start."""

    def test_pm_agent_workflow_instructions(self):
        """Test that backstory includes correct workflow sequence."""
        backstory = PM_AGENT_BACKSTORY
        
        # The workflow should be: plan -> populate -> start
        # Check these concepts appear in order
        plan_idx = backstory.find("SPRINT PLANNING")
        activate_idx = backstory.find("SPRINT ACTIVATION")
        
        # SPRINT PLANNING should come before SPRINT ACTIVATION in backstory
        assert plan_idx < activate_idx
        assert plan_idx != -1
        assert activate_idx != -1

    def test_pm_agent_approval_workflow(self):
        """Test that backstory mentions approval before starting sprint."""
        backstory = PM_AGENT_BACKSTORY
        
        # Check for approval-related language
        activation_section = backstory[backstory.find("SPRINT ACTIVATION"):]
        assert "approval" in activation_section.lower() or "approved" in activation_section.lower()

    def test_pm_agent_state_validation_rules(self):
        """Test that backstory includes state validation rules."""
        backstory = PM_AGENT_BACKSTORY
        
        # Rules section should mention state constraints
        rules_section = backstory[backstory.find("Rules:"):]
        assert "future" in rules_section
        assert "start" in rules_section.lower()

    def test_pm_agent_has_all_sprint_management_tools(self):
        """Test that PM Agent has all necessary sprint management tools."""
        agent = build_pm_agent(verbose=False, tools=SPRINT_TOOLS)
        tool_names = [tool.name for tool in agent.tools]
        
        required_sprint_tools = [
            "list_sprints",      # To view sprints
            "create_sprint",     # To create new sprint
            "add_issues_to_sprint",  # To populate sprint
            "start_sprint",      # To activate sprint
        ]
        
        for required_tool in required_sprint_tools:
            assert required_tool in tool_names, f"Missing required tool: {required_tool}"


class TestStartSprintDocumentation:
    """Test that sprint starting functionality is well-documented."""

    def test_start_sprint_tool_description(self):
        """Test that StartSprintTool has comprehensive description."""
        from tools.pm_tools import StartSprintTool
        
        tool = StartSprintTool()
        description = tool.description.lower()
        
        # Description should explain what the tool does
        assert "start" in description
        assert "sprint" in description
        assert "future" in description
        
        # Should mention state requirements
        assert "state" in description

    def test_jira_client_start_sprint_docstring(self):
        """Test that start_sprint function has comprehensive docstring."""
        from tools import jira_client
        
        docstring = jira_client.start_sprint.__doc__
        assert docstring is not None
        
        # Should document parameters
        assert "sprint_id" in docstring.lower()
        
        # Should document return value
        assert "returns" in docstring.lower()
        
        # Should document errors
        assert "raises" in docstring.lower()
        assert "ValueError" in docstring

    def test_backstory_numbered_responsibilities(self):
        """Test that sprint activation is properly numbered in responsibilities."""
        backstory = PM_AGENT_BACKSTORY
        
        # Should have numbered responsibility for sprint activation
        assert "6. SPRINT ACTIVATION" in backstory

    def test_backstory_includes_tool_name(self):
        """Test that backstory explicitly mentions start_sprint tool."""
        backstory = PM_AGENT_BACKSTORY
        assert "start_sprint" in backstory
