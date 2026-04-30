"""
Tests for orchestrator state management.
"""

import pytest
from datetime import datetime
from uuid import uuid4

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, OrchestratorState, OrchestratorStatus
from database import SessionLocal

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
def state_manager(db_session):
    """Create a state manager with test database session."""
    return StateManager(db=db_session)


def test_create_state(state_manager):
    """Test creating a new orchestrator state."""
    state = state_manager.create_state(
        sprint_id=123,
        sprint_name="Sprint 1",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1", "SDT1-2", "SDT1-3"],
    )
    
    assert state.id is not None
    assert state.sprint_id == 123
    assert state.sprint_name == "Sprint 1"
    assert state.jira_project_key == "SDT1"
    assert state.status == OrchestratorStatus.PENDING
    assert state.ticket_queue == ["SDT1-1", "SDT1-2", "SDT1-3"]
    assert state.completed_tickets == []
    assert state.failed_tickets == []
    assert state.current_ticket is None
    assert state.total_tickets == 3


def test_get_state(state_manager):
    """Test retrieving a state by ID."""
    created_state = state_manager.create_state(
        sprint_id=123,
        sprint_name="Sprint 1",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1"],
    )
    
    retrieved_state = state_manager.get_state(created_state.id)
    
    assert retrieved_state is not None
    assert retrieved_state.id == created_state.id
    assert retrieved_state.sprint_id == 123


def test_get_state_not_found(state_manager):
    """Test retrieving a non-existent state returns None."""
    state = state_manager.get_state(uuid4())
    assert state is None


def test_get_latest_state_for_sprint(state_manager):
    """Test getting the latest state for a sprint."""
    # Create multiple states for same sprint
    state1 = state_manager.create_state(
        sprint_id=123,
        sprint_name="Sprint 1",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1"],
    )
    
    state2 = state_manager.create_state(
        sprint_id=123,
        sprint_name="Sprint 1",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-2"],
    )
    
    latest = state_manager.get_latest_state_for_sprint(123)
    
    assert latest is not None
    assert latest.id == state2.id


def test_start_execution(state_manager):
    """Test starting execution of a state."""
    state = state_manager.create_state(
        sprint_id=123,
        sprint_name="Sprint 1",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1"],
    )
    
    started_state = state_manager.start_execution(state.id)
    
    assert started_state.status == OrchestratorStatus.RUNNING
    assert started_state.started_at is not None


def test_checkpoint(state_manager):
    """Test saving a checkpoint."""
    state = state_manager.create_state(
        sprint_id=123,
        sprint_name="Sprint 1",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1", "SDT1-2"],
    )
    
    updated_state = state_manager.checkpoint(
        state.id,
        current_ticket="SDT1-1",
        completed_tickets=["SDT1-0"],
    )
    
    assert updated_state.current_ticket == "SDT1-1"
    assert updated_state.completed_tickets == ["SDT1-0"]
    assert updated_state.last_checkpoint_at is not None


def test_mark_ticket_completed(state_manager):
    """Test marking a ticket as completed."""
    state = state_manager.create_state(
        sprint_id=123,
        sprint_name="Sprint 1",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1", "SDT1-2", "SDT1-3"],
    )
    
    state_manager.checkpoint(state.id, current_ticket="SDT1-1")
    
    updated_state = state_manager.mark_ticket_completed(state.id, "SDT1-1")
    
    assert "SDT1-1" in updated_state.completed_tickets
    assert "SDT1-1" not in updated_state.ticket_queue
    assert updated_state.current_ticket is None
    assert len(updated_state.ticket_queue) == 2


def test_mark_ticket_failed(state_manager):
    """Test marking a ticket as failed."""
    state = state_manager.create_state(
        sprint_id=123,
        sprint_name="Sprint 1",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1", "SDT1-2"],
    )
    
    state_manager.checkpoint(state.id, current_ticket="SDT1-1")
    
    updated_state = state_manager.mark_ticket_failed(
        state.id,
        "SDT1-1",
        "Test error message",
    )
    
    assert len(updated_state.failed_tickets) == 1
    assert updated_state.failed_tickets[0]["ticket_key"] == "SDT1-1"
    assert updated_state.failed_tickets[0]["error_message"] == "Test error message"
    assert "SDT1-1" not in updated_state.ticket_queue
    assert updated_state.current_ticket is None


