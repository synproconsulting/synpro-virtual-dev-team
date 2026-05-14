"""Add jira_board_id column to products table (SDT1-121).

Each product needs its own Jira Agile board ID so the
``/proxy/jira/sprints`` endpoint can fetch the correct native sprints
and graft their state / start / end dates onto the version-based sprint
list. Without it the proxy cannot tell which board belongs to which
product and falls through to returning version-only data with no
``active`` state recognition.

The new column is a nullable ``VARCHAR(50)`` - board IDs are numeric but
arrive from Jira as strings in some endpoints, so we keep the column
flexible. The proxy converts to ``int`` at read time.

Idempotent: the column add is guarded by an existence check against
``information_schema.columns`` (via SQLAlchemy ``inspect``), so this
migration is safe to re-run. ``downgrade`` is intentionally a no-op,
matching the project policy of never auto-dropping data columns.

Revision ID: 007
Revises: 006
Create Date: 2026-05-14
"""

from typing import Sequence, Set, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "007"
down_revision: Union[str, None] = "006"
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
    if "jira_board_id" not in cols:
        op.add_column(
            "products",
            sa.Column("jira_board_id", sa.String(50), nullable=True),
        )


def downgrade() -> None:
    pass
