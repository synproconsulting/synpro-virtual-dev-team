"""
uat/backend/orchestrator_router.py
───────────────────────────────────
FastAPI router for orchestrator state persistence and sprint execution.

Provides REST endpoints for:
- Starting sprint executions
- Resuming from crashes/failures
- Checking execution status
- Pausing/cancelling executions
- Listing resumable states
"""

import os
import sys
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from agents.orchestrator import Orchestrator
from agents.orchestrator_state import StateManager
from database import get_db


# ── Request / Response models ─────────────────────────────────────────────────

class StartSprintRequest(BaseModel):
    """Request to start a sprint execution."""
    sprint_id: int = Field(..., description="Jira sprint ID", example=123)
    sprint_name: str = Field(..., description="Sprint name", example="Sprint 10")
    jira_project_key: str = Field(..., description="Jira project key", example="SDT1")


class StartSprintResponse(BaseModel):
    """Response after starting a sprint execution."""
    success: bool
    state_id: str
    sprint_id: int
    sprint_name: str
    message: str


class ResumeSprintRequest(BaseModel):
    """Request to resume a sprint execution."""
    state_id: str = Field(..., description="UUID of orchestrator state to resume")
    jira_project_key: str = Field(..., description="Jira project key", example="SDT1")


class ResumeSprintResponse(BaseModel):
    """Response after resuming a sprint execution."""
    success: bool
    state_id: str
    message: str


class ExecutionProgressResponse(BaseModel):
    """Progress information for a sprint execution."""
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


class ResumableStateResponse(BaseModel):
    """Information about a resumable orchestrator state."""
    state_id: str
    sprint_id: int
    sprint_name: str
    status: str
    total_tickets: int
    completed: int
    failed: int
    remaining: int
    last_updated: str


class PauseExecutionRequest(BaseModel):
    """Request to pause an execution."""
    state_id: str = Field(..., description="UUID of orchestrator state to pause")
    reason: Optional[str] = Field(None, description="Optional reason for pausing")


class CancelExecutionRequest(BaseModel):
    """Request to cancel an execution."""
    state_id: str = Field(..., description="UUID of orchestrator state to cancel")
    reason: Optional[str] = Field(None, description="Optional reason for cancellation")


class OperationResponse(BaseModel):
    """Generic operation response."""
    success: bool
    message: str
    state_id: str


# ── Router ────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


@router.post("/start", response_model=StartSprintResponse)
def start_sprint(
    request: StartSprintRequest,
    db: Session = Depends(get_db),
) -> StartSprintResponse:
    """Start executing a sprint from the beginning.
    
    Creates a new orchestrator state and begins executing tickets in the sprint
    according to their execution_order (customfield_10071).
    
    The execution runs asynchronously and can be monitored via the /progress endpoint.
    If execution is interrupted, it can be resumed via the /resume endpoint.
    """
    try:
        orchestrator = Orchestrator(
            jira_project_key=request.jira_project_key,
            db=db,
            verbose=True,
        )
        
        state_id = orchestrator.start_sprint(
            sprint_id=request.sprint_id,
            sprint_name=request.sprint_name,
        )
        
        return StartSprintResponse(
            success=True,
            state_id=str(state_id),
            sprint_id=request.sprint_id,
            sprint_name=request.sprint_name,
            message=f"Sprint execution started. State ID: {state_id}",
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start sprint execution: {str(e)}",
        )


@router.post("/resume", response_model=ResumeSprintResponse)
def resume_sprint(
    request: ResumeSprintRequest,
    db: Session = Depends(get_db),
) -> ResumeSprintResponse:
    """Resume a sprint execution from the last checkpoint.
    
    Can resume PAUSED or FAILED executions. The orchestrator will continue
    from where it left off, processing remaining tickets in the queue.
    """
    try:
        state_id = UUID(request.state_id)
        
        orchestrator = Orchestrator(
            jira_project_key=request.jira_project_key,
            db=db,
            verbose=True,
        )
        
        orchestrator.resume_sprint(state_id)
        
        return ResumeSprintResponse(
            success=True,
            state_id=request.state_id,
            message=f"Sprint execution resumed successfully",
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume sprint execution: {str(e)}",
        )


@router.get("/progress/{state_id}", response_model=ExecutionProgressResponse)
def get_progress(
    state_id: str,
    db: Session = Depends(get_db),
) -> ExecutionProgressResponse:
    """Get execution progress for a sprint.
    
    Returns detailed information about the current state of execution including:
    - Overall progress percentage
    - Number of completed, failed, and remaining tickets
    - Current ticket being processed
    - Timestamps for start and last checkpoint
    """
    try:
        state_uuid = UUID(state_id)
        state_manager = StateManager(db=db)
        
        progress = state_manager.get_progress(state_uuid)
        
        return ExecutionProgressResponse(**progress)
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state ID format")
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=f"State {state_id} not found")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get progress: {str(e)}",
        )


@router.get("/resumable", response_model=List[ResumableStateResponse])
def list_resumable(
    db: Session = Depends(get_db),
) -> List[ResumableStateResponse]:
    """List all sprints that can be resumed.
    
    Returns states with PAUSED or FAILED status that can be resumed
    to continue execution from the last checkpoint.
    """
    try:
        # Create a temporary orchestrator instance just to access list_resumable
        orchestrator = Orchestrator(
            jira_project_key="",  # Not needed for listing
            db=db,
            verbose=False,
        )
        
        resumable_states = orchestrator.list_resumable()
        
        return [ResumableStateResponse(**state) for state in resumable_states]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list resumable states: {str(e)}",
        )


@router.post("/pause", response_model=OperationResponse)
def pause_execution(
    request: PauseExecutionRequest,
    db: Session = Depends(get_db),
) -> OperationResponse:
    """Pause an ongoing sprint execution.
    
    The execution can be resumed later from the last checkpoint using the /resume endpoint.
    """
    try:
        state_id = UUID(request.state_id)
        state_manager = StateManager(db=db)
        
        state_manager.pause_execution(state_id, reason=request.reason)
        
        return OperationResponse(
            success=True,
            state_id=request.state_id,
            message="Execution paused successfully",
        )
        
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to pause execution: {str(e)}",
        )


@router.post("/cancel", response_model=OperationResponse)
def cancel_execution(
    request: CancelExecutionRequest,
    db: Session = Depends(get_db),
) -> OperationResponse:
    """Cancel an ongoing sprint execution.
    
    Unlike pause, a cancelled execution cannot be resumed. This permanently
    ends the execution for this state.
    """
    try:
        state_id = UUID(request.state_id)
        state_manager = StateManager(db=db)
        
        state_manager.cancel_execution(state_id, reason=request.reason)
        
        return OperationResponse(
            success=True,
            state_id=request.state_id,
            message="Execution cancelled successfully",
        )
        
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel execution: {str(e)}",
        )


@router.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint for orchestrator service."""
    return {
        "status": "ok",
        "service": "orchestrator",
        "version": "1.0.0",
    }
