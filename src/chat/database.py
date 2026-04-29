"""
Database configuration and session management.

This module provides database connection setup and session management
for the chat system.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base


def get_database_url() -> str:
    """
    Get database URL from environment variables.
    
    Returns:
        Database connection URL
        
    Raises:
        ValueError: If DATABASE_URL is not set
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return database_url


def create_database_engine(database_url: str = None):
    """
    Create a SQLAlchemy engine.
    
    Args:
        database_url: Optional database URL. If not provided, reads from environment
        
    Returns:
        SQLAlchemy Engine instance
    """
    if database_url is None:
        database_url = get_database_url()
    
    # Add connection arguments for PostgreSQL
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    
    engine = create_engine(database_url, connect_args=connect_args)
    return engine


def create_tables(engine) -> None:
    """
    Create all tables in the database.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.create_all(bind=engine)


def get_session_factory(engine):
    """
    Create a session factory bound to an engine.
    
    Args:
        engine: SQLAlchemy engine instance
        
    Returns:
        SessionLocal factory
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session(session_factory) -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    
    Args:
        session_factory: SessionLocal factory
        
    Yields:
        Database session
    """
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