def test_pause_execution(state_manager):
    """Test pausing execution."""
    state = state_manager.create_state(
        sprint_id=123,
        sprint_name="Sprint 1",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1"],
    )
    
    state_manager.start_execution(state.id)
    
    paused_state = state_manager.pause_execution(state.id, "User requested")
    
    assert paused_state.status == OrchestratorStatus.PAUSED
    assert paused_state.error_message == "User requested"


def test_complete_execution(state_manager):
    """Test completing execution."""
    state = state_manager.create_state(
        sprint_id=123,
        sprint_name="Sprint 1",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1"],
    )
    
    state_manager.start_execution(state.id)
    
    completed_state = state_manager.complete_execution(state.id)
    
    assert completed_state.status == OrchestratorStatus.COMPLETED
    assert completed_state.completed_at is not None
    assert completed_state.current_ticket is None


def test_fail_execution(state_manager):
    """Test failing execution."""
    state = state_manager.create_state(
        sprint_id=123,
        sprint_name="Sprint 1",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1"],
    )
    
    state_manager.start_execution(state.id)
    
    failed_state = state_manager.fail_execution(state.id, "Critical error")
    
    assert failed_state.status == OrchestratorStatus.FAILED
    assert failed_state.error_message == "Critical error"


def test_cancel_execution(state_manager):
    """Test cancelling execution."""
    state = state_manager.create_state(
        sprint_id=123,
        sprint_name="Sprint 1",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1"],
    )
    
    cancelled_state = state_manager.cancel_execution(state.id, "User cancelled")
    
    assert cancelled_state.status == OrchestratorStatus.CANCELLED
    assert cancelled_state.error_message == "User cancelled"
    assert cancelled_state.completed_at is not None


def test_get_resumable_states(state_manager):
    """Test getting resumable states."""
    # Create states with different statuses
    state1 = state_manager.create_state(
        sprint_id=1,
        sprint_name="Sprint 1",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1"],
    )
    state_manager.pause_execution(state1.id)
    
    state2 = state_manager.create_state(
        sprint_id=2,
        sprint_name="Sprint 2",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-2"],
    )
    state_manager.start_execution(state2.id)
    state_manager.fail_execution(state2.id, "Error")
    
    state3 = state_manager.create_state(
        sprint_id=3,
        sprint_name="Sprint 3",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-3"],
    )
    state_manager.complete_execution(state3.id)
    
    resumable = state_manager.get_resumable_states()
    
    assert len(resumable) == 2
    resumable_ids = [s.id for s in resumable]
    assert state1.id in resumable_ids
    assert state2.id in resumable_ids
    assert state3.id not in resumable_ids


def test_get_progress(state_manager):
    """Test getting execution progress."""
    state = state_manager.create_state(
        sprint_id=123,
        sprint_name="Sprint 1",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1", "SDT1-2", "SDT1-3", "SDT1-4"],
    )
    
    state_manager.start_execution(state.id)
    state_manager.mark_ticket_completed(state.id, "SDT1-1")
    state_manager.mark_ticket_completed(state.id, "SDT1-2")
    state_manager.mark_ticket_failed(state.id, "SDT1-3", "Error")
    
    progress = state_manager.get_progress(state.id)
    
    assert progress["total_tickets"] == 4
    assert progress["completed_tickets"] == 2
    assert progress["failed_tickets"] == 1
    assert progress["remaining_tickets"] == 1
    assert progress["progress_percentage"] == 50.0
    assert progress["status"] == OrchestratorStatus.RUNNING.value


def test_context_manager(db_session):
    """Test StateManager context manager."""
    with StateManager(db=db_session) as manager:
        state = manager.create_state(
            sprint_id=123,
            sprint_name="Sprint 1",
            jira_project_key="SDT1",
            ticket_queue=["SDT1-1"],
        )
        assert state.id is not None
