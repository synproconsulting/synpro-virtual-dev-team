"""
profile_router.py
─────────────────
User profile management router module.
Extracted from main.py as part of router modularization refactor.
Currently placeholder - no profile endpoints exist in original main.py.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db

# ── Router ─────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/profile", tags=["profile"])

# ── Models ─────────────────────────────────────────────────────────────────────


class ProfileResponse(BaseModel):
    """User profile response."""
    message: str


# ── Routes ─────────────────────────────────────────────────────────────────────


@router.get("/")
def get_profile(db: Session = Depends(get_db)):
    """Get user profile.
    
    Args:
        db: Database session
        
    Returns:
        Profile information
    """
    # Placeholder endpoint - no profile logic exists in original main.py
    return {"message": "Profile endpoint - to be implemented"}
