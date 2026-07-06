from __future__ import annotations

import pytest

from db_query.exceptions import ReadOnlyViolationError
from db_query.query_engine import QueryEngine, _adapt_for_dialect, _execute_sql


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
