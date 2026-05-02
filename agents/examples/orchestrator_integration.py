"""
Example integration of Cap Manager Agent with orchestrator.

This demonstrates how to integrate retrigger loop protection into
the ticket processing pipeline.
"""

import logging
from typing import Dict, Any, Optional
from agents.cap_manager_agent import CapManagerAgent

logger = logging.getLogger(__name__)


class TicketOrchestrator:
    """Example orchestrator with Cap Manager Agent integration."""
    
    def __init__(self):
        """Initialize the orchestrator with Cap Manager Agent."""
        self.cap_manager = CapManagerAgent(
            max_retrigger_attempts=3,
            retrigger_window_minutes=60
        )
        logger.info("Orchestrator initialized with Cap Manager Agent")
    
    def process_ticket(self, ticket_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a ticket with retrigger protection.
        
        Args:
            ticket_id: The Jira ticket ID to process
            context: Processing context including dependencies, status, etc.
            
        Returns:
            Dictionary with processing result
        """
        logger.info(f"Processing ticket {ticket_id}")
        
        # Example: Check if dependencies are ready
        if not self._check_dependencies(ticket_id, context):
            return self._handle_retrigger(
                ticket_id,
                reason="waiting for dependencies",
                context=context
            )
        
        # Example: Check if capacity is available
        if not self._check_capacity(ticket_id, context):
            return self._handle_retrigger(
                ticket_id,
                reason="insufficient capacity",
                context=context
            )
        
        # Process the ticket
        result = self._execute_ticket(ticket_id, context)
        
        # Reset retrigger state on successful completion
        if result.get("success"):
            self.cap_manager.reset_retrigger_state(ticket_id)
            logger.info(f"Ticket {ticket_id} processed successfully, state reset")
        
        return result
    
    def _handle_retrigger(
        self,
        ticket_id: str,
        reason: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle retrigger logic with loop protection.
        
        Args:
            ticket_id: The Jira ticket ID to retrigger
            reason: Reason for the retrigger
            context: Processing context
            
        Returns:
            Dictionary with retrigger result
        """
        logger.info(f"Attempting retrigger for {ticket_id}: {reason}")
        
        # Use Cap Manager to check and record retrigger
        result = self.cap_manager.manage_capacity(
            ticket_id=ticket_id,
            action="retrigger",
            context={"reason": reason}
        )
        
        if not result["success"]:
            # Retrigger limit reached - escalate
            logger.error(
                f"Retrigger limit reached for {ticket_id}: {result['error']}"
            )
            self._escalate_ticket(ticket_id, result)
            
            return {
                "status": "escalated",
                "ticket_id": ticket_id,
                "reason": "retrigger_limit_reached",
                "details": result,
            }
        
        # Schedule for later processing
        logger.info(
            f"Retrigger scheduled for {ticket_id}: "
            f"attempt {result['state']['attempt_count']}/{result['state']['max_attempts']}"
        )
        
        return {
            "status": "retriggered",
            "ticket_id": ticket_id,
            "reason": reason,
            "retrigger_state": result["state"],
        }
    
    def _check_dependencies(self, ticket_id: str, context: Dict[str, Any]) -> bool:
        """
        Check if ticket dependencies are ready.
        
        Args:
            ticket_id: The Jira ticket ID
            context: Processing context
            
        Returns:
            True if dependencies are ready, False otherwise
        """
        # Example implementation - replace with actual logic
        dependencies = context.get("dependencies", [])
        return all(dep.get("status") == "done" for dep in dependencies)
    
    def _check_capacity(self, ticket_id: str, context: Dict[str, Any]) -> bool:
        """
        Check if capacity is available for the ticket.
        
        Args:
            ticket_id: The Jira ticket ID
            context: Processing context
            
        Returns:
            True if capacity is available, False otherwise
        """
        # Example implementation - replace with actual logic
        required_capacity = context.get("story_points", 0)
        available_capacity = context.get("available_capacity", 0)
        return available_capacity >= required_capacity
    
    def _execute_ticket(self, ticket_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the ticket processing.
        
        Args:
            ticket_id: The Jira ticket ID
            context: Processing context
            
        Returns:
            Dictionary with execution result
        """
        # Example implementation - replace with actual logic
        logger.info(f"Executing ticket {ticket_id}")
        
        try:
            # Perform actual processing...
            return {
                "success": True,
                "ticket_id": ticket_id,
                "message": "Ticket processed successfully",
            }
        except Exception as e:
            logger.error(f"Error processing ticket {ticket_id}: {e}")
            return {
                "success": False,
                "ticket_id": ticket_id,
                "error": str(e),
            }
    
    def _escalate_ticket(self, ticket_id: str, retrigger_result: Dict[str, Any]) -> None:
        """
        Escalate a ticket that has exceeded retrigger limits.
        
        Args:
            ticket_id: The Jira ticket ID to escalate
            retrigger_result: The retrigger result containing state information
        """
        logger.warning(f"Escalating ticket {ticket_id} - retrigger limit reached")
        
        # Example actions:
        # 1. Send notification to team
        # 2. Add comment to Jira ticket
        # 3. Update ticket status to "Needs Review"
        # 4. Create alert in monitoring system
        
        state = retrigger_result.get("state", {})
        reasons = state.get("trigger_reasons", [])
        
        message = (
            f"Ticket {ticket_id} has exceeded the retrigger limit "
            f"({state.get('attempt_count', 0)}/{state.get('max_attempts', 0)} attempts). "
            f"Reasons: {', '.join(reasons)}. Manual intervention required."
        )
        
        # Send notification (example - implement actual notification)
        logger.error(f"ESCALATION: {message}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status including retrigger statistics.
        
        Returns:
            Dictionary with health status and metrics
        """
        all_states = self.cap_manager.get_all_retrigger_states()
        
        # Calculate statistics
        total_tickets = len(all_states)
        at_limit = sum(
            1 for state in all_states.values()
            if state and not state.get("can_retrigger", True)
        )
        
        return {
            "status": "healthy" if at_limit == 0 else "degraded",
            "total_tickets_tracked": total_tickets,
            "tickets_at_limit": at_limit,
            "retrigger_states": all_states,
        }


def example_usage():
    """Example usage of the orchestrator with Cap Manager integration."""
    orchestrator = TicketOrchestrator()
    
    # Example 1: Process a ticket with dependencies not ready
    context1 = {
        "dependencies": [
            {"ticket_id": "STORY-100", "status": "in_progress"},
            {"ticket_id": "STORY-101", "status": "done"},
        ],
        "story_points": 5,
        "available_capacity": 10,
    }
    
    result1 = orchestrator.process_ticket("STORY-102", context1)
    print(f"Result 1: {result1}")
    
    # Example 2: Process with dependencies ready but insufficient capacity
    context2 = {
        "dependencies": [
            {"ticket_id": "STORY-100", "status": "done"},
            {"ticket_id": "STORY-101", "status": "done"},
        ],
        "story_points": 15,
        "available_capacity": 10,
    }
    
    result2 = orchestrator.process_ticket("STORY-103", context2)
    print(f"Result 2: {result2}")
    
    # Example 3: Check health status
    health = orchestrator.get_health_status()
    print(f"Health Status: {health}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    example_usage()
