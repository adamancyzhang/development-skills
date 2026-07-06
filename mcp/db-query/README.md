# DB Query MCP Server

MCP server that lets LLMs query databases securely using standard SQL syntax. The LLM writes queries without knowing the specific database instance or dialect — the server parses, validates, normalizes, and executes them against configured databases.

## Supported Databases

| Database | Driver | Dialect |
|---|---|---|
| PostgreSQL | asyncpg | `postgresql` |
| MySQL | aiomysql | `mysql` |
| Oracle | oracledb | `oracle` |

## Quick Start

### Installation

```bash
cd mcp/db-query
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[all]"
```

Install only the driver you need:

```bash
pip install -e ".[postgresql]"   # PostgreSQL only
pip install -e ".[mysql]"        # MySQL only
pip install -e ".[oracle]"       # Oracle only
```

### Configuration

Configure database connections via environment variables:

```bash
# Required: at least one DB_<NAME>_URL
export DB_DEFAULT_URL=postgresql+asyncpg://user:pass@host:5432/mydb
export DB_ANALYTICS_URL=mysql+aiomysql://user:pass@host:3306/analytics
export DB_LEGACY_URL=oracle+oracledb://user:pass@host:1521/SERVICENAME

# Optional: per-connection settings
export DB_DEFAULT_MAX_ROWS=500       # Max rows per query (default: 100)
export DB_DEFAULT_POOL_SIZE=10       # Connection pool size (default: 5)
export DB_DEFAULT_POOL_OVERFLOW=20   # Pool overflow (default: 10)
```

### Running

```bash
source .venv/bin/activate
python -m db_query.server
```

### Claude Desktop Configuration

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "db-query": {
      "command": "python",
      "args": ["-m", "db_query.server"],
      "env": {
        "DB_DEFAULT_URL": "postgresql+asyncpg://user:pass@host:5432/mydb"
      }
    }
  }
}
```

### Claude Code Configuration

Add to `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "db-query": {
      "command": "python",
      "args": ["-m", "db_query.server"],
      "env": {
        "DB_DEFAULT_URL": "postgresql+asyncpg://user:pass@host:5432/mydb",
        "DB_ANALYTICS_URL": "mysql+aiomysql://user:pass@host:3306/analytics"
      }
    }
  }
}
```

## MCP Tools

### `query_database`

Execute a read-only SQL query. Supports JOINs, subqueries, aggregations, CTEs, and window functions.

```
Parameters:
  sql      — SQL query text (standard SQL syntax)
  db_name  — Database connection name (default: "default")
```

Returns:
```json
{
  "columns": ["id", "name", "email"],
  "rows": [[1, "Alice", "alice@example.com"], [2, "Bob", "bob@example.com"]],
  "row_count": 2,
  "truncated": false,
  "elapsed_ms": 12.3,
  "query_id": "a1b2c3d4e5f6"
}
```

### `list_databases`

List all configured database connections with their SQL dialects and table counts.

### `list_tables`

List all tables in a database.

```
Parameters:
  db_name  — Database connection name (default: "default")
```

### `describe_table`

Describe the columns of a table (name, type, nullable, primary key).

```
Parameters:
  db_name     — Database connection name (default: "default")
  table_name  — Name of the table
```

### `get_dialect_info`

Get the SQL dialect and database version for a connection.

## Query Pipeline

```
LLM writes SQL text
       ↓
mo-sql-parsing parse() → JSON parse tree (standard IR)
       ↓
validate_parse_tree() — reject INSERT/UPDATE/DELETE/DROP/etc.
       ↓
enforce row limit in parse tree
       ↓
mo-sql-parsing format() → canonical SQL (discards original, eliminates injection)
       ↓
dialect adaptation (Oracle: LIMIT → FETCH FIRST N ROWS ONLY)
       ↓
SQLAlchemy text() execute in READ ONLY transaction
       ↓
return {columns, rows, row_count, truncated, elapsed_ms, query_id}
```

## Security

Read-only enforcement is applied at multiple layers:

| Layer | Mechanism |
|---|---|
| Parse-tree validation | Reject parse trees with write-operation top-level keys |
| SQL reformatting | Discard original SQL, rebuild from parse tree |
| Transaction READ ONLY | `SET TRANSACTION READ ONLY` before each query |
| Row limit | Hard-cap results via LIMIT injection |
| Database user | User should have read-only permissions (out of band) |

## Internal JSON Representation

The server uses [mo-sql-parsing](https://pypi.org/project/mo-sql-parsing/) parse trees as the standard intermediate JSON format. Example:

```json
{
  "select": [{"value": "u.name"}, {"value": "o.total"}],
  "from": [
    {"value": "users", "name": "u"},
    {"inner join": {"value": "orders", "name": "o"}, "on": {"eq": ["u.id", "o.user_id"]}}
  ],
  "where": {"gt": ["o.total", 100]},
  "orderby": [{"value": "o.total", "sort": "desc"}],
  "limit": 10
}
```

## Development

```bash
pip install -e ".[dev]"
pytest -v
```
