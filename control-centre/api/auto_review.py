"""Auto review API helper for Control Centre."""
import os
import requests
from typing import Dict, Any, List


class AutoReviewAPI:
    """Handle automated PR review operations."""

    def __init__(self):
        self.base_url = os.getenv('VCS_API_URL', 'https://api.vcs-service.com')
        self.api_token = os.getenv('VCS_API_TOKEN')
        self.review_service_url = os.getenv('REVIEW_SERVICE_URL', 'https://review-service.internal')
        
        if not self.api_token:
            raise ValueError('VCS_API_TOKEN environment variable is required')

    def get_open_pull_requests(self, project_id: str) -> List[Dict[str, Any]]:
        """Fetch all open pull requests for a project.

        Args:
            project_id: The project identifier

        Returns:
            List of pull request dictionaries
        """
        headers = {
            'Authorization': f'Bearer {self.api_token}',
        }

        response = requests.get(
            f'{self.base_url}/projects/{project_id}/merge_requests',
            headers=headers,
            params={'state': 'opened'},
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

        return [
            {
                'id': pr.get('iid'),
                'title': pr.get('title'),
                'author': pr.get('author', {}).get('username'),
                'source_branch': pr.get('source_branch'),
                'target_branch': pr.get('target_branch'),
                'url': pr.get('web_url'),
                'created_at': pr.get('created_at'),
                'auto_review_status': self._get_review_status(project_id, pr.get('iid')),
            }
            for pr in data
        ]

    def _get_review_status(self, project_id: str, pr_id: str) -> str:
        """Get the auto-review status for a PR.

        Args:
            project_id: The project identifier
            pr_id: The pull request identifier

        Returns:
            Status string (not_started, in_progress, completed, failed)
        """
        try:
            response = requests.get(
                f'{self.review_service_url}/reviews/status',
                params={'project_id': project_id, 'pr_id': pr_id},
                timeout=10,
            )
            if response.status_code == 200:
                return response.json().get('status', 'not_started')
        except requests.RequestException:
            pass
        
        return 'not_started'

    def trigger_auto_review(self, project_id: str, pr_id: str) -> Dict[str, Any]:
        """Trigger automated review for a pull request.

        Args:
            project_id: The project identifier
            pr_id: The pull request identifier

        Returns:
            Dictionary containing review_id and status
        """
        # First, get PR details
        headers = {
            'Authorization': f'Bearer {self.api_token}',
        }

        pr_response = requests.get(
            f'{self.base_url}/projects/{project_id}/merge_requests/{pr_id}',
            headers=headers,
            timeout=30,
        )
        pr_response.raise_for_status()
        pr_data = pr_response.json()

        # Trigger review service
        review_payload = {
            'project_id': project_id,
            'pr_id': pr_id,
            'pr_title': pr_data.get('title'),
            'source_branch': pr_data.get('source_branch'),
            'target_branch': pr_data.get('target_branch'),
            'diff_url': pr_data.get('diff_refs', {}).get('base_sha'),
        }

        review_response = requests.post(
            f'{self.review_service_url}/reviews/trigger',
            json=review_payload,
            timeout=30,
        )
        review_response.raise_for_status()
        review_data = review_response.json()

        return {
            'review_id': review_data.get('review_id'),
            'status': review_data.get('status', 'in_progress'),
            'estimated_completion': review_data.get('estimated_completion'),
        }

    def get_review_results(self, review_id: str) -> Dict[str, Any]:
        """Get the results of an automated review.

        Args:
            review_id: The review identifier

        Returns:
            Dictionary containing review results
        """
        response = requests.get(
            f'{self.review_service_url}/reviews/{review_id}',
            timeout=30,
        )
        response.raise_for_status()
        
        return response.json()
