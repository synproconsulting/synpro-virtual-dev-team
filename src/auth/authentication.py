"""
Authentication service for user registration, login, and token management.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import bcrypt
from jose import JWTError, jwt

from src.auth.user import User


class AuthService:
    """
    Provides authentication services including registration, login, and JWT token management.
    """
    
    def __init__(self) -> None:
        """Initialize the authentication service with configuration from environment."""
        self.secret_key = os.getenv("JWT_SECRET_KEY", "default-secret-key-change-in-production")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.expiration_minutes = int(os.getenv("JWT_EXPIRATION_MINUTES", "30"))
        self.users_db: Dict[str, User] = {}
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password as a string
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            password_hash: Hashed password to check against
            
        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    
    def register_user(self, email: str, password: str) -> User:
        """
        Register a new user in the system.
        
        Args:
            email: User's email address
            password: User's plain text password
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If email already exists or validation fails
        """
        if email in self.users_db:
            raise ValueError("User with this email already exists")
        
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        user_id = str(uuid.uuid4())
        password_hash = self.hash_password(password)
        
        user = User(
            user_id=user_id,
            email=email,
            password_hash=password_hash,
            created_at=datetime.utcnow()
        )
        
        self.users_db[email] = user
        return user
    
    def authenticate_user(self, email: str, password: str) -> bool:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User's email address
            password: User's plain text password
            
        Returns:
            True if authentication successful, False otherwise
        """
        user = self.users_db.get(email)
        if not user:
            return False
        
        if self.verify_password(password, user.password_hash):
            user.last_login = datetime.utcnow()
            return True
        
        return False
    
    def generate_token(self, user_id: str) -> str:
        """
        Generate a JWT token for a user.
        
        Args:
            user_id: Unique identifier of the user
            
        Returns:
            JWT token as a string
        """
        expiration = datetime.utcnow() + timedelta(minutes=self.expiration_minutes)
        
        payload = {
            "sub": user_id,
            "exp": expiration,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a JWT token and extract its payload.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.
        
        Args:
            email: User's email address
            
        Returns:
            User object if found, None otherwise
        """
        return self.users_db.get(email)
