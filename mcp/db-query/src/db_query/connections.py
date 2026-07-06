from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from .config import DbConfig
from .exceptions import UnknownDatabaseError


class ConnectionManager:
    """Manages lifecycle of SQLAlchemy async engines per DbConfig.

    Engines are created lazily on first use and cached. All engines
    are disposed on close_all() during server shutdown.
    """

    _engines: dict[str, AsyncEngine] = {}
    _configs: dict[str, DbConfig] = {}

    @classmethod
    def initialize(cls, configs: dict[str, DbConfig]) -> None:
        """Store configs. Engines are created lazily on first use."""
        cls._configs = configs

    @classmethod
    def get_engine(cls, name: str) -> AsyncEngine:
        """Get or create the async engine for a named connection."""
        if name not in cls._engines:
            config = cls._get_config(name)
            cls._engines[name] = create_async_engine(
                config.url,
                pool_size=config.pool_size,
                max_overflow=config.pool_overflow,
                pool_pre_ping=True,
                connect_args=config.connect_args,
            )
        return cls._engines[name]

    @classmethod
    async def close_all(cls) -> None:
        """Dispose all engines gracefully during server shutdown."""
        for name, engine in cls._engines.items():
            await engine.dispose()
        cls._engines.clear()

    @classmethod
    def get_dialect(cls, name: str) -> str:
        return cls._get_config(name).dialect

    @classmethod
    def get_max_rows(cls, name: str) -> int:
        return cls._get_config(name).max_rows

    @classmethod
    def list_databases(cls) -> list[str]:
        return sorted(cls._configs.keys())

    @classmethod
    def _get_config(cls, name: str) -> DbConfig:
        if name not in cls._configs:
            raise UnknownDatabaseError(
                f"Unknown database: {name!r}. "
                f"Available: {', '.join(sorted(cls._configs.keys()))}"
            )
        return cls._configs[name]
