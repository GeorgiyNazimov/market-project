"""rename order total column to total_price

Revision ID: b3007c62d51b
Revises: 74dfd6ac44be
Create Date: 2026-03-10 22:10:37.335924

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3007c62d51b"
down_revision: Union[str, None] = "74dfd6ac44be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("orders", "total", new_column_name="total_price")


def downgrade() -> None:
    op.alter_column("orders", "total_price", new_column_name="total")
