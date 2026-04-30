"""
Integration tests for the orchestrator with state persistence.

These tests verify the complete flow from start to resume.
"""

import pytest
import time

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, OrchestratorStatus

# Add agents directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from agents.orchestrator import Orchestrator


class SimulatedOrchestrator(Orchestrator):
    """Orchestrator with simulated Jira calls for testing."""
    
    def __init__(self, *args, tickets=None, execution_behavior=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._tickets = tickets or []
        self._execution_behavior = execution_behavior or {}
    
    def get_sprint_tickets(self, sprint_id):
        """Return simulated tickets."""
        return self._tickets
    
    def execute_ticket(self, ticket_key):
        """Simulate ticket execution with configurable behavior."""
        behavior = self._execution_behavior.get(ticket_key, "success")
        
        time.sleep(0.01)  # Minimal delay for realism
        
        if behavior == "success":
            return True
        elif behavior == "failure":
            raise Exception(f"Simulated failure for {ticket_key}")
        elif behavior == "pause":
            raise KeyboardInterrupt(f"Simulated pause at {ticket_key}")
        else:
            return True


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine)
    session = TestSessionLocal()
    
    yield session
    
    session.close()


def test_complete_sprint_execution(db_session):
    """Test complete sprint execution from start to finish."""
    tickets = [
        {"key": "TEST-1", "summary": "Task 1", "execution_order": 1},
        {"key": "TEST-2", "summary": "Task 2", "execution_order": 2},
        {"key": "TEST-3", "summary": "Task 3", "execution_order": 3},
    ]
    
    orch = SimulatedOrchestrator(
        jira_project_key="TEST",
        db=db_session,
        verbose=False,
        tickets=tickets,
    )
    
    state_id = orch.start_sprint(123, "Test Sprint")
    
    # Verify completion
    state = orch.state_manager.get_state(state_id)
    assert state.status == OrchestratorStatus.COMPLETED
    assert len(state.completed_tickets) == 3
    assert len(state.failed_tickets) == 0
    assert len(state.ticket_queue) == 0


def test_sprint_with_failures(db_session):
    """Test sprint execution with ticket failures."""
    tickets = [
        {"key": "TEST-1", "summary": "Task 1", "execution_order": 1},
        {"key": "TEST-2", "summary": "Task 2 (fail)", "execution_order": 2},
        {"key": "TEST-3", "summary": "Task 3", "execution_order": 3},
    ]
    
    execution_behavior = {
        "TEST-1": "success",
        "TEST-2": "failure",
        "TEST-3": "success",
    }
    
    orch = SimulatedOrchestrator(
        jira_project_key="TEST",
        db=db_session,
        verbose=False,
        tickets=tickets,
        execution_behavior=execution_behavior,
    )
    
    state_id = orch.start_sprint(123, "Test Sprint")
    
    # Verify partial completion
    state = orch.state_manager.get_state(state_id)
    assert state.status == OrchestratorStatus.COMPLETED
    assert len(state.completed_tickets) == 2
    assert len(state.failed_tickets) == 1
    assert state.failed_tickets[0]["ticket_key"] == "TEST-2"


def test_pause_and_resume(db_session):
    """Test pausing execution and resuming later."""
    tickets = [
        {"key": "TEST-1", "summary": "Task 1", "execution_order": 1},
        {"key": "TEST-2", "summary": "Task 2", "execution_order": 2},
        {"key": "TEST-3", "summary": "Task 3", "execution_order": 3},
        {"key": "TEST-4", "summary": "Task 4", "execution_order": 4},
    ]
    
    # First execution - complete 2 tickets then pause
    execution_behavior = {
        "TEST-1": "success",
        "TEST-2": "pause",  # Will pause here
    }
    
    orch1 = SimulatedOrchestrator(
        jira_project_key="TEST",
        db=db_session,
        verbose=False,
        tickets=tickets,
        execution_behavior=execution_behavior,
    )
    
    try:
        state_id = orch1.start_sprint(123, "Test Sprint")
    except KeyboardInterrupt:
        # Expected - get the state
        state = orch1.state_manager.get_latest_state_for_sprint(123)
        state_id = state.id
        orch1.state_manager.pause_execution(state_id, "Test pause")
    
    # Verify paused state
    state = orch1.state_manager.get_state(state_id)
    assert state.status == OrchestratorStatus.PAUSED
    assert len(state.completed_tickets) == 1  # Only TEST-1 completed
    assert "TEST-2" in state.ticket_queue
    assert "TEST-3" in state.ticket_queue
    assert "TEST-4" in state.ticket_queue
    
    # Resume execution - all tickets succeed now
    orch2 = SimulatedOrchestrator(
        jira_project_key="TEST",
        db=db_session,
        verbose=False,
        tickets=tickets,
        execution_behavior={},  # All succeed
    )
    
    orch2.resume_sprint(state_id)
    
    # Verify completion
    state = orch2.state_manager.get_state(state_id)
    assert state.status == OrchestratorStatus.COMPLETED
    assert len(state.completed_tickets) == 4
    assert len(state.failed_tickets) == 0
    assert len(state.ticket_queue) == 0


