"""SonarCloud API client for triggering analysis and retrieving results."""

import os
from typing import Any

import httpx


class SonarCloudClient:
    """Client for interacting with SonarCloud API."""

    def __init__(self, token: str | None = None, base_url: str = "https://sonarcloud.io/api") -> None:
        """Initialize SonarCloud client.

        Args:
            token: SonarCloud authentication token. If None, reads from SONARCLOUD_TOKEN env var.
            base_url: Base URL for SonarCloud API.

        Raises:
            ValueError: If token is not provided and SONARCLOUD_TOKEN env var is not set.
        """
        self.token = token or os.getenv("SONARCLOUD_TOKEN")
        if not self.token:
            raise ValueError("SonarCloud token must be provided or set in SONARCLOUD_TOKEN env var")
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=30.0,
        )

    def __enter__(self) -> "SonarCloudClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def trigger_analysis(self, project_key: str, branch: str | None = None) -> dict[str, Any]:
        """Trigger an on-demand analysis for a project.

        Args:
            project_key: The SonarCloud project key.
            branch: Optional branch name to analyze.

        Returns:
            Dictionary containing the analysis task details.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        params: dict[str, str] = {"projectKey": project_key}
        if branch:
            params["branch"] = branch

        response = self._client.post(f"{self.base_url}/project_analyses/trigger", params=params)
        response.raise_for_status()
        return response.json()

    def get_analysis_status(self, project_key: str, branch: str | None = None) -> dict[str, Any]:
        """Get the latest analysis status for a project.

        Args:
            project_key: The SonarCloud project key.
            branch: Optional branch name to check.

        Returns:
            Dictionary containing analysis status and metrics.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        params: dict[str, str] = {"component": project_key}
        if branch:
            params["branch"] = branch

        response = self._client.get(f"{self.base_url}/qualitygates/project_status", params=params)
        response.raise_for_status()
        return response.json()

    def get_measures(self, project_key: str, metric_keys: list[str], branch: str | None = None) -> dict[str, Any]:
        """Get specific measures for a project.

        Args:
            project_key: The SonarCloud project key.
            metric_keys: List of metric keys to retrieve.
            branch: Optional branch name.

        Returns:
            Dictionary containing the requested measures.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        params: dict[str, str] = {
            "component": project_key,
            "metricKeys": ",".join(metric_keys),
        }
        if branch:
            params["branch"] = branch

        response = self._client.get(f"{self.base_url}/measures/component", params=params)
        response.raise_for_status()
        return response.json()
