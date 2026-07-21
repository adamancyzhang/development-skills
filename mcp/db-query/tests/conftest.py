from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from db_query.config import DbConfig
from db_query.connections import ConnectionManager


@pytest.fixture
async def sqlite_engine() -> AsyncEngine:
    """Create an in-memory SQLite database with test schema."""
    engine = create_async_engine("sqlite+aiosqlite://")

    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE
            )
        """))
        await conn.execute(text("""
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                total REAL NOT NULL CHECK (total > 0),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """))
        await conn.execute(text("""
            CREATE INDEX idx_orders_user_id ON orders (user_id)
        """))
        await conn.execute(text(
            "INSERT INTO users VALUES (1, 'Alice', 'alice@example.com')"
        ))
        await conn.execute(text(
            "INSERT INTO users VALUES (2, 'Bob', 'bob@example.com')"
        ))
        await conn.execute(text(
            "INSERT INTO orders VALUES (1, 1, 100.0)"
        ))
        await conn.execute(text(
            "INSERT INTO orders VALUES (2, 1, 200.0)"
        ))
        await conn.execute(text(
            "INSERT INTO orders VALUES (3, 2, 50.0)"
        ))

    yield engine
    await engine.dispose()


@pytest.fixture
def sqlite_config(sqlite_engine) -> DbConfig:
    return DbConfig(
        name="test",
        url="sqlite+aiosqlite://",
        dialect="sqlite",
        max_rows=100,
    )


@pytest.fixture(autouse=True)
def disable_yaml_config(monkeypatch):
    """Prevent tests from picking up a real databases.yaml file."""
    monkeypatch.setenv("DB_CONFIG_PATH", "/nonexistent/path")


@pytest.fixture(autouse=True)
def setup_connection_manager(monkeypatch):
    """Reset ConnectionManager before each test."""
    ConnectionManager._engines.clear()
    ConnectionManager._configs.clear()
    yield
    ConnectionManager._engines.clear()
    ConnectionManager._configs.clear()
