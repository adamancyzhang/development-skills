from __future__ import annotations

import pytest
from mo_sql_parsing import parse

from db_query.exceptions import EmptyQueryError, ReadOnlyViolationError
from db_query.security import enforce_row_count, sanitize_sql, validate_parse_tree


class TestSanitizeSQL:
    def test_returns_stripped_text(self):
        assert sanitize_sql("  SELECT * FROM users  ") == "SELECT * FROM users"

    def test_rejects_empty_string(self):
        with pytest.raises(EmptyQueryError):
            sanitize_sql("")

    def test_rejects_whitespace_only(self):
        with pytest.raises(EmptyQueryError):
            sanitize_sql("   \t\n   ")


class TestValidateParseTree:
    def test_simple_select_passes(self):
        tree = parse("SELECT * FROM users")
        validate_parse_tree(tree)

    def test_select_with_join_passes(self):
        tree = parse(
            "SELECT u.name, o.total FROM users u "
            "INNER JOIN orders o ON u.id = o.user_id"
        )
        validate_parse_tree(tree)

    def test_select_with_subquery_passes(self):
        tree = parse(
            "SELECT * FROM (SELECT id FROM users) AS sub"
        )
        validate_parse_tree(tree)

    def test_select_with_cte_passes(self):
        tree = parse(
            "WITH active AS (SELECT * FROM users WHERE id > 0) "
            "SELECT * FROM active"
        )
        validate_parse_tree(tree)

    def test_insert_raises(self):
        tree = parse("INSERT INTO users VALUES (1, 'test')")
        with pytest.raises(ReadOnlyViolationError) as exc:
            validate_parse_tree(tree)
        assert "insert" in str(exc.value).lower()
        assert "READ_ONLY_VIOLATION" in exc.value.status_code

    def test_update_raises(self):
        tree = parse("UPDATE users SET name = 'x'")
        with pytest.raises(ReadOnlyViolationError):
            validate_parse_tree(tree)

    def test_delete_raises(self):
        tree = parse("DELETE FROM users")
        with pytest.raises(ReadOnlyViolationError):
            validate_parse_tree(tree)

    def test_drop_raises(self):
        tree = parse("DROP TABLE users")
        with pytest.raises(ReadOnlyViolationError):
            validate_parse_tree(tree)

    def test_create_raises(self):
        tree = parse("CREATE TABLE users (id int)")
        with pytest.raises(ReadOnlyViolationError):
            validate_parse_tree(tree)

    def test_alter_raises(self):
        tree = parse("ALTER TABLE users ADD COLUMN x int")
        with pytest.raises(ReadOnlyViolationError):
            validate_parse_tree(tree)


class TestEnforceRowCount:
    def test_no_limit_uses_max(self):
        assert enforce_row_count(None, 100) == 100

    def test_lower_limit_kept(self):
        assert enforce_row_count(50, 100) == 50

    def test_higher_limit_capped(self):
        assert enforce_row_count(500, 100) == 100

    def test_exact_limit(self):
        assert enforce_row_count(100, 100) == 100
