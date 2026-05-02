"""
tests/test_orchestrator_state.py
─────────────────────────────────
Tests for orchestrator state persistence and recovery.

Tests cover:
- Creating and persisting orchestrator states
- Checkpointing during execution
- Marking tickets as completed or failed
- Pausing, resuming, and cancelling executions
- Progress tracking
- Listing resumable states
"""

import os
import sys
from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from models import Base, OrchestratorState, OrchestratorStatus
from agents.orchestrator_state import StateManager


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
def state_manager(db_session):
    """Create a StateManager instance for testing."""
    return StateManager(db=db_session)


@pytest.fixture
def sample_state(state_manager):
    """Create a sample orchestrator state for testing."""
    return state_manager.create_state(
        sprint_id=123,
        sprint_name="Test Sprint",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1", "SDT1-2", "SDT1-3"],
    )


# ── Tests: State Creation ─────────────────────────────────────────────────────

def test_create_state(state_manager):
    """Test creating a new orchestrator state."""
    state = state_manager.create_state(
        sprint_id=100,
        sprint_name="Sprint 1",
        jira_project_key="TEST",
        ticket_queue=["TEST-1", "TEST-2"],
    )
    
    assert state.id is not None
    assert state.sprint_id == 100
    assert state.sprint_name == "Sprint 1"
    assert state.jira_project_key == "TEST"
    assert state.status == OrchestratorStatus.PENDING
    assert state.ticket_queue == ["TEST-1", "TEST-2"]
    assert state.completed_tickets == []
    assert state.failed_tickets == []
    assert state.current_ticket is None
    assert state.total_tickets == 2
    assert state.started_at is None
    assert state.completed_at is None


def test_create_state_with_empty_queue(state_manager):
    """Test creating a state with no tickets."""
    state = state_manager.create_state(
        sprint_id=101,
        sprint_name="Empty Sprint",
        jira_project_key="TEST",
        ticket_queue=[],
    )
    
    assert state.total_tickets == 0
    assert state.ticket_queue == []


# ── Tests: State Retrieval ────────────────────────────────────────────────────

def test_get_state(state_manager, sample_state):
    """Test retrieving a state by ID."""
    retrieved = state_manager.get_state(sample_state.id)
    
    assert retrieved is not None
    assert retrieved.id == sample_state.id
    assert retrieved.sprint_id == sample_state.sprint_id
    assert retrieved.sprint_name == sample_state.sprint_name


def test_get_state_not_found(state_manager):
    """Test retrieving a non-existent state."""
    fake_id = uuid4()
    retrieved = state_manager.get_state(fake_id)
    
    assert retrieved is None


def test_get_latest_state_for_sprint(state_manager):
    """Test retrieving the most recent state for a sprint."""
    # Create multiple states for the same sprint
    state1 = state_manager.create_state(
        sprint_id=200,
        sprint_name="Sprint 2",
        jira_project_key="TEST",
        ticket_queue=["TEST-1"],
    )
    
    state2 = state_manager.create_state(
        sprint_id=200,
        sprint_name="Sprint 2",
        jira_project_key="TEST",
        ticket_queue=["TEST-2"],
    )
    
    latest = state_manager.get_latest_state_for_sprint(200)
    
    assert latest is not None
    assert latest.id == state2.id  # Should be the most recent


def test_get_latest_state_for_sprint_not_found(state_manager):
    """Test retrieving latest state for non-existent sprint."""
    latest = state_manager.get_latest_state_for_sprint(999)
    assert latest is None


# ── Tests: Execution Lifecycle ────────────────────────────────────────────────

def test_start_execution(state_manager, sample_state):
    """Test starting execution."""
    state = state_manager.start_execution(sample_state.id)
    
    assert state.status == OrchestratorStatus.RUNNING
    assert state.started_at is not None
    assert isinstance(state.started_at, datetime)


def test_start_execution_idempotent(state_manager, sample_state):
    """Test that starting execution multiple times doesn't reset start time."""
    state1 = state_manager.start_execution(sample_state.id)
    first_start = state1.started_at
    
    state2 = state_manager.start_execution(sample_state.id)
    
    assert state2.started_at == first_start


def test_complete_execution(state_manager, sample_state):
    """Test completing execution."""
    state_manager.start_execution(sample_state.id)
    state = state_manager.complete_execution(sample_state.id)
    
    assert state.status == OrchestratorStatus.COMPLETED
    assert state.completed_at is not None
    assert state.current_ticket is None


def test_fail_execution(state_manager, sample_state):
    """Test failing execution."""
    error_msg = "Something went wrong"
    state = state_manager.fail_execution(sample_state.id, error_msg)
    
    assert state.status == OrchestratorStatus.FAILED
    assert state.error_message == error_msg
    assert state.last_checkpoint_at is not None


def test_pause_execution(state_manager, sample_state):
    """Test pausing execution."""
    reason = "User requested pause"
    state = state_manager.pause_execution(sample_state.id, reason)
    
    assert state.status == OrchestratorStatus.PAUSED
    assert state.error_message == reason
    assert state.last_checkpoint_at is not None


