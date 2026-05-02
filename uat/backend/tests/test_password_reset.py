"""Tests for password reset functionality."""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException

from auth import (
    request_password_reset,
    complete_password_reset,
    ResetRequestModel,
    ResetCompleteModel,
    hash_password,
)


class MockCursor:
    """Mock database cursor."""
    
    def __init__(self):
        self.queries = []
        self.results = []
        self.result_index = 0
    
    def execute(self, query: str, params: tuple = ()):
        """Record executed query."""
        self.queries.append((query, params))
    
    def fetchone(self):
        """Return mocked result."""
        if self.result_index < len(self.results):
            result = self.results[self.result_index]
            self.result_index += 1
            return result
        return None
    
    def set_results(self, results: list):
        """Set mock results for fetchone calls."""
        self.results = results
        self.result_index = 0


class MockDB:
    """Mock database connection."""
    
    def __init__(self):
        self.cursor_instance = MockCursor()
        self.committed = False
    
    def cursor(self):
        """Return mock cursor."""
        return self.cursor_instance
    
    def commit(self):
        """Mark as committed."""
        self.committed = True


@pytest.fixture
def mock_db():
    """Provide a mock database connection."""
    return MockDB()


@pytest.mark.asyncio
async def test_request_password_reset_existing_user(mock_db):
    """Test password reset request for existing user sends email."""
    # Setup
    user_id = str(uuid.uuid4())
    email = "test@example.com"
    mock_db.cursor_instance.set_results([
        {"id": user_id}  # User exists
    ])
    
    request = ResetRequestModel(email=email)
    
    # Mock email service
    with patch("auth.send_password_reset_email", new_callable=AsyncMock) as mock_send_email:
        mock_send_email.return_value = True
        
        # Execute
        response = await request_password_reset(request, db=mock_db)
        
        # Verify
        assert response.message == "If that email exists in our system, a password reset link has been sent"
        assert mock_db.committed is True
        
        # Check that email was sent
        assert mock_send_email.called
        call_args = mock_send_email.call_args
        assert call_args[0][0] == email.lower()  # Email address
        assert isinstance(call_args[0][1], str)  # Token
        assert len(call_args[0][1]) == 36  # UUID format
        
        # Verify database queries
        queries = mock_db.cursor_instance.queries
        assert len(queries) == 2
        assert "SELECT id FROM users WHERE email = %s" in queries[0][0]
        assert "INSERT INTO password_reset_tokens" in queries[1][0]


@pytest.mark.asyncio
async def test_request_password_reset_token_not_in_response(mock_db):
    """
    SECURITY TEST (SDT1-62): Verify reset token is NEVER returned in API response.
    
    This test explicitly verifies that the password reset token is not exposed
    in the API response body. The token should only be sent via email.
    """
    # Setup
    user_id = str(uuid.uuid4())
    email = "security-test@example.com"
    mock_db.cursor_instance.set_results([
        {"id": user_id}
    ])
    
    request = ResetRequestModel(email=email)
    
    # Mock email service and capture the token that was generated
    captured_token = None
    
    async def capture_token(to_email: str, reset_token: str) -> bool:
        nonlocal captured_token
        captured_token = reset_token
        return True
    
    with patch("auth.send_password_reset_email", new_callable=AsyncMock) as mock_send_email:
        mock_send_email.side_effect = capture_token
        
        # Execute
        response = await request_password_reset(request, db=mock_db)
        
        # CRITICAL SECURITY CHECK: Token must NOT be in response
        assert hasattr(response, 'message'), "Response should only have 'message' field"
        assert not hasattr(response, 'token'), "Response must NOT contain 'token' field"
        assert not hasattr(response, 'reset_token'), "Response must NOT contain 'reset_token' field"
        
        # Verify the response is a simple message only
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response.dict()
        assert list(response_dict.keys()) == ['message'], "Response should only contain 'message' key"
        assert 'token' not in str(response_dict).lower(), "Token must not appear anywhere in response"
        
        # Verify token was generated (captured from email call) but not in response
        assert captured_token is not None, "Token should have been generated"
        assert captured_token not in str(response_dict), "Token value must not be in response"
        assert len(captured_token) == 36, "Token should be UUID format"


