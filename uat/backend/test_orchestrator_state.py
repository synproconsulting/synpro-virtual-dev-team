"""
test_orchestrator_state.py
═════════════════════════
Tests for orchestrator state persistence and resume functionality.

Tests cover:
- State creation and retrieval
- State transitions (pending -> running -> completed/failed/paused)
- Checkpoint saving and restoration
- Ticket completion and failure tracking
- Resume capability from saved states
- Error handling and edge cases
"""

import pytest
import sys
import os
from datetime import datetime
from uuid import UUID

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, OrchestratorState, OrchestratorStatus
from agents.orchestrator_state import StateManager


# ── Fixtures ──────────────────────────────────────────────────────────────────────────


@pytest.fixture
def db_session() -> Session:
    """Create a test database session."""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    
    session = SessionLocal()
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def state_manager(db_session: Session) -> StateManager:
    """Create a StateManager instance with test database."""
    return StateManager(db=db_session)


@pytest.fixture
def sample_ticket_queue() -> list:
    """Sample ticket queue for testing."""
    return ["SDT1-1", "SDT1-2", "SDT1-3", "SDT1-4", "SDT1-5"]


# ── State Creation Tests ─────────────────────────────────────────────────────────────


def test_create_state(state_manager: StateManager, sample_ticket_queue: list):
    """Test creating a new orchestrator state."""
    state = state_manager.create_state(
        sprint_id=42,
        sprint_name="Sprint 10",
        jira_project_key="SDT1",
        ticket_queue=sample_ticket_queue,
    )
    
    assert state.id is not None
    assert isinstance(state.id, UUID)
    assert state.sprint_id == 42
    assert state.sprint_name == "Sprint 10"
    assert state.jira_project_key == "SDT1"
    assert state.status == OrchestratorStatus.PENDING
    assert state.ticket_queue == sample_ticket_queue
    assert state.completed_tickets == []
    assert state.failed_tickets == []
    assert state.current_ticket is None
    assert state.total_tickets == len(sample_ticket_queue)
    assert state.started_at is None
    assert state.completed_at is None


def test_get_state(state_manager: StateManager, sample_ticket_queue: list):
    """Test retrieving a state by ID."""
    created_state = state_manager.create_state(
        sprint_id=42,
        sprint_name="Sprint 10",
        jira_project_key="SDT1",
        ticket_queue=sample_ticket_queue,
    )
    
    retrieved_state = state_manager.get_state(created_state.id)
    
    assert retrieved_state is not None
    assert retrieved_state.id == created_state.id
    assert retrieved_state.sprint_id == created_state.sprint_id
    assert retrieved_state.ticket_queue == created_state.ticket_queue


def test_get_nonexistent_state(state_manager: StateManager):
    """Test retrieving a state that doesn't exist."""
    fake_uuid = UUID("00000000-0000-0000-0000-000000000000")
    state = state_manager.get_state(fake_uuid)
    
    assert state is None


# ── State Transition Tests ───────────────────────────────────────────────────────────


def test_start_execution(state_manager: StateManager, sample_ticket_queue: list):
    """Test starting execution transitions state to RUNNING."""
    state = state_manager.create_state(
        sprint_id=42,
        sprint_name="Sprint 10",
        jira_project_key="SDT1",
        ticket_queue=sample_ticket_queue,
    )
    
    updated_state = state_manager.start_execution(state.id)
    
    assert updated_state.status == OrchestratorStatus.RUNNING
    assert updated_state.started_at is not None
    assert isinstance(updated_state.started_at, datetime)


def test_complete_execution(state_manager: StateManager, sample_ticket_queue: list):
    """Test completing execution transitions state to COMPLETED."""
    state = state_manager.create_state(
        sprint_id=42,
        sprint_name="Sprint 10",
        jira_project_key="SDT1",
        ticket_queue=sample_ticket_queue,
    )
    
    state_manager.start_execution(state.id)
    completed_state = state_manager.complete_execution(state.id)
    
    assert completed_state.status == OrchestratorStatus.COMPLETED
    assert completed_state.completed_at is not None
    assert completed_state.current_ticket is None


