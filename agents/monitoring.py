"""
Monitoring and alerting utilities for Cap Manager Agent.

Provides functionality to track, report, and alert on retrigger patterns
and potential issues.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class RetriggerAlert:
    """Represents an alert for retrigger issues."""
    
    ticket_id: str
    alert_type: str  # 'limit_reached', 'high_frequency', 'pattern_detected'
    severity: str  # 'warning', 'error', 'critical'
    message: str
    timestamp: datetime
    metadata: Dict[str, Any]


class RetriggerMonitor:
    """
    Monitors retrigger patterns and generates alerts.
    
    Tracks retrigger behavior across tickets to identify:
    - Tickets hitting retrigger limits
    - High-frequency retrigger patterns
    - Common failure reasons
    - Systemic issues affecting multiple tickets
    """
    
    def __init__(self, alert_threshold: int = 2):
        """
        Initialize the retrigger monitor.
        
        Args:
            alert_threshold: Number of retriggers before generating a warning alert
        """
        self.alert_threshold = alert_threshold
        self.alerts: List[RetriggerAlert] = []
        self.reason_stats: Dict[str, int] = defaultdict(int)
    
    def analyze_retrigger_state(
        self,
        ticket_id: str,
        state: Dict[str, Any]
    ) -> List[RetriggerAlert]:
        """
        Analyze a ticket's retrigger state and generate alerts if needed.
        
        Args:
            ticket_id: The Jira ticket ID
            state: The retrigger state from CapManagerAgent.get_retrigger_state()
            
        Returns:
            List of alerts generated from the analysis
        """
        alerts = []
        
        if not state:
            return alerts
        
        attempt_count = state.get("attempt_count", 0)
        max_attempts = state.get("max_attempts", 3)
        trigger_reasons = state.get("trigger_reasons", [])
        
        # Track reason statistics
        for reason in trigger_reasons:
            self.reason_stats[reason] += 1
        
        # Alert if at limit
        if attempt_count >= max_attempts:
            alert = RetriggerAlert(
                ticket_id=ticket_id,
                alert_type="limit_reached",
                severity="critical",
                message=f"Ticket {ticket_id} has reached retrigger limit ({attempt_count}/{max_attempts})",
                timestamp=datetime.utcnow(),
                metadata={
                    "attempt_count": attempt_count,
                    "max_attempts": max_attempts,
                    "reasons": trigger_reasons,
                }
            )
            alerts.append(alert)
            self.alerts.append(alert)
        
        # Warning if approaching limit
        elif attempt_count >= self.alert_threshold:
            alert = RetriggerAlert(
                ticket_id=ticket_id,
                alert_type="high_frequency",
                severity="warning",
                message=f"Ticket {ticket_id} has high retrigger count ({attempt_count}/{max_attempts})",
                timestamp=datetime.utcnow(),
                metadata={
                    "attempt_count": attempt_count,
                    "max_attempts": max_attempts,
                    "reasons": trigger_reasons,
                }
            )
            alerts.append(alert)
            self.alerts.append(alert)
        
        # Detect pattern of same reason
        if len(trigger_reasons) > 1:
            unique_reasons = set(trigger_reasons)
            if len(unique_reasons) == 1:
                alert = RetriggerAlert(
                    ticket_id=ticket_id,
                    alert_type="pattern_detected",
                    severity="warning",
                    message=f"Ticket {ticket_id} repeatedly retriggered for same reason: {list(unique_reasons)[0]}",
                    timestamp=datetime.utcnow(),
                    metadata={
                        "repeated_reason": list(unique_reasons)[0],
                        "count": len(trigger_reasons),
                    }
                )
                alerts.append(alert)
                self.alerts.append(alert)
        
        return alerts
    
    def analyze_all_states(
        self,
        all_states: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze all retrigger states and generate a comprehensive report.
        
        Args:
            all_states: Dictionary of all retrigger states from CapManagerAgent
            
        Returns:
            Dictionary containing analysis results and alerts
        """
        all_alerts = []
        
        for ticket_id, state in all_states.items():
            alerts = self.analyze_retrigger_state(ticket_id, state)
            all_alerts.extend(alerts)
        
        # Analyze for systemic issues
        systemic_issues = self._detect_systemic_issues(all_states)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_tickets": len(all_states),
            "tickets_at_limit": sum(
                1 for state in all_states.values()
                if state and state.get("attempt_count", 0) >= state.get("max_attempts", 3)
            ),
            "tickets_at_threshold": sum(
                1 for state in all_states.values()
                if state and state.get("attempt_count", 0) >= self.alert_threshold
            ),
            "alerts": [
                {
                    "ticket_id": alert.ticket_id,
                    "type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "metadata": alert.metadata,
                }
                for alert in all_alerts
            ],
            "reason_statistics": dict(self.reason_stats),
            "systemic_issues": systemic_issues,
        }
    
    def _detect_systemic_issues(
        self,
        all_states: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect systemic issues affecting multiple tickets.
        
        Args:
            all_states: Dictionary of all retrigger states
            
        Returns:
            List of detected systemic issues
        """
        issues = []
        
        # Check if a large percentage of tickets are being retriggered
        total_tickets = len(all_states)
        if total_tickets > 0:
            high_retrigger_tickets = sum(
                1 for state in all_states.values()
                if state and state.get("attempt_count", 0) >= self.alert_threshold
            )
            
            percentage = (high_retrigger_tickets / total_tickets) * 100
            
            if percentage > 50:
                issues.append({
                    "type": "high_retrigger_rate",
                    "severity": "critical",
                    "message": f"{percentage:.1f}% of tickets have high retrigger counts",
                    "affected_tickets": high_retrigger_tickets,
                    "total_tickets": total_tickets,
                })
        
        # Check for common reasons across multiple tickets
        if self.reason_stats:
            most_common_reason = max(self.reason_stats, key=self.reason_stats.get)
            count = self.reason_stats[most_common_reason]
            
            if count >= 3:  # If same reason appears 3+ times
                issues.append({
                    "type": "common_failure_reason",
                    "severity": "warning",
                    "message": f"Common retrigger reason detected: '{most_common_reason}' ({count} occurrences)",
                    "reason": most_common_reason,
                    "count": count,
                })
        
        return issues
    
    def get_alerts(
        self,
        severity: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[RetriggerAlert]:
        """
        Get alerts, optionally filtered by severity and time.
        
        Args:
            severity: Filter by severity level ('warning', 'error', 'critical')
            since: Only return alerts after this timestamp
            
        Returns:
            List of matching alerts
        """
        alerts = self.alerts
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if since:
            alerts = [a for a in alerts if a.timestamp >= since]
        
        return alerts
    
    def clear_old_alerts(self, older_than_hours: int = 24) -> int:
        """
        Clear alerts older than specified hours.
        
        Args:
            older_than_hours: Remove alerts older than this many hours
            
        Returns:
            Number of alerts removed
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        initial_count = len(self.alerts)
        
        self.alerts = [
            alert for alert in self.alerts
            if alert.timestamp >= cutoff_time
        ]
        
        removed = initial_count - len(self.alerts)
        logger.info(f"Cleared {removed} alerts older than {older_than_hours} hours")
        
        return removed
    
    def generate_report(self) -> str:
        """
        Generate a human-readable report of retrigger activity.
        
        Returns:
            Formatted report string
        """
        report_lines = [
            "=== Retrigger Monitor Report ===",
            f"Generated: {datetime.utcnow().isoformat()}",
            "",
            f"Total Alerts: {len(self.alerts)}",
        ]
        
        # Count by severity
        severity_counts = defaultdict(int)
        for alert in self.alerts:
            severity_counts[alert.severity] += 1
        
        report_lines.append("\nAlerts by Severity:")
        for severity in ["critical", "error", "warning"]:
            count = severity_counts.get(severity, 0)
            report_lines.append(f"  {severity.upper()}: {count}")
        
        # Top reasons
        if self.reason_stats:
            report_lines.append("\nTop Retrigger Reasons:")
            sorted_reasons = sorted(
                self.reason_stats.items(),
                key=lambda x: x[1],
                reverse=True
            )
            for reason, count in sorted_reasons[:5]:
                report_lines.append(f"  {reason}: {count}")
        
        # Recent critical alerts
        recent_critical = [
            alert for alert in self.alerts[-10:]
            if alert.severity == "critical"
        ]
        
        if recent_critical:
            report_lines.append("\nRecent Critical Alerts:")
            for alert in recent_critical:
                report_lines.append(f"  [{alert.timestamp.isoformat()}] {alert.ticket_id}: {alert.message}")
        
        return "\n".join(report_lines)


def create_dashboard_data(monitor: RetriggerMonitor) -> Dict[str, Any]:
    """
    Create data structure suitable for dashboard display.
    
    Args:
        monitor: RetriggerMonitor instance
        
    Returns:
        Dictionary with dashboard data
    """
    recent_alerts = monitor.get_alerts(since=datetime.utcnow() - timedelta(hours=24))
    
    # Group alerts by severity
    alerts_by_severity = defaultdict(list)
    for alert in recent_alerts:
        alerts_by_severity[alert.severity].append({
            "ticket_id": alert.ticket_id,
            "type": alert.alert_type,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
        })
    
    # Top reasons for last 24 hours
    top_reasons = sorted(
        monitor.reason_stats.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    return {
        "summary": {
            "total_alerts": len(recent_alerts),
            "critical_alerts": len(alerts_by_severity.get("critical", [])),
            "warning_alerts": len(alerts_by_severity.get("warning", [])),
        },
        "alerts_by_severity": dict(alerts_by_severity),
        "top_reasons": [
            {"reason": reason, "count": count}
            for reason, count in top_reasons
        ],
        "generated_at": datetime.utcnow().isoformat(),
    }
