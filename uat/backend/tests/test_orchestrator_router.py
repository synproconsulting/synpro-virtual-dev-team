"""
Tests for the Orchestrator API router.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import UUID, uuid4

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from models import Base, OrchestratorStatus
from database import get_db

# Add agents directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from agents.orchestrator_state import StateManager


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


def test_start_sprint_endpoint(client, db_session):
    """Test starting a sprint via API."""
    with patch("orchestrator_router.Orchestrator") as mock_orchestrator_class:
        # Mock orchestrator instance
        mock_orchestrator = Mock()
        mock_state_id = uuid4()
        mock_orchestrator.start_sprint.return_value = mock_state_id
        
        # Mock state
        mock_state = Mock()
        mock_state.status = OrchestratorStatus.RUNNING
        mock_orchestrator.state_manager.get_state.return_value = mock_state
        
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Make request
        response = client.post(
            "/api/orchestrator/start",
            json={
                "sprint_id": 123,
                "sprint_name": "Sprint 42",
                "jira_project_key": "SDT1",
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["sprint_id"] == 123
        assert data["sprint_name"] == "Sprint 42"
        assert data["state_id"] == str(mock_state_id)


def test_resume_sprint_endpoint(client, db_session):
    """Test resuming a sprint via API."""
    # Create a paused state
    state_manager = StateManager(db=db_session)
    state = state_manager.create_state(
        sprint_id=123,
        sprint_name="Sprint 42",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1", "SDT1-2"],
    )
    state_manager.start_execution(state.id)
    state_manager.pause_execution(state.id)
    
    with patch("orchestrator_router.Orchestrator") as mock_orchestrator_class:
        # Mock orchestrator instance
        mock_orchestrator = Mock()
        mock_orchestrator.state_manager = state_manager
        mock_orchestrator.resume_sprint.return_value = None
        
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Make request
        response = client.post(
            "/api/orchestrator/resume",
            json={
                "state_id": str(state.id),
                "jira_project_key": "SDT1",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["sprint_id"] == 123
        assert data["sprint_name"] == "Sprint 42"


def test_resume_sprint_invalid_uuid(client):
    """Test resuming with invalid UUID format."""
    response = client.post(
        "/api/orchestrator/resume",
        json={
            "state_id": "not-a-uuid",
            "jira_project_key": "SDT1",
        }
    )
    
    assert response.status_code == 400
    assert "Invalid state ID format" in response.json()["detail"]


def test_get_progress_endpoint(client, db_session):
    """Test getting progress via API."""
    # Create a state
    state_manager = StateManager(db=db_session)
    state = state_manager.create_state(
        sprint_id=123,
        sprint_name="Sprint 42",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1", "SDT1-2", "SDT1-3"],
    )
    state_manager.start_execution(state.id)
    state_manager.mark_ticket_completed(state.id, "SDT1-1")
    
    # Get progress
    response = client.get(f"/api/orchestrator/progress/{state.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["sprint_id"] == 123
    assert data["total_tickets"] == 3
    assert data["completed_tickets"] == 1
    assert data["remaining_tickets"] == 2


def test_get_progress_not_found(client):
    """Test getting progress for non-existent state."""
    fake_uuid = str(uuid4())
    response = client.get(f"/api/orchestrator/progress/{fake_uuid}")
    
    assert response.status_code == 404


def test_list_resumable_endpoint(client, db_session):
    """Test listing resumable sprints via API."""
    # Create multiple states
    state_manager = StateManager(db=db_session)
    
    # Paused state
    state1 = state_manager.create_state(
        sprint_id=1,
        sprint_name="Sprint 1",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1"],
    )
    state_manager.pause_execution(state1.id)
    
    # Failed state
    state2 = state_manager.create_state(
        sprint_id=2,
        sprint_name="Sprint 2",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-2"],
    )
    state_manager.fail_execution(state2.id, "Error")
    
    # Completed state (should not appear)
    state3 = state_manager.create_state(
        sprint_id=3,
        sprint_name="Sprint 3",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-3"],
    )
    state_manager.complete_execution(state3.id)
    
    # Get resumable
    response = client.get("/api/orchestrator/resumable")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    sprint_ids = [s["sprint_id"] for s in data]
    assert 1 in sprint_ids
    assert 2 in sprint_ids
    assert 3 not in sprint_ids


def test_pause_sprint_endpoint(client, db_session):
    """Test pausing a sprint via API."""
    # Create a running state
    state_manager = StateManager(db=db_session)
    state = state_manager.create_state(
        sprint_id=123,
        sprint_name="Sprint 42",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1"],
    )
    state_manager.start_execution(state.id)
    
    # Pause it
    response = client.post(
        "/api/orchestrator/pause",
        json={
            "state_id": str(state.id),
            "reason": "Maintenance",
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "paused"
    
    # Verify state was updated
    updated_state = state_manager.get_state(state.id)
    assert updated_state.status == OrchestratorStatus.PAUSED
    assert updated_state.error_message == "Maintenance"


def test_cancel_sprint_endpoint(client, db_session):
    """Test cancelling a sprint via API."""
    # Create a running state
    state_manager = StateManager(db=db_session)
    state = state_manager.create_state(
        sprint_id=123,
        sprint_name="Sprint 42",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1"],
    )
    state_manager.start_execution(state.id)
    
    # Cancel it
    response = client.post(
        "/api/orchestrator/cancel",
        json={
            "state_id": str(state.id),
            "reason": "Project cancelled",
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "cancelled"
    
    # Verify state was updated
    updated_state = state_manager.get_state(state.id)
    assert updated_state.status == OrchestratorStatus.CANCELLED
    assert updated_state.error_message == "Project cancelled"


def test_pause_invalid_state(client):
    """Test pausing a non-existent state."""
    response = client.post(
        "/api/orchestrator/pause",
        json={
            "state_id": str(uuid4()),
        }
    )
    
    assert response.status_code == 404


def test_cancel_invalid_state(client):
    """Test cancelling a non-existent state."""
    response = client.post(
        "/api/orchestrator/cancel",
        json={
            "state_id": str(uuid4()),
        }
    )
    
    assert response.status_code == 404


def test_empty_resumable_list(client):
    """Test listing resumable when none exist."""
    response = client.get("/api/orchestrator/resumable")
    
    assert response.status_code == 200
    data = response.json()
    assert data == []
