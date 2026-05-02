"""
Tests for retrigger monitoring and alerting.
"""

import pytest
from datetime import datetime, timedelta
from agents.monitoring import RetriggerMonitor, RetriggerAlert, create_dashboard_data


class TestRetriggerAlert:
    """Tests for RetriggerAlert dataclass."""
    
    def test_alert_creation(self):
        """Test creating a retrigger alert."""
        alert = RetriggerAlert(
            ticket_id="TEST-123",
            alert_type="limit_reached",
            severity="critical",
            message="Test alert",
            timestamp=datetime.utcnow(),
            metadata={"test": "data"}
        )
        
        assert alert.ticket_id == "TEST-123"
        assert alert.alert_type == "limit_reached"
        assert alert.severity == "critical"
        assert alert.message == "Test alert"
        assert alert.metadata == {"test": "data"}


class TestRetriggerMonitor:
    """Tests for RetriggerMonitor class."""
    
    def test_initialization(self):
        """Test monitor initialization."""
        monitor = RetriggerMonitor(alert_threshold=2)
        
        assert monitor.alert_threshold == 2
        assert monitor.alerts == []
        assert len(monitor.reason_stats) == 0
    
    def test_analyze_limit_reached(self):
        """Test alert generation when limit is reached."""
        monitor = RetriggerMonitor()
        
        state = {
            "ticket_id": "TEST-123",
            "attempt_count": 3,
            "max_attempts": 3,
            "trigger_reasons": ["reason1", "reason2", "reason3"],
        }
        
        alerts = monitor.analyze_retrigger_state("TEST-123", state)
        
        assert len(alerts) == 1
        assert alerts[0].alert_type == "limit_reached"
        assert alerts[0].severity == "critical"
        assert "TEST-123" in alerts[0].message
    
    def test_analyze_high_frequency(self):
        """Test alert generation for high frequency retriggers."""
        monitor = RetriggerMonitor(alert_threshold=2)
        
        state = {
            "ticket_id": "TEST-456",
            "attempt_count": 2,
            "max_attempts": 3,
            "trigger_reasons": ["reason1", "reason2"],
        }
        
        alerts = monitor.analyze_retrigger_state("TEST-456", state)
        
        assert len(alerts) == 1
        assert alerts[0].alert_type == "high_frequency"
        assert alerts[0].severity == "warning"
    
    def test_analyze_repeated_reason(self):
        """Test alert generation for repeated same reason."""
        monitor = RetriggerMonitor()
        
        state = {
            "ticket_id": "TEST-789",
            "attempt_count": 3,
            "max_attempts": 5,
            "trigger_reasons": ["same_reason", "same_reason", "same_reason"],
        }
        
        alerts = monitor.analyze_retrigger_state("TEST-789", state)
        
        # Should have pattern_detected alert
        pattern_alerts = [a for a in alerts if a.alert_type == "pattern_detected"]
        assert len(pattern_alerts) == 1
        assert "same reason" in pattern_alerts[0].message.lower()
    
    def test_analyze_no_alerts_for_low_count(self):
        """Test no alerts generated for low retrigger counts."""
        monitor = RetriggerMonitor(alert_threshold=3)
        
        state = {
            "ticket_id": "TEST-999",
            "attempt_count": 1,
            "max_attempts": 5,
            "trigger_reasons": ["reason1"],
        }
        
        alerts = monitor.analyze_retrigger_state("TEST-999", state)
        
        assert len(alerts) == 0
    
    def test_analyze_none_state(self):
        """Test handling of None state."""
        monitor = RetriggerMonitor()
        
        alerts = monitor.analyze_retrigger_state("TEST-123", None)
        
        assert len(alerts) == 0
    
    def test_reason_statistics_tracking(self):
        """Test that reason statistics are tracked correctly."""
        monitor = RetriggerMonitor()
        
        states = [
            {
                "ticket_id": "TEST-1",
                "attempt_count": 2,
                "max_attempts": 3,
                "trigger_reasons": ["dependency_issue", "capacity_issue"],
            },
            {
                "ticket_id": "TEST-2",
                "attempt_count": 1,
                "max_attempts": 3,
                "trigger_reasons": ["dependency_issue"],
            },
            {
                "ticket_id": "TEST-3",
                "attempt_count": 1,
                "max_attempts": 3,
                "trigger_reasons": ["capacity_issue"],
            },
        ]
        
        for state in states:
            monitor.analyze_retrigger_state(state["ticket_id"], state)
        
        assert monitor.reason_stats["dependency_issue"] == 2
        assert monitor.reason_stats["capacity_issue"] == 2
    
    def test_analyze_all_states(self):
        """Test analyzing all states together."""
        monitor = RetriggerMonitor(alert_threshold=2)
        
        all_states = {
            "TEST-1": {
                "ticket_id": "TEST-1",
                "attempt_count": 3,
                "max_attempts": 3,
                "trigger_reasons": ["reason1", "reason2", "reason3"],
            },
            "TEST-2": {
                "ticket_id": "TEST-2",
                "attempt_count": 2,
                "max_attempts": 3,
                "trigger_reasons": ["reason1", "reason2"],
            },
            "TEST-3": {
                "ticket_id": "TEST-3",
                "attempt_count": 1,
                "max_attempts": 3,
                "trigger_reasons": ["reason1"],
            },
        }
        
        report = monitor.analyze_all_states(all_states)
        
        assert report["total_tickets"] == 3
        assert report["tickets_at_limit"] == 1
        assert report["tickets_at_threshold"] == 2
        assert len(report["alerts"]) > 0
        assert "reason_statistics" in report
        assert report["reason_statistics"]["reason1"] == 6
    
    def test_systemic_issues_high_retrigger_rate(self):
        """Test detection of high retrigger rate systemic issue."""
        monitor = RetriggerMonitor(alert_threshold=2)
        
        # Create states where most tickets have high retrigger counts
        all_states = {
            f"TEST-{i}": {
                "ticket_id": f"TEST-{i}",
                "attempt_count": 2,
                "max_attempts": 3,
                "trigger_reasons": ["reason1", "reason2"],
            }
            for i in range(10)
        }
        
        report = monitor.analyze_all_states(all_states)
        
        systemic_issues = report["systemic_issues"]
        high_rate_issues = [
            issue for issue in systemic_issues
            if issue["type"] == "high_retrigger_rate"
        ]
        
        assert len(high_rate_issues) > 0
        assert high_rate_issues[0]["severity"] == "critical"
    
    def test_systemic_issues_common_reason(self):
        """Test detection of common failure reason."""
        monitor = RetriggerMonitor()
        
        all_states = {
            f"TEST-{i}": {
                "ticket_id": f"TEST-{i}",
                "attempt_count": 1,
                "max_attempts": 3,
                "trigger_reasons": ["common_issue"],
            }
            for i in range(5)
        }
        
        report = monitor.analyze_all_states(all_states)
        
        systemic_issues = report["systemic_issues"]
        common_reason_issues = [
            issue for issue in systemic_issues
            if issue["type"] == "common_failure_reason"
        ]
        
        assert len(common_reason_issues) > 0
        assert common_reason_issues[0]["reason"] == "common_issue"
    
    def test_get_alerts_no_filter(self):
        """Test getting all alerts without filters."""
        monitor = RetriggerMonitor()
        
        # Generate some alerts
        state1 = {
            "attempt_count": 3,
            "max_attempts": 3,
            "trigger_reasons": ["r1"],
        }
        state2 = {
            "attempt_count": 2,
            "max_attempts": 3,
            "trigger_reasons": ["r1", "r2"],
        }
        
        monitor.analyze_retrigger_state("TEST-1", state1)
        monitor.analyze_retrigger_state("TEST-2", state2)
        
        alerts = monitor.get_alerts()
        assert len(alerts) >= 2
    
    def test_get_alerts_by_severity(self):
        """Test filtering alerts by severity."""
        monitor = RetriggerMonitor(alert_threshold=2)
        
        state_critical = {
            "attempt_count": 3,
            "max_attempts": 3,
            "trigger_reasons": ["r1"],
        }
        state_warning = {
            "attempt_count": 2,
            "max_attempts": 3,
            "trigger_reasons": ["r1", "r2"],
        }
        
        monitor.analyze_retrigger_state("TEST-1", state_critical)
        monitor.analyze_retrigger_state("TEST-2", state_warning)
        
        critical_alerts = monitor.get_alerts(severity="critical")
        warning_alerts = monitor.get_alerts(severity="warning")
        
        assert len(critical_alerts) >= 1
        assert len(warning_alerts) >= 1
        assert all(a.severity == "critical" for a in critical_alerts)
        assert all(a.severity == "warning" for a in warning_alerts)
    
    def test_get_alerts_by_time(self):
        """Test filtering alerts by time."""
        monitor = RetriggerMonitor()
        
        state = {
            "attempt_count": 3,
            "max_attempts": 3,
            "trigger_reasons": ["r1"],
        }
        
        monitor.analyze_retrigger_state("TEST-1", state)
        
        # Get alerts from last hour
        since = datetime.utcnow() - timedelta(hours=1)
        recent_alerts = monitor.get_alerts(since=since)
        
        assert len(recent_alerts) >= 1
        assert all(a.timestamp >= since for a in recent_alerts)
    
    def test_clear_old_alerts(self):
        """Test clearing old alerts."""
        monitor = RetriggerMonitor()
        
        # Create an alert
        state = {
            "attempt_count": 3,
            "max_attempts": 3,
            "trigger_reasons": ["r1"],
        }
        monitor.analyze_retrigger_state("TEST-1", state)
        
        initial_count = len(monitor.alerts)
        assert initial_count > 0
        
        # Manually set alert timestamp to be old
        for alert in monitor.alerts:
            alert.timestamp = datetime.utcnow() - timedelta(hours=25)
        
        # Clear old alerts
        removed = monitor.clear_old_alerts(older_than_hours=24)
        
        assert removed == initial_count
        assert len(monitor.alerts) == 0
    
    def test_generate_report(self):
        """Test report generation."""
        monitor = RetriggerMonitor(alert_threshold=2)
        
        # Generate some alerts
        states = {
            "TEST-1": {
                "attempt_count": 3,
                "max_attempts": 3,
                "trigger_reasons": ["dependency_issue", "capacity_issue", "timing_issue"],
            },
            "TEST-2": {
                "attempt_count": 2,
                "max_attempts": 3,
                "trigger_reasons": ["dependency_issue", "capacity_issue"],
            },
        }
        
        for ticket_id, state in states.items():
            monitor.analyze_retrigger_state(ticket_id, state)
        
        report = monitor.generate_report()
        
        assert "Retrigger Monitor Report" in report
        assert "Total Alerts" in report
        assert "Alerts by Severity" in report
        assert "Top Retrigger Reasons" in report


