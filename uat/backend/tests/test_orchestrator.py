"""
tests/test_orchestrator.py
──────────────────────────
Integration tests for the Orchestrator with state persistence.

Tests cover:
- Starting sprint executions
- Resuming after failures
- Pausing and resuming executions
- Cancelling executions
- Progress tracking during execution
- Error handling and recovery
"""

import os
import sys
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from models import Base, OrchestratorStatus
from agents.orchestrator import Orchestrator, TicketExecutionError


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
def orchestrator(db_session):
    """Create an Orchestrator instance for testing."""
    return Orchestrator(
        jira_project_key="TEST",
        db=db_session,
        verbose=False,
    )


# ── Mock Orchestrator for Testing ─────────────────────────────────────────────

class MockOrchestrator(Orchestrator):
    """Mock orchestrator that simulates ticket execution without calling Jira."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticket_results = {}  # ticket_key -> success (bool or Exception)
        self.execution_log = []  # List of executed ticket keys
    
    def set_ticket_result(self, ticket_key: str, result) -> None:
        """Set the result for a specific ticket.
        
        Args:
            ticket_key: Ticket key
            result: True for success, False for failure, or Exception to raise
        """
        self.ticket_results[ticket_key] = result
    
    def get_sprint_tickets(self, sprint_id: int):
        """Override to return mock tickets."""
        # Return predefined tickets for testing
        return [
            {"key": "TEST-1", "execution_order": 1},
            {"key": "TEST-2", "execution_order": 2},
            {"key": "TEST-3", "execution_order": 3},
        ]
    
    def execute_ticket(self, ticket_key: str) -> bool:
        """Override to simulate ticket execution."""
        self.execution_log.append(ticket_key)
        
        # Check if we have a predefined result
        if ticket_key in self.ticket_results:
            result = self.ticket_results[ticket_key]
            
            if isinstance(result, Exception):
                raise result
            
            return result
        
        # Default: success
        return True


@pytest.fixture
def mock_orchestrator(db_session):
    """Create a MockOrchestrator instance for testing."""
    return MockOrchestrator(
        jira_project_key="TEST",
        db=db_session,
        verbose=False,
    )


# ── Tests: Basic Execution ────────────────────────────────────────────────────

def test_start_sprint_success(mock_orchestrator):
    """Test starting and completing a sprint successfully."""
    state_id = mock_orchestrator.start_sprint(
        sprint_id=100,
        sprint_name="Test Sprint",
    )
    
    assert state_id is not None
    
    # Verify all tickets were executed
    assert mock_orchestrator.execution_log == ["TEST-1", "TEST-2", "TEST-3"]
    
    # Check state
    progress = mock_orchestrator.get_progress(state_id)
    assert progress["status"] == OrchestratorStatus.COMPLETED.value
    assert progress["completed_tickets"] == 3
    assert progress["failed_tickets"] == 0


def test_start_sprint_with_ticket_failure(mock_orchestrator):
    """Test sprint execution with a ticket failure."""
    # Make TEST-2 fail
    mock_orchestrator.set_ticket_result("TEST-2", False)
    
    state_id = mock_orchestrator.start_sprint(
        sprint_id=101,
        sprint_name="Test Sprint with Failure",
    )
    
    # All tickets should be attempted
    assert len(mock_orchestrator.execution_log) == 3
    
    # Check state
    progress = mock_orchestrator.get_progress(state_id)
    assert progress["completed_tickets"] == 2  # TEST-1 and TEST-3
    assert progress["failed_tickets"] == 1  # TEST-2
    
    # Check failed ticket details
    state = mock_orchestrator.state_manager.get_state(state_id)
    assert len(state.failed_tickets) == 1
    assert state.failed_tickets[0]["ticket_key"] == "TEST-2"


def test_start_sprint_with_exception(mock_orchestrator):
    """Test sprint execution with a ticket raising an exception."""
    # Make TEST-2 raise an exception
    mock_orchestrator.set_ticket_result("TEST-2", RuntimeError("Test error"))
    
    state_id = mock_orchestrator.start_sprint(
        sprint_id=102,
        sprint_name="Test Sprint with Exception",
    )
    
    # All tickets should be attempted
    assert len(mock_orchestrator.execution_log) == 3
    
    # Check state
    progress = mock_orchestrator.get_progress(state_id)
    assert progress["completed_tickets"] == 2  # TEST-1 and TEST-3
    assert progress["failed_tickets"] == 1  # TEST-2
    
    # Check error message
    state = mock_orchestrator.state_manager.get_state(state_id)
    assert "Test error" in state.failed_tickets[0]["error_message"]


# ── Tests: Resume Capability ──────────────────────────────────────────────────

def test_resume_from_paused(mock_orchestrator):
    """Test resuming a paused execution."""
    # Start sprint
    state_id = mock_orchestrator.start_sprint(
        sprint_id=103,
        sprint_name="Test Resume from Pause",
    )
    
    # Manually pause after first ticket
    state = mock_orchestrator.state_manager.get_state(state_id)
    state.ticket_queue = ["TEST-2", "TEST-3"]  # Simulate partial completion
    state.completed_tickets = ["TEST-1"]
    mock_orchestrator.state_manager.pause_execution(state_id, "Test pause")
    
    # Clear execution log
    mock_orchestrator.execution_log.clear()
    
    # Resume
    mock_orchestrator.resume_sprint(state_id)
    
    # Should only execute remaining tickets
    assert mock_orchestrator.execution_log == ["TEST-2", "TEST-3"]
    
    # Check final state
    progress = mock_orchestrator.get_progress(state_id)
    assert progress["status"] == OrchestratorStatus.COMPLETED.value
    assert progress["completed_tickets"] == 3


def test_resume_from_failed(mock_orchestrator):
    """Test resuming a failed execution."""
    # Make TEST-2 fail initially
    mock_orchestrator.set_ticket_result("TEST-2", RuntimeError("Initial failure"))
    
    state_id = mock_orchestrator.start_sprint(
        sprint_id=104,
        sprint_name="Test Resume from Failed",
    )
    
    # Verify TEST-2 failed
    state = mock_orchestrator.state_manager.get_state(state_id)
    assert len(state.failed_tickets) == 1
    
    # Manually set state to failed and restore TEST-2 to queue
    state.ticket_queue = ["TEST-2"]  # Put failed ticket back
    state.completed_tickets = ["TEST-1", "TEST-3"]
    state.failed_tickets = []  # Clear failures
    mock_orchestrator.state_manager.fail_execution(state_id, "Simulated failure")
    
    # Fix TEST-2 for retry
    mock_orchestrator.set_ticket_result("TEST-2", True)
    mock_orchestrator.execution_log.clear()
    
    # Resume
    mock_orchestrator.resume_sprint(state_id)
    
    # Should retry TEST-2
    assert "TEST-2" in mock_orchestrator.execution_log
    
    # Check final state
    progress = mock_orchestrator.get_progress(state_id)
    assert progress["status"] == OrchestratorStatus.COMPLETED.value
    assert progress["completed_tickets"] == 3


def test_resume_invalid_state(mock_orchestrator):
    """Test that resuming an invalid state raises an error."""
    fake_id = uuid4()
    
    with pytest.raises(ValueError, match="not found"):
        mock_orchestrator.resume_sprint(fake_id)


def test_resume_completed_state(mock_orchestrator):
    """Test that resuming a completed state raises an error."""
    state_id = mock_orchestrator.start_sprint(
        sprint_id=105,
        sprint_name="Completed Sprint",
    )
    
    # State should be completed
    state = mock_orchestrator.state_manager.get_state(state_id)
    assert state.status == OrchestratorStatus.COMPLETED
    
    # Try to resume
    with pytest.raises(ValueError, match="Cannot resume"):
        mock_orchestrator.resume_sprint(state_id)


# ── Tests: Pause and Cancel ───────────────────────────────────────────────────

def test_pause_execution(mock_orchestrator):
    """Test pausing an execution."""
    state_id = mock_orchestrator.start_sprint(
        sprint_id=106,
        sprint_name="Test Pause",
    )
    
    # Pause the execution
    mock_orchestrator.pause(state_id, "Test pause")
    
    # Check state
    state = mock_orchestrator.state_manager.get_state(state_id)
    assert state.status == OrchestratorStatus.PAUSED
    assert state.error_message == "Test pause"


def test_cancel_execution(mock_orchestrator):
    """Test cancelling an execution."""
    state_id = mock_orchestrator.start_sprint(
        sprint_id=107,
        sprint_name="Test Cancel",
    )
    
    # Cancel the execution
    mock_orchestrator.cancel(state_id, "Test cancellation")
    
    # Check state
    state = mock_orchestrator.state_manager.get_state(state_id)
    assert state.status == OrchestratorStatus.CANCELLED
    assert state.error_message == "Test cancellation"
    assert state.completed_at is not None


# ── Tests: Progress Tracking ──────────────────────────────────────────────────

def test_get_progress(mock_orchestrator):
    """Test getting execution progress."""
    # Make TEST-2 fail
    mock_orchestrator.set_ticket_result("TEST-2", False)
    
    state_id = mock_orchestrator.start_sprint(
        sprint_id=108,
        sprint_name="Test Progress",
    )
    
    progress = mock_orchestrator.get_progress(state_id)
    
    assert progress["sprint_id"] == 108
    assert progress["sprint_name"] == "Test Progress"
    assert progress["total_tickets"] == 3
    assert progress["completed_tickets"] == 2
    assert progress["failed_tickets"] == 1
    assert progress["remaining_tickets"] == 0
    assert progress["progress_percentage"] == pytest.approx(66.67, abs=0.01)


def test_list_resumable(mock_orchestrator):
    """Test listing resumable states."""
    # Create multiple states with different statuses
    state1_id = mock_orchestrator.start_sprint(200, "Sprint 1")
    mock_orchestrator.pause(state1_id, "Paused")
    
    # Manually create a failed state
    state2 = mock_orchestrator.state_manager.create_state(
        sprint_id=201,
        sprint_name="Sprint 2",
        jira_project_key="TEST",
        ticket_queue=["TEST-1"],
    )
    mock_orchestrator.state_manager.fail_execution(state2.id, "Failed")
    
    # Completed state (should not be resumable)
    mock_orchestrator.start_sprint(202, "Sprint 3")
    
    # Get resumable states
    resumable = mock_orchestrator.list_resumable()
    
    assert len(resumable) == 2
    
    # Check that both paused and failed states are included
    statuses = {s["status"] for s in resumable}
    assert "paused" in statuses
    assert "failed" in statuses


# ── Tests: Error Handling ─────────────────────────────────────────────────────

def test_start_sprint_with_orchestrator_failure(mock_orchestrator):
    """Test handling of orchestrator-level failures."""
    # Make all tickets fail
    mock_orchestrator.set_ticket_result("TEST-1", RuntimeError("Catastrophic failure"))
    mock_orchestrator.set_ticket_result("TEST-2", RuntimeError("Catastrophic failure"))
    mock_orchestrator.set_ticket_result("TEST-3", RuntimeError("Catastrophic failure"))
    
    state_id = mock_orchestrator.start_sprint(
        sprint_id=109,
        sprint_name="Test Catastrophic Failure",
    )
    
    # Should still complete but with all tickets failed
    progress = mock_orchestrator.get_progress(state_id)
    assert progress["failed_tickets"] == 3
    assert progress["completed_tickets"] == 0


def test_empty_sprint(mock_orchestrator):
    """Test handling of sprint with no tickets."""
    # Override to return no tickets
    def get_no_tickets(sprint_id):
        return []
    
    mock_orchestrator.get_sprint_tickets = get_no_tickets
    
    state_id = mock_orchestrator.start_sprint(
        sprint_id=110,
        sprint_name="Empty Sprint",
    )
    
    # Should complete immediately
    progress = mock_orchestrator.get_progress(state_id)
    assert progress["status"] == OrchestratorStatus.COMPLETED.value
    assert progress["total_tickets"] == 0


# ── Tests: Context Manager ────────────────────────────────────────────────────

def test_orchestrator_context_manager():
    """Test Orchestrator as a context manager."""
    with Orchestrator(jira_project_key="TEST", verbose=False) as orch:
        # Should create its own session
        assert orch._db is not None
        assert orch.state_manager.db is not None
        
        # Test that it works
        state = orch.state_manager.create_state(
            sprint_id=300,
            sprint_name="Context Test",
            jira_project_key="TEST",
            ticket_queue=["TEST-1"],
        )
        
        assert state.id is not None
