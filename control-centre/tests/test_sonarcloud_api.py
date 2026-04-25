"""Tests for SonarCloud API integration."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from control_centre.api.sonarcloud import SonarCloudClient, SonarCloudAPIError


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables."""
    monkeypatch.setenv('SONARCLOUD_TOKEN', 'test-token')
    monkeypatch.setenv('SONARCLOUD_ORGANIZATION', 'test-org')


@pytest.fixture
def sonar_client(mock_env):
    """Create SonarCloud client instance."""
    return SonarCloudClient()


def test_client_initialization(mock_env):
    """Test client initializes with environment variables."""
    client = SonarCloudClient()
    assert client.token == 'test-token'
    assert client.organization == 'test-org'
    assert client.base_url == 'https://sonarcloud.io/api'


def test_client_initialization_no_token():
    """Test client raises error without token."""
    with pytest.raises(SonarCloudAPIError, match='token not configured'):
        SonarCloudClient(token=None)


@patch('control_centre.api.sonarcloud.requests.request')
def test_trigger_analysis(mock_request, sonar_client):
    """Test triggering analysis."""
    mock_response = Mock()
    mock_response.json.return_value = {'key': 'test-project'}
    mock_response.content = True
    mock_request.return_value = mock_response

    result = sonar_client.trigger_analysis('test-project', 'main')

    assert 'taskId' in result
    assert result['projectKey'] == 'test-project'
    assert result['branch'] == 'main'
    assert result['status'] == 'PENDING'


@patch('control_centre.api.sonarcloud.requests.request')
def test_get_quality_gate_status(mock_request, sonar_client):
    """Test getting quality gate status."""
    mock_response = Mock()
    mock_response.json.return_value = {
        'projectStatus': {'status': 'OK'}
    }
    mock_response.content = True
    mock_request.return_value = mock_response

    result = sonar_client.get_quality_gate_status('test-project')

    assert result['projectStatus']['status'] == 'OK'
    mock_request.assert_called_once()


@patch('control_centre.api.sonarcloud.requests.request')
def test_get_measures(mock_request, sonar_client):
    """Test getting project measures."""
    mock_response = Mock()
    mock_response.json.return_value = {
        'component': {
            'measures': [
                {'metric': 'bugs', 'value': '5'},
                {'metric': 'coverage', 'value': '85.5'}
            ]
        }
    }
    mock_response.content = True
    mock_request.return_value = mock_response

    result = sonar_client.get_measures('test-project')

    assert result['bugs'] == '5'
    assert result['coverage'] == '85.5'


@patch('control_centre.api.sonarcloud.requests.request')
def test_get_issues(mock_request, sonar_client):
    """Test getting project issues."""
    mock_response = Mock()
    mock_response.json.return_value = {
        'issues': [
            {
                'key': 'issue-1',
                'severity': 'MAJOR',
                'message': 'Test issue'
            }
        ]
    }
    mock_response.content = True
    mock_request.return_value = mock_response

    result = sonar_client.get_issues('test-project')

    assert len(result) == 1
    assert result[0]['severity'] == 'MAJOR'


@patch('control_centre.api.sonarcloud.requests.request')
def test_api_error_handling(mock_request, sonar_client):
    """Test API error handling."""
    mock_request.side_effect = Exception('Connection error')

    with pytest.raises(SonarCloudAPIError, match='API request failed'):
        sonar_client.get_quality_gate_status('test-project')


@patch('control_centre.api.sonarcloud.SonarCloudClient.get_quality_gate_status')
@patch('control_centre.api.sonarcloud.SonarCloudClient.get_measures')
@patch('control_centre.api.sonarcloud.SonarCloudClient.get_issues')
def test_get_project_results(mock_issues, mock_measures, mock_qg, sonar_client):
    """Test getting comprehensive project results."""
    mock_qg.return_value = {'projectStatus': {'status': 'OK'}}
    mock_measures.return_value = {
        'bugs': '3',
        'vulnerabilities': '1',
        'code_smells': '10',
        'coverage': '80.0'
    }
    mock_issues.return_value = [{'key': 'issue-1'}]

    result = sonar_client.get_project_results('test-project', 'main')

    assert result['qualityGateStatus'] == 'OK'
    assert result['bugs'] == 3
    assert result['vulnerabilities'] == 1
    assert result['coverage'] == 80.0
    assert len(result['issues']) == 1
