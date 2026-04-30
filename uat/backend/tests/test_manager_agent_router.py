"""
Tests for Manager Agent FastAPI router.
"""

import pytest
import sys
import os
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Add agents to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../..", "agents"))

from manager_agent import TransitionStatus, TransitionResult


# ── Fixtures ──────────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("JIRA_BASE_URL", "https://test.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "test@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
    monkeypatch.setenv("JIRA_PROJECT_KEY", "TEST")
    monkeypatch.setenv("DATABASE_URL", "")


@pytest.fixture
def client(mock_env):
    """Create test client."""
    from main import app
    return TestClient(app)


# ── Router Tests ──────────────────────────────────────────────────────────────────────


class TestManagerAgentRouter:
    """Test Manager Agent API endpoints."""
    
    def test_transition_issue_by_status(self, client):
        """Test transitioning issue by target status."""
        with patch("manager_agent.create_manager_agent") as mock_create:
            mock_agent = MagicMock()
            mock_client = MagicMock()
            mock_agent.client = mock_client
            
            # Mock transition_issue_by_name as async
            async def mock_transition(*args, **kwargs):
                return TransitionResult(
                    status=TransitionStatus.SUCCESS,
                    issue_key="TEST-1",
                    transition_name="Start Progress",
                    attempts=1,
                    total_time=0.5,
                    final_status="In Progress",
                )
            
            mock_client.transition_issue_by_name = mock_transition
            mock_create.return_value = mock_agent
            
            response = client.post(
                "/api/manager-agent/transition",
                json={
                    "issue_key": "TEST-1",
                    "target_status": "In Progress",
                    "comment": "Starting work",
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["issue_key"] == "TEST-1"
            assert data["final_status"] == "In Progress"
    
    def test_transition_issue_by_id(self, client):
        """Test transitioning issue by transition ID."""
        with patch("manager_agent.create_manager_agent") as mock_create:
            mock_agent = MagicMock()
            mock_client = MagicMock()
            mock_agent.client = mock_client
            
            async def mock_transition(*args, **kwargs):
                return TransitionResult(
                    status=TransitionStatus.SUCCESS,
                    issue_key="TEST-1",
                    transition_id="11",
                    attempts=1,
                    total_time=0.5,
                    final_status="In Progress",
                )
            
            mock_client.transition_issue = mock_transition
            mock_create.return_value = mock_agent
            
            response = client.post(
                "/api/manager-agent/transition",
                json={
                    "issue_key": "TEST-1",
                    "transition_id": "11",
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["transition_id"] == "11"
    
    def test_transition_issue_missing_params(self, client):
        """Test transition with missing required parameters."""
        response = client.post(
            "/api/manager-agent/transition",
            json={"issue_key": "TEST-1"}
        )
        
        assert response.status_code == 400
        assert "target_status or transition_id must be provided" in response.json()["detail"]
    
    def test_start_work(self, client):
        """Test start work endpoint."""
        with patch("manager_agent.create_manager_agent") as mock_create:
            mock_agent = MagicMock()
            
            async def mock_start_work(*args, **kwargs):
                return TransitionResult(
                    status=TransitionStatus.SUCCESS,
                    issue_key="TEST-1",
                    attempts=1,
                    total_time=0.5,
                    final_status="In Progress",
                )
            
            mock_agent.start_work = mock_start_work
            mock_create.return_value = mock_agent
            
            response = client.post(
                "/api/manager-agent/start-work/TEST-1",
                params={"assignee": "john.doe", "comment": "Starting"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["final_status"] == "In Progress"
    
    def test_complete_work(self, client):
        """Test complete work endpoint."""
        with patch("manager_agent.create_manager_agent") as mock_create:
            mock_agent = MagicMock()
            
            async def mock_complete_work(*args, **kwargs):
                return TransitionResult(
                    status=TransitionStatus.SUCCESS,
                    issue_key="TEST-1",
                    attempts=1,
                    total_time=0.5,
                    final_status="Done",
                )
            
            mock_agent.complete_work = mock_complete_work
            mock_create.return_value = mock_agent
            
            response = client.post("/api/manager-agent/complete-work/TEST-1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["final_status"] == "Done"
    
    def test_move_to_code_review(self, client):
        """Test code review endpoint."""
        with patch("manager_agent.create_manager_agent") as mock_create:
            mock_agent = MagicMock()
            
            async def mock_code_review(*args, **kwargs):
                return TransitionResult(
                    status=TransitionStatus.SUCCESS,
                    issue_key="TEST-1",
                    attempts=1,
                    total_time=0.5,
                    final_status="Code Review",
                )
            
            mock_agent.move_to_code_review = mock_code_review
            mock_create.return_value = mock_agent
            
            response = client.post("/api/manager-agent/code-review/TEST-1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["final_status"] == "Code Review"
    
    def test_move_to_testing(self, client):
        """Test testing endpoint."""
        with patch("manager_agent.create_manager_agent") as mock_create:
            mock_agent = MagicMock()
            
            async def mock_testing(*args, **kwargs):
                return TransitionResult(
                    status=TransitionStatus.SUCCESS,
                    issue_key="TEST-1",
                    attempts=1,
                    total_time=0.5,
                    final_status="Testing",
                )
            
            mock_agent.move_to_testing = mock_testing
            mock_create.return_value = mock_agent
            
            response = client.post("/api/manager-agent/testing/TEST-1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["final_status"] == "Testing"
    
    def test_get_issue_status(self, client):
        """Test get issue status endpoint."""
        with patch("manager_agent.create_manager_agent") as mock_create:
            mock_agent = MagicMock()
            
            async def mock_get_status(*args, **kwargs):
                return "In Progress"
            
            mock_agent.get_issue_status = mock_get_status
            mock_create.return_value = mock_agent
            
            response = client.get("/api/manager-agent/status/TEST-1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["issue_key"] == "TEST-1"
            assert data["status"] == "In Progress"
    
    def test_get_issue_status_not_found(self, client):
        """Test get issue status when issue not found."""
        with patch("manager_agent.create_manager_agent") as mock_create:
            mock_agent = MagicMock()
            
            async def mock_get_status(*args, **kwargs):
                return None
            
            mock_agent.get_issue_status = mock_get_status
            mock_create.return_value = mock_agent
            
            response = client.get("/api/manager-agent/status/TEST-999")
            
            assert response.status_code == 404
    
    def test_bulk_transition(self, client):
        """Test bulk transition endpoint."""
        with patch("manager_agent.create_manager_agent") as mock_create:
            mock_agent = MagicMock()
            mock_client = MagicMock()
            mock_agent.client = mock_client
            
            async def mock_bulk(*args, **kwargs):
                return [
                    TransitionResult(
                        status=TransitionStatus.SUCCESS,
                        issue_key="TEST-1",
                        attempts=1,
                        total_time=0.5,
                        final_status="In Progress",
                    ),
                    TransitionResult(
                        status=TransitionStatus.SUCCESS,
                        issue_key="TEST-2",
                        attempts=2,
                        total_time=1.2,
                        final_status="Done",
                    ),
                ]
            
            mock_client.bulk_transition = mock_bulk
            mock_create.return_value = mock_agent
            
            response = client.post(
                "/api/manager-agent/bulk-transition",
                json={
                    "transitions": [
                        {"issue_key": "TEST-1", "target_status": "In Progress"},
                        {"issue_key": "TEST-2", "target_status": "Done"},
                    ]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert data["successful"] == 2
            assert data["failed"] == 0
            assert len(data["results"]) == 2
    
    def test_transition_failure(self, client):
        """Test failed transition returns proper error status."""
        with patch("manager_agent.create_manager_agent") as mock_create:
            mock_agent = MagicMock()
            mock_client = MagicMock()
            mock_agent.client = mock_client
            
            async def mock_transition(*args, **kwargs):
                return TransitionResult(
                    status=TransitionStatus.FAILED,
                    issue_key="TEST-1",
                    attempts=5,
                    total_time=15.0,
                    error_message="Max retries exceeded",
                )
            
            mock_client.transition_issue_by_name = mock_transition
            mock_create.return_value = mock_agent
            
            response = client.post(
                "/api/manager-agent/transition",
                json={
                    "issue_key": "TEST-1",
                    "target_status": "Invalid Status",
                }
            )
            
            assert response.status_code == 200  # Returns 200 but success=False
            data = response.json()
            assert data["success"] is False
            assert data["status"] == "failed"
            assert data["attempts"] == 5
            assert "Max retries" in data["error_message"]
    
    def test_exception_handling(self, client):
        """Test that exceptions are properly handled."""
        with patch("manager_agent.create_manager_agent") as mock_create:
            mock_create.side_effect = Exception("Test error")
            
            response = client.post(
                "/api/manager-agent/start-work/TEST-1"
            )
            
            assert response.status_code == 500
            assert "Test error" in response.json()["detail"]