def test_resume_after_failure(db_session):
    """Test resuming after a failed execution."""
    tickets = [
        {"key": "TEST-1", "summary": "Task 1", "execution_order": 1},
        {"key": "TEST-2", "summary": "Task 2", "execution_order": 2},
    ]
    
    # First execution - first ticket fails with system error
    first_call = {"is_first": True}
    
    def failing_execution(ticket_key):
        if first_call["is_first"] and ticket_key == "TEST-1":
            first_call["is_first"] = False
            raise Exception("Database connection failed")
        return True
    
    orch1 = SimulatedOrchestrator(
        jira_project_key="TEST",
        db=db_session,
        verbose=False,
        tickets=tickets,
    )
    orch1.execute_ticket = failing_execution
    
    state_id = orch1.start_sprint(123, "Test Sprint")
    
    # Should have failed first ticket
    state = orch1.state_manager.get_state(state_id)
    assert len(state.failed_tickets) == 1
    assert state.failed_tickets[0]["ticket_key"] == "TEST-1"
    
    # Resume - now succeeds
    orch2 = SimulatedOrchestrator(
        jira_project_key="TEST",
        db=db_session,
        verbose=False,
        tickets=tickets,
        execution_behavior={},  # All succeed
    )
    
    # Mark as failed so it's resumable
    orch2.state_manager.pause_execution(state_id, "Ready to retry")
    
    orch2.resume_sprint(state_id)
    
    # Verify completion
    state = orch2.state_manager.get_state(state_id)
    assert state.status == OrchestratorStatus.COMPLETED
    assert len(state.completed_tickets) == 1  # TEST-2 (TEST-1 already marked as failed)


def test_progress_tracking(db_session):
    """Test progress tracking throughout execution."""
    tickets = [
        {"key": f"TEST-{i}", "summary": f"Task {i}", "execution_order": i}
        for i in range(1, 11)
    ]
    
    orch = SimulatedOrchestrator(
        jira_project_key="TEST",
        db=db_session,
        verbose=False,
        tickets=tickets,
    )
    
    state_id = orch.start_sprint(123, "Test Sprint")
    
    # Check progress
    progress = orch.get_progress(state_id)
    
    assert progress["total_tickets"] == 10
    assert progress["completed_tickets"] == 10
    assert progress["failed_tickets"] == 0
    assert progress["remaining_tickets"] == 0
    assert progress["progress_percentage"] == 100.0
    assert progress["status"] == "completed"


def test_multiple_sprints_concurrent(db_session):
    """Test managing multiple sprint states concurrently."""
    tickets1 = [
        {"key": "TEST-1", "summary": "Sprint 1 Task", "execution_order": 1},
    ]
    
    tickets2 = [
        {"key": "TEST-2", "summary": "Sprint 2 Task", "execution_order": 1},
    ]
    
    # Start sprint 1
    orch1 = SimulatedOrchestrator(
        jira_project_key="TEST",
        db=db_session,
        verbose=False,
        tickets=tickets1,
    )
    state_id_1 = orch1.start_sprint(100, "Sprint 1")
    
    # Start sprint 2
    orch2 = SimulatedOrchestrator(
        jira_project_key="TEST",
        db=db_session,
        verbose=False,
        tickets=tickets2,
    )
    state_id_2 = orch2.start_sprint(200, "Sprint 2")
    
    # Verify both exist independently
    state1 = orch1.state_manager.get_state(state_id_1)
    state2 = orch2.state_manager.get_state(state_id_2)
    
    assert state1.sprint_id == 100
    assert state2.sprint_id == 200
    assert state1.id != state2.id
    assert state1.status == OrchestratorStatus.COMPLETED
    assert state2.status == OrchestratorStatus.COMPLETED


def test_checkpoint_persistence(db_session):
    """Test that checkpoints persist across instances."""
    tickets = [
        {"key": "TEST-1", "summary": "Task 1", "execution_order": 1},
        {"key": "TEST-2", "summary": "Task 2", "execution_order": 2},
    ]
    
    # Create state and checkpoint
    orch1 = SimulatedOrchestrator(
        jira_project_key="TEST",
        db=db_session,
        verbose=False,
        tickets=tickets,
        execution_behavior={"TEST-1": "success", "TEST-2": "pause"},
    )
    
    try:
        state_id = orch1.start_sprint(123, "Test Sprint")
    except KeyboardInterrupt:
        state = orch1.state_manager.get_latest_state_for_sprint(123)
        state_id = state.id
        orch1.state_manager.pause_execution(state_id)
    
    # Create new instance and verify state persisted
    orch2 = SimulatedOrchestrator(
        jira_project_key="TEST",
        db=db_session,
        verbose=False,
        tickets=tickets,
    )
    
    state = orch2.state_manager.get_state(state_id)
    assert state is not None
    assert state.status == OrchestratorStatus.PAUSED
    assert len(state.completed_tickets) == 1
    assert state.last_checkpoint_at is not None
