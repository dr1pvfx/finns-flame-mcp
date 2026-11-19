"""Call the local stdio MCP server once from a desktop integration."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def call(tool: str, args: dict[str, Any], expected_pid: int | None = None) -> dict[str, Any]:
    server = StdioServerParameters(
        command=sys.executable, args=["-m", "flame_mcp"], env=dict(os.environ)
    )
    async with stdio_client(server) as (reader, writer), ClientSession(reader, writer) as client:
        await client.initialize()
        if expected_pid is not None:
            info = await client.call_tool("flame_version_info", {})
            payload = info.structured_content
            bridge = (
                payload.get("result", {}).get("bridge", {}) if isinstance(payload, dict) else {}
            )
            if not bridge.get("reachable") or bridge.get("pid") != expected_pid:
                raise ValueError("The local MCP is not connected to this Flame process.")
        result = await client.call_tool(tool, args)
        payload = result.structured_content
        if not isinstance(payload, dict):
            raise ValueError("The MCP response has no structured result.")
        return dict(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tool",
        default="flame_do",
        choices=("flame_do", "flame_version_info", "flame_catalog", "flame_context"),
    )
    parser.add_argument("--expect-flame-pid", type=int, help="Require this live Flame process.")
    opts = parser.parse_args()
    try:
        raw = sys.stdin.buffer.read(65_537)
        if len(raw) > 65_536:
            raise ValueError("An MCP request may contain at most 65,536 bytes.")
        args = json.loads(raw or b"{}")
        if not isinstance(args, dict):
            raise ValueError("Use a JSON object for MCP arguments.")
    except ValueError as exc:
        parser.exit(2, f"{exc}\n")

    async def once() -> dict[str, Any]:
        with anyio.fail_after(40):
            return await call(opts.tool, args, opts.expect_flame_pid)

    try:
        result = anyio.run(once)
    except Exception as exc:
        parser.exit(1, f"Local Flame MCP call failed ({type(exc).__name__}).\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
