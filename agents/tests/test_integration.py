"""
Integration tests for Cap Manager Agent with monitoring.
"""

import pytest
from agents.cap_manager_agent import CapManagerAgent
from agents.monitoring import RetriggerMonitor


class TestCapManagerIntegration:
    """Integration tests combining Cap Manager and monitoring."""
    
    def test_full_workflow_with_monitoring(self):
        """Test complete workflow with retrigger management and monitoring."""
        # Initialize components
        cap_manager = CapManagerAgent(max_retrigger_attempts=3)
        monitor = RetriggerMonitor(alert_threshold=2)
        
        # Simulate ticket processing with retriggers
        tickets = ["STORY-100", "STORY-101", "STORY-102"]
        
        # Process first ticket - needs multiple retriggers
        for i in range(3):
            result = cap_manager.manage_capacity(
                ticket_id="STORY-100",
                action="retrigger",
                context={"reason": f"attempt {i+1}"}
            )
            
            if not result["success"]:
                break
        
        # Analyze state and generate alerts
        state = cap_manager.get_retrigger_state("STORY-100")
        alerts = monitor.analyze_retrigger_state("STORY-100", state)
        
        # Should have critical alert for limit reached
        assert len(alerts) > 0
        assert any(a.alert_type == "limit_reached" for a in alerts)
        
        # Process second ticket - moderate retriggers
        cap_manager.manage_capacity(
            ticket_id="STORY-101",
            action="retrigger",
            context={"reason": "dependency wait"}
        )
        cap_manager.manage_capacity(
            ticket_id="STORY-101",
            action="retrigger",
            context={"reason": "dependency wait"}
        )
        
        state = cap_manager.get_retrigger_state("STORY-101")
        alerts = monitor.analyze_retrigger_state("STORY-101", state)
        
        # Should have warning alert for high frequency
        assert any(a.alert_type == "high_frequency" for a in alerts)
        
        # Process third ticket - single retrigger
        cap_manager.manage_capacity(
            ticket_id="STORY-102",
            action="retrigger",
            context={"reason": "capacity check"}
        )
        
        # Analyze all states
        all_states = cap_manager.get_all_retrigger_states()
        full_report = monitor.analyze_all_states(all_states)
        
        assert full_report["total_tickets"] == 3
        assert full_report["tickets_at_limit"] == 1
        assert len(full_report["alerts"]) >= 2
        
        # Generate report
        report = monitor.generate_report()
        assert "Retrigger Monitor Report" in report
        assert "CRITICAL" in report
    
    def test_orchestrator_simulation(self):
        """Simulate orchestrator behavior with Cap Manager."""
        cap_manager = CapManagerAgent(max_retrigger_attempts=3)
        monitor = RetriggerMonitor()
        
        # Simulate processing multiple tickets
        def process_ticket(ticket_id: str, ready: bool, reason: str = "processing"):
            if ready:
                # Ticket is ready, process it
                cap_manager.reset_retrigger_state(ticket_id)
                return {"status": "completed", "ticket_id": ticket_id}
            else:
                # Ticket not ready, check if can retrigger
                result = cap_manager.manage_capacity(
                    ticket_id=ticket_id,
                    action="retrigger",
                    context={"reason": reason}
                )
                
                if not result["success"]:
                    # Hit limit, escalate
                    return {"status": "escalated", "ticket_id": ticket_id}
                else:
                    return {"status": "retriggered", "ticket_id": ticket_id}
        
        # Process tickets
        results = []
        
        # STORY-200: Dependencies not ready for 3 attempts, then ready
        for i in range(3):
            results.append(process_ticket("STORY-200", False, "waiting for dependencies"))
        results.append(process_ticket("STORY-200", True))
        
        # STORY-201: Capacity issues, hit limit
        for i in range(4):
            results.append(process_ticket("STORY-201", False, "insufficient capacity"))
        
        # STORY-202: Ready immediately
        results.append(process_ticket("STORY-202", True))
        
        # Check results
        completed = [r for r in results if r["status"] == "completed"]
        escalated = [r for r in results if r["status"] == "escalated"]
        retriggered = [r for r in results if r["status"] == "retriggered"]
        
        assert len(completed) == 2  # STORY-200 and STORY-202
        assert len(escalated) == 1  # STORY-201 hit limit
        assert len(retriggered) == 6  # Various retriggers
        
        # Analyze with monitoring
        all_states = cap_manager.get_all_retrigger_states()
        
        # STORY-200 should be cleared (completed)
        assert "STORY-200" not in all_states
        
        # STORY-201 should be at limit
        assert "STORY-201" in all_states
        state_201 = all_states["STORY-201"]
        assert state_201["attempt_count"] == 3
        
        # STORY-202 should not be tracked (never retriggered)
        assert "STORY-202" not in all_states
    
    def test_dashboard_generation(self):
        """Test generating dashboard data from integrated system."""
        from agents.monitoring import create_dashboard_data
        
        cap_manager = CapManagerAgent(max_retrigger_attempts=3)
        monitor = RetriggerMonitor(alert_threshold=2)
        
        # Create various scenarios
        scenarios = [
            ("CRITICAL-1", 3, "limit reached"),
            ("WARNING-1", 2, "high frequency"),
            ("WARNING-2", 2, "high frequency"),
            ("OK-1", 1, "normal"),
        ]
        
        for ticket_id, attempts, reason in scenarios:
            for i in range(attempts):
                cap_manager.manage_capacity(
                    ticket_id=ticket_id,
                    action="retrigger",
                    context={"reason": reason}
                )
        
        # Analyze all states
        all_states = cap_manager.get_all_retrigger_states()
        monitor.analyze_all_states(all_states)
        
        # Generate dashboard
        dashboard = create_dashboard_data(monitor)
        
        assert dashboard["summary"]["total_alerts"] > 0
        assert dashboard["summary"]["critical_alerts"] >= 1
        assert dashboard["summary"]["warning_alerts"] >= 2
        assert len(dashboard["top_reasons"]) > 0
        
        # Verify dashboard structure
        assert "alerts_by_severity" in dashboard
        assert "critical" in dashboard["alerts_by_severity"]
        assert "warning" in dashboard["alerts_by_severity"]


