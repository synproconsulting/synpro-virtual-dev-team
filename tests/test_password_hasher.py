"""
Unit tests for password hashing functionality.
"""
import pytest
from src.auth.password_hasher import PasswordHasher


class TestPasswordHasher:
    """Test cases for PasswordHasher."""
    
    def test_hash_password(self):
        """Test that password hashing works."""
        hasher = PasswordHasher()
        password = "TestPassword123!"
        
        hashed = hasher.hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
    
    def test_hash_password_different_each_time(self):
        """Test that hashing same password produces different hashes (salt)."""
        hasher = PasswordHasher()
        password = "TestPassword123!"
        
        hash1 = hasher.hash_password(password)
        hash2 = hasher.hash_password(password)
        
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Test that correct password verification works."""
        hasher = PasswordHasher()
        password = "TestPassword123!"
        
        hashed = hasher.hash_password(password)
        result = hasher.verify_password(password, hashed)
        
        assert result is True
    
    def test_verify_password_incorrect(self):
        """Test that incorrect password is rejected."""
        hasher = PasswordHasher()
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        
        hashed = hasher.hash_password(password)
        result = hasher.verify_password(wrong_password, hashed)
        
        assert result is False
    
    def test_verify_password_case_sensitive(self):
        """Test that password verification is case sensitive."""
        hasher = PasswordHasher()
        password = "TestPassword123!"
        
        hashed = hasher.hash_password(password)
        result = hasher.verify_password("testpassword123!", hashed)
        
        assert result is False
