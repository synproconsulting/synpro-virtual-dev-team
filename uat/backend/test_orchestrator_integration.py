"""
test_orchestrator_integration.py
════════════════════════════════
Integration tests for orchestrator crash recovery and resume scenarios.

Tests realistic scenarios:
- Complete sprint execution
- Simulated crash and recovery
- Manual pause and resume
- Ticket failure handling
- Progress monitoring
"""

import pytest
import sys
import os
from uuid import UUID
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, OrchestratorStatus
from agents.orchestrator import Orchestrator, TicketExecutionError
from agents.orchestrator_state import StateManager


# ── Fixtures ──────────────────────────────────────────────────────────────────────────


@pytest.fixture
def db_session() -> Session:
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    
    session = SessionLocal()
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def orchestrator(db_session: Session) -> Orchestrator:
    """Create an Orchestrator instance with test database."""
    return Orchestrator(
        jira_project_key="SDT1",
        db=db_session,
        verbose=False,  # Disable logging for tests
    )


@pytest.fixture
def mock_tickets():
    """Mock ticket data for testing."""
    return [
        {"key": "SDT1-1", "summary": "First ticket", "execution_order": 1},
        {"key": "SDT1-2", "summary": "Second ticket", "execution_order": 2},
        {"key": "SDT1-3", "summary": "Third ticket", "execution_order": 3},
        {"key": "SDT1-4", "summary": "Fourth ticket", "execution_order": 4},
        {"key": "SDT1-5", "summary": "Fifth ticket", "execution_order": 5},
    ]


# ── Complete Execution Tests ─────────────────────────────────────────────────────────


def test_complete_sprint_execution_success(orchestrator: Orchestrator, mock_tickets):
    """Test successful execution of a complete sprint."""
    # Mock ticket fetching and execution
    with patch.object(orchestrator, 'get_sprint_tickets', return_value=mock_tickets):
        with patch.object(orchestrator, 'execute_ticket', return_value=True):
            state_id = orchestrator.start_sprint(
                sprint_id=42,
                sprint_name="Sprint 10",
            )
    
    # Verify final state
    state = orchestrator.state_manager.get_state(state_id)
    
    assert state.status == OrchestratorStatus.COMPLETED
    assert len(state.completed_tickets) == 5
    assert len(state.failed_tickets) == 0
    assert len(state.ticket_queue) == 0
    assert state.completed_at is not None


def test_sprint_execution_with_failures(orchestrator: Orchestrator, mock_tickets):
    """Test sprint execution with some ticket failures."""
    # Mock execution to fail on specific tickets
    def mock_execute(ticket_key):
        if ticket_key in ["SDT1-2", "SDT1-4"]:
            raise TicketExecutionError(f"Execution failed for {ticket_key}")
        return True
    
    with patch.object(orchestrator, 'get_sprint_tickets', return_value=mock_tickets):
        with patch.object(orchestrator, 'execute_ticket', side_effect=mock_execute):
            state_id = orchestrator.start_sprint(
                sprint_id=42,
                sprint_name="Sprint 10",
            )
    
    # Verify final state
    state = orchestrator.state_manager.get_state(state_id)
    
    assert state.status == OrchestratorStatus.COMPLETED
    assert len(state.completed_tickets) == 3  # 1, 3, 5
    assert len(state.failed_tickets) == 2  # 2, 4
    assert len(state.ticket_queue) == 0
    
    # Verify failed ticket details
    failed_keys = [f["ticket_key"] for f in state.failed_tickets]
    assert "SDT1-2" in failed_keys
    assert "SDT1-4" in failed_keys


# ── Crash Recovery Tests ─────────────────────────────────────────────────────────────


