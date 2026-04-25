"""Tests for sprint status API."""
import pytest
from unittest.mock import Mock, patch
from control_centre.api.sprint_status import SprintStatusAPI


class TestSprintStatusAPI:
    """Test cases for SprintStatusAPI."""

    @pytest.fixture
    def api(self):
        """Create SprintStatusAPI instance for testing."""
        return SprintStatusAPI()

    @pytest.fixture
    def mock_jira_response(self):
        """Mock Jira API response."""
        return {
            'name': 'Sprint 45',
            'startDate': '2024-01-01',
            'endDate': '2024-01-14',
        }

    @pytest.fixture
    def mock_issues_response(self):
        """Mock Jira issues response."""
        return {
            'issues': [
                {
                    'key': 'SDT1-31',
                    'fields': {
                        'summary': 'Sprint dashboard',
                        'status': {'name': 'In Progress'},
                        'priority': {'name': 'High'},
                        'assignee': {'displayName': 'John Doe'},
                        'customfield_10016': 5,
                    }
                }
            ]
        }

    @patch('control_centre.api.sprint_status.requests.get')
    def test_fetch_sprint_status_success(self, mock_get, api, mock_jira_response, mock_issues_response):
        """Test successful sprint status fetch."""
        mock_response = Mock()
        mock_response.json.side_effect = [mock_jira_response, mock_issues_response]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch.dict('os.environ', {
            'JIRA_BASE_URL': 'https://jira.example.com',
            'JIRA_API_TOKEN': 'test-token'
        }):
            api = SprintStatusAPI()
            result = api.fetch_sprint_status('123')

        assert result['name'] == 'Sprint 45'
        assert 'metrics' in result
        assert 'jiraIssues' in result

    def test_calculate_metrics(self, api):
        """Test metrics calculation."""
        issues = [
            {'status': 'Done'},
            {'status': 'In Progress'},
            {'status': 'Blocked'},
            {'status': 'Done'},
        ]
        metrics = api._calculate_metrics(issues, [], [])

        assert metrics['totalIssues'] == 4
        assert metrics['completedIssues'] == 2
        assert metrics['inProgressIssues'] == 1
        assert metrics['blockedIssues'] == 1

    @patch('control_centre.api.sprint_status.requests.get')
    def test_fetch_sprint_status_api_error(self, mock_get, api):
        """Test handling of API errors."""
        mock_get.side_effect = Exception('API Error')

        with patch.dict('os.environ', {
            'JIRA_BASE_URL': 'https://jira.example.com',
            'JIRA_API_TOKEN': 'test-token'
        }):
            api = SprintStatusAPI()
            with pytest.raises(Exception, match='Failed to fetch sprint status'):
                api.fetch_sprint_status('123')

    def test_missing_credentials(self, api):
        """Test behavior when credentials are missing."""
        with patch.dict('os.environ', {}, clear=True):
            api = SprintStatusAPI()
            sprint_info = api._get_jira_sprint_info('123')
            issues = api._get_jira_issues('123')

        assert sprint_info['name'] == 'Sprint 123'
        assert issues == []
