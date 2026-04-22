"""
Tests for password hashing utilities.
"""

import pytest
from src.auth.password_hasher import hash_password, verify_password


class TestPasswordHasher:
    """Test cases for password hashing."""
    
    def test_hash_password(self):
        """Test that password hashing works."""
        password = "MySecurePassword123!"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
    
    def test_hash_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "SamePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Bcrypt uses salt, so hashes should be different
        assert hash1 != hash2
    
    def test_verify_correct_password(self):
        """Test that correct password verification works."""
        password = "CorrectPassword123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """Test that incorrect password verification fails."""
        password = "CorrectPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "Password123!"
        hashed = hash_password(password)
        
        assert verify_password("password123!", hashed) is False
        assert verify_password("PASSWORD123!", hashed) is False
