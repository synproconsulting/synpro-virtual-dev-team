"""GitHub Actions workflow API helper."""
import os
import requests
from typing import Dict, List, Optional
from datetime import datetime


class GitHubWorkflowsAPI:
    """Helper class for fetching GitHub Actions workflow data."""

    def __init__(self, token: Optional[str] = None):
        """Initialize with optional GitHub token.
        
        Args:
            token: GitHub personal access token. If not provided, reads from GITHUB_TOKEN env var.
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.base_url = 'https://api.github.com'
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
        }
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'

    def get_workflow_runs(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None,
        status: Optional[str] = None,
        per_page: int = 10
    ) -> Dict:
        """Fetch workflow runs for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Optional branch name filter
            status: Optional status filter (completed, in_progress, queued)
            per_page: Number of results per page (max 100)
            
        Returns:
            Dictionary containing workflow runs and metadata
        """
        url = f'{self.base_url}/repos/{owner}/{repo}/actions/runs'
        params = {'per_page': min(per_page, 100)}
        
        if branch:
            params['branch'] = branch
        if status:
            params['status'] = status

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'success': True,
                'workflows': self._format_workflow_runs(data.get('workflow_runs', [])),
                'total_count': data.get('total_count', 0)
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'workflows': []
            }

    def get_workflow_run_details(self, owner: str, repo: str, run_id: int) -> Dict:
        """Fetch details for a specific workflow run.
        
        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID
            
        Returns:
            Dictionary containing workflow run details
        """
        url = f'{self.base_url}/repos/{owner}/{repo}/actions/runs/{run_id}'
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'success': True,
                'workflow': self._format_single_workflow(data)
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_workflow_jobs(self, owner: str, repo: str, run_id: int) -> Dict:
        """Fetch jobs for a specific workflow run.
        
        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID
            
        Returns:
            Dictionary containing workflow jobs
        """
        url = f'{self.base_url}/repos/{owner}/{repo}/actions/runs/{run_id}/jobs'
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'success': True,
                'jobs': data.get('jobs', []),
                'total_count': data.get('total_count', 0)
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'jobs': []
            }

    def _format_workflow_runs(self, runs: List[Dict]) -> List[Dict]:
        """Format workflow runs for frontend consumption."""
        return [self._format_single_workflow(run) for run in runs]

    def _format_single_workflow(self, run: Dict) -> Dict:
        """Format a single workflow run."""
        return {
            'id': run.get('id'),
            'name': run.get('name', 'Unnamed Workflow'),
            'head_branch': run.get('head_branch'),
            'head_sha': run.get('head_sha'),
            'status': run.get('status'),
            'conclusion': run.get('conclusion'),
            'event': run.get('event'),
            'created_at': run.get('created_at'),
            'updated_at': run.get('updated_at'),
            'run_number': run.get('run_number'),
            'html_url': run.get('html_url'),
            'workflow_id': run.get('workflow_id')
        }

    def get_repository_workflows(self, owner: str, repo: str) -> Dict:
        """Fetch all workflows defined in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary containing workflow definitions
        """
        url = f'{self.base_url}/repos/{owner}/{repo}/actions/workflows'
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'success': True,
                'workflows': data.get('workflows', []),
                'total_count': data.get('total_count', 0)
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'workflows': []
            }
