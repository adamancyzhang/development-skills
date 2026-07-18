from __future__ import annotations

import re
import time
import uuid

from mo_sql_parsing import format as mo_format
from mo_sql_parsing import parse
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

from .connections import ConnectionManager
from .exceptions import SQLError
from .models import ColumnInfo, QueryResult, TableInfo
from .security import enforce_row_count, sanitize_sql, validate_parse_tree

DIALECTS_WITH_READ_ONLY = frozenset({"postgresql", "mysql", "oracle"})

_LIMIT_OFFSET_RE = re.compile(
    r"\bLIMIT\s+(\d+)(?:\s+OFFSET\s+(\d+))?",
    re.IGNORECASE,
)


class QueryEngine:
    """Core query execution pipeline.

    Pipeline: parse SQL -> validate read-only -> enforce row limit ->
    format canonical SQL -> adapt dialect -> execute -> return results.

    For structured queries, execute_structured() builds the parse tree
    directly instead of parsing user-written SQL.
    """

    @staticmethod
    async def execute(
        db_name: str,
        sql_text: str,
    ) -> QueryResult:
        """Execute raw SQL text. Kept for backward compatibility;
        prefer execute_structured() for new code.
        """
        start = time.monotonic()
        query_id = uuid.uuid4().hex[:12]

        clean_sql = sanitize_sql(sql_text)
        try:
            parse_tree = parse(clean_sql)
        except Exception as e:
            raise SQLError(f"Failed to parse SQL: {e}", query_id=query_id) from e

        validate_parse_tree(parse_tree)

        engine = ConnectionManager.get_engine(db_name)
        dialect_name = ConnectionManager.get_dialect(db_name)
        max_rows = ConnectionManager.get_max_rows(db_name)

        existing_limit = parse_tree.get("limit")
        effective_limit = enforce_row_count(existing_limit, max_rows)
        # Fetch one extra row to detect truncation reliably
        parse_tree["limit"] = effective_limit + 1

        canonical_sql = mo_format(parse_tree)
        adapted_sql = _adapt_for_dialect(canonical_sql, dialect_name)

        try:
            rows, columns = await _execute_sql(engine, adapted_sql, dialect_name)
        except Exception as e:
            raise SQLError(f"Query execution failed: {e}", query_id=query_id) from e

        elapsed = time.monotonic() - start
        truncated = len(rows) > effective_limit
        if truncated:
            rows = rows[:effective_limit]

        return QueryResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            truncated=truncated,
            elapsed_ms=round(elapsed * 1000, 1),
            query_id=query_id,
        )

    @staticmethod
    async def execute_structured(
        db_name: str,
        table: str,
        *,
        columns: list[str] | None = None,
        filters: list | None = None,
        order_by: list | None = None,
        aggregations: list | None = None,
        group_by: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> QueryResult:
        """Execute a structured single-table query.

        Structured parameters are converted to a mo-sql-parsing parse
        tree, then fed through the standard pipeline: validate →
        enforce row limit → format → dialect adapt → execute.
        """
        start = time.monotonic()
        query_id = uuid.uuid4().hex[:12]

        from .sql_builder import build_select_tree

        parse_tree = build_select_tree(
            table=table,
            columns=columns,
            filters=filters,
            order_by=order_by,
            aggregations=aggregations,
            group_by=group_by,
            limit=limit,
            offset=offset,
        )

        validate_parse_tree(parse_tree)

        engine = ConnectionManager.get_engine(db_name)
        dialect_name = ConnectionManager.get_dialect(db_name)
        max_rows = ConnectionManager.get_max_rows(db_name)

        existing_limit = parse_tree.get("limit")
        effective_limit = enforce_row_count(existing_limit, max_rows)
        # Fetch one extra row to detect truncation reliably
        parse_tree["limit"] = effective_limit + 1

        canonical_sql = mo_format(parse_tree)
        adapted_sql = _adapt_for_dialect(canonical_sql, dialect_name)

        try:
            rows, columns = await _execute_sql(engine, adapted_sql, dialect_name)
        except Exception as e:
            raise SQLError(f"Query execution failed: {e}", query_id=query_id) from e

        elapsed = time.monotonic() - start
        truncated = len(rows) > effective_limit
        if truncated:
            rows = rows[:effective_limit]

        return QueryResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            truncated=truncated,
            elapsed_ms=round(elapsed * 1000, 1),
            query_id=query_id,
        )

    @staticmethod
    async def list_tables(db_name: str) -> list[TableInfo]:
        """List all tables with their comments (database-native descriptions)."""
        engine = ConnectionManager.get_engine(db_name)
        async with engine.connect() as conn:

            def _get(sync_conn):
                insp = inspect(sync_conn)
                names = insp.get_table_names()
                result = []
                for name in sorted(names):
                    try:
                        c = insp.get_table_comment(name)
                        comment = (c.get("text") or "") if c else ""
                    except Exception:
                        comment = ""
                    result.append(TableInfo(name=name, comment=comment))
                return result

            return await conn.run_sync(_get)

    @staticmethod
    async def describe_table(
        db_name: str, table_name: str
    ) -> list[ColumnInfo]:
        engine = ConnectionManager.get_engine(db_name)
        async with engine.connect() as conn:
            cols = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_columns(table_name)
            )
            return [
                ColumnInfo(
                    name=c["name"],
                    type=str(c["type"]),
                    nullable=c.get("nullable", True),
                    primary_key=c.get("primary_key", False),
                )
                for c in cols
            ]


async def _execute_sql(
    engine: AsyncEngine, sql: str, dialect: str = "unknown"
) -> tuple[list[list], list[str]]:
    """Execute a SQL string and return (rows, column_names)."""
    async with engine.connect() as conn:
        if dialect in DIALECTS_WITH_READ_ONLY:
            await conn.execute(text("SET TRANSACTION READ ONLY"))
        result = await conn.execute(text(sql))
        columns = list(result.keys())
        rows = [list(row) for row in result.fetchall()]
        return rows, columns


def _adapt_for_dialect(sql: str, dialect: str) -> str:
    """Adapt canonical SQL to database-specific syntax.

    The main adaptation is Oracle's LIMIT clause:
    Oracle 12c+ uses FETCH FIRST / OFFSET ... FETCH NEXT.
    """
    if dialect == "oracle":

        def _replace_limit(m: re.Match) -> str:
            limit = m.group(1)
            offset = m.group(2)
            if offset:
                return f"OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"
            return f"FETCH FIRST {limit} ROWS ONLY"

        return _LIMIT_OFFSET_RE.sub(_replace_limit, sql)
    return sql
