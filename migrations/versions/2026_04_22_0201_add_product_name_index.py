"""add product name index

Revision ID: 5b316576b7d8
Revises: 101591bfdf8f
Create Date: 2026-04-22 02:01:58.454689

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
revision: str = "5b316576b7d8"
down_revision: Union[str, None] = "101591bfdf8f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "products"
COLUMNS = ["name"]
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
