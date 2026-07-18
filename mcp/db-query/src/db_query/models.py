from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class QueryResult(BaseModel):
    """Result of a structured query."""

    columns: list[str] = Field(description="Column names in result order")
    rows: list[list[Any]] = Field(description="Row data as lists of values")
    row_count: int = Field(description="Number of rows returned")
    truncated: bool = Field(
        default=False,
        description="Whether results were truncated to the row limit",
    )
    elapsed_ms: float = Field(
        default=0.0, description="Query execution time in milliseconds"
    )
    query_id: str = Field(default="", description="Unique query identifier")


class ColumnInfo(BaseModel):
    """Schema information for a single table column."""

    name: str = Field(description="Column name")
    type: str = Field(description="SQL data type")
    nullable: bool = Field(default=True, description="Whether NULL is allowed")
    primary_key: bool = Field(default=False, description="Whether this is a primary key")


class TableInfo(BaseModel):
    """Table name and description."""

    name: str = Field(description="Table name")
    comment: str = Field(
        default="", description="Database-native table comment (COMMENT ON TABLE)"
    )


class DbInfo(BaseModel):
    name: str
    dialect: str
    tables_count: int = 0


class ErrorResponse(BaseModel):
    error: str
    detail: str
    query_id: str | None = None


# ── Structured query parameter models ────────────────────────────────────


class FilterOperator(str, Enum):
    """Comparison operators for WHERE conditions."""

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
    """A single WHERE condition.

    For is_null and is_not_null, value is ignored.
    For in, value must be a list.
    """

    column: str = Field(description="Column name to filter on")
    operator: FilterOperator = Field(description="Comparison operator")
    value: Any | None = Field(
        default=None,
        description=(
            "Value to compare against. Required for all operators "
            "except is_null and is_not_null. "
            "For 'in', provide a list."
        ),
    )


class OrderDirection(str, Enum):
    """Sort direction for ORDER BY clauses."""

    ASC = "asc"
    DESC = "desc"


class OrderByClause(BaseModel):
    """A single ORDER BY clause."""

    column: str = Field(description="Column to order by")
    direction: OrderDirection = Field(
        default=OrderDirection.ASC, description="Sort direction"
    )


class AggregationFunction(str, Enum):
    """Aggregation functions."""

    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"


class AggregationFunc(BaseModel):
    """An aggregation applied to a column, e.g. SUM(total) AS grand_total.

    Set column to None with function='count' for COUNT(*).
    """

    function: AggregationFunction = Field(description="Aggregation function to apply")
    column: str | None = Field(
        default=None,
        description=(
            "Column to aggregate. Set to None for COUNT(*) "
            "(only valid when function is 'count')."
        ),
    )
    alias: str | None = Field(
        default=None,
        description="Alias for the result column. Auto-generated if omitted.",
    )