@pytest.mark.asyncio
async def test_request_password_reset_nonexistent_user(mock_db):
    """Test password reset request for non-existent user does not send email."""
    # Setup
    email = "nonexistent@example.com"
    mock_db.cursor_instance.set_results([
        None  # User does not exist
    ])
    
    request = ResetRequestModel(email=email)
    
    # Mock email service
    with patch("auth.send_password_reset_email", new_callable=AsyncMock) as mock_send_email:
        # Execute
        response = await request_password_reset(request, db=mock_db)
        
        # Verify - same message for security (prevent email enumeration)
        assert response.message == "If that email exists in our system, a password reset link has been sent"
        assert mock_db.committed is False
        
        # Check that email was NOT sent
        assert not mock_send_email.called
        
        # Verify only SELECT query was executed
        queries = mock_db.cursor_instance.queries
        assert len(queries) == 1
        assert "SELECT id FROM users WHERE email = %s" in queries[0][0]


@pytest.mark.asyncio
async def test_request_password_reset_nonexistent_user_no_token_in_response(mock_db):
    """
    SECURITY TEST (SDT1-62): Verify no token in response even for non-existent users.
    """
    # Setup
    email = "nonexistent@example.com"
    mock_db.cursor_instance.set_results([None])
    
    request = ResetRequestModel(email=email)
    
    # Execute (no email mock needed - shouldn't be called)
    response = await request_password_reset(request, db=mock_db)
    
    # CRITICAL: Verify response structure - message only, no token
    response_dict = response.model_dump() if hasattr(response, 'model_dump') else response.dict()
    assert list(response_dict.keys()) == ['message']
    assert 'token' not in response_dict
    assert 'reset_token' not in response_dict


@pytest.mark.asyncio
async def test_request_password_reset_email_failure(mock_db):
    """Test password reset request handles email sending failure gracefully."""
    # Setup
    user_id = str(uuid.uuid4())
    email = "test@example.com"
    mock_db.cursor_instance.set_results([
        {"id": user_id}
    ])
    
    request = ResetRequestModel(email=email)
    
    # Mock email service to fail
    with patch("auth.send_password_reset_email", new_callable=AsyncMock) as mock_send_email:
        mock_send_email.return_value = False
        
        # Execute
        response = await request_password_reset(request, db=mock_db)
        
        # Verify - still returns success to prevent info leakage
        assert response.message == "If that email exists in our system, a password reset link has been sent"
        assert mock_db.committed is True


def test_complete_password_reset_success(mock_db):
    """Test successful password reset completion."""
    # Setup
    token = str(uuid.uuid4())
    token_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    mock_db.cursor_instance.set_results([
        {
            "id": token_id,
            "user_id": user_id,
            "expires_at": expires_at,
            "used": False
        }
    ])
    
    request = ResetCompleteModel(
        token=token,
        new_password="NewPassword123!"
    )
    
    # Execute
    response = complete_password_reset(request, db=mock_db)
    
    # Verify
    assert response.message == "Password reset successfully"
    assert mock_db.committed is True
    
    # Verify database queries
    queries = mock_db.cursor_instance.queries
    assert len(queries) == 3
    assert "SELECT t.id, t.user_id, t.expires_at, t.used" in queries[0][0]
    assert "UPDATE users SET password_hash" in queries[1][0]
    assert "UPDATE password_reset_tokens SET used = TRUE" in queries[2][0]


def test_complete_password_reset_invalid_token(mock_db):
    """Test password reset with invalid token."""
    # Setup
    mock_db.cursor_instance.set_results([None])  # Token not found
    
    request = ResetCompleteModel(
        token="invalid-token",
        new_password="NewPassword123!"
    )
    
    # Execute & Verify
    with pytest.raises(HTTPException) as exc_info:
        complete_password_reset(request, db=mock_db)
    
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid reset token"
    assert mock_db.committed is False


def test_complete_password_reset_used_token(mock_db):
    """Test password reset with already used token."""
    # Setup
    token = str(uuid.uuid4())
    token_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    mock_db.cursor_instance.set_results([
        {
            "id": token_id,
            "user_id": user_id,
            "expires_at": expires_at,
            "used": True  # Token already used
        }
    ])
    
    request = ResetCompleteModel(
        token=token,
        new_password="NewPassword123!"
    )
    
    # Execute & Verify
    with pytest.raises(HTTPException) as exc_info:
        complete_password_reset(request, db=mock_db)
    
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Token already used"
    assert mock_db.committed is False


