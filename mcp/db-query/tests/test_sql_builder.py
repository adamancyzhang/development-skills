"""Tests for sql_builder.py — mo-sql-parsing tree construction.

Each test verifies the shape of the generated tree dict. Round-trip
tests (tree → mo_format → SQL string) are in test_integration.py.
"""

from __future__ import annotations

import pytest

from db_query.models import (
    AggregationFunc,
    AggregationFunction,
    FilterCondition,
    FilterOperator,
    OrderByClause,
    OrderDirection,
)
from db_query.sql_builder import build_select_tree


class TestBuildSelectTree:
    """Test tree structure for various parameter combinations."""

    # ── Basic SELECT ────────────────────────────────────────────────────

    def test_select_all(self):
        """SELECT * FROM users"""
        tree = build_select_tree(table="users")
        assert tree["from"] == "users"
        assert tree["select"] == "*"

    def test_select_columns(self):
        """SELECT id, name FROM users"""
        tree = build_select_tree(table="users", columns=["id", "name"])
        assert tree["from"] == "users"
        assert tree["select"] == [{"value": "id"}, {"value": "name"}]

    def test_empty_columns_list(self):
        """Empty columns list → SELECT *"""
        tree = build_select_tree(table="users", columns=[])
        assert tree["select"] == "*"

    # ── WHERE filters ──────────────────────────────────────────────────

    def test_where_eq_string(self):
        """WHERE status = 'active'"""
        tree = build_select_tree(
            table="users",
            filters=[FilterCondition(column="status", operator="eq", value="active")],
        )
        assert tree["where"] == {"eq": ["status", {"literal": "active"}]}

    def test_where_eq_number(self):
        """WHERE id = 5"""
        tree = build_select_tree(
            table="users",
            filters=[FilterCondition(column="id", operator="eq", value=5)],
        )
        assert tree["where"] == {"eq": ["id", 5]}

    def test_where_eq_float(self):
        """WHERE price = 9.99"""
        tree = build_select_tree(
            table="products",
            filters=[FilterCondition(column="price", operator="eq", value=9.99)],
        )
        assert tree["where"] == {"eq": ["price", 9.99]}

    def test_where_neq(self):
        """WHERE status != 'archived'"""
        tree = build_select_tree(
            table="users",
            filters=[
                FilterCondition(column="status", operator="neq", value="archived")
            ],
        )
        assert tree["where"] == {"neq": ["status", {"literal": "archived"}]}

    def test_where_gt(self):
        tree = build_select_tree(
            table="users",
            filters=[FilterCondition(column="age", operator="gt", value=18)],
        )
        assert tree["where"] == {"gt": ["age", 18]}

    def test_where_gte(self):
        tree = build_select_tree(
            table="users",
            filters=[FilterCondition(column="age", operator="gte", value=21)],
        )
        assert tree["where"] == {"gte": ["age", 21]}

    def test_where_lt(self):
        tree = build_select_tree(
            table="users",
            filters=[FilterCondition(column="age", operator="lt", value=65)],
        )
        assert tree["where"] == {"lt": ["age", 65]}

    def test_where_lte(self):
        tree = build_select_tree(
            table="users",
            filters=[FilterCondition(column="age", operator="lte", value=64)],
        )
        assert tree["where"] == {"lte": ["age", 64]}

    def test_where_like(self):
        """WHERE name LIKE '%test%'"""
        tree = build_select_tree(
            table="users",
            filters=[
                FilterCondition(column="name", operator="like", value="%test%")
            ],
        )
        assert tree["where"] == {"like": ["name", {"literal": "%test%"}]}

    def test_where_in(self):
        """WHERE id IN (1, 2, 3)"""
        tree = build_select_tree(
            table="users",
            filters=[
                FilterCondition(column="id", operator="in", value=[1, 2, 3])
            ],
        )
        assert tree["where"] == {"in": ["id", [1, 2, 3]]}

    def test_where_in_strings(self):
        """WHERE status IN ('a', 'b') — note: list values pass through as-is"""
        tree = build_select_tree(
            table="users",
            filters=[
                FilterCondition(
                    column="status", operator="in", value=["active", "pending"]
                )
            ],
        )
        assert tree["where"] == {"in": ["status", ["active", "pending"]]}

    def test_where_is_null(self):
        """WHERE email IS NULL"""
        tree = build_select_tree(
            table="users",
            filters=[FilterCondition(column="email", operator="is_null")],
        )
        assert tree["where"] == {"missing": "email"}

    def test_where_is_not_null(self):
        """WHERE email IS NOT NULL"""
        tree = build_select_tree(
            table="users",
            filters=[FilterCondition(column="email", operator="is_not_null")],
        )
        assert tree["where"] == {"exists": "email"}

    def test_multiple_filters_combined_with_and(self):
        """WHERE status = 'active' AND age >= 18"""
        tree = build_select_tree(
            table="users",
            filters=[
                FilterCondition(column="status", operator="eq", value="active"),
                FilterCondition(column="age", operator="gte", value=18),
            ],
        )
        assert "and" in tree["where"]
        assert len(tree["where"]["and"]) == 2

    def test_single_filter_no_and_wrapping(self):
        """A single filter should not be wrapped in 'and'."""
        tree = build_select_tree(
            table="users",
            filters=[FilterCondition(column="id", operator="eq", value=1)],
        )
        assert "and" not in tree["where"]

    # ── ORDER BY ────────────────────────────────────────────────────────

    def test_order_by_asc(self):
        """ORDER BY name ASC"""
        tree = build_select_tree(
            table="users",
            order_by=[OrderByClause(column="name", direction="asc")],
        )
        assert tree["orderby"] == [{"value": "name"}]

    def test_order_by_desc(self):
        """ORDER BY name DESC"""
        tree = build_select_tree(
            table="users",
            order_by=[OrderByClause(column="name", direction="desc")],
        )
        assert tree["orderby"] == [{"value": "name", "sort": "desc"}]

    def test_order_by_default_asc(self):
        """Default direction is ASC"""
        tree = build_select_tree(
            table="users",
            order_by=[OrderByClause(column="name")],
        )
        assert tree["orderby"] == [{"value": "name"}]

    def test_order_by_multiple(self):
        """ORDER BY dept ASC, salary DESC"""
        tree = build_select_tree(
            table="users",
            order_by=[
                OrderByClause(column="dept", direction="asc"),
                OrderByClause(column="salary", direction="desc"),
            ],
        )
        assert len(tree["orderby"]) == 2

    # ── Pagination ──────────────────────────────────────────────────────

    def test_limit(self):
        """LIMIT 10"""
        tree = build_select_tree(table="users", limit=10)
        assert tree["limit"] == 10

    def test_limit_offset(self):
        """LIMIT 10 OFFSET 20"""
        tree = build_select_tree(table="users", limit=10, offset=20)
        assert tree["limit"] == 10
        assert tree["offset"] == 20

    def test_offset_without_limit(self):
        """Offset only — no limit key but offset present."""
        tree = build_select_tree(table="users", offset=20)
        assert "limit" not in tree
        assert tree["offset"] == 20

    # ── Aggregations ────────────────────────────────────────────────────

    def test_aggregation_count_star(self):
        """SELECT COUNT(*) AS cnt FROM users"""
        tree = build_select_tree(
            table="users",
            aggregations=[AggregationFunc(function="count", alias="cnt")],
        )
        assert tree["select"] == [
            {"value": {"count": "*"}, "name": "cnt"}
        ]

    def test_aggregation_count_column(self):
        """SELECT COUNT(id) AS count_id FROM users"""
        tree = build_select_tree(
            table="users",
            aggregations=[AggregationFunc(function="count", column="id")],
        )
        assert tree["select"][0]["value"] == {"count": "id"}
        assert tree["select"][0]["name"] == "count_id"

    def test_aggregation_sum(self):
        """SELECT SUM(total) AS total_sum FROM orders"""
        tree = build_select_tree(
            table="orders",
            aggregations=[
                AggregationFunc(function="sum", column="total", alias="total_sum")
            ],
        )
        assert tree["select"] == [
            {"value": {"sum": "total"}, "name": "total_sum"}
        ]

    def test_aggregation_avg(self):
        tree = build_select_tree(
            table="t",
            aggregations=[AggregationFunc(function="avg", column="score")],
        )
        assert tree["select"][0]["value"] == {"avg": "score"}

    def test_aggregation_min(self):
        tree = build_select_tree(
            table="t",
            aggregations=[AggregationFunc(function="min", column="price")],
        )
        assert tree["select"][0]["value"] == {"min": "price"}

    def test_aggregation_max(self):
        tree = build_select_tree(
            table="t",
            aggregations=[AggregationFunc(function="max", column="price")],
        )
        assert tree["select"][0]["value"] == {"max": "price"}

    def test_aggregation_auto_alias(self):
        """Auto-generated alias: {function}_{column}"""
        tree = build_select_tree(
            table="t",
            aggregations=[AggregationFunc(function="sum", column="total")],
        )
        assert tree["select"][0]["name"] == "sum_total"

    def test_aggregation_auto_alias_count_star(self):
        tree = build_select_tree(
            table="t",
            aggregations=[AggregationFunc(function="count")],
        )
        assert tree["select"][0]["name"] == "count_star"

    def test_aggregation_with_group_by(self):
        """SELECT dept, SUM(salary) AS total FROM emp GROUP BY dept"""
        tree = build_select_tree(
            table="employees",
            columns=["dept"],
            aggregations=[
                AggregationFunc(function="sum", column="salary", alias="total")
            ],
            group_by=["dept"],
        )
        assert tree["groupby"] == [{"value": "dept"}]
        assert tree["select"] == [
            {"value": "dept"},
            {"value": {"sum": "salary"}, "name": "total"},
        ]

    # ── GROUP BY ────────────────────────────────────────────────────────

    def test_group_by_single(self):
        tree = build_select_tree(table="t", group_by=["a"])
        assert tree["groupby"] == [{"value": "a"}]

    def test_group_by_multiple(self):
        tree = build_select_tree(table="t", group_by=["a", "b"])
        assert tree["groupby"] == [{"value": "a"}, {"value": "b"}]

    # ── Combined queries ────────────────────────────────────────────────

    def test_combined_select_filter_order_limit(self):
        """SELECT id, name FROM users WHERE age > 18 ORDER BY name LIMIT 10"""
        tree = build_select_tree(
            table="users",
            columns=["id", "name"],
            filters=[FilterCondition(column="age", operator="gt", value=18)],
            order_by=[OrderByClause(column="name", direction="asc")],
            limit=10,
        )
        assert tree["from"] == "users"
        assert tree["select"] == [{"value": "id"}, {"value": "name"}]
        assert tree["where"] == {"gt": ["age", 18]}
        assert tree["orderby"] == [{"value": "name"}]
        assert tree["limit"] == 10

    def test_combined_aggregation_filter_group(self):
        """SELECT status, COUNT(*) AS cnt FROM orders
           WHERE total > 100 GROUP BY status LIMIT 50"""
        tree = build_select_tree(
            table="orders",
            columns=["status"],
            filters=[FilterCondition(column="total", operator="gt", value=100)],
            aggregations=[AggregationFunc(function="count", alias="cnt")],
            group_by=["status"],
            limit=50,
        )
        assert tree["from"] == "orders"
        assert tree["where"] == {"gt": ["total", 100]}
        assert tree["groupby"] == [{"value": "status"}]
        assert tree["limit"] == 50

    # ── Edge cases ──────────────────────────────────────────────────────

    def test_no_optional_params(self):
        """Only table → SELECT * FROM t"""
        tree = build_select_tree(table="t")
        assert tree == {"from": "t", "select": "*"}

    def test_columns_and_aggregations_combined(self):
        """SELECT name, SUM(salary) AS total FROM emp GROUP BY name"""
        tree = build_select_tree(
            table="emp",
            columns=["name"],
            aggregations=[
                AggregationFunc(function="sum", column="salary", alias="total")
            ],
            group_by=["name"],
        )
        assert len(tree["select"]) == 2
        assert tree["select"][0] == {"value": "name"}
        assert tree["select"][1] == {"value": {"sum": "salary"}, "name": "total"}

    # ── Validation ──────────────────────────────────────────────────────

    def test_invalid_in_value_raises(self):
        """IN operator requires value to be a list."""
        with pytest.raises(ValueError, match="list"):
            build_select_tree(
                table="users",
                filters=[
                    FilterCondition(column="id", operator="in", value="not_a_list")
                ],
            )