def test_crash_recovery_scenario(db_session: Session, mock_tickets):
    """Test crash recovery: execution stops mid-way and resumes later."""
    
    # Phase 1: Initial execution that crashes after 2 tickets
    execution_count = {"count": 0}
    
    def mock_execute_with_crash(ticket_key):
        execution_count["count"] += 1
        if execution_count["count"] > 2:
            # Simulate crash by raising exception
            raise RuntimeError("Simulated system crash")
        return True
    
    orchestrator1 = Orchestrator(
        jira_project_key="SDT1",
        db=db_session,
        verbose=False,
    )
    
    with patch.object(orchestrator1, 'get_sprint_tickets', return_value=mock_tickets):
        with patch.object(orchestrator1, 'execute_ticket', side_effect=mock_execute_with_crash):
            try:
                state_id = orchestrator1.start_sprint(
                    sprint_id=42,
                    sprint_name="Sprint 10",
                )
            except RuntimeError:
                pass  # Expected crash
    
    # Verify state after crash
    state_manager = StateManager(db=db_session)
    state = state_manager.get_state(state_id)
    
    assert state is not None
    assert state.status == OrchestratorStatus.FAILED
    assert len(state.completed_tickets) == 2  # SDT1-1, SDT1-2 completed
    assert len(state.ticket_queue) == 2  # SDT1-4, SDT1-5 remaining (SDT1-3 failed)
    
    # Phase 2: System recovers and resumes execution
    orchestrator2 = Orchestrator(
        jira_project_key="SDT1",
        db=db_session,
        verbose=False,
    )
    
    with patch.object(orchestrator2, 'execute_ticket', return_value=True):
        orchestrator2.resume_sprint(state_id)
    
    # Verify state after recovery
    recovered_state = state_manager.get_state(state_id)
    
    assert recovered_state.status == OrchestratorStatus.COMPLETED
    assert len(recovered_state.completed_tickets) == 4  # 2 original + 2 resumed
    assert len(recovered_state.failed_tickets) == 1  # 1 from crash
    assert len(recovered_state.ticket_queue) == 0


def test_crash_preserves_history(db_session: Session, mock_tickets):
    """Test that crash preserves completed and failed ticket history."""
    
    # Create initial state with some completed and failed tickets
    state_manager = StateManager(db=db_session)
    state = state_manager.create_state(
        sprint_id=42,
        sprint_name="Sprint 10",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-3", "SDT1-4", "SDT1-5"],
    )
    
    # Simulate some prior work
    state_manager.start_execution(state.id)
    state_manager.mark_ticket_completed(state.id, "SDT1-1")
    state_manager.mark_ticket_completed(state.id, "SDT1-2")
    state_manager.mark_ticket_failed(state.id, "SDT1-0", "Failed before crash")
    
    # Simulate crash
    state_manager.fail_execution(state.id, "System crash")
    
    # Verify state preservation
    crashed_state = state_manager.get_state(state.id)
    assert len(crashed_state.completed_tickets) == 2
    assert len(crashed_state.failed_tickets) == 1
    assert len(crashed_state.ticket_queue) == 3
    
    # Resume execution
    orchestrator = Orchestrator(
        jira_project_key="SDT1",
        db=db_session,
        verbose=False,
    )
    
    with patch.object(orchestrator, 'execute_ticket', return_value=True):
        orchestrator.resume_sprint(state.id)
    
    # Verify history is preserved after resume
    final_state = state_manager.get_state(state.id)
    assert len(final_state.completed_tickets) == 5  # 2 original + 3 resumed
    assert len(final_state.failed_tickets) == 1  # Original failure preserved
    assert final_state.completed_tickets[0] == "SDT1-1"  # Original order preserved
    assert final_state.completed_tickets[1] == "SDT1-2"


# ── Pause and Resume Tests ───────────────────────────────────────────────────────────


