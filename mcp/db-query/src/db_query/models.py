from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QueryResult(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool = False
    elapsed_ms: float = 0.0
    query_id: str = ""


class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False


class DbInfo(BaseModel):
    name: str
    dialect: str
    tables_count: int = 0


class ErrorResponse(BaseModel):
    error: str
    detail: str
    query_id: str | None = None
