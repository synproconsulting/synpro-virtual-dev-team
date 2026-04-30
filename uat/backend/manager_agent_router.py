"""
Manager Agent router - exposes Manager Agent Jira transition functionality via API.
"""

import os
import sys
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add agents directory to path so we can import manager_agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../..", "agents"))

from manager_agent import (
    create_manager_agent,
    TransitionStatus,
    TransitionResult,
)


# ── Request Models ────────────────────────────────────────────────────────────────────


class TransitionRequest(BaseModel):
    """Request to transition an issue."""
    issue_key: str
    target_status: Optional[str] = None
    transition_id: Optional[str] = None
    assignee: Optional[str] = None
    comment: Optional[str] = None


class BulkTransitionRequest(BaseModel):
    """Request to transition multiple issues."""
    transitions: List[TransitionRequest]


class TransitionResponse(BaseModel):
    """Response from a transition operation."""
    success: bool
    status: str
    issue_key: str
    transition_id: Optional[str] = None
    transition_name: Optional[str] = None
    attempts: int
    total_time: float
    error_message: Optional[str] = None
    final_status: Optional[str] = None


# ── Helper Functions ──────────────────────────────────────────────────────────────────


def _result_to_response(result: TransitionResult) -> TransitionResponse:
    """Convert TransitionResult to TransitionResponse."""
    return TransitionResponse(
        success=result.status == TransitionStatus.SUCCESS,
        status=result.status.value,
        issue_key=result.issue_key,
        transition_id=result.transition_id,
        transition_name=result.transition_name,
        attempts=result.attempts,
        total_time=result.total_time,
        error_message=result.error_message,
        final_status=result.final_status,
    )


# ── Router ────────────────────────────────────────────────────────────────────────────


router = APIRouter(prefix="/api/manager-agent", tags=["manager-agent"])


@router.post("/transition")
async def transition_issue(request: TransitionRequest):
    """
    Transition a Jira issue with exponential backoff retry logic.
    
    Either target_status or transition_id must be provided.
    """
    try:
        agent = create_manager_agent()
        
        if request.transition_id:
            # Use transition ID directly
            result = await agent.client.transition_issue(
                issue_key=request.issue_key,
                transition_id=request.transition_id,
                fields={"assignee": {"name": request.assignee}} if request.assignee else None,
                comment=request.comment,
            )
        elif request.target_status:
            # Use target status name
            result = await agent.client.transition_issue_by_name(
                issue_key=request.issue_key,
                target_status=request.target_status,
                fields={"assignee": {"name": request.assignee}} if request.assignee else None,
                comment=request.comment,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either target_status or transition_id must be provided"
            )
        
        return _result_to_response(result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-transition")
async def bulk_transition(request: BulkTransitionRequest):
    """
    Transition multiple Jira issues with exponential backoff retry logic.
    """
    try:
        agent = create_manager_agent()
        
        # Convert request models to dictionaries
        transitions = []
        for trans in request.transitions:
            trans_dict = {"issue_key": trans.issue_key}
            if trans.target_status:
                trans_dict["target_status"] = trans.target_status
            if trans.transition_id:
                trans_dict["transition_id"] = trans.transition_id
            if trans.comment:
                trans_dict["comment"] = trans.comment
            if trans.assignee:
                trans_dict["fields"] = {"assignee": {"name": trans.assignee}}
            transitions.append(trans_dict)
        
        results = await agent.client.bulk_transition(transitions)
        
        return {
            "results": [_result_to_response(r) for r in results],
            "total": len(results),
            "successful": sum(1 for r in results if r.status == TransitionStatus.SUCCESS),
            "failed": sum(1 for r in results if r.status != TransitionStatus.SUCCESS),
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start-work/{issue_key}")
async def start_work(issue_key: str, assignee: Optional[str] = None, comment: Optional[str] = None):
    """
    Transition an issue to 'In Progress' status.
    """
    try:
        agent = create_manager_agent()
        result = await agent.start_work(issue_key, assignee=assignee, comment=comment)
        return _result_to_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete-work/{issue_key}")
async def complete_work(issue_key: str, comment: Optional[str] = None):
    """
    Transition an issue to 'Done' status.
    """
    try:
        agent = create_manager_agent()
        result = await agent.complete_work(issue_key, comment=comment)
        return _result_to_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code-review/{issue_key}")
async def move_to_code_review(issue_key: str, comment: Optional[str] = None):
    """
    Transition an issue to 'Code Review' status.
    """
    try:
        agent = create_manager_agent()
        result = await agent.move_to_code_review(issue_key, comment=comment)
        return _result_to_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/testing/{issue_key}")
async def move_to_testing(issue_key: str, comment: Optional[str] = None):
    """
    Transition an issue to 'Testing' or 'QA' status.
    """
    try:
        agent = create_manager_agent()
        result = await agent.move_to_testing(issue_key, comment=comment)
        return _result_to_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{issue_key}")
async def get_issue_status(issue_key: str):
    """
    Get the current status of a Jira issue.
    """
    try:
        agent = create_manager_agent()
        status = await agent.get_issue_status(issue_key)
        
        if status is None:
            raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found or error retrieving status")
        
        return {"issue_key": issue_key, "status": status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
