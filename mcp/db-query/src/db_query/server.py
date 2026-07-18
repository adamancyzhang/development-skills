from __future__ import annotations

from contextlib import asynccontextmanager
from enum import Enum

from fastmcp import Context, FastMCP

from .config import load_config
from .connections import ConnectionManager
from .exceptions import DbQueryError
from .models import AggregationFunc, FilterCondition, OrderByClause
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
) -> dict:
    """Query a single table using structured, database-agnostic parameters.

    Specify columns, filter conditions, sort order, aggregations,
    grouping, and pagination. The server generates and executes SQL
    internally — no SQL knowledge needed.

    Parameters:
        table: Name of the table to query.
        db_name: Database connection to query.
        columns: Columns to select. None or empty means all columns (*).
        filters: WHERE conditions. Each has column, operator, and value.
        order_by: ORDER BY clauses with column and direction (asc/desc).
        aggregations: Aggregation functions (count, sum, avg, min, max).
            Set column=None with function=count for COUNT(*).
        group_by: Columns to GROUP BY when using aggregations.
        limit: Max rows to return (server-enforced cap applies).
        offset: Rows to skip before returning results.
    """
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
        return result.model_dump(mode="json")
    except DbQueryError as e:
        return {
            "error": e.status_code,
            "detail": str(e),
            "query_id": e.query_id,
        }


@mcp.tool
async def list_tables(
    ctx: Context,
    db_name: _DbNameEnum = _default_db,
) -> list[dict]:
    """List all tables with their comments.

    Returns each table's name and database-native comment
    (COMMENT ON TABLE in PostgreSQL). LLMs can use the
    comment to understand what each table represents.

    Parameters:
        db_name: Database connection to inspect.
    """
    return await QueryEngine.list_tables(_db_value(db_name))


@mcp.tool
async def describe_table(
    ctx: Context,
    db_name: _DbNameEnum = _default_db,
    table_name: str = "",
) -> list[dict]:
    """Describe the columns of a table.

    Returns column name, type, nullable flag, and primary key status.

    Parameters:
        db_name: Database connection to inspect.
        table_name: Name of the table to describe.
    """
    cols = await QueryEngine.describe_table(_db_value(db_name), table_name)
    return [c.model_dump() for c in cols]


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