def test_cancel_execution(state_manager, sample_state):
    """Test cancelling execution."""
    reason = "Sprint cancelled"
    state = state_manager.cancel_execution(sample_state.id, reason)
    
    assert state.status == OrchestratorStatus.CANCELLED
    assert state.error_message == reason
    assert state.completed_at is not None


# ── Tests: Checkpointing ──────────────────────────────────────────────────────

def test_checkpoint_current_ticket(state_manager, sample_state):
    """Test checkpointing with current ticket update."""
    state = state_manager.checkpoint(sample_state.id, current_ticket="SDT1-1")
    
    assert state.current_ticket == "SDT1-1"
    assert state.last_checkpoint_at is not None


def test_checkpoint_all_fields(state_manager, sample_state):
    """Test checkpointing with all field updates."""
    state = state_manager.checkpoint(
        sample_state.id,
        current_ticket="SDT1-2",
        completed_tickets=["SDT1-1"],
        failed_tickets=[{"ticket_key": "SDT1-3", "error": "Failed"}],
        ticket_queue=["SDT1-2"],
    )
    
    assert state.current_ticket == "SDT1-2"
    assert state.completed_tickets == ["SDT1-1"]
    assert state.failed_tickets == [{"ticket_key": "SDT1-3", "error": "Failed"}]
    assert state.ticket_queue == ["SDT1-2"]
    assert state.last_checkpoint_at is not None


def test_checkpoint_partial_update(state_manager, sample_state):
    """Test that checkpoint only updates provided fields."""
    # First checkpoint
    state1 = state_manager.checkpoint(
        sample_state.id,
        current_ticket="SDT1-1",
        completed_tickets=["SDT1-0"],
    )
    
    # Second checkpoint - only update current_ticket
    state2 = state_manager.checkpoint(
        sample_state.id,
        current_ticket="SDT1-2",
    )
    
    assert state2.current_ticket == "SDT1-2"
    assert state2.completed_tickets == ["SDT1-0"]  # Should be preserved


# ── Tests: Ticket Management ──────────────────────────────────────────────────

def test_mark_ticket_completed(state_manager, sample_state):
    """Test marking a ticket as completed."""
    state = state_manager.mark_ticket_completed(sample_state.id, "SDT1-1")
    
    assert "SDT1-1" in state.completed_tickets
    assert "SDT1-1" not in state.ticket_queue
    assert state.last_checkpoint_at is not None


def test_mark_ticket_completed_clears_current(state_manager, sample_state):
    """Test that completing a ticket clears current_ticket if it matches."""
    state_manager.checkpoint(sample_state.id, current_ticket="SDT1-1")
    state = state_manager.mark_ticket_completed(sample_state.id, "SDT1-1")
    
    assert state.current_ticket is None


def test_mark_ticket_completed_preserves_other_current(state_manager, sample_state):
    """Test that completing a ticket doesn't clear a different current_ticket."""
    state_manager.checkpoint(sample_state.id, current_ticket="SDT1-2")
    state = state_manager.mark_ticket_completed(sample_state.id, "SDT1-1")
    
    assert state.current_ticket == "SDT1-2"


def test_mark_ticket_failed(state_manager, sample_state):
    """Test marking a ticket as failed."""
    error_msg = "Test failed"
    state = state_manager.mark_ticket_failed(sample_state.id, "SDT1-2", error_msg)
    
    assert len(state.failed_tickets) == 1
    assert state.failed_tickets[0]["ticket_key"] == "SDT1-2"
    assert state.failed_tickets[0]["error_message"] == error_msg
    assert "timestamp" in state.failed_tickets[0]
    assert "SDT1-2" not in state.ticket_queue
    assert state.last_checkpoint_at is not None


def test_mark_multiple_tickets_failed(state_manager, sample_state):
    """Test marking multiple tickets as failed."""
    state_manager.mark_ticket_failed(sample_state.id, "SDT1-1", "Error 1")
    state = state_manager.mark_ticket_failed(sample_state.id, "SDT1-2", "Error 2")
    
    assert len(state.failed_tickets) == 2
    assert state.failed_tickets[0]["ticket_key"] == "SDT1-1"
    assert state.failed_tickets[1]["ticket_key"] == "SDT1-2"


# ── Tests: Progress Tracking ──────────────────────────────────────────────────

def test_get_progress_initial(state_manager, sample_state):
    """Test progress for a newly created state."""
    progress = state_manager.get_progress(sample_state.id)
    
    assert progress["state_id"] == str(sample_state.id)
    assert progress["sprint_id"] == 123
    assert progress["sprint_name"] == "Test Sprint"
    assert progress["status"] == OrchestratorStatus.PENDING.value
    assert progress["total_tickets"] == 3
    assert progress["completed_tickets"] == 0
    assert progress["failed_tickets"] == 0
    assert progress["remaining_tickets"] == 3
    assert progress["progress_percentage"] == 0.0


