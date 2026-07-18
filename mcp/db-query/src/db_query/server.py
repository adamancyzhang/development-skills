from __future__ import annotations

from contextlib import asynccontextmanager

from fastmcp import Context, FastMCP

from .config import load_config
from .connections import ConnectionManager
from .exceptions import DbQueryError
from .models import AggregationFunc, FilterCondition, OrderByClause
from .query_engine import QueryEngine


@asynccontextmanager
async def db_lifespan(server: FastMCP):
    configs = load_config()
    ConnectionManager.initialize(configs)
    try:
        yield
    finally:
        await ConnectionManager.close_all()


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


@mcp.tool
async def query_table(
    ctx: Context,
    table: str,
    db_name: str = "default",
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
        db_name: Database connection name (default: "default").
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
            db_name=db_name,
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
async def list_databases(ctx: Context) -> list[dict]:
    """List all configured database connections with their table counts."""
    names = ConnectionManager.list_databases()
    result = []
    for name in names:
        try:
            tables = await QueryEngine.list_tables(name)
            count = len(tables)
        except Exception:
            count = -1
        result.append({"name": name, "tables_count": count})
    return result


@mcp.tool
async def list_tables(
    ctx: Context,
    db_name: str = "default",
) -> list[str]:
    """List all tables in a configured database.

    Parameters:
        db_name: Database connection name
    """
    return await QueryEngine.list_tables(db_name)


@mcp.tool
async def describe_table(
    ctx: Context,
    db_name: str = "default",
    table_name: str = "",
) -> list[dict]:
    """Describe the columns of a table.

    Returns column name, type, nullable flag, and primary key status.

    Parameters:
        db_name: Database connection name
        table_name: Name of the table to describe
    """
    cols = await QueryEngine.describe_table(db_name, table_name)
    return [c.model_dump() for c in cols]


if __name__ == "__main__":
    import atexit
    import signal

    atexit.register(ConnectionManager.close_all_sync)
    # Handle SIGINT/SIGTERM gracefully: run sync cleanup then re-raise
    signal.signal(signal.SIGINT, lambda s, f: (ConnectionManager.close_all_sync(), exit(0)))
    signal.signal(signal.SIGTERM, lambda s, f: (ConnectionManager.close_all_sync(), exit(0)))

    mcp.run(transport="stdio")
