"""Dump raw MCP tool JSON schemas — run with pytest -s.

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
    """Connect to the MCP server and print raw JSON schemas."""
    project_dir = os.path.join(os.path.dirname(__file__), "..")

    params = StdioServerParameters(
        command="uv",
        args=["run", "--directory", project_dir, "python", "-m", "db_query.server"],
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()

            result = []
            for t in tools.tools:
                result.append({
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.inputSchema,
                    "outputSchema": getattr(t, "outputSchema", None),
                })
            print(json.dumps(result, indent=2, ensure_ascii=False))
