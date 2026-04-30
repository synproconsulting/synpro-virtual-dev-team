"""
Tests for PM Agent tools, focusing on issue link functionality.
"""

from unittest.mock import MagicMock, patch, Mock
import pytest
from tools.pm_tools import (
    CreateBlockerLinkTool,
    ListIssueLinksToolImpl,
)


@pytest.fixture
def mock_jira_client():
    """Mock the jira_client module."""
    with patch("tools.pm_tools.jira") as mock:
        yield mock


class TestCreateBlockerLinkTool:
    """Test suite for CreateBlockerLinkTool."""
    
    def test_create_blocker_link_success(self, mock_jira_client):
        """Test successfully creating a blocker link."""
        tool = CreateBlockerLinkTool()
        
        blocker = "TEST-1"
        blocked = "TEST-2"
        
        result = tool._run(blocker_issue_key=blocker, blocked_issue_key=blocked)
        
        # Verify the jira_client was called with correct parameters
        mock_jira_client.create_issue_link.assert_called_once_with(
            inward_issue_key=blocked,
            outward_issue_key=blocker,
            link_type="Blocks"
        )
        
        # Verify the result message
        assert blocker in result
        assert blocked in result
        assert "blocks" in result
    
    def test_create_blocker_link_with_different_keys(self, mock_jira_client):
        """Test creating blocker link with different issue keys."""
        tool = CreateBlockerLinkTool()
        
        blocker = "PROJ-100"
        blocked = "PROJ-200"
        
        result = tool._run(blocker_issue_key=blocker, blocked_issue_key=blocked)
        
        mock_jira_client.create_issue_link.assert_called_once_with(
            inward_issue_key=blocked,
            outward_issue_key=blocker,
            link_type="Blocks"
        )
        
        assert "PROJ-100" in result
        assert "PROJ-200" in result


class TestListIssueLinksToolImpl:
    """Test suite for ListIssueLinksToolImpl."""
    
    def test_list_links_with_no_links(self, mock_jira_client):
        """Test listing links when issue has no links."""
        tool = ListIssueLinksToolImpl()
        
        mock_jira_client.list_issue_links.return_value = []
        
        result = tool._run(issue_key="TEST-1")
        
        mock_jira_client.list_issue_links.assert_called_once_with("TEST-1")
        assert "No links found" in result
        assert "TEST-1" in result
    
    def test_list_links_with_single_link(self, mock_jira_client):
        """Test listing links when issue has one link."""
        tool = ListIssueLinksToolImpl()
        
        mock_links = [
            {
                "link_type": "Blocks",
                "direction": "outward",
                "related_issue": "TEST-2",
                "relationship": "blocks"
            }
        ]
        mock_jira_client.list_issue_links.return_value = mock_links
        
        result = tool._run(issue_key="TEST-1")
        
        mock_jira_client.list_issue_links.assert_called_once_with("TEST-1")
        assert "TEST-1" in result
        assert "blocks" in result
        assert "TEST-2" in result
        assert "Blocks" in result
    
    def test_list_links_with_multiple_links(self, mock_jira_client):
        """Test listing links when issue has multiple links."""
        tool = ListIssueLinksToolImpl()
        
        mock_links = [
            {
                "link_type": "Blocks",
                "direction": "outward",
                "related_issue": "TEST-2",
                "relationship": "blocks"
            },
            {
                "link_type": "Blocks",
                "direction": "inward",
                "related_issue": "TEST-0",
                "relationship": "is blocked by"
            },
            {
                "link_type": "Relates",
                "direction": "outward",
                "related_issue": "TEST-3",
                "relationship": "relates to"
            }
        ]
        mock_jira_client.list_issue_links.return_value = mock_links
        
        result = tool._run(issue_key="TEST-1")
        
        mock_jira_client.list_issue_links.assert_called_once_with("TEST-1")
        
        # Verify all links are in the result
        assert "TEST-2" in result
        assert "TEST-0" in result
        assert "TEST-3" in result
        assert "blocks" in result
        assert "is blocked by" in result
        assert "relates to" in result
    
    def test_list_links_formats_correctly(self, mock_jira_client):
        """Test that link formatting is correct."""
        tool = ListIssueLinksToolImpl()
        
        mock_links = [
            {
                "link_type": "Blocks",
                "direction": "inward",
                "related_issue": "TEST-100",
                "relationship": "is blocked by"
            }
        ]
        mock_jira_client.list_issue_links.return_value = mock_links
        
        result = tool._run(issue_key="TEST-200")
        
        # Check the formatting includes all expected parts
        lines = result.split("\n")
        assert len(lines) == 2  # Header + 1 link
        assert lines[0] == "Links for TEST-200:"
        assert "is blocked by" in lines[1]
        assert "TEST-100" in lines[1]
        assert "Blocks" in lines[1]


class TestToolMetadata:
    """Test tool metadata (names, descriptions, schemas)."""
    
    def test_create_blocker_link_tool_metadata(self):
        """Test CreateBlockerLinkTool has correct metadata."""
        tool = CreateBlockerLinkTool()
        
        assert tool.name == "create_blocker_link"
        assert "blocks" in tool.description.lower()
        assert "dependencies" in tool.description.lower()
        
        # Verify schema has correct fields
        schema = tool.args_schema
        assert hasattr(schema, "blocker_issue_key")
        assert hasattr(schema, "blocked_issue_key")
    
    def test_list_issue_links_tool_metadata(self):
        """Test ListIssueLinksToolImpl has correct metadata."""
        tool = ListIssueLinksToolImpl()
        
        assert tool.name == "list_issue_links"
        assert "links" in tool.description.lower()
        assert "blocks" in tool.description.lower()
        
        # Verify schema has correct fields
        schema = tool.args_schema
        assert hasattr(schema, "issue_key")


class TestToolIntegration:
    """Integration tests for tools working together."""
    
    def test_create_and_list_workflow(self, mock_jira_client):
        """Test the workflow of creating a link then listing it."""
        create_tool = CreateBlockerLinkTool()
        list_tool = ListIssueLinksToolImpl()
        
        # Create a blocker link
        blocker = "TEST-1"
        blocked = "TEST-2"
        create_tool._run(blocker_issue_key=blocker, blocked_issue_key=blocked)
        
        # Mock the list response to show the link was created
        mock_links = [
            {
                "link_type": "Blocks",
                "direction": "inward",
                "related_issue": blocker,
                "relationship": "is blocked by"
            }
        ]
        mock_jira_client.list_issue_links.return_value = mock_links
        
        # List links for the blocked issue
        result = list_tool._run(issue_key=blocked)
        
        # Verify both issues appear in the result
        assert blocker in result
        assert blocked in result
        assert "is blocked by" in result
