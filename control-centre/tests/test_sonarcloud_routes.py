"""Tests for SonarCloud API routes."""

import pytest
from unittest.mock import patch, Mock
from flask import Flask
from control-centre.api.sonarcloud_routes import sonarcloud_bp


@pytest.fixture
def app():
    """Create test Flask app."""
    app = Flask(__name__)
    app.register_blueprint(sonarcloud_bp)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestSonarCloudRoutes:
    """Test cases for SonarCloud routes."""

    @patch('control-centre.api.sonarcloud_routes.get_sonarcloud_helper')
    def test_trigger_analysis_success(self, mock_get_helper, client):
        """Test successful analysis trigger."""
        mock_helper = Mock()
        mock_helper.trigger_analysis.return_value = {
            'status': 'triggered',
            'repository': 'owner/repo'
        }
        mock_get_helper.return_value = mock_helper
        
        response = client.post(
            '/api/sonarcloud/trigger',
            json={'repository': 'owner/repo', 'branch': 'main'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'triggered'

    def test_trigger_analysis_no_data(self, client):
        """Test trigger without data returns 400."""
        response = client.post('/api/sonarcloud/trigger')
        assert response.status_code == 400

    def test_trigger_analysis_no_repository(self, client):
        """Test trigger without repository returns 400."""
        response = client.post(
            '/api/sonarcloud/trigger',
            json={'branch': 'main'}
        )
        assert response.status_code == 400

    @patch('control-centre.api.sonarcloud_routes.get_sonarcloud_helper')
    def test_get_results_success(self, mock_get_helper, client):
        """Test successful results retrieval."""
        mock_helper = Mock()
        mock_helper.get_full_analysis.return_value = {
            'repository': 'owner/repo',
            'bugs': '5',
            'coverage': '85'
        }
        mock_get_helper.return_value = mock_helper
        
        response = client.get('/api/sonarcloud/results?repository=owner/repo')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['repository'] == 'owner/repo'

    def test_get_results_no_repository(self, client):
        """Test results without repository parameter returns 400."""
        response = client.get('/api/sonarcloud/results')
        assert response.status_code == 400

    @patch('control-centre.api.sonarcloud_routes.get_sonarcloud_helper')
    def test_get_status_success(self, mock_get_helper, client):
        """Test successful status retrieval."""
        mock_helper = Mock()
        mock_helper.get_project_status.return_value = {'status': 'OK'}
        mock_get_helper.return_value = mock_helper
        
        response = client.get('/api/sonarcloud/status/owner/repo')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'OK'

    @patch('control-centre.api.sonarcloud_routes.get_sonarcloud_helper')
    def test_get_issues_success(self, mock_get_helper, client):
        """Test successful issues retrieval."""
        mock_helper = Mock()
        mock_helper.get_project_issues.return_value = {
            'issues': [{'severity': 'MAJOR'}],
            'total': 1
        }
        mock_get_helper.return_value = mock_helper
        
        response = client.get('/api/sonarcloud/issues/owner/repo')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['total'] == 1
