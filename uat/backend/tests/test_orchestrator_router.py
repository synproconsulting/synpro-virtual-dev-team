"""
tests/test_orchestrator_router.py
─────────────────────────────────
Tests for the orchestrator REST API endpoints.

Tests cover:
- Starting sprint executions via API
- Resuming executions via API
- Getting progress via API
- Listing resumable states via API
- Pausing and cancelling via API
- Error handling and validation
"""

import os
import sys
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from models import Base, OrchestratorStatus
from database import get_db
from main import app


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_orchestrator(monkeypatch):
    """Mock the orchestrator to avoid actual Jira calls."""
    from agents import orchestrator
    
    class MockOrchestrator:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
        
        def start_sprint(self, sprint_id, sprint_name):
            # Create a real state for testing
            from agents.orchestrator_state import StateManager
            state_manager = StateManager(db=self.kwargs.get('db'))
            state = state_manager.create_state(
                sprint_id=sprint_id,
                sprint_name=sprint_name,
                jira_project_key=self.kwargs.get('jira_project_key', 'TEST'),
                ticket_queue=[],
            )
            state_manager.complete_execution(state.id)
            return state.id
        
        def resume_sprint(self, state_id):
            from agents.orchestrator_state import StateManager
            state_manager = StateManager(db=self.kwargs.get('db'))
            state = state_manager.get_state(state_id)
            if not state:
                raise ValueError(f"State {state_id} not found")
            if state.status not in [OrchestratorStatus.PAUSED, OrchestratorStatus.FAILED]:
                raise ValueError(f"Cannot resume state with status {state.status.value}")
            state_manager.complete_execution(state_id)
        
        def get_progress(self, state_id):
            from agents.orchestrator_state import StateManager
            state_manager = StateManager(db=self.kwargs.get('db'))
            return state_manager.get_progress(state_id)
        
        def list_resumable(self):
            from agents.orchestrator_state import StateManager
            state_manager = StateManager(db=self.kwargs.get('db'))
            states = state_manager.get_resumable_states()
            return [
                {
                    "state_id": str(state.id),
                    "sprint_id": state.sprint_id,
                    "sprint_name": state.sprint_name,
                    "status": state.status.value,
                    "total_tickets": state.total_tickets,
                    "completed": len(state.completed_tickets or []),
                    "failed": len(state.failed_tickets or []),
                    "remaining": len(state.ticket_queue or []),
                    "last_updated": state.updated_at.isoformat(),
                }
                for state in states
            ]
        
        def pause(self, state_id, reason=None):
            from agents.orchestrator_state import StateManager
            state_manager = StateManager(db=self.kwargs.get('db'))
            state_manager.pause_execution(state_id, reason)
        
        def cancel(self, state_id, reason=None):
            from agents.orchestrator_state import StateManager
            state_manager = StateManager(db=self.kwargs.get('db'))
            state_manager.cancel_execution(state_id, reason)
    
    monkeypatch.setattr(orchestrator, "Orchestrator", MockOrchestrator)


# ── Tests: Start Sprint ───────────────────────────────────────────────────────

