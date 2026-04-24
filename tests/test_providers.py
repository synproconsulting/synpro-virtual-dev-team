"""Tests for data provider implementations."""

import pytest
from unittest.mock import Mock, patch

from src.auth.jira_provider import JiraProvider
from src.auth.pr_provider import PRProvider
from src.auth.ci_provider import CIProvider
from src.auth.sprint_dashboard import IntegrationStatus


def test_jira_provider_initialization() -> None:
    """Test Jira provider initialization."""
    provider = JiraProvider(
        base_url="https://jira.example.com",
        api_token="token123",
        email="user@example.com",
    )
    assert provider.base_url == "https://jira.example.com"
    assert provider.api_token == "token123"
    assert provider.email == "user@example.com"


def test_jira_provider_fetch_data_no_sprint_id() -> None:
    """Test Jira provider raises error without sprint_id."""
    provider = JiraProvider()
    with pytest.raises(ValueError, match="sprint_id is required"):
        provider.fetch_data()


def test_pr_provider_initialization() -> None:
    """Test PR provider initialization."""
    provider = PRProvider(token="ghp_token", repository="owner/repo")
    assert provider.token == "ghp_token"
    assert provider.repository == "owner/repo"


def test_pr_provider_extract_jira_keys() -> None:
    """Test extracting Jira keys from text."""
    provider = PRProvider()
    text = "This PR fixes SDT-123 and SDT-456"
    keys = provider._extract_jira_keys(text)
    assert keys == ["SDT-123", "SDT-456"]


def test_pr_provider_get_pr_status() -> None:
    """Test PR status determination."""
    provider = PRProvider()
    
    merged_pr = {"merged_at": "2024-01-01", "state": "closed"}
    assert provider._get_pr_status(merged_pr) == "merged"
    
    closed_pr = {"merged_at": None, "state": "closed"}
    assert provider._get_pr_status(closed_pr) == "closed"
    
    draft_pr = {"merged_at": None, "state": "open", "draft": True}
    assert provider._get_pr_status(draft_pr) == "draft"
    
    open_pr = {"merged_at": None, "state": "open", "draft": False}
    assert provider._get_pr_status(open_pr) == "open"


def test_ci_provider_initialization() -> None:
    """Test CI provider initialization."""
    provider = CIProvider(token="ghp_token", repository="owner/repo")
    assert provider.token == "ghp_token"
    assert provider.repository == "owner/repo"


def test_ci_provider_map_status() -> None:
    """Test mapping CI conclusions to status."""
    provider = CIProvider()
    
    assert provider._map_status("success") == IntegrationStatus.SUCCESS
    assert provider._map_status("failure") == IntegrationStatus.FAILURE
    assert provider._map_status("cancelled") == IntegrationStatus.FAILURE
    assert provider._map_status(None) == IntegrationStatus.PENDING
    assert provider._map_status("unknown") == IntegrationStatus.UNKNOWN


def test_ci_provider_extract_pr_number() -> None:
    """Test extracting PR number from workflow run."""
    provider = CIProvider()
    
    run_with_pr = {"pull_requests": [{"number": 42}]}
    assert provider._extract_pr_number(run_with_pr) == "42"
    
    run_without_pr = {"pull_requests": []}
    assert provider._extract_pr_number(run_without_pr) is None