def test_pause_execution(state_manager: StateManager, sample_ticket_queue: list):
    """Test pausing execution."""
    state = state_manager.create_state(
        sprint_id=42,
        sprint_name="Sprint 10",
        jira_project_key="SDT1",
        ticket_queue=sample_ticket_queue,
    )
    
    state_manager.start_execution(state.id)
    paused_state = state_manager.pause_execution(state.id, "User requested pause")
    
    assert paused_state.status == OrchestratorStatus.PAUSED
    assert paused_state.error_message == "User requested pause"
    assert paused_state.last_checkpoint_at is not None


def test_fail_execution(state_manager: StateManager, sample_ticket_queue: list):
    """Test failing execution."""
    state = state_manager.create_state(
        sprint_id=42,
        sprint_name="Sprint 10",
        jira_project_key="SDT1",
        ticket_queue=sample_ticket_queue,
    )
    
    state_manager.start_execution(state.id)
    failed_state = state_manager.fail_execution(state.id, "Critical error occurred")
    
    assert failed_state.status == OrchestratorStatus.FAILED
    assert failed_state.error_message == "Critical error occurred"
    assert failed_state.last_checkpoint_at is not None


def test_cancel_execution(state_manager: StateManager, sample_ticket_queue: list):
    """Test canceling execution."""
    state = state_manager.create_state(
        sprint_id=42,
        sprint_name="Sprint 10",
        jira_project_key="SDT1",
        ticket_queue=sample_ticket_queue,
    )
    
    state_manager.start_execution(state.id)
    cancelled_state = state_manager.cancel_execution(state.id, "User cancelled")
    
    assert cancelled_state.status == OrchestratorStatus.CANCELLED
    assert cancelled_state.error_message == "User cancelled"
    assert cancelled_state.completed_at is not None


# ── Checkpoint Tests ─────────────────────────────────────────────────────────────────


def test_checkpoint_update_current_ticket(state_manager: StateManager, sample_ticket_queue: list):
    """Test updating current ticket in checkpoint."""
    state = state_manager.create_state(
        sprint_id=42,
        sprint_name="Sprint 10",
        jira_project_key="SDT1",
        ticket_queue=sample_ticket_queue,
    )
    
    state_manager.start_execution(state.id)
    updated_state = state_manager.checkpoint(state.id, current_ticket="SDT1-1")
    
    assert updated_state.current_ticket == "SDT1-1"
    assert updated_state.last_checkpoint_at is not None


def test_checkpoint_update_multiple_fields(state_manager: StateManager, sample_ticket_queue: list):
    """Test updating multiple fields in checkpoint."""
    state = state_manager.create_state(
        sprint_id=42,
        sprint_name="Sprint 10",
        jira_project_key="SDT1",
        ticket_queue=sample_ticket_queue,
    )
    
    state_manager.start_execution(state.id)
    
    updated_state = state_manager.checkpoint(
        state.id,
        current_ticket="SDT1-2",
        completed_tickets=["SDT1-1"],
        ticket_queue=["SDT1-2", "SDT1-3", "SDT1-4", "SDT1-5"],
    )
    
    assert updated_state.current_ticket == "SDT1-2"
    assert updated_state.completed_tickets == ["SDT1-1"]
    assert len(updated_state.ticket_queue) == 4
    assert updated_state.last_checkpoint_at is not None


# ── Ticket Tracking Tests ────────────────────────────────────────────────────────────


def test_mark_ticket_completed(state_manager: StateManager, sample_ticket_queue: list):
    """Test marking a ticket as completed."""
    state = state_manager.create_state(
        sprint_id=42,
        sprint_name="Sprint 10",
        jira_project_key="SDT1",
        ticket_queue=sample_ticket_queue,
    )
    
    state_manager.start_execution(state.id)
    state_manager.checkpoint(state.id, current_ticket="SDT1-1")
    
    updated_state = state_manager.mark_ticket_completed(state.id, "SDT1-1")
    
    assert "SDT1-1" in updated_state.completed_tickets
    assert "SDT1-1" not in updated_state.ticket_queue
    assert updated_state.current_ticket is None  # Should be cleared
    assert updated_state.last_checkpoint_at is not None


