"""Notifications router - stub (SDT1-47 refactor).

No notification endpoints existed in main.py at the time of the router split.
Notification endpoints will be added in a future sprint.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Placeholder - no notification endpoints implemented yet.