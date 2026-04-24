"""Jira data provider for sprint dashboard."""

import os
from typing import Any
import requests
from src.auth.sprint_dashboard import JiraTicket


class JiraProvider:
    """Provider for fetching Jira ticket data."""
    
    def __init__(self, base_url: str | None = None, api_token: str | None = None, email: str | None = None) -> None:
        """Initialize Jira provider.
        
        Args:
            base_url: Jira instance URL (defaults to JIRA_BASE_URL env var)
            api_token: Jira API token (defaults to JIRA_API_TOKEN env var)
            email: Jira user email (defaults to JIRA_EMAIL env var)
        """
        self._base_url = (base_url or os.getenv("JIRA_BASE_URL", "")).rstrip("/")
        self._api_token = api_token or os.getenv("JIRA_API_TOKEN", "")
        self._email = email or os.getenv("JIRA_EMAIL", "")
        self._session = requests.Session()
        
        if self._api_token and self._email:
            self._session.auth = (self._email, self._api_token)
    
    def fetch_data(self, **kwargs: Any) -> list[JiraTicket]:
        """Fetch Jira tickets for a sprint.
        
        Args:
            **kwargs: Must include 'sprint_id'
            
        Returns:
            List of JiraTicket objects
            
        Raises:
            ValueError: If sprint_id not provided
            requests.RequestException: If API call fails
        """
        sprint_id = kwargs.get("sprint_id")
        if not sprint_id:
            raise ValueError("sprint_id is required")
        
        url = f"{self._base_url}/rest/api/3/search"
        params = {
            "jql": f"sprint={sprint_id}",
            "fields": "summary,status,assignee,customfield_10016",
            "maxResults": 100
        }
        
        response = self._session.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        tickets = []
        for issue in data.get("issues", []):
            fields = issue["fields"]
            tickets.append(JiraTicket(
                key=issue["key"],
                summary=fields.get("summary", ""),
                status=fields.get("status", {}).get("name", "Unknown"),
                assignee=fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
                story_points=fields.get("customfield_10016")
            ))
        
        return tickets