def test_mark_multiple_tickets_completed(state_manager: StateManager, sample_ticket_queue: list):
    """Test marking multiple tickets as completed."""
    state = state_manager.create_state(
        sprint_id=42,
        sprint_name="Sprint 10",
        jira_project_key="SDT1",
        ticket_queue=sample_ticket_queue,
    )
    
    state_manager.start_execution(state.id)
    
    # Complete first ticket
    state_manager.checkpoint(state.id, current_ticket="SDT1-1")
    state1 = state_manager.mark_ticket_completed(state.id, "SDT1-1")
    
    # Complete second ticket
    state_manager.checkpoint(state.id, current_ticket="SDT1-2")
    state2 = state_manager.mark_ticket_completed(state.id, "SDT1-2")
    
    assert len(state2.completed_tickets) == 2
    assert "SDT1-1" in state2.completed_tickets
    assert "SDT1-2" in state2.completed_tickets
    assert len(state2.ticket_queue) == 3


def test_mark_ticket_failed(state_manager: StateManager, sample_ticket_queue: list):
    """Test marking a ticket as failed."""
    state = state_manager.create_state(
        sprint_id=42,
        sprint_name="Sprint 10",
        jira_project_key="SDT1",
        ticket_queue=sample_ticket_queue,
    )
    
    state_manager.start_execution(state.id)
    state_manager.checkpoint(state.id, current_ticket="SDT1-1")
    
    updated_state = state_manager.mark_ticket_failed(
        state.id,
        "SDT1-1",
        "Test execution failed",
    )
    
    assert len(updated_state.failed_tickets) == 1
    assert updated_state.failed_tickets[0]["ticket_key"] == "SDT1-1"
    assert updated_state.failed_tickets[0]["error_message"] == "Test execution failed"
    assert "timestamp" in updated_state.failed_tickets[0]
    assert "SDT1-1" not in updated_state.ticket_queue
    assert updated_state.current_ticket is None


def test_mark_multiple_tickets_failed(state_manager: StateManager, sample_ticket_queue: list):
    """Test marking multiple tickets as failed."""
    state = state_manager.create_state(
        sprint_id=42,
        sprint_name="Sprint 10",
        jira_project_key="SDT1",
        ticket_queue=sample_ticket_queue,
    )
    
    state_manager.start_execution(state.id)
    
    # Fail first ticket
    state_manager.checkpoint(state.id, current_ticket="SDT1-1")
    state1 = state_manager.mark_ticket_failed(state.id, "SDT1-1", "Error 1")
    
    # Fail second ticket
    state_manager.checkpoint(state.id, current_ticket="SDT1-2")
    state2 = state_manager.mark_ticket_failed(state.id, "SDT1-2", "Error 2")
    
    assert len(state2.failed_tickets) == 2
    assert state2.failed_tickets[0]["ticket_key"] == "SDT1-1"
    assert state2.failed_tickets[1]["ticket_key"] == "SDT1-2"


# ── Resume Capability Tests ──────────────────────────────────────────────────────────


def test_get_resumable_states_paused(state_manager: StateManager, sample_ticket_queue: list):
    """Test getting resumable states (PAUSED)."""
    # Create multiple states
    state1 = state_manager.create_state(42, "Sprint 10", "SDT1", sample_ticket_queue)
    state2 = state_manager.create_state(43, "Sprint 11", "SDT1", sample_ticket_queue)
    state3 = state_manager.create_state(44, "Sprint 12", "SDT1", sample_ticket_queue)
    
    # Set different statuses
    state_manager.start_execution(state1.id)
    state_manager.pause_execution(state1.id)
    
    state_manager.start_execution(state2.id)
    state_manager.complete_execution(state2.id)
    
    state_manager.start_execution(state3.id)
    # Leave state3 running
    
    # Get resumable states
    resumable = state_manager.get_resumable_states()
    
    assert len(resumable) == 1
    assert resumable[0].id == state1.id
    assert resumable[0].status == OrchestratorStatus.PAUSED


