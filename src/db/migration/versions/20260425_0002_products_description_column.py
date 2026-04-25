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
    op.alter_column("products", "body_text", new_column_name="description")
    op.drop_column("products", "body_html")


def downgrade() -> None:
    op.add_column("products", sa.Column("body_html", sa.Text(), nullable=True))
    op.alter_column("products", "description", new_column_name="body_text")
