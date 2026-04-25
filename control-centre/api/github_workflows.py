"""GitHub Actions workflow monitoring API helper."""
import os
import requests
from typing import Dict, List, Optional
from datetime import datetime


class GitHubWorkflowsAPI:
    """Helper class for fetching GitHub Actions workflow data."""

    def __init__(self, token: Optional[str] = None):
        """Initialize with GitHub token from environment or parameter."""
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.base_url = 'https://api.github.com'
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
        }
        if self.token:
            self.headers['Authorization'] = f'Bearer {self.token}'

    def get_workflow_runs(
        self,
        owner: str,
        repo: str,
        per_page: int = 10,
        status: Optional[str] = None
    ) -> Dict:
        """Fetch workflow runs for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            per_page: Number of results per page (max 100)
            status: Filter by status (completed, in_progress, queued)
            
        Returns:
            Dictionary containing workflow runs and metadata
        """
        url = f'{self.base_url}/repos/{owner}/{repo}/actions/runs'
        params = {'per_page': min(per_page, 100)}
        
        if status:
            params['status'] = status

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            workflows = []
            for run in data.get('workflow_runs', []):
                workflows.append({
                    'id': run['id'],
                    'name': run['name'],
                    'status': run['status'],
                    'conclusion': run.get('conclusion'),
                    'branch': run['head_branch'],
                    'event': run['event'],
                    'created_at': run['created_at'],
                    'updated_at': run['updated_at'],
                    'html_url': run['html_url'],
                    'commit_message': run['head_commit']['message'] if run.get('head_commit') else 'N/A',
                    'author': run['head_commit']['author']['name'] if run.get('head_commit') else 'Unknown',
                })
            
            return {
                'workflows': workflows,
                'total_count': data.get('total_count', 0),
                'fetched_at': datetime.utcnow().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            raise Exception(f'Failed to fetch workflows: {str(e)}')

    def get_workflow_status_summary(self, owner: str, repo: str) -> Dict:
        """Get a summary of workflow statuses.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary with status counts
        """
        data = self.get_workflow_runs(owner, repo, per_page=50)
        workflows = data.get('workflows', [])
        
        summary = {
            'total': len(workflows),
            'success': 0,
            'failure': 0,
            'in_progress': 0,
            'queued': 0,
            'cancelled': 0,
            'other': 0
        }
        
        for workflow in workflows:
            status = workflow['status']
            conclusion = workflow.get('conclusion')
            
            if status in ['in_progress', 'queued']:
                summary[status] += 1
            elif conclusion == 'success':
                summary['success'] += 1
            elif conclusion == 'failure':
                summary['failure'] += 1
            elif conclusion == 'cancelled':
                summary['cancelled'] += 1
            else:
                summary['other'] += 1
        
        return summary

    def get_latest_run_for_workflow(
        self,
        owner: str,
        repo: str,
        workflow_id: str
    ) -> Optional[Dict]:
        """Get the latest run for a specific workflow.
        
        Args:
            owner: Repository owner
            repo: Repository name
            workflow_id: Workflow ID or filename
            
        Returns:
            Latest workflow run data or None
        """
        url = f'{self.base_url}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs'
        params = {'per_page': 1}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            runs = data.get('workflow_runs', [])
            if runs:
                run = runs[0]
                return {
                    'id': run['id'],
                    'status': run['status'],
                    'conclusion': run.get('conclusion'),
                    'created_at': run['created_at'],
                    'html_url': run['html_url']
                }
            return None
            
        except requests.exceptions.RequestException as e:
            raise Exception(f'Failed to fetch workflow: {str(e)}')
