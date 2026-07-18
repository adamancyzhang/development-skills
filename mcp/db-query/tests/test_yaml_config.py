"""Tests for YAML-based database configuration."""

from __future__ import annotations

import textwrap

import pytest

from db_query.config import (
    _build_configs_from_yaml,
    _build_db_config_from_yaml,
    _build_url_from_yaml,
)
from db_query.exceptions import ConfigurationError


class TestBuildUrlFromYaml:
    def test_postgresql_full(self):
        url = _build_url_from_yaml(
            "postgresql",
            {
                "host": "127.0.0.1",
                "port": 5431,
                "user": "ainowork",
                "password": "Abc@1234",
                "database": "ainowork",
            },
        )
        assert url == "postgresql+asyncpg://ainowork:Abc%401234@127.0.0.1:5431/ainowork"

    def test_postgresql_minimal(self):
        url = _build_url_from_yaml(
            "postgresql",
            {"host": "db.example.com", "database": "mydb"},
        )
        assert url == "postgresql+asyncpg://db.example.com/mydb"

    def test_postgresql_without_password(self):
        url = _build_url_from_yaml(
            "postgresql",
            {"host": "127.0.0.1", "user": "myuser", "database": "mydb"},
        )
        assert "myuser@127.0.0.1" in url
        assert "/mydb" in url

    def test_mysql(self):
        url = _build_url_from_yaml(
            "mysql",
            {
                "host": "127.0.0.1",
                "port": 3306,
                "user": "root",
                "password": "secret",
                "database": "mydb",
            },
        )
        assert url == "mysql+aiomysql://root:secret@127.0.0.1:3306/mydb"

    def test_oracle(self):
        url = _build_url_from_yaml(
            "oracle",
            {
                "host": "127.0.0.1",
                "port": 1521,
                "user": "scott",
                "password": "tiger",
                "service_name": "XEPDB1",
            },
        )
        assert "oracle+oracledb://scott:tiger@127.0.0.1:1521/" in url
        assert "service_name=XEPDB1" in url

    def test_unsupported_type(self):
        with pytest.raises(ConfigurationError, match="Unsupported"):
            _build_url_from_yaml("mongodb", {"host": "localhost"})


class TestBuildDbConfigFromYaml:
    def test_defaults(self):
        cfg = _build_db_config_from_yaml(
            "main",
            {"host": "127.0.0.1", "database": "test"},
        )
        assert cfg.name == "main"
        assert cfg.dialect == "postgresql"
        assert cfg.max_rows == 500
        assert cfg.pool_size == 5
        assert cfg.pool_overflow == 10

    def test_overrides(self):
        cfg = _build_db_config_from_yaml(
            "analytics",
            {
                "type": "mysql",
                "host": "127.0.0.1",
                "database": "analytics",
                "max_rows": 200,
                "pool_size": 10,
                "pool_overflow": 20,
            },
        )
        assert cfg.name == "analytics"
        assert cfg.dialect == "mysql"
        assert cfg.max_rows == 200
        assert cfg.pool_size == 10
        assert cfg.pool_overflow == 20


class TestBuildConfigsFromYaml:
    def test_multiple_databases(self):
        entries = {
            "main": {
                "host": "127.0.0.1",
                "port": 5431,
                "user": "app",
                "password": "p1",
                "database": "maindb",
            },
            "analytics": {
                "type": "postgresql",
                "host": "127.0.0.1",
                "port": 5432,
                "user": "reader",
                "password": "p2",
                "database": "analytics",
            },
        }
        configs = _build_configs_from_yaml(entries)
        assert set(configs.keys()) == {"main", "analytics"}
        assert configs["main"].dialect == "postgresql"
        assert configs["analytics"].dialect == "postgresql"
        assert "maindb" in configs["main"].url
        assert "analytics" in configs["analytics"].url

    def test_mixed_types(self):
        entries = {
            "pg": {
                "host": "127.0.0.1",
                "database": "pgdb",
                "max_rows": 100,
            },
            "my": {
                "type": "mysql",
                "host": "127.0.0.1",
                "database": "mydb",
            },
            "ora": {
                "type": "oracle",
                "host": "127.0.0.1",
                "service_name": "ORCL",
            },
        }
        configs = _build_configs_from_yaml(entries)
        assert set(configs.keys()) == {"pg", "my", "ora"}
        assert configs["pg"].dialect == "postgresql"
        assert configs["my"].dialect == "mysql"
        assert configs["ora"].dialect == "oracle"
        assert configs["pg"].max_rows == 100
        assert configs["my"].max_rows == 500
