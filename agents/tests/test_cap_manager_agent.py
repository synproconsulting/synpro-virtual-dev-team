"""
Tests for Cap Manager Agent retrigger loop protection.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from agents.cap_manager_agent import CapManagerAgent, RetriggerState


class TestRetriggerState:
    """Tests for RetriggerState dataclass."""
    
    def test_initial_state(self):
        """Test initial retrigger state creation."""
        state = RetriggerState(ticket_id="TEST-123")
        
        assert state.ticket_id == "TEST-123"
        assert state.attempt_count == 0
        assert state.first_trigger_time is None
        assert state.last_trigger_time is None
        assert state.trigger_reasons == []
    
    def test_increment(self):
        """Test incrementing retrigger count."""
        state = RetriggerState(ticket_id="TEST-123")
        
        state.increment("first reason")
        assert state.attempt_count == 1
        assert state.first_trigger_time is not None
        assert state.last_trigger_time is not None
        assert "first reason" in state.trigger_reasons
        
        first_time = state.first_trigger_time
        state.increment("second reason")
        assert state.attempt_count == 2
        assert state.first_trigger_time == first_time
        assert "second reason" in state.trigger_reasons


class TestCapManagerAgent:
    """Tests for Cap Manager Agent."""
    
    def test_initialization_defaults(self):
        """Test agent initialization with default values."""
        agent = CapManagerAgent()
        
        assert agent.max_retrigger_attempts == 3
        assert agent.retrigger_window_minutes == 60
        assert agent._retrigger_state == {}
    
    def test_initialization_custom_values(self):
        """Test agent initialization with custom values."""
        agent = CapManagerAgent(
            max_retrigger_attempts=5,
            retrigger_window_minutes=120
        )
        
        assert agent.max_retrigger_attempts == 5
        assert agent.retrigger_window_minutes == 120
    
    def test_initialization_from_env(self):
        """Test agent initialization from environment variables."""
        with patch.dict('os.environ', {
            'MAX_RETRIGGER_ATTEMPTS': '7',
            'RETRIGGER_WINDOW_MINUTES': '90'
        }):
            agent = CapManagerAgent()
            assert agent.max_retrigger_attempts == 7
            assert agent.retrigger_window_minutes == 90
    
    def test_can_retrigger_new_ticket(self):
        """Test that a new ticket can be retriggered."""
        agent = CapManagerAgent(max_retrigger_attempts=3)
        
        assert agent.can_retrigger("TEST-123", "initial check")
    
    def test_can_retrigger_within_limit(self):
        """Test retriggering within the limit."""
        agent = CapManagerAgent(max_retrigger_attempts=3)
        
        agent.record_retrigger("TEST-123", "first attempt")
        assert agent.can_retrigger("TEST-123", "second check")
        
        agent.record_retrigger("TEST-123", "second attempt")
        assert agent.can_retrigger("TEST-123", "third check")
    
    def test_cannot_retrigger_at_limit(self):
        """Test that retriggering is blocked at the limit."""
        agent = CapManagerAgent(max_retrigger_attempts=3)
        
        agent.record_retrigger("TEST-123", "attempt 1")
        agent.record_retrigger("TEST-123", "attempt 2")
        agent.record_retrigger("TEST-123", "attempt 3")
        
        assert not agent.can_retrigger("TEST-123", "should fail")
    
    def test_record_retrigger(self):
        """Test recording retrigger attempts."""
        agent = CapManagerAgent()
        
        agent.record_retrigger("TEST-123", "test reason")
        
        state = agent.get_retrigger_state("TEST-123")
        assert state is not None
        assert state["attempt_count"] == 1
        assert "test reason" in state["trigger_reasons"]
    
    def test_get_retrigger_state_nonexistent(self):
        """Test getting state for a ticket that hasn't been tracked."""
        agent = CapManagerAgent()
        
        state = agent.get_retrigger_state("NONEXISTENT")
        assert state is None
    
    def test_get_retrigger_state_existing(self):
        """Test getting state for a tracked ticket."""
        agent = CapManagerAgent(max_retrigger_attempts=5)
        
        agent.record_retrigger("TEST-123", "reason 1")
        agent.record_retrigger("TEST-123", "reason 2")
        
        state = agent.get_retrigger_state("TEST-123")
        assert state is not None
        assert state["ticket_id"] == "TEST-123"
        assert state["attempt_count"] == 2
        assert state["max_attempts"] == 5
        assert len(state["trigger_reasons"]) == 2
        assert state["first_trigger_time"] is not None
        assert state["last_trigger_time"] is not None
    
    def test_reset_retrigger_state(self):
        """Test resetting retrigger state."""
        agent = CapManagerAgent()
        
        agent.record_retrigger("TEST-123", "test")
        assert agent.get_retrigger_state("TEST-123") is not None
        
        agent.reset_retrigger_state("TEST-123")
        assert agent.get_retrigger_state("TEST-123") is None
    
    def test_reset_nonexistent_state(self):
        """Test resetting state for a nonexistent ticket (should not error)."""
        agent = CapManagerAgent()
        
        # Should not raise an exception
        agent.reset_retrigger_state("NONEXISTENT")
    
    def test_get_all_retrigger_states(self):
        """Test getting all retrigger states."""
        agent = CapManagerAgent()
        
        agent.record_retrigger("TEST-123", "reason 1")
        agent.record_retrigger("TEST-456", "reason 2")
        agent.record_retrigger("TEST-789", "reason 3")
        
        all_states = agent.get_all_retrigger_states()
        assert len(all_states) == 3
        assert "TEST-123" in all_states
        assert "TEST-456" in all_states
        assert "TEST-789" in all_states
    
    def test_time_window_reset(self):
        """Test that retrigger count resets after time window expires."""
        agent = CapManagerAgent(
            max_retrigger_attempts=3,
            retrigger_window_minutes=60
        )
        
        # Mock datetime to simulate expired window
        past_time = datetime.utcnow() - timedelta(minutes=65)
        
        with patch('agents.cap_manager_agent.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = past_time
            agent.record_retrigger("TEST-123", "old attempt 1")
            agent.record_retrigger("TEST-123", "old attempt 2")
            agent.record_retrigger("TEST-123", "old attempt 3")
            
            # Now move to current time
            mock_datetime.utcnow.return_value = datetime.utcnow()
            
            # Should be able to retrigger again after window expired
            assert agent.can_retrigger("TEST-123", "new attempt")
    
    def test_manage_capacity_retrigger_success(self):
        """Test manage_capacity with retrigger action - success case."""
        agent = CapManagerAgent()
        
        result = agent.manage_capacity(
            ticket_id="TEST-123",
            action="retrigger",
            context={"reason": "dependency resolved"}
        )
        
        assert result["success"] is True
        assert result["ticket_id"] == "TEST-123"
        assert result["action"] == "retrigger"
        assert result["state"]["attempt_count"] == 1
    
    def test_manage_capacity_retrigger_limit_reached(self):
        """Test manage_capacity with retrigger action - limit reached."""
        agent = CapManagerAgent(max_retrigger_attempts=2)
        
        agent.record_retrigger("TEST-123", "attempt 1")
        agent.record_retrigger("TEST-123", "attempt 2")
        
        result = agent.manage_capacity(
            ticket_id="TEST-123",
            action="retrigger",
            context={"reason": "should fail"}
        )
        
        assert result["success"] is False
        assert result["error"] == "Retrigger limit reached"
        assert result["state"]["attempt_count"] == 2
    
    def test_manage_capacity_check(self):
        """Test manage_capacity with check action."""
        agent = CapManagerAgent()
        
        agent.record_retrigger("TEST-123", "test")
        
        result = agent.manage_capacity(
            ticket_id="TEST-123",
            action="check"
        )
        
        assert result["success"] is True
        assert result["action"] == "check"
        assert result["can_retrigger"] is True
        assert result["state"]["attempt_count"] == 1
    
    def test_manage_capacity_reset(self):
        """Test manage_capacity with reset action."""
        agent = CapManagerAgent()
        
        agent.record_retrigger("TEST-123", "test")
        
        result = agent.manage_capacity(
            ticket_id="TEST-123",
            action="reset"
        )
        
        assert result["success"] is True
        assert result["action"] == "reset"
        assert agent.get_retrigger_state("TEST-123") is None
    
    def test_manage_capacity_unknown_action(self):
        """Test manage_capacity with unknown action."""
        agent = CapManagerAgent()
        
        result = agent.manage_capacity(
            ticket_id="TEST-123",
            action="invalid_action"
        )
        
        assert result["success"] is False
        assert "Unknown action" in result["error"]
    
    def test_multiple_tickets_independent(self):
        """Test that retrigger limits are tracked independently per ticket."""
        agent = CapManagerAgent(max_retrigger_attempts=2)
        
        agent.record_retrigger("TEST-123", "attempt 1")
        agent.record_retrigger("TEST-123", "attempt 2")
        
        # TEST-123 should be at limit
        assert not agent.can_retrigger("TEST-123", "should fail")
        
        # TEST-456 should still be able to retrigger
        assert agent.can_retrigger("TEST-456", "should succeed")
        agent.record_retrigger("TEST-456", "attempt 1")
        assert agent.can_retrigger("TEST-456", "should still succeed")
    
    def test_retrigger_reasons_tracked(self):
        """Test that retrigger reasons are properly tracked."""
        agent = CapManagerAgent()
        
        agent.record_retrigger("TEST-123", "dependency updated")
        agent.record_retrigger("TEST-123", "capacity available")
        agent.record_retrigger("TEST-123", "manual retrigger")
        
        state = agent.get_retrigger_state("TEST-123")
        assert len(state["trigger_reasons"]) == 3
        assert "dependency updated" in state["trigger_reasons"]
        assert "capacity available" in state["trigger_reasons"]
        assert "manual retrigger" in state["trigger_reasons"]


class TestIntegrationScenarios:
    """Integration test scenarios for Cap Manager Agent."""
    
    def test_typical_workflow(self):
        """Test a typical workflow with retriggers."""
        agent = CapManagerAgent(max_retrigger_attempts=3)
        
        # Initial check - should pass
        result = agent.manage_capacity("STORY-100", "check")
        assert result["success"] is True
        assert result["can_retrigger"] is True
        
        # First retrigger
        result = agent.manage_capacity(
            "STORY-100",
            "retrigger",
            context={"reason": "waiting for dependencies"}
        )
        assert result["success"] is True
        
        # Second retrigger
        result = agent.manage_capacity(
            "STORY-100",
            "retrigger",
            context={"reason": "dependencies resolved"}
        )
        assert result["success"] is True
        
        # Third retrigger
        result = agent.manage_capacity(
            "STORY-100",
            "retrigger",
            context={"reason": "capacity available"}
        )
        assert result["success"] is True
        
        # Fourth retrigger should fail
        result = agent.manage_capacity(
            "STORY-100",
            "retrigger",
            context={"reason": "should fail"}
        )
        assert result["success"] is False
        assert result["error"] == "Retrigger limit reached"
    
    def test_workflow_with_reset(self):
        """Test workflow with manual reset."""
        agent = CapManagerAgent(max_retrigger_attempts=2)
        
        # Hit the limit
        agent.manage_capacity("STORY-100", "retrigger", context={"reason": "1"})
        agent.manage_capacity("STORY-100", "retrigger", context={"reason": "2"})
        
        # Should be blocked
        result = agent.manage_capacity("STORY-100", "retrigger", context={"reason": "3"})
        assert result["success"] is False
        
        # Reset the state
        agent.manage_capacity("STORY-100", "reset")
        
        # Should be able to retrigger again
        result = agent.manage_capacity("STORY-100", "retrigger", context={"reason": "4"})
        assert result["success"] is True
