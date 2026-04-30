"""
uat/backend/manager_agent_router.py
────────────────────────────────────
FastAPI router for Jira issue transitions with exponential backoff retry.
Self-contained — no imports from agents/ directory.
"""

import os
import time
import base64
import asyncio
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Any, Dict

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


# ── Config ────────────────────────────────────────────────────────────────────

JIRA_BASE_URL  = os.getenv("JIRA_BASE_URL", "")
JIRA_EMAIL     = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")

MAX_RETRIES = 4
BASE_DELAY  = 1.0   # seconds; delay = BASE_DELAY * 2^attempt


def _jira_headers() -> dict:
    creds   = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    encoded = base64.b64encode(creds.encode()).decode()
    return {
        "Authorization": f"Basic {encoded}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


# ── Domain types ──────────────────────────────────────────────────────────────

class TransitionStatus(str, Enum):
    SUCCESS = "success"
    FAILED  = "failed"
    TIMEOUT = "timeout"


@dataclass
class TransitionResult:
    issue_key:       str
    status:          TransitionStatus
    attempts:        int   = 0
    total_time:      float = 0.0
    transition_id:   Optional[str] = None
    transition_name: Optional[str] = None
    error_message:   Optional[str] = None
    final_status:    Optional[str] = None


# ── Jira helpers ──────────────────────────────────────────────────────────────

async def _get_transitions(issue_key: str) -> List[dict]:
    """Fetch available transitions for a Jira issue."""
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=_jira_headers(), timeout=10.0)
        r.raise_for_status()
        return r.json().get("transitions", [])


async def _post_transition(
    issue_key: str, transition_id: str, comment: Optional[str] = None
) -> bool:
    """Execute a single transition API call."""
    url  = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions"
    body: Dict[str, Any] = {"transition": {"id": transition_id}}
    if comment:
        body["update"] = {"comment": [{"add": {"body": {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph",
                         "content": [{"type": "text", "text": comment}]}],
        }}}]}
    async with httpx.AsyncClient() as client:
        r = await client.post(url, headers=_jira_headers(), json=body, timeout=10.0)
        return r.status_code in (200, 204)


async def _get_issue_status(issue_key: str) -> Optional[str]:
    """Return the current status name for an issue, or None on error."""
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=_jira_headers(),
                             params={"fields": "status"}, timeout=10.0)
        if r.status_code == 200:
            return r.json()["fields"]["status"]["name"]
    return None


async def _transition_with_retry(
    issue_key: str,
    transition_id: str,
    transition_name: str,
    comment: Optional[str] = None,
) -> TransitionResult:
    """Execute a transition with exponential backoff retry (up to MAX_RETRIES attempts)."""
    start    = time.monotonic()
    last_err = None

    for attempt in range(MAX_RETRIES):
        try:
            ok = await _post_transition(issue_key, transition_id, comment)
            if ok:
                final_status = await _get_issue_status(issue_key)
                return TransitionResult(
                    issue_key=issue_key,
                    status=TransitionStatus.SUCCESS,
                    attempts=attempt + 1,
                    total_time=time.monotonic() - start,
                    transition_id=transition_id,
                    transition_name=transition_name,
                    final_status=final_status,
                )
        except Exception as exc:
            last_err = str(exc)

        if attempt < MAX_RETRIES - 1:
            await asyncio.sleep(BASE_DELAY * (2 ** attempt))

    return TransitionResult(
        issue_key=issue_key,
        status=TransitionStatus.FAILED,
        attempts=MAX_RETRIES,
        total_time=time.monotonic() - start,
        transition_id=transition_id,
        transition_name=transition_name,
        error_message=last_err or "All retry attempts failed",
    )


async def _transition_by_name(
    issue_key: str,
    target_status: str,
    comment: Optional[str] = None,
) -> TransitionResult:
    """Look up the transition ID for target_status, then execute with retry."""
    try:
        transitions = await _get_transitions(issue_key)
    except Exception as exc:
        return TransitionResult(
            issue_key=issue_key,
            status=TransitionStatus.FAILED,
            error_message=f"Failed to fetch transitions: {exc}",
        )

    match = next(
        (t for t in transitions
         if t["to"]["name"].lower() == target_status.lower()),
        None,
    )
    if not match:
        available = [t["to"]["name"] for t in transitions]
        return TransitionResult(
            issue_key=issue_key,
            status=TransitionStatus.FAILED,
            error_message=(
                f"Status '{target_status}' not available. "
                f"Available transitions: {available}"
            ),
        )

    return await _transition_with_retry(
        issue_key, match["id"], match["name"], comment
    )