def test_manual_pause_and_resume(db_session: Session, mock_tickets):
    """Test manual pause during execution and subsequent resume."""
    
    # Track execution to pause after 2 tickets
    execution_count = {"count": 0}
    
    def mock_execute_with_pause(ticket_key):
        execution_count["count"] += 1
        if execution_count["count"] == 2:
            # Simulate manual pause by raising special exception
            raise KeyboardInterrupt("User requested pause")
        return True
    
    orchestrator1 = Orchestrator(
        jira_project_key="SDT1",
        db=db_session,
        verbose=False,
    )
    
    with patch.object(orchestrator1, 'get_sprint_tickets', return_value=mock_tickets):
        with patch.object(orchestrator1, 'execute_ticket', side_effect=mock_execute_with_pause):
            try:
                state_id = orchestrator1.start_sprint(
                    sprint_id=42,
                    sprint_name="Sprint 10",
                )
            except KeyboardInterrupt:
                pass
    
    # Manually set to paused state
    state_manager = StateManager(db=db_session)
    state_manager.pause_execution(state_id, "User requested pause")
    
    # Verify paused state
    paused_state = state_manager.get_state(state_id)
    assert paused_state.status == OrchestratorStatus.PAUSED
    assert len(paused_state.completed_tickets) == 2
    assert len(paused_state.ticket_queue) == 3
    
    # Resume execution
    orchestrator2 = Orchestrator(
        jira_project_key="SDT1",
        db=db_session,
        verbose=False,
    )
    
    with patch.object(orchestrator2, 'execute_ticket', return_value=True):
        orchestrator2.resume_sprint(state_id)
    
    # Verify completed state
    completed_state = state_manager.get_state(state_id)
    assert completed_state.status == OrchestratorStatus.COMPLETED
    assert len(completed_state.completed_tickets) == 5


def test_cannot_resume_completed_state(orchestrator: Orchestrator, mock_tickets):
    """Test that completed states cannot be resumed."""
    
    with patch.object(orchestrator, 'get_sprint_tickets', return_value=mock_tickets):
        with patch.object(orchestrator, 'execute_ticket', return_value=True):
            state_id = orchestrator.start_sprint(
                sprint_id=42,
                sprint_name="Sprint 10",
            )
    
    # Try to resume completed state
    with pytest.raises(ValueError, match="Cannot resume state with status completed"):
        orchestrator.resume_sprint(state_id)


def test_cannot_resume_cancelled_state(orchestrator: Orchestrator, db_session: Session):
    """Test that cancelled states cannot be resumed."""
    
    # Create and cancel a state
    state_manager = StateManager(db=db_session)
    state = state_manager.create_state(
        sprint_id=42,
        sprint_name="Sprint 10",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1", "SDT1-2"],
    )
    state_manager.start_execution(state.id)
    state_manager.cancel_execution(state.id, "Test cancellation")
    
    # Try to resume
    with pytest.raises(ValueError, match="Cannot resume state with status cancelled"):
        orchestrator.resume_sprint(state.id)


# ── Progress Monitoring Tests ────────────────────────────────────────────────────────


def test_progress_tracking_during_execution(orchestrator: Orchestrator, mock_tickets):
    """Test progress tracking as execution proceeds."""
    
    execution_count = {"count": 0}
    progress_snapshots = []
    
    def mock_execute_with_tracking(ticket_key):
        execution_count["count"] += 1
        # Capture progress after each ticket
        state_id = orchestrator.state_manager.get_latest_state_for_sprint(42).id
        progress = orchestrator.get_progress(state_id)
        progress_snapshots.append(progress)
        return True
    
    with patch.object(orchestrator, 'get_sprint_tickets', return_value=mock_tickets):
        with patch.object(orchestrator, 'execute_ticket', side_effect=mock_execute_with_tracking):
            state_id = orchestrator.start_sprint(
                sprint_id=42,
                sprint_name="Sprint 10",
            )
    
    # Verify progress increased over time
    assert len(progress_snapshots) == 5
    
    # Check first snapshot (after first ticket)
    assert progress_snapshots[0]["completed_tickets"] == 1
    assert progress_snapshots[0]["progress_percentage"] == 20.0
    
    # Check last snapshot (after last ticket)
    assert progress_snapshots[-1]["completed_tickets"] == 5
    assert progress_snapshots[-1]["progress_percentage"] == 100.0


# ── Resumable States Tests ───────────────────────────────────────────────────────────


