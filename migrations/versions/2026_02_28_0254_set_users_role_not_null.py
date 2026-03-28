"""set users role not null

Revision ID: 74dfd6ac44be
Revises: a74d2cb02f7d
Create Date: 2026-02-28 02:54:45.622524

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from migrations.migration_utils import (
    drop_constraint_safe,
    drop_index_concurrently,
    fmt_ck,
    fmt_ix,
    get_constraint_status,
    get_index_status,
    is_column_not_null,
)

# revision identifiers, used by Alembic.
revision: str = "74dfd6ac44be"
down_revision: Union[str, None] = "a74d2cb02f7d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "users"
COLUMN = "role"
DATA_MIGRATION_NAME = "2026_02_25_1908_set_default_roles_for_users.py"
RAW_CONSTRAINT = f"check_{COLUMN}_not_null"
DB_CONSTRAINT = fmt_ck(TABLE, RAW_CONSTRAINT)
TMP_INDEX = fmt_ix(TABLE, [COLUMN, "nulls", "tmp"])


def upgrade() -> None:
    conn = op.get_bind()

    column_not_null = is_column_not_null(conn, TABLE, COLUMN)

    if not column_not_null:
        idx_status = get_index_status(conn, TMP_INDEX)
        if idx_status == "invalid":
            drop_index_concurrently(TMP_INDEX)
            idx_status = "none"

        if idx_status == "none":
            op.execute("COMMIT")
            op.execute(
                f"CREATE INDEX CONCURRENTLY {TMP_INDEX} ON {TABLE} ({COLUMN}) "
                f"WHERE {COLUMN} IS NULL"
            )

        has_nulls = conn.execute(
            sa.text(f"SELECT 1 FROM {TABLE} WHERE {COLUMN} IS NULL LIMIT 1")
        ).scalar()

        if has_nulls:
            raise Exception(
                f"\n[MIGRATION ERROR]: Найдено нарушение целостности данных в {TABLE}.{COLUMN}.\n"
                f"Для продолжения необходимо заполнить NULL-значения.\n"
                f"ЗАПУСТИТЕ МИГРАЦИЮ ДАННЫХ: python migrations/data_migrations/{DATA_MIGRATION_NAME}"
            )

        c_status = get_constraint_status(conn, DB_CONSTRAINT)
        if c_status == "none":
            op.execute(
                f'ALTER TABLE {TABLE} ADD CONSTRAINT "{DB_CONSTRAINT}" '
                f"CHECK ({COLUMN} IS NOT NULL) NOT VALID"
            )
            op.execute("COMMIT")
            c_status = "not_validated"

        if c_status == "not_validated":
            op.execute(f'ALTER TABLE {TABLE} VALIDATE CONSTRAINT "{DB_CONSTRAINT}"')
            op.execute("COMMIT")

    op.alter_column(TABLE, COLUMN, nullable=False)

    drop_constraint_safe(TABLE, DB_CONSTRAINT)
    drop_index_concurrently(TMP_INDEX)


def downgrade() -> None:
    op.alter_column(TABLE, COLUMN, nullable=True)
