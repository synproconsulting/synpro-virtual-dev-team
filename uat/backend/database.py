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


def run_migrations_for_url(db_url: str) -> None:
    """Run Alembic migrations against a specific database URL.

    Used to initialise or upgrade per-product per-environment databases (SDT1-99).
    Requires alembic.ini to be present in the working directory.

    Runbook — adding a new product/environment database:
      1. Create the target PostgreSQL database.
      2. Set db_url_dev / db_url_test / db_url_prod on the product record via PUT /api/products/{id}.
      3. POST /api/products/{product_id}/migrate with ?environment=dev|test|prod.
      4. This function applies all Alembic migrations so all tables exist and are up to date.
      5. Repeat for each environment that needs an isolated database.

    Args:
        db_url: PostgreSQL connection string for the target database.

    Raises:
        Exception: Propagated from Alembic if migrations fail.
    """
    from alembic.config import Config
    from alembic import command

    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")