"""
Tests for StartSprintTool in pm_tools.py

Run with: pytest tools/tests/test_pm_tools_start_sprint.py -v
"""

from unittest.mock import patch, Mock
import pytest
from tools.pm_tools import StartSprintTool


@pytest.fixture
def start_sprint_tool():
    """Create a StartSprintTool instance."""
    return StartSprintTool()


def test_start_sprint_tool_success(start_sprint_tool):
    """Test StartSprintTool with successful sprint start."""
    mock_result = {
        "id": 123,
        "name": "Sprint 1",
        "state": "active",
        "start_date": "2025-01-20T09:00:00.000Z",
        "end_date": "2025-02-03T17:00:00.000Z",
        "goal": "Complete user authentication"
    }
    
    with patch("tools.pm_tools.jira.start_sprint", return_value=mock_result) as mock_start:
        result = start_sprint_tool._run(sprint_id=123)
        
        # Verify the jira client was called correctly
        mock_start.assert_called_once_with(123)
        
        # Verify the response format
        assert "Sprint started successfully!" in result
        assert "ID: 123" in result
        assert "Name: Sprint 1" in result
        assert "State: active" in result
        assert "Start: 2025-01-20T09:00:00.000Z" in result
        assert "End: 2025-02-03T17:00:00.000Z" in result


def test_start_sprint_tool_value_error(start_sprint_tool):
    """Test StartSprintTool handling ValueError (invalid state)."""
    with patch("tools.pm_tools.jira.start_sprint") as mock_start:
        mock_start.side_effect = ValueError("Sprint is in 'active' state. Only sprints in 'future' state can be started.")
        
        result = start_sprint_tool._run(sprint_id=123)
        
        # Verify error is caught and formatted properly
        assert "Failed to start sprint:" in result
        assert "Sprint is in 'active' state" in result


def test_start_sprint_tool_generic_error(start_sprint_tool):
    """Test StartSprintTool handling generic exceptions."""
    with patch("tools.pm_tools.jira.start_sprint") as mock_start:
        mock_start.side_effect = Exception("Network connection error")
        
        result = start_sprint_tool._run(sprint_id=123)
        
        # Verify error is caught and formatted properly
        assert "Error starting sprint:" in result
        assert "Network connection error" in result


def test_start_sprint_tool_missing_dates_error(start_sprint_tool):
    """Test StartSprintTool handling missing date error."""
    with patch("tools.pm_tools.jira.start_sprint") as mock_start:
        mock_start.side_effect = ValueError(
            "Sprint 123 must have start_date and end_date set before it can be started."
        )
        
        result = start_sprint_tool._run(sprint_id=123)
        
        # Verify error message is preserved
        assert "Failed to start sprint:" in result
        assert "must have start_date and end_date set" in result


def test_start_sprint_tool_with_minimal_response(start_sprint_tool):
    """Test StartSprintTool with minimal response data."""
    mock_result = {
        "id": 456,
        "name": "Sprint 2",
        "state": "active",
        # No start_date, end_date, or goal
    }
    
    with patch("tools.pm_tools.jira.start_sprint", return_value=mock_result) as mock_start:
        result = start_sprint_tool._run(sprint_id=456)
        
        # Verify the tool handles missing optional fields
        assert "Sprint started successfully!" in result
        assert "ID: 456" in result
        assert "Name: Sprint 2" in result
        assert "State: active" in result
        assert "Start: N/A" in result
        assert "End: N/A" in result


def test_start_sprint_tool_attributes():
    """Test that StartSprintTool has correct metadata."""
    tool = StartSprintTool()
    
    assert tool.name == "start_sprint"
    assert "start" in tool.description.lower()
    assert "activate" in tool.description.lower()
    assert "sprint" in tool.description.lower()


def test_start_sprint_tool_input_schema():
    """Test that StartSprintTool has correct input schema."""
    tool = StartSprintTool()
    
    # Verify the tool accepts sprint_id parameter
    schema = tool.args_schema.schema()
    
    assert "sprint_id" in schema["properties"]
    assert schema["properties"]["sprint_id"]["type"] == "integer"
    assert "required" in schema
    assert "sprint_id" in schema["required"]


def test_start_sprint_tool_in_sprint_tools_list():
    """Test that StartSprintTool is included in SPRINT_TOOLS."""
    from tools.pm_tools import SPRINT_TOOLS
    
    tool_names = [tool.name for tool in SPRINT_TOOLS]
    assert "start_sprint" in tool_names


def test_start_sprint_tool_workflow_simulation(start_sprint_tool):
    """Simulate a complete sprint workflow: create -> populate -> start."""
    # Mock the entire workflow
    with patch("tools.pm_tools.jira.create_sprint") as mock_create, \
         patch("tools.pm_tools.jira.add_issues_to_sprint") as mock_add, \
         patch("tools.pm_tools.jira.start_sprint") as mock_start:
        
        # Set up mocks
        mock_create.return_value = {"id": 999, "name": "Test Sprint", "state": "future"}
        mock_add.return_value = None
        mock_start.return_value = {
            "id": 999,
            "name": "Test Sprint",
            "state": "active",
            "start_date": "2025-01-20T09:00:00.000Z",
            "end_date": "2025-02-03T17:00:00.000Z",
        }
        
        # Workflow step 3: Start the sprint
        result = start_sprint_tool._run(sprint_id=999)
        
        # Verify success
        assert "Sprint started successfully!" in result
        assert "ID: 999" in result
        assert "State: active" in result
        mock_start.assert_called_once_with(999)
