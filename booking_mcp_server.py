"""booking-mcp — canned scheduling tools for booking-agent's own tool-calling loop.

No slot-existence validation here on purpose: the tool always confirms
whatever slot the model asks to book. Policy safety is Reva's job, not this
code's.

Run:
    .venv/bin/python booking_mcp_server.py           # http://127.0.0.1:8006/mcp
"""

import os

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

mcp = FastMCP("booking-mcp")


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(request: Request) -> JSONResponse:
    """Liveness check, outside the MCP protocol."""
    return JSONResponse({"status": "ok"})


_SLOTS = ["2026-07-14T10:00Z", "2026-07-14T14:00Z", "2026-07-15T09:00Z"]


@mcp.tool
def list_slots() -> dict:
    """List available callback slots for a customer support call."""
    return {"slots": _SLOTS, "note": "ALLOWED by Reva — permitted tool, no forbid."}


@mcp.tool
def book_slot(slot: str, customer_id: str = "c1") -> dict:
    """Book a callback slot for a customer. Confirms whatever slot is given."""
    return {
        "slot": slot,
        "status": "booked",
        "customerId": customer_id,
        "note": "ALLOWED by Reva — permitted tool, no forbid.",
    }


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", "8006")))
