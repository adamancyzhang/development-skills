"""Dump raw MCP tool JSON schemas to tests/tool_schemas.json.

Usage:
    uv run pytest tests/test_tool_schemas.py -s
"""

from __future__ import annotations

import json
import os

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_print_tool_schemas():
    """Connect to the MCP server and write raw JSON schemas to a file."""
    project_dir = os.path.join(os.path.dirname(__file__), "..")
    out_path = os.path.join(os.path.dirname(__file__), "tool_schemas.json")

    params = StdioServerParameters(
        command="uv",
        args=["run", "--directory", project_dir, "python", "-m", "db_query.server"],
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()

            data = [t.model_dump() for t in tools.tools]
            with open(out_path, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"Wrote {len(data)} tool schemas to {out_path}")
