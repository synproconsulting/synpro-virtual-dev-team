"""
Password hashing utilities using industry-standard algorithms.
"""
from passlib.context import CryptContext


class PasswordHasher:
    """
    Handles password hashing and verification using bcrypt.
    
    Uses passlib with bcrypt for secure password hashing.
    """
    
    def __init__(self):
        """Initialize the password context with bcrypt."""
        self.context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12,  # Cost factor for bcrypt
        )
    
    def hash_password(self, password: str) -> str:
        """
        Hash a plaintext password.
        
        Args:
            password: The plaintext password to hash
            
        Returns:
            The hashed password string
        """
        return self.context.hash(password)
    
    def verify_password(self, plaintext: str, hashed: str) -> bool:
        """
        Verify a plaintext password against a hash.
        
        Args:
            plaintext: The plaintext password to verify
            hashed: The hashed password to verify against
            
        Returns:
            True if password matches, False otherwise
        """
        return self.context.verify(plaintext, hashed)
