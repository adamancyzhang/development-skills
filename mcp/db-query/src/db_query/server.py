from __future__ import annotations

from contextlib import asynccontextmanager

from fastmcp import Context, FastMCP
from sqlalchemy import text

from .config import load_config
from .connections import ConnectionManager
from .exceptions import DbQueryError
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
        "Secure read-only database query service. "
        "Write standard SQL syntax; the server validates, normalizes, "
        "and executes queries against configured databases. "
        "Supports MySQL, PostgreSQL, and Oracle. "
        "Use list_tables and describe_table to discover the schema first, "
        "then query_database to execute SELECT queries with JOINs, "
        "aggregations, subqueries, CTEs, and window functions."
    ),
    lifespan=db_lifespan,
)


@mcp.tool
async def query_database(
    ctx: Context,
    sql: str,
    db_name: str = "default",
) -> dict:
    """Execute a read-only SQL query on a configured database.

    Write standard SQL syntax. JOINs, subqueries, aggregations, CTEs,
    and window functions are supported. Only SELECT statements are allowed.

    Parameters:
        sql: SQL query text (standard SQL-like syntax)
        db_name: Database connection name (matches DB_<NAME>_URL env var)
    """
    try:
        result = await QueryEngine.execute(db_name, sql)
        return result.model_dump(mode="json")
    except DbQueryError as e:
        return {
            "error": e.status_code,
            "detail": str(e),
            "query_id": e.query_id,
        }


@mcp.tool
async def list_databases(ctx: Context) -> list[dict]:
    """List all configured database connections with their SQL dialects."""
    names = ConnectionManager.list_databases()
    result = []
    for name in names:
        dialect = ConnectionManager.get_dialect(name)
        try:
            tables = await QueryEngine.list_tables(name)
            count = len(tables)
        except Exception:
            count = -1
        result.append({"name": name, "dialect": dialect, "tables_count": count})
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


@mcp.tool
async def get_dialect_info(
    ctx: Context,
    db_name: str = "default",
) -> dict:
    """Get the SQL dialect and database version for a connection.

    Parameters:
        db_name: Database connection name
    """
    from .query_engine import DIALECTS_WITH_READ_ONLY

    dialect = ConnectionManager.get_dialect(db_name)
    engine = ConnectionManager.get_engine(db_name)
    async with engine.connect() as conn:
        if dialect in DIALECTS_WITH_READ_ONLY:
            await conn.execute(text("SET TRANSACTION READ ONLY"))
        result = await conn.execute(text("SELECT version()"))
        version = result.scalar()
    return {"name": db_name, "dialect": dialect, "version": str(version)}


if __name__ == "__main__":
    import atexit
    import signal

    atexit.register(ConnectionManager.close_all_sync)
    # Handle SIGINT/SIGTERM gracefully: run sync cleanup then re-raise
    signal.signal(signal.SIGINT, lambda s, f: (ConnectionManager.close_all_sync(), exit(0)))
    signal.signal(signal.SIGTERM, lambda s, f: (ConnectionManager.close_all_sync(), exit(0)))

    mcp.run(transport="stdio")
