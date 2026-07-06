from __future__ import annotations

import pytest

from db_query.config import _extract_dialect, load_config
from db_query.exceptions import ConfigurationError


class TestLoadConfig:
    def test_single_default_database(self, monkeypatch):
        monkeypatch.setenv(
            "DB_DEFAULT_URL", "postgresql+asyncpg://user:pass@host:5432/mydb"
        )
        configs = load_config()
        assert set(configs.keys()) == {"default"}
        assert configs["default"].dialect == "postgresql"
        assert configs["default"].max_rows == 100
        assert configs["default"].pool_size == 5

    def test_multiple_databases(self, monkeypatch):
        monkeypatch.setenv(
            "DB_DEFAULT_URL", "postgresql+asyncpg://u:p@h/db1"
        )
        monkeypatch.setenv(
            "DB_ANALYTICS_URL", "mysql+aiomysql://u:p@h/db2"
        )
        monkeypatch.setenv(
            "DB_LEGACY_URL", "oracle+oracledb://u:p@h/svc"
        )
        configs = load_config()
        assert set(configs.keys()) == {"default", "analytics", "legacy"}
        assert configs["default"].dialect == "postgresql"
        assert configs["analytics"].dialect == "mysql"
        assert configs["legacy"].dialect == "oracle"

    def test_name_normalized_to_lowercase(self, monkeypatch):
        monkeypatch.setenv(
            "DB_MY_DB_URL", "postgresql+asyncpg://u:p@h/db"
        )
        configs = load_config()
        assert "my_db" in configs

    def test_per_connection_max_rows(self, monkeypatch):
        monkeypatch.setenv(
            "DB_DEFAULT_URL", "postgresql+asyncpg://u:p@h/db"
        )
        monkeypatch.setenv("DB_DEFAULT_MAX_ROWS", "500")
        configs = load_config()
        assert configs["default"].max_rows == 500

    def test_per_connection_pool_size(self, monkeypatch):
        monkeypatch.setenv(
            "DB_DEFAULT_URL", "postgresql+asyncpg://u:p@h/db"
        )
        monkeypatch.setenv("DB_DEFAULT_POOL_SIZE", "10")
        monkeypatch.setenv("DB_DEFAULT_POOL_OVERFLOW", "20")
        configs = load_config()
        assert configs["default"].pool_size == 10
        assert configs["default"].pool_overflow == 20

    def test_no_databases_configured_raises(self, monkeypatch):
        # Ensure no DB_*_URL env vars exist in the real environment
        import os
        for key in list(os.environ):
            if key.startswith("DB_") and key.endswith("_URL"):
                monkeypatch.delenv(key, raising=False)
        with pytest.raises(ConfigurationError, match="No database connections"):
            load_config()


class TestExtractDialect:
    def test_postgresql(self):
        assert _extract_dialect("postgresql+asyncpg://u:p@h/db") == "postgresql"

    def test_mysql(self):
        assert _extract_dialect("mysql+aiomysql://u:p@h/db") == "mysql"

    def test_oracle(self):
        assert _extract_dialect("oracle+oracledb://u:p@h/svc") == "oracle"

    def test_sqlite(self):
        assert _extract_dialect("sqlite+aiosqlite:///test.db") == "sqlite"

    def test_unknown_fallback(self):
        assert _extract_dialect("garbage") == "unknown"
