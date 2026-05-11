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
    op.add_column('products', sa.Column('railway_dev_service_id', sa.String(255), nullable=True))
    op.add_column('products', sa.Column('railway_test_service_id', sa.String(255), nullable=True))
    op.add_column('products', sa.Column('railway_prod_service_id', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('products', 'railway_prod_service_id')
    op.drop_column('products', 'railway_test_service_id')
    op.drop_column('products', 'railway_dev_service_id')
