from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from .exceptions import ConfigurationError

_URL_KEY_PATTERN = re.compile(r"^DB_([A-Z][A-Z0-9_]*)_URL$")
_MAX_ROWS_KEY_PATTERN = re.compile(r"^DB_([A-Z][A-Z0-9_]*)_MAX_ROWS$")
_POOL_SIZE_KEY_PATTERN = re.compile(r"^DB_([A-Z][A-Z0-9_]*)_POOL_SIZE$")
_POOL_OVERFLOW_KEY_PATTERN = re.compile(r"^DB_([A-Z][A-Z0-9_]*)_POOL_OVERFLOW$")


@dataclass
class DbConfig:
    name: str
    url: str
    dialect: str
    max_rows: int = 100
    pool_size: int = 5
    pool_overflow: int = 10
    connect_args: dict = field(default_factory=dict)


def load_config() -> dict[str, DbConfig]:
    """Scan environment for DB_<NAME>_URL and return DbConfig dict.

    Environment variable convention::

        DB_DEFAULT_URL=postgresql+asyncpg://user:pass@host:5432/mydb
        DB_ANALYTICS_URL=mysql+aiomysql://user:pass@host:3306/analytics
        DB_LEGACY_URL=oracle+oracledb://user:pass@host:1521/SERVICENAME

    Optional per-connection overrides::

        DB_DEFAULT_MAX_ROWS=500
        DB_DEFAULT_POOL_SIZE=5

    Returns a dict mapping lowercase connection name -> DbConfig.
    """
    url_entries: list[tuple[str, str]] = []
    overrides: dict[str, dict] = {}

    for key, value in os.environ.items():
        m = _URL_KEY_PATTERN.match(key)
        if m:
            url_entries.append((m.group(1).lower(), value))
            continue
        m = _MAX_ROWS_KEY_PATTERN.match(key)
        if m:
            overrides.setdefault(m.group(1).lower(), {})["max_rows"] = int(value)
            continue
        m = _POOL_SIZE_KEY_PATTERN.match(key)
        if m:
            overrides.setdefault(m.group(1).lower(), {})["pool_size"] = int(value)
            continue
        m = _POOL_OVERFLOW_KEY_PATTERN.match(key)
        if m:
            overrides.setdefault(m.group(1).lower(), {})["pool_overflow"] = int(value)
            continue

    if not url_entries:
        raise ConfigurationError(
            "No database connections configured. "
            "Set at least one DB_<NAME>_URL environment variable."
        )

    configs: dict[str, DbConfig] = {}
    for name, url in url_entries:
        dialect = _extract_dialect(url)
        extra = overrides.get(name, {})
        configs[name] = DbConfig(
            name=name,
            url=url,
            dialect=dialect,
            max_rows=extra.get("max_rows", 100),
            pool_size=extra.get("pool_size", 5),
            pool_overflow=extra.get("pool_overflow", 10),
        )

    return configs


def _extract_dialect(url: str) -> str:
    """Extract the SQL dialect name from a SQLAlchemy URL.

    >>> _extract_dialect("postgresql+asyncpg://u:p@h/db")
    'postgresql'
    >>> _extract_dialect("mysql+aiomysql://u:p@h/db")
    'mysql'
    >>> _extract_dialect("oracle+oracledb://u:p@h/svc")
    'oracle'
    >>> _extract_dialect("sqlite+aiosqlite:///test.db")
    'sqlite'
    """
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme
        if not scheme:
            return "unknown"
        return scheme.split("+")[0]
    except Exception:
        return "unknown"
