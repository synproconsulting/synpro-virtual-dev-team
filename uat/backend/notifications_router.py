"""
notifications_router.py
───────────────────────
Notifications management router module.
Extracted from main.py as part of router modularization refactor.
Currently placeholder - no notification endpoints exist in original main.py.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db

# ── Router ─────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/notifications", tags=["notifications"])

# ── Models ─────────────────────────────────────────────────────────────────────


class NotificationResponse(BaseModel):
    """Notification response."""
    message: str


# ── Routes ─────────────────────────────────────────────────────────────────────


@router.get("/")
def get_notifications(db: Session = Depends(get_db)):
    """Get user notifications.
    
    Args:
        db: Database session
        
    Returns:
        List of notifications
    """
    # Placeholder endpoint - no notification logic exists in original main.py
    return {"message": "Notifications endpoint - to be implemented"}
