"""
tests/test_fix_versions.py
──────────────────────────
Unit tests for fix version management functionality in jira_client and pm_tools.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from tools import jira_client
from tools.pm_tools import CreateOrGetFixVersionTool, ListFixVersionsTool


@pytest.fixture
def mock_jira():
    """Mock the JIRA client."""
    with patch("tools.jira_client._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_project_key():
    """Mock the project key."""
    with patch("tools.jira_client._get_project_key") as mock_get_key:
        mock_get_key.return_value = "TEST"
        yield mock_get_key


class TestListFixVersions:
    """Test listing fix versions."""
    
    def test_list_fix_versions_success(self, mock_jira, mock_project_key):
        """Test successfully listing fix versions."""
        # Create mock versions
        mock_version1 = MagicMock()
        mock_version1.id = "10001"
        mock_version1.name = "v1.0.0"
        mock_version1.description = "First release"
        mock_version1.released = True
        mock_version1.releaseDate = "2025-01-15"
        
        mock_version2 = MagicMock()
        mock_version2.id = "10002"
        mock_version2.name = "v1.1.0"
        mock_version2.description = "Second release"
        mock_version2.released = False
        
        mock_project = MagicMock()
        mock_jira.project.return_value = mock_project
        mock_jira.project_versions.return_value = [mock_version1, mock_version2]
        
        # Call function
        result = jira_client.list_fix_versions()
        
        # Verify
        assert len(result) == 2
        assert result[0]["id"] == "10001"
        assert result[0]["name"] == "v1.0.0"
        assert result[0]["description"] == "First release"
        assert result[0]["released"] is True
        assert result[0]["release_date"] == "2025-01-15"
        
        assert result[1]["id"] == "10002"
        assert result[1]["name"] == "v1.1.0"
        assert result[1]["released"] is False
        
        mock_jira.project.assert_called_once_with("TEST")
        mock_jira.project_versions.assert_called_once()
    
    def test_list_fix_versions_empty(self, mock_jira, mock_project_key):
        """Test listing fix versions when none exist."""
        mock_project = MagicMock()
        mock_jira.project.return_value = mock_project
        mock_jira.project_versions.return_value = []
        
        result = jira_client.list_fix_versions()
        
        assert result == []
        mock_jira.project.assert_called_once_with("TEST")


class TestCreateOrGetFixVersion:
    """Test create or get fix version functionality."""
    
    def test_get_existing_version(self, mock_jira, mock_project_key):
        """Test getting an existing version by name."""
        # Mock existing versions
        mock_version = MagicMock()
        mock_version.id = "10001"
        mock_version.name = "v1.0.0"
        mock_version.description = "Existing version"
        mock_version.released = False
        
        mock_project = MagicMock()
        mock_jira.project.return_value = mock_project
        mock_jira.project_versions.return_value = [mock_version]
        
        # Call function
        result = jira_client.create_or_get_fix_version("v1.0.0")
        
        # Verify it found the existing version
        assert result["id"] == "10001"
        assert result["name"] == "v1.0.0"
        assert result["created"] is False
        
        # Should not have called create_version
        mock_jira.create_version.assert_not_called()
    
    def test_create_new_version_basic(self, mock_jira, mock_project_key):
        """Test creating a new version when it doesn't exist."""
        # Mock no existing versions
        mock_project = MagicMock()
        mock_jira.project.return_value = mock_project
        mock_jira.project_versions.return_value = []
        
        # Mock new version creation
        mock_new_version = MagicMock()
        mock_new_version.id = "10005"
        mock_new_version.name = "v2.0.0"
        mock_jira.create_version.return_value = mock_new_version
        
        # Call function
        result = jira_client.create_or_get_fix_version("v2.0.0")
        
        # Verify new version was created
        assert result["id"] == "10005"
        assert result["name"] == "v2.0.0"
        assert result["created"] is True
        
        # Verify create_version was called correctly
        mock_jira.create_version.assert_called_once()
        call_args = mock_jira.create_version.call_args[1]
        assert call_args["name"] == "v2.0.0"
        assert call_args["project"] == "TEST"
        assert call_args["released"] is False
    
    def test_create_new_version_with_all_fields(self, mock_jira, mock_project_key):
        """Test creating a new version with all optional fields."""
        mock_project = MagicMock()
        mock_jira.project.return_value = mock_project
        mock_jira.project_versions.return_value = []
        
        mock_new_version = MagicMock()
        mock_new_version.id = "10006"
        mock_new_version.name = "v3.0.0"
        mock_jira.create_version.return_value = mock_new_version
        
        # Call function with all fields
        result = jira_client.create_or_get_fix_version(
            name="v3.0.0",
            description="Major release",
            release_date="2025-06-01",
            released=True
        )
        
        # Verify
        assert result["id"] == "10006"
        assert result["name"] == "v3.0.0"
        assert result["created"] is True
        
        # Verify all fields were passed
        call_args = mock_jira.create_version.call_args[1]
        assert call_args["name"] == "v3.0.0"
        assert call_args["description"] == "Major release"
        assert call_args["releaseDate"] == "2025-06-01"
        assert call_args["released"] is True
    
    def test_deterministic_behavior(self, mock_jira, mock_project_key):
        """Test that calling with same name returns same ID (deterministic)."""
        mock_version = MagicMock()
        mock_version.id = "10001"
        mock_version.name = "v1.0.0"
        mock_version.released = False
        
        mock_project = MagicMock()
        mock_jira.project.return_value = mock_project
        mock_jira.project_versions.return_value = [mock_version]
        
        # Call multiple times
        result1 = jira_client.create_or_get_fix_version("v1.0.0")
        result2 = jira_client.create_or_get_fix_version("v1.0.0")
        result3 = jira_client.create_or_get_fix_version("v1.0.0", description="Different description")
        
        # All should return the same ID
        assert result1["id"] == "10001"
        assert result2["id"] == "10001"
        assert result3["id"] == "10001"
        
        assert result1["created"] is False
        assert result2["created"] is False
        assert result3["created"] is False
        
        # Should never have called create_version
        mock_jira.create_version.assert_not_called()


