"""
Cap Manager Agent - Manages capacity planning and prevents infinite retrigger loops.

This agent is responsible for:
- Managing team capacity allocation
- Monitoring story point distribution
- Preventing infinite retrigger cycles with configurable max attempts
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RetriggerState:
    """Tracks retrigger attempts to prevent infinite loops."""
    
    ticket_id: str
    attempt_count: int = 0
    first_trigger_time: Optional[datetime] = None
    last_trigger_time: Optional[datetime] = None
    trigger_reasons: list[str] = field(default_factory=list)
    
    def increment(self, reason: str) -> None:
        """Increment the retrigger count and update timestamps."""
        self.attempt_count += 1
        self.last_trigger_time = datetime.utcnow()
        if self.first_trigger_time is None:
            self.first_trigger_time = datetime.utcnow()
        self.trigger_reasons.append(reason)


class CapManagerAgent:
    """
    Capacity Manager Agent with retrigger loop protection.
    
    Manages team capacity and prevents infinite retrigger cycles by:
    - Tracking retrigger attempts per ticket
    - Enforcing configurable max retrigger limits
    - Logging detailed retrigger history for debugging
    """
    
    def __init__(
        self,
        max_retrigger_attempts: Optional[int] = None,
        retrigger_window_minutes: Optional[int] = None
    ):
        """
        Initialize the Cap Manager Agent.
        
        Args:
            max_retrigger_attempts: Maximum number of retrigger attempts per ticket.
                                   Defaults to MAX_RETRIGGER_ATTEMPTS env var or 3.
            retrigger_window_minutes: Time window for counting retriggering.
                                     Defaults to RETRIGGER_WINDOW_MINUTES env var or 60.
        """
        self.max_retrigger_attempts = max_retrigger_attempts or int(
            os.getenv("MAX_RETRIGGER_ATTEMPTS", "3")
        )
        self.retrigger_window_minutes = retrigger_window_minutes or int(
            os.getenv("RETRIGGER_WINDOW_MINUTES", "60")
        )
        
        # Track retrigger state per ticket
        self._retrigger_state: Dict[str, RetriggerState] = {}
        
        logger.info(
            f"Cap Manager Agent initialized with max_retrigger_attempts={self.max_retrigger_attempts}, "
            f"retrigger_window_minutes={self.retrigger_window_minutes}"
        )
    
    def can_retrigger(self, ticket_id: str, reason: str = "unspecified") -> bool:
        """
        Check if a ticket can be retriggered without exceeding limits.
        
        Args:
            ticket_id: The Jira ticket ID to check
            reason: Reason for the retrigger attempt
            
        Returns:
            True if retrigger is allowed, False if limit reached
        """
        if ticket_id not in self._retrigger_state:
            self._retrigger_state[ticket_id] = RetriggerState(ticket_id=ticket_id)
        
        state = self._retrigger_state[ticket_id]
        
        # Check if we're within the time window and need to reset
        if state.first_trigger_time:
            elapsed_minutes = (
                datetime.utcnow() - state.first_trigger_time
            ).total_seconds() / 60
            
            if elapsed_minutes > self.retrigger_window_minutes:
                logger.info(
                    f"Resetting retrigger count for {ticket_id} - "
                    f"window expired ({elapsed_minutes:.1f} minutes)"
                )
                self._retrigger_state[ticket_id] = RetriggerState(ticket_id=ticket_id)
                state = self._retrigger_state[ticket_id]
        
        # Check if limit reached
        if state.attempt_count >= self.max_retrigger_attempts:
            logger.warning(
                f"Retrigger limit reached for {ticket_id}: "
                f"{state.attempt_count}/{self.max_retrigger_attempts} attempts. "
                f"Reasons: {state.trigger_reasons}"
            )
            return False
        
        return True
    
    def record_retrigger(self, ticket_id: str, reason: str = "unspecified") -> None:
        """
        Record a retrigger attempt for a ticket.
        
        Args:
            ticket_id: The Jira ticket ID being retriggered
            reason: Reason for the retrigger
        """
        if ticket_id not in self._retrigger_state:
            self._retrigger_state[ticket_id] = RetriggerState(ticket_id=ticket_id)
        
        state = self._retrigger_state[ticket_id]
        state.increment(reason)
        
        logger.info(
            f"Retrigger recorded for {ticket_id}: "
            f"attempt {state.attempt_count}/{self.max_retrigger_attempts}, "
            f"reason: {reason}"
        )
    
    def get_retrigger_state(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current retrigger state for a ticket.
        
        Args:
            ticket_id: The Jira ticket ID to query
            
        Returns:
            Dictionary with retrigger state information or None if not tracked
        """
        if ticket_id not in self._retrigger_state:
            return None
        
        state = self._retrigger_state[ticket_id]
        return {
            "ticket_id": state.ticket_id,
            "attempt_count": state.attempt_count,
            "max_attempts": self.max_retrigger_attempts,
            "first_trigger_time": state.first_trigger_time.isoformat() if state.first_trigger_time else None,
            "last_trigger_time": state.last_trigger_time.isoformat() if state.last_trigger_time else None,
            "trigger_reasons": state.trigger_reasons,
            "can_retrigger": self.can_retrigger(ticket_id, "query"),
        }
    
    def reset_retrigger_state(self, ticket_id: str) -> None:
        """
        Reset the retrigger state for a ticket.
        
        Useful when a ticket has been successfully processed or manually reset.
        
        Args:
            ticket_id: The Jira ticket ID to reset
        """
        if ticket_id in self._retrigger_state:
            logger.info(f"Resetting retrigger state for {ticket_id}")
            del self._retrigger_state[ticket_id]
    
    def get_all_retrigger_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Get retrigger states for all tracked tickets.
        
        Returns:
            Dictionary mapping ticket IDs to their retrigger state
        """
        return {
            ticket_id: self.get_retrigger_state(ticket_id)
            for ticket_id in self._retrigger_state.keys()
        }
    
    def manage_capacity(
        self,
        ticket_id: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for capacity management operations.
        
        Args:
            ticket_id: The Jira ticket ID to manage
            action: The action to perform (e.g., 'allocate', 'retrigger', 'check')
            context: Additional context for the operation
            
        Returns:
            Dictionary with operation result and metadata
        """
        context = context or {}
        reason = context.get("reason", "unspecified")
        
        logger.info(
            f"Cap Manager processing ticket {ticket_id}, action={action}, reason={reason}"
        )
        
        if action == "retrigger":
            if not self.can_retrigger(ticket_id, reason):
                return {
                    "success": False,
                    "ticket_id": ticket_id,
                    "action": action,
                    "error": "Retrigger limit reached",
                    "state": self.get_retrigger_state(ticket_id),
                }
            
            self.record_retrigger(ticket_id, reason)
            return {
                "success": True,
                "ticket_id": ticket_id,
                "action": action,
                "state": self.get_retrigger_state(ticket_id),
            }
        
        elif action == "check":
            return {
                "success": True,
                "ticket_id": ticket_id,
                "action": action,
                "can_retrigger": self.can_retrigger(ticket_id, "check"),
                "state": self.get_retrigger_state(ticket_id),
            }
        
        elif action == "reset":
            self.reset_retrigger_state(ticket_id)
            return {
                "success": True,
                "ticket_id": ticket_id,
                "action": action,
                "message": "Retrigger state reset",
            }
        
        else:
            logger.warning(f"Unknown action: {action}")
            return {
                "success": False,
                "ticket_id": ticket_id,
                "action": action,
                "error": f"Unknown action: {action}",
            }
