"""
agents/orchestrator_state.py
────────────────────────────
State management for the Orchestrator with persistence to database.

This module provides utilities to save and restore orchestrator execution state,
enabling resume capability after failures, interruptions, or manual pauses.
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../uat/backend"))

from sqlalchemy.orm import Session
from models import OrchestratorState, OrchestratorStatus
from database import SessionLocal


class StateManager:
    """Manages orchestrator state persistence and recovery."""

    def __init__(self, db: Optional[Session] = None):
        """Initialize state manager.
        
        Args:
            db: Database session. If None, creates a new session.
        """
        self._db = db
        self._owns_session = db is None

    def __enter__(self):
        """Context manager entry."""
        if self._owns_session:
            self._db = SessionLocal()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._owns_session and self._db:
            self._db.close()

    @property
    def db(self) -> Session:
        """Get database session."""
        if self._db is None:
            raise RuntimeError("StateManager not initialized with a session")
        return self._db

    def create_state(
        self,
        sprint_id: int,
        sprint_name: str,
        jira_project_key: str,
        ticket_queue: List[str],
    ) -> OrchestratorState:
        """Create a new orchestrator state for a sprint.
        
        Args:
            sprint_id: Jira sprint ID
            sprint_name: Sprint name
            jira_project_key: Jira project key (e.g., 'SDT1')
            ticket_queue: Ordered list of ticket keys to execute
            
        Returns:
            OrchestratorState: Created state object
        """
        state = OrchestratorState(
            sprint_id=sprint_id,
            sprint_name=sprint_name,
            jira_project_key=jira_project_key,
            status=OrchestratorStatus.PENDING,
            ticket_queue=ticket_queue,
            completed_tickets=[],
            failed_tickets=[],
            current_ticket=None,
            total_tickets=len(ticket_queue),
            started_at=None,
            completed_at=None,
            last_checkpoint_at=None,
            error_message=None,
        )
        
        self.db.add(state)
        self.db.commit()
        self.db.refresh(state)
        
        return state

    def get_state(self, state_id: UUID) -> Optional[OrchestratorState]:
        """Retrieve orchestrator state by ID.
        
        Args:
            state_id: UUID of the state
            
        Returns:
            OrchestratorState or None if not found
        """
        return self.db.query(OrchestratorState).filter(
            OrchestratorState.id == state_id
        ).first()

    def get_latest_state_for_sprint(self, sprint_id: int) -> Optional[OrchestratorState]:
        """Get the most recent orchestrator state for a sprint.
        
        Args:
            sprint_id: Jira sprint ID
            
        Returns:
            OrchestratorState or None if no state exists
        """
        return self.db.query(OrchestratorState).filter(
            OrchestratorState.sprint_id == sprint_id
        ).order_by(OrchestratorState.created_at.desc()).first()

    def get_resumable_states(self) -> List[OrchestratorState]:
        """Get all states that can be resumed (PAUSED or FAILED status).
        
        Returns:
            List of resumable OrchestratorState objects
        """
        return self.db.query(OrchestratorState).filter(
            OrchestratorState.status.in_([
                OrchestratorStatus.PAUSED,
                OrchestratorStatus.FAILED,
            ])
        ).order_by(OrchestratorState.updated_at.desc()).all()

    def start_execution(self, state_id: UUID) -> OrchestratorState:
        """Mark state as running and set start time.
        
        Args:
            state_id: UUID of the state
            
        Returns:
            Updated OrchestratorState
        """
        state = self.get_state(state_id)
        if not state:
            raise ValueError(f"State {state_id} not found")
        
        state.status = OrchestratorStatus.RUNNING
        if state.started_at is None:
            state.started_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(state)
        
        return state

    def checkpoint(
        self,
        state_id: UUID,
        current_ticket: Optional[str] = None,
        completed_tickets: Optional[List[str]] = None,
        failed_tickets: Optional[List[Dict]] = None,
        ticket_queue: Optional[List[str]] = None,
    ) -> OrchestratorState:
        """Save a checkpoint of the current execution state.
        
        Args:
            state_id: UUID of the state
            current_ticket: Currently executing ticket key
            completed_tickets: List of completed ticket keys
            failed_tickets: List of failed tickets with error info
            ticket_queue: Updated ticket queue
            
        Returns:
            Updated OrchestratorState
        """
        state = self.get_state(state_id)
        if not state:
            raise ValueError(f"State {state_id} not found")
        
        if current_ticket is not None:
            state.current_ticket = current_ticket
        if completed_tickets is not None:
            state.completed_tickets = completed_tickets
        if failed_tickets is not None:
            state.failed_tickets = failed_tickets
        if ticket_queue is not None:
            state.ticket_queue = ticket_queue
        
        state.last_checkpoint_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(state)
        
        return state

    def mark_ticket_completed(
        self,
        state_id: UUID,
        ticket_key: str,
    ) -> OrchestratorState:
        """Mark a ticket as completed and remove from queue.
        
        Args:
            state_id: UUID of the state
            ticket_key: Ticket key that was completed
            
        Returns:
            Updated OrchestratorState
        """
        state = self.get_state(state_id)
        if not state:
            raise ValueError(f"State {state_id} not found")
        
        # Add to completed list
        completed = state.completed_tickets or []
        if ticket_key not in completed:
            completed.append(ticket_key)
        state.completed_tickets = completed
        
        # Remove from queue
        queue = state.ticket_queue or []
        if ticket_key in queue:
            queue.remove(ticket_key)
        state.ticket_queue = queue
        
        # Clear current ticket if it matches
        if state.current_ticket == ticket_key:
            state.current_ticket = None
        
        state.last_checkpoint_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(state)
        
        return state

    def mark_ticket_failed(
        self,
        state_id: UUID,
        ticket_key: str,
        error_message: str,
    ) -> OrchestratorState:
        """Mark a ticket as failed and record the error.
        
        Args:
            state_id: UUID of the state
            ticket_key: Ticket key that failed
            error_message: Error message or exception details
            
        Returns:
            Updated OrchestratorState
        """
        state = self.get_state(state_id)
        if not state:
            raise ValueError(f"State {state_id} not found")
        
        # Add to failed list
        failed = state.failed_tickets or []
        failed.append({
            "ticket_key": ticket_key,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat(),
        })
        state.failed_tickets = failed
        
        # Remove from queue
        queue = state.ticket_queue or []
        if ticket_key in queue:
            queue.remove(ticket_key)
        state.ticket_queue = queue
        
        # Clear current ticket if it matches
        if state.current_ticket == ticket_key:
            state.current_ticket = None
        
        state.last_checkpoint_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(state)
        
        return state

    def pause_execution(
        self,
        state_id: UUID,
        reason: Optional[str] = None,
    ) -> OrchestratorState:
        """Pause the orchestrator execution.
        
        Args:
            state_id: UUID of the state
            reason: Optional reason for pausing
            
        Returns:
            Updated OrchestratorState
        """
        state = self.get_state(state_id)
        if not state:
            raise ValueError(f"State {state_id} not found")
        
        state.status = OrchestratorStatus.PAUSED
        if reason:
            state.error_message = reason
        state.last_checkpoint_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(state)
        
        return state

    def complete_execution(
        self,
        state_id: UUID,
    ) -> OrchestratorState:
        """Mark execution as completed.
        
        Args:
            state_id: UUID of the state
            
        Returns:
            Updated OrchestratorState
        """
        state = self.get_state(state_id)
        if not state:
            raise ValueError(f"State {state_id} not found")
        
        state.status = OrchestratorStatus.COMPLETED
        state.completed_at = datetime.utcnow()
        state.current_ticket = None
        
        self.db.commit()
        self.db.refresh(state)
        
        return state

    def fail_execution(
        self,
        state_id: UUID,
        error_message: str,
    ) -> OrchestratorState:
        """Mark execution as failed.
        
        Args:
            state_id: UUID of the state
            error_message: Error message describing the failure
            
        Returns:
            Updated OrchestratorState
        """
        state = self.get_state(state_id)
        if not state:
            raise ValueError(f"State {state_id} not found")
        
        state.status = OrchestratorStatus.FAILED
        state.error_message = error_message
        state.last_checkpoint_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(state)
        
        return state

    def cancel_execution(
        self,
        state_id: UUID,
        reason: Optional[str] = None,
    ) -> OrchestratorState:
        """Cancel the orchestrator execution.
        
        Args:
            state_id: UUID of the state
            reason: Optional reason for cancellation
            
        Returns:
            Updated OrchestratorState
        """
        state = self.get_state(state_id)
        if not state:
            raise ValueError(f"State {state_id} not found")
        
        state.status = OrchestratorStatus.CANCELLED
        if reason:
            state.error_message = reason
        state.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(state)
        
        return state

    def get_progress(self, state_id: UUID) -> Dict:
        """Get execution progress statistics.
        
        Args:
            state_id: UUID of the state
            
        Returns:
            Dictionary with progress information
        """
        state = self.get_state(state_id)
        if not state:
            raise ValueError(f"State {state_id} not found")
        
        completed_count = len(state.completed_tickets or [])
        failed_count = len(state.failed_tickets or [])
        remaining_count = len(state.ticket_queue or [])
        total = state.total_tickets
        
        progress_pct = (completed_count / total * 100) if total > 0 else 0
        
        return {
            "state_id": str(state.id),
            "sprint_id": state.sprint_id,
            "sprint_name": state.sprint_name,
            "status": state.status.value,
            "total_tickets": total,
            "completed_tickets": completed_count,
            "failed_tickets": failed_count,
            "remaining_tickets": remaining_count,
            "current_ticket": state.current_ticket,
            "progress_percentage": round(progress_pct, 2),
            "started_at": state.started_at.isoformat() if state.started_at else None,
            "last_checkpoint": state.last_checkpoint_at.isoformat() if state.last_checkpoint_at else None,
        }
