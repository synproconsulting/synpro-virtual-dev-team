"""
tests/integration/test_fix_version_integration.py
──────────────────────────────────────────────────
Integration tests for fix version functionality against a real Jira instance.

These tests are marked as integration tests and require:
- JIRA_URL
- JIRA_EMAIL
- JIRA_API_TOKEN
- JIRA_PROJECT_KEY

Run with: pytest tests/integration/test_fix_version_integration.py -v -m integration
"""

import pytest
import os
from tools import jira_client
from tools.pm_tools import CreateOrGetFixVersionTool, ListFixVersionsTool


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def check_jira_credentials():
    """Verify Jira credentials are available."""
    required_vars = ["JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"]
    missing = [var for var in required_vars if not os.environ.get(var)]
    
    if missing:
        pytest.skip(f"Missing Jira credentials: {', '.join(missing)}")
    
    return True


@pytest.fixture
def unique_version_name():
    """Generate a unique version name for testing."""
    import time
    return f"test-version-{int(time.time())}"


class TestFixVersionIntegration:
    """Integration tests for fix version operations."""
    
    def test_create_new_version(self, check_jira_credentials, unique_version_name):
        """Test creating a new fix version in Jira."""
        result = jira_client.create_or_get_fix_version(
            name=unique_version_name,
            description="Integration test version",
            release_date="2025-12-31",
            released=False
        )
        
        assert result["id"] is not None
        assert result["name"] == unique_version_name
        assert result["created"] is True
    
    def test_get_existing_version(self, check_jira_credentials, unique_version_name):
        """Test getting an existing version returns same ID."""
        # Create version
        result1 = jira_client.create_or_get_fix_version(name=unique_version_name)
        version_id = result1["id"]
        
        # Get same version
        result2 = jira_client.create_or_get_fix_version(name=unique_version_name)
        
        assert result2["id"] == version_id
        assert result2["created"] is False
    
    def test_deterministic_behavior(self, check_jira_credentials, unique_version_name):
        """Test that multiple calls with same name return same ID."""
        results = []
        
        # Call 5 times
        for i in range(5):
            result = jira_client.create_or_get_fix_version(
                name=unique_version_name,
                description=f"Call {i + 1}"
            )
            results.append(result["id"])
        
        # All IDs should be identical
        assert len(set(results)) == 1, "Version IDs should be identical across calls"
        
        # Only first call should have created=True
        first_result = jira_client.create_or_get_fix_version(name=unique_version_name)
        assert first_result["created"] is False  # Already exists from earlier calls
    
    def test_list_versions_includes_created(self, check_jira_credentials, unique_version_name):
        """Test that listing versions includes newly created version."""
        # Create a version
        created = jira_client.create_or_get_fix_version(name=unique_version_name)
        version_id = created["id"]
        
        # List all versions
        versions = jira_client.list_fix_versions()
        
        # Find our version in the list
        found = False
        for version in versions:
            if version["id"] == version_id:
                found = True
                assert version["name"] == unique_version_name
                break
        
        assert found, f"Created version {version_id} not found in version list"
    
    def test_create_version_with_all_fields(self, check_jira_credentials, unique_version_name):
        """Test creating version with all optional fields."""
        result = jira_client.create_or_get_fix_version(
            name=unique_version_name,
            description="Full integration test version with all fields",
            release_date="2026-01-15",
            released=False
        )
        
        assert result["id"] is not None
        assert result["name"] == unique_version_name
        assert result["created"] is True
        
        # Verify version appears in list with correct details
        versions = jira_client.list_fix_versions()
        version_found = next(
            (v for v in versions if v["id"] == result["id"]),
            None
        )
        
        assert version_found is not None
        assert version_found["name"] == unique_version_name
        assert "integration test" in version_found.get("description", "").lower()


