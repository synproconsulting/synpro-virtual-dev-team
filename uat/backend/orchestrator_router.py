"""
orchestrator_router.py
══════════════════════
API endpoints for Orchestrator state management and execution control.

Provides REST API for:
- Starting sprint execution
- Resuming from saved state
- Pausing/canceling execution
- Querying execution status and progress
- Listing resumable states

Self-contained — no imports from agents/ directory.
"""

import base64
import os
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import get_current_user as require_auth
from database import get_db
from models import OrchestratorState, OrchestratorStatus


# ── Jira config ───────────────────────────────────────────────────────────────

JIRA_BASE_URL  = os.getenv("JIRA_BASE_URL", "")
JIRA_EMAIL     = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")


def _jira_headers() -> dict:
    creds   = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    encoded = base64.b64encode(creds.encode()).decode()
    return {
        "Authorization": f"Basic {encoded}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


async def _fetch_sprint_tickets(sprint_id: int, jira_project_key: str) -> List[Dict]:
    """Return To Do stories for a sprint from Jira, ordered by execution order."""
    jql = (
        f"project = {jira_project_key} "
        f"AND sprint = {sprint_id} "
        f"AND issuetype not in (Epic, Sub-task, Subtask) "
        f"AND status = 'To Do' "
        f"ORDER BY cf[10071] ASC"
    )
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    async with httpx.AsyncClient() as client:
        r = await client.get(
            url,
            headers=_jira_headers(),
            params={"jql": jql, "maxResults": 100, "fields": "summary,customfield_10071"},
            timeout=15.0,
        )
        r.raise_for_status()
    return [
        {"key": issue["key"], "summary": issue["fields"].get("summary", "")}
        for issue in r.json().get("issues", [])
    ]


# ── State management helpers (inlined from agents/orchestrator_state.py) ─────

def _get_state(db: Session, state_id: UUID) -> Optional[OrchestratorState]:
    return db.query(OrchestratorState).filter(OrchestratorState.id == state_id).first()


def _create_state(
    db: Session,
    sprint_id: int,
    sprint_name: str,
    jira_project_key: str,
    ticket_queue: List[str],
) -> OrchestratorState:
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
    db.add(state)
    db.commit()
    db.refresh(state)
    return state


def _start_execution(db: Session, state_id: UUID) -> OrchestratorState:
    state = _get_state(db, state_id)
    if not state:
        raise ValueError(f"State {state_id} not found")
    state.status = OrchestratorStatus.RUNNING
    if state.started_at is None:
        state.started_at = datetime.utcnow()
    db.commit()
    db.refresh(state)
    return state


def _pause_execution(
    db: Session, state_id: UUID, reason: Optional[str] = None
) -> OrchestratorState:
    state = _get_state(db, state_id)
    if not state:
        raise ValueError(f"State {state_id} not found")
    state.status = OrchestratorStatus.PAUSED
    if reason:
        state.error_message = reason
    state.last_checkpoint_at = datetime.utcnow()
    db.commit()
    db.refresh(state)
    return state


def _cancel_execution(
    db: Session, state_id: UUID, reason: Optional[str] = None
) -> OrchestratorState:
    state = _get_state(db, state_id)
    if not state:
        raise ValueError(f"State {state_id} not found")
    state.status = OrchestratorStatus.CANCELLED
    if reason:
        state.error_message = reason
    state.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(state)
    return state


def _get_progress(db: Session, state_id: UUID) -> Dict:
    state = _get_state(db, state_id)
    if not state:
        raise ValueError(f"State {state_id} not found")
    completed_count = len(state.completed_tickets or [])
    failed_count    = len(state.failed_tickets or [])
    remaining_count = len(state.ticket_queue or [])
    total           = state.total_tickets
    progress_pct    = (completed_count / total * 100) if total > 0 else 0.0
    return {
        "state_id":           str(state.id),
        "sprint_id":          state.sprint_id,
        "sprint_name":        state.sprint_name,
        "status":             state.status.value,
        "total_tickets":      total,
        "completed_tickets":  completed_count,
        "failed_tickets":     failed_count,
        "remaining_tickets":  remaining_count,
        "current_ticket":     state.current_ticket,
        "progress_percentage": round(progress_pct, 2),
        "started_at":         state.started_at.isoformat() if state.started_at else None,
        "last_checkpoint":    state.last_checkpoint_at.isoformat() if state.last_checkpoint_at else None,
    }


def _get_resumable_states(db: Session) -> List[OrchestratorState]:
    return (
        db.query(OrchestratorState)
        .filter(OrchestratorState.status.in_([OrchestratorStatus.PAUSED, OrchestratorStatus.FAILED]))
        .order_by(OrchestratorState.updated_at.desc())
        .all()
    )


# ── Request / Response models ─────────────────────────────────────────────────

class StartSprintRequest(BaseModel):
    sprint_id:        int = Field(..., description="Jira sprint ID")
    sprint_name:      str = Field(..., description="Sprint name")
    jira_project_key: str = Field(..., description="Jira project key (e.g., 'SDT1')")


class StartSprintResponse(BaseModel):
    state_id:    str = Field(..., description="UUID of the created state")
    sprint_id:   int
    sprint_name: str
    status:      str
    message:     str


class ResumeSprintRequest(BaseModel):
    state_id:         str = Field(..., description="UUID of the state to resume")
    jira_project_key: str = Field(..., description="Jira project key")


class StateControlRequest(BaseModel):
    state_id: str           = Field(..., description="UUID of the state")
    reason:   Optional[str] = Field(None, description="Optional reason for the action")


class ProgressResponse(BaseModel):
    state_id:             str
    sprint_id:            int
    sprint_name:          str
    status:               str
    total_tickets:        int
    completed_tickets:    int
    failed_tickets:       int
    remaining_tickets:    int
    current_ticket:       Optional[str]
    progress_percentage:  float
    started_at:           Optional[str]
    last_checkpoint:      Optional[str]


class ResumableStateInfo(BaseModel):
    state_id:     str
    sprint_id:    int
    sprint_name:  str
    status:       str
    total_tickets: int
    completed:    int
    failed:       int
    remaining:    int
    last_updated: str


class StateListResponse(BaseModel):
    states: List[ResumableStateInfo]
    count:  int


class MessageResponse(BaseModel):
    message:  str
    state_id: str
    status:   str


# ── Router ────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


@router.post("/start", response_model=StartSprintResponse, status_code=status.HTTP_201_CREATED)
async def start_sprint(
    request: StartSprintRequest,
    db:      Session = Depends(get_db),
    user:    Dict    = Depends(require_auth),
) -> StartSprintResponse:
    """Start executing a sprint.

    Fetches To Do tickets from Jira, creates an orchestrator state record,
    and returns immediately. Background execution is not yet wired — use
    the returned state_id to track and control progress via the other endpoints.
    """
    try:
        tickets      = await _fetch_sprint_tickets(request.sprint_id, request.jira_project_key)
        ticket_queue = [t["key"] for t in tickets]
        state        = _create_state(
            db,
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
            message=f"Sprint execution initiated. {len(ticket_queue)} tickets queued. State ID: {state.id}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start sprint execution: {e}",
        )


@router.post("/resume", response_model=MessageResponse)
async def resume_sprint(
    request: ResumeSprintRequest,
    db:      Session = Depends(get_db),
    user:    Dict    = Depends(require_auth),
) -> MessageResponse:
    """Resume a paused or failed sprint execution."""
    try:
        state_id = UUID(request.state_id)
        state    = _get_state(db, state_id)

        if not state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"State {request.state_id} not found",
            )
        if state.status not in [OrchestratorStatus.PAUSED, OrchestratorStatus.FAILED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot resume state with status {state.status.value}. "
                    "Only PAUSED or FAILED states can be resumed."
                ),
            )

        _start_execution(db, state_id)

        return MessageResponse(
            message=f"Sprint execution resumed. {len(state.ticket_queue or [])} tickets remaining.",
            state_id=request.state_id,
            status="running",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume sprint execution: {e}",
        )


