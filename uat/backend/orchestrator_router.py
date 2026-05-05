"""
orchestrator_router.py
═════════════════════
API endpoints for Orchestrator state management and execution control.

Provides REST API for:
- Starting sprint execution
- Resuming from saved state
- Pausing/canceling execution
- Querying execution status and progress
- Listing resumable states
"""

from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user as require_auth

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from agents.orchestrator import Orchestrator
from agents.orchestrator_state import StateManager
from models import OrchestratorStatus


router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


# ── Request/Response Models ────────────────────────────────────────────────────────────


class StartSprintRequest(BaseModel):
    """Request to start a sprint execution."""

    sprint_id: int = Field(..., description="Jira sprint ID")
    sprint_name: str = Field(..., description="Sprint name")
    jira_project_key: str = Field(..., description="Jira project key (e.g., 'SDT1')")


class StartSprintResponse(BaseModel):
    """Response from starting a sprint."""

    state_id: str = Field(..., description="UUID of the created state")
    sprint_id: int
    sprint_name: str
    status: str
    message: str


class ResumeSprintRequest(BaseModel):
    """Request to resume a sprint execution."""

    state_id: str = Field(..., description="UUID of the state to resume")
    jira_project_key: str = Field(..., description="Jira project key")


class StateControlRequest(BaseModel):
    """Request to control state (pause, cancel)."""

    state_id: str = Field(..., description="UUID of the state")
    reason: Optional[str] = Field(None, description="Optional reason for the action")


class ProgressResponse(BaseModel):
    """Execution progress information."""

    state_id: str
    sprint_id: int
    sprint_name: str
    status: str
    total_tickets: int
    completed_tickets: int
    failed_tickets: int
    remaining_tickets: int
    current_ticket: Optional[str]
    progress_percentage: float
    started_at: Optional[str]
    last_checkpoint: Optional[str]


class ResumableStateInfo(BaseModel):
    """Information about a resumable state."""

    state_id: str
    sprint_id: int
    sprint_name: str
    status: str
    total_tickets: int
    completed: int
    failed: int
    remaining: int
    last_updated: str


class StateListResponse(BaseModel):
    """List of resumable states."""

    states: List[ResumableStateInfo]
    count: int


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str
    state_id: str
    status: str


# ── Endpoints ──────────────────────────────────────────────────────────────────────────


@router.post("/start", response_model=StartSprintResponse, status_code=status.HTTP_201_CREATED)
async def start_sprint(
    request: StartSprintRequest,
    db: Session = Depends(get_db),
    user: Dict = Depends(require_auth),
) -> StartSprintResponse:
    """Start executing a sprint.
    
    Creates a new orchestrator state and begins executing tickets
    in the sprint sequentially based on their execution_order.
    
    The execution runs asynchronously in the background. Use the
    returned state_id to query progress.
    
    Args:
        request: Sprint start request with sprint_id, name, and project key
        db: Database session
        user: Authenticated user
        
    Returns:
        StartSprintResponse with state_id and initial status
    """
    try:
        orchestrator = Orchestrator(
            jira_project_key=request.jira_project_key,
            db=db,
            verbose=True,
        )
        
        # Note: In production, this should be run in a background task
        # For now, we'll create the state and return immediately
        state_manager = StateManager(db=db)
        
        # Fetch tickets (placeholder - will integrate with Jira API)
        tickets = orchestrator.get_sprint_tickets(request.sprint_id)
        ticket_queue = [t["key"] for t in tickets]
        
        # Create state
        state = state_manager.create_state(
            sprint_id=request.sprint_id,
            sprint_name=request.sprint_name,
            jira_project_key=request.jira_project_key,
            ticket_queue=ticket_queue,
        )
        
        return StartSprintResponse(
            state_id=str(state.id),
            sprint_id=state.sprint_id,
            sprint_name=state.sprint_name,
            status=state.status.value,
            message=f"Sprint execution initiated. State ID: {state.id}",
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start sprint execution: {str(e)}",
        )


@router.post("/resume", response_model=MessageResponse)
async def resume_sprint(
    request: ResumeSprintRequest,
    db: Session = Depends(get_db),
    user: Dict = Depends(require_auth),
) -> MessageResponse:
    """Resume a paused or failed sprint execution.
    
    Resumes execution from the last checkpoint. Only states with
    PAUSED or FAILED status can be resumed.
    
    Args:
        request: Resume request with state_id
        db: Database session
        user: Authenticated user
        
    Returns:
        MessageResponse with confirmation
        
    Raises:
        HTTPException: If state not found or not resumable
    """
    try:
        state_id = UUID(request.state_id)
        
        state_manager = StateManager(db=db)
        state = state_manager.get_state(state_id)
        
        if not state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"State {request.state_id} not found",
            )
        
        if state.status not in [OrchestratorStatus.PAUSED, OrchestratorStatus.FAILED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot resume state with status {state.status.value}. "
                       f"Only PAUSED or FAILED states can be resumed.",
            )
        
        # Note: In production, this should be run in a background task
        orchestrator = Orchestrator(
            jira_project_key=request.jira_project_key,
            db=db,
            verbose=True,
        )
        
        # For now, just mark as running
        state_manager.start_execution(state_id)
        
        return MessageResponse(
            message=f"Sprint execution resumed. {len(state.ticket_queue or [])} tickets remaining.",
            state_id=request.state_id,
            status="running",
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume sprint execution: {str(e)}",
        )