def test_get_resumable_states_failed(state_manager: StateManager, sample_ticket_queue: list):
    """Test getting resumable states (FAILED)."""
    state = state_manager.create_state(42, "Sprint 10", "SDT1", sample_ticket_queue)
    
    state_manager.start_execution(state.id)
    state_manager.fail_execution(state.id, "Test error")
    
    resumable = state_manager.get_resumable_states()
    
    assert len(resumable) == 1
    assert resumable[0].id == state.id
    assert resumable[0].status == OrchestratorStatus.FAILED


def test_get_resumable_states_multiple(state_manager: StateManager, sample_ticket_queue: list):
    """Test getting multiple resumable states."""
    state1 = state_manager.create_state(42, "Sprint 10", "SDT1", sample_ticket_queue)
    state2 = state_manager.create_state(43, "Sprint 11", "SDT1", sample_ticket_queue)
    
    state_manager.start_execution(state1.id)
    state_manager.pause_execution(state1.id)
    
    state_manager.start_execution(state2.id)
    state_manager.fail_execution(state2.id, "Error")
    
    resumable = state_manager.get_resumable_states()
    
    assert len(resumable) == 2
    resumable_ids = {s.id for s in resumable}
    assert state1.id in resumable_ids
    assert state2.id in resumable_ids


def test_get_resumable_states_empty(state_manager: StateManager, sample_ticket_queue: list):
    """Test getting resumable states when none exist."""
    state = state_manager.create_state(42, "Sprint 10", "SDT1", sample_ticket_queue)
    state_manager.start_execution(state.id)
    state_manager.complete_execution(state.id)
    
    resumable = state_manager.get_resumable_states()
    
    assert len(resumable) == 0


def test_resume_from_paused_state(state_manager: StateManager, sample_ticket_queue: list):
    """Test resuming from a paused state."""
    state = state_manager.create_state(42, "Sprint 10", "SDT1", sample_ticket_queue)
    
    # Start and pause
    state_manager.start_execution(state.id)
    state_manager.checkpoint(state.id, current_ticket="SDT1-1")
    state_manager.mark_ticket_completed(state.id, "SDT1-1")
    state_manager.pause_execution(state.id)
    
    # Verify paused state
    paused = state_manager.get_state(state.id)
    assert paused.status == OrchestratorStatus.PAUSED
    assert len(paused.completed_tickets) == 1
    assert len(paused.ticket_queue) == 4
    
    # Resume
    resumed = state_manager.start_execution(state.id)
    
    assert resumed.status == OrchestratorStatus.RUNNING
    assert len(resumed.completed_tickets) == 1  # Should preserve completed tickets
    assert len(resumed.ticket_queue) == 4  # Should preserve remaining queue


def test_resume_from_failed_state(state_manager: StateManager, sample_ticket_queue: list):
    """Test resuming from a failed state."""
    state = state_manager.create_state(42, "Sprint 10", "SDT1", sample_ticket_queue)
    
    # Start, complete one, fail another
    state_manager.start_execution(state.id)
    state_manager.mark_ticket_completed(state.id, "SDT1-1")
    state_manager.mark_ticket_failed(state.id, "SDT1-2", "Test error")
    state_manager.fail_execution(state.id, "Sprint failed")
    
    # Verify failed state
    failed = state_manager.get_state(state.id)
    assert failed.status == OrchestratorStatus.FAILED
    assert len(failed.completed_tickets) == 1
    assert len(failed.failed_tickets) == 1
    assert len(failed.ticket_queue) == 3
    
    # Resume
    resumed = state_manager.start_execution(state.id)
    
    assert resumed.status == OrchestratorStatus.RUNNING
    assert len(resumed.completed_tickets) == 1  # Should preserve history
    assert len(resumed.failed_tickets) == 1  # Should preserve failed history
    assert len(resumed.ticket_queue) == 3  # Should resume with remaining tickets


# ── Progress Tracking Tests ──────────────────────────────────────────────────────────


