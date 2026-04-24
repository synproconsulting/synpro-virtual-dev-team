"""Sprint trigger functionality for one-click sprint initiation."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SprintConfig:
    """Configuration for sprint triggering."""
    
    sprint_duration_days: int = 14
    auto_start: bool = True
    notification_enabled: bool = True
    team_id: Optional[str] = None


class SprintTrigger:
    """Handles one-click sprint triggering with configurable parameters."""
    
    def __init__(self, config: SprintConfig):
        """Initialize sprint trigger with configuration.
        
        Args:
            config: Sprint configuration object
        """
        self.config = config
        self._active_sprint: Optional[Dict[str, Any]] = None
        logger.info(f"SprintTrigger initialized for team {config.team_id}")
    
    async def trigger_sprint(self, name: str, start_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Trigger a new sprint with one click.
        
        Args:
            name: Sprint name/identifier
            start_date: Optional sprint start date, defaults to now
            
        Returns:
            Dictionary containing sprint details
            
        Raises:
            ValueError: If a sprint is already active
        """
        if self._active_sprint and self._active_sprint.get("status") == "active":
            raise ValueError("Cannot start new sprint while another is active")
        
        start = start_date or datetime.utcnow()
        end = start + timedelta(days=self.config.sprint_duration_days)
        
        self._active_sprint = {
            "name": name,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "status": "active",
            "team_id": self.config.team_id,
            "triggered_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Sprint '{name}' triggered successfully")
        
        if self.config.notification_enabled:
            await self._send_notification(self._active_sprint)
        
        return self._active_sprint
    
    async def _send_notification(self, sprint_data: Dict[str, Any]) -> None:
        """Send notification about sprint trigger.
        
        Args:
            sprint_data: Sprint information to include in notification
        """
        # Placeholder for actual notification logic
        await asyncio.sleep(0.1)
        logger.info(f"Notification sent for sprint: {sprint_data['name']}")
    
    def get_active_sprint(self) -> Optional[Dict[str, Any]]:
        """Get currently active sprint information.
        
        Returns:
            Active sprint dictionary or None
        """
        return self._active_sprint
    
    async def complete_sprint(self) -> Dict[str, Any]:
        """Mark the current sprint as completed.
        
        Returns:
            Completed sprint data
            
        Raises:
            ValueError: If no active sprint exists
        """
        if not self._active_sprint:
            raise ValueError("No active sprint to complete")
        
        self._active_sprint["status"] = "completed"
        self._active_sprint["completed_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Sprint '{self._active_sprint['name']}' completed")
        return self._active_sprint
