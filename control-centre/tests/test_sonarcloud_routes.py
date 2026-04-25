"""Tests for SonarCloud API routes."""

import pytest
from unittest.mock import patch, Mock
import json


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def mock_sonar_client():
    """Mock SonarCloud client."""
    with patch('control_centre.api.sonarcloud_routes.get_client') as mock:
        yield mock


def test_trigger_analysis_success(client, mock_sonar_client):
    """Test successful analysis trigger."""
    mock_client = Mock()
    mock_client.trigger_analysis.return_value = {
        'taskId': 'task-123',
        'projectKey': 'test-project',
        'status': 'PENDING'
    }
    mock_sonar_client.return_value = mock_client

    response = client.post(
        '/api/sonarcloud/trigger',
        data=json.dumps({'projectKey': 'test-project', 'branch': 'main'}),
        content_type='application/json'
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['taskId'] == 'task-123'
    assert data['projectKey'] == 'test-project'


def test_trigger_analysis_missing_project_key(client, mock_sonar_client):
    """Test trigger fails without project key."""
    response = client.post(
        '/api/sonarcloud/trigger',
        data=json.dumps({'branch': 'main'}),
        content_type='application/json'
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_get_analysis_status(client, mock_sonar_client):
    """Test getting analysis status."""
    mock_client = Mock()
    mock_client.get_analysis_status.return_value = {
        'status': 'SUCCESS',
        'taskId': 'task-123'
    }
    mock_sonar_client.return_value = mock_client

    response = client.get('/api/sonarcloud/status/task-123')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'SUCCESS'


def test_get_project_results(client, mock_sonar_client):
    """Test getting project results."""
    mock_client = Mock()
    mock_client.get_project_results.return_value = {
        'projectKey': 'test-project',
        'qualityGateStatus': 'OK',
        'bugs': 5,
        'vulnerabilities': 2
    }
    mock_sonar_client.return_value = mock_client

    response = client.get('/api/sonarcloud/results/test-project?branch=main')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['qualityGateStatus'] == 'OK'
    assert data['bugs'] == 5


def test_get_quality_gate(client, mock_sonar_client):
    """Test getting quality gate status."""
    mock_client = Mock()
    mock_client.get_quality_gate_status.return_value = {
        'projectStatus': {'status': 'OK'}
    }
    mock_sonar_client.return_value = mock_client

    response = client.get('/api/sonarcloud/quality-gate/test-project')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['projectStatus']['status'] == 'OK'
