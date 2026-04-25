"""Tests for SonarCloud helper."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from control-centre.api.sonarcloud_helper import SonarCloudHelper


class TestSonarCloudHelper:
    """Test cases for SonarCloudHelper."""

    @patch.dict('os.environ', {'SONARCLOUD_TOKEN': 'test-token', 'SONARCLOUD_ORG': 'test-org'})
    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        helper = SonarCloudHelper()
        assert helper.token == 'test-token'
        assert helper.organization == 'test-org'

    def test_init_without_token_raises_error(self):
        """Test initialization without token raises ValueError."""
        with pytest.raises(ValueError, match='SonarCloud token not provided'):
            SonarCloudHelper(token=None, organization='test-org')

    def test_init_without_org_raises_error(self):
        """Test initialization without organization raises ValueError."""
        with pytest.raises(ValueError, match='SonarCloud organization not provided'):
            SonarCloudHelper(token='test-token', organization=None)

    @patch('requests.request')
    def test_trigger_analysis(self, mock_request):
        """Test triggering analysis."""
        helper = SonarCloudHelper(token='test-token', organization='test-org')
        result = helper.trigger_analysis('owner/repo', 'main')
        
        assert result['status'] == 'triggered'
        assert result['repository'] == 'owner/repo'
        assert result['branch'] == 'main'
        assert 'timestamp' in result

    @patch('requests.request')
    def test_get_project_status(self, mock_request):
        """Test getting project status."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'projectStatus': {'status': 'OK'}
        }
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        helper = SonarCloudHelper(token='test-token', organization='test-org')
        status = helper.get_project_status('owner/repo')
        
        assert status == {'status': 'OK'}

    @patch('requests.request')
    def test_get_project_measures(self, mock_request):
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
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        helper = SonarCloudHelper(token='test-token', organization='test-org')
        measures = helper.get_project_measures('owner/repo')
        
        assert measures['bugs'] == '5'
        assert measures['coverage'] == '85.5'

    @patch('requests.request')
    def test_get_project_issues(self, mock_request):
        """Test getting project issues."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'issues': [
                {
                    'key': 'issue-1',
                    'severity': 'MAJOR',
                    'type': 'BUG',
                    'message': 'Test issue',
                    'component': 'project:file.py',
                    'line': 42,
                    'status': 'OPEN'
                }
            ],
            'total': 1
        }
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        helper = SonarCloudHelper(token='test-token', organization='test-org')
        result = helper.get_project_issues('owner/repo')
        
        assert len(result['issues']) == 1
        assert result['total'] == 1
        assert result['issues'][0]['severity'] == 'MAJOR'

    @patch.object(SonarCloudHelper, 'get_project_status')
    @patch.object(SonarCloudHelper, 'get_project_measures')
    @patch.object(SonarCloudHelper, 'get_project_issues')
    def test_get_full_analysis(self, mock_issues, mock_measures, mock_status):
        """Test getting full analysis."""
        mock_status.return_value = {'status': 'OK'}
        mock_measures.return_value = {
            'bugs': '3',
            'vulnerabilities': '1',
            'coverage': '80'
        }
        mock_issues.return_value = {'issues': [], 'total': 0}
        
        helper = SonarCloudHelper(token='test-token', organization='test-org')
        analysis = helper.get_full_analysis('owner/repo')
        
        assert analysis['repository'] == 'owner/repo'
        assert analysis['bugs'] == '3'
        assert analysis['vulnerabilities'] == '1'
        assert analysis['coverage'] == '80'
        assert 'timestamp' in analysis
