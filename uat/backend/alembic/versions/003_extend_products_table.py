"""Extend products table with full multi-product configuration columns (SDT1-95).

Adds jira_base_url, github_org, railway_project_id,
railway_backend_service_name, and railway_frontend_service_name columns
to the products table created in migration 002.

Revision ID: 003
Revises: 002
Create Date: 2026-05-09
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if not bind.dialect.has_table(bind, 'products'):
        return
    op.add_column('products', sa.Column('jira_base_url', sa.String(500), nullable=True))
    op.add_column('products', sa.Column('github_org', sa.String(255), nullable=True))
    op.add_column('products', sa.Column('railway_project_id', sa.String(255), nullable=True))
    op.add_column('products', sa.Column('railway_backend_service_name', sa.String(255), nullable=True))
    op.add_column('products', sa.Column('railway_frontend_service_name', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('products', 'railway_frontend_service_name')
    op.drop_column('products', 'railway_backend_service_name')
    op.drop_column('products', 'railway_project_id')
    op.drop_column('products', 'github_org')
    op.drop_column('products', 'jira_base_url')