def test_get_progress(state_manager: StateManager, sample_ticket_queue: list):
    """Test getting progress information."""
    state = state_manager.create_state(42, "Sprint 10", "SDT1", sample_ticket_queue)
    
    state_manager.start_execution(state.id)
    state_manager.mark_ticket_completed(state.id, "SDT1-1")
    state_manager.mark_ticket_completed(state.id, "SDT1-2")
    state_manager.mark_ticket_failed(state.id, "SDT1-3", "Error")
    
    progress = state_manager.get_progress(state.id)
    
    assert progress["state_id"] == str(state.id)
    assert progress["sprint_id"] == 42
    assert progress["sprint_name"] == "Sprint 10"
    assert progress["status"] == OrchestratorStatus.RUNNING.value
    assert progress["total_tickets"] == 5
    assert progress["completed_tickets"] == 2
    assert progress["failed_tickets"] == 1
    assert progress["remaining_tickets"] == 2
    assert progress["progress_percentage"] == 40.0  # 2 completed out of 5
    assert progress["started_at"] is not None


def test_get_progress_zero_tickets(state_manager: StateManager):
    """Test getting progress with zero tickets."""
    state = state_manager.create_state(42, "Sprint 10", "SDT1", [])
    
    progress = state_manager.get_progress(state.id)
    
    assert progress["total_tickets"] == 0
    assert progress["completed_tickets"] == 0
    assert progress["failed_tickets"] == 0
    assert progress["remaining_tickets"] == 0
    assert progress["progress_percentage"] == 0.0


def test_get_progress_all_completed(state_manager: StateManager, sample_ticket_queue: list):
    """Test getting progress when all tickets completed."""
    state = state_manager.create_state(42, "Sprint 10", "SDT1", sample_ticket_queue)
    
    state_manager.start_execution(state.id)
    for ticket in sample_ticket_queue:
        state_manager.mark_ticket_completed(state.id, ticket)
    
    progress = state_manager.get_progress(state.id)
    
    assert progress["completed_tickets"] == 5
    assert progress["remaining_tickets"] == 0
    assert progress["progress_percentage"] == 100.0


# ── Latest State Tests ───────────────────────────────────────────────────────────────


def test_get_latest_state_for_sprint(state_manager: StateManager, sample_ticket_queue: list):
    """Test getting the most recent state for a sprint."""
    # Create multiple states for same sprint
    state1 = state_manager.create_state(42, "Sprint 10", "SDT1", sample_ticket_queue)
    state2 = state_manager.create_state(42, "Sprint 10", "SDT1", sample_ticket_queue)
    state3 = state_manager.create_state(42, "Sprint 10", "SDT1", sample_ticket_queue)
    
    latest = state_manager.get_latest_state_for_sprint(42)
    
    assert latest is not None
    assert latest.id == state3.id  # Should be the most recent


def test_get_latest_state_for_nonexistent_sprint(state_manager: StateManager):
    """Test getting latest state for a sprint with no states."""
    latest = state_manager.get_latest_state_for_sprint(999)
    
    assert latest is None


# ── Error Handling Tests ─────────────────────────────────────────────────────────────


def test_start_execution_invalid_id(state_manager: StateManager):
    """Test starting execution with invalid state ID."""
    fake_uuid = UUID("00000000-0000-0000-0000-000000000000")
    
    with pytest.raises(ValueError, match="State .* not found"):
        state_manager.start_execution(fake_uuid)


def test_checkpoint_invalid_id(state_manager: StateManager):
    """Test checkpoint with invalid state ID."""
    fake_uuid = UUID("00000000-0000-0000-0000-000000000000")
    
    with pytest.raises(ValueError, match="State .* not found"):
        state_manager.checkpoint(fake_uuid, current_ticket="SDT1-1")


def test_get_progress_invalid_id(state_manager: StateManager):
    """Test getting progress with invalid state ID."""
    fake_uuid = UUID("00000000-0000-0000-0000-000000000000")
    
    with pytest.raises(ValueError, match="State .* not found"):
        state_manager.get_progress(fake_uuid)
