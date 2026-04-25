"""Tests for GitHub workflows API helper."""
import pytest
from unittest.mock import Mock, patch
from control_centre.api.github_workflows import GitHubWorkflowsAPI


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        'total_count': 2,
        'workflow_runs': [
            {
                'id': 123456,
                'name': 'CI',
                'status': 'completed',
                'conclusion': 'success',
                'head_branch': 'main',
                'event': 'push',
                'created_at': '2024-01-01T10:00:00Z',
                'updated_at': '2024-01-01T10:05:00Z',
                'html_url': 'https://github.com/owner/repo/actions/runs/123456',
                'head_commit': {
                    'message': 'Fix bug',
                    'author': {'name': 'Developer'}
                }
            },
            {
                'id': 123457,
                'name': 'Test',
                'status': 'in_progress',
                'conclusion': None,
                'head_branch': 'feature',
                'event': 'pull_request',
                'created_at': '2024-01-01T11:00:00Z',
                'updated_at': '2024-01-01T11:02:00Z',
                'html_url': 'https://github.com/owner/repo/actions/runs/123457',
                'head_commit': {
                    'message': 'Add feature',
                    'author': {'name': 'Contributor'}
                }
            }
        ]
    }
    return response


class TestGitHubWorkflowsAPI:
    """Test suite for GitHubWorkflowsAPI class."""

    def test_init_with_token(self):
        """Test initialization with explicit token."""
        api = GitHubWorkflowsAPI(token='test_token')
        assert api.token == 'test_token'
        assert 'Authorization' in api.headers
        assert api.headers['Authorization'] == 'Bearer test_token'

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'env_token'})
    def test_init_from_environment(self):
        """Test initialization with token from environment."""
        api = GitHubWorkflowsAPI()
        assert api.token == 'env_token'

    @patch('requests.get')
    def test_get_workflow_runs_success(self, mock_get, mock_response):
        """Test successful workflow runs fetch."""
        mock_get.return_value = mock_response
        
        api = GitHubWorkflowsAPI(token='test_token')
        result = api.get_workflow_runs('owner', 'repo')
        
        assert 'workflows' in result
        assert len(result['workflows']) == 2
        assert result['workflows'][0]['name'] == 'CI'
        assert result['workflows'][0]['status'] == 'completed'
        assert result['workflows'][1]['status'] == 'in_progress'
        assert result['total_count'] == 2

    @patch('requests.get')
    def test_get_workflow_runs_with_status_filter(self, mock_get, mock_response):
        """Test workflow runs fetch with status filter."""
        mock_get.return_value = mock_response
        
        api = GitHubWorkflowsAPI(token='test_token')
        api.get_workflow_runs('owner', 'repo', status='completed')
        
        call_args = mock_get.call_args
        assert call_args[1]['params']['status'] == 'completed'

    @patch('requests.get')
    def test_get_workflow_runs_api_error(self, mock_get):
        """Test handling of API errors."""
        mock_get.side_effect = Exception('API Error')
        
        api = GitHubWorkflowsAPI(token='test_token')
        with pytest.raises(Exception) as exc_info:
            api.get_workflow_runs('owner', 'repo')
        
        assert 'Failed to fetch workflows' in str(exc_info.value)

    @patch('requests.get')
    def test_get_workflow_status_summary(self, mock_get, mock_response):
        """Test workflow status summary."""
        mock_get.return_value = mock_response
        
        api = GitHubWorkflowsAPI(token='test_token')
        summary = api.get_workflow_status_summary('owner', 'repo')
        
        assert summary['total'] == 2
        assert summary['success'] == 1
        assert summary['in_progress'] == 1
        assert summary['failure'] == 0

    @patch('requests.get')
    def test_get_latest_run_for_workflow(self, mock_get):
        """Test fetching latest run for specific workflow."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'workflow_runs': [
                {
                    'id': 999,
                    'status': 'completed',
                    'conclusion': 'success',
                    'created_at': '2024-01-01T12:00:00Z',
                    'html_url': 'https://github.com/owner/repo/actions/runs/999'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        api = GitHubWorkflowsAPI(token='test_token')
        result = api.get_latest_run_for_workflow('owner', 'repo', 'ci.yml')
        
        assert result is not None
        assert result['id'] == 999
        assert result['conclusion'] == 'success'

    @patch('requests.get')
    def test_get_latest_run_no_runs(self, mock_get):
        """Test fetching latest run when no runs exist."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'workflow_runs': []}
        mock_get.return_value = mock_response
        
        api = GitHubWorkflowsAPI(token='test_token')
        result = api.get_latest_run_for_workflow('owner', 'repo', 'ci.yml')
        
        assert result is None
