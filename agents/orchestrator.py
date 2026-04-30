"""
agents/orchestrator.py
──────────────────────
Sprint Orchestrator with resume capability.

The Orchestrator sequences and executes stories from a sprint in dependency order
based on execution_order (customfield_10071). It persists state to the database
and can resume execution after failures or interruptions.

Key features:
- Reads execution_order from Jira tickets
- Executes tickets sequentially in the correct order
- Persists state after each ticket completion
- Supports resume from last checkpoint
- Handles failures gracefully with detailed error logging
"""

import os
import sys
import time
from typing import Dict, List, Optional, Tuple
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../uat/backend"))

from sqlalchemy.orm import Session
from models import OrchestratorStatus
from database import SessionLocal

from agents.orchestrator_state import StateManager


class TicketExecutionError(Exception):
    """Exception raised when a ticket execution fails."""
    pass


class Orchestrator:
    """Sprint orchestrator with state persistence and resume capability."""

    def __init__(
        self,
        jira_project_key: str,
        db: Optional[Session] = None,
        verbose: bool = True,
    ):
        """Initialize orchestrator.
        
        Args:
            jira_project_key: Jira project key (e.g., 'SDT1')
            db: Database session. If None, creates a new session.
            verbose: Whether to print execution logs
        """
        self.jira_project_key = jira_project_key
        self.verbose = verbose
        self._db = db
        self._owns_session = db is None
        self.state_manager = StateManager(db=db)

    def __enter__(self):
        """Context manager entry."""
        if self._owns_session:
            self._db = SessionLocal()
            self.state_manager = StateManager(db=self._db)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._owns_session and self._db:
            self._db.close()

    def log(self, message: str) -> None:
        """Log a message if verbose mode is enabled.
        
        Args:
            message: Message to log
        """
        if self.verbose:
            print(f"[ORCHESTRATOR] {message}")

    def get_sprint_tickets(self, sprint_id: int) -> List[Dict]:
        """Fetch all tickets in a sprint and sort by execution_order.
        
        This is a placeholder - in production, this would call the Jira API
        to fetch tickets and their execution_order (customfield_10071).
        
        Args:
            sprint_id: Jira sprint ID
            
        Returns:
            List of ticket dictionaries sorted by execution_order
        """
        # TODO: Implement actual Jira API call
        # For now, return empty list as a placeholder
        # In production:
        # 1. Call Jira API to get all issues in sprint
        # 2. Filter for stories (not subtasks or epics)
        # 3. Read customfield_10071 (execution_order)
        # 4. Sort by execution_order ascending
        # 5. Return list of dicts with keys: key, summary, execution_order, status
        
        self.log(f"Fetching tickets for sprint {sprint_id}")
        return []

    def execute_ticket(self, ticket_key: str) -> bool:
        """Execute a single ticket.
        
        This is a placeholder for the actual ticket execution logic.
        In production, this would:
        1. Assign ticket to appropriate agent (Dev, QA, etc.)
        2. Execute the work
        3. Wait for completion
        4. Verify results
        
        Args:
            ticket_key: Jira ticket key (e.g., 'SDT1-42')
            
        Returns:
            bool: True if execution succeeded, False otherwise
            
        Raises:
            TicketExecutionError: If execution fails
        """
        self.log(f"Executing ticket: {ticket_key}")
        
        # TODO: Implement actual ticket execution
        # Placeholder that simulates execution
        time.sleep(0.1)  # Simulate work
        
        # Placeholder success
        return True

    def start_sprint(
        self,
        sprint_id: int,
        sprint_name: str,
    ) -> UUID:
        """Start executing a sprint from the beginning.
        
        Args:
            sprint_id: Jira sprint ID
            sprint_name: Sprint name
            
        Returns:
            UUID: State ID for tracking execution
        """
        self.log(f"Starting sprint: {sprint_name} (ID: {sprint_id})")
        
        # Fetch tickets from Jira
        tickets = self.get_sprint_tickets(sprint_id)
        
        if not tickets:
            self.log("Warning: No tickets found in sprint")
        
        # Create ticket queue (just the keys, in execution_order)
        ticket_queue = [t["key"] for t in tickets]
        
        self.log(f"Ticket queue: {ticket_queue}")
        
        # Create state
        state = self.state_manager.create_state(
            sprint_id=sprint_id,
            sprint_name=sprint_name,
            jira_project_key=self.jira_project_key,
            ticket_queue=ticket_queue,
        )
        
        self.log(f"Created state: {state.id}")
        
        # Execute the sprint
        try:
            self._execute_sprint(state.id)
        except Exception as e:
            self.log(f"Sprint execution failed: {e}")
            self.state_manager.fail_execution(state.id, str(e))
            raise
        
        return state.id

    def resume_sprint(self, state_id: UUID) -> None:
        """Resume executing a sprint from the last checkpoint.
        
        Args:
            state_id: UUID of the orchestrator state to resume
            
        Raises:
            ValueError: If state not found or not resumable
        """
        state = self.state_manager.get_state(state_id)
        
        if not state:
            raise ValueError(f"State {state_id} not found")
        
        if state.status not in [OrchestratorStatus.PAUSED, OrchestratorStatus.FAILED]:
            raise ValueError(
                f"Cannot resume state with status {state.status.value}. "
                f"Only PAUSED or FAILED states can be resumed."
            )
        
        self.log(f"Resuming sprint: {state.sprint_name} (state: {state.id})")
        self.log(f"Remaining tickets: {state.ticket_queue}")
        
        # Resume execution
        try:
            self._execute_sprint(state.id)
        except Exception as e:
            self.log(f"Sprint execution failed: {e}")
            self.state_manager.fail_execution(state.id, str(e))
            raise

    def _execute_sprint(self, state_id: UUID) -> None:
        """Internal method to execute tickets in a sprint.
        
        Args:
            state_id: UUID of the orchestrator state
        """
        # Mark as running
        state = self.state_manager.start_execution(state_id)
        
        self.log(f"Executing {len(state.ticket_queue)} tickets")
        
        # Process each ticket in the queue
        while state.ticket_queue:
            # Get next ticket
            ticket_key = state.ticket_queue[0]
            
            self.log(f"Processing ticket: {ticket_key}")
            
            # Update current ticket
            self.state_manager.checkpoint(state_id, current_ticket=ticket_key)
            
            try:
                # Execute the ticket
                success = self.execute_ticket(ticket_key)
                
                if success:
                    # Mark as completed
                    self.log(f"✓ Completed: {ticket_key}")
                    state = self.state_manager.mark_ticket_completed(state_id, ticket_key)
                else:
                    # Execution returned False - treat as failure
                    error_msg = f"Ticket execution returned False"
                    self.log(f"✗ Failed: {ticket_key} - {error_msg}")
                    state = self.state_manager.mark_ticket_failed(
                        state_id,
                        ticket_key,
                        error_msg,
                    )
                    
            except Exception as e:
                # Handle execution errors
                error_msg = f"{type(e).__name__}: {str(e)}"
                self.log(f"✗ Failed: {ticket_key} - {error_msg}")
                state = self.state_manager.mark_ticket_failed(
                    state_id,
                    ticket_key,
                    error_msg,
                )
                
                # Optionally pause on errors (can be configured)
                # For now, we continue with remaining tickets
                continue
        
        # All tickets processed
        self.log("All tickets processed")
        self.state_manager.complete_execution(state_id)
        
        # Print summary
        state = self.state_manager.get_state(state_id)
        progress = self.state_manager.get_progress(state_id)
        
        self.log(f"Execution complete:")
        self.log(f"  ✓ Completed: {progress['completed_tickets']}")
        self.log(f"  ✗ Failed: {progress['failed_tickets']}")
        
        if state.failed_tickets:
            self.log("Failed tickets:")
            for failure in state.failed_tickets:
                self.log(f"  - {failure['ticket_key']}: {failure['error_message']}")

    def pause(self, state_id: UUID, reason: Optional[str] = None) -> None:
        """Pause the execution of a sprint.
        
        Args:
            state_id: UUID of the orchestrator state
            reason: Optional reason for pausing
        """
        self.log(f"Pausing execution: {reason or 'User requested'}")
        self.state_manager.pause_execution(state_id, reason)

    def cancel(self, state_id: UUID, reason: Optional[str] = None) -> None:
        """Cancel the execution of a sprint.
        
        Args:
            state_id: UUID of the orchestrator state
            reason: Optional reason for cancellation
        """
        self.log(f"Cancelling execution: {reason or 'User requested'}")
        self.state_manager.cancel_execution(state_id, reason)

    def get_progress(self, state_id: UUID) -> Dict:
        """Get execution progress for a sprint.
        
        Args:
            state_id: UUID of the orchestrator state
            
        Returns:
            Dictionary with progress information
        """
        return self.state_manager.get_progress(state_id)

    def list_resumable(self) -> List[Dict]:
        """List all sprints that can be resumed.
        
        Returns:
            List of dictionaries with sprint and state information
        """
        states = self.state_manager.get_resumable_states()
        
        return [
            {
                "state_id": str(state.id),
                "sprint_id": state.sprint_id,
                "sprint_name": state.sprint_name,
                "status": state.status.value,
                "total_tickets": state.total_tickets,
                "completed": len(state.completed_tickets or []),
                "failed": len(state.failed_tickets or []),
                "remaining": len(state.ticket_queue or []),
                "last_updated": state.updated_at.isoformat(),
            }
            for state in states
        ]


def start_sprint_execution(
    sprint_id: int,
    sprint_name: str,
    jira_project_key: str,
    verbose: bool = True,
) -> UUID:
    """Convenience function to start a sprint execution.
    
    Args:
        sprint_id: Jira sprint ID
        sprint_name: Sprint name
        jira_project_key: Jira project key
        verbose: Whether to print execution logs
        
    Returns:
        UUID: State ID for tracking execution
    """
    with Orchestrator(jira_project_key, verbose=verbose) as orchestrator:
        return orchestrator.start_sprint(sprint_id, sprint_name)


def resume_sprint_execution(
    state_id: UUID,
    jira_project_key: str,
    verbose: bool = True,
) -> None:
    """Convenience function to resume a sprint execution.
    
    Args:
        state_id: UUID of the orchestrator state to resume
        jira_project_key: Jira project key
        verbose: Whether to print execution logs
    """
    with Orchestrator(jira_project_key, verbose=verbose) as orchestrator:
        orchestrator.resume_sprint(state_id)