@router.post("/pause", response_model=MessageResponse)
async def pause_sprint(
    request: StateControlRequest,
    db:      Session = Depends(get_db),
    user:    Dict    = Depends(require_auth),
) -> MessageResponse:
    """Pause a running sprint execution."""
    try:
        state = _pause_execution(db, UUID(request.state_id), request.reason)
        return MessageResponse(
            message=f"Sprint execution paused. {len(state.ticket_queue or [])} tickets remaining.",
            state_id=request.state_id,
            status=state.status.value,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause sprint execution: {e}",
        )


@router.post("/cancel", response_model=MessageResponse)
async def cancel_sprint(
    request: StateControlRequest,
    db:      Session = Depends(get_db),
    user:    Dict    = Depends(require_auth),
) -> MessageResponse:
    """Cancel a sprint execution. Cancelled states cannot be resumed."""
    try:
        state = _cancel_execution(db, UUID(request.state_id), request.reason)
        return MessageResponse(
            message="Sprint execution cancelled.",
            state_id=request.state_id,
            status=state.status.value,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel sprint execution: {e}",
        )


@router.get("/progress/{state_id}", response_model=ProgressResponse)
async def get_progress(
    state_id: str,
    db:       Session = Depends(get_db),
    user:     Dict    = Depends(require_auth),
) -> ProgressResponse:
    """Get execution progress for a state."""
    try:
        return ProgressResponse(**_get_progress(db, UUID(state_id)))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress: {e}",
        )


