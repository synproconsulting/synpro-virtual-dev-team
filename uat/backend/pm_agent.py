"""PM Agent router - extracted from main.py (SDT1-47 refactor)."""

import os
from typing import List, Optional

import anthropic
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# ── Config ────────────────────────────────────────────────────────────────────────────

PM_AGENT_SYSTEM = """You are a Product Manager AI agent for a software development team.
Your role is to help plan sprints, create user stories, and manage product backlogs.

When given a feature brief, you should:
1. Break it down into epics and user stories
2. Estimate story points (1, 2, 3, 5, 8, 13)
3. Define acceptance criteria for each story
4. Suggest execution order based on dependencies
5. Flag any risks or dependencies

Format stories as:
- Title: clear, concise
- Description: as a [user], I want [feature] so that [benefit]
- Acceptance criteria: bullet points
- Story points: number
- Priority: Highest/High/Medium/Low/Lowest
- Execution order: number

Always ask clarifying questions if the brief is unclear."""


def _get_anthropic_client():
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")
    return anthropic.Anthropic(api_key=api_key)


# ── Request models ─────────────────────────────────────────────────────────────────────────

class PMAgentMessage(BaseModel):
    message: str
    history: Optional[List[dict]] = []


class GenerateSprintRequest(BaseModel):
    brief: str = ""
    message: str = ""
    content: str = ""
    history: Optional[List[dict]] = []
    conversationHistory: Optional[List[dict]] = None


# ── Router ────────────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/pm-agent", tags=["pm-agent"])


@router.post("/chat")
async def pm_agent_chat(request: PMAgentMessage):
    """Chat with the PM Agent."""
    try:
        client      = _get_anthropic_client()
        # C-1 fix: define history_raw explicitly so it is always in scope
        history_raw = request.history or []
        messages    = []
        for h in history_raw:
            if h.get("role") in ("user", "assistant"):
                messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": request.message})
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2000,
            system=PM_AGENT_SYSTEM,
            messages=messages,
        )
        reply = response.content[0].text
        return {"reply": reply, "role": "assistant"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-sprint")
async def pm_agent_generate_sprint(request: GenerateSprintRequest):
    """Generate a sprint plan from a feature brief."""
    import json
    try:
        client      = _get_anthropic_client()
        # C-2 fix: request is now a Pydantic model; dot access works without AttributeError
        brief       = request.brief or request.message or request.content
        history_raw = request.history or request.conversationHistory or []
        prompt = f"""Given this feature brief, create a complete sprint plan:

{brief}

Return a JSON object with this structure:
{{
  "epic": {{
    "title": "Epic title",
    "description": "Epic description"
  }},
  "stories": [
    {{
      "title": "Story title",
      "description": "As a user...",
      "acceptance_criteria": ["criterion 1", "criterion 2"],
      "story_points": 5,
      "priority": "High",
      "execution_order": 1
    }}
  ],
  "summary": "Brief summary of the sprint plan",
  "total_points": 0,
  "risks": ["risk 1"]
}}

Return ONLY valid JSON, no markdown."""

        messages = []
        for h in (history_raw or []):
            if h.get("role") in ("user", "assistant"):
                messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": prompt})

        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4000,
            system=PM_AGENT_SYSTEM,
            messages=messages,
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:-1])
        plan = json.loads(raw)
        return {"plan": plan, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
