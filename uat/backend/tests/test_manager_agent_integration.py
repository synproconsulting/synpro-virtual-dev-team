"""
Integration tests for Manager Agent API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json


# Mock the imports to avoid requiring actual API keys during tests
@pytest.fixture
def mock_anthropic():
    """Mock Anthropic client."""
    with patch("manager_agent._get_anthropic_client") as mock:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="## Summary\nLooks good!\n## Approval\nAPPROVE")]
        mock_client.messages.create.return_value = mock_response
        mock.return_value = mock_client
        yield mock


@pytest.fixture
def mock_github():
    """Mock GitHub API responses."""
    with patch("httpx.AsyncClient") as mock:
        async_client = MagicMock()
        
        # Mock PR response
        pr_response = MagicMock()
        pr_response.status_code = 200
        pr_response.json.return_value = {
            "title": "Test PR",
            "body": "Test description",
            "number": 123
        }
        
        # Mock files response
        files_response = MagicMock()
        files_response.status_code = 200
        files_response.json.return_value = [
            {
                "filename": "new_feature.py",
                "status": "added",
                "additions": 50,
                "deletions": 0,
                "patch": "@@ test patch\n+new code\n"
            },
            {
                "filename": "existing.py",
                "status": "modified",
                "additions": 10,
                "deletions": 5,
                "patch": "@@ test patch\n+modified code\n"
            }
        ]
        
        async def mock_get(url, **kwargs):
            if "files" in url:
                return files_response
            return pr_response
        
        async_client.get = mock_get
        
        async def mock_aenter(*args, **kwargs):
            return async_client
        
        async def mock_aexit(*args, **kwargs):
            pass
        
        mock.return_value.__aenter__ = mock_aenter
        mock.return_value.__aexit__ = mock_aexit
        
        yield mock


@pytest.fixture
def client():
    """Create test client."""
    # Import here to use mocked dependencies
    from main import app
    return TestClient(app)


def test_health_check(client):
    """Test manager agent health check endpoint."""
    response = client.get("/api/manager-agent/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "manager-agent"
    assert "smart_diff_truncation" in data["features"]


def test_truncate_diff_endpoint_basic(client):
    """Test basic diff truncation endpoint."""
    request_data = {
        "files": [
            {
                "filename": "new.py",
                "status": "added",
                "additions": 20,
                "deletions": 0,
                "patch": "@@ test\n+new code\n"
            }
        ],
        "max_chars": 10000,
        "min_files": 1
    }
    
    response = client.post("/api/manager-agent/truncate-diff", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "truncated_diff" in data
    assert "summary" in data
    assert data["summary"]["total_files"] == 1
    assert data["summary"]["included_files"] == 1


def test_truncate_diff_prioritizes_new_files(client):
    """Test that truncation prioritizes new files."""
    # Create files where only one can fit
    large_patch = "x" * 1000
    
    request_data = {
        "files": [
            {
                "filename": "modified.py",
                "status": "modified",
                "additions": 100,
                "deletions": 50,
                "patch": large_patch
            },
            {
                "filename": "new.py",
                "status": "added",
                "additions": 50,
                "deletions": 0,
                "patch": "small patch"
            }
        ],
        "max_chars": 500,
        "min_files": 1
    }
    
    response = client.post("/api/manager-agent/truncate-diff", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    
    # New file should be included
    assert "new.py" in data["truncated_diff"]


def test_truncate_diff_with_multiple_file_types(client):
    """Test truncation with mixed file types."""
    request_data = {
        "files": [
            {
                "filename": "new1.py",
                "status": "added",
                "additions": 100,
                "deletions": 0,
                "patch": "patch1"
            },
            {
                "filename": "new2.py",
                "status": "added",
                "additions": 50,
                "deletions": 0,
                "patch": "patch2"
            },
            {
                "filename": "modified.py",
                "status": "modified",
                "additions": 30,
                "deletions": 10,
                "patch": "patch3"
            },
            {
                "filename": "deleted.py",
                "status": "removed",
                "additions": 0,
                "deletions": 100,
                "patch": "patch4"
            }
        ],
        "max_chars": 10000,
        "min_files": 2
    }
    
    response = client.post("/api/manager-agent/truncate-diff", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["summary"]["total_files"] == 4
    
    # Should include at least minimum files
    assert data["summary"]["included_files"] >= 2
    
    # Summary should contain proper counts
    summary_text = data["summary"]["diff_summary"]
    assert "4 files" in summary_text
    assert "2 new" in summary_text


def test_truncate_diff_empty_files(client):
    """Test truncation with empty file list."""
    request_data = {
        "files": [],
        "max_chars": 10000,
        "min_files": 1
    }
    
    response = client.post("/api/manager-agent/truncate-diff", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["summary"]["total_files"] == 0
    assert data["summary"]["included_files"] == 0


def test_truncate_diff_min_files_override(client):
    """Test that min_files can exceed max_chars."""
    large_patch = "x" * 2000
    
    request_data = {
        "files": [
            {
                "filename": "file1.py",
                "status": "added",
                "additions": 100,
                "deletions": 0,
                "patch": large_patch
            },
            {
                "filename": "file2.py",
                "status": "added",
                "additions": 100,
                "deletions": 0,
                "patch": large_patch
            },
            {
                "filename": "file3.py",
                "status": "added",
                "additions": 100,
                "deletions": 0,
                "patch": large_patch
            }
        ],
        "max_chars": 1000,  # Too small for 3 files
        "min_files": 3      # But require 3 files
    }
    
    response = client.post("/api/manager-agent/truncate-diff", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    
    # Should include all 3 files despite exceeding max_chars
    assert data["summary"]["included_files"] == 3


@pytest.mark.skipif(
    True,  # Skip by default as it requires real API keys
    reason="Requires ANTHROPIC_API_KEY and GITHUB_TOKEN"
)
def test_review_pr_endpoint_with_mocks(client, mock_anthropic, mock_github):
    """Test PR review endpoint with mocked external APIs."""
    request_data = {
        "owner": "testorg",
        "repo": "testrepo",
        "pr_number": 123,
        "ticket_key": "TEST-1",
        "max_diff_chars": 50000
    }
    
    response = client.post("/api/manager-agent/review-pr", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "review" in data
    assert "diff_summary" in data


def test_truncation_notice_format(client):
    """Test that truncation notice is properly formatted."""
    large_patch = "x" * 5000
    small_patch = "x" * 100
    
    request_data = {
        "files": [
            {
                "filename": "new_small.py",
                "status": "added",
                "additions": 10,
                "deletions": 0,
                "patch": small_patch
            },
            {
                "filename": "new_large.py",
                "status": "added",
                "additions": 500,
                "deletions": 0,
                "patch": large_patch
            },
            {
                "filename": "modified.py",
                "status": "modified",
                "additions": 100,
                "deletions": 50,
                "patch": large_patch
            }
        ],
        "max_chars": 1000,
        "min_files": 1
    }
    
    response = client.post("/api/manager-agent/truncate-diff", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    truncated_diff = data["truncated_diff"]
    
    # If files were excluded, check notice format
    if data["summary"]["excluded_files"] > 0:
        assert "DIFF TRUNCATED" in truncated_diff
        assert "files excluded" in truncated_diff
        
        # Check that excluded files are listed
        for excluded_file in data["summary"]["excluded_file_list"]:
            assert excluded_file in truncated_diff


def test_diff_summary_accuracy(client):
    """Test that diff summary accurately reflects changes."""
    request_data = {
        "files": [
            {
                "filename": "new1.py",
                "status": "added",
                "additions": 100,
                "deletions": 0,
                "patch": "patch"
            },
            {
                "filename": "new2.py",
                "status": "added",
                "additions": 50,
                "deletions": 0,
                "patch": "patch"
            },
            {
                "filename": "modified.py",
                "status": "modified",
                "additions": 25,
                "deletions": 15,
                "patch": "patch"
            }
        ],
        "max_chars": 50000,
        "min_files": 1
    }
    
    response = client.post("/api/manager-agent/truncate-diff", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    summary = data["summary"]["diff_summary"]
    
    # Check file counts
    assert "3 files" in summary
    assert "2 new" in summary
    assert "1 modified" in summary
    
    # Check line counts (100 + 50 + 25 = 175 additions)
    assert "+175" in summary
    
    # Check deletions (15 deletions)
    assert "-15" in summary
