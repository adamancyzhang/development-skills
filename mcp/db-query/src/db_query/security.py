from __future__ import annotations

from .exceptions import EmptyQueryError, ReadOnlyViolationError

FORBIDDEN_OP_KEYS: frozenset[str] = frozenset({
    "insert",
    "update",
    "delete",
    "drop",
    "create",
    "alter",
    "truncate",
    "replace",
    "merge",
    "call",
    "exec",
    "execute",
    "grant",
    "revoke",
})


def validate_parse_tree(tree: dict) -> None:
    """Validate that the parse tree contains only read operations.

    Checks top-level keys against FORBIDDEN_OP_KEYS using prefix matching
    (e.g., "create table" and "create view" are both detected as "create").
    A SELECT query has "select" as a top-level key; INSERT has "insert", etc.

    Raises ReadOnlyViolationError if any forbidden operation is detected.
    """
    forbidden_found: set[str] = set()
    for key in tree:
        # Check the first word of multi-word keys like "create table"
        first_word = key.split()[0]
        if first_word in FORBIDDEN_OP_KEYS:
            forbidden_found.add(key)

    if forbidden_found:
        raise ReadOnlyViolationError(
            f"Forbidden SQL operation(s): {', '.join(sorted(forbidden_found))}. "
            f"Only SELECT queries are allowed."
        )


def sanitize_sql(sql: str) -> str:
    """Pre-parse sanitization of raw SQL input.

    - Rejects empty or whitespace-only input
    - Strips leading/trailing whitespace
    """
    stripped = sql.strip()
    if not stripped:
        raise EmptyQueryError("SQL query is empty.")
    return stripped


def enforce_row_count(limit: int | None, max_rows: int) -> int:
    """Determine the effective row limit.

    - If no limit in query, uses max_rows
    - If query limit exceeds max_rows, caps at max_rows
    - Otherwise, uses the query's own limit

    Returns the effective limit to apply.
    """
    if limit is None:
        return max_rows
    return min(limit, max_rows)
