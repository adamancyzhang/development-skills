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

Create `databases.yaml` from the example:

```bash
cp databases.yaml.example databases.yaml
```

Each entry is an independent data source — add as many as you need. The name is yours to choose:

```yaml
databases:
  main:
    host: 127.0.0.1
    port: 5431
    user: ainowork
    password: Abc@1234
    database: ainowork
    max_rows: 500
    pool_size: 10
    pool_overflow: 20

  analytics:
    host: 127.0.0.1
    port: 5432
    user: reader
    password: secret
    database: analytics
```

- `type` defaults to `postgresql`; also supports `mysql` and `oracle`
- `max_rows` defaults to 500, `pool_size` to 5, `pool_overflow` to 10
- MySQL uses `database`; Oracle uses `service_name` instead

To use a custom file path, set `DB_CONFIG_PATH` in `.env` or the environment:

```bash
DB_CONFIG_PATH=/path/to/my-databases.yaml
```

## Transport Modes

The server is a standard FastMCP application. All [FastMCP settings](https://gofastmcp.com/deployment/settings)
are read from `FASTMCP_`-prefixed env vars or `.env`. Key settings:

```bash
# .env
FASTMCP_TRANSPORT=stdio                # stdio (default) | http | sse | streamable-http
FASTMCP_HOST=127.0.0.1                 # only for http / sse / streamable-http
FASTMCP_PORT=8000                      # only for http / sse / streamable-http
FASTMCP_STATELESS_HTTP=false           # if true, new transport per request (no session state)
```

| `FASTMCP_TRANSPORT` | Endpoint | Notes |
|---|---|---|
| `stdio` | — | Subprocess I/O (default) |
| `sse` | `/sse` + `/messages/` | SSE over HTTP. Best for older clients. |
| `http` | `/mcp` | Streamable HTTP (alias for `streamable-http`). |
| `streamable-http` | `/mcp` | Streamable HTTP (2024-11-05). Requires `Accept: application/json, text/event-stream`. |

If no YAML file is found, the server falls back to `.env`-style environment variables.

### Running

```bash
# stdio (default)
uv run python -m db_query.server

# sse
FASTMCP_TRANSPORT=sse uv run python -m db_query.server
# → http://127.0.0.1:8000/sse

# streamable-http
FASTMCP_TRANSPORT=streamable-http uv run python -m db_query.server
# → http://127.0.0.1:8000/mcp
```

### Claude Desktop Configuration

#### stdio mode

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

#### HTTP mode

Set `FASTMCP_TRANSPORT=sse` (or `streamable-http`) in `.env`, start the server:

```json
{
  "mcpServers": {
    "db-query": {
      "url": "http://127.0.0.1:8000/sse"
    }
  }
}
```

### Claude Code Configuration

Add to `.claude/settings.local.json`:

#### stdio mode

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

#### HTTP mode

```json
{
  "mcpServers": {
    "db-query": {
      "type": "http",
      "url": "http://127.0.0.1:8000/sse"
    }
  }
}
```

## MCP Tools

### `query_table`

Query a single table using structured, database-agnostic parameters. No SQL knowledge required — the LLM fills in typed fields and the server generates and executes SQL internally.

```
Parameters:
  table        — Name of the table to query
  db_name      — Database connection name (default: "default")
  columns      — Columns to select. None or empty → all columns (*)
  filters      — WHERE conditions (column, operator, value)
  order_by     — ORDER BY clauses (column, direction: asc/desc)
  aggregations — COUNT, SUM, AVG, MIN, MAX
  group_by     — Columns to GROUP BY
  limit        — Max rows to return (server cap: 500)
  offset       — Rows to skip before returning results
```

Filter operators: `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `like`, `in`, `is_null`, `is_not_null`

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

List all configured database connections with their table counts.

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

## Query Pipeline

```
LLM fills structured query parameters (typed, no SQL)
       ↓
sql_builder.build_select_tree() → mo-sql-parsing tree
       ↓
validate_parse_tree() — always SELECT
       ↓
enforce row limit in parse tree
       ↓
mo-sql-parsing format() → canonical SQL
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
