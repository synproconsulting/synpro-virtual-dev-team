"""Add products table for multi-product virtual dev team configuration.

Revision ID: 002
Revises: 001
Create Date: 2026-04-29

Replaces the e-commerce product schema (from initial SDT1-51 implementation)
with the correct virtual dev team configuration schema: each product maps a
software project to its Jira project key, GitHub repo, and optional Railway
and SonarCloud integration identifiers.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.has_table(bind, 'products'):
        return
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('jira_project_key', sa.String(50), nullable=False),
        sa.Column('github_repo', sa.String(255), nullable=False),
        sa.Column('railway_service_id', sa.String(255), nullable=True),
        sa.Column('sonarcloud_key', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    if not bind.dialect.has_table(bind, 'products'):
        return
    op.drop_index(op.f('ix_products_name'), table_name='products')
    op.drop_table('products')