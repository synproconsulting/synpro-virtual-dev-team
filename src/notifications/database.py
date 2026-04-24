"""
Database models and schema for notification storage with SQLAlchemy.
"""

import os
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Enum,
    Text,
    JSON,
    create_engine,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.notifications.models import NotificationStatus, NotificationType


Base = declarative_base()


class NotificationDB(Base):
    """
    SQLAlchemy model for notifications table.
    """
    
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    notification_type = Column(
        Enum(NotificationType, name="notification_type_enum"),
        nullable=False,
    )
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(
        Enum(NotificationStatus, name="notification_status_enum"),
        nullable=False,
        default=NotificationStatus.UNREAD,
        index=True,
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    read_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, nullable=False, default=dict)
    action_url = Column(String(500), nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    
    def __repr__(self) -> str:
        return f"<NotificationDB(id={self.id}, user_id={self.user_id}, title={self.title})>"


def get_database_url() -> str:
    """
    Get database URL from environment variables.
    
    Returns:
        Database connection URL
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Default to SQLite for development
        database_url = "sqlite:///./notifications.db"
    return database_url


def create_database_engine(database_url: Optional[str] = None):
    """
    Create SQLAlchemy engine for database connections.
    
    Args:
        database_url: Optional database URL, uses environment variable if not provided
        
    Returns:
        SQLAlchemy engine instance
    """
    if database_url is None:
        database_url = get_database_url()
    
    engine = create_engine(
        database_url,
        echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
    )
    return engine


def create_tables(engine) -> None:
    """
    Create all database tables.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.create_all(bind=engine)


def get_session_maker(engine):
    """
    Create a session maker for database sessions.
    
    Args:
        engine: SQLAlchemy engine instance
        
    Returns:
        SQLAlchemy session maker
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
