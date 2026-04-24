"""Tests for CI provider."""

import pytest
from unittest.mock import Mock, patch
from src.auth.ci_provider import CIProvider
from src.auth.sprint_dashboard import StatusType


@pytest.fixture
def mock_ci_response():
    """Create mock GitHub Actions API response."""
    return {
        "workflow_runs": [
            {
                "id": 12345,
                "status": "completed",
                "conclusion": "success",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:05:00Z",
                "pull_requests": [{"number": 1}]
            },
            {
                "id": 12346,
                "status": "in_progress",
                "conclusion": None,
                "created_at": "2024-01-15T11:00:00Z",
                "updated_at": None,
                "pull_requests": []
            },
            {
                "id": 12347,
                "status": "completed",
                "conclusion": "failure",
                "created_at": "2024-01-15T12:00:00Z",
                "updated_at": "2024-01-15T12:10:00Z",
                "pull_requests": [{"number": 2}]
            }
        ]
    }


def test_ci_provider_initialization():
    """Test CI provider initialization."""
    provider = CIProvider(token="ghp_token", repo="owner/repo")
    assert provider._token == "ghp_token"
    assert provider._repo == "owner/repo"


@patch('src.auth.ci_provider.requests.Session')
def test_fetch_data_success(mock_session_class, mock_ci_response):
    """Test successful CI data fetch."""
    mock_session = Mock()
    mock_session_class.return_value = mock_session
    mock_session.get.return_value.json.return_value = mock_ci_response
    mock_session.get.return_value.raise_for_status = Mock()
    
    provider = CIProvider(token="token", repo="owner/repo")
    builds = provider.fetch_data()
    
    assert len(builds) == 3
    assert builds[0].build_id == "12345"
    assert builds[0].status == StatusType.SUCCESS
    assert builds[0].pr_id == "1"
    assert builds[1].status == StatusType.PENDING
    assert builds[1].pr_id is None
    assert builds[2].status == StatusType.FAILED


def test_map_ci_status():
    """Test CI status mapping."""
    provider = CIProvider()
    
    assert provider._map_ci_status("success", "completed") == StatusType.SUCCESS
    assert provider._map_ci_status("failure", "completed") == StatusType.FAILED
    assert provider._map_ci_status(None, "in_progress") == StatusType.PENDING
    assert provider._map_ci_status("cancelled", "completed") == StatusType.FAILED