def test_list_resumable_states(db_session: Session):
    """Test listing all resumable states."""
    
    state_manager = StateManager(db=db_session)
    
    # Create states with different statuses
    state1 = state_manager.create_state(41, "Sprint 9", "SDT1", ["SDT1-1"])
    state2 = state_manager.create_state(42, "Sprint 10", "SDT1", ["SDT1-2"])
    state3 = state_manager.create_state(43, "Sprint 11", "SDT1", ["SDT1-3"])
    state4 = state_manager.create_state(44, "Sprint 12", "SDT1", ["SDT1-4"])
    
    # Set different statuses
    state_manager.start_execution(state1.id)
    state_manager.pause_execution(state1.id)  # PAUSED - resumable
    
    state_manager.start_execution(state2.id)
    state_manager.fail_execution(state2.id, "Error")  # FAILED - resumable
    
    state_manager.start_execution(state3.id)
    state_manager.complete_execution(state3.id)  # COMPLETED - not resumable
    
    # state4 remains PENDING - not resumable
    
    # Get resumable states
    orchestrator = Orchestrator(
        jira_project_key="SDT1",
        db=db_session,
        verbose=False,
    )
    
    resumable = orchestrator.list_resumable()
    
    assert len(resumable) == 2
    resumable_ids = {r["state_id"] for r in resumable}
    assert str(state1.id) in resumable_ids
    assert str(state2.id) in resumable_ids


# ── Error Handling Tests ─────────────────────────────────────────────────────────────


def test_invalid_state_id_resume(orchestrator: Orchestrator):
    """Test resuming with invalid state ID."""
    
    fake_uuid = UUID("00000000-0000-0000-0000-000000000000")
    
    with pytest.raises(ValueError, match="State .* not found"):
        orchestrator.resume_sprint(fake_uuid)


def test_ticket_execution_error_handling(orchestrator: Orchestrator, mock_tickets):
    """Test proper handling of ticket execution errors."""
    
    def mock_execute_with_errors(ticket_key):
        if ticket_key == "SDT1-3":
            raise Exception("Unexpected error in ticket execution")
        return True
    
    with patch.object(orchestrator, 'get_sprint_tickets', return_value=mock_tickets):
        with patch.object(orchestrator, 'execute_ticket', side_effect=mock_execute_with_errors):
            state_id = orchestrator.start_sprint(
                sprint_id=42,
                sprint_name="Sprint 10",
            )
    
    # Verify error was captured
    state = orchestrator.state_manager.get_state(state_id)
    
    assert len(state.failed_tickets) == 1
    assert state.failed_tickets[0]["ticket_key"] == "SDT1-3"
    assert "Unexpected error" in state.failed_tickets[0]["error_message"]
    
    # Other tickets should still complete
    assert len(state.completed_tickets) == 4


# ── Checkpoint Consistency Tests ─────────────────────────────────────────────────────


def test_checkpoint_after_each_ticket(orchestrator: Orchestrator, mock_tickets):
    """Test that checkpoints are created after each ticket."""
    
    checkpoint_times = []
    
    def mock_execute_with_checkpoint_tracking(ticket_key):
        # Get current state and track checkpoint time
        state = orchestrator.state_manager.get_latest_state_for_sprint(42)
        if state.last_checkpoint_at:
            checkpoint_times.append(state.last_checkpoint_at)
        return True
    
    with patch.object(orchestrator, 'get_sprint_tickets', return_value=mock_tickets):
        with patch.object(orchestrator, 'execute_ticket', 
                         side_effect=mock_execute_with_checkpoint_tracking):
            state_id = orchestrator.start_sprint(
                sprint_id=42,
                sprint_name="Sprint 10",
            )
    
    # Verify checkpoints were created
    assert len(checkpoint_times) >= 4  # At least one per completed ticket


def test_state_consistency_across_checkpoints(db_session: Session):
    """Test that state remains consistent across multiple checkpoints."""
    
    state_manager = StateManager(db=db_session)
    state = state_manager.create_state(
        sprint_id=42,
        sprint_name="Sprint 10",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1", "SDT1-2", "SDT1-3"],
    )
    
    state_manager.start_execution(state.id)
    
    # Execute tickets one by one with checkpoints
    for ticket in ["SDT1-1", "SDT1-2", "SDT1-3"]:
        state_manager.checkpoint(state.id, current_ticket=ticket)
        state_manager.mark_ticket_completed(state.id, ticket)
        
        # Verify state consistency
        current_state = state_manager.get_state(state.id)
        completed = len(current_state.completed_tickets)
        remaining = len(current_state.ticket_queue)
        
        # Total should always equal initial count
        assert completed + remaining == 3
    
    # Verify final state
    final_state = state_manager.get_state(state.id)
    assert len(final_state.completed_tickets) == 3
    assert len(final_state.ticket_queue) == 0
