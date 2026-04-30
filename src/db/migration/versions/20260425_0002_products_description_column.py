"""Rename product body_text to description and drop body_html

Revision ID: 20260425_0002
Revises: 20260425_0001
Create Date: 2026-04-25 00:30:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260425_0002"
down_revision: Union[str, None] = "20260425_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # First migration already creates description column directly,
    # so this is now a no-op for fresh installs.
    # Keeping the migration file for history/rollback compatibility.
    pass


def downgrade() -> None:
    pass