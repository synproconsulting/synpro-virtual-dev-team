"""
uat/backend/orchestrator_router.py
═══════════════════════════════════
FastAPI router for orchestrator management endpoints.

Provides REST API endpoints for:
- Starting sprint execution
- Resuming interrupted execution
- Listing resumable sprints
- Checking execution progress
- Pausing/cancelling execution
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from database import get_db
from models import OrchestratorStatus
from agents.orchestrator import Orchestrator


router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


# ── Request/Response Models ───────────────────────────────────────────────────────────


class StartSprintRequest(BaseModel):
    """Request to start a sprint execution."""
    
    sprint_id: int = Field(..., description="Jira sprint ID")
    sprint_name: str = Field(..., description="Sprint name")
    jira_project_key: str = Field(..., description="Jira project key (e.g., 'SDT1')")


class StartSprintResponse(BaseModel):
    """Response from starting a sprint execution."""
    
    state_id: str = Field(..., description="UUID of the orchestrator state")
    sprint_id: int
    sprint_name: str
    status: str
    message: str


class ResumeSprintRequest(BaseModel):
    """Request to resume a sprint execution."""
    
    state_id: str = Field(..., description="UUID of the orchestrator state to resume")
    jira_project_key: str = Field(..., description="Jira project key")


class ResumeSprintResponse(BaseModel):
    """Response from resuming a sprint execution."""
    
    state_id: str
    sprint_id: int
    sprint_name: str
    status: str
    message: str


class PauseSprintRequest(BaseModel):
    """Request to pause a sprint execution."""
    
    state_id: str = Field(..., description="UUID of the orchestrator state")
    jira_project_key: str = Field(..., description="Jira project key")
    reason: Optional[str] = Field(None, description="Reason for pausing")


class PauseSprintResponse(BaseModel):
    """Response from pausing a sprint execution."""
    
    state_id: str
    status: str
    message: str


class CancelSprintRequest(BaseModel):
    """Request to cancel a sprint execution."""
    
    state_id: str = Field(..., description="UUID of the orchestrator state")
    jira_project_key: str = Field(..., description="Jira project key")
    reason: Optional[str] = Field(None, description="Reason for cancellation")


class CancelSprintResponse(BaseModel):
    """Response from cancelling a sprint execution."""
    
    state_id: str
    status: str
    message: str


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


class ResumableSprintInfo(BaseModel):
    """Information about a resumable sprint."""
    
    state_id: str
    sprint_id: int
    sprint_name: str
    status: str
    total_tickets: int
    completed: int
    failed: int
    remaining: int
    last_updated: str


class ListResumableResponse(BaseModel):
    """Response with list of resumable sprints."""
    
    sprints: List[ResumableSprintInfo]
    count: int


# ── Endpoints ─────────────────────────────────────────────────────────────────────────


@router.post("/start", response_model=StartSprintResponse, status_code=status.HTTP_202_ACCEPTED)
def start_sprint(
    request: StartSprintRequest,
    db: Session = Depends(get_db),
) -> StartSprintResponse:
    """Start executing a sprint from the beginning.
    
    This endpoint initiates orchestrator execution for a sprint. The execution
    runs asynchronously, and the state_id can be used to track progress.
    
    Args:
        request: Sprint start request with sprint details
        db: Database session
        
    Returns:
        StartSprintResponse with state_id and execution details
        
    Raises:
        HTTPException: If sprint start fails
    """
    try:
        with Orchestrator(request.jira_project_key, db=db, verbose=True) as orch:
            state_id = orch.start_sprint(
                sprint_id=request.sprint_id,
                sprint_name=request.sprint_name,
            )
            
            return StartSprintResponse(
                state_id=str(state_id),
                sprint_id=request.sprint_id,
                sprint_name=request.sprint_name,
                status=OrchestratorStatus.RUNNING.value,
                message=f"Sprint execution started successfully",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start sprint: {str(e)}",
        )


@router.post("/resume", response_model=ResumeSprintResponse, status_code=status.HTTP_202_ACCEPTED)
def resume_sprint(
    request: ResumeSprintRequest,
    db: Session = Depends(get_db),
) -> ResumeSprintResponse:
    """Resume executing a sprint from the last checkpoint.
    
    This endpoint resumes orchestrator execution for a paused or failed sprint.
    Only sprints with PAUSED or FAILED status can be resumed.
    
    Args:
        request: Resume request with state_id
        db: Database session
        
    Returns:
        ResumeSprintResponse with execution details
        
    Raises:
        HTTPException: If state not found or cannot be resumed
    """
    try:
        state_id = UUID(request.state_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state_id format",
        )
    
    try:
        with Orchestrator(request.jira_project_key, db=db, verbose=True) as orch:
            # Get state info before resuming
            state = orch.state_manager.get_state(state_id)
            if not state:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"State {request.state_id} not found",
                )
            
            # Resume execution
            orch.resume_sprint(state_id)
            
            # Get updated state
            updated_state = orch.state_manager.get_state(state_id)
            
            return ResumeSprintResponse(
                state_id=str(state_id),
                sprint_id=updated_state.sprint_id,
                sprint_name=updated_state.sprint_name,
                status=updated_state.status.value,
                message=f"Sprint execution resumed successfully",
            )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume sprint: {str(e)}",
        )


@router.post("/pause", response_model=PauseSprintResponse)
def pause_sprint(
    request: PauseSprintRequest,
    db: Session = Depends(get_db),
) -> PauseSprintResponse:
    """Pause the execution of a sprint.
    
    This endpoint pauses orchestrator execution. The sprint can be resumed
    later from the last checkpoint.
    
    Args:
        request: Pause request with state_id and optional reason
        db: Database session
        
    Returns:
        PauseSprintResponse with pause confirmation
        
    Raises:
        HTTPException: If state not found or cannot be paused
    """
    try:
        state_id = UUID(request.state_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state_id format",
        )
    
    try:
        with Orchestrator(request.jira_project_key, db=db, verbose=True) as orch:
            orch.pause(state_id, reason=request.reason)
            
            return PauseSprintResponse(
                state_id=str(state_id),
                status=OrchestratorStatus.PAUSED.value,
                message="Sprint execution paused successfully",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause sprint: {str(e)}",
        )


@router.post("/cancel", response_model=CancelSprintResponse)
def cancel_sprint(
    request: CancelSprintRequest,
    db: Session = Depends(get_db),
) -> CancelSprintResponse:
    """Cancel the execution of a sprint.
    
    This endpoint cancels orchestrator execution. Unlike pause, a cancelled
    sprint cannot be resumed.
    
    Args:
        request: Cancel request with state_id and optional reason
        db: Database session
        
    Returns:
        CancelSprintResponse with cancellation confirmation
        
    Raises:
        HTTPException: If state not found or cannot be cancelled
    """
    try:
        state_id = UUID(request.state_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state_id format",
        )
    
    try:
        with Orchestrator(request.jira_project_key, db=db, verbose=True) as orch:
            orch.cancel(state_id, reason=request.reason)
            
            return CancelSprintResponse(
                state_id=str(state_id),
                status=OrchestratorStatus.CANCELLED.value,
                message="Sprint execution cancelled successfully",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel sprint: {str(e)}",
        )


@router.get("/progress/{state_id}", response_model=ProgressResponse)
def get_progress(
    state_id: str,
    jira_project_key: str,
    db: Session = Depends(get_db),
) -> ProgressResponse:
    """Get execution progress for a sprint.
    
    This endpoint retrieves current execution status and progress statistics
    for a sprint orchestration run.
    
    Args:
        state_id: UUID of the orchestrator state
        jira_project_key: Jira project key
        db: Database session
        
    Returns:
        ProgressResponse with detailed progress information
        
    Raises:
        HTTPException: If state not found
    """
    try:
        uuid_state_id = UUID(state_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state_id format",
        )
    
    try:
        with Orchestrator(jira_project_key, db=db, verbose=False) as orch:
            progress = orch.get_progress(uuid_state_id)
            
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


@router.get("/resumable", response_model=ListResumableResponse)
def list_resumable(
    jira_project_key: str,
    db: Session = Depends(get_db),
) -> ListResumableResponse:
    """List all sprints that can be resumed.
    
    This endpoint returns all orchestrator states that are in PAUSED or
    FAILED status and can be resumed.
    
    Args:
        jira_project_key: Jira project key
        db: Database session
        
    Returns:
        ListResumableResponse with list of resumable sprints
    """
    try:
        with Orchestrator(jira_project_key, db=db, verbose=False) as orch:
            resumable = orch.list_resumable()
            
            sprints = [ResumableSprintInfo(**sprint) for sprint in resumable]
            
            return ListResumableResponse(
                sprints=sprints,
                count=len(sprints),
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list resumable sprints: {str(e)}",
        )
