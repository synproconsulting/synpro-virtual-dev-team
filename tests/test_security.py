"""
Tests for security utilities.
"""

import pytest
from datetime import timedelta
from src.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    generate_reset_token
)


def test_hash_password():
    """Test password hashing."""
    password = "TestPassword123!"
    hashed = hash_password(password)
    
    assert hashed != password
    assert len(hashed) > 0
    assert hashed.startswith("$2b$")  # bcrypt hash prefix


def test_verify_password_correct():
    """Test password verification with correct password."""
    password = "TestPassword123!"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    """Test password verification with incorrect password."""
    password = "TestPassword123!"
    wrong_password = "WrongPassword123!"
    hashed = hash_password(password)
    
    assert verify_password(wrong_password, hashed) is False


def test_create_access_token():
    """Test JWT token creation."""
    data = {"sub": "user@example.com"}
    token = create_access_token(data)
    
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_with_expiration():
    """Test JWT token creation with custom expiration."""
    data = {"sub": "user@example.com"}
    expires_delta = timedelta(minutes=15)
    token = create_access_token(data, expires_delta)
    
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_access_token_valid():
    """Test decoding a valid JWT token."""
    data = {"sub": "user@example.com"}
    token = create_access_token(data)
    
    decoded = decode_access_token(token)
    
    assert decoded is not None
    assert decoded["sub"] == "user@example.com"
    assert "exp" in decoded


def test_decode_access_token_invalid():
    """Test decoding an invalid JWT token."""
    invalid_token = "invalid.jwt.token"
    
    decoded = decode_access_token(invalid_token)
    
    assert decoded is None


def test_generate_reset_token():
    """Test reset token generation."""
    token1 = generate_reset_token()
    token2 = generate_reset_token()
    
    assert isinstance(token1, str)
    assert isinstance(token2, str)
    assert len(token1) == 64  # 32 bytes as hex = 64 characters
    assert len(token2) == 64
    assert token1 != token2  # Each token should be unique
