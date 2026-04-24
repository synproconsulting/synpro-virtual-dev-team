"""Sprint trigger functionality for one-click sprint execution."""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SprintConfig:
    """Configuration for sprint execution."""
    sprint_name: str
    start_date: datetime
    duration_days: int
    team_id: str
    auto_review_enabled: bool = True


class SprintTrigger:
    """Handles one-click sprint triggering and orchestration."""

    def __init__(self, config: SprintConfig) -> None:
        """Initialize sprint trigger with configuration.
        
        Args:
            config: Sprint configuration details
        """
        self.config = config
        self._status: str = "idle"
        self._sprint_id: Optional[str] = None

    def trigger_sprint(self) -> Dict[str, Any]:
        """Trigger a new sprint execution.
        
        Returns:
            Dictionary containing sprint execution details
            
        Raises:
            ValueError: If sprint is already running
        """
        if self._status == "running":
            raise ValueError("Sprint is already running")

        logger.info(f"Triggering sprint: {self.config.sprint_name}")
        
        self._status = "running"
        self._sprint_id = self._generate_sprint_id()
        
        result = {
            "sprint_id": self._sprint_id,
            "name": self.config.sprint_name,
            "status": self._status,
            "start_date": self.config.start_date.isoformat(),
            "duration_days": self.config.duration_days,
            "team_id": self.config.team_id,
            "auto_review_enabled": self.config.auto_review_enabled,
            "triggered_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Sprint triggered successfully: {self._sprint_id}")
        return result

    def stop_sprint(self) -> Dict[str, Any]:
        """Stop the current sprint.
        
        Returns:
            Dictionary containing sprint stop details
        """
        logger.info(f"Stopping sprint: {self._sprint_id}")
        
        self._status = "stopped"
        
        return {
            "sprint_id": self._sprint_id,
            "status": self._status,
            "stopped_at": datetime.utcnow().isoformat()
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current sprint status.
        
        Returns:
            Dictionary containing current sprint status
        """
        return {
            "sprint_id": self._sprint_id,
            "status": self._status,
            "config": {
                "name": self.config.sprint_name,
                "team_id": self.config.team_id,
                "auto_review_enabled": self.config.auto_review_enabled
            }
        }

    def _generate_sprint_id(self) -> str:
        """Generate unique sprint identifier.
        
        Returns:
            Unique sprint ID string
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"sprint-{self.config.team_id}-{timestamp}"
