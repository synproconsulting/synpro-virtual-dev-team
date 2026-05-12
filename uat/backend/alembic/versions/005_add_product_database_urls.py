"""Add per-environment database URLs to products table (SDT1-99).

Each product can now store separate PostgreSQL connection strings for its DEV,
TEST, and PROD environments. These connection strings are used by the migrate
endpoint to run Alembic against product-specific databases, keeping data
isolated across products and environments.

Revision ID: 005
Revises: 004
Create Date: 2026-05-11
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('ALTER TABLE products ADD COLUMN IF NOT EXISTS db_url_dev VARCHAR(1000)')
    op.execute('ALTER TABLE products ADD COLUMN IF NOT EXISTS db_url_test VARCHAR(1000)')
    op.execute('ALTER TABLE products ADD COLUMN IF NOT EXISTS db_url_prod VARCHAR(1000)')


def downgrade() -> None:
    op.execute('ALTER TABLE products DROP COLUMN IF EXISTS db_url_prod')
    op.execute('ALTER TABLE products DROP COLUMN IF EXISTS db_url_test')
    op.execute('ALTER TABLE products DROP COLUMN IF EXISTS db_url_dev')