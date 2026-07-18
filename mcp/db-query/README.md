# DB Query MCP Server

MCP server that lets LLMs query databases securely using standard SQL syntax. The LLM writes queries without knowing the specific database instance or dialect — the server parses, validates, normalizes, and executes them against configured databases.

## Supported Databases

| Database | Driver | Dialect |
|---|---|---|
| PostgreSQL | asyncpg | `postgresql` |
| MySQL | aiomysql | `mysql` |
| Oracle | oracledb | `oracle` |

## Quick Start

### Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager and venv manager

### Installation

```bash
cd mcp/db-query
uv sync                              # core dependencies only
uv sync --extra postgresql           # + PostgreSQL driver
uv sync --extra mysql                # + MySQL driver
uv sync --extra oracle               # + Oracle driver
uv sync --all-extras                 # all drivers + dev tools
```

### Configuration

Copy the example file and edit it:

```bash
cp .env.example .env
```

The `.env` file uses friendly per-database environment variables. PostgreSQL is the default:

```bash
# PostgreSQL (connection name: "default")
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5431
POSTGRES_USER=ainowork
POSTGRES_PASSWORD=Abc@1234
POSTGRES_DB=ainowork

# MySQL (connection name: "mysql") — uncomment to enable
# MYSQL_HOST=127.0.0.1
# MYSQL_PORT=3306
# MYSQL_USER=root
# MYSQL_PASSWORD=your_password
# MYSQL_DB=mydb

# Oracle (connection name: "oracle") — uncomment to enable
# ORACLE_HOST=127.0.0.1
# ORACLE_PORT=1521
# ORACLE_USER=scott
# ORACLE_PASSWORD=tiger
# ORACLE_SERVICE_NAME=XEPDB1
```

Optional per-connection overrides:

```bash
DB_DEFAULT_MAX_ROWS=500       # Max rows per query (default: 100)
DB_DEFAULT_POOL_SIZE=10       # Connection pool size (default: 5)
DB_DEFAULT_POOL_OVERFLOW=20   # Pool overflow (default: 10)
```

#### Advanced: explicit SQLAlchemy URLs

Friendly vars are the recommended way. If you need a SQLAlchemy URL directly (e.g. custom driver or query params), set `DB_<NAME>_URL` — it takes precedence over friendly vars for the same connection name:

```bash
DB_DEFAULT_URL=postgresql+asyncpg://user:pass@host:5432/mydb
DB_ANALYTICS_URL=mysql+aiomysql://user:pass@host:3306/analytics
DB_LEGACY_URL=oracle+oracledb://user:pass@host:1521/SERVICENAME
```

### Running

```bash
uv run python -m db_query.server
```

### Claude Desktop Configuration

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "db-query": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp/db-query", "python", "-m", "db_query.server"]
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
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp/db-query", "python", "-m", "db_query.server"]
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
uv sync --all-extras
uv run pytest -v
```
