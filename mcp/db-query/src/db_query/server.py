from __future__ import annotations

from contextlib import asynccontextmanager
from enum import Enum

from fastmcp import Context, FastMCP

from .config import load_config
from .connections import ConnectionManager
from .models import (
    AggregationFunc,
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
    table: str,
    db_name: _DbNameEnum = _default_db,
    columns: list[str] | None = None,
    filters: list[FilterCondition] | None = None,
    order_by: list[OrderByClause] | None = None,
    aggregations: list[AggregationFunc] | None = None,
    group_by: list[str] | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> QueryResult:
    """Query a single table with structured parameters. No SQL needed.

    Typical workflow:
    1. list_tables — discover tables and their purposes via comments
    2. describe_table("users") — see columns, types, nullable, keys
    3. query_table(table="users", columns=["name","email"],
       filters=[{"column":"status","operator":"eq","value":"active"}],
       order_by=[{"column":"name","direction":"asc"}], limit=10)

    Use aggregations for statistics:
      query_table(table="orders", columns=["status"],
        aggregations=[{"function":"sum","column":"amount","alias":"total"}],
        group_by=["status"])

    Parameters:
        table: Name of the table. Get valid names from list_tables.
        db_name: Which database to query. Available options are shown in the enum.
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
        limit: Maximum rows to return. Server cap is 500.
        offset: Number of rows to skip (for pagination).
    """
    return await QueryEngine.execute_structured(
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


@mcp.tool
async def list_tables(
    ctx: Context,
    db_name: _DbNameEnum = _default_db,
) -> list[TableInfo]:
    """List all tables in the database with their descriptions.

    Call this first when exploring a database. The comment field
    explains what each table is for — use it to pick the right
    table before calling describe_table or query_table.

    Parameters:
        db_name: Database connection to inspect.
    """
    return await QueryEngine.list_tables(_db_value(db_name))


@mcp.tool
async def describe_table(
    ctx: Context,
    db_name: _DbNameEnum = _default_db,
    table_name: str = "",
) -> list[ColumnInfo]:
    """Get the schema of a table: column names, types, nullable, and keys.

    Call this after choosing a table via list_tables. Use the returned
    column names and types to build query_table arguments — filter values
    must match the column's SQL type (string for VARCHAR, number for INTEGER, etc.).

    Parameters:
        db_name: Database connection to inspect.
        table_name: Name of the table. Get valid names from list_tables.
    """
    return await QueryEngine.describe_table(_db_value(db_name), table_name)


# ── Helpers ─────────────────────────────────────────────────────────────


def _db_value(db_name: _DbNameEnum | str) -> str:
    """Extract the string value from a db_name parameter.

    When the Enum type is used, FastMCP/Pydantic converts the incoming
    string to an enum member; we extract .value. Falls back to str()
    for the degenerate case where no databases are configured.
    """
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