@router.post("/pause", response_model=MessageResponse)
async def pause_sprint(
    request: StateControlRequest,
    db: Session = Depends(get_db),
    user: Dict = Depends(require_auth),
) -> MessageResponse:
    """Pause a running sprint execution.
    
    Pauses the execution at the next checkpoint. The current ticket
    will complete before pausing.
    
    Args:
        request: Control request with state_id and optional reason
        db: Database session
        user: Authenticated user
        
    Returns:
        MessageResponse with confirmation
    """
    try:
        state_id = UUID(request.state_id)
        
        state_manager = StateManager(db=db)
        state = state_manager.pause_execution(state_id, request.reason)
        
        return MessageResponse(
            message=f"Sprint execution paused. {len(state.ticket_queue or [])} tickets remaining.",
            state_id=request.state_id,
            status=state.status.value,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause sprint execution: {str(e)}",
        )


@router.post("/cancel", response_model=MessageResponse)
async def cancel_sprint(
    request: StateControlRequest,
    db: Session = Depends(get_db),
    user: Dict = Depends(require_auth),
) -> MessageResponse:
    """Cancel a sprint execution.
    
    Permanently cancels the execution. Cancelled states cannot be resumed.
    
    Args:
        request: Control request with state_id and optional reason
        db: Database session
        user: Authenticated user
        
    Returns:
        MessageResponse with confirmation
    """
    try:
        state_id = UUID(request.state_id)
        
        state_manager = StateManager(db=db)
        state = state_manager.cancel_execution(state_id, request.reason)
        
        return MessageResponse(
            message="Sprint execution cancelled.",
            state_id=request.state_id,
            status=state.status.value,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel sprint execution: {str(e)}",
        )


@router.get("/progress/{state_id}", response_model=ProgressResponse)
async def get_progress(
    state_id: str,
    db: Session = Depends(get_db),
    user: Dict = Depends(require_auth),
) -> ProgressResponse:
    """Get execution progress for a state.
    
    Returns detailed progress information including completed, failed,
    and remaining tickets.
    
    Args:
        state_id: UUID of the state
        db: Database session
        user: Authenticated user
        
    Returns:
        ProgressResponse with progress details
    """
    try:
        state_uuid = UUID(state_id)
        
        state_manager = StateManager(db=db)
        progress = state_manager.get_progress(state_uuid)
        
        return ProgressResponse(**progress)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress: {str(e)}",
        )


@router.get("/resumable", response_model=StateListResponse)
async def list_resumable(
    db: Session = Depends(get_db),
    user: Dict = Depends(require_auth),
) -> StateListResponse:
    """List all resumable sprint executions.
    
    Returns all states with PAUSED or FAILED status that can be resumed.
    
    Args:
        db: Database session
        user: Authenticated user
        
    Returns:
        StateListResponse with list of resumable states
    """
    try:
        state_manager = StateManager(db=db)
        resumable_states = state_manager.get_resumable_states()
        
        states = [
            ResumableStateInfo(
                state_id=str(state.id),
                sprint_id=state.sprint_id,
                sprint_name=state.sprint_name,
                status=state.status.value,
                total_tickets=state.total_tickets,
                completed=len(state.completed_tickets or []),
                failed=len(state.failed_tickets or []),
                remaining=len(state.ticket_queue or []),
                last_updated=state.updated_at.isoformat(),
            )
            for state in resumable_states
        ]
        
        return StateListResponse(
            states=states,
            count=len(states),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list resumable states: {str(e)}",
        )


@router.get("/state/{state_id}")
async def get_state(
    state_id: str,
    db: Session = Depends(get_db),
    user: Dict = Depends(require_auth),
) -> Dict:
    """Get full state details including ticket lists.
    
    Returns complete state information including ticket_queue,
    completed_tickets, and failed_tickets.
    
    Args:
        state_id: UUID of the state
        db: Database session
        user: Authenticated user
        
    Returns:
        Dictionary with complete state information
    """
    try:
        state_uuid = UUID(state_id)
        
        state_manager = StateManager(db=db)
        state = state_manager.get_state(state_uuid)
        
        if not state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"State {state_id} not found",
            )
        
        return {
            "id": str(state.id),
            "sprint_id": state.sprint_id,
            "sprint_name": state.sprint_name,
            "jira_project_key": state.jira_project_key,
            "status": state.status.value,
            "ticket_queue": state.ticket_queue or [],
            "completed_tickets": state.completed_tickets or [],
            "failed_tickets": state.failed_tickets or [],
            "current_ticket": state.current_ticket,
            "total_tickets": state.total_tickets,
            "started_at": state.started_at.isoformat() if state.started_at else None,
            "completed_at": state.completed_at.isoformat() if state.completed_at else None,
            "last_checkpoint_at": state.last_checkpoint_at.isoformat() if state.last_checkpoint_at else None,
            "error_message": state.error_message,
            "created_at": state.created_at.isoformat(),
            "updated_at": state.updated_at.isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get state: {str(e)}",
        )