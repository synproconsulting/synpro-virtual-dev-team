"""
pm_agent_router.py
──────────────────
Product Manager Agent router module.
Extracted from main.py as part of router modularization refactor.
Currently placeholder - no PM agent endpoints exist in original main.py.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db

# ── Router ─────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/pm-agent", tags=["pm-agent"])

# ── Models ─────────────────────────────────────────────────────────────────────


class PMAgentResponse(BaseModel):
    """PM Agent response."""
    message: str


# ── Routes ─────────────────────────────────────────────────────────────────────


@router.get("/")
def get_pm_agent(db: Session = Depends(get_db)):
    """Get PM Agent information.
    
    Args:
        db: Database session
        
    Returns:
        PM Agent information
    """
    # Placeholder endpoint - no PM agent logic exists in original main.py
    return {"message": "PM Agent endpoint - to be implemented"}
