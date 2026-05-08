"""PM Agent router — Anthropic API calls removed (SDT1-83).

Sprint planning is now managed via Claude Code.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional


class PMAgentMessage(BaseModel):
    message: str
    history: Optional[List[dict]] = []


class GenerateSprintRequest(BaseModel):
    brief: str = ""
    message: str = ""
    content: str = ""
    history: Optional[List[dict]] = []
    conversationHistory: Optional[List[dict]] = None


router = APIRouter(prefix="/api/pm-agent", tags=["pm-agent"])

_DISABLED_MSG = (
    "Sprint planning is managed via Claude Code. "
    "Use the Claude Code prompt workflow to plan sprints."
)


@router.post("/chat")
async def pm_agent_chat(request: PMAgentMessage):
    raise HTTPException(status_code=503, detail=_DISABLED_MSG)


@router.post("/generate-sprint")
async def pm_agent_generate_sprint(request: GenerateSprintRequest):
    raise HTTPException(status_code=503, detail=_DISABLED_MSG)