from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    """Standard wrapper for all tool responses."""

    success: bool = Field(description="Whether the operation succeeded")
    message: str = Field(description="Human-readable result summary or error detail")
    data: Any | None = Field(
        default=None,
        description="Response payload — QueryResult, list[TableInfo], or TableSchema",
    )


class QueryResult(BaseModel):
    """Result of a structured query. columns and rows are aligned by index."""

    columns: list[str] = Field(
        description="Column names in the result set. Each column corresponds to the value at the same index in each row."
    )
    rows: list[list[Any]] = Field(
        description="Row data. Each row is a list of values whose positions match the columns array. Values can be strings, numbers, booleans, or null."
    )
    row_count: int = Field(description="Total number of rows returned in this result")
    truncated: bool = Field(
        default=False,
        description="True if the result was cut short by the row limit — more rows exist in the database than were returned.",
    )
    elapsed_ms: float = Field(
        default=0.0, description="Wall-clock time the query took, in milliseconds"
    )
    query_id: str = Field(
        default="", description="Unique 12-character hex identifier for this query"
    )


class ColumnInfo(BaseModel):
    """Schema information for a single table column, as returned by describe_table."""

    name: str = Field(description="Column name as it appears in the database")
    type: str = Field(
        description="SQL data type, e.g. VARCHAR(255), INTEGER, TIMESTAMP, TEXT. Use this to decide filter value types."
    )
    nullable: bool = Field(
        default=True, description="Whether the column accepts NULL values"
    )
    primary_key: bool = Field(
        default=False, description="Whether this column is part of the primary key"
    )


class TableInfo(BaseModel):
    """Table name and its database comment, as returned by list_tables."""

    name: str = Field(description="Table name — use this as the table argument in query_table")
    comment: str = Field(
        default="",
        description="Database-native comment describing the table's purpose. Empty string means no comment was set.",
    )


# ── Rich table schema models (describe_table) ─────────────────────────────


class PrimaryKeyInfo(BaseModel):
    """Primary key constraint for a table."""

    name: str | None = Field(
        default=None,
        description="Name of the primary key constraint. May be None on databases that do not assign a name (e.g. SQLite).",
    )
    column_names: list[str] = Field(
        default_factory=list,
        description="Column(s) that form the primary key. Single-element list for simple PKs, multiple for composite keys.",
    )


class ForeignKeyInfo(BaseModel):
    """A foreign key constraint referencing another table."""

    name: str | None = Field(
        default=None,
        description="Name of the foreign key constraint. May be None if the database does not name it.",
    )
    constrained_columns: list[str] = Field(
        default_factory=list,
        description="Column(s) in this table that reference another table.",
    )
    referred_table: str = Field(
        default="",
        description="The table being referenced by this foreign key.",
    )
    referred_columns: list[str] = Field(
        default_factory=list,
        description="Column(s) in the referenced table, aligned by position with constrained_columns.",
    )
    referred_schema: str | None = Field(
        default=None,
        description="Schema of the referenced table, if different from the current schema.",
    )


class IndexInfo(BaseModel):
    """A database index on one or more columns."""

    name: str | None = Field(
        default=None,
        description="Name of the index. May be None for auto-generated indexes.",
    )
    column_names: list[str] = Field(
        default_factory=list,
        description="Column(s) included in the index, in order.",
    )
    unique: bool = Field(
        default=False,
        description="True if this is a UNIQUE index.",
    )


class UniqueConstraintInfo(BaseModel):
    """A UNIQUE constraint (not the primary key)."""

    name: str | None = Field(
        default=None,
        description="Name of the unique constraint. May be None if the database does not name it.",
    )
    column_names: list[str] = Field(
        default_factory=list,
        description="Column(s) covered by the constraint.",
    )


class CheckConstraintInfo(BaseModel):
    """A CHECK constraint with its SQL expression."""

    name: str | None = Field(
        default=None,
        description="Name of the check constraint. May be None if the database does not name it.",
    )
    sqltext: str = Field(
        default="",
        description="The SQL expression that rows must satisfy.",
    )


