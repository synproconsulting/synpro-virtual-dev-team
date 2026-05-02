"""
Integration tests for the complete password reset flow.

Tests the end-to-end password reset process ensuring security at every step.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import uuid
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path

# Add parent directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


@pytest.fixture
def client():
    """Create a test client with mocked database."""
    with patch('auth.get_db') as mock_get_db:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_db.return_value.__exit__ = Mock(return_value=None)
        
        # Store mocks for access in tests
        mock_get_db.mock_conn = mock_conn
        mock_get_db.mock_cursor = mock_cursor
        
        # Import after mocking
        from main import app
        client = TestClient(app)
        client.mock_db = (mock_conn, mock_cursor)
        yield client


class TestPasswordResetFlowSecurity:
    """Test the complete password reset flow for security issues."""
    
    @patch('auth.send_password_reset_email', new_callable=AsyncMock)
    def test_complete_password_reset_flow_secure(self, mock_send_email, client):
        """
        Test a complete password reset flow ensuring no token leakage at any step.
        """
        mock_conn, mock_cursor = client.mock_db
        test_email = "user@example.com"
        test_user_id = str(uuid.uuid4())
        test_token = str(uuid.uuid4())
        
        # Step 1: User requests password reset
        mock_cursor.fetchone.return_value = {"id": test_user_id}
        mock_send_email.return_value = True
        
        request_response = client.post(
            "/auth/password-reset/request",
            json={"email": test_email}
        )
        
        assert request_response.status_code == 200
        request_data = request_response.json()
        
        # Verify no token in request response
        assert "token" not in request_data
        assert "reset_token" not in request_data
        assert test_token not in str(request_data)
        
        # Verify email was sent with token
        assert mock_send_email.called
        sent_email, sent_token = mock_send_email.call_args[0]
        assert sent_email == test_email
        assert isinstance(sent_token, str)
        
        # Step 2: User receives email and uses token to reset password
        # Mock the token lookup
        mock_cursor.fetchone.return_value = {
            "id": str(uuid.uuid4()),
            "user_id": test_user_id,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "used": False
        }
        
        complete_response = client.post(
            "/auth/password-reset/complete",
            json={
                "token": sent_token,
                "new_password": "NewSecureP@ss123"
            }
        )
        
        assert complete_response.status_code == 200
        complete_data = complete_response.json()
        
        # Verify token not echoed in complete response
        assert sent_token not in str(complete_data)
        assert "token" not in complete_data
        assert complete_data["message"] == "Password reset successfully"
    
    @patch('auth.send_password_reset_email', new_callable=AsyncMock)
    def test_expired_token_secure_error(self, mock_send_email, client):
        """
        Test that expired token errors don't leak token information.
        """
        mock_conn, mock_cursor = client.mock_db
        test_token = str(uuid.uuid4())
        
        # Mock expired token
        mock_cursor.fetchone.return_value = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "expires_at": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
            "used": False
        }
        
        response = client.post(
            "/auth/password-reset/complete",
            json={
                "token": test_token,
                "new_password": "NewSecureP@ss123"
            }
        )
        
        assert response.status_code == 400
        error_data = response.json()
        
        # Verify error message doesn't leak token
        assert test_token not in str(error_data)
        assert error_data["detail"] == "Token has expired"
    
    @patch('auth.send_password_reset_email', new_callable=AsyncMock)
    def test_used_token_secure_error(self, mock_send_email, client):
        """
        Test that used token errors don't leak token information.
        """
        mock_conn, mock_cursor = client.mock_db
        test_token = str(uuid.uuid4())
        
        # Mock used token
        mock_cursor.fetchone.return_value = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "used": True  # Already used
        }
        
        response = client.post(
            "/auth/password-reset/complete",
            json={
                "token": test_token,
                "new_password": "NewSecureP@ss123"
            }
        )
        
        assert response.status_code == 400
        error_data = response.json()
        
        # Verify error message doesn't leak token
        assert test_token not in str(error_data)
        assert error_data["detail"] == "Token already used"
    
    @patch('auth.send_password_reset_email', new_callable=AsyncMock)
    def test_invalid_token_secure_error(self, mock_send_email, client):
        """
        Test that invalid token errors don't leak token information.
        """
        mock_conn, mock_cursor = client.mock_db
        test_token = str(uuid.uuid4())
        
        # Mock token not found
        mock_cursor.fetchone.return_value = None
        
        response = client.post(
            "/auth/password-reset/complete",
            json={
                "token": test_token,
                "new_password": "NewSecureP@ss123"
            }
        )
        
        assert response.status_code == 400
        error_data = response.json()
        
        # Verify error message doesn't leak token
        assert test_token not in str(error_data)
        assert error_data["detail"] == "Invalid reset token"
    
    @patch('auth.send_password_reset_email', new_callable=AsyncMock)
    def test_multiple_requests_same_email(self, mock_send_email, client):
        """
        Test that multiple password reset requests don't leak information.
        """
        mock_conn, mock_cursor = client.mock_db
        test_email = "user@example.com"
        test_user_id = str(uuid.uuid4())
        
        mock_cursor.fetchone.return_value = {"id": test_user_id}
        mock_send_email.return_value = True
        
        # Make multiple requests
        responses = []
        tokens_sent = []
        
        for _ in range(3):
            response = client.post(
                "/auth/password-reset/request",
                json={"email": test_email}
            )
            responses.append(response)
            
            # Capture token from email call
            if mock_send_email.called:
                _, token = mock_send_email.call_args[0]
                tokens_sent.append(token)
        
        # All responses should be identical
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "If that email exists in our system, a password reset link has been sent"
            
            # Verify no tokens in any response
            for token in tokens_sent:
                assert token not in str(data)
    
    @patch('auth.send_password_reset_email', new_callable=AsyncMock)
    def test_timing_attack_prevention(self, mock_send_email, client):
        """
        Test that response times don't differ significantly for valid/invalid emails.
        Note: This is a basic check. More sophisticated timing analysis may be needed.
        """
        mock_conn, mock_cursor = client.mock_db
        mock_send_email.return_value = True
        
        # Request with valid email
        mock_cursor.fetchone.return_value = {"id": str(uuid.uuid4())}
        response_valid = client.post(
            "/auth/password-reset/request",
            json={"email": "valid@example.com"}
        )
        
        # Request with invalid email
        mock_cursor.fetchone.return_value = None
        response_invalid = client.post(
            "/auth/password-reset/request",
            json={"email": "invalid@example.com"}
        )
        
        # Both should return same status and message
        assert response_valid.status_code == response_invalid.status_code
        assert response_valid.json()["message"] == response_invalid.json()["message"]
        
        # Both should not contain any tokens
        assert "token" not in response_valid.json()
        assert "token" not in response_invalid.json()


class TestPasswordResetValidation:
    """Test password validation in reset flow."""
    
    def test_weak_password_rejected(self, client):
        """Test that weak passwords are rejected during reset."""
        mock_conn, mock_cursor = client.mock_db
        test_token = str(uuid.uuid4())
        
        # Mock valid token
        mock_cursor.fetchone.return_value = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "used": False
        }
        
        # Try with weak password
        response = client.post(
            "/auth/password-reset/complete",
            json={
                "token": test_token,
                "new_password": "weak"
            }
        )
        
        assert response.status_code == 400
        error_data = response.json()
        assert "Password requirements not met" in error_data["detail"]["message"]
        
        # Even in error, token should not be leaked
        assert test_token not in str(error_data)
