"""
Tests for Railway deployment alerting.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from railway_alerting import (
    DeploymentAlert,
    send_deployment_summary
)


@pytest.fixture
def mock_webhook_url():
    """Mock Slack webhook URL."""
    return "https://hooks.slack.com/services/TEST/WEBHOOK/URL"


@pytest.fixture
def alerter(mock_webhook_url):
    """Create an alerter instance with mocked webhook."""
    return DeploymentAlert(webhook_url=mock_webhook_url)


class TestDeploymentAlert:
    """Test suite for DeploymentAlert."""
    
    def test_initialization_with_url(self, mock_webhook_url):
        """Test alerter initialization with webhook URL."""
        alerter = DeploymentAlert(webhook_url=mock_webhook_url)
        assert alerter.webhook_url == mock_webhook_url
    
    def test_initialization_from_env(self):
        """Test alerter initialization from environment variable."""
        with patch.dict('os.environ', {'SLACK_WEBHOOK_URL': 'https://test.url'}):
            alerter = DeploymentAlert()
            assert alerter.webhook_url == 'https://test.url'
    
    def test_initialization_no_webhook(self):
        """Test alerter initialization without webhook URL."""
        with patch.dict('os.environ', {}, clear=True):
            alerter = DeploymentAlert()
            assert alerter.webhook_url is None
    
    @patch('railway_alerting.requests.post')
    def test_send_slack_notification_success(self, mock_post, alerter):
        """Test successful Slack notification."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = alerter.send_slack_notification(
            message="Test message",
            color="#36a64f",
            title="Test Title"
        )
        
        assert result is True
        mock_post.assert_called_once()
        
        # Verify payload structure
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert 'attachments' in payload
        assert len(payload['attachments']) == 1
        assert payload['attachments'][0]['text'] == "Test message"
        assert payload['attachments'][0]['color'] == "#36a64f"
        assert payload['attachments'][0]['title'] == "Test Title"
    
    @patch('railway_alerting.requests.post')
    def test_send_slack_notification_with_fields(self, mock_post, alerter):
        """Test Slack notification with custom fields."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        fields = [
            {"title": "Field 1", "value": "Value 1", "short": True},
            {"title": "Field 2", "value": "Value 2", "short": False}
        ]
        
        result = alerter.send_slack_notification(
            message="Test message",
            fields=fields
        )
        
        assert result is True
        
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['attachments'][0]['fields'] == fields
    
    @patch('railway_alerting.requests.post')
    def test_send_slack_notification_failure(self, mock_post, alerter):
        """Test failed Slack notification."""
        mock_post.side_effect = Exception("Network error")
        
        result = alerter.send_slack_notification(message="Test")
        
        assert result is False
    
    def test_send_slack_notification_no_webhook(self):
        """Test notification when no webhook configured."""
        alerter = DeploymentAlert(webhook_url=None)
        
        result = alerter.send_slack_notification(message="Test")
        
        assert result is False
    
    @patch('railway_alerting.requests.post')
    def test_alert_deployment_success(self, mock_post, alerter):
        """Test deployment success alert."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = alerter.alert_deployment_success(
            service_name="test-service",
            environment="production",
            deployment_id="deploy_123",
            commit_sha="abc123def456",
            branch="main"
        )
        
        assert result is True
        
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        attachment = payload['attachments'][0]
        
        assert attachment['color'] == "#36a64f"  # Green
        assert "Deployment Success" in attachment['title']
        assert "successful" in attachment['text'].lower()
        
        # Verify fields
        fields = {f['title']: f['value'] for f in attachment['fields']}
        assert fields['Service'] == "test-service"
        assert fields['Environment'] == "production"
        assert fields['Deployment ID'] == "deploy_123"
        assert fields['Commit'] == "abc123d"  # Truncated
        assert fields['Branch'] == "main"
    
    @patch('railway_alerting.requests.post')
    def test_alert_deployment_failure(self, mock_post, alerter):
        """Test deployment failure alert."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        error_details = {"error": "Build failed", "code": 500}
        
        result = alerter.alert_deployment_failure(
            service_name="test-service",
            environment="production",
            error_message="Build process failed",
            deployment_id="deploy_456",
            commit_sha="xyz789abc",
            branch="feature-branch",
            error_details=error_details
        )
        
        assert result is True
        
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        attachment = payload['attachments'][0]
        
        assert attachment['color'] == "#ff0000"  # Red
        assert "Deployment Failure" in attachment['title']
        assert "failed" in attachment['text'].lower()
        
        # Verify fields
        fields = {f['title']: f['value'] for f in attachment['fields']}
        assert fields['Service'] == "test-service"
        assert fields['Error'] == "Build process failed"
        assert fields['Deployment ID'] == "deploy_456"
    
    @patch('railway_alerting.requests.post')
    def test_alert_validation_warning(self, mock_post, alerter):
        """Test validation warning alert."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = alerter.alert_validation_warning(
            message="Deployment took longer than expected",
            service_name="test-service",
            details={"duration": "5m 30s"}
        )
        
        assert result is True
        
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        attachment = payload['attachments'][0]
        
        assert attachment['color'] == "#ffaa00"  # Orange
        assert "Deployment Warning" in attachment['title']
        assert "⚠️" in attachment['text']
    
    @patch('railway_alerting.requests.post')
    def test_alert_api_connectivity_failure(self, mock_post, alerter):
        """Test API connectivity failure alert."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = alerter.alert_api_connectivity_failure(
            error_message="Connection timeout",
            project_id="proj_123"
        )
        
        assert result is True
        
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        attachment = payload['attachments'][0]
        
        assert attachment['color'] == "#ff0000"  # Red
        assert "API Connectivity Failure" in attachment['title']
        
        fields = {f['title']: f['value'] for f in attachment['fields']}
        assert fields['Project ID'] == "proj_123"
        assert fields['Error'] == "Connection timeout"


class TestDeploymentSummary:
    """Test suite for deployment summary function."""
    
    @patch('railway_alerting.requests.post')
    def test_send_deployment_summary_all_success(self, mock_post, mock_webhook_url):
        """Test deployment summary with all successful deployments."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = send_deployment_summary(
            webhook_url=mock_webhook_url,
            successful_deploys=2,
            failed_deploys=0,
            warnings=0,
            build_url="https://github.com/test/repo/actions/runs/123"
        )
        
        assert result is True
        
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        attachment = payload['attachments'][0]
        
        assert attachment['color'] == "#36a64f"  # Green
        assert "✅" in attachment['text']
        assert "Success" in attachment['text']
        
        fields = {f['title']: f['value'] for f in attachment['fields']}
        assert fields['Successful'] == "2"
        assert fields['Failed'] == "0"
        assert fields['Warnings'] == "0"
    
    @patch('railway_alerting.requests.post')
    def test_send_deployment_summary_with_failures(self, mock_post, mock_webhook_url):
        """Test deployment summary with failures."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = send_deployment_summary(
            webhook_url=mock_webhook_url,
            successful_deploys=1,
            failed_deploys=1,
            warnings=0
        )
        
        assert result is True
        
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        attachment = payload['attachments'][0]
        
        assert attachment['color'] == "#ff0000"  # Red
        assert "❌" in attachment['text']
        assert "Failed" in attachment['text']
    
    @patch('railway_alerting.requests.post')
    def test_send_deployment_summary_with_warnings(self, mock_post, mock_webhook_url):
        """Test deployment summary with warnings."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = send_deployment_summary(
            webhook_url=mock_webhook_url,
            successful_deploys=2,
            failed_deploys=0,
            warnings=1
        )
        
        assert result is True
        
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        attachment = payload['attachments'][0]
        
        assert attachment['color'] == "#ffaa00"  # Orange
        assert "⚠️" in attachment['text']
        assert "warnings" in attachment['text'].lower()
