"""Tests for PR provider."""

import pytest
from unittest.mock import Mock, patch
from src.auth.pr_provider import PRProvider
from src.auth.sprint_dashboard import StatusType


@pytest.fixture
def mock_pr_response():
    """Create mock GitHub PR API response."""
    return [
        {
            "number": 1,
            "title": "[SDT-1] Fix bug",
            "body": "Fixes SDT-1",
            "user": {"login": "alice"},
            "state": "closed",
            "merged": True,
            "html_url": "https://github.com/repo/pull/1"
        },
        {
            "number": 2,
            "title": "Add feature",
            "body": "Related to SDT-2 and SDT-3",
            "user": {"login": "bob"},
            "state": "open",
            "merged": False,
            "html_url": "https://github.com/repo/pull/2"
        }
    ]


def test_pr_provider_initialization():
    """Test PR provider initialization."""
    provider = PRProvider(token="ghp_token", repo="owner/repo")
    assert provider._token == "ghp_token"
    assert provider._repo == "owner/repo"


@patch('src.auth.pr_provider.requests.Session')
def test_fetch_data_success(mock_session_class, mock_pr_response):
    """Test successful PR data fetch."""
    mock_session = Mock()
    mock_session_class.return_value = mock_session
    mock_session.get.return_value.json.return_value = mock_pr_response
    mock_session.get.return_value.raise_for_status = Mock()
    
    provider = PRProvider(token="token", repo="owner/repo")
    prs = provider.fetch_data()
    
    assert len(prs) == 2
    assert prs[0].id == "1"
    assert prs[0].title == "[SDT-1] Fix bug"
    assert prs[0].status == StatusType.SUCCESS
    assert "SDT-1" in prs[0].jira_keys
    assert len(prs[1].jira_keys) == 2
    assert "SDT-2" in prs[1].jira_keys
    assert "SDT-3" in prs[1].jira_keys


def test_extract_jira_keys():
    """Test Jira key extraction."""
    provider = PRProvider()
    text = "This fixes ABC-123 and XYZ-456. Also relates to DEF-789."
    keys = provider._extract_jira_keys(text)
    
    assert len(keys) == 3
    assert "ABC-123" in keys
    assert "XYZ-456" in keys
    assert "DEF-789" in keys


def test_map_pr_status():
    """Test PR status mapping."""
    provider = PRProvider()
    
    assert provider._map_pr_status({"merged": True, "state": "closed"}) == StatusType.SUCCESS
    assert provider._map_pr_status({"merged": False, "state": "closed"}) == StatusType.FAILED
    assert provider._map_pr_status({"merged": False, "state": "open"}) == StatusType.PENDING
