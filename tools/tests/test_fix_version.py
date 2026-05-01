"""
tools/tests/test_fix_version.py
────────────────────────────────
Unit tests for fix version management in jira_client and pm_tools.

These tests use mocking to avoid actual Jira API calls.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from tools import jira_client
from tools.pm_tools import CreateOrGetFixVersionTool, ListFixVersionsTool


class MockVersion:
    """Mock Jira Version object."""
    
    def __init__(self, id: str, name: str, description: str = "",
                 archived: bool = False, released: bool = False,
                 release_date: str = None):
        self.id = id
        self.name = name
        self.description = description
        self.archived = archived
        self.released = released
        self.releaseDate = release_date


class TestCreateOrGetFixVersion:
    """Test suite for create_or_get_fix_version function."""
    
    @patch('tools.jira_client._get_client')
    @patch('tools.jira_client._get_project_key')
    def test_create_new_version(self, mock_get_key, mock_get_client):
        """Test creating a new fix version when none exists."""
        # Setup
        mock_get_key.return_value = "TEST"
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        mock_project = Mock()
        mock_jira.project.return_value = mock_project
        mock_jira.project_versions.return_value = []
        
        # Mock the created version
        new_version = MockVersion(
            id="12345",
            name="v1.0.0",
            description="First release",
            release_date="2025-12-31"
        )
        mock_jira.create_version.return_value = new_version
        
        # Execute
        result = jira_client.create_or_get_fix_version(
            name="v1.0.0",
            description="First release",
            release_date="2025-12-31"
        )
        
        # Assert
        assert result["id"] == "12345"
        assert result["name"] == "v1.0.0"
        assert result["description"] == "First release"
        assert result["release_date"] == "2025-12-31"
        assert result["created"] is True
        assert result["archived"] is False
        assert result["released"] is False
        
        # Verify create_version was called
        mock_jira.create_version.assert_called_once_with(
            name="v1.0.0",
            project="TEST",
            description="First release",
            releaseDate="2025-12-31",
            archived=False,
            released=False
        )
    
    @patch('tools.jira_client._get_client')
    @patch('tools.jira_client._get_project_key')
    def test_get_existing_version(self, mock_get_key, mock_get_client):
        """Test retrieving an existing fix version."""
        # Setup
        mock_get_key.return_value = "TEST"
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        mock_project = Mock()
        mock_jira.project.return_value = mock_project
        
        # Mock existing versions
        existing_version = MockVersion(
            id="99999",
            name="v1.0.0",
            description="Existing release"
        )
        mock_jira.project_versions.return_value = [existing_version]
        
        # Execute
        result = jira_client.create_or_get_fix_version(
            name="v1.0.0",
            description="Should be ignored"
        )
        
        # Assert
        assert result["id"] == "99999"
        assert result["name"] == "v1.0.0"
        assert result["description"] == "Existing release"
        assert result["created"] is False
        
        # Verify create_version was NOT called
        mock_jira.create_version.assert_not_called()
    
    @patch('tools.jira_client._get_client')
    @patch('tools.jira_client._get_project_key')
    def test_idempotent_multiple_calls(self, mock_get_key, mock_get_client):
        """Test that multiple calls with the same name return the same version."""
        # Setup
        mock_get_key.return_value = "TEST"
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        mock_project = Mock()
        mock_jira.project.return_value = mock_project
        
        # First call - no existing versions
        mock_jira.project_versions.return_value = []
        new_version = MockVersion(id="12345", name="v2.0.0")
        mock_jira.create_version.return_value = new_version
        
        result1 = jira_client.create_or_get_fix_version(name="v2.0.0")
        
        # Second call - now version exists
        mock_jira.project_versions.return_value = [new_version]
        result2 = jira_client.create_or_get_fix_version(name="v2.0.0")
        
        # Assert both return same ID
        assert result1["id"] == result2["id"]
        assert result1["created"] is True
        assert result2["created"] is False
        
        # create_version should only be called once
        assert mock_jira.create_version.call_count == 1
    
    @patch('tools.jira_client._get_client')
    @patch('tools.jira_client._get_project_key')
    def test_create_with_all_parameters(self, mock_get_key, mock_get_client):
        """Test creating a version with all optional parameters."""
        # Setup
        mock_get_key.return_value = "TEST"
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        mock_project = Mock()
        mock_jira.project.return_value = mock_project
        mock_jira.project_versions.return_value = []
        
        new_version = MockVersion(
            id="54321",
            name="v1.5.0",
            description="Hotfix release",
            archived=True,
            released=True,
            release_date="2025-06-15"
        )
        mock_jira.create_version.return_value = new_version
        
        # Execute
        result = jira_client.create_or_get_fix_version(
            name="v1.5.0",
            description="Hotfix release",
            release_date="2025-06-15",
            archived=True,
            released=True
        )
        
        # Assert
        assert result["id"] == "54321"
        assert result["archived"] is True
        assert result["released"] is True
        
        mock_jira.create_version.assert_called_once_with(
            name="v1.5.0",
            project="TEST",
            description="Hotfix release",
            releaseDate="2025-06-15",
            archived=True,
            released=True
        )
    
    @patch('tools.jira_client._get_client')
    @patch('tools.jira_client._get_project_key')
    def test_multiple_versions_returns_correct_one(self, mock_get_key, mock_get_client):
        """Test that the correct version is returned when multiple exist."""
        # Setup
        mock_get_key.return_value = "TEST"
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        mock_project = Mock()
        mock_jira.project.return_value = mock_project
        
        # Mock multiple existing versions
        versions = [
            MockVersion(id="100", name="v1.0.0"),
            MockVersion(id="200", name="v2.0.0"),
            MockVersion(id="300", name="v3.0.0"),
        ]
        mock_jira.project_versions.return_value = versions
        
        # Execute - request v2.0.0
        result = jira_client.create_or_get_fix_version(name="v2.0.0")
        
        # Assert correct version returned
        assert result["id"] == "200"
        assert result["name"] == "v2.0.0"
        assert result["created"] is False


class TestListFixVersions:
    """Test suite for list_fix_versions function."""
    
    @patch('tools.jira_client._get_client')
    @patch('tools.jira_client._get_project_key')
    def test_list_all_unreleased_versions(self, mock_get_key, mock_get_client):
        """Test listing unreleased versions."""
        # Setup
        mock_get_key.return_value = "TEST"
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        mock_project = Mock()
        mock_jira.project.return_value = mock_project
        
        versions = [
            MockVersion(id="1", name="v1.0.0", released=False, archived=False),
            MockVersion(id="2", name="v2.0.0", released=False, archived=False),
        ]
        mock_jira.project_versions.return_value = versions
        
        # Execute
        result = jira_client.list_fix_versions(
            include_archived=False,
            include_released=True
        )
        
        # Assert
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"
    
    @patch('tools.jira_client._get_client')
    @patch('tools.jira_client._get_project_key')
    def test_filter_archived_versions(self, mock_get_key, mock_get_client):
        """Test filtering out archived versions."""
        # Setup
        mock_get_key.return_value = "TEST"
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        mock_project = Mock()
        mock_jira.project.return_value = mock_project
        
        versions = [
            MockVersion(id="1", name="v1.0.0", archived=False),
            MockVersion(id="2", name="v2.0.0", archived=True),
            MockVersion(id="3", name="v3.0.0", archived=False),
        ]
        mock_jira.project_versions.return_value = versions
        
        # Execute - exclude archived
        result = jira_client.list_fix_versions(include_archived=False)
        
        # Assert
        assert len(result) == 2
        assert all(not v["archived"] for v in result)
    
    @patch('tools.jira_client._get_client')
    @patch('tools.jira_client._get_project_key')
    def test_filter_released_versions(self, mock_get_key, mock_get_client):
        """Test filtering out released versions."""
        # Setup
        mock_get_key.return_value = "TEST"
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        mock_project = Mock()
        mock_jira.project.return_value = mock_project
        
        versions = [
            MockVersion(id="1", name="v1.0.0", released=True),
            MockVersion(id="2", name="v2.0.0", released=False),
            MockVersion(id="3", name="v3.0.0", released=True),
        ]
        mock_jira.project_versions.return_value = versions
        
        # Execute - exclude released
        result = jira_client.list_fix_versions(include_released=False)
        
        # Assert
        assert len(result) == 1
        assert result[0]["id"] == "2"
        assert result[0]["released"] is False
    
    @patch('tools.jira_client._get_client')
    @patch('tools.jira_client._get_project_key')
    def test_list_empty_project(self, mock_get_key, mock_get_client):
        """Test listing versions when project has none."""
        # Setup
        mock_get_key.return_value = "TEST"
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        mock_project = Mock()
        mock_jira.project.return_value = mock_project
        mock_jira.project_versions.return_value = []
        
        # Execute
        result = jira_client.list_fix_versions()
        
        # Assert
        assert result == []


class TestCreateOrGetFixVersionTool:
    """Test suite for the CrewAI tool wrapper."""
    
    @patch('tools.pm_tools.jira.create_or_get_fix_version')
    def test_tool_creates_new_version(self, mock_create):
        """Test the tool wrapper for creating a new version."""
        # Setup
        mock_create.return_value = {
            "id": "12345",
            "name": "Sprint 1",
            "description": "First sprint release",
            "release_date": "2025-02-01",
            "archived": False,
            "released": False,
            "created": True
        }
        
        tool = CreateOrGetFixVersionTool()
        
        # Execute
        result = tool._run(
            name="Sprint 1",
            description="First sprint release",
            release_date="2025-02-01"
        )
        
        # Assert
        assert "Sprint 1" in result
        assert "12345" in result
        assert "created" in result
        assert "First sprint release" in result
        assert "2025-02-01" in result
        
        mock_create.assert_called_once_with(
            name="Sprint 1",
            description="First sprint release",
            release_date="2025-02-01",
            archived=False,
            released=False
        )
    
    @patch('tools.pm_tools.jira.create_or_get_fix_version')
    def test_tool_gets_existing_version(self, mock_create):
        """Test the tool wrapper for retrieving existing version."""
        # Setup
        mock_create.return_value = {
            "id": "99999",
            "name": "Sprint 1",
            "description": "First sprint release",
            "release_date": None,
            "archived": False,
            "released": False,
            "created": False
        }
        
        tool = CreateOrGetFixVersionTool()
        
        # Execute
        result = tool._run(name="Sprint 1")
        
        # Assert
        assert "Sprint 1" in result
        assert "99999" in result
        assert "found existing" in result or "existing" in result.lower()


class TestListFixVersionsTool:
    """Test suite for the ListFixVersions CrewAI tool."""
    
    @patch('tools.pm_tools.jira.list_fix_versions')
    def test_tool_lists_versions(self, mock_list):
        """Test the tool wrapper for listing versions."""
        # Setup
        mock_list.return_value = [
            {
                "id": "1",
                "name": "v1.0.0",
                "description": "First release",
                "release_date": "2025-01-01",
                "archived": False,
                "released": False
            },
            {
                "id": "2",
                "name": "v2.0.0",
                "description": "Second release",
                "release_date": None,
                "archived": False,
                "released": True
            }
        ]
        
        tool = ListFixVersionsTool()
        
        # Execute
        result = tool._run(include_archived=False, include_released=True)
        
        # Assert
        assert "v1.0.0" in result
        assert "v2.0.0" in result
        assert "First release" in result
        assert "Released" in result
        
        mock_list.assert_called_once_with(
            include_archived=False,
            include_released=True
        )
    
    @patch('tools.pm_tools.jira.list_fix_versions')
    def test_tool_handles_empty_list(self, mock_list):
        """Test the tool wrapper when no versions exist."""
        # Setup
        mock_list.return_value = []
        
        tool = ListFixVersionsTool()
        
        # Execute
        result = tool._run()
        
        # Assert
        assert "No fix versions found" in result


class TestDeterministicBehavior:
    """Integration-style tests for deterministic ID behavior."""
    
    @patch('tools.jira_client._get_client')
    @patch('tools.jira_client._get_project_key')
    def test_same_name_returns_same_id(self, mock_get_key, mock_get_client):
        """Test that requesting the same version name always returns same ID."""
        # Setup
        mock_get_key.return_value = "TEST"
        mock_jira = Mock()
        mock_get_client.return_value = mock_jira
        
        mock_project = Mock()
        mock_jira.project.return_value = mock_project
        
        # First call - create version
        mock_jira.project_versions.return_value = []
        version = MockVersion(id="DETERMINISTIC_ID", name="Release 1.0")
        mock_jira.create_version.return_value = version
        
        result1 = jira_client.create_or_get_fix_version(name="Release 1.0")
        
        # Second call - version now exists
        mock_jira.project_versions.return_value = [version]
        result2 = jira_client.create_or_get_fix_version(name="Release 1.0")
        
        # Third call - still same version
        result3 = jira_client.create_or_get_fix_version(name="Release 1.0")
        
        # Assert all calls return same ID
        assert result1["id"] == "DETERMINISTIC_ID"
        assert result2["id"] == "DETERMINISTIC_ID"
        assert result3["id"] == "DETERMINISTIC_ID"
        
        # Only created once
        assert mock_jira.create_version.call_count == 1