class TestErrorHandling:
    """Test error handling in integrated scenarios."""
    
    def test_invalid_action_handling(self):
        """Test handling of invalid actions."""
        cap_manager = CapManagerAgent()
        
        result = cap_manager.manage_capacity(
            ticket_id="TEST-1",
            action="invalid_action"
        )
        
        assert result["success"] is False
        assert "Unknown action" in result["error"]
    
    def test_monitoring_with_none_states(self):
        """Test monitoring handles None states gracefully."""
        monitor = RetriggerMonitor()
        
        # Analyze None state
        alerts = monitor.analyze_retrigger_state("TEST-1", None)
        assert len(alerts) == 0
        
        # Analyze empty dict
        report = monitor.analyze_all_states({})
        assert report["total_tickets"] == 0
        assert len(report["alerts"]) == 0
    
    def test_reset_during_monitoring(self):
        """Test that resets are properly reflected in monitoring."""
        cap_manager = CapManagerAgent()
        monitor = RetriggerMonitor()
        
        # Create retrigger history
        cap_manager.record_retrigger("TEST-1", "reason 1")
        cap_manager.record_retrigger("TEST-1", "reason 2")
        
        # Analyze
        state = cap_manager.get_retrigger_state("TEST-1")
        alerts_before = monitor.analyze_retrigger_state("TEST-1", state)
        assert len(alerts_before) > 0
        
        # Reset
        cap_manager.reset_retrigger_state("TEST-1")
        
        # Analyze again
        state_after = cap_manager.get_retrigger_state("TEST-1")
        assert state_after is None


class TestPerformance:
    """Test performance with many tickets."""
    
    def test_many_tickets(self):
        """Test handling many tickets efficiently."""
        cap_manager = CapManagerAgent()
        monitor = RetriggerMonitor()
        
        # Create 100 tickets with varying retrigger counts
        for i in range(100):
            ticket_id = f"PERF-{i}"
            attempts = (i % 3) + 1  # 1-3 attempts
            
            for _ in range(attempts):
                cap_manager.record_retrigger(ticket_id, f"test reason {i}")
        
        # Analyze all states
        all_states = cap_manager.get_all_retrigger_states()
        assert len(all_states) == 100
        
        # Generate report
        report = monitor.analyze_all_states(all_states)
        assert report["total_tickets"] == 100
        
        # Generate dashboard
        from agents.monitoring import create_dashboard_data
        dashboard = create_dashboard_data(monitor)
        assert dashboard["summary"]["total_alerts"] >= 0
