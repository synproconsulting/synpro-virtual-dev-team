"""Tests for password hashing functionality."""

import pytest
from src.auth.password_hasher import PasswordHasher


class TestPasswordHasher:
    """Test cases for PasswordHasher class."""
    
    def test_generate_salt(self) -> None:
        """Test salt generation."""
        hasher = PasswordHasher()
        salt1 = hasher.generate_salt()
        salt2 = hasher.generate_salt()
        
        assert salt1 != salt2
        assert len(salt1) == 64  # 32 bytes = 64 hex chars
        assert len(salt2) == 64
    
    def test_hash_password_deterministic(self) -> None:
        """Test that same password and salt produce same hash."""
        hasher = PasswordHasher()
        password = "testpassword123"
        salt = hasher.generate_salt()
        
        hash1 = hasher.hash_password(password, salt)
        hash2 = hasher.hash_password(password, salt)
        
        assert hash1 == hash2
    
    def test_hash_password_different_salts(self) -> None:
        """Test that different salts produce different hashes."""
        hasher = PasswordHasher()
        password = "testpassword123"
        
        salt1 = hasher.generate_salt()
        salt2 = hasher.generate_salt()
        
        hash1 = hasher.hash_password(password, salt1)
        hash2 = hasher.hash_password(password, salt2)
        
        assert hash1 != hash2
    
    def test_hash_new_password(self) -> None:
        """Test generating hash and salt for new password."""
        hasher = PasswordHasher()
        password = "mypassword123"
        
        password_hash, salt = hasher.hash_new_password(password)
        
        assert len(password_hash) == 64  # SHA256 = 32 bytes = 64 hex chars
        assert len(salt) == 64
    
    def test_verify_password_correct(self) -> None:
        """Test password verification with correct password."""
        hasher = PasswordHasher()
        password = "correctpassword"
        
        password_hash, salt = hasher.hash_new_password(password)
        result = hasher.verify_password(password, password_hash, salt)
        
        assert result is True
    
    def test_verify_password_incorrect(self) -> None:
        """Test password verification with incorrect password."""
        hasher = PasswordHasher()
        password = "correctpassword"
        wrong_password = "wrongpassword"
        
        password_hash, salt = hasher.hash_new_password(password)
        result = hasher.verify_password(wrong_password, password_hash, salt)
        
        assert result is False
    
    def test_custom_iterations(self) -> None:
        """Test hasher with custom iteration count."""
        hasher = PasswordHasher(iterations=100000)
        password = "testpassword"
        
        password_hash, salt = hasher.hash_new_password(password)
        result = hasher.verify_password(password, password_hash, salt)
        
        assert result is True
