"""add product created_at id index

Revision ID: 942fae266fd2
Revises: 7f2cca8f2586
Create Date: 2026-05-18 19:27:04.890874

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migrations.migration_utils import create_index_concurrently, drop_index_concurrently, fmt_ix, get_index_status


# revision identifiers, used by Alembic.
revision: str = '942fae266fd2'
down_revision: Union[str, None] = '7f2cca8f2586'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLE = "products"
COLUMNS = ["created_at", "id"]
INDEX_NAME = fmt_ix(TABLE, COLUMNS)

COLUMNS_WITH_DESC = ["created_at DESC NULLS LAST", "id DESC"]

def upgrade() -> None:
    conn = op.get_bind()

    status = get_index_status(conn, INDEX_NAME)

    if status == "invalid":
        drop_index_concurrently(INDEX_NAME)
        status = "none"

    if status == "none":
        create_index_concurrently(TABLE, INDEX_NAME, COLUMNS_WITH_DESC)


def downgrade() -> None:
    drop_index_concurrently(INDEX_NAME)