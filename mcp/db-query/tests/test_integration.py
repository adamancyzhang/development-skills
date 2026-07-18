from __future__ import annotations

import pytest

from db_query.config import DbConfig
from db_query.connections import ConnectionManager
from db_query.exceptions import ReadOnlyViolationError
from db_query.models import (
    AggregationFunc,
    FilterCondition,
    FilterOperator,
    OrderByClause,
)
from db_query.query_engine import QueryEngine, _adapt_for_dialect, _execute_sql
from db_query.sql_builder import build_select_tree
from mo_sql_parsing import format as mo_format


class TestExecuteSQL:
    @pytest.mark.asyncio
    async def test_simple_select(self, sqlite_engine):
        rows, columns = await _execute_sql(
            sqlite_engine, "SELECT * FROM users ORDER BY id"
        )
        assert columns == ["id", "name", "email"]
        assert len(rows) == 2
        assert rows[0] == [1, "Alice", "alice@example.com"]

    @pytest.mark.asyncio
    async def test_select_with_where(self, sqlite_engine):
        rows, columns = await _execute_sql(
            sqlite_engine, "SELECT name FROM users WHERE id = 1"
        )
        assert rows == [["Alice"]]

    @pytest.mark.asyncio
    async def test_select_no_rows(self, sqlite_engine):
        rows, columns = await _execute_sql(
            sqlite_engine, "SELECT * FROM users WHERE id = 999"
        )
        assert rows == []

    @pytest.mark.asyncio
    async def test_aggregation(self, sqlite_engine):
        rows, columns = await _execute_sql(
            sqlite_engine, "SELECT count(1) FROM users"
        )
        assert rows == [[2]]

    @pytest.mark.asyncio
    async def test_join_query(self, sqlite_engine):
        rows, columns = await _execute_sql(
            sqlite_engine,
            "SELECT u.name, o.total FROM users u "
            "JOIN orders o ON u.id = o.user_id "
            "ORDER BY o.total",
        )
        assert len(rows) == 3
        assert rows[0] == ["Bob", 50.0]
        assert rows[1] == ["Alice", 100.0]
        assert rows[2] == ["Alice", 200.0]

    @pytest.mark.asyncio
    async def test_group_by(self, sqlite_engine):
        rows, columns = await _execute_sql(
            sqlite_engine,
            "SELECT u.name, sum(o.total) AS total_spent "
            "FROM users u JOIN orders o ON u.id = o.user_id "
            "GROUP BY u.name ORDER BY total_spent DESC",
        )
        assert rows == [["Alice", 300.0], ["Bob", 50.0]]

    @pytest.mark.asyncio
    async def test_limit(self, sqlite_engine):
        rows, columns = await _execute_sql(
            sqlite_engine, "SELECT * FROM users LIMIT 1"
        )
        assert len(rows) == 1

    @pytest.mark.asyncio
    async def test_invalid_sql_raises(self, sqlite_engine):
        with pytest.raises(Exception):
            await _execute_sql(
                sqlite_engine, "SELECT * FROM nonexistent_table"
            )


class TestDialectAdaptation:
    def test_oracle_limit(self):
        sql = "SELECT * FROM users LIMIT 10"
        result = _adapt_for_dialect(sql, "oracle")
        assert result == "SELECT * FROM users FETCH FIRST 10 ROWS ONLY"

    def test_oracle_limit_offset(self):
        sql = "SELECT * FROM users LIMIT 10 OFFSET 20"
        result = _adapt_for_dialect(sql, "oracle")
        assert result == "SELECT * FROM users OFFSET 20 ROWS FETCH NEXT 10 ROWS ONLY"

    def test_mysql_no_change(self):
        sql = "SELECT * FROM users LIMIT 10"
        assert _adapt_for_dialect(sql, "mysql") == sql

    def test_postgresql_no_change(self):
        sql = "SELECT * FROM users LIMIT 10"
        assert _adapt_for_dialect(sql, "postgresql") == sql


class TestQueryEngine:
    @pytest.mark.asyncio
    async def test_execute_simple_select(self, sqlite_engine, monkeypatch):
        from db_query.config import DbConfig
        from db_query.connections import ConnectionManager

        ConnectionManager._engines["test"] = sqlite_engine
        ConnectionManager._configs["test"] = DbConfig(
            name="test", url="sqlite+aiosqlite://", dialect="sqlite", max_rows=100
        )

        result = await QueryEngine.execute("test", "SELECT * FROM users ORDER BY id")
        assert result.columns == ["id", "name", "email"]
        assert result.row_count == 2
        assert not result.truncated
        assert result.elapsed_ms > 0
        assert len(result.query_id) == 12


