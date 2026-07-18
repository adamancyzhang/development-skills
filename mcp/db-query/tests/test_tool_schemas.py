"""Print MCP tool schemas — run with pytest -s to see full output.

Usage:
    uv run pytest tests/test_tool_schemas.py -s
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_print_tool_schemas():
    """Connect to the MCP server and print all tool schemas."""
    project_dir = os.path.join(os.path.dirname(__file__), "..")

    params = StdioServerParameters(
        command="uv",
        args=["run", "--directory", project_dir, "python", "-m", "db_query.server"],
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()

            print(f"\n{'=' * 70}")
            print(f"  MCP Server: db-query  |  Tools: {len(tools.tools)}")
            print(f"{'=' * 70}")

            for t in tools.tools:
                print(f"\n{'─' * 70}")
                print(f"  Tool: {t.name}")
                print(f"{'─' * 70}")
                print(f"  Description: {t.description}")

                print(f"\n  Input Parameters:")
                for pname, pinfo in t.inputSchema.get("properties", {}).items():
                    e = f" [enum: {pinfo['enum']}]" if "enum" in pinfo else ""
                    d = f" [default: {pinfo['default']}]" if "default" in pinfo else ""
                    req = " *required" if pname in t.inputSchema.get("required", []) else ""
                    print(f"    {pname}{req}{e}{d}")
                    print(f"      {pinfo.get('description', '')}")

                    # Show nested properties for list-of-object params
                    items = pinfo.get("items") or {}
                    for nested_ref in pinfo.get("anyOf", []):
                        if nested_ref.get("type") == "array":
                            items = nested_ref.get("items", {})
                    nested = items.get("properties", {})
                    if nested:
                        for nname, ninfo in nested.items():
                            ne = f" [enum: {ninfo['enum']}]" if "enum" in ninfo else ""
                            nd = f" [default: {ninfo['default']}]" if "default" in ninfo else ""
                            nreq = " *required" if nname in items.get("required", []) else ""
                            print(f"      └─ {nname}{nreq}{ne}{nd}: {ninfo.get('description', '')}")

                print(f"\n  Output:")
                out = getattr(t, "outputSchema", {})
                out_props = (
                    out.get("properties", {})
                    .get("result", {})
                    .get("items", {})
                    .get("properties", {})
                ) or out.get("properties", {})
                for oname, oinfo in out_props.items():
                    od = f" [default: {oinfo['default']}]" if "default" in oinfo else ""
                    print(f"    {oname}{od}: {oinfo.get('description', '')}")

            print(f"\n{'=' * 70}")
            print(f"  Schema dump complete.")
            print(f"{'=' * 70}\n")
