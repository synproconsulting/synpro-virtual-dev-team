"""PM Agent router - product-scoped chat with per-product Anthropic key (SDT1-121).

The chat endpoint accepts an optional ``product_id`` in the request body. When
provided, the Anthropic API key is loaded from the matching ``products`` row
(``anthropic_api_key_enc``) and decrypted via :mod:`encryption.decrypt_secret`.
If no product is supplied, or the row has no key, the ``ANTHROPIC_API_KEY``
environment variable is used.

Sprint plan generation remains delegated to Claude Code (SDT1-83) and continues
to return HTTP 503.
"""

import logging
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from anthropic import Anthropic

from database import get_db
from encryption import decrypt_secret
from models import Product

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pm-agent", tags=["pm-agent"])

_MODEL = "claude-sonnet-4-5"
_MAX_TOKENS = 4096
_SYSTEM_PROMPT = (
    "You are a Product Manager agent helping plan software sprints. "
    "You collaborate with the user to refine briefs, identify scope, "
    "and suggest sprint plans. Keep replies concise and actionable."
)
_SPRINT_DISABLED_MSG = (
    "Sprint plan generation is managed via Claude Code. "
    "Use the Claude Code prompt workflow to plan sprints."
)


class PMAgentMessage(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    product_id: Optional[str] = None


class GenerateSprintRequest(BaseModel):
    brief: str = ""
    message: str = ""
    content: str = ""
    history: Optional[List[dict]] = []
    conversationHistory: Optional[List[dict]] = None
    product_id: Optional[str] = None


def _resolve_anthropic_key(product_id: Optional[str], db: Session) -> str:
    """Return the Anthropic API key for the request.

    Prefers the per-product encrypted key when ``product_id`` is supplied
    and the row carries one. Falls back to ``ANTHROPIC_API_KEY``. Raises
    HTTP 503 if neither source yields a usable key.
    """
    if product_id:
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
        except Exception as exc:
            logger.warning("PM Agent chat: product lookup failed for %s: %s", product_id, exc)
            product = None
        if product and product.anthropic_api_key_enc:
            try:
                return decrypt_secret(product.anthropic_api_key_enc)
            except Exception as exc:
                logger.warning(
                    "Decrypt failed for product %s anthropic_api_key_enc: %s",
                    product_id, exc,
                )
        elif not product:
            logger.info("PM Agent chat: product_id %s not found, using env fallback", product_id)
    env_key = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    if not env_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "No Anthropic API key available. Configure the selected product's "
                "anthropic_api_key or set the ANTHROPIC_API_KEY environment variable."
            ),
        )
    return env_key


def _build_messages(message: str, history: Optional[List[dict]]) -> List[dict]:
    """Coerce the incoming history into Anthropic message format."""
    converted: List[dict] = []
    for entry in (history or []):
        if not isinstance(entry, dict):
            continue
        role = entry.get("role")
        if not role:
            entry_type = entry.get("type")
            if entry_type == "user":
                role = "user"
            elif entry_type in {"agent", "assistant"}:
                role = "assistant"
        if role not in {"user", "assistant"}:
            continue
        content = entry.get("content")
        if not isinstance(content, str) or not content.strip():
            continue
        converted.append({"role": role, "content": content})
    converted.append({"role": "user", "content": message})
    return converted


@router.post("/chat")
def pm_agent_chat(
    request: PMAgentMessage,
    db: Session = Depends(get_db),
) -> dict:
    """Send a chat message to the PM Agent backed by Anthropic.

    Uses the selected product's encrypted Anthropic key when supplied.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="message is required")

    api_key = _resolve_anthropic_key(request.product_id, db)
    client = Anthropic(api_key=api_key)
    messages = _build_messages(request.message, request.history)

    try:
        response = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=_SYSTEM_PROMPT,
            messages=messages,
        )
    except Exception as exc:
        logger.error("PM Agent Anthropic call failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {exc}")

    reply_parts = []
    for block in (response.content or []):
        text = getattr(block, "text", None)
        if isinstance(text, str):
            reply_parts.append(text)
    reply = "".join(reply_parts).strip()
    return {"reply": reply, "role": "assistant"}


@router.post("/generate-sprint")
def pm_agent_generate_sprint(request: GenerateSprintRequest) -> dict:
    """Sprint plan generation remains delegated to Claude Code (SDT1-83)."""
    raise HTTPException(status_code=503, detail=_SPRINT_DISABLED_MSG)