class TestFixVersionToolIntegration:
    """Integration tests for the CrewAI tool wrappers."""
    
    def test_create_or_get_tool_creates_version(self, check_jira_credentials, unique_version_name):
        """Test that the tool successfully creates a version."""
        tool = CreateOrGetFixVersionTool()
        result = tool._run(name=unique_version_name)
        
        assert "Created fix version" in result or "Found existing fix version" in result
        assert unique_version_name in result
        assert "ID=" in result
    
    def test_create_or_get_tool_finds_existing(self, check_jira_credentials, unique_version_name):
        """Test that the tool finds existing version."""
        tool = CreateOrGetFixVersionTool()
        
        # Create version
        result1 = tool._run(name=unique_version_name)
        assert "Created fix version" in result1
        
        # Try to create again - should find existing
        result2 = tool._run(name=unique_version_name)
        assert "Found existing fix version" in result2
    
    def test_list_versions_tool(self, check_jira_credentials):
        """Test that list versions tool works."""
        tool = ListFixVersionsTool()
        result = tool._run()
        
        # Should either have versions or indicate none found
        assert "Fix Versions:" in result or "No fix versions found" in result
    
    def test_list_versions_tool_includes_created(self, check_jira_credentials, unique_version_name):
        """Test that list tool includes newly created versions."""
        # Create a version
        create_tool = CreateOrGetFixVersionTool()
        create_result = create_tool._run(name=unique_version_name)
        
        # List versions
        list_tool = ListFixVersionsTool()
        list_result = list_tool._run()
        
        # Should include our version
        assert unique_version_name in list_result


class TestConcurrentAccess:
    """Test thread-safety and concurrent access scenarios."""
    
    def test_concurrent_create_or_get(self, check_jira_credentials, unique_version_name):
        """Test that concurrent calls don't create duplicates."""
        from concurrent.futures import ThreadPoolExecutor
        
        def create_version():
            return jira_client.create_or_get_fix_version(name=unique_version_name)
        
        # Execute 10 concurrent calls
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_version) for _ in range(10)]
            results = [f.result() for f in futures]
        
        # All should return the same ID
        version_ids = [r["id"] for r in results]
        assert len(set(version_ids)) == 1, "All concurrent calls should return same version ID"
        
        # At most one should have created=True
        created_count = sum(1 for r in results if r["created"])
        # Due to race conditions, might be 0 or 1
        assert created_count <= 1, "At most one concurrent call should report creating the version"


class TestErrorHandling:
    """Test error handling in integration scenarios."""
    
    def test_invalid_release_date_format(self, check_jira_credentials, unique_version_name):
        """Test handling of invalid date format."""
        # Jira typically accepts YYYY-MM-DD, but let's test invalid format
        try:
            result = jira_client.create_or_get_fix_version(
                name=unique_version_name,
                release_date="invalid-date"
            )
            # If Jira accepts it, that's fine - we're testing it doesn't crash
            assert result["id"] is not None
        except Exception as e:
            # If it fails, it should fail gracefully with a meaningful error
            assert "date" in str(e).lower() or "invalid" in str(e).lower()
    
    def test_empty_version_name(self, check_jira_credentials):
        """Test handling of empty version name."""
        with pytest.raises(Exception):
            jira_client.create_or_get_fix_version(name="")
    
    def test_very_long_version_name(self, check_jira_credentials):
        """Test handling of very long version name."""
        long_name = "test-" + "x" * 1000
        
        try:
            result = jira_client.create_or_get_fix_version(name=long_name)
            # If it succeeds, verify we got a valid ID
            assert result["id"] is not None
        except Exception as e:
            # If it fails, should be due to length constraints
            assert "length" in str(e).lower() or "too long" in str(e).lower() or "invalid" in str(e).lower()


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_versions(check_jira_credentials):
    """Cleanup fixture to remove test versions after all tests complete."""
    # This runs after all tests in the module
    yield
    
    # Note: Jira doesn't provide an easy way to delete versions via API
    # In a real scenario, you might want to manually clean up test versions
    # or use a dedicated test project that can be reset
    print("\n\nNote: Test versions created during integration tests should be manually cleaned up")
    print("or use a dedicated test Jira project that can be reset.")
