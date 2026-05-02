"""
Integration tests for orchestrator crash recovery and state persistence.

These tests verify end-to-end behavior of the orchestrator including:
- State persistence across restarts
- Resume from crash scenarios
- Multi-step recovery processes
"""

import pytest
from unittest.mock import Mock, patch
from uuid import UUID

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, OrchestratorStatus

# Add agents directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from agents.orchestrator import Orchestrator
from agents.orchestrator_state import StateManager


@pytest.fixture
def db_session():
    """Create a test database session that persists across test steps."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine)
    session = TestSessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def orchestrator(db_session):
    """Create an orchestrator instance."""
    return Orchestrator("SDT1", db=db_session, verbose=False)


class TestCrashRecovery:
    """Test suite for crash recovery scenarios."""
    
    def test_crash_during_execution_full_recovery(self, db_session):
        """Test full recovery cycle: start -> crash -> resume -> complete."""
        
        # Step 1: Start execution
        orch1 = Orchestrator("SDT1", db=db_session, verbose=False)
        
        execution_count = {"count": 0}
        
        def mock_execute_crash_at_3(ticket_key):
            execution_count["count"] += 1
            if execution_count["count"] == 3:
                raise Exception("Simulated crash")
            return True
        
        mock_tickets = [
            {"key": "SDT1-1", "summary": "T1", "execution_order": 1},
            {"key": "SDT1-2", "summary": "T2", "execution_order": 2},
            {"key": "SDT1-3", "summary": "T3", "execution_order": 3},
            {"key": "SDT1-4", "summary": "T4", "execution_order": 4},
            {"key": "SDT1-5", "summary": "T5", "execution_order": 5},
        ]
        
        with patch.object(orch1, 'get_sprint_tickets', return_value=mock_tickets):
            with patch.object(orch1, 'execute_ticket', side_effect=mock_execute_crash_at_3):
                try:
                    state_id = orch1.start_sprint(100, "Test Sprint")
                except Exception:
                    pass  # Expected crash
        
        # Step 2: Verify state after crash
        state_manager = StateManager(db=db_session)
        states = state_manager.get_resumable_states()
        
        # Should have one failed state
        assert len(states) > 0
        state = states[0]
        state_id = state.id
        
        # Should have 2 completed tickets (1 and 2)
        assert len(state.completed_tickets or []) == 2
        
        # Should have 1 failed ticket (3)
        assert len(state.failed_tickets or []) == 1
        assert state.failed_tickets[0]["ticket_key"] == "SDT1-3"
        
        # Should have 2 remaining tickets (4 and 5)
        assert len(state.ticket_queue or []) == 2
        
        # Step 3: Resume execution with new orchestrator instance
        orch2 = Orchestrator("SDT1", db=db_session, verbose=False)
        
        def mock_execute_success(ticket_key):
            return True
        
        with patch.object(orch2, 'execute_ticket', side_effect=mock_execute_success):
            orch2.resume_sprint(state_id)
        
        # Step 4: Verify final state
        final_state = state_manager.get_state(state_id)
        
        assert final_state.status == OrchestratorStatus.COMPLETED
        # Should have completed 2 original + 2 remaining = 4 total
        assert len(final_state.completed_tickets) == 4
        # Failed ticket should still be recorded
        assert len(final_state.failed_tickets) == 1
        # Queue should be empty
        assert len(final_state.ticket_queue) == 0
    
    def test_multiple_crash_recovery_cycles(self, db_session):
        """Test recovering from multiple consecutive crashes."""
        
        state_manager = StateManager(db=db_session)
        
        # Create initial state
        state = state_manager.create_state(
            sprint_id=200,
            sprint_name="Multi-Crash Sprint",
            jira_project_key="SDT1",
            ticket_queue=["SDT1-1", "SDT1-2", "SDT1-3", "SDT1-4", "SDT1-5"],
        )
        
        state_id = state.id
        
        # Cycle 1: Complete first ticket, then crash
        orch1 = Orchestrator("SDT1", db=db_session, verbose=False)
        
        def mock_execute_first_only(ticket_key):
            if ticket_key == "SDT1-1":
                return True
            raise Exception("Crash after first ticket")
        
        with patch.object(orch1, 'execute_ticket', side_effect=mock_execute_first_only):
            with pytest.raises(Exception):
                orch1.resume_sprint(state_id)
        
        # Verify progress
        state = state_manager.get_state(state_id)
        assert len(state.completed_tickets) == 1
        assert len(state.failed_tickets) == 1
        assert len(state.ticket_queue) == 3
        
        # Mark as failed so we can resume
        state_manager.fail_execution(state_id, "Crash 1")
        
        # Cycle 2: Complete two more tickets, then crash
        orch2 = Orchestrator("SDT1", db=db_session, verbose=False)
        
        completed_in_cycle2 = {"count": 0}
        
        def mock_execute_two_more(ticket_key):
            if ticket_key in ["SDT1-3", "SDT1-4"]:
                completed_in_cycle2["count"] += 1
                if completed_in_cycle2["count"] <= 2:
                    return True
            raise Exception("Crash after two more tickets")
        
        with patch.object(orch2, 'execute_ticket', side_effect=mock_execute_two_more):
            with pytest.raises(Exception):
                orch2.resume_sprint(state_id)
        
        # Verify progress
        state = state_manager.get_state(state_id)
        assert len(state.completed_tickets) == 3  # 1 + 2 more
        
        # Mark as failed so we can resume
        state_manager.fail_execution(state_id, "Crash 2")
        
        # Cycle 3: Complete remaining tickets
        orch3 = Orchestrator("SDT1", db=db_session, verbose=False)
        
        def mock_execute_success(ticket_key):
            return True
        
        with patch.object(orch3, 'execute_ticket', side_effect=mock_execute_success):
            orch3.resume_sprint(state_id)
        
        # Verify final state
        final_state = state_manager.get_state(state_id)
        assert final_state.status == OrchestratorStatus.COMPLETED
        assert len(final_state.ticket_queue) == 0
    
    def test_resume_preserves_execution_order(self, db_session):
        """Test that resume maintains correct ticket execution order."""
        
        state_manager = StateManager(db=db_session)
        
        # Create state with specific order
        state = state_manager.create_state(
            sprint_id=300,
            sprint_name="Order Test Sprint",
            jira_project_key="SDT1",
            ticket_queue=["SDT1-10", "SDT1-20", "SDT1-30", "SDT1-40", "SDT1-50"],
        )
        
        state_id = state.id
        
        # Execute first two tickets
        state_manager.start_execution(state_id)
        state_manager.mark_ticket_completed(state_id, "SDT1-10")
        state_manager.mark_ticket_completed(state_id, "SDT1-20")
        state_manager.pause_execution(state_id)
        
        # Resume and track execution order
        orch = Orchestrator("SDT1", db=db_session, verbose=False)
        
        executed_order = []
        
        def mock_execute_track_order(ticket_key):
            executed_order.append(ticket_key)
            return True
        
        with patch.object(orch, 'execute_ticket', side_effect=mock_execute_track_order):
            orch.resume_sprint(state_id)
        
        # Verify order
        assert executed_order == ["SDT1-30", "SDT1-40", "SDT1-50"]
    
    def test_checkpoint_frequency(self, db_session):
        """Test that checkpoints are saved at correct intervals."""
        
        orch = Orchestrator("SDT1", db=db_session, verbose=False)
        
        mock_tickets = [
            {"key": "SDT1-1", "summary": "T1", "execution_order": 1},
            {"key": "SDT1-2", "summary": "T2", "execution_order": 2},
            {"key": "SDT1-3", "summary": "T3", "execution_order": 3},
        ]
        
        checkpoint_times = []
        original_checkpoint = orch.state_manager.checkpoint
        
        def track_checkpoint(*args, **kwargs):
            checkpoint_times.append(True)
            return original_checkpoint(*args, **kwargs)
        
        with patch.object(orch, 'get_sprint_tickets', return_value=mock_tickets):
            with patch.object(orch, 'execute_ticket', return_value=True):
                with patch.object(
                    orch.state_manager,
                    'checkpoint',
                    side_effect=track_checkpoint
                ):
                    state_id = orch.start_sprint(400, "Checkpoint Test")
        
        # Should have checkpoints for each ticket
        assert len(checkpoint_times) >= 3
    
    def test_concurrent_sprint_executions(self, db_session):
        """Test handling multiple concurrent sprint executions."""
        
        state_manager = StateManager(db=db_session)
        
        # Create multiple sprint states
        state1 = state_manager.create_state(
            sprint_id=501,
            sprint_name="Sprint A",
            jira_project_key="SDT1",
            ticket_queue=["SDT1-1", "SDT1-2"],
        )
        
        state2 = state_manager.create_state(
            sprint_id=502,
            sprint_name="Sprint B",
            jira_project_key="SDT1",
            ticket_queue=["SDT1-10", "SDT1-11"],
        )
        
        state3 = state_manager.create_state(
            sprint_id=503,
            sprint_name="Sprint C",
            jira_project_key="SDT1",
            ticket_queue=["SDT1-20", "SDT1-21"],
        )
        
        # Execute them partially
        state_manager.start_execution(state1.id)
        state_manager.mark_ticket_completed(state1.id, "SDT1-1")
        state_manager.pause_execution(state1.id)
        
        state_manager.start_execution(state2.id)
        state_manager.mark_ticket_completed(state2.id, "SDT1-10")
        state_manager.fail_execution(state2.id, "Error")
        
        state_manager.start_execution(state3.id)
        state_manager.mark_ticket_completed(state3.id, "SDT1-20")
        state_manager.mark_ticket_completed(state3.id, "SDT1-21")
        state_manager.complete_execution(state3.id)
        
        # List resumable
        resumable = state_manager.get_resumable_states()
        
        # Should have 2 resumable (paused and failed)
        assert len(resumable) == 2
        resumable_ids = [str(s.id) for s in resumable]
        assert str(state1.id) in resumable_ids
        assert str(state2.id) in resumable_ids
        assert str(state3.id) not in resumable_ids
    
    def test_error_message_preservation(self, db_session):
        """Test that error messages are preserved through crashes."""
        
        orch = Orchestrator("SDT1", db=db_session, verbose=False)
        
        error_message = "Database connection timeout after 30 seconds"
        
        mock_tickets = [
            {"key": "SDT1-1", "summary": "T1", "execution_order": 1},
            {"key": "SDT1-2", "summary": "T2", "execution_order": 2},
        ]
        
        def mock_execute_with_error(ticket_key):
            if ticket_key == "SDT1-1":
                return True
            raise Exception(error_message)
        
        with patch.object(orch, 'get_sprint_tickets', return_value=mock_tickets):
            with patch.object(orch, 'execute_ticket', side_effect=mock_execute_with_error):
                try:
                    state_id = orch.start_sprint(600, "Error Test")
                except:
                    pass
        
        # Get state
        state_manager = StateManager(db=db_session)
        states = state_manager.get_resumable_states()
        
        if states:
            state = states[0]
            # Verify error is recorded
            assert len(state.failed_tickets) > 0
            assert error_message in state.failed_tickets[0]["error_message"]