class TestCreateOrGetFixVersionTool:
    """Test the CrewAI tool wrapper for create_or_get_fix_version."""
    
    @patch("tools.pm_tools.jira.create_or_get_fix_version")
    def test_tool_creates_new_version(self, mock_create_or_get):
        """Test tool successfully creates a new version."""
        mock_create_or_get.return_value = {
            "id": "10007",
            "name": "Sprint 1 Release",
            "created": True
        }
        
        tool = CreateOrGetFixVersionTool()
        result = tool._run(name="Sprint 1 Release")
        
        assert "Created fix version" in result
        assert "ID=10007" in result
        assert "Sprint 1 Release" in result
        
        mock_create_or_get.assert_called_once_with(
            "Sprint 1 Release", "", None, False
        )
    
    @patch("tools.pm_tools.jira.create_or_get_fix_version")
    def test_tool_finds_existing_version(self, mock_create_or_get):
        """Test tool finds an existing version."""
        mock_create_or_get.return_value = {
            "id": "10001",
            "name": "v1.0.0",
            "created": False
        }
        
        tool = CreateOrGetFixVersionTool()
        result = tool._run(name="v1.0.0")
        
        assert "Found existing fix version" in result
        assert "ID=10001" in result
        assert "v1.0.0" in result
    
    @patch("tools.pm_tools.jira.create_or_get_fix_version")
    def test_tool_with_all_parameters(self, mock_create_or_get):
        """Test tool with all parameters provided."""
        mock_create_or_get.return_value = {
            "id": "10008",
            "name": "Q2 Release",
            "created": True
        }
        
        tool = CreateOrGetFixVersionTool()
        result = tool._run(
            name="Q2 Release",
            description="Quarterly release",
            release_date="2025-06-30",
            released=False
        )
        
        assert "Created fix version" in result
        assert "Q2 Release" in result
        
        mock_create_or_get.assert_called_once_with(
            "Q2 Release", "Quarterly release", "2025-06-30", False
        )


class TestListFixVersionsTool:
    """Test the CrewAI tool wrapper for list_fix_versions."""
    
    @patch("tools.pm_tools.jira.list_fix_versions")
    def test_tool_lists_versions(self, mock_list_versions):
        """Test tool successfully lists versions."""
        mock_list_versions.return_value = [
            {
                "id": "10001",
                "name": "v1.0.0",
                "description": "First release",
                "released": True,
                "release_date": "2025-01-15"
            },
            {
                "id": "10002",
                "name": "v1.1.0",
                "description": "Second release",
                "released": False,
                "release_date": None
            }
        ]
        
        tool = ListFixVersionsTool()
        result = tool._run()
        
        assert "Fix Versions:" in result
        assert "[10001] v1.0.0" in result
        assert "Released" in result
        assert "Release: 2025-01-15" in result
        assert "[10002] v1.1.0" in result
        assert "Unreleased" in result
        
        mock_list_versions.assert_called_once()
    
    @patch("tools.pm_tools.jira.list_fix_versions")
    def test_tool_empty_list(self, mock_list_versions):
        """Test tool with no versions."""
        mock_list_versions.return_value = []
        
        tool = ListFixVersionsTool()
        result = tool._run()
        
        assert result == "No fix versions found."
        mock_list_versions.assert_called_once()


class TestToolIntegration:
    """Integration tests to ensure tools are properly registered."""
    
    def test_version_tools_are_registered(self):
        """Test that VERSION_TOOLS list is properly defined."""
        from tools.pm_tools import VERSION_TOOLS
        
        assert len(VERSION_TOOLS) == 2
        tool_names = [tool.name for tool in VERSION_TOOLS]
        assert "list_fix_versions" in tool_names
        assert "create_or_get_fix_version" in tool_names
    
    def test_version_tools_in_all_pm_tools(self):
        """Test that version tools are included in ALL_PM_TOOLS."""
        from tools.pm_tools import ALL_PM_TOOLS
        
        tool_names = [tool.name for tool in ALL_PM_TOOLS]
        assert "list_fix_versions" in tool_names
        assert "create_or_get_fix_version" in tool_names
    
    def test_create_or_get_tool_schema(self):
        """Test that the tool has proper schema validation."""
        tool = CreateOrGetFixVersionTool()
        
        # Verify required fields
        assert tool.args_schema is not None
        schema_fields = tool.args_schema.model_fields
        
        assert "name" in schema_fields
        assert "description" in schema_fields
        assert "release_date" in schema_fields
        assert "released" in schema_fields
        
        # Verify name is required
        assert schema_fields["name"].is_required()
        
        # Verify others are optional with defaults
        assert not schema_fields["description"].is_required()
        assert not schema_fields["release_date"].is_required()
        assert not schema_fields["released"].is_required()