def test_complete_password_reset_expired_token(mock_db):
    """Test password reset with expired token."""
    # Setup
    token = str(uuid.uuid4())
    token_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) - timedelta(hours=1)  # Expired
    
    mock_db.cursor_instance.set_results([
        {
            "id": token_id,
            "user_id": user_id,
            "expires_at": expires_at,
            "used": False
        }
    ])
    
    request = ResetCompleteModel(
        token=token,
        new_password="NewPassword123!"
    )
    
    # Execute & Verify
    with pytest.raises(HTTPException) as exc_info:
        complete_password_reset(request, db=mock_db)
    
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Token has expired"
    assert mock_db.committed is False


def test_complete_password_reset_weak_password(mock_db):
    """Test password reset with weak password."""
    # Setup
    token = str(uuid.uuid4())
    token_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    mock_db.cursor_instance.set_results([
        {
            "id": token_id,
            "user_id": user_id,
            "expires_at": expires_at,
            "used": False
        }
    ])
    
    request = ResetCompleteModel(
        token=token,
        new_password="weak"  # Does not meet requirements
    )
    
    # Execute & Verify
    with pytest.raises(HTTPException) as exc_info:
        complete_password_reset(request, db=mock_db)
    
    assert exc_info.value.status_code == 400
    assert "Password requirements not met" in str(exc_info.value.detail)
    assert mock_db.committed is False


@pytest.mark.asyncio
async def test_request_password_reset_case_insensitive_email(mock_db):
    """Test that email is stored and checked in lowercase."""
    # Setup
    user_id = str(uuid.uuid4())
    email = "Test@Example.COM"
    mock_db.cursor_instance.set_results([
        {"id": user_id}
    ])
    
    request = ResetRequestModel(email=email)
    
    # Mock email service
    with patch("auth.send_password_reset_email", new_callable=AsyncMock) as mock_send_email:
        mock_send_email.return_value = True
        
        # Execute
        await request_password_reset(request, db=mock_db)
        
        # Verify email was sent to lowercase version
        call_args = mock_send_email.call_args
        assert call_args[0][0] == email.lower()
        
        # Verify database query used lowercase
        queries = mock_db.cursor_instance.queries
        assert queries[0][1][0] == email.lower()


def test_password_hash_uniqueness():
    """Test that same password generates different hashes (due to salt)."""
    password = "TestPassword123!"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    
    assert hash1 != hash2  # Different salts
    assert ":" in hash1  # Contains salt and hash separated by colon
    assert ":" in hash2


@pytest.mark.asyncio
async def test_request_password_reset_response_model_structure(mock_db):
    """
    SECURITY TEST (SDT1-62): Verify response model only contains 'message' field.
    
    This test ensures the response model is properly restricted and cannot
    accidentally expose sensitive data.
    """
    # Test with existing user
    user_id = str(uuid.uuid4())
    email = "test@example.com"
    mock_db.cursor_instance.set_results([{"id": user_id}])
    request = ResetRequestModel(email=email)
    
    with patch("auth.send_password_reset_email", new_callable=AsyncMock) as mock_send_email:
        mock_send_email.return_value = True
        response = await request_password_reset(request, db=mock_db)
        
        # Verify response model structure
        assert hasattr(response, 'message')
        response_fields = list(response.model_dump().keys())
        assert response_fields == ['message'], f"Response should only have 'message' field, got: {response_fields}"


def test_complete_password_reset_response_model_structure(mock_db):
    """
    SECURITY TEST (SDT1-62): Verify complete endpoint response is also message-only.
    """
    token = str(uuid.uuid4())
    token_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    mock_db.cursor_instance.set_results([
        {
            "id": token_id,
            "user_id": user_id,
            "expires_at": expires_at,
            "used": False
        }
    ])
    
    request = ResetCompleteModel(token=token, new_password="NewPassword123!")
    response = complete_password_reset(request, db=mock_db)
    
    # Verify response contains only message
    assert hasattr(response, 'message')
    response_fields = list(response.model_dump().keys())
    assert response_fields == ['message'], f"Response should only have 'message' field, got: {response_fields}"
