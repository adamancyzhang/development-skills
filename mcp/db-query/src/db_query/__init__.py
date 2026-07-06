"""MCP server for read-only database queries.

Supports MySQL, PostgreSQL, and Oracle via SQLAlchemy.
LLMs write standard SQL syntax; the server validates, normalizes,
and executes queries against configured databases.
"""

__version__ = "0.1.0"
