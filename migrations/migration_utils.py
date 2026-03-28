import sqlalchemy as sa
from alembic import op


def fmt_ix(table: str, columns: list[str]) -> str:
    cols_str = "_".join(columns)
    return f"ix__{table}__{cols_str}"


def fmt_uq(table: str, columns: list[str]) -> str:
    cols_str = "_".join(columns)
    return f"uq__{table}__{cols_str}"


def fmt_ck(table: str, constraint_name: str) -> str:
    return f"ck__{table}__{constraint_name}"


def fmt_pk(table: str) -> str:
    return f"pk__{table}"


def fmt_fk(table: str, columns: list[str], referred_table: str) -> str:
    cols_str = "_".join(columns)
    return f"fk__{table}__{cols_str}__{referred_table}"


def is_column_not_null(conn, table: str, column: str) -> bool:
    query = sa.text(
        "SELECT attnotnull FROM pg_attribute "
        "WHERE attrelid = :table\:\:regclass AND attname = :column"
    )
    return bool(conn.execute(query, {"table": table, "column": column}).scalar())


def get_constraint_status(conn, name: str) -> str:
    query = sa.text("SELECT convalidated FROM pg_constraint WHERE conname = :name")
    res = conn.execute(query, {"name": name}).fetchone()
    if res is None:
        return "none"
    return "validated" if res[0] else "not_validated"


def get_index_status(conn, name: str) -> str:
    query = sa.text(
        "SELECT i.indisvalid FROM pg_class c "
        "JOIN pg_index i ON c.oid = i.indexrelid "
        "WHERE c.relname = :name AND c.relkind = 'i'"
    )
    res = conn.execute(query, {"name": name}).fetchone()
    if res is None:
        return "none"
    return "ready" if res[0] else "invalid"


def drop_index_concurrently(index_name: str):
    op.execute("COMMIT")
    op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {index_name}")


def drop_constraint_safe(table: str, constraint: str):
    op.execute(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS "{constraint}"')
