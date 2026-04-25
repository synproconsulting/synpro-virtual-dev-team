"""SonarCloud API integration for triggering analysis and fetching results."""

import os
import requests
from typing import Dict, Any, Optional
from flask import current_app


class SonarCloudAPIError(Exception):
    """Custom exception for SonarCloud API errors."""
    pass


class SonarCloudClient:
    """Client for interacting with SonarCloud API."""

    def __init__(self, token: Optional[str] = None, organization: Optional[str] = None):
        self.token = token or os.getenv('SONARCLOUD_TOKEN')
        self.organization = organization or os.getenv('SONARCLOUD_ORGANIZATION')
        self.base_url = 'https://sonarcloud.io/api'

        if not self.token:
            raise SonarCloudAPIError('SonarCloud token not configured')

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to SonarCloud API."""
        url = f"{self.base_url}/{endpoint}"
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Bearer {self.token}'

        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"SonarCloud API error: {str(e)}")
            raise SonarCloudAPIError(f"API request failed: {str(e)}")

    def trigger_analysis(self, project_key: str, branch: str = 'main') -> Dict[str, Any]:
        """Trigger on-demand analysis for a project.
        
        Note: This simulates triggering. Actual trigger would depend on CI/CD integration.
        In practice, you might call a GitHub Action or other CI webhook.
        """
        # Check if project exists first
        try:
            self._make_request(
                'GET',
                'components/show',
                params={'component': project_key}
            )
        except SonarCloudAPIError:
            raise SonarCloudAPIError(f"Project {project_key} not found")

        # For actual implementation, trigger via CI/CD webhook
        # This is a placeholder returning mock task ID
        import uuid
        task_id = str(uuid.uuid4())
        
        current_app.logger.info(
            f"Analysis triggered for project {project_key} on branch {branch}"
        )
        
        return {
            'taskId': task_id,
            'projectKey': project_key,
            'branch': branch,
            'status': 'PENDING'
        }

    def get_analysis_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of analysis task."""
        try:
            result = self._make_request(
                'GET',
                'ce/task',
                params={'id': task_id}
            )
            return result.get('task', {})
        except SonarCloudAPIError:
            # If task not found, return pending status
            return {'status': 'PENDING', 'taskId': task_id}

    def get_quality_gate_status(self, project_key: str, branch: str = 'main') -> Dict[str, Any]:
        """Get quality gate status for a project."""
        params = {'projectKey': project_key}
        if branch:
            params['branch'] = branch

        return self._make_request(
            'GET',
            'qualitygates/project_status',
            params=params
        )

    def get_measures(self, project_key: str, branch: str = 'main') -> Dict[str, Any]:
        """Get project measures (bugs, vulnerabilities, code smells, coverage)."""
        metric_keys = [
            'bugs',
            'vulnerabilities',
            'code_smells',
            'coverage',
            'duplicated_lines_density',
            'ncloc',
            'sqale_rating',
            'reliability_rating',
            'security_rating'
        ]

        params = {
            'component': project_key,
            'metricKeys': ','.join(metric_keys)
        }
        if branch:
            params['branch'] = branch

        result = self._make_request(
            'GET',
            'measures/component',
            params=params
        )

        measures = {}
        for measure in result.get('component', {}).get('measures', []):
            measures[measure['metric']] = measure.get('value')

        return measures

    def get_issues(self, project_key: str, branch: str = 'main', page_size: int = 20) -> list:
        """Get issues for a project."""
        params = {
            'componentKeys': project_key,
            'resolved': 'false',
            'ps': page_size,
            's': 'SEVERITY',
            'asc': 'false'
        }
        if branch:
            params['branch'] = branch

        result = self._make_request(
            'GET',
            'issues/search',
            params=params
        )

        return result.get('issues', [])

    def get_project_results(self, project_key: str, branch: str = 'main') -> Dict[str, Any]:
        """Get comprehensive results for a project."""
        try:
            quality_gate = self.get_quality_gate_status(project_key, branch)
            measures = self.get_measures(project_key, branch)
            issues = self.get_issues(project_key, branch)

            return {
                'projectKey': project_key,
                'branch': branch,
                'qualityGateStatus': quality_gate.get('projectStatus', {}).get('status'),
                'bugs': int(measures.get('bugs', 0)),
                'vulnerabilities': int(measures.get('vulnerabilities', 0)),
                'codeSmells': int(measures.get('code_smells', 0)),
                'coverage': float(measures.get('coverage', 0)),
                'duplicatedLinesDensity': float(measures.get('duplicated_lines_density', 0)),
                'linesOfCode': int(measures.get('ncloc', 0)),
                'issues': issues
            }
        except Exception as e:
            current_app.logger.error(f"Error fetching project results: {str(e)}")
            raise SonarCloudAPIError(f"Failed to fetch results: {str(e)}")


def get_client() -> SonarCloudClient:
    """Get configured SonarCloud client instance."""
    return SonarCloudClient()
