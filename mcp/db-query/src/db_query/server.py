from __future__ import annotations

from contextlib import asynccontextmanager
from enum import Enum

from fastmcp import Context, FastMCP

from .config import load_config
from .connections import ConnectionManager
from .exceptions import DbQueryError
from .models import (
    AggregationFunc,
    ApiResponse,
    ColumnInfo,
    FilterCondition,
    OrderByClause,
    QueryResult,
    TableInfo,
)
from .query_engine import QueryEngine

# ── Load config early to build db_name Enum for tool signatures ────────

_configs = load_config()
_db_names = sorted(_configs.keys())

if _db_names:
    _DbNameEnum = Enum("_DbNameEnum", {n: n for n in _db_names})  # type: ignore[misc]
    _default_db: _DbNameEnum | None = list(_DbNameEnum)[0]
else:
    _DbNameEnum = str  # type: ignore[assignment]
    _default_db = None


# ── Lifespan ────────────────────────────────────────────────────────────


@asynccontextmanager
async def db_lifespan(server: FastMCP):
    ConnectionManager.initialize(_configs)
    try:
        yield
    finally:
        await ConnectionManager.close_all()


# ── FastMCP server ──────────────────────────────────────────────────────

mcp = FastMCP(
    "db-query",
    instructions=(
        "Structured read-only database query service. "
        "Use list_tables and describe_table to discover the schema first, "
        "then query_table with structured parameters (filters, ordering, "
        "aggregations, pagination) to retrieve data. "
        "Single-table queries only. "
        "Supports MySQL, PostgreSQL, and Oracle."
    ),
    lifespan=db_lifespan,
)


# ── Tools ───────────────────────────────────────────────────────────────


@mcp.tool
async def query_table(
    ctx: Context,
    db_name: _DbNameEnum = _default_db,
    table: str = "",
    columns: list[str] | None = None,
    filters: list[FilterCondition] | None = None,
    order_by: list[OrderByClause] | None = None,
    aggregations: list[AggregationFunc] | None = None,
    group_by: list[str] | None = None,
    limit: int = 500,
    offset: int | None = None,
) -> ApiResponse:
    """Query a single table with structured parameters. No SQL needed.

    Typical workflow:
    1. list_tables — discover tables and their purposes via comments
    2. describe_table(table="users") — see columns, types, nullable, keys
    3. query_table(table="users", columns=["name","email"],
       filters=[{"column":"status","operator":"eq","value":"active"}],
       order_by=[{"column":"name","direction":"asc"}])

    Use aggregations for statistics:
      query_table(table="orders", columns=["status"],
        aggregations=[{"function":"sum","column":"amount","alias":"total"}],
        group_by=["status"])

    Parameters:
        db_name: Which database to query. Available options are shown in the enum.
        table: Name of the table. Get valid names from list_tables.
        columns: Column names to return. Omit or pass null to get all columns.
        filters: List of filter conditions combined with AND.
            Each has: column (use exact name from describe_table),
            operator (eq/neq/gt/gte/lt/lte/like/in/is_null/is_not_null),
            value (type must match the column's SQL type from describe_table).
        order_by: Sort order. Each has: column name, direction (asc or desc).
        aggregations: Summary functions. Each has: function (count/sum/avg/min/max),
            column (omit for COUNT(*)), and optional alias.
        group_by: Column names to group by. Use when combining regular
            columns with aggregation functions.
        limit: Maximum rows to return. Default 500. Capped at 500.
        offset: Number of rows to skip (for pagination).
    """
    if not table or not table.strip():
        return ApiResponse(success=False, message="table is required and must not be blank.", data=None)
    if limit < 1:
        return ApiResponse(success=False, message=f"limit must be at least 1, got {limit}.", data=None)
    if offset is not None and offset < 0:
        return ApiResponse(success=False, message=f"offset must be >= 0, got {offset}.", data=None)

    try:
        result = await QueryEngine.execute_structured(
            db_name=_db_value(db_name),
            table=table,
            columns=columns,
            filters=filters,
            order_by=order_by,
            aggregations=aggregations,
            group_by=group_by,
            limit=limit,
            offset=offset,
        )
        # Build summary message from result
        parts = [f"Returned {result.row_count} row{'s' if result.row_count != 1 else ''}"]
        if result.truncated:
            parts.append(
                "⚠️ Results truncated — the query matched more rows "
                "than the limit allows. Narrow filters or increase limit "
                "to see the complete data."
            )
        if result.row_count == 0:
            parts.append("No rows matched the query — try broader filters.")
        parts.append(f"in {result.elapsed_ms}ms")
        return ApiResponse(
            success=True,
            message=" ".join(parts),
            data=result,
        )
    except DbQueryError as e:
        return ApiResponse(success=False, message=str(e), data=None)


@mcp.tool
async def list_tables(
    ctx: Context,
    db_name: _DbNameEnum = _default_db,
) -> ApiResponse:
    """List all tables in the database with their descriptions.

    Call this first when exploring a database. The comment field
    explains what each table is for — use it to pick the right
    table before calling describe_table or query_table.

    Parameters:
        db_name: Database connection to inspect.
    """
    tables = await QueryEngine.list_tables(_db_value(db_name))
    return ApiResponse(
        success=True,
        message=f"Found {len(tables)} table{'s' if len(tables) != 1 else ''}",
        data=tables,
    )


@mcp.tool
async def describe_table(
    ctx: Context,
    db_name: _DbNameEnum = _default_db,
    table: str = "",
) -> ApiResponse:
    """Get the schema of a table: column names, types, nullable, and keys.

    Call this after choosing a table via list_tables. Use the returned
    column names and types to build query_table arguments — filter values
    must match the column's SQL type (string for VARCHAR, number for INTEGER, etc.).

    Parameters:
        db_name: Database connection to inspect.
        table: Name of the table. Get valid names from list_tables.
    """
    if not table or not table.strip():
        return ApiResponse(success=False, message="table is required and must not be blank.", data=None)
    cols = await QueryEngine.describe_table(_db_value(db_name), table)
    return ApiResponse(
        success=True,
        message=f"Table {table!r} has {len(cols)} column{'s' if len(cols) != 1 else ''}",
        data=cols,
    )


# ── Helpers ─────────────────────────────────────────────────────────────


def _db_value(db_name: _DbNameEnum | str) -> str:
    """Extract the string value from a db_name parameter."""
    if isinstance(db_name, Enum):
        return db_name.value
    return str(db_name)


# ── Entry point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import atexit
    import signal

    atexit.register(ConnectionManager.close_all_sync)
    signal.signal(signal.SIGINT, lambda s, f: (ConnectionManager.close_all_sync(), exit(0)))
    signal.signal(signal.SIGTERM, lambda s, f: (ConnectionManager.close_all_sync(), exit(0)))

    mcp.run(transport="stdio")
