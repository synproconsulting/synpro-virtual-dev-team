"""Tests for GitHub workflows API helper."""
import unittest
from unittest.mock import patch, Mock
from control-centre.api.github_workflows import GitHubWorkflowsAPI


class TestGitHubWorkflowsAPI(unittest.TestCase):
    """Test cases for GitHubWorkflowsAPI."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = GitHubWorkflowsAPI(token='test_token')

    def test_init_with_token(self):
        """Test initialization with token."""
        self.assertEqual(self.api.token, 'test_token')
        self.assertIn('Authorization', self.api.headers)
        self.assertEqual(self.api.headers['Authorization'], 'token test_token')

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'env_token'})
    def test_init_with_env_token(self):
        """Test initialization with environment variable."""
        api = GitHubWorkflowsAPI()
        self.assertEqual(api.token, 'env_token')

    @patch('control-centre.api.github_workflows.requests.get')
    def test_get_workflow_runs_success(self, mock_get):
        """Test successful workflow runs fetch."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'workflow_runs': [
                {
                    'id': 123,
                    'name': 'Test Workflow',
                    'status': 'completed',
                    'conclusion': 'success'
                }
            ],
            'total_count': 1
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.api.get_workflow_runs('owner', 'repo')

        self.assertTrue(result['success'])
        self.assertEqual(len(result['workflows']), 1)
        self.assertEqual(result['workflows'][0]['name'], 'Test Workflow')

    @patch('control-centre.api.github_workflows.requests.get')
    def test_get_workflow_runs_with_filters(self, mock_get):
        """Test workflow runs fetch with filters."""
        mock_response = Mock()
        mock_response.json.return_value = {'workflow_runs': [], 'total_count': 0}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        self.api.get_workflow_runs('owner', 'repo', branch='main', status='completed')

        call_args = mock_get.call_args
        params = call_args[1]['params']
        self.assertEqual(params['branch'], 'main')
        self.assertEqual(params['status'], 'completed')

    @patch('control-centre.api.github_workflows.requests.get')
    def test_get_workflow_runs_error(self, mock_get):
        """Test workflow runs fetch with error."""
        mock_get.side_effect = Exception('API Error')

        result = self.api.get_workflow_runs('owner', 'repo')

        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertEqual(len(result['workflows']), 0)

    @patch('control-centre.api.github_workflows.requests.get')
    def test_get_workflow_run_details(self, mock_get):
        """Test fetching specific workflow run details."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 123,
            'name': 'Test Workflow',
            'status': 'completed'
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.api.get_workflow_run_details('owner', 'repo', 123)

        self.assertTrue(result['success'])
        self.assertEqual(result['workflow']['id'], 123)

    @patch('control-centre.api.github_workflows.requests.get')
    def test_get_workflow_jobs(self, mock_get):
        """Test fetching workflow jobs."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'jobs': [{'id': 1, 'name': 'build'}],
            'total_count': 1
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.api.get_workflow_jobs('owner', 'repo', 123)

        self.assertTrue(result['success'])
        self.assertEqual(len(result['jobs']), 1)

    def test_format_single_workflow(self):
        """Test workflow formatting."""
        raw_workflow = {
            'id': 123,
            'name': 'Test',
            'status': 'completed',
            'head_sha': 'abc123',
            'extra_field': 'ignored'
        }

        formatted = self.api._format_single_workflow(raw_workflow)

        self.assertEqual(formatted['id'], 123)
        self.assertEqual(formatted['name'], 'Test')
        self.assertNotIn('extra_field', formatted)


if __name__ == '__main__':
    unittest.main()
