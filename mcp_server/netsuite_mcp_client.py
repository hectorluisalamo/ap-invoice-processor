# ABOUTME: Tiny MCP client helper that spawns the NetSuite mock MCP server over stdio
# ABOUTME: and calls its single tool, exposing a sync wrapper for use from sync nodes.
"""MCP client for the NetSuite mock server.

Spawns ``netsuite_mcp_server.py`` as a subprocess over the stdio transport, opens an
MCP client session, calls the ``post_invoice_to_netsuite`` tool, and returns the parsed
result. A synchronous wrapper (:func:`post_invoice_sync`) lets a plain (sync) ADK node
drive the async MCP round-trip without the caller managing an event loop.
"""

import asyncio
import json
import os
import sys
import threading
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_SERVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "netsuite_mcp_server.py")


async def post_invoice_async(
    invoice_id: str,
    vendor: str,
    amount: float,
    gl_account: str,
) -> dict[str, Any]:
    """Connect to the NetSuite mock MCP server over stdio and post one invoice.

    Returns the tool's structured result: ``{transaction_id, status, timestamp}``.
    """
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[_SERVER_PATH],
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "post_invoice_to_netsuite",
                arguments={
                    "invoice_id": invoice_id,
                    "vendor": vendor,
                    "amount": amount,
                    "gl_account": gl_account,
                },
            )
            return _extract_tool_result(result)


def _extract_tool_result(result: Any) -> dict[str, Any]:
    """Pull the dict payload out of an MCP CallToolResult.

    Prefers ``structured_content`` (FastMCP wraps a dict return), falling back to
    parsing the first text content block as JSON.
    """
    structured = getattr(result, "structuredContent", None) or getattr(
        result, "structured_content", None
    )
    if isinstance(structured, dict):
        # FastMCP wraps a bare dict return under a "result" key.
        if set(structured.keys()) == {"result"} and isinstance(structured["result"], dict):
            return structured["result"]
        return structured

    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                continue

    raise RuntimeError(f"Could not parse MCP tool result: {result!r}")


def post_invoice_sync(
    invoice_id: str,
    vendor: str,
    amount: float,
    gl_account: str,
) -> dict[str, Any]:
    """Synchronous wrapper around :func:`post_invoice_async`.

    Runs the async MCP round-trip to completion and returns its result. Safe to call
    from a synchronous node even when an outer event loop is already running: in that
    case it executes the coroutine on a dedicated background thread (with its own loop)
    to avoid ``asyncio.run`` failing inside a running loop.
    """
    coro_factory = lambda: post_invoice_async(invoice_id, vendor, amount, gl_account)

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No running loop in this thread: simplest path.
        return asyncio.run(coro_factory())

    # A loop is already running in this thread; offload to a worker thread.
    box: dict[str, Any] = {}

    def _worker() -> None:
        try:
            box["result"] = asyncio.run(coro_factory())
        except BaseException as exc:  # noqa: BLE001 - re-raised on caller thread
            box["error"] = exc

    t = threading.Thread(target=_worker)
    t.start()
    t.join()

    if "error" in box:
        raise box["error"]
    return box["result"]
