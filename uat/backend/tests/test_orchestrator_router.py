"""
Tests for orchestrator API router.
"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4, UUID

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from models import Base, OrchestratorStatus
from database import get_db


@pytest.fixture
def db_session():
    """Create a test database session."""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine)
    session = TestSessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def client(db_session):
    """Create a test client with test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


def test_start_sprint(client, db_session):
    """Test starting a sprint via API."""
    with patch("orchestrator_router.Orchestrator") as MockOrchestrator:
        mock_orch = Mock()
        state_id = uuid4()
        mock_orch.start_sprint.return_value = state_id
        MockOrchestrator.return_value.__enter__.return_value = mock_orch
        
        response = client.post(
            "/api/orchestrator/start",
            json={
                "sprint_id": 123,
                "sprint_name": "Sprint 1",
                "jira_project_key": "SDT1",
            },
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["sprint_id"] == 123
        assert data["sprint_name"] == "Sprint 1"
        assert data["status"] == "running"
        assert "state_id" in data


def test_start_sprint_error(client, db_session):
    """Test starting a sprint with error."""
    with patch("orchestrator_router.Orchestrator") as MockOrchestrator:
        mock_orch = Mock()
        mock_orch.start_sprint.side_effect = Exception("Test error")
        MockOrchestrator.return_value.__enter__.return_value = mock_orch
        
        response = client.post(
            "/api/orchestrator/start",
            json={
                "sprint_id": 123,
                "sprint_name": "Sprint 1",
                "jira_project_key": "SDT1",
            },
        )
        
        assert response.status_code == 500
        assert "Failed to start sprint" in response.json()["detail"]


def test_resume_sprint(client, db_session):
    """Test resuming a sprint via API."""
    state_id = uuid4()
    
    with patch("orchestrator_router.Orchestrator") as MockOrchestrator:
        mock_orch = Mock()
        mock_state = Mock()
        mock_state.sprint_id = 123
        mock_state.sprint_name = "Sprint 1"
        mock_state.status = OrchestratorStatus.COMPLETED
        mock_orch.state_manager.get_state.return_value = mock_state
        MockOrchestrator.return_value.__enter__.return_value = mock_orch
        
        response = client.post(
            "/api/orchestrator/resume",
            json={
                "state_id": str(state_id),
                "jira_project_key": "SDT1",
            },
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["sprint_id"] == 123
        assert data["sprint_name"] == "Sprint 1"
        assert data["status"] == "completed"


def test_resume_sprint_invalid_uuid(client, db_session):
    """Test resuming with invalid UUID."""
    response = client.post(
        "/api/orchestrator/resume",
        json={
            "state_id": "not-a-uuid",
            "jira_project_key": "SDT1",
        },
    )
    
    assert response.status_code == 400
    assert "Invalid state_id format" in response.json()["detail"]


def test_resume_sprint_not_found(client, db_session):
    """Test resuming non-existent sprint."""
    state_id = uuid4()
    
    with patch("orchestrator_router.Orchestrator") as MockOrchestrator:
        mock_orch = Mock()
        mock_orch.state_manager.get_state.return_value = None
        MockOrchestrator.return_value.__enter__.return_value = mock_orch
        
        response = client.post(
            "/api/orchestrator/resume",
            json={
                "state_id": str(state_id),
                "jira_project_key": "SDT1",
            },
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


def test_pause_sprint(client, db_session):
    """Test pausing a sprint via API."""
    state_id = uuid4()
    
    with patch("orchestrator_router.Orchestrator") as MockOrchestrator:
        mock_orch = Mock()
        MockOrchestrator.return_value.__enter__.return_value = mock_orch
        
        response = client.post(
            "/api/orchestrator/pause",
            json={
                "state_id": str(state_id),
                "jira_project_key": "SDT1",
                "reason": "Test pause",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused"
        mock_orch.pause.assert_called_once_with(state_id, reason="Test pause")


def test_cancel_sprint(client, db_session):
    """Test cancelling a sprint via API."""
    state_id = uuid4()
    
    with patch("orchestrator_router.Orchestrator") as MockOrchestrator:
        mock_orch = Mock()
        MockOrchestrator.return_value.__enter__.return_value = mock_orch
        
        response = client.post(
            "/api/orchestrator/cancel",
            json={
                "state_id": str(state_id),
                "jira_project_key": "SDT1",
                "reason": "Test cancel",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
        mock_orch.cancel.assert_called_once_with(state_id, reason="Test cancel")


def test_get_progress(client, db_session):
    """Test getting execution progress via API."""
    state_id = uuid4()
    
    with patch("orchestrator_router.Orchestrator") as MockOrchestrator:
        mock_orch = Mock()
        mock_orch.get_progress.return_value = {
            "state_id": str(state_id),
            "sprint_id": 123,
            "sprint_name": "Sprint 1",
            "status": "running",
            "total_tickets": 10,
            "completed_tickets": 5,
            "failed_tickets": 1,
            "remaining_tickets": 4,
            "current_ticket": "SDT1-5",
            "progress_percentage": 50.0,
            "started_at": "2024-01-01T00:00:00",
            "last_checkpoint": "2024-01-01T01:00:00",
        }
        MockOrchestrator.return_value.__enter__.return_value = mock_orch
        
        response = client.get(
            f"/api/orchestrator/progress/{state_id}",
            params={"jira_project_key": "SDT1"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["sprint_id"] == 123
        assert data["total_tickets"] == 10
        assert data["completed_tickets"] == 5
        assert data["progress_percentage"] == 50.0


def test_get_progress_not_found(client, db_session):
    """Test getting progress for non-existent state."""
    state_id = uuid4()
    
    with patch("orchestrator_router.Orchestrator") as MockOrchestrator:
        mock_orch = Mock()
        mock_orch.get_progress.side_effect = ValueError("State not found")
        MockOrchestrator.return_value.__enter__.return_value = mock_orch
        
        response = client.get(
            f"/api/orchestrator/progress/{state_id}",
            params={"jira_project_key": "SDT1"},
        )
        
        assert response.status_code == 404


def test_list_resumable(client, db_session):
    """Test listing resumable sprints via API."""
    with patch("orchestrator_router.Orchestrator") as MockOrchestrator:
        mock_orch = Mock()
        mock_orch.list_resumable.return_value = [
            {
                "state_id": str(uuid4()),
                "sprint_id": 1,
                "sprint_name": "Sprint 1",
                "status": "paused",
                "total_tickets": 10,
                "completed": 5,
                "failed": 0,
                "remaining": 5,
                "last_updated": "2024-01-01T00:00:00",
            },
            {
                "state_id": str(uuid4()),
                "sprint_id": 2,
                "sprint_name": "Sprint 2",
                "status": "failed",
                "total_tickets": 8,
                "completed": 3,
                "failed": 1,
                "remaining": 4,
                "last_updated": "2024-01-02T00:00:00",
            },
        ]
        MockOrchestrator.return_value.__enter__.return_value = mock_orch
        
        response = client.get(
            "/api/orchestrator/resumable",
            params={"jira_project_key": "SDT1"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["sprints"]) == 2
        assert data["sprints"][0]["sprint_name"] == "Sprint 1"
        assert data["sprints"][1]["sprint_name"] == "Sprint 2"


def test_list_resumable_empty(client, db_session):
    """Test listing resumable sprints when none exist."""
    with patch("orchestrator_router.Orchestrator") as MockOrchestrator:
        mock_orch = Mock()
        mock_orch.list_resumable.return_value = []
        MockOrchestrator.return_value.__enter__.return_value = mock_orch
        
        response = client.get(
            "/api/orchestrator/resumable",
            params={"jira_project_key": "SDT1"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert len(data["sprints"]) == 0


def test_request_validation(client, db_session):
    """Test request validation."""
    # Missing required fields
    response = client.post(
        "/api/orchestrator/start",
        json={
            "sprint_id": 123,
            # Missing sprint_name and jira_project_key
        },
    )
    
    assert response.status_code == 422  # Validation error


def test_invalid_state_id_format(client, db_session):
    """Test invalid state ID format handling."""
    response = client.get(
        "/api/orchestrator/progress/not-a-uuid",
        params={"jira_project_key": "SDT1"},
    )
    
    assert response.status_code == 400
    assert "Invalid state_id format" in response.json()["detail"]
