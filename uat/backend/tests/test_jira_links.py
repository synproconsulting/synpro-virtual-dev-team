"""
Tests for Jira issue link functionality (blocks/is-blocked-by).
"""

import os
from unittest.mock import MagicMock, Mock, patch
import pytest
from tools import jira_client


@pytest.fixture
def mock_jira():
    """Mock JIRA client for testing."""
    with patch("tools.jira_client.JIRA") as mock_jira_class:
        mock_instance = MagicMock()
        mock_jira_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("JIRA_URL", "https://test.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "test@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
    monkeypatch.setenv("JIRA_PROJECT_KEY", "TEST")
    monkeypatch.setenv("JIRA_BOARD_ID", "123")


class TestCreateIssueLink:
    """Test suite for creating issue links."""
    
    def test_create_blocks_link(self, mock_jira, mock_env):
        """Test creating a 'blocks' link between two issues."""
        # Reset the singleton
        if hasattr(jira_client._get_client, "_instance"):
            delattr(jira_client._get_client, "_instance")
        
        blocker_key = "TEST-1"
        blocked_key = "TEST-2"
        
        jira_client.create_issue_link(
            inward_issue_key=blocked_key,
            outward_issue_key=blocker_key,
            link_type="Blocks"
        )
        
        mock_jira.create_issue_link.assert_called_once_with(
            type="Blocks",
            inwardIssue=blocked_key,
            outwardIssue=blocker_key,
        )
    
    def test_create_link_with_custom_type(self, mock_jira, mock_env):
        """Test creating a link with a custom link type."""
        # Reset the singleton
        if hasattr(jira_client._get_client, "_instance"):
            delattr(jira_client._get_client, "_instance")
        
        issue_a = "TEST-10"
        issue_b = "TEST-20"
        
        jira_client.create_issue_link(
            inward_issue_key=issue_a,
            outward_issue_key=issue_b,
            link_type="Relates"
        )
        
        mock_jira.create_issue_link.assert_called_once_with(
            type="Relates",
            inwardIssue=issue_a,
            outwardIssue=issue_b,
        )


class TestListIssueLinks:
    """Test suite for listing issue links."""
    
    def test_list_links_with_outward_link(self, mock_jira, mock_env):
        """Test listing links when issue has an outward link."""
        # Reset the singleton
        if hasattr(jira_client._get_client, "_instance"):
            delattr(jira_client._get_client, "_instance")
        
        # Mock issue with outward link
        mock_issue = Mock()
        mock_link = Mock()
        mock_link.type.name = "Blocks"
        mock_link.type.outward = "blocks"
        mock_link.outwardIssue.key = "TEST-2"
        
        # No inward issue
        delattr(mock_link, "inwardIssue")
        mock_issue.fields.issuelinks = [mock_link]
        
        mock_jira.issue.return_value = mock_issue
        
        links = jira_client.list_issue_links("TEST-1")
        
        assert len(links) == 1
        assert links[0]["link_type"] == "Blocks"
        assert links[0]["direction"] == "outward"
        assert links[0]["related_issue"] == "TEST-2"
        assert links[0]["relationship"] == "blocks"
    
    def test_list_links_with_inward_link(self, mock_jira, mock_env):
        """Test listing links when issue has an inward link."""
        # Reset the singleton
        if hasattr(jira_client._get_client, "_instance"):
            delattr(jira_client._get_client, "_instance")
        
        # Mock issue with inward link
        mock_issue = Mock()
        mock_link = Mock()
        mock_link.type.name = "Blocks"
        mock_link.type.inward = "is blocked by"
        mock_link.inwardIssue.key = "TEST-1"
        
        # No outward issue
        delattr(mock_link, "outwardIssue")
        mock_issue.fields.issuelinks = [mock_link]
        
        mock_jira.issue.return_value = mock_issue
        
        links = jira_client.list_issue_links("TEST-2")
        
        assert len(links) == 1
        assert links[0]["link_type"] == "Blocks"
        assert links[0]["direction"] == "inward"
        assert links[0]["related_issue"] == "TEST-1"
        assert links[0]["relationship"] == "is blocked by"
    
    def test_list_links_with_multiple_links(self, mock_jira, mock_env):
        """Test listing links when issue has multiple links."""
        # Reset the singleton
        if hasattr(jira_client._get_client, "_instance"):
            delattr(jira_client._get_client, "_instance")
        
        # Mock issue with both inward and outward links
        mock_issue = Mock()
        
        mock_link1 = Mock()
        mock_link1.type.name = "Blocks"
        mock_link1.type.outward = "blocks"
        mock_link1.outwardIssue.key = "TEST-3"
        delattr(mock_link1, "inwardIssue")
        
        mock_link2 = Mock()
        mock_link2.type.name = "Blocks"
        mock_link2.type.inward = "is blocked by"
        mock_link2.inwardIssue.key = "TEST-1"
        delattr(mock_link2, "outwardIssue")
        
        mock_link3 = Mock()
        mock_link3.type.name = "Relates"
        mock_link3.type.outward = "relates to"
        mock_link3.outwardIssue.key = "TEST-4"
        delattr(mock_link3, "inwardIssue")
        
        mock_issue.fields.issuelinks = [mock_link1, mock_link2, mock_link3]
        
        mock_jira.issue.return_value = mock_issue
        
        links = jira_client.list_issue_links("TEST-2")
        
        assert len(links) == 3
        
        # Check first link
        assert links[0]["link_type"] == "Blocks"
        assert links[0]["direction"] == "outward"
        assert links[0]["related_issue"] == "TEST-3"
        
        # Check second link
        assert links[1]["link_type"] == "Blocks"
        assert links[1]["direction"] == "inward"
        assert links[1]["related_issue"] == "TEST-1"
        
        # Check third link
        assert links[2]["link_type"] == "Relates"
        assert links[2]["direction"] == "outward"
        assert links[2]["related_issue"] == "TEST-4"
    
    def test_list_links_with_no_links(self, mock_jira, mock_env):
        """Test listing links when issue has no links."""
        # Reset the singleton
        if hasattr(jira_client._get_client, "_instance"):
            delattr(jira_client._get_client, "_instance")
        
        # Mock issue with no links
        mock_issue = Mock()
        mock_issue.fields.issuelinks = []
        
        mock_jira.issue.return_value = mock_issue
        
        links = jira_client.list_issue_links("TEST-5")
        
        assert len(links) == 0


class TestJiraClientEnvironment:
    """Test environment variable handling."""
    
    def test_missing_jira_url(self, monkeypatch):
        """Test that missing JIRA_URL raises an error."""
        # Reset the singleton
        if hasattr(jira_client._get_client, "_instance"):
            delattr(jira_client._get_client, "_instance")
        
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.setenv("JIRA_EMAIL", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        
        with pytest.raises(ValueError, match="Missing required Jira environment variables"):
            jira_client._get_client()
    
    def test_missing_project_key(self, monkeypatch):
        """Test that missing JIRA_PROJECT_KEY raises an error."""
        monkeypatch.delenv("JIRA_PROJECT_KEY", raising=False)
        
        with pytest.raises(ValueError, match="JIRA_PROJECT_KEY environment variable not set"):
            jira_client._get_project_key()
    
    def test_missing_board_id(self, monkeypatch):
        """Test that missing JIRA_BOARD_ID raises an error."""
        monkeypatch.delenv("JIRA_BOARD_ID", raising=False)
        
        with pytest.raises(ValueError, match="JIRA_BOARD_ID environment variable not set"):
            jira_client._get_board_id()


class TestJiraClientConnection:
    """Test Jira client connection handling."""
    
    def test_singleton_connection(self, mock_env):
        """Test that _get_client returns a singleton instance."""
        # Reset the singleton
        if hasattr(jira_client._get_client, "_instance"):
            delattr(jira_client._get_client, "_instance")
        
        with patch("tools.jira_client.JIRA") as mock_jira_class:
            mock_instance1 = MagicMock()
            mock_jira_class.return_value = mock_instance1
            
            client1 = jira_client._get_client()
            client2 = jira_client._get_client()
            
            # Should only create one instance
            assert mock_jira_class.call_count == 1
            assert client1 is client2
