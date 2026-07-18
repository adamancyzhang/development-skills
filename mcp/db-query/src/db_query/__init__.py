"""MCP server for structured read-only database queries.

Supports MySQL, PostgreSQL, and Oracle via SQLAlchemy.
LLMs use structured query parameters (filters, ordering, aggregations);
the server generates and executes SQL internally.
"""

__version__ = "0.1.0"
