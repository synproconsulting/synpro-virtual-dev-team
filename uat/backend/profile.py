"""Profile router - stub (SDT1-47 refactor).

No profile endpoints existed in main.py at the time of the router split.
Profile management endpoints will be added in a future sprint.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/profile", tags=["profile"])

# Placeholder - no profile endpoints implemented yet.