def test_start_sprint_success(client, mock_orchestrator):
    """Test starting a sprint execution via API."""
    response = client.post(
        "/api/orchestrator/start",
        json={
            "sprint_id": 100,
            "sprint_name": "Test Sprint",
            "jira_project_key": "TEST",
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "state_id" in data
    assert data["sprint_id"] == 100
    assert data["sprint_name"] == "Test Sprint"
    assert "message" in data


def test_start_sprint_invalid_data(client):
    """Test starting a sprint with invalid data."""
    response = client.post(
        "/api/orchestrator/start",
        json={
            "sprint_id": "invalid",  # Should be int
            "sprint_name": "Test Sprint",
            "jira_project_key": "TEST",
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_start_sprint_missing_fields(client):
    """Test starting a sprint with missing fields."""
    response = client.post(
        "/api/orchestrator/start",
        json={
            "sprint_id": 100,
            # Missing sprint_name and jira_project_key
        }
    )
    
    assert response.status_code == 422  # Validation error


# ── Tests: Resume Sprint ──────────────────────────────────────────────────────

def test_resume_sprint_success(client, mock_orchestrator, db_session):
    """Test resuming a sprint execution via API."""
    # Create a paused state
    from agents.orchestrator_state import StateManager
    state_manager = StateManager(db=db_session)
    state = state_manager.create_state(
        sprint_id=101,
        sprint_name="Resume Test",
        jira_project_key="TEST",
        ticket_queue=["TEST-1"],
    )
    state_manager.pause_execution(state.id, "Test pause")
    
    response = client.post(
        "/api/orchestrator/resume",
        json={
            "state_id": str(state.id),
            "jira_project_key": "TEST",
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["state_id"] == str(state.id)
    assert "message" in data


def test_resume_sprint_invalid_state_id(client, mock_orchestrator):
    """Test resuming with invalid state ID."""
    response = client.post(
        "/api/orchestrator/resume",
        json={
            "state_id": "invalid-uuid",
            "jira_project_key": "TEST",
        }
    )
    
    assert response.status_code == 400


def test_resume_sprint_not_found(client, mock_orchestrator):
    """Test resuming a non-existent state."""
    fake_id = str(uuid4())
    
    response = client.post(
        "/api/orchestrator/resume",
        json={
            "state_id": fake_id,
            "jira_project_key": "TEST",
        }
    )
    
    assert response.status_code == 400


def test_resume_sprint_completed(client, mock_orchestrator, db_session):
    """Test that completed states cannot be resumed."""
    # Create a completed state
    from agents.orchestrator_state import StateManager
    state_manager = StateManager(db=db_session)
    state = state_manager.create_state(
        sprint_id=102,
        sprint_name="Completed Test",
        jira_project_key="TEST",
        ticket_queue=[],
    )
    state_manager.complete_execution(state.id)
    
    response = client.post(
        "/api/orchestrator/resume",
        json={
            "state_id": str(state.id),
            "jira_project_key": "TEST",
        }
    )
    
    assert response.status_code == 400


# ── Tests: Get Progress ───────────────────────────────────────────────────────

def test_get_progress_success(client, db_session):
    """Test getting execution progress via API."""
    # Create a state
    from agents.orchestrator_state import StateManager
    state_manager = StateManager(db=db_session)
    state = state_manager.create_state(
        sprint_id=103,
        sprint_name="Progress Test",
        jira_project_key="TEST",
        ticket_queue=["TEST-1", "TEST-2"],
    )
    state_manager.start_execution(state.id)
    state_manager.mark_ticket_completed(state.id, "TEST-1")
    
    response = client.get(f"/api/orchestrator/progress/{state.id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["state_id"] == str(state.id)
    assert data["sprint_id"] == 103
    assert data["sprint_name"] == "Progress Test"
    assert data["total_tickets"] == 2
    assert data["completed_tickets"] == 1
    assert data["remaining_tickets"] == 1


def test_get_progress_not_found(client):
    """Test getting progress for non-existent state."""
    fake_id = str(uuid4())
    
    response = client.get(f"/api/orchestrator/progress/{fake_id}")
    
    assert response.status_code == 404


def test_get_progress_invalid_id(client):
    """Test getting progress with invalid state ID."""
    response = client.get("/api/orchestrator/progress/invalid-uuid")
    
    assert response.status_code == 400


# ── Tests: List Resumable ─────────────────────────────────────────────────────

def test_list_resumable_empty(client, mock_orchestrator):
    """Test listing resumable states when none exist."""
    response = client.get("/api/orchestrator/resumable")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) == 0


def test_list_resumable_with_states(client, mock_orchestrator, db_session):
    """Test listing resumable states."""
    # Create multiple states
    from agents.orchestrator_state import StateManager
    state_manager = StateManager(db=db_session)
    
    state1 = state_manager.create_state(104, "Sprint 1", "TEST", ["TEST-1"])
    state_manager.pause_execution(state1.id, "Paused")
    
    state2 = state_manager.create_state(105, "Sprint 2", "TEST", ["TEST-2"])
    state_manager.fail_execution(state2.id, "Failed")
    
    state3 = state_manager.create_state(106, "Sprint 3", "TEST", ["TEST-3"])
    state_manager.complete_execution(state3.id)
    
    response = client.get("/api/orchestrator/resumable")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 2  # Only paused and failed
    statuses = {item["status"] for item in data}
    assert "paused" in statuses
    assert "failed" in statuses


# ── Tests: Pause Execution ────────────────────────────────────────────────────

def test_pause_execution_success(client, mock_orchestrator, db_session):
    """Test pausing an execution via API."""
    # Create a running state
    from agents.orchestrator_state import StateManager
    state_manager = StateManager(db=db_session)
    state = state_manager.create_state(
        sprint_id=107,
        sprint_name="Pause Test",
        jira_project_key="TEST",
        ticket_queue=["TEST-1"],
    )
    state_manager.start_execution(state.id)
    
    response = client.post(
        "/api/orchestrator/pause",
        json={
            "state_id": str(state.id),
            "reason": "Test pause",
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["state_id"] == str(state.id)
    assert "message" in data


def test_pause_execution_not_found(client, mock_orchestrator):
    """Test pausing a non-existent state."""
    fake_id = str(uuid4())
    
    response = client.post(
        "/api/orchestrator/pause",
        json={
            "state_id": fake_id,
        }
    )
    
    assert response.status_code == 404


def test_pause_execution_invalid_id(client):
    """Test pausing with invalid state ID."""
    response = client.post(
        "/api/orchestrator/pause",
        json={
            "state_id": "invalid-uuid",
        }
    )
    
    assert response.status_code == 400


# ── Tests: Cancel Execution ───────────────────────────────────────────────────

def test_cancel_execution_success(client, mock_orchestrator, db_session):
    """Test cancelling an execution via API."""
    # Create a running state
    from agents.orchestrator_state import StateManager
    state_manager = StateManager(db=db_session)
    state = state_manager.create_state(
        sprint_id=108,
        sprint_name="Cancel Test",
        jira_project_key="TEST",
        ticket_queue=["TEST-1"],
    )
    state_manager.start_execution(state.id)
    
    response = client.post(
        "/api/orchestrator/cancel",
        json={
            "state_id": str(state.id),
            "reason": "Test cancellation",
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["state_id"] == str(state.id)
    assert "message" in data


def test_cancel_execution_not_found(client, mock_orchestrator):
    """Test cancelling a non-existent state."""
    fake_id = str(uuid4())
    
    response = client.post(
        "/api/orchestrator/cancel",
        json={
            "state_id": fake_id,
        }
    )
    
    assert response.status_code == 404


# ── Tests: Health Check ───────────────────────────────────────────────────────

def test_health_check(client):
    """Test orchestrator health check endpoint."""
    response = client.get("/api/orchestrator/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert data["service"] == "orchestrator"
    assert "version" in data