class TestSqlBuilderRoundTrip:
    """Verify build_select_tree output produces valid SQL via mo_format."""

    def test_select_all_sql(self):
        tree = build_select_tree(table="users")
        sql = mo_format(tree)
        assert "select *" in sql.lower()
        assert "from users" in sql.lower()

    def test_select_columns_sql(self):
        tree = build_select_tree(table="users", columns=["id", "name"])
        sql = mo_format(tree)
        assert "select id" in sql.lower()
        assert "name" in sql.lower()
        assert "from users" in sql.lower()

    def test_where_eq_string_sql(self):
        tree = build_select_tree(
            table="users",
            filters=[FilterCondition(column="name", operator="eq", value="Alice")],
        )
        sql = mo_format(tree)
        assert "name = 'Alice'" in sql

    def test_where_eq_number_sql(self):
        tree = build_select_tree(
            table="users",
            filters=[FilterCondition(column="id", operator="eq", value=5)],
        )
        sql = mo_format(tree)
        assert "id = 5" in sql

    def test_where_like_sql(self):
        tree = build_select_tree(
            table="users",
            filters=[
                FilterCondition(column="name", operator="like", value="%test%")
            ],
        )
        sql = mo_format(tree)
        assert "like" in sql.lower()

    def test_where_is_null_sql(self):
        tree = build_select_tree(
            table="users",
            filters=[FilterCondition(column="email", operator="is_null")],
        )
        sql = mo_format(tree)
        assert "is null" in sql.lower()

    def test_aggregation_count_star_sql(self):
        tree = build_select_tree(
            table="users",
            aggregations=[AggregationFunc(function="count", alias="cnt")],
        )
        sql = mo_format(tree)
        assert "count(*)" in sql.lower()

    def test_limit_sql(self):
        tree = build_select_tree(table="users", limit=5)
        sql = mo_format(tree)
        assert "limit 5" in sql.lower()

    def test_limit_offset_sql(self):
        tree = build_select_tree(table="users", limit=10, offset=20)
        sql = mo_format(tree)
        assert "limit 10" in sql.lower()
        assert "offset 20" in sql.lower()

    def test_order_by_desc_sql(self):
        tree = build_select_tree(
            table="users",
            order_by=[OrderByClause(column="name", direction="desc")],
        )
        sql = mo_format(tree)
        assert "order by" in sql.lower()
        assert "desc" in sql.lower()

    def test_group_by_sql(self):
        tree = build_select_tree(
            table="users",
            columns=["status"],
            aggregations=[AggregationFunc(function="count", alias="cnt")],
            group_by=["status"],
        )
        sql = mo_format(tree)
        assert "group by" in sql.lower()

    def test_multiple_filters_and_sql(self):
        tree = build_select_tree(
            table="users",
            filters=[
                FilterCondition(column="status", operator="eq", value="active"),
                FilterCondition(column="age", operator="gte", value=18),
            ],
        )
        sql = mo_format(tree)
        assert "status = 'active'" in sql
        assert "age >= 18" in sql

    def test_round_trip_parseable(self):
        """Generated SQL should be re-parseable by mo-sql-parsing."""
        from mo_sql_parsing import parse

        tree = build_select_tree(
            table="users",
            columns=["id", "name"],
            filters=[FilterCondition(column="age", operator="gt", value=18)],
            order_by=[OrderByClause(column="name")],
            limit=10,
        )
        sql = mo_format(tree)
        reparsed = parse(sql)
        assert reparsed["from"] == "users"