@router.get("/resumable", response_model=StateListResponse)
async def list_resumable(
    db:   Session = Depends(get_db),
    user: Dict    = Depends(require_auth),
) -> StateListResponse:
    """List all resumable sprint executions (PAUSED or FAILED)."""
    try:
        states = [
            ResumableStateInfo(
                state_id=str(s.id),
                sprint_id=s.sprint_id,
                sprint_name=s.sprint_name,
                status=s.status.value,
                total_tickets=s.total_tickets,
                completed=len(s.completed_tickets or []),
                failed=len(s.failed_tickets or []),
                remaining=len(s.ticket_queue or []),
                last_updated=s.updated_at.isoformat(),
            )
            for s in _get_resumable_states(db)
        ]
        return StateListResponse(states=states, count=len(states))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list resumable states: {e}",
        )


@router.get("/state/{state_id}")
async def get_state(
    state_id: str,
    db:       Session = Depends(get_db),
    user:     Dict    = Depends(require_auth),
) -> Dict:
    """Get full state details including ticket lists."""
    try:
        state = _get_state(db, UUID(state_id))
        if not state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"State {state_id} not found",
            )
        return {
            "id":                str(state.id),
            "sprint_id":         state.sprint_id,
            "sprint_name":       state.sprint_name,
            "jira_project_key":  state.jira_project_key,
            "status":            state.status.value,
            "ticket_queue":      state.ticket_queue or [],
            "completed_tickets": state.completed_tickets or [],
            "failed_tickets":    state.failed_tickets or [],
            "current_ticket":    state.current_ticket,
            "total_tickets":     state.total_tickets,
            "started_at":        state.started_at.isoformat() if state.started_at else None,
            "completed_at":      state.completed_at.isoformat() if state.completed_at else None,
            "last_checkpoint_at": state.last_checkpoint_at.isoformat() if state.last_checkpoint_at else None,
            "error_message":     state.error_message,
            "created_at":        state.created_at.isoformat(),
            "updated_at":        state.updated_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get state: {e}",
        )