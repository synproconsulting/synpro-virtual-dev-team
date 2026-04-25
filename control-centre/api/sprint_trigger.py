"""Sprint trigger API helper for Control Centre."""
import os
import requests
from typing import Dict, Any


class SprintTriggerAPI:
    """Handle sprint pipeline triggering operations."""

    def __init__(self):
        self.base_url = os.getenv('CI_API_URL', 'https://api.ci-service.com')
        self.api_token = os.getenv('CI_API_TOKEN')
        if not self.api_token:
            raise ValueError('CI_API_TOKEN environment variable is required')

    def trigger_sprint(self, project_id: str, branch: str = 'main') -> Dict[str, Any]:
        """Trigger a sprint pipeline for the given project.

        Args:
            project_id: The project identifier
            branch: The branch to run the sprint on (default: main)

        Returns:
            Dictionary containing pipeline_id and status

        Raises:
            requests.RequestException: If the API request fails
        """
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
        }

        payload = {
            'project_id': project_id,
            'ref': branch,
            'variables': {
                'TRIGGER_TYPE': 'sprint',
                'AUTOMATED': 'true',
            },
        }

        response = requests.post(
            f'{self.base_url}/projects/{project_id}/pipeline',
            json=payload,
            headers=headers,
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

        return {
            'pipeline_id': data.get('id'),
            'web_url': data.get('web_url'),
            'status': data.get('status', 'pending'),
            'created_at': data.get('created_at'),
        }

    def get_pipeline_status(self, project_id: str, pipeline_id: str) -> Dict[str, Any]:
        """Get the status of a pipeline.

        Args:
            project_id: The project identifier
            pipeline_id: The pipeline identifier

        Returns:
            Dictionary containing pipeline status information
        """
        headers = {
            'Authorization': f'Bearer {self.api_token}',
        }

        response = requests.get(
            f'{self.base_url}/projects/{project_id}/pipelines/{pipeline_id}',
            headers=headers,
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

        return {
            'id': data.get('id'),
            'status': data.get('status'),
            'web_url': data.get('web_url'),
            'duration': data.get('duration'),
            'finished_at': data.get('finished_at'),
        }
