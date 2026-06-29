# ABOUTME: A tiny throwaway MCP server (FastMCP, stdio transport) that exposes a single
# ABOUTME: mock NetSuite posting tool. No real ERP, no network, no secrets - synthetic only.
"""NetSuite (MOCK) MCP server.

Exposes one tool, ``post_invoice_to_netsuite``, over the stdio transport. The tool
wraps the same mock posting logic the Poster node used to inline (generate an
``NS-POST-#####`` transaction id plus a timestamp). It is intentionally minimal and
self-contained so a judge can run it directly and watch a real MCP client/server
round-trip happen. Nothing here talks to a real NetSuite instance.
"""

import random
import sys
from datetime import datetime

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("netsuite-mock")


@mcp.tool()
def post_invoice_to_netsuite(
    invoice_id: str,
    vendor: str,
    amount: float,
    gl_account: str,
) -> dict:
    """Post an approved AP invoice to the (mock) NetSuite ERP and return the result.

    This is a synthetic stand-in for a real NetSuite posting call. It generates a
    deterministic-shaped transaction id and a timestamp, exactly mirroring the mock
    logic the agent used before the MCP integration existed.

    Args:
        invoice_id: The internal invoice identifier being posted.
        vendor: The vendor name on the invoice.
        amount: The total dollar amount being posted.
        gl_account: The GL account the entry is coded to.

    Returns:
        A dict with ``transaction_id``, ``status``, and ``timestamp``.
    """
    transaction_id = f"NS-POST-{random.randint(10000, 99999)}"
    timestamp = datetime.now().isoformat()

    # Emit a server-side log line to stderr so an observer can see the tool fire.
    # stdout is reserved for the MCP protocol, so logging MUST go to stderr.
    print(
        f"[netsuite-mock-mcp] post_invoice_to_netsuite called: "
        f"invoice_id={invoice_id} vendor={vendor!r} amount={amount} "
        f"gl_account={gl_account} -> transaction_id={transaction_id}",
        file=sys.stderr,
        flush=True,
    )

    return {
        "transaction_id": transaction_id,
        "status": "posted",
        "timestamp": timestamp,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
