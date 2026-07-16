"""billing-mcp — a demo MCP server whose tools exist as Tool entities in the
Reva policy store.

Kong proxies to this service; the Kong plugin asks Reva before the tool runs.
Expected decisions (typical agentic store):

    get_billing_report      ALLOW
    get_compliance_status   ALLOW
    get_customer_pii        DENY (forbid)

Server name `billing-mcp` is load-bearing: Reva resource ids are usually
`{server}/{tool}` (e.g. billing-mcp/get_customer_pii). Kong route path segments
must match.

`analytics_probe` lives on external-mcp, not here.

Run:
    .venv/bin/python billing_mcp_server.py          # http://127.0.0.1:8001/mcp
"""

import os

from fastmcp import FastMCP

mcp = FastMCP("billing-mcp")


@mcp.tool
def get_billing_report(customer_id: str) -> dict:
    """Summarised, non-sensitive billing totals for a customer."""
    return {
        "customerId": customer_id,
        "invoices": 3,
        "outstanding": "1240.00",
        "currency": "USD",
        "note": "ALLOWED by Reva — permitted tool, no forbid.",
    }


@mcp.tool
def get_compliance_status(customer_id: str) -> dict:
    """Whether a customer's account is in good compliance standing."""
    return {
        "customerId": customer_id,
        "kyc": "verified",
        "standing": "good",
        "note": "ALLOWED by Reva — permitted tool, no forbid.",
    }


@mcp.tool
def get_customer_pii(customer_id: str) -> dict:
    """Full customer PII. A Reva forbid blocks this before it ever runs.

    If you are reading this payload, Kong did not deny — the tool was invoked.
    """
    return {
        "customerId": customer_id,
        "ssn": "000-00-0000",
        "dob": "1990-01-01",
        "note": "If you can see this, the PII forbid did not fire.",
    }


if __name__ == "__main__":
    # Render (and any PaaS) injects $PORT and needs 0.0.0.0; locally falls back to 8001.
    mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", "8001")))
