"""SonarCloud API helper for triggering analysis and fetching results."""

import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime


class SonarCloudHelper:
    """Helper class for SonarCloud API operations."""

    def __init__(self, token: Optional[str] = None, organization: Optional[str] = None):
        """Initialize SonarCloud helper.
        
        Args:
            token: SonarCloud API token (defaults to SONARCLOUD_TOKEN env var)
            organization: SonarCloud organization (defaults to SONARCLOUD_ORG env var)
        """
        self.token = token or os.getenv('SONARCLOUD_TOKEN')
        self.organization = organization or os.getenv('SONARCLOUD_ORG')
        self.base_url = 'https://sonarcloud.io/api'
        
        if not self.token:
            raise ValueError('SonarCloud token not provided')
        if not self.organization:
            raise ValueError('SonarCloud organization not provided')

    def _make_request(self, endpoint: str, method: str = 'GET', **kwargs) -> Dict[str, Any]:
        """Make authenticated request to SonarCloud API.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            **kwargs: Additional request parameters
            
        Returns:
            JSON response data
        """
        url = f"{self.base_url}/{endpoint}"
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Bearer {self.token}'
        
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()

    def trigger_analysis(self, repository: str, branch: str = 'main') -> Dict[str, Any]:
        """Trigger SonarCloud analysis for a repository.
        
        Args:
            repository: Repository name in format 'owner/repo'
            branch: Branch name to analyze
            
        Returns:
            Trigger response data
        """
        project_key = f"{self.organization}_{repository.replace('/', '_')}"
        
        # Trigger analysis via GitHub Actions or similar CI
        # This is a placeholder - actual implementation depends on CI setup
        return {
            'status': 'triggered',
            'repository': repository,
            'branch': branch,
            'project_key': project_key,
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_project_status(self, repository: str) -> Dict[str, Any]:
        """Get quality gate status for a project.
        
        Args:
            repository: Repository name in format 'owner/repo'
            
        Returns:
            Quality gate status
        """
        project_key = f"{self.organization}_{repository.replace('/', '_')}"
        
        try:
            data = self._make_request(
                'qualitygates/project_status',
                params={'projectKey': project_key}
            )
            return data.get('projectStatus', {})
        except requests.exceptions.RequestException as e:
            return {'status': 'ERROR', 'error': str(e)}

    def get_project_measures(self, repository: str) -> Dict[str, Any]:
        """Get code quality measures for a project.
        
        Args:
            repository: Repository name in format 'owner/repo'
            
        Returns:
            Project measures
        """
        project_key = f"{self.organization}_{repository.replace('/', '_')}"
        
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
        
        try:
            data = self._make_request(
                'measures/component',
                params={
                    'component': project_key,
                    'metricKeys': ','.join(metric_keys)
                }
            )
            
            measures = {}
            for measure in data.get('component', {}).get('measures', []):
                measures[measure['metric']] = measure.get('value', '0')
            
            return measures
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

    def get_project_issues(self, repository: str, page_size: int = 20) -> Dict[str, Any]:
        """Get open issues for a project.
        
        Args:
            repository: Repository name in format 'owner/repo'
            page_size: Number of issues to return
            
        Returns:
            List of issues
        """
        project_key = f"{self.organization}_{repository.replace('/', '_')}"
        
        try:
            data = self._make_request(
                'issues/search',
                params={
                    'componentKeys': project_key,
                    'resolved': 'false',
                    'ps': page_size,
                    's': 'SEVERITY',
                    'asc': 'false'
                }
            )
            
            issues = []
            for issue in data.get('issues', []):
                issues.append({
                    'key': issue.get('key'),
                    'severity': issue.get('severity'),
                    'type': issue.get('type'),
                    'message': issue.get('message'),
                    'component': issue.get('component', '').split(':')[-1],
                    'line': issue.get('line'),
                    'status': issue.get('status')
                })
            
            return {'issues': issues, 'total': data.get('total', 0)}
        except requests.exceptions.RequestException as e:
            return {'issues': [], 'total': 0, 'error': str(e)}

    def get_full_analysis(self, repository: str) -> Dict[str, Any]:
        """Get complete analysis results for a project.
        
        Args:
            repository: Repository name in format 'owner/repo'
            
        Returns:
            Complete analysis data
        """
        quality_gate = self.get_project_status(repository)
        measures = self.get_project_measures(repository)
        issues_data = self.get_project_issues(repository)
        
        return {
            'repository': repository,
            'qualityGate': quality_gate,
            'bugs': measures.get('bugs', '0'),
            'vulnerabilities': measures.get('vulnerabilities', '0'),
            'codeSmells': measures.get('code_smells', '0'),
            'coverage': measures.get('coverage', '0'),
            'duplicatedLines': measures.get('duplicated_lines_density', '0'),
            'linesOfCode': measures.get('ncloc', '0'),
            'metrics': {
                'maintainability': measures.get('sqale_rating', 'A'),
                'reliability': measures.get('reliability_rating', 'A'),
                'security': measures.get('security_rating', 'A'),
            },
            'issues': issues_data.get('issues', []),
            'totalIssues': issues_data.get('total', 0),
            'timestamp': datetime.utcnow().isoformat()
        }
