"""Redesign products table - per-product credentials and environment model (SDT1-118).

Adds encrypted credential columns and per-environment backend/frontend
service ID columns to the products table.

New columns (all nullable):
    * jira_email
    * jira_api_token_enc
    * github_token_enc
    * anthropic_api_key_enc
    * resend_api_key_enc
    * resend_from_email
    * dev_backend_service_id
    * dev_frontend_service_id
    * test_backend_service_id
    * test_frontend_service_id
    * prod_backend_service_id
    * prod_frontend_service_id

If the legacy ``railway_backend_service_name`` /
``railway_frontend_service_name`` columns from migration 003 exist, their
values are preserved by renaming them to ``dev_backend_service_id`` /
``dev_frontend_service_id`` respectively. The shorter ``railway_backend_service``
/ ``railway_frontend_service`` names are handled the same way for robustness.

Idempotent: every column add and rename is guarded by an existence check
against ``information_schema.columns``, so this migration is safe to run
repeatedly. ``downgrade`` is intentionally a no-op - secret columns are
never dropped automatically, matching the project policy on irreversible
data loss.

Revision ID: 006
Revises: 005
Create Date: 2026-05-13
"""

from typing import Sequence, Set, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(bind, table: str) -> Set[str]:
    """Return the set of existing column names on ``table``."""
    insp = inspect(bind)
    return {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    if not bind.dialect.has_table(bind, "products"):
        return

    cols = _column_names(bind, "products")

    rename_map = [
        ("railway_backend_service_name", "dev_backend_service_id"),
        ("railway_backend_service", "dev_backend_service_id"),
        ("railway_frontend_service_name", "dev_frontend_service_id"),
        ("railway_frontend_service", "dev_frontend_service_id"),
    ]
    for old, new in rename_map:
        if old in cols and new not in cols:
            op.alter_column("products", old, new_column_name=new)
            cols.discard(old)
            cols.add(new)

    new_columns = [
        ("jira_email", sa.String(255)),
        ("jira_api_token_enc", sa.String(1000)),
        ("github_token_enc", sa.String(1000)),
        ("anthropic_api_key_enc", sa.String(1000)),
        ("resend_api_key_enc", sa.String(1000)),
        ("resend_from_email", sa.String(255)),
        ("dev_backend_service_id", sa.String(255)),
        ("dev_frontend_service_id", sa.String(255)),
        ("test_backend_service_id", sa.String(255)),
        ("test_frontend_service_id", sa.String(255)),
        ("prod_backend_service_id", sa.String(255)),
        ("prod_frontend_service_id", sa.String(255)),
    ]
    for name, type_ in new_columns:
        if name not in cols:
            op.add_column("products", sa.Column(name, type_, nullable=True))
            cols.add(name)


def downgrade() -> None:
    pass