def test_get_progress_partial(state_manager, sample_state):
    """Test progress with some tickets completed."""
    state_manager.start_execution(sample_state.id)
    state_manager.mark_ticket_completed(sample_state.id, "SDT1-1")
    state_manager.mark_ticket_failed(sample_state.id, "SDT1-2", "Failed")
    
    progress = state_manager.get_progress(sample_state.id)
    
    assert progress["completed_tickets"] == 1
    assert progress["failed_tickets"] == 1
    assert progress["remaining_tickets"] == 1
    assert progress["progress_percentage"] == pytest.approx(33.33, abs=0.01)


def test_get_progress_complete(state_manager, sample_state):
    """Test progress for completed execution."""
    state_manager.start_execution(sample_state.id)
    state_manager.mark_ticket_completed(sample_state.id, "SDT1-1")
    state_manager.mark_ticket_completed(sample_state.id, "SDT1-2")
    state_manager.mark_ticket_completed(sample_state.id, "SDT1-3")
    
    progress = state_manager.get_progress(sample_state.id)
    
    assert progress["completed_tickets"] == 3
    assert progress["failed_tickets"] == 0
    assert progress["remaining_tickets"] == 0
    assert progress["progress_percentage"] == 100.0


def test_get_progress_not_found(state_manager):
    """Test getting progress for non-existent state."""
    fake_id = uuid4()
    
    with pytest.raises(ValueError, match="not found"):
        state_manager.get_progress(fake_id)


# ── Tests: Resumable States ───────────────────────────────────────────────────

def test_get_resumable_states_empty(state_manager):
    """Test getting resumable states when none exist."""
    resumable = state_manager.get_resumable_states()
    assert resumable == []


def test_get_resumable_states_paused(state_manager, sample_state):
    """Test getting resumable states includes paused executions."""
    state_manager.pause_execution(sample_state.id)
    
    resumable = state_manager.get_resumable_states()
    
    assert len(resumable) == 1
    assert resumable[0].id == sample_state.id
    assert resumable[0].status == OrchestratorStatus.PAUSED


def test_get_resumable_states_failed(state_manager, sample_state):
    """Test getting resumable states includes failed executions."""
    state_manager.fail_execution(sample_state.id, "Error occurred")
    
    resumable = state_manager.get_resumable_states()
    
    assert len(resumable) == 1
    assert resumable[0].id == sample_state.id
    assert resumable[0].status == OrchestratorStatus.FAILED


def test_get_resumable_states_excludes_completed(state_manager, sample_state):
    """Test that completed states are not resumable."""
    state_manager.complete_execution(sample_state.id)
    
    resumable = state_manager.get_resumable_states()
    
    assert len(resumable) == 0


def test_get_resumable_states_excludes_cancelled(state_manager, sample_state):
    """Test that cancelled states are not resumable."""
    state_manager.cancel_execution(sample_state.id)
    
    resumable = state_manager.get_resumable_states()
    
    assert len(resumable) == 0


def test_get_resumable_states_multiple(state_manager):
    """Test getting multiple resumable states."""
    # Create several states with different statuses
    state1 = state_manager.create_state(300, "S1", "TEST", ["T-1"])
    state2 = state_manager.create_state(301, "S2", "TEST", ["T-2"])
    state3 = state_manager.create_state(302, "S3", "TEST", ["T-3"])
    state4 = state_manager.create_state(303, "S4", "TEST", ["T-4"])
    
    state_manager.pause_execution(state1.id)
    state_manager.fail_execution(state2.id, "Error")
    state_manager.complete_execution(state3.id)
    # state4 remains PENDING
    
    resumable = state_manager.get_resumable_states()
    
    assert len(resumable) == 2
    resumable_ids = {s.id for s in resumable}
    assert state1.id in resumable_ids
    assert state2.id in resumable_ids


# ── Tests: Error Handling ─────────────────────────────────────────────────────

def test_operation_on_nonexistent_state(state_manager):
    """Test that operations on non-existent states raise errors."""
    fake_id = uuid4()
    
    with pytest.raises(ValueError, match="not found"):
        state_manager.start_execution(fake_id)
    
    with pytest.raises(ValueError, match="not found"):
        state_manager.checkpoint(fake_id, current_ticket="TEST-1")
    
    with pytest.raises(ValueError, match="not found"):
        state_manager.mark_ticket_completed(fake_id, "TEST-1")
    
    with pytest.raises(ValueError, match="not found"):
        state_manager.mark_ticket_failed(fake_id, "TEST-1", "Error")
    
    with pytest.raises(ValueError, match="not found"):
        state_manager.pause_execution(fake_id)
    
    with pytest.raises(ValueError, match="not found"):
        state_manager.complete_execution(fake_id)
    
    with pytest.raises(ValueError, match="not found"):
        state_manager.fail_execution(fake_id, "Error")
    
    with pytest.raises(ValueError, match="not found"):
        state_manager.cancel_execution(fake_id)


# ── Tests: Context Manager ────────────────────────────────────────────────────

def test_state_manager_context_manager():
    """Test StateManager as a context manager."""
    with StateManager() as sm:
        # Should create its own session
        assert sm.db is not None
        
        # Should be able to create a state
        state = sm.create_state(
            sprint_id=400,
            sprint_name="Context Test",
            jira_project_key="TEST",
            ticket_queue=["TEST-1"],
        )
        
        assert state.id is not None
