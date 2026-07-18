from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote, urlparse

from dotenv import load_dotenv

from .exceptions import ConfigurationError

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

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
    """Build DbConfig dict from YAML file or environment variables.

    Precedence:
    1. YAML file at DB_CONFIG_PATH or ./databases.yaml
    2. Environment variables (.env, friendly vars, DB_<NAME>_URL)

    Returns a dict mapping connection name -> DbConfig.
    """
    _ensure_dotenv()

    configs = _try_load_yaml()
    if configs is not None:
        return configs

    return _load_from_env()

def _load_from_env() -> dict[str, DbConfig]:
    """Fallback: build DbConfig dict from environment variables.

    Collects connections from two sources:
    1. Friendly per-database env vars (POSTGRES_*, MYSQL_*, ORACLE_*)
    2. Explicit SQLAlchemy URLs (DB_<NAME>_URL)
    Explicit URLs take precedence over friendly vars for the same name.
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

    existing_names = {name for name, _ in url_entries}
    _fill_from_friendly_vars(url_entries, existing_names)

    if not url_entries:
        raise ConfigurationError(
            "No database connections configured. "
            "Create a databases.yaml file, set POSTGRES_* in .env, "
            "or set at least one DB_<NAME>_URL environment variable."
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


# ── YAML loading ───────────────────────────────────────────────────────────


def _resolve_yaml_path() -> Path | None:
    """Find the YAML config file path.

    1. DB_CONFIG_PATH env var (if set and file exists, use it; if set
       but file doesn't exist, return None — don't fall back)
    2. databases.yaml in current working directory
    Returns None if no file found.
    """
    env_path = os.environ.get("DB_CONFIG_PATH")
    if env_path:
        p = Path(env_path)
        return p if p.exists() else None

    cwd_path = Path("databases.yaml")
    return cwd_path if cwd_path.exists() else None


def _try_load_yaml() -> dict[str, DbConfig] | None:
    """Try to load config from YAML file. Returns None if no YAML found."""
    if yaml is None:
        return None

    yaml_path = _resolve_yaml_path()
    if yaml_path is None:
        return None

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    if not data or "databases" not in data:
        return None

    return _build_configs_from_yaml(data["databases"])


def _build_configs_from_yaml(entries: dict) -> dict[str, DbConfig]:
    """Convert YAML database entries to DbConfig dict."""
    configs: dict[str, DbConfig] = {}
    for name, entry in entries.items():
        configs[name] = _build_db_config_from_yaml(name, entry)
    return configs


def _build_db_config_from_yaml(name: str, entry: dict) -> DbConfig:
    """Build a single DbConfig from a YAML entry."""
    db_type = entry.get("type", "postgresql")
    url = _build_url_from_yaml(db_type, entry)
    return DbConfig(
        name=name,
        url=url,
        dialect=db_type,
        max_rows=entry.get("max_rows", 500),
        pool_size=entry.get("pool_size", 5),
        pool_overflow=entry.get("pool_overflow", 10),
    )


def _build_url_from_yaml(db_type: str, entry: dict) -> str:
    """Build a SQLAlchemy URL from a YAML entry dict."""
    host = entry["host"]
    port = entry.get("port", "")
    user = entry.get("user", "")
    password = entry.get("password", "")
    database = entry.get("database", "")
    service_name = entry.get("service_name", "")

    encoded_user = quote(user, safe="") if user else ""
    encoded_password = quote(password, safe="") if password else ""

    if encoded_user and encoded_password:
        auth = f"{encoded_user}:{encoded_password}@"
    elif encoded_user:
        auth = f"{encoded_user}@"
    else:
        auth = ""

    if db_type == "postgresql":
        driver = "asyncpg"
        netloc = f"{host}:{port}" if port else host
        return f"postgresql+{driver}://{auth}{netloc}/{database}"

    if db_type == "mysql":
        driver = "aiomysql"
        netloc = f"{host}:{port}" if port else host
        return f"mysql+{driver}://{auth}{netloc}/{database}"

    if db_type == "oracle":
        driver = "oracledb"
        netloc = f"{host}:{port}" if port else host
        return f"oracle+{driver}://{auth}{netloc}/?service_name={service_name}"

    raise ConfigurationError(f"Unsupported database type: {db_type!r}")


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
