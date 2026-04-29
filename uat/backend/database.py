"""Database configuration and session management.

This module provides database engine, session factory, and connection
utilities for the UAT backend application.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base


def get_database_url() -> str:
    """Get database URL from environment variables.
    
    Returns:
        str: Database connection URL
        
    Raises:
        ValueError: If DATABASE_URL is not set
    """
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Please configure the database connection string."
        )
    
    return database_url


def create_database_engine():
    """Create SQLAlchemy engine with database URL.
    
    Returns:
        Engine: SQLAlchemy engine instance
    """
    database_url = get_database_url()
    
    # Handle PostgreSQL URL variations
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    
    return engine


# Create engine and session factory
engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database() -> None:
    """Initialize database by creating all tables.
    
    This function creates all tables defined in the models
    if they don't already exist.
    """
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session dependency.
    
    This function is designed to be used as a FastAPI dependency
    to provide database sessions to route handlers.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def drop_all_tables() -> None:
    """Drop all tables from the database.
    
    Warning: This will delete all data. Use only for testing or development.
    """
    Base.metadata.drop_all(bind=engine)
