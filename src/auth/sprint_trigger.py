"""Sprint trigger functionality for one-click sprint activation."""

import os
from typing import Optional
from datetime import datetime, timedelta
import httpx


class SprintTrigger:
    """Handles one-click sprint triggering via API."""

    def __init__(self, api_base_url: Optional[str] = None, api_token: Optional[str] = None):
        """
        Initialize sprint trigger.

        Args:
            api_base_url: Base URL for the sprint API
            api_token: Authentication token for API access
        """
        self.api_base_url = api_base_url or os.getenv("SPRINT_API_URL", "")
        self.api_token = api_token or os.getenv("SPRINT_API_TOKEN", "")
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def trigger_sprint(
        self,
        sprint_name: str,
        duration_days: int = 14,
        board_id: Optional[str] = None,
    ) -> dict:
        """
        Trigger a new sprint with one click.

        Args:
            sprint_name: Name of the sprint to create
            duration_days: Duration of the sprint in days
            board_id: Optional board ID to associate sprint with

        Returns:
            Dictionary containing sprint details

        Raises:
            ValueError: If API credentials are not configured
            httpx.HTTPStatusError: If API request fails
        """
        if not self.api_base_url or not self.api_token:
            raise ValueError("Sprint API credentials not configured")

        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration_days)

        payload = {
            "name": sprint_name,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "board_id": board_id,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base_url}/sprints",
                json=payload,
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_sprint_status(self, sprint_id: str) -> dict:
        """
        Get current status of a sprint.

        Args:
            sprint_id: ID of the sprint

        Returns:
            Dictionary containing sprint status
        """
        if not self.api_base_url or not self.api_token:
            raise ValueError("Sprint API credentials not configured")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base_url}/sprints/{sprint_id}",
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def complete_sprint(self, sprint_id: str) -> dict:
        """
        Mark a sprint as complete.

        Args:
            sprint_id: ID of the sprint to complete

        Returns:
            Dictionary containing updated sprint details
        """
        if not self.api_base_url or not self.api_token:
            raise ValueError("Sprint API credentials not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base_url}/sprints/{sprint_id}/complete",
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
