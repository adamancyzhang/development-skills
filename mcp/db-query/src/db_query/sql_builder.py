"""Build mo-sql-parsing parse trees from structured query parameters.

Converts typed FilterCondition, OrderByClause, and AggregationFunc
objects into a mo-sql-parsing-compatible dict that can be validated,
formatted, and executed through the existing query pipeline.
"""

from __future__ import annotations

from .models import AggregationFunc, FilterCondition, FilterOperator, OrderByClause


def build_select_tree(
    table: str,
    *,
    columns: list[str] | None = None,
    filters: list[FilterCondition] | None = None,
    order_by: list[OrderByClause] | None = None,
    aggregations: list[AggregationFunc] | None = None,
    group_by: list[str] | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> dict:
    """Build a mo-sql-parsing-compatible SELECT parse tree dict.

    Returns a dict whose top-level key is ``"select"`` via the
    structured parameters. The tree passes through the existing
    pipeline: validate_parse_tree → mo_format → dialect adapt → execute.
    """
    tree: dict = {"from": table}

    select_clause = _build_select_clause(columns, aggregations)
    tree["select"] = select_clause if select_clause is not None else "*"

    if filters:
        tree["where"] = _build_where_clause(filters)

    if order_by:
        tree["orderby"] = _build_order_by_clause(order_by)

    if group_by:
        tree["groupby"] = _build_group_by_clause(group_by)

    if limit is not None:
        tree["limit"] = limit

    if offset is not None:
        tree["offset"] = offset

    return tree


# ── SELECT clause ───────────────────────────────────────────────────────


def _build_select_clause(
    columns: list[str] | None,
    aggregations: list[AggregationFunc] | None,
) -> list[dict] | None:
    select_items: list[dict] = []

    # Regular columns first
    if columns:
        for col in columns:
            select_items.append({"value": col})

    # Then aggregation expressions
    if aggregations:
        for agg in aggregations:
            select_items.append(_build_aggregation_value(agg))

    if select_items:
        return select_items
    # None → SELECT *
    return None


# ── WHERE clause ────────────────────────────────────────────────────────


def _build_where_clause(filters: list[FilterCondition]) -> dict:
    conditions = [_build_single_condition(f) for f in filters]

    if len(conditions) == 1:
        return conditions[0]

    return {"and": conditions}


def _build_single_condition(cond: FilterCondition) -> dict:
    """Map a FilterCondition to a mo-sql-parsing operator sub-tree."""
    col = cond.value
    val = _wrap_value(cond.value)

    if cond.operator == FilterOperator.EQ:
        return {"eq": [cond.column, val]}

    if cond.operator == FilterOperator.NEQ:
        return {"neq": [cond.column, val]}

    if cond.operator == FilterOperator.GT:
        return {"gt": [cond.column, val]}

    if cond.operator == FilterOperator.GTE:
        return {"gte": [cond.column, val]}

    if cond.operator == FilterOperator.LT:
        return {"lt": [cond.column, val]}

    if cond.operator == FilterOperator.LTE:
        return {"lte": [cond.column, val]}

    if cond.operator == FilterOperator.LIKE:
        return {"like": [cond.column, {"literal": str(cond.value)}]}

    if cond.operator == FilterOperator.IN:
        if not isinstance(cond.value, list):
            raise ValueError(
                f"IN operator requires a list value, got {type(cond.value).__name__}"
            )
        return {"in": [cond.column, cond.value]}

    if cond.operator == FilterOperator.IS_NULL:
        return {"missing": cond.column}

    if cond.operator == FilterOperator.IS_NOT_NULL:
        return {"exists": cond.column}

    raise ValueError(f"Unknown filter operator: {cond.operator}")


def _wrap_value(value: object) -> object:
    """Wrap a Python value for mo-sql-parsing.

    Strings → {"literal": value} to prevent them being treated as column refs.
    Numbers → used directly (int, float).
    None → used directly (for IS_NULL / IS_NOT_NULL these won't hit here).
    """
    if isinstance(value, str):
        return {"literal": value}
    return value


# ── ORDER BY clause ─────────────────────────────────────────────────────


def _build_order_by_clause(order_by: list[OrderByClause]) -> list[dict]:
    items: list[dict] = []
    for ob in order_by:
        item: dict = {"value": ob.column}
        if ob.direction != "asc":
            item["sort"] = ob.direction
        items.append(item)
    return items


# ── GROUP BY clause ─────────────────────────────────────────────────────


def _build_group_by_clause(group_by: list[str]) -> list[dict]:
    return [{"value": col} for col in group_by]


# ── Aggregation value ───────────────────────────────────────────────────


def _build_aggregation_value(agg: AggregationFunc) -> dict:
    """Build a mo-sql-parsing aggregation value, e.g. {"sum": "total"}.

    Wraps in {"value": ...} and optionally {"name": alias}.
    """
    if agg.function == "count" and agg.column is None:
        inner = {"count": "*"}
    else:
        col = agg.column or "*"
        inner = {agg.function.value: col}

    alias = agg.alias
    if alias is None:
        alias = f"{agg.function.value}_{agg.column or 'star'}"

    return {"value": inner, "name": alias}
