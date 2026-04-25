"""Tests for GitHub workflows API routes."""
import pytest
from unittest.mock import patch, Mock
from flask import Flask
from control_centre.api.github_workflows_routes import github_bp


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app = Flask(__name__)
    app.register_blueprint(github_bp)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def mock_api_response():
    """Mock API response data."""
    return {
        'workflows': [
            {
                'id': 123,
                'name': 'CI',
                'status': 'completed',
                'conclusion': 'success',
                'branch': 'main',
                'event': 'push'
            }
        ],
        'total_count': 1,
        'fetched_at': '2024-01-01T12:00:00'
    }


class TestGitHubWorkflowsRoutes:
    """Test suite for GitHub workflows routes."""

    @patch('control_centre.api.github_workflows_routes.GitHubWorkflowsAPI')
    def test_get_workflows_success(self, mock_api_class, client, mock_api_response):
        """Test successful workflows fetch."""
        mock_api = Mock()
        mock_api.get_workflow_runs.return_value = mock_api_response
        mock_api_class.return_value = mock_api
        
        response = client.get('/api/github/workflows?owner=test&repo=repo')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'workflows' in data
        assert len(data['workflows']) == 1
        assert data['workflows'][0]['name'] == 'CI'

    def test_get_workflows_missing_params(self, client):
        """Test workflows endpoint with missing parameters."""
        response = client.get('/api/github/workflows')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    @patch('control_centre.api.github_workflows_routes.GitHubWorkflowsAPI')
    def test_get_workflows_with_filters(self, mock_api_class, client, mock_api_response):
        """Test workflows endpoint with query parameters."""
        mock_api = Mock()
        mock_api.get_workflow_runs.return_value = mock_api_response
        mock_api_class.return_value = mock_api
        
        response = client.get(
            '/api/github/workflows?owner=test&repo=repo&per_page=20&status=completed'
        )
        
        assert response.status_code == 200
        mock_api.get_workflow_runs.assert_called_once_with('test', 'repo', 20, 'completed')

    @patch('control_centre.api.github_workflows_routes.GitHubWorkflowsAPI')
    def test_get_workflow_summary_success(self, mock_api_class, client):
        """Test workflow summary endpoint."""
        mock_api = Mock()
        mock_api.get_workflow_status_summary.return_value = {
            'total': 10,
            'success': 7,
            'failure': 2,
            'in_progress': 1
        }
        mock_api_class.return_value = mock_api
        
        response = client.get('/api/github/workflows/summary?owner=test&repo=repo')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['total'] == 10
        assert data['success'] == 7

    @patch('control_centre.api.github_workflows_routes.GitHubWorkflowsAPI')
    def test_get_latest_workflow_run(self, mock_api_class, client):
        """Test latest workflow run endpoint."""
        mock_api = Mock()
        mock_api.get_latest_run_for_workflow.return_value = {
            'id': 999,
            'status': 'completed',
            'conclusion': 'success'
        }
        mock_api_class.return_value = mock_api
        
        response = client.get(
            '/api/github/workflows/ci.yml/latest?owner=test&repo=repo'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == 999

    @patch('control_centre.api.github_workflows_routes.GitHubWorkflowsAPI')
    def test_get_latest_workflow_run_not_found(self, mock_api_class, client):
        """Test latest workflow run when no runs exist."""
        mock_api = Mock()
        mock_api.get_latest_run_for_workflow.return_value = None
        mock_api_class.return_value = mock_api
        
        response = client.get(
            '/api/github/workflows/ci.yml/latest?owner=test&repo=repo'
        )
        
        assert response.status_code == 404

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
    def test_health_check_with_token(self, client):
        """Test health check endpoint with token configured."""
        response = client.get('/api/github/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert data['token_configured'] is True

    @patch('control_centre.api.github_workflows_routes.GitHubWorkflowsAPI')
    def test_api_error_handling(self, mock_api_class, client):
        """Test error handling in routes."""
        mock_api = Mock()
        mock_api.get_workflow_runs.side_effect = Exception('API Error')
        mock_api_class.return_value = mock_api
        
        response = client.get('/api/github/workflows?owner=test&repo=repo')
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