class TableSchema(BaseModel):
    """Complete schema metadata for a table, as returned by describe_table.

    Bundles column details, primary key, foreign keys, indexes, unique
    constraints, check constraints, and the table comment into a single
    response so the LLM can understand the full structure without
    multiple round-trips.
    """

    table_name: str = Field(description="Name of the table.")
    table_comment: str = Field(
        default="",
        description="Database-native comment describing the table's purpose. Empty if no comment was set.",
    )
    columns: list[ColumnInfo] = Field(
        default_factory=list,
        description="Per-column metadata: name, type, nullable, primary_key flag.",
    )
    primary_key: PrimaryKeyInfo | None = Field(
        default=None,
        description="Primary key constraint. None if the table has no primary key.",
    )
    foreign_keys: list[ForeignKeyInfo] = Field(
        default_factory=list,
        description="Foreign key constraints referencing other tables. Use to discover JOIN paths.",
    )
    indexes: list[IndexInfo] = Field(
        default_factory=list,
        description="Indexes defined on this table. Includes auto-created indexes (e.g. for PK).",
    )
    unique_constraints: list[UniqueConstraintInfo] = Field(
        default_factory=list,
        description="UNIQUE constraints defined on this table (beyond the primary key).",
    )
    check_constraints: list[CheckConstraintInfo] = Field(
        default_factory=list,
        description="CHECK constraints defined on this table.",
    )


# ── Structured query parameter models ────────────────────────────────────


class FilterOperator(str, Enum):
    """Comparison operators for filter conditions."""

    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    LIKE = "like"
    IN = "in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class FilterCondition(BaseModel):
    """A single WHERE filter condition."""

    column: str = Field(
        description="Name of the column to filter on. Must match a column returned by describe_table."
    )
    operator: FilterOperator = Field(
        description="Comparison operator: eq(=), neq(!=), gt(>), gte(>=), lt(<), lte(<=), like(LIKE pattern), in(IN list), is_null(IS NULL), is_not_null(IS NOT NULL)"
    )
    value: Any | None = Field(
        default=None,
        description=(
            "Value to compare against. Required for eq, neq, gt, gte, lt, lte, like, in. "
            "Not used for is_null or is_not_null. "
            "Use the same type shown in describe_table: "
            "strings for VARCHAR/TEXT, numbers for INTEGER/NUMERIC, "
            "booleans for BOOLEAN. "
            "For 'in', provide a list of values, e.g. [1, 2, 3] or ['a', 'b']. "
            "For 'like', use SQL LIKE wildcards: % matches any sequence, _ matches one character."
        ),
    )


class OrderDirection(str, Enum):
    """Sort direction."""

    ASC = "asc"
    DESC = "desc"


class OrderByClause(BaseModel):
    """A single ORDER BY clause."""

    column: str = Field(
        description="Column to sort by. Must be a column in the queried table."
    )
    direction: OrderDirection = Field(
        default=OrderDirection.ASC,
        description="asc = ascending (A→Z, 1→9), desc = descending (Z→A, 9→1)",
    )


class AggregationFunction(str, Enum):
    """Aggregation functions for summarizing data."""

    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"


class AggregationFunc(BaseModel):
    """Apply an aggregation, e.g. COUNT(*) AS total, SUM(amount) AS grand_total."""

    function: AggregationFunction = Field(
        description="Aggregation to apply: count (number of rows), sum (total), avg (mean), min (smallest), max (largest)"
    )
    column: str | None = Field(
        default=None,
        description=(
            "Column to aggregate, e.g. 'amount' for SUM(amount). "
            "Set to null (or omit) when function is 'count' to get COUNT(*), "
            "which counts all rows regardless of column values."
        ),
    )
    alias: str | None = Field(
        default=None,
        description="Name for the result column. If omitted, auto-generated as function_column (e.g. 'sum_amount', 'count_star').",
    )
