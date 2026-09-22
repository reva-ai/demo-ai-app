"""ticketing-mcp — canned ticketing tools for ticketing-agent's own tool-calling loop.

Kong proxies to this service; the Kong plugin asks Reva before each tool runs.
No state, no validation: every call returns a fixed, demo-shaped payload. Real
safety (what's allowed to run) is Reva's job, not this code's.

Run:
    .venv/bin/python ticketing_mcp_server.py        # http://127.0.0.1:8005/mcp
"""

import os

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

mcp = FastMCP("ticketing-mcp")


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(request: Request) -> JSONResponse:
    """Liveness check, outside the MCP protocol."""
    return JSONResponse({"status": "ok"})


@mcp.tool
def open_ticket(summary: str, customer_id: str = "c1") -> dict:
    """Open a new support ticket for a customer and return its id."""
    return {
        "ticket_id": "TKT-1001",
        "status": "open",
        "summary": summary,
        "customerId": customer_id,
        "note": "ALLOWED by Reva — permitted tool, no forbid.",
    }


@mcp.tool
def close_ticket(ticket_id: str) -> dict:
    """Close an open support ticket by id. Privileged: a policy may forbid this."""
    return {
        "ticket_id": ticket_id,
        "status": "closed",
        "note": "ALLOWED by Reva — permitted tool, no forbid.",
    }


@mcp.tool
def get_ticket_status(ticket_id: str) -> dict:
    """Look up the status of an existing support ticket by id."""
    return {
        "ticket_id": ticket_id,
        "status": "open",
        "summary": "Demo ticket — canned status, no real store behind this.",
        "note": "ALLOWED by Reva — permitted tool, no forbid.",
    }


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", "8005")))
