"""Add search_vector tsvector to products for full-text search

Revision ID: 20260507_0001
Revises: 20260503_0001
Create Date: 2026-05-07 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260507_0001"
down_revision: Union[str, None] = "20260503_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add generated tsvector column for full-text search
    op.execute(
        """
        ALTER TABLE products
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('simple', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('simple', coalesce(vendor, '')), 'B') ||
            setweight(to_tsvector('simple', coalesce(product_type, '')), 'B') ||
            setweight(to_tsvector('simple', coalesce(description, '')), 'C')
        ) STORED
        """
    )

    # Create GIN index for fast full-text search
    op.execute(
        "CREATE INDEX ix_products_search_vector ON products USING GIN (search_vector)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_products_search_vector")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS search_vector")