# ── Request / Response models ─────────────────────────────────────────────────

class TransitionRequest(BaseModel):
    issue_key:     str
    target_status: Optional[str] = None
    transition_id: Optional[str] = None
    comment:       Optional[str] = None


class BulkTransitionRequest(BaseModel):
    transitions: List[TransitionRequest]


class TransitionResponse(BaseModel):
    success:         bool
    status:          str
    issue_key:       str
    transition_id:   Optional[str] = None
    transition_name: Optional[str] = None
    attempts:        int
    total_time:      float
    error_message:   Optional[str] = None
    final_status:    Optional[str] = None


def _to_response(result: TransitionResult) -> TransitionResponse:
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


# ── Router ────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/manager-agent", tags=["manager-agent"])


@router.post("/transition")
async def transition_issue(request: TransitionRequest) -> TransitionResponse:
    """Transition a Jira issue with exponential backoff retry."""
    if not request.target_status and not request.transition_id:
        raise HTTPException(
            status_code=400,
            detail="Either target_status or transition_id must be provided",
        )
    if request.transition_id:
        result = await _transition_with_retry(
            request.issue_key, request.transition_id,
            transition_name=request.transition_id,
            comment=request.comment,
        )
    else:
        result = await _transition_by_name(
            request.issue_key, request.target_status, comment=request.comment
        )
    return _to_response(result)


@router.post("/bulk-transition")
async def bulk_transition(request: BulkTransitionRequest):
    """Transition multiple Jira issues concurrently with exponential backoff."""
    tasks = []
    for t in request.transitions:
        if t.target_status:
            tasks.append(_transition_by_name(t.issue_key, t.target_status, t.comment))
        elif t.transition_id:
            tasks.append(_transition_with_retry(
                t.issue_key, t.transition_id, t.transition_id, t.comment
            ))
        else:
            async def _invalid(key=t.issue_key):
                return TransitionResult(
                    issue_key=key, status=TransitionStatus.FAILED,
                    error_message="Either target_status or transition_id required",
                )
            tasks.append(_invalid())

    results = await asyncio.gather(*tasks)
    return {
        "results":    [_to_response(r) for r in results],
        "total":      len(results),
        "successful": sum(1 for r in results if r.status == TransitionStatus.SUCCESS),
        "failed":     sum(1 for r in results if r.status != TransitionStatus.SUCCESS),
    }


@router.post("/start-work/{issue_key}")
async def start_work(issue_key: str, comment: Optional[str] = None) -> TransitionResponse:
    """Transition an issue to 'In Progress'."""
    return _to_response(await _transition_by_name(issue_key, "In Progress", comment))


@router.post("/complete-work/{issue_key}")
async def complete_work(issue_key: str, comment: Optional[str] = None) -> TransitionResponse:
    """Transition an issue to 'Done'."""
    return _to_response(await _transition_by_name(issue_key, "Done", comment))


@router.post("/code-review/{issue_key}")
async def move_to_code_review(
    issue_key: str, comment: Optional[str] = None
) -> TransitionResponse:
    """Transition an issue to 'Code Review'."""
    return _to_response(await _transition_by_name(issue_key, "Code Review", comment))


@router.post("/testing/{issue_key}")
async def move_to_testing(
    issue_key: str, comment: Optional[str] = None
) -> TransitionResponse:
    """Transition an issue to 'Testing'."""
    return _to_response(await _transition_by_name(issue_key, "Testing", comment))


@router.get("/status/{issue_key}")
async def get_issue_status(issue_key: str):
    """Get the current status of a Jira issue."""
    status = await _get_issue_status(issue_key)
    if status is None:
        raise HTTPException(
            status_code=404, detail=f"Issue {issue_key} not found"
        )
    return {"issue_key": issue_key, "status": status}
