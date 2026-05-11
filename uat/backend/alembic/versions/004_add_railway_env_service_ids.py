"""Add per-environment Railway service IDs to products table (SDT1-98).

Revision ID: 004
Revises: 003
Create Date: 2026-05-11
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('ALTER TABLE products ADD COLUMN IF NOT EXISTS railway_dev_service_id VARCHAR(255)')
    op.execute('ALTER TABLE products ADD COLUMN IF NOT EXISTS railway_test_service_id VARCHAR(255)')
    op.execute('ALTER TABLE products ADD COLUMN IF NOT EXISTS railway_prod_service_id VARCHAR(255)')


def downgrade() -> None:
    op.execute('ALTER TABLE products DROP COLUMN IF EXISTS railway_prod_service_id')
    op.execute('ALTER TABLE products DROP COLUMN IF EXISTS railway_test_service_id')
    op.execute('ALTER TABLE products DROP COLUMN IF EXISTS railway_dev_service_id')