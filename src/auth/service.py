"""
Authentication service layer containing business logic.
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
import os

from src.auth.models import User, PasswordResetToken
from src.auth.schemas import UserCreate
from src.auth.security import hash_password, verify_password, generate_reset_token


RESET_TOKEN_EXPIRE_HOURS = int(os.getenv("RESET_TOKEN_EXPIRE_HOURS", "24"))


class AuthService:
    """Service class for authentication operations."""
    
    def __init__(self, db: Session):
        """
        Initialize the auth service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by email address.
        
        Args:
            email: User's email address
            
        Returns:
            User object if found, None otherwise
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user account.
        
        Args:
            user_data: User registration data
            
        Returns:
            Created user object
            
        Raises:
            ValueError: If email already exists
        """
        existing_user = self.get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError("Email already registered")
        
        hashed_password = hash_password(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user
    
    def create_password_reset_token(self, email: str) -> Optional[str]:
        """
        Create a password reset token for a user.
        
        Args:
            email: User's email address
            
        Returns:
            Reset token string if user exists, None otherwise
        """
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        token = generate_reset_token()
        expires_at = datetime.utcnow() + timedelta(hours=RESET_TOKEN_EXPIRE_HOURS)
        
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        
        self.db.add(reset_token)
        self.db.commit()
        return token
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset a user's password using a reset token.
        
        Args:
            token: Password reset token
            new_password: New password to set
            
        Returns:
            True if password was reset, False otherwise
        """
        reset_token = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.utcnow()
        ).first()
        
        if not reset_token:
            return False
        
        user = self.db.query(User).filter(User.id == reset_token.user_id).first()
        if not user:
            return False
        
        user.hashed_password = hash_password(new_password)
        reset_token.used = True
        
        self.db.commit()
        return True
