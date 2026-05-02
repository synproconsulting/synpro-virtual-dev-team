"""
orchestrator_router.py
══════════════════════
FastAPI routes for orchestrator state management and resume capability.

Provides REST API endpoints to:
- Start sprint execution
- Resume interrupted sprints
- Get execution status and progress
- Pause/cancel running sprints
- List resumable sprints
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from database import get_db
from models import OrchestratorStatus
from agents.orchestrator import Orchestrator
from agents.orchestrator_state import StateManager


router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


# ── Request/Response Models ──────────────────────────────────────────────────────────


class StartSprintRequest(BaseModel):
    """Request to start sprint execution."""
    
    sprint_id: int = Field(..., description="Jira sprint ID", example=123)
    sprint_name: str = Field(..., description="Sprint name", example="Sprint 42")
    jira_project_key: str = Field(..., description="Jira project key", example="SDT1")


class StartSprintResponse(BaseModel):
    """Response after starting sprint execution."""
    
    state_id: str = Field(..., description="State ID for tracking execution")
    sprint_id: int
    sprint_name: str
    status: str
    message: str


class ResumeSprintRequest(BaseModel):
    """Request to resume sprint execution."""
    
    state_id: str = Field(..., description="State ID to resume")
    jira_project_key: str = Field(..., description="Jira project key", example="SDT1")


class ResumeSprintResponse(BaseModel):
    """Response after resuming sprint execution."""
    
    state_id: str
    sprint_id: int
    sprint_name: str
    status: str
    message: str


class ProgressResponse(BaseModel):
    """Sprint execution progress information."""
    
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


class PauseRequest(BaseModel):
    """Request to pause execution."""
    
    state_id: str
    reason: Optional[str] = None


class CancelRequest(BaseModel):
    """Request to cancel execution."""
    
    state_id: str
    reason: Optional[str] = None


class ActionResponse(BaseModel):
    """Generic action response."""
    
    success: bool
    message: str
    state_id: str
    status: str


# ── Routes ───────────────────────────────────────────────────────────────────────────


@router.post("/start", response_model=StartSprintResponse, status_code=status.HTTP_201_CREATED)
async def start_sprint(
    request: StartSprintRequest,
    db: Session = Depends(get_db),
) -> StartSprintResponse:
    """Start executing a sprint.
    
    This endpoint initiates orchestrator execution for a sprint.
    The execution happens asynchronously, and the state ID is returned
    for tracking progress.
    
    Args:
        request: Sprint start request
        db: Database session
        
    Returns:
        StartSprintResponse with state ID and initial status
        
    Raises:
        HTTPException: If execution fails to start
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
        
        # Get final state
        state = orchestrator.state_manager.get_state(state_id)
        
        return StartSprintResponse(
            state_id=str(state_id),
            sprint_id=request.sprint_id,
            sprint_name=request.sprint_name,
            status=state.status.value,
            message=f"Sprint execution started with state ID {state_id}",
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start sprint: {str(e)}",
        )


@router.post("/resume", response_model=ResumeSprintResponse)
async def resume_sprint(
    request: ResumeSprintRequest,
    db: Session = Depends(get_db),
) -> ResumeSprintResponse:
    """Resume a paused or failed sprint execution.
    
    This endpoint resumes execution from the last checkpoint.
    Only sprints with PAUSED or FAILED status can be resumed.
    
    Args:
        request: Resume request with state ID
        db: Database session
        
    Returns:
        ResumeSprintResponse with updated status
        
    Raises:
        HTTPException: If state not found or not resumable
    """
    try:
        state_id = UUID(request.state_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state ID format: {request.state_id}",
        )
    
    try:
        orchestrator = Orchestrator(
            jira_project_key=request.jira_project_key,
            db=db,
            verbose=True,
        )
        
        orchestrator.resume_sprint(state_id)
        
        # Get final state
        state = orchestrator.state_manager.get_state(state_id)
        
        return ResumeSprintResponse(
            state_id=str(state_id),
            sprint_id=state.sprint_id,
            sprint_name=state.sprint_name,
            status=state.status.value,
            message=f"Sprint execution resumed and completed with status {state.status.value}",
        )
        
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


@router.get("/progress/{state_id}", response_model=ProgressResponse)
async def get_progress(
    state_id: str,
    db: Session = Depends(get_db),
) -> ProgressResponse:
    """Get execution progress for a sprint.
    
    Args:
        state_id: UUID of the orchestrator state
        db: Database session
        
    Returns:
        ProgressResponse with current execution status
        
    Raises:
        HTTPException: If state not found
    """
    try:
        state_uuid = UUID(state_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state ID format: {state_id}",
        )
    
    try:
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


@router.get("/resumable", response_model=List[ResumableSprintInfo])
async def list_resumable_sprints(
    db: Session = Depends(get_db),
) -> List[ResumableSprintInfo]:
    """List all sprints that can be resumed.
    
    Returns sprints with PAUSED or FAILED status.
    
    Args:
        db: Database session
        
    Returns:
        List of resumable sprint information
    """
    try:
        # We need a dummy orchestrator to use list_resumable
        orchestrator = Orchestrator(
            jira_project_key="DUMMY",  # Not used for listing
            db=db,
            verbose=False,
        )
        
        resumable = orchestrator.list_resumable()
        
        return [ResumableSprintInfo(**sprint) for sprint in resumable]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list resumable sprints: {str(e)}",
        )


@router.post("/pause", response_model=ActionResponse)
async def pause_sprint(
    request: PauseRequest,
    db: Session = Depends(get_db),
) -> ActionResponse:
    """Pause a running sprint execution.
    
    Args:
        request: Pause request
        db: Database session
        
    Returns:
        ActionResponse with success status
        
    Raises:
        HTTPException: If state not found or operation fails
    """
    try:
        state_id = UUID(request.state_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state ID format: {request.state_id}",
        )
    
    try:
        state_manager = StateManager(db=db)
        state_manager.pause_execution(state_id, request.reason)
        
        state = state_manager.get_state(state_id)
        
        return ActionResponse(
            success=True,
            message=f"Sprint execution paused: {request.reason or 'User requested'}",
            state_id=str(state_id),
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
            detail=f"Failed to pause sprint: {str(e)}",
        )


@router.post("/cancel", response_model=ActionResponse)
async def cancel_sprint(
    request: CancelRequest,
    db: Session = Depends(get_db),
) -> ActionResponse:
    """Cancel a sprint execution.
    
    Args:
        request: Cancel request
        db: Database session
        
    Returns:
        ActionResponse with success status
        
    Raises:
        HTTPException: If state not found or operation fails
    """
    try:
        state_id = UUID(request.state_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state ID format: {request.state_id}",
        )
    
    try:
        state_manager = StateManager(db=db)
        state_manager.cancel_execution(state_id, request.reason)
        
        state = state_manager.get_state(state_id)
        
        return ActionResponse(
            success=True,
            message=f"Sprint execution cancelled: {request.reason or 'User requested'}",
            state_id=str(state_id),
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
            detail=f"Failed to cancel sprint: {str(e)}",
        )
