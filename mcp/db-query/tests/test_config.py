from __future__ import annotations

import pytest

from db_query.config import (
    _build_mysql_url,
    _build_oracle_url,
    _build_postgres_url,
    _extract_dialect,
    load_config,
)
from db_query.exceptions import ConfigurationError

_FRIENDLY_PREFIXES = ("POSTGRES_", "MYSQL_", "ORACLE_")
_DB_VAR_PREFIX = "DB_"


def _clear_friendly_vars(monkeypatch) -> None:
    """Remove all friendly and DB_* env vars so .env doesn't leak into tests."""
    import os
    for key in list(os.environ):
        if key.startswith(_FRIENDLY_PREFIXES) or key.startswith(_DB_VAR_PREFIX):
            monkeypatch.delenv(key, raising=False)


class TestLoadConfig:
    def test_single_default_database(self, monkeypatch):
        monkeypatch.setenv(
            "DB_DEFAULT_URL", "postgresql+asyncpg://user:pass@host:5432/mydb"
        )
        configs = load_config()
        assert set(configs.keys()) == {"default"}
        assert configs["default"].dialect == "postgresql"
        assert configs["default"].max_rows == 500
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
        import os
        for key in list(os.environ):
            if key.startswith("DB_") and key.endswith("_URL"):
                monkeypatch.delenv(key, raising=False)
        for key in ("POSTGRES_HOST", "MYSQL_HOST", "ORACLE_HOST"):
            monkeypatch.delenv(key, raising=False)
        with pytest.raises(ConfigurationError, match="No database connections"):
            load_config()

    # ── Friendly PostgreSQL env vars ───────────────────────────────────

    def test_postgres_friendly_vars_as_default(self, monkeypatch):
        monkeypatch.setenv("POSTGRES_HOST", "127.0.0.1")
        monkeypatch.setenv("POSTGRES_PORT", "5431")
        monkeypatch.setenv("POSTGRES_USER", "ainowork")
        monkeypatch.setenv("POSTGRES_PASSWORD", "Abc@1234")
        monkeypatch.setenv("POSTGRES_DB", "ainowork")
        configs = load_config()
        assert "default" in configs
        cfg = configs["default"]
        assert cfg.dialect == "postgresql"
        assert "ainowork:Abc%401234@127.0.0.1:5431/ainowork" in cfg.url

    def test_postgres_friendly_vars_minimal(self, monkeypatch):
        _clear_friendly_vars(monkeypatch)
        monkeypatch.setenv("POSTGRES_HOST", "db.example.com")
        configs = load_config()
        assert "default" in configs
        cfg = configs["default"]
        assert cfg.dialect == "postgresql"
        assert "db.example.com:5432" in cfg.url
        assert "postgres@" in cfg.url

    def test_postgres_friendly_without_password(self, monkeypatch):
        _clear_friendly_vars(monkeypatch)
        monkeypatch.setenv("POSTGRES_HOST", "127.0.0.1")
        monkeypatch.setenv("POSTGRES_USER", "myuser")
        monkeypatch.setenv("POSTGRES_DB", "mydb")
        configs = load_config()
        assert "myuser@127.0.0.1:5432/mydb" in configs["default"].url

    # ── Friendly MySQL env vars ────────────────────────────────────────

    def test_mysql_friendly_vars(self, monkeypatch):
        # Ensure no POSTGRES_HOST so default doesn't fire
        monkeypatch.setenv("MYSQL_HOST", "127.0.0.1")
        monkeypatch.setenv("MYSQL_PORT", "3307")
        monkeypatch.setenv("MYSQL_USER", "app")
        monkeypatch.setenv("MYSQL_PASSWORD", "secret")
        monkeypatch.setenv("MYSQL_DB", "appdb")
        configs = load_config()
        assert "mysql" in configs
        cfg = configs["mysql"]
        assert cfg.dialect == "mysql"
        assert "app:secret@127.0.0.1:3307/appdb" in cfg.url

    def test_mysql_friendly_vars_minimal(self, monkeypatch):
        monkeypatch.setenv("MYSQL_HOST", "db.example.com")
        configs = load_config()
        assert "mysql" in configs
        cfg = configs["mysql"]
        assert cfg.dialect == "mysql"
        assert "root@db.example.com:3306/mysql" in cfg.url

    # ── Friendly Oracle env vars ───────────────────────────────────────

    def test_oracle_friendly_vars(self, monkeypatch):
        monkeypatch.setenv("ORACLE_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_PORT", "1522")
        monkeypatch.setenv("ORACLE_USER", "scott")
        monkeypatch.setenv("ORACLE_PASSWORD", "tiger")
        monkeypatch.setenv("ORACLE_SERVICE_NAME", "ORCLPDB1")
        configs = load_config()
        assert "oracle" in configs
        cfg = configs["oracle"]
        assert cfg.dialect == "oracle"
        assert "service_name=ORCLPDB1" in cfg.url

    # ── Mix: friendly + explicit URL (URL wins, friendly fills gaps) ──

    def test_explicit_url_overrides_friendly_postgres(self, monkeypatch):
        monkeypatch.setenv("POSTGRES_HOST", "127.0.0.1")
        monkeypatch.setenv("POSTGRES_USER", "friendly")
        monkeypatch.setenv(
            "DB_DEFAULT_URL", "postgresql+asyncpg://explicit:pass@host/db"
        )
        configs = load_config()
        assert configs["default"].url == "postgresql+asyncpg://explicit:pass@host/db"

    def test_friendly_and_explicit_coexist(self, monkeypatch):
        monkeypatch.setenv("POSTGRES_HOST", "127.0.0.1")
        monkeypatch.setenv("POSTGRES_USER", "pguser")
        monkeypatch.setenv("MYSQL_HOST", "127.0.0.1")
        monkeypatch.setenv("MYSQL_USER", "mysqluser")
        monkeypatch.setenv(
            "DB_ANALYTICS_URL", "postgresql+asyncpg://u:p@h/analytics"
        )
        configs = load_config()
        assert set(configs.keys()) == {"default", "mysql", "analytics"}
        assert configs["default"].dialect == "postgresql"
        assert configs["mysql"].dialect == "mysql"
        assert configs["analytics"].dialect == "postgresql"

    def test_explicit_url_blocks_friendly_same_name(self, monkeypatch):
        """DB_MYSQL_URL blocks MYSQL_* friendly vars for name 'mysql'."""
        monkeypatch.setenv("MYSQL_HOST", "127.0.0.1")
        monkeypatch.setenv("MYSQL_USER", "friendly")
        monkeypatch.setenv(
            "DB_MYSQL_URL", "mysql+aiomysql://explicit:pass@host/db"
        )
        configs = load_config()
        assert configs["mysql"].url == "mysql+aiomysql://explicit:pass@host/db"

    # ── Friendly: per-connection overrides work with friendly vars ─────

    def test_friendly_postgres_with_overrides(self, monkeypatch):
        monkeypatch.setenv("POSTGRES_HOST", "127.0.0.1")
        monkeypatch.setenv("DB_DEFAULT_MAX_ROWS", "500")
        monkeypatch.setenv("DB_DEFAULT_POOL_SIZE", "10")
        monkeypatch.setenv("DB_DEFAULT_POOL_OVERFLOW", "20")
        configs = load_config()
        assert configs["default"].max_rows == 500
        assert configs["default"].pool_size == 10
        assert configs["default"].pool_overflow == 20


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


