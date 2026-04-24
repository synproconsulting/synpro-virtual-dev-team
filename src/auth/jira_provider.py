"""Jira data provider implementation."""

import os
from typing import Any
import requests
from requests.auth import HTTPBasicAuth


class JiraProvider:
    """Provider for fetching data from Jira API."""

    def __init__(self, base_url: str | None = None, api_token: str | None = None, email: str | None = None) -> None:
        """Initialize Jira provider.

        Args:
            base_url: Jira instance base URL (from env if not provided)
            api_token: Jira API token (from env if not provided)
            email: Jira user email (from env if not provided)
        """
        self.base_url = (base_url or os.getenv("JIRA_BASE_URL", "")).rstrip("/")
        self.api_token = api_token or os.getenv("JIRA_API_TOKEN", "")
        self.email = email or os.getenv("JIRA_EMAIL", "")
        self.session = requests.Session()
        
        if self.api_token and self.email:
            self.session.auth = HTTPBasicAuth(self.email, self.api_token)

    def fetch_data(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Fetch Jira tickets for a sprint.

        Args:
            **kwargs: Must include 'sprint_id'

        Returns:
            List of ticket dictionaries
        """
        sprint_id = kwargs.get("sprint_id")
        if not sprint_id:
            raise ValueError("sprint_id is required")

        if not self.base_url:
            return []

        jql = f"sprint = {sprint_id}"
        url = f"{self.base_url}/rest/api/3/search"
        params = {
            "jql": jql,
            "fields": "summary,status,assignee,customfield_10016",  # story points field
            "maxResults": 100,
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return self._parse_tickets(data.get("issues", []))
        except requests.RequestException:
            return []

    def _parse_tickets(self, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Parse Jira API response into ticket format."""
        tickets = []
        for issue in issues:
            fields = issue.get("fields", {})
            assignee = fields.get("assignee")
            tickets.append(
                {
                    "key": issue.get("key", ""),
                    "summary": fields.get("summary", ""),
                    "status": fields.get("status", {}).get("name", "Unknown"),
                    "assignee": assignee.get("displayName") if assignee else None,
                    "story_points": fields.get("customfield_10016"),
                }
            )
        return tickets
