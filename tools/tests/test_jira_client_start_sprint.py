"""
Tests for start_sprint functionality in jira_client.py

Run with: pytest tools/tests/test_jira_client_start_sprint.py -v
"""

import os
from unittest.mock import Mock, patch, MagicMock
import pytest
from tools import jira_client


@pytest.fixture
def mock_jira_env(monkeypatch):
    """Set up mock environment variables for Jira connection."""
    monkeypatch.setenv("JIRA_URL", "https://test.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "test@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
    monkeypatch.setenv("JIRA_PROJECT_KEY", "TEST")
    monkeypatch.setenv("JIRA_BOARD_ID", "1")


@pytest.fixture
def mock_jira_client():
    """Create a mock JIRA client."""
    with patch("tools.jira_client.JIRA") as mock_jira:
        yield mock_jira


def test_start_sprint_success(mock_jira_env, mock_jira_client):
    """Test successfully starting a sprint in 'future' state."""
    # Clear the singleton instance
    if hasattr(jira_client._get_client, "_instance"):
        delattr(jira_client._get_client, "_instance")
    
    # Set up mock sprint in 'future' state
    mock_sprint = Mock()
    mock_sprint.id = 123
    mock_sprint.name = "Sprint 1"
    mock_sprint.state = "future"
    mock_sprint.startDate = "2025-01-20T09:00:00.000Z"
    mock_sprint.endDate = "2025-02-03T17:00:00.000Z"
    mock_sprint.goal = "Complete user authentication"
    
    # Set up updated sprint in 'active' state
    mock_updated_sprint = Mock()
    mock_updated_sprint.id = 123
    mock_updated_sprint.name = "Sprint 1"
    mock_updated_sprint.state = "active"
    mock_updated_sprint.startDate = "2025-01-20T09:00:00.000Z"
    mock_updated_sprint.endDate = "2025-02-03T17:00:00.000Z"
    mock_updated_sprint.goal = "Complete user authentication"
    
    # Configure mock client
    mock_instance = mock_jira_client.return_value
    mock_instance.sprint.side_effect = [mock_sprint, mock_updated_sprint]
    mock_instance.update_sprint.return_value = None
    
    # Execute
    result = jira_client.start_sprint(123)
    
    # Verify
    assert result["id"] == 123
    assert result["name"] == "Sprint 1"
    assert result["state"] == "active"
    assert result["start_date"] == "2025-01-20T09:00:00.000Z"
    assert result["end_date"] == "2025-02-03T17:00:00.000Z"
    assert result["goal"] == "Complete user authentication"
    
    # Verify update_sprint was called with correct parameters
    mock_instance.update_sprint.assert_called_once_with(123, state="active")


def test_start_sprint_already_active(mock_jira_env, mock_jira_client):
    """Test that starting an already active sprint raises ValueError."""
    # Clear the singleton instance
    if hasattr(jira_client._get_client, "_instance"):
        delattr(jira_client._get_client, "_instance")
    
    # Set up mock sprint in 'active' state
    mock_sprint = Mock()
    mock_sprint.id = 123
    mock_sprint.name = "Sprint 1"
    mock_sprint.state = "active"
    mock_sprint.startDate = "2025-01-20T09:00:00.000Z"
    mock_sprint.endDate = "2025-02-03T17:00:00.000Z"
    
    # Configure mock client
    mock_instance = mock_jira_client.return_value
    mock_instance.sprint.return_value = mock_sprint
    
    # Execute and verify exception
    with pytest.raises(ValueError) as exc_info:
        jira_client.start_sprint(123)
    
    assert "is in 'active' state" in str(exc_info.value)
    assert "Only sprints in 'future' state can be started" in str(exc_info.value)
    
    # Verify update_sprint was NOT called
    mock_instance.update_sprint.assert_not_called()


def test_start_sprint_missing_start_date(mock_jira_env, mock_jira_client):
    """Test that starting a sprint without start_date raises ValueError."""
    # Clear the singleton instance
    if hasattr(jira_client._get_client, "_instance"):
        delattr(jira_client._get_client, "_instance")
    
    # Set up mock sprint without start_date
    mock_sprint = Mock()
    mock_sprint.id = 123
    mock_sprint.name = "Sprint 1"
    mock_sprint.state = "future"
    mock_sprint.startDate = None
    mock_sprint.endDate = "2025-02-03T17:00:00.000Z"
    
    # Configure mock client
    mock_instance = mock_jira_client.return_value
    mock_instance.sprint.return_value = mock_sprint
    
    # Execute and verify exception
    with pytest.raises(ValueError) as exc_info:
        jira_client.start_sprint(123)
    
    assert "must have start_date and end_date set" in str(exc_info.value)
    
    # Verify update_sprint was NOT called
    mock_instance.update_sprint.assert_not_called()


def test_start_sprint_missing_end_date(mock_jira_env, mock_jira_client):
    """Test that starting a sprint without end_date raises ValueError."""
    # Clear the singleton instance
    if hasattr(jira_client._get_client, "_instance"):
        delattr(jira_client._get_client, "_instance")
    
    # Set up mock sprint without end_date
    mock_sprint = Mock()
    mock_sprint.id = 123
    mock_sprint.name = "Sprint 1"
    mock_sprint.state = "future"
    mock_sprint.startDate = "2025-01-20T09:00:00.000Z"
    mock_sprint.endDate = None
    
    # Configure mock client
    mock_instance = mock_jira_client.return_value
    mock_instance.sprint.return_value = mock_sprint
    
    # Execute and verify exception
    with pytest.raises(ValueError) as exc_info:
        jira_client.start_sprint(123)
    
    assert "must have start_date and end_date set" in str(exc_info.value)
    
    # Verify update_sprint was NOT called
    mock_instance.update_sprint.assert_not_called()


def test_start_sprint_completed_state(mock_jira_env, mock_jira_client):
    """Test that starting a completed sprint raises ValueError."""
    # Clear the singleton instance
    if hasattr(jira_client._get_client, "_instance"):
        delattr(jira_client._get_client, "_instance")
    
    # Set up mock sprint in 'closed' state
    mock_sprint = Mock()
    mock_sprint.id = 123
    mock_sprint.name = "Sprint 1"
    mock_sprint.state = "closed"
    
    # Configure mock client
    mock_instance = mock_jira_client.return_value
    mock_instance.sprint.return_value = mock_sprint
    
    # Execute and verify exception
    with pytest.raises(ValueError) as exc_info:
        jira_client.start_sprint(123)
    
    assert "is in 'closed' state" in str(exc_info.value)
    assert "Only sprints in 'future' state can be started" in str(exc_info.value)
    
    # Verify update_sprint was NOT called
    mock_instance.update_sprint.assert_not_called()


def test_start_sprint_with_minimal_attributes(mock_jira_env, mock_jira_client):
    """Test starting a sprint that has minimal required attributes."""
    # Clear the singleton instance
    if hasattr(jira_client._get_client, "_instance"):
        delattr(jira_client._get_client, "_instance")
    
    # Set up mock sprint without goal
    mock_sprint = Mock()
    mock_sprint.id = 456
    mock_sprint.name = "Sprint 2"
    mock_sprint.state = "future"
    mock_sprint.startDate = "2025-02-03T09:00:00.000Z"
    mock_sprint.endDate = "2025-02-17T17:00:00.000Z"
    # No goal attribute
    
    mock_updated_sprint = Mock()
    mock_updated_sprint.id = 456
    mock_updated_sprint.name = "Sprint 2"
    mock_updated_sprint.state = "active"
    mock_updated_sprint.startDate = "2025-02-03T09:00:00.000Z"
    mock_updated_sprint.endDate = "2025-02-17T17:00:00.000Z"
    # No goal attribute
    
    # Configure mock client
    mock_instance = mock_jira_client.return_value
    mock_instance.sprint.side_effect = [mock_sprint, mock_updated_sprint]
    mock_instance.update_sprint.return_value = None
    
    # Execute
    result = jira_client.start_sprint(456)
    
    # Verify - should handle missing goal gracefully
    assert result["id"] == 456
    assert result["name"] == "Sprint 2"
    assert result["state"] == "active"
    assert result["goal"] == ""  # Should default to empty string
    
    mock_instance.update_sprint.assert_called_once_with(456, state="active")


def test_start_sprint_integration_with_create_sprint(mock_jira_env, mock_jira_client):
    """Test workflow: create sprint -> add issues -> start sprint."""
    # Clear the singleton instance
    if hasattr(jira_client._get_client, "_instance"):
        delattr(jira_client._get_client, "_instance")
    
    # Mock create_sprint
    mock_created_sprint = Mock()
    mock_created_sprint.id = 789
    mock_created_sprint.name = "Sprint 3"
    mock_created_sprint.state = "future"
    
    # Mock sprint retrieval for start_sprint
    mock_future_sprint = Mock()
    mock_future_sprint.id = 789
    mock_future_sprint.name = "Sprint 3"
    mock_future_sprint.state = "future"
    mock_future_sprint.startDate = "2025-02-17T09:00:00.000Z"
    mock_future_sprint.endDate = "2025-03-03T17:00:00.000Z"
    mock_future_sprint.goal = "Implement new features"
    
    mock_active_sprint = Mock()
    mock_active_sprint.id = 789
    mock_active_sprint.name = "Sprint 3"
    mock_active_sprint.state = "active"
    mock_active_sprint.startDate = "2025-02-17T09:00:00.000Z"
    mock_active_sprint.endDate = "2025-03-03T17:00:00.000Z"
    mock_active_sprint.goal = "Implement new features"
    
    # Configure mock client
    mock_instance = mock_jira_client.return_value
    mock_instance.create_sprint.return_value = mock_created_sprint
    mock_instance.sprint.side_effect = [mock_future_sprint, mock_active_sprint]
    mock_instance.update_sprint.return_value = None
    mock_instance.add_issues_to_sprint.return_value = None
    
    # Execute workflow
    # 1. Create sprint
    created = jira_client.create_sprint(
        name="Sprint 3",
        goal="Implement new features",
        start_date="2025-02-17T09:00:00.000Z",
        end_date="2025-03-03T17:00:00.000Z"
    )
    assert created["id"] == 789
    assert created["state"] == "future"
    
    # 2. Add issues to sprint
    jira_client.add_issues_to_sprint(789, ["TEST-1", "TEST-2", "TEST-3"])
    
    # 3. Start sprint
    result = jira_client.start_sprint(789)
    
    # Verify final state
    assert result["id"] == 789
    assert result["state"] == "active"
    assert result["name"] == "Sprint 3"
    
    # Verify all calls were made
    mock_instance.create_sprint.assert_called_once()
    mock_instance.add_issues_to_sprint.assert_called_once_with(789, ["TEST-1", "TEST-2", "TEST-3"])
    mock_instance.update_sprint.assert_called_once_with(789, state="active")
