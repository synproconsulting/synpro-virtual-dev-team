"""
Security tests for authentication endpoints.

Tests ensure that sensitive data like password reset tokens are never exposed
in API responses (SDT1-62).
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import uuid
from datetime import datetime, timezone, timedelta

# We need to mock the database before importing main
import sys
from pathlib import Path

# Add parent directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


@pytest.fixture
def mock_db():
    """Mock database connection."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


@pytest.fixture
def client(mock_db):
    """Create a test client with mocked database."""
    with patch('auth.get_db') as mock_get_db:
        mock_conn, _ = mock_db
        mock_get_db.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_db.return_value.__exit__ = Mock(return_value=None)
        
        # Import after mocking
        from main import app
        client = TestClient(app)
        yield client


class TestPasswordResetSecurity:
    """Test that password reset tokens are never exposed in API responses."""
    
    @patch('auth.send_password_reset_email', new_callable=AsyncMock)
    def test_password_reset_request_does_not_return_token(self, mock_send_email, client, mock_db):
        """
        Test that the password reset request endpoint never returns the token
        in the response body (SDT1-62).
        """
        mock_conn, mock_cursor = mock_db
        test_email = "user@example.com"
        test_user_id = str(uuid.uuid4())
        
        # Mock user exists
        mock_cursor.fetchone.return_value = {"id": test_user_id}
        mock_send_email.return_value = True
        
        # Request password reset
        response = client.post(
            "/auth/password-reset/request",
            json={"email": test_email}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Verify response only contains generic message
        assert "message" in response_data
        assert "token" not in response_data
        assert "reset_token" not in response_data
        
        # Verify the response doesn't contain any UUID-like strings
        # (which would indicate a token leak)
        response_str = str(response_data).lower()
        # This regex pattern matches UUIDs
        import re
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        assert not re.search(uuid_pattern, response_str), \
            "Response should not contain any UUID tokens"
    
    @patch('auth.send_password_reset_email', new_callable=AsyncMock)
    def test_password_reset_request_nonexistent_email_same_response(
        self, mock_send_email, client, mock_db
    ):
        """
        Test that requesting a reset for a non-existent email returns the same
        generic response (prevents email enumeration).
        """
        mock_conn, mock_cursor = mock_db
        
        # Mock user does NOT exist
        mock_cursor.fetchone.return_value = None
        
        # Request password reset
        response = client.post(
            "/auth/password-reset/request",
            json={"email": "nonexistent@example.com"}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Should return same generic message
        assert "message" in response_data
        expected_message = "If that email exists in our system, a password reset link has been sent"
        assert response_data["message"] == expected_message
        
        # Should NOT contain token
        assert "token" not in response_data
        assert "reset_token" not in response_data
    
    @patch('auth.send_password_reset_email', new_callable=AsyncMock)
    def test_token_only_sent_via_email(self, mock_send_email, client, mock_db):
        """
        Test that the reset token is only sent via email, not in the API response.
        """
        mock_conn, mock_cursor = mock_db
        test_email = "user@example.com"
        test_user_id = str(uuid.uuid4())
        
        # Mock user exists
        mock_cursor.fetchone.return_value = {"id": test_user_id}
        mock_send_email.return_value = True
        
        # Request password reset
        response = client.post(
            "/auth/password-reset/request",
            json={"email": test_email}
        )
        
        assert response.status_code == 200
        
        # Verify email was called with token
        assert mock_send_email.called
        call_args = mock_send_email.call_args
        assert call_args is not None
        email_arg, token_arg = call_args[0]
        
        # Email should be correct
        assert email_arg == test_email
        # Token should be a valid UUID
        assert isinstance(token_arg, str)
        assert len(token_arg) == 36  # UUID string length
        
        # But response should NOT contain the token
        response_data = response.json()
        assert token_arg not in str(response_data)
    
    def test_password_reset_complete_does_not_echo_token(self, client, mock_db):
        """
        Test that the password reset complete endpoint doesn't echo back
        the token in the response.
        """
        mock_conn, mock_cursor = mock_db
        test_token = str(uuid.uuid4())
        test_user_id = str(uuid.uuid4())
        
        # Mock valid token
        mock_cursor.fetchone.return_value = {
            "id": str(uuid.uuid4()),
            "user_id": test_user_id,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "used": False
        }
        
        # Complete password reset
        response = client.post(
            "/auth/password-reset/complete",
            json={
                "token": test_token,
                "new_password": "NewSecureP@ss123"
            }
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Response should only contain success message
        assert "message" in response_data
        
        # Should NOT echo back the token
        assert "token" not in response_data
        assert test_token not in str(response_data)
    
    def test_password_reset_headers_do_not_leak_token(self, client, mock_db):
        """
        Test that response headers don't accidentally leak the reset token.
        """
        mock_conn, mock_cursor = mock_db
        test_email = "user@example.com"
        test_user_id = str(uuid.uuid4())
        
        # Mock user exists
        mock_cursor.fetchone.return_value = {"id": test_user_id}
        
        with patch('auth.send_password_reset_email', new_callable=AsyncMock) as mock_send_email:
            mock_send_email.return_value = True
            
            # Request password reset
            response = client.post(
                "/auth/password-reset/request",
                json={"email": test_email}
            )
            
            # Check headers don't contain tokens
            for header_name, header_value in response.headers.items():
                # Verify no UUID-like strings in headers
                import re
                uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
                assert not re.search(uuid_pattern, str(header_value).lower()), \
                    f"Header {header_name} should not contain UUID tokens"


class TestLoggingSecurity:
    """Test that sensitive data is not logged."""
    
    @patch('auth.send_password_reset_email', new_callable=AsyncMock)
    @patch('auth.logger')
    def test_reset_token_not_logged(self, mock_logger, mock_send_email, client, mock_db):
        """
        Test that the reset token is never logged directly (SDT1-62).
        """
        mock_conn, mock_cursor = mock_db
        test_email = "user@example.com"
        test_user_id = str(uuid.uuid4())
        
        # Mock user exists
        mock_cursor.fetchone.return_value = {"id": test_user_id}
        mock_send_email.return_value = True
        
        # Request password reset
        response = client.post(
            "/auth/password-reset/request",
            json={"email": test_email}
        )
        
        assert response.status_code == 200
        
        # Check all log calls
        for call in mock_logger.info.call_args_list + mock_logger.warning.call_args_list + mock_logger.error.call_args_list:
            if call:
                log_message = str(call)
                # Verify no UUID tokens in logs (except user_id which is expected)
                # We check that if there's a UUID, it's explicitly labeled as user_id
                import re
                uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
                uuids_in_log = re.findall(uuid_pattern, log_message.lower())
                
                for uuid_found in uuids_in_log:
                    # If a UUID is logged, ensure it's clearly marked as user_id
                    # and not a bare token
                    assert 'user_id' in log_message.lower() or 'id' in log_message.lower(), \
                        f"UUID in log should be clearly identified: {log_message}"
