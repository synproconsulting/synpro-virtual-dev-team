"""Tests for Jira provider."""

import pytest
from unittest.mock import Mock, patch
from src.auth.jira_provider import JiraProvider
from src.auth.sprint_dashboard import JiraTicket


@pytest.fixture
def mock_response():
    """Create mock Jira API response."""
    return {
        "issues": [
            {
                "key": "TEST-1",
                "fields": {
                    "summary": "Test ticket",
                    "status": {"name": "Done"},
                    "assignee": {"displayName": "John Doe"},
                    "customfield_10016": 5
                }
            },
            {
                "key": "TEST-2",
                "fields": {
                    "summary": "Another ticket",
                    "status": {"name": "In Progress"},
                    "assignee": None,
                    "customfield_10016": None
                }
            }
        ]
    }


def test_jira_provider_initialization():
    """Test Jira provider initialization."""
    provider = JiraProvider(base_url="https://jira.example.com", api_token="token", email="test@example.com")
    assert provider._base_url == "https://jira.example.com"
    assert provider._api_token == "token"
    assert provider._email == "test@example.com"


@patch('src.auth.jira_provider.requests.Session')
def test_fetch_data_success(mock_session_class, mock_response):
    """Test successful data fetch."""
    mock_session = Mock()
    mock_session_class.return_value = mock_session
    mock_session.get.return_value.json.return_value = mock_response
    mock_session.get.return_value.raise_for_status = Mock()
    
    provider = JiraProvider(base_url="https://jira.example.com", api_token="token", email="test@example.com")
    tickets = provider.fetch_data(sprint_id="123")
    
    assert len(tickets) == 2
    assert tickets[0].key == "TEST-1"
    assert tickets[0].summary == "Test ticket"
    assert tickets[0].status == "Done"
    assert tickets[0].assignee == "John Doe"
    assert tickets[0].story_points == 5
    assert tickets[1].assignee is None
    assert tickets[1].story_points is None


def test_fetch_data_missing_sprint_id():
    """Test fetch data without sprint_id."""
    provider = JiraProvider()
    with pytest.raises(ValueError, match="sprint_id is required"):
        provider.fetch_data()