class TestBuildPostgresUrl:
    def test_full_config(self, monkeypatch):
        monkeypatch.setenv("POSTGRES_HOST", "127.0.0.1")
        monkeypatch.setenv("POSTGRES_PORT", "5431")
        monkeypatch.setenv("POSTGRES_USER", "ainowork")
        monkeypatch.setenv("POSTGRES_PASSWORD", "Abc@1234")
        monkeypatch.setenv("POSTGRES_DB", "ainowork")
        url = _build_postgres_url()
        assert url == "postgresql+asyncpg://ainowork:Abc%401234@127.0.0.1:5431/ainowork"

    def test_no_host_returns_none(self, monkeypatch):
        monkeypatch.delenv("POSTGRES_HOST", raising=False)
        assert _build_postgres_url() is None

    def test_defaults(self, monkeypatch):
        _clear_friendly_vars(monkeypatch)
        monkeypatch.setenv("POSTGRES_HOST", "localhost")
        url = _build_postgres_url()
        assert url == "postgresql+asyncpg://postgres@localhost:5432/postgres"


class TestBuildMysqlUrl:
    def test_no_host_returns_none(self, monkeypatch):
        monkeypatch.delenv("MYSQL_HOST", raising=False)
        assert _build_mysql_url() is None

    def test_full_config(self, monkeypatch):
        monkeypatch.setenv("MYSQL_HOST", "db.example.com")
        monkeypatch.setenv("MYSQL_PORT", "3307")
        monkeypatch.setenv("MYSQL_USER", "app")
        monkeypatch.setenv("MYSQL_PASSWORD", "secret")
        monkeypatch.setenv("MYSQL_DB", "appdb")
        url = _build_mysql_url()
        assert url == "mysql+aiomysql://app:secret@db.example.com:3307/appdb"


class TestBuildOracleUrl:
    def test_no_host_returns_none(self, monkeypatch):
        monkeypatch.delenv("ORACLE_HOST", raising=False)
        assert _build_oracle_url() is None

    def test_full_config(self, monkeypatch):
        monkeypatch.setenv("ORACLE_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_PORT", "1522")
        monkeypatch.setenv("ORACLE_USER", "scott")
        monkeypatch.setenv("ORACLE_PASSWORD", "tiger")
        monkeypatch.setenv("ORACLE_SERVICE_NAME", "ORCLPDB1")
        url = _build_oracle_url()
        assert "oracle+oracledb://scott:tiger@127.0.0.1:1522/" in url
        assert "service_name=ORCLPDB1" in url
