"""Password hashing utilities using PBKDF2."""

import hashlib
import secrets
from typing import Tuple


class PasswordHasher:
    """Handles password hashing and verification using PBKDF2-HMAC-SHA256."""
    
    def __init__(self, iterations: int = 600000, salt_length: int = 32) -> None:
        """Initialize password hasher.
        
        Args:
            iterations: Number of PBKDF2 iterations (default: 600000)
            salt_length: Length of salt in bytes (default: 32)
        """
        self.iterations = iterations
        self.salt_length = salt_length
    
    def generate_salt(self) -> str:
        """Generate a cryptographically secure random salt.
        
        Returns:
            Hexadecimal string representation of the salt
        """
        return secrets.token_hex(self.salt_length)
    
    def hash_password(self, password: str, salt: str) -> str:
        """Hash a password with the given salt.
        
        Args:
            password: Plain text password to hash
            salt: Hexadecimal salt string
            
        Returns:
            Hexadecimal string representation of the password hash
        """
        password_bytes = password.encode('utf-8')
        salt_bytes = bytes.fromhex(salt)
        
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password_bytes,
            salt_bytes,
            self.iterations
        )
        
        return hash_bytes.hex()
    
    def hash_new_password(self, password: str) -> Tuple[str, str]:
        """Generate salt and hash for a new password.
        
        Args:
            password: Plain text password
            
        Returns:
            Tuple of (password_hash, salt) as hexadecimal strings
        """
        salt = self.generate_salt()
        password_hash = self.hash_password(password, salt)
        return password_hash, salt
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify a password against a stored hash.
        
        Args:
            password: Plain text password to verify
            password_hash: Stored password hash (hexadecimal)
            salt: Salt used for hashing (hexadecimal)
            
        Returns:
            True if password matches, False otherwise
        """
        computed_hash = self.hash_password(password, salt)
        return secrets.compare_digest(computed_hash, password_hash)
