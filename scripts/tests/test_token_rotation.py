"""
Tests for token rotation script.

Run with: pytest scripts/tests/test_token_rotation.py
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rotate_tokens import TokenRotator, RotationResult, TokenRotationError


@pytest.fixture
def mock_aws_clients():
    """Mock AWS clients."""
    with patch('boto3.client') as mock_client:
        mock_secrets = MagicMock()
        mock_ssm = MagicMock()
        
        def client_factory(service_name):
            if service_name == 'secretsmanager':
                return mock_secrets
            elif service_name == 'ssm':
                return mock_ssm
            return MagicMock()
        
        mock_client.side_effect = client_factory
        yield mock_secrets, mock_ssm


@pytest.fixture
def token_rotator(mock_aws_clients):
    """Create a TokenRotator instance with mocked AWS clients."""
    rotator = TokenRotator(environment='staging', dry_run=True, force=True)
    return rotator


class TestTokenRotator:
    """Tests for TokenRotator class."""
    
    def test_initialization(self, token_rotator):
        """Test TokenRotator initialization."""
        assert token_rotator.environment == 'staging'
        assert token_rotator.dry_run is True
        assert token_rotator.force is True
        assert token_rotator.secret_prefix == 'pm-agent/staging'
        assert token_rotator.rotation_log == []
    
    def test_get_secret(self, token_rotator, mock_aws_clients):
        """Test retrieving a secret."""
        mock_secrets, _ = mock_aws_clients
        mock_secrets.get_secret_value.return_value = {
            'SecretString': 'test-secret-value'
        }
        
        result = token_rotator._get_secret('test-secret')
        
        assert result == 'test-secret-value'
        mock_secrets.get_secret_value.assert_called_once_with(
            SecretId='pm-agent/staging/test-secret'
        )
    
    def test_get_secret_error(self, token_rotator, mock_aws_clients):
        """Test secret retrieval error handling."""
        mock_secrets, _ = mock_aws_clients
        mock_secrets.get_secret_value.side_effect = Exception("Secret not found")
        
        with pytest.raises(TokenRotationError):
            token_rotator._get_secret('nonexistent-secret')
    
    def test_update_secret_dry_run(self, token_rotator, mock_aws_clients):
        """Test secret update in dry-run mode."""
        mock_secrets, _ = mock_aws_clients
        
        result = token_rotator._update_secret('test-secret', 'new-value')
        
        assert result is True
        mock_secrets.update_secret.assert_not_called()
    
    def test_update_secret(self, mock_aws_clients):
        """Test actual secret update."""
        mock_secrets, _ = mock_aws_clients
        rotator = TokenRotator(environment='staging', dry_run=False, force=True)
        
        result = rotator._update_secret('test-secret', 'new-value')
        
        assert result is True
        mock_secrets.update_secret.assert_called_once()
    
    def test_update_kubernetes_env_dry_run(self, token_rotator):
        """Test Kubernetes environment update in dry-run mode."""
        result = token_rotator._update_kubernetes_env(
            'test-deployment',
            'TEST_VAR',
            'test-value'
        )
        
        assert result is True
    
    @patch('subprocess.run')
    def test_update_kubernetes_env(self, mock_run, mock_aws_clients):
        """Test actual Kubernetes environment update."""
        rotator = TokenRotator(environment='staging', dry_run=False, force=True)
        mock_run.return_value = MagicMock(returncode=0)
        
        result = rotator._update_kubernetes_env(
            'test-deployment',
            'TEST_VAR',
            'test-value'
        )
        
        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'kubectl' in args
        assert 'set' in args
        assert 'env' in args
    
    @patch('requests.get')
    def test_test_http_endpoint_success(self, mock_get, token_rotator):
        """Test HTTP endpoint testing with success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = token_rotator._test_http_endpoint(
            'https://api.example.com/test',
            {'Authorization': 'Bearer token'}
        )
        
        assert result is True
    
    @patch('requests.get')
    def test_test_http_endpoint_failure(self, mock_get, token_rotator):
        """Test HTTP endpoint testing with failure."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        result = token_rotator._test_http_endpoint(
            'https://api.example.com/test',
            {'Authorization': 'Bearer token'}
        )
        
        assert result is False
    
    @patch('requests.get')
    def test_test_http_endpoint_exception(self, mock_get, token_rotator):
        """Test HTTP endpoint testing with exception."""
        mock_get.side_effect = Exception("Connection error")
        
        result = token_rotator._test_http_endpoint(
            'https://api.example.com/test',
            {'Authorization': 'Bearer token'}
        )
        
        assert result is False
    
    @patch.dict(os.environ, {
        'NEW_JIRA_TOKEN': 'test-jira-token-12345',
        'JIRA_EMAIL': 'test@example.com',
        'JIRA_DOMAIN': 'test.atlassian.net'
    })
    def test_rotate_jira_token(self, token_rotator, mock_aws_clients):
        """Test Jira token rotation."""
        mock_secrets, _ = mock_aws_clients
        mock_secrets.get_secret_value.return_value = {
            'SecretString': 'old-jira-token-67890'
        }
        
        result = token_rotator.rotate_jira_token()
        
        assert result.token_type == 'jira'
        assert result.success is True
        assert result.old_token_last4 == '7890'
        assert result.new_token_last4 == '2345'
        assert result.error is None
    
    @patch.dict(os.environ, {'NEW_OPENAI_KEY': 'sk-test-key-12345'})
    def test_rotate_openai_key(self, token_rotator, mock_aws_clients):
        """Test OpenAI key rotation."""
        mock_secrets, _ = mock_aws_clients
        mock_secrets.get_secret_value.return_value = {
            'SecretString': 'sk-old-key-67890'
        }
        
        result = token_rotator.rotate_openai_key()
        
        assert result.token_type == 'openai'
        assert result.success is True
        assert result.old_token_last4 == '7890'
        assert result.new_token_last4 == '2345'
    
    @patch.dict(os.environ, {'NEW_GITHUB_TOKEN': 'ghp_test_token_12345'})
    def test_rotate_github_token(self, token_rotator, mock_aws_clients):
        """Test GitHub token rotation."""
        mock_secrets, _ = mock_aws_clients
        mock_secrets.get_secret_value.return_value = {
            'SecretString': 'ghp_old_token_67890'
        }
        
        result = token_rotator.rotate_github_token()
        
        assert result.token_type == 'github'
        assert result.success is True
        assert result.old_token_last4 == '7890'
        assert result.new_token_last4 == '2345'
    
    def test_rotate_jwt_secret(self, token_rotator, mock_aws_clients):
        """Test JWT secret rotation."""
        mock_secrets, _ = mock_aws_clients
        mock_secrets.get_secret_value.return_value = {
            'SecretString': 'old-jwt-secret-67890'
        }
        
        result = token_rotator.rotate_jwt_secret()
        
        assert result.token_type == 'jwt'
        assert result.success is True
        assert result.old_token_last4 == '7890'
        assert len(result.new_token_last4) == 4
    
    def test_rotate_database_password(self, token_rotator, mock_aws_clients):
        """Test database password rotation."""
        mock_secrets, _ = mock_aws_clients
        mock_secrets.get_secret_value.return_value = {
            'SecretString': 'postgresql://user:oldpass1234@localhost:5432/db'
        }
        
        result = token_rotator.rotate_database_password()
        
        assert result.token_type == 'database'
        assert result.success is True
        assert result.old_token_last4 == '1234'
    
    def test_rotate_tokens_multiple(self, token_rotator, mock_aws_clients):
        """Test rotating multiple tokens."""
        mock_secrets, _ = mock_aws_clients
        mock_secrets.get_secret_value.return_value = {
            'SecretString': 'test-secret-value'
        }
        
        with patch.dict(os.environ, {
            'NEW_JIRA_TOKEN': 'jira-token',
            'NEW_OPENAI_KEY': 'openai-key'
        }):
            results = token_rotator.rotate_tokens(['jira', 'openai'])
        
        assert len(results) == 2
        assert all(r.success for r in results)
        assert results[0].token_type == 'jira'
        assert results[1].token_type == 'openai'
    
    def test_rotate_tokens_all(self, token_rotator, mock_aws_clients):
        """Test rotating all tokens."""
        mock_secrets, _ = mock_aws_clients
        mock_secrets.get_secret_value.return_value = {
            'SecretString': 'postgresql://user:pass@localhost:5432/db'
        }
        
        with patch.dict(os.environ, {
            'NEW_JIRA_TOKEN': 'jira-token',
            'NEW_OPENAI_KEY': 'openai-key',
            'NEW_GITHUB_TOKEN': 'github-token'
        }):
            results = token_rotator.rotate_tokens(['all'])
        
        assert len(results) == 5  # jira, openai, github, jwt, database
        token_types = {r.token_type for r in results}
        assert token_types == {'jira', 'openai', 'github', 'jwt', 'database'}
    
    def test_generate_report(self, token_rotator):
        """Test report generation."""
        token_rotator.rotation_log = [
            RotationResult(
                token_type='jira',
                success=True,
                timestamp=datetime.now().isoformat(),
                old_token_last4='1234',
                new_token_last4='5678'
            ),
            RotationResult(
                token_type='openai',
                success=False,
                timestamp=datetime.now().isoformat(),
                error='Test error'
            )
        ]
        
        report = token_rotator.generate_report()
        
        assert 'Token Rotation Report' in report
        assert 'staging' in report
        assert 'JIRA: ✅ SUCCESS' in report
        assert 'OPENAI: ❌ FAILED' in report
        assert '1/2 successful' in report
        assert 'Test error' in report
    
    def test_save_audit_log(self, token_rotator, tmp_path):
        """Test audit log saving."""
        token_rotator.rotation_log = [
            RotationResult(
                token_type='jira',
                success=True,
                timestamp=datetime.now().isoformat()
            )
        ]
        
        log_file = tmp_path / "audit.json"
        token_rotator.save_audit_log(str(log_file))
        
        assert log_file.exists()
        
        import json
        with open(log_file) as f:
            data = json.load(f)
        
        assert data['environment'] == 'staging'
        assert data['dry_run'] is True
        assert len(data['results']) == 1
        assert data['results'][0]['token_type'] == 'jira'


class TestRotationResult:
    """Tests for RotationResult dataclass."""
    
    def test_rotation_result_success(self):
        """Test RotationResult for successful rotation."""
        result = RotationResult(
            token_type='jira',
            success=True,
            timestamp='2024-01-01T00:00:00Z',
            old_token_last4='1234',
            new_token_last4='5678'
        )
        
        assert result.token_type == 'jira'
        assert result.success is True
        assert result.error is None
    
    def test_rotation_result_failure(self):
        """Test RotationResult for failed rotation."""
        result = RotationResult(
            token_type='openai',
            success=False,
            timestamp='2024-01-01T00:00:00Z',
            error='Connection timeout'
        )
        
        assert result.token_type == 'openai'
        assert result.success is False
        assert result.error == 'Connection timeout'


class TestTokenRotationError:
    """Tests for TokenRotationError exception."""
    
    def test_token_rotation_error(self):
        """Test TokenRotationError exception."""
        error = TokenRotationError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
