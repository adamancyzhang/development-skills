from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from urllib.parse import quote, urlparse

from dotenv import load_dotenv

from .exceptions import ConfigurationError

_URL_KEY_PATTERN = re.compile(r"^DB_([A-Z][A-Z0-9_]*)_URL$")
_MAX_ROWS_KEY_PATTERN = re.compile(r"^DB_([A-Z][A-Z0-9_]*)_MAX_ROWS$")
_POOL_SIZE_KEY_PATTERN = re.compile(r"^DB_([A-Z][A-Z0-9_]*)_POOL_SIZE$")
_POOL_OVERFLOW_KEY_PATTERN = re.compile(r"^DB_([A-Z][A-Z0-9_]*)_POOL_OVERFLOW$")

_ENV_LOADED = False


@dataclass
class DbConfig:
    name: str
    url: str
    dialect: str
    max_rows: int = 500
    pool_size: int = 5
    pool_overflow: int = 10
    connect_args: dict = field(default_factory=dict)


def load_config() -> dict[str, DbConfig]:
    """Build DbConfig dict from environment variables.

    Loads .env file first, then collects connections from two sources
    (explicit URLs take precedence over friendly vars):

    1. Friendly per-database env vars::

        POSTGRES_HOST=127.0.0.1
        POSTGRES_PORT=5431
        POSTGRES_USER=ainowork
        POSTGRES_PASSWORD=Abc@1234
        POSTGRES_DB=ainowork

        MYSQL_HOST=127.0.0.1
        MYSQL_PORT=3306
        MYSQL_USER=root
        MYSQL_PASSWORD=secret
        MYSQL_DB=mydb

        ORACLE_HOST=127.0.0.1
        ORACLE_PORT=1521
        ORACLE_USER=scott
        ORACLE_PASSWORD=tiger
        ORACLE_SERVICE_NAME=XEPDB1

    2. Explicit SQLAlchemy URLs (backward compatible)::

        DB_DEFAULT_URL=postgresql+asyncpg://user:pass@host:5432/mydb
        DB_ANALYTICS_URL=mysql+aiomysql://user:pass@host:3306/analytics

    Optional per-connection overrides::

        DB_DEFAULT_MAX_ROWS=500
        DB_DEFAULT_POOL_SIZE=10
        DB_DEFAULT_POOL_OVERFLOW=20

    Returns a dict mapping lowercase connection name -> DbConfig.
    """
    _ensure_dotenv()

    url_entries: list[tuple[str, str]] = []
    overrides: dict[str, dict] = {}

    # Phase 1: Collect explicit DB_<NAME>_URL entries
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

    existing_names = {name for name, _ in url_entries}

    # Phase 2: Fill in from friendly env vars (only if name not already taken)
    _fill_from_friendly_vars(url_entries, existing_names)

    if not url_entries:
        raise ConfigurationError(
            "No database connections configured. "
            "Set POSTGRES_* environment variables in .env "
            "or at least one DB_<NAME>_URL environment variable."
        )

    configs: dict[str, DbConfig] = {}
    for name, url in url_entries:
        dialect = _extract_dialect(url)
        extra = overrides.get(name, {})
        configs[name] = DbConfig(
            name=name,
            url=url,
            dialect=dialect,
            max_rows=extra.get("max_rows", 500),
            pool_size=extra.get("pool_size", 5),
            pool_overflow=extra.get("pool_overflow", 10),
        )

    return configs


# ── .env loading ──────────────────────────────────────────────────────────


def _ensure_dotenv() -> None:
    """Load .env file once at module level."""
    global _ENV_LOADED
    if not _ENV_LOADED:
        load_dotenv()
        _ENV_LOADED = True


# ── Friendly env var builders ─────────────────────────────────────────────


def _build_postgres_url() -> str | None:
    """Build PostgreSQL SQLAlchemy URL from POSTGRES_* env vars."""
    host = os.environ.get("POSTGRES_HOST")
    if not host:
        return None
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "")
    db = os.environ.get("POSTGRES_DB", "postgres")
    encoded_user = quote(user, safe="")
    auth = f"{encoded_user}:{quote(password, safe='')}@" if password else f"{encoded_user}@"
    return f"postgresql+asyncpg://{auth}{host}:{port}/{db}"


def _build_mysql_url() -> str | None:
    """Build MySQL SQLAlchemy URL from MYSQL_* env vars."""
    host = os.environ.get("MYSQL_HOST")
    if not host:
        return None
    port = os.environ.get("MYSQL_PORT", "3306")
    user = os.environ.get("MYSQL_USER", "root")
    password = os.environ.get("MYSQL_PASSWORD", "")
    db = os.environ.get("MYSQL_DB", "mysql")
    encoded_user = quote(user, safe="")
    auth = f"{encoded_user}:{quote(password, safe='')}@" if password else f"{encoded_user}@"
    return f"mysql+aiomysql://{auth}{host}:{port}/{db}"


def _build_oracle_url() -> str | None:
    """Build Oracle SQLAlchemy URL from ORACLE_* env vars."""
    host = os.environ.get("ORACLE_HOST")
    if not host:
        return None
    port = os.environ.get("ORACLE_PORT", "1521")
    user = os.environ.get("ORACLE_USER", "system")
    password = os.environ.get("ORACLE_PASSWORD", "")
    service = os.environ.get("ORACLE_SERVICE_NAME", "XEPDB1")
    encoded_user = quote(user, safe="")
    auth = f"{encoded_user}:{quote(password, safe='')}@" if password else f"{encoded_user}@"
    return f"oracle+oracledb://{auth}{host}:{port}/?service_name={service}"


_FRIENDLY_BUILDERS: list[tuple[str, callable]] = [
    ("default", _build_postgres_url),   # POSTGRES_* → "default"
    ("mysql", _build_mysql_url),         # MYSQL_*    → "mysql"
    ("oracle", _build_oracle_url),       # ORACLE_*   → "oracle"
]


def _fill_from_friendly_vars(
    url_entries: list[tuple[str, str]],
    existing_names: set[str],
) -> None:
    """Append URL entries from friendly env vars, skipping taken names."""
    for name, builder in _FRIENDLY_BUILDERS:
        if name not in existing_names:
            url = builder()
            if url is not None:
                url_entries.append((name, url))


# ── Dialect extraction ────────────────────────────────────────────────────


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