class TestDashboardData:
    """Tests for dashboard data generation."""
    
    def test_create_dashboard_data(self):
        """Test creating dashboard data structure."""
        monitor = RetriggerMonitor(alert_threshold=2)
        
        # Generate some alerts
        states = {
            "TEST-1": {
                "attempt_count": 3,
                "max_attempts": 3,
                "trigger_reasons": ["reason1", "reason2", "reason3"],
            },
            "TEST-2": {
                "attempt_count": 2,
                "max_attempts": 3,
                "trigger_reasons": ["reason1", "reason2"],
            },
        }
        
        for ticket_id, state in states.items():
            monitor.analyze_retrigger_state(ticket_id, state)
        
        dashboard = create_dashboard_data(monitor)
        
        assert "summary" in dashboard
        assert "total_alerts" in dashboard["summary"]
        assert "critical_alerts" in dashboard["summary"]
        assert "warning_alerts" in dashboard["summary"]
        assert "alerts_by_severity" in dashboard
        assert "top_reasons" in dashboard
        assert "generated_at" in dashboard
    
    def test_dashboard_data_structure(self):
        """Test dashboard data has correct structure."""
        monitor = RetriggerMonitor()
        
        state = {
            "attempt_count": 3,
            "max_attempts": 3,
            "trigger_reasons": ["test_reason"],
        }
        monitor.analyze_retrigger_state("TEST-1", state)
        
        dashboard = create_dashboard_data(monitor)
        
        # Check summary structure
        assert isinstance(dashboard["summary"]["total_alerts"], int)
        assert isinstance(dashboard["summary"]["critical_alerts"], int)
        assert isinstance(dashboard["summary"]["warning_alerts"], int)
        
        # Check top reasons structure
        assert isinstance(dashboard["top_reasons"], list)
        if dashboard["top_reasons"]:
            assert "reason" in dashboard["top_reasons"][0]
            assert "count" in dashboard["top_reasons"][0]
