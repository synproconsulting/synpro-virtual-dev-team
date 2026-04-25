"""Sprint status API integration for Jira, GitHub PR, and CI systems."""
import os
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class SprintStatusAPI:
    """Handles fetching sprint status from multiple integration sources."""

    def __init__(self):
        self.jira_base_url = os.environ.get('JIRA_BASE_URL')
        self.jira_api_token = os.environ.get('JIRA_API_TOKEN')
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.ci_api_url = os.environ.get('CI_API_URL')
        self.ci_api_token = os.environ.get('CI_API_TOKEN')

    def fetch_sprint_status(self, sprint_id: str) -> Dict:
        """Fetch complete sprint status including Jira, PRs, and CI builds."""
        try:
            sprint_info = self._get_jira_sprint_info(sprint_id)
            jira_issues = self._get_jira_issues(sprint_id)
            pull_requests = self._get_pull_requests(sprint_id)
            ci_builds = self._get_ci_builds(sprint_id)
            metrics = self._calculate_metrics(jira_issues, pull_requests, ci_builds)

            return {
                'name': sprint_info.get('name', f'Sprint {sprint_id}'),
                'startDate': sprint_info.get('startDate', ''),
                'endDate': sprint_info.get('endDate', ''),
                'metrics': metrics,
                'jiraIssues': jira_issues,
                'pullRequests': pull_requests,
                'ciBuilds': ci_builds,
            }
        except Exception as e:
            raise Exception(f"Failed to fetch sprint status: {str(e)}")

    def _get_jira_sprint_info(self, sprint_id: str) -> Dict:
        """Fetch sprint information from Jira."""
        if not self.jira_base_url or not self.jira_api_token:
            return {'name': f'Sprint {sprint_id}', 'startDate': '', 'endDate': ''}

        url = f"{self.jira_base_url}/rest/agile/1.0/sprint/{sprint_id}"
        headers = {'Authorization': f'Bearer {self.jira_api_token}'}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def _get_jira_issues(self, sprint_id: str) -> List[Dict]:
        """Fetch Jira issues for the sprint."""
        if not self.jira_base_url or not self.jira_api_token:
            return []

        url = f"{self.jira_base_url}/rest/agile/1.0/sprint/{sprint_id}/issue"
        headers = {'Authorization': f'Bearer {self.jira_api_token}'}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        issues = []
        for issue in data.get('issues', []):
            fields = issue.get('fields', {})
            issues.append({
                'key': issue.get('key'),
                'summary': fields.get('summary'),
                'status': fields.get('status', {}).get('name'),
                'priority': fields.get('priority', {}).get('name'),
                'assignee': fields.get('assignee', {}).get('displayName', 'Unassigned'),
                'storyPoints': fields.get('customfield_10016'),
                'url': f"{self.jira_base_url}/browse/{issue.get('key')}",
            })
        return issues

    def _get_pull_requests(self, sprint_id: str) -> List[Dict]:
        """Fetch pull requests related to the sprint from GitHub."""
        if not self.github_token:
            return []

        # This would need to be customized based on your GitHub organization/repos
        # For now, returning a structure that matches the expected format
        return []

    def _get_ci_builds(self, sprint_id: str) -> List[Dict]:
        """Fetch CI/CD build information for the sprint."""
        if not self.ci_api_url or not self.ci_api_token:
            return []

        url = f"{self.ci_api_url}/builds"
        headers = {'Authorization': f'Bearer {self.ci_api_token}'}
        params = {'sprint_id': sprint_id}
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get('builds', [])

    def _calculate_metrics(self, issues: List[Dict], prs: List[Dict], builds: List[Dict]) -> Dict:
        """Calculate sprint metrics from the collected data."""
        total_issues = len(issues)
        completed_issues = len([i for i in issues if i['status'] == 'Done'])
        in_progress_issues = len([i for i in issues if i['status'] == 'In Progress'])
        blocked_issues = len([i for i in issues if i['status'] == 'Blocked'])

        return {
            'totalIssues': total_issues,
            'completedIssues': completed_issues,
            'inProgressIssues': in_progress_issues,
            'blockedIssues': blocked_issues,
            'completionTrend': 0,  # Would need historical data to calculate
        }


# Flask endpoint helper
def fetch_sprint_status(sprint_id: str) -> Dict:
    """Helper function for Flask route."""
    api = SprintStatusAPI()
    return api.fetch_sprint_status(sprint_id)
