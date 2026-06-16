"""add fts gin index on recipes instructions

Revision ID: 0e80b1b4dd26
Revises: 78aa2d228591
Create Date: 2026-06-16 17:57:57.555610

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0e80b1b4dd26"
down_revision: str | Sequence[str] | None = "78aa2d228591"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute(
        "CREATE INDEX ix_recipes_instructions_fts "
        "ON recipes USING gin(to_tsvector('english', instructions))"
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.execute("DROP INDEX IF EXISTS ix_recipes_instructions_fts")
