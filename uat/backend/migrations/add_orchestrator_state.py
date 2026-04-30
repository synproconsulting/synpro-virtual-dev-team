"""
Migration script to add orchestrator_states table.

This script creates the orchestrator_states table for tracking
sprint execution state with resume capability.

Usage:
    python -m migrations.add_orchestrator_state
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from database import engine, init_database
from models import Base, OrchestratorState


def upgrade():
    """Create the orchestrator_states table."""
    print("Creating orchestrator_states table...")
    
    # Create only the OrchestratorState table
    OrchestratorState.__table__.create(engine, checkfirst=True)
    
    print("✓ orchestrator_states table created successfully")


def downgrade():
    """Drop the orchestrator_states table."""
    print("Dropping orchestrator_states table...")
    
    OrchestratorState.__table__.drop(engine, checkfirst=True)
    
    print("✓ orchestrator_states table dropped successfully")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate orchestrator_states table")
    parser.add_argument(
        "--downgrade",
        action="store_true",
        help="Drop the table instead of creating it"
    )
    
    args = parser.parse_args()
    
    if args.downgrade:
        confirm = input("Are you sure you want to drop the orchestrator_states table? (yes/no): ")
        if confirm.lower() == "yes":
            downgrade()
        else:
            print("Migration cancelled")
    else:
        upgrade()