class TestQueryEngineStructured:
    """Integration tests: structured params → QueryEngine → QueryResult."""

    @pytest.mark.asyncio
    async def test_simple_select_all(self, sqlite_engine):
        self._setup_engine(sqlite_engine)
        result = await QueryEngine.execute_structured(
            db_name="test",
            table="users",
            order_by=[OrderByClause(column="id", direction="asc")],
        )
        assert result.columns == ["id", "name", "email"]
        assert result.row_count == 2
        assert not result.truncated

    @pytest.mark.asyncio
    async def test_select_with_columns(self, sqlite_engine):
        self._setup_engine(sqlite_engine)
        result = await QueryEngine.execute_structured(
            db_name="test", table="users", columns=["name"]
        )
        assert result.columns == ["name"]
        assert result.row_count == 2

    @pytest.mark.asyncio
    async def test_filter_eq_string(self, sqlite_engine):
        self._setup_engine(sqlite_engine)
        result = await QueryEngine.execute_structured(
            db_name="test",
            table="users",
            filters=[FilterCondition(column="name", operator="eq", value="Alice")],
        )
        assert result.row_count == 1
        assert result.rows[0] == [1, "Alice", "alice@example.com"]

    @pytest.mark.asyncio
    async def test_filter_gt_number(self, sqlite_engine):
        self._setup_engine(sqlite_engine)
        result = await QueryEngine.execute_structured(
            db_name="test",
            table="orders",
            filters=[FilterCondition(column="total", operator="gt", value=50)],
        )
        assert result.row_count == 2  # 100.0 and 200.0

    @pytest.mark.asyncio
    async def test_filter_like(self, sqlite_engine):
        self._setup_engine(sqlite_engine)
        result = await QueryEngine.execute_structured(
            db_name="test",
            table="users",
            filters=[
                FilterCondition(column="email", operator="like", value="%@example.com")
            ],
        )
        assert result.row_count == 2

    @pytest.mark.asyncio
    async def test_filter_is_null(self, sqlite_engine):
        self._setup_engine(sqlite_engine)
        result = await QueryEngine.execute_structured(
            db_name="test",
            table="users",
            filters=[FilterCondition(column="email", operator="is_null")],
        )
        assert result.row_count == 0  # all rows have emails

    @pytest.mark.asyncio
    async def test_filter_is_not_null(self, sqlite_engine):
        self._setup_engine(sqlite_engine)
        result = await QueryEngine.execute_structured(
            db_name="test",
            table="users",
            filters=[FilterCondition(column="email", operator="is_not_null")],
        )
        assert result.row_count == 2

    @pytest.mark.asyncio
    async def test_filter_multiple_and(self, sqlite_engine):
        self._setup_engine(sqlite_engine)
        result = await QueryEngine.execute_structured(
            db_name="test",
            table="orders",
            filters=[
                FilterCondition(column="user_id", operator="eq", value=1),
                FilterCondition(column="total", operator="gt", value=50),
            ],
        )
        assert result.row_count == 2  # user 1 has orders 100 and 200

    @pytest.mark.asyncio
    async def test_aggregation_count(self, sqlite_engine):
        self._setup_engine(sqlite_engine)
        result = await QueryEngine.execute_structured(
            db_name="test",
            table="users",
            aggregations=[AggregationFunc(function="count", alias="user_count")],
        )
        assert result.rows[0][0] == 2

    @pytest.mark.asyncio
    async def test_aggregation_sum(self, sqlite_engine):
        self._setup_engine(sqlite_engine)
        result = await QueryEngine.execute_structured(
            db_name="test",
            table="orders",
            aggregations=[
                AggregationFunc(function="sum", column="total", alias="grand_total")
            ],
        )
        assert result.rows[0][0] == 350.0

    @pytest.mark.asyncio
    async def test_aggregation_avg_min_max(self, sqlite_engine):
        self._setup_engine(sqlite_engine)
        result = await QueryEngine.execute_structured(
            db_name="test",
            table="orders",
            aggregations=[
                AggregationFunc(function="avg", column="total", alias="avg_total"),
                AggregationFunc(function="min", column="total", alias="min_total"),
                AggregationFunc(function="max", column="total", alias="max_total"),
            ],
        )
        # avg ≈ 116.67, min = 50, max = 200
        assert abs(result.rows[0][0] - 116.67) < 1
        assert result.rows[0][1] == 50.0
        assert result.rows[0][2] == 200.0

    @pytest.mark.asyncio
    async def test_group_by_with_aggregation(self, sqlite_engine):
        self._setup_engine(sqlite_engine)
        result = await QueryEngine.execute_structured(
            db_name="test",
            table="orders",
            columns=["user_id"],
            aggregations=[
                AggregationFunc(function="sum", column="total", alias="total")
            ],
            group_by=["user_id"],
        )
        assert result.row_count == 2

    @pytest.mark.asyncio
    async def test_order_by_asc(self, sqlite_engine):
        self._setup_engine(sqlite_engine)
        result = await QueryEngine.execute_structured(
            db_name="test",
            table="users",
            order_by=[OrderByClause(column="name", direction="asc")],
        )
        assert result.rows[0][1] == "Alice"
        assert result.rows[1][1] == "Bob"

    @pytest.mark.asyncio
    async def test_order_by_desc(self, sqlite_engine):
        self._setup_engine(sqlite_engine)
        result = await QueryEngine.execute_structured(
            db_name="test",
            table="users",
            order_by=[OrderByClause(column="name", direction="desc")],
        )
        assert result.rows[0][1] == "Bob"

    @pytest.mark.asyncio
    async def test_limit(self, sqlite_engine):
        self._setup_engine(sqlite_engine)
        result = await QueryEngine.execute_structured(
            db_name="test", table="users", limit=1
        )
        assert result.row_count == 1

    @pytest.mark.asyncio
    async def test_no_results(self, sqlite_engine):
        self._setup_engine(sqlite_engine)
        result = await QueryEngine.execute_structured(
            db_name="test",
            table="users",
            filters=[FilterCondition(column="name", operator="eq", value="Nobody")],
        )
        assert result.row_count == 0
        assert result.rows == []

    @pytest.mark.asyncio
    async def test_truncation(self, sqlite_engine):
        ConnectionManager._configs["test"] = DbConfig(
            name="test", url="sqlite+aiosqlite://", dialect="sqlite", max_rows=1
        )
        ConnectionManager._engines["test"] = sqlite_engine
        result = await QueryEngine.execute_structured(
            db_name="test", table="users"
        )
        assert result.row_count == 1
        assert result.truncated

    @pytest.mark.asyncio
    async def test_query_id_present(self, sqlite_engine):
        self._setup_engine(sqlite_engine)
        result = await QueryEngine.execute_structured(
            db_name="test", table="users", limit=1
        )
        assert len(result.query_id) == 12

    @staticmethod
    def _setup_engine(sqlite_engine):
        ConnectionManager._engines["test"] = sqlite_engine
        ConnectionManager._configs["test"] = DbConfig(
            name="test", url="sqlite+aiosqlite://", dialect="sqlite", max_rows=100
        )
