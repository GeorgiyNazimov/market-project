"""add review (user_id, product_id) index

Revision ID: 101591bfdf8f
Revises: b3007c62d51b
Create Date: 2026-04-18 23:08:16.585726

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from migrations.migration_utils import (
    create_index_concurrently,
    drop_index_concurrently,
    fmt_ix,
    get_index_status,
)

# revision identifiers, used by Alembic.
revision: str = "101591bfdf8f"
down_revision: Union[str, None] = "b3007c62d51b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLUMNS = ["user_id", "product_id"]
TABLE = "reviews"
INDEX_NAME = fmt_ix(TABLE, COLUMNS)


def upgrade() -> None:
    conn = op.get_bind()

    status = get_index_status(conn, INDEX_NAME)

    if status == "invalid":
        drop_index_concurrently(INDEX_NAME)
        status = "none"

    if status == "none":
        create_index_concurrently(TABLE, INDEX_NAME, COLUMNS)


def downgrade() -> None:
    drop_index_concurrently(INDEX_NAME)
