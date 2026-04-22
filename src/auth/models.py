"""
Database models for user authentication.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    """
    User model representing a registered user in the system.
    
    Attributes:
        id: Primary key
        email: Unique email address
        hashed_password: Bcrypt hashed password
        full_name: User's full name
        is_active: Whether the user account is active
        created_at: Timestamp of account creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PasswordResetToken(Base):
    """
    Password reset token model for managing password reset requests.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to user
        token: Unique reset token
        expires_at: Token expiration timestamp
        used: Whether the token has been used
        created_at: Timestamp of token creation
    """
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
