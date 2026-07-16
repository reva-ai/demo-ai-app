"""external-mcp — a demo MCP server standing in for an untrusted third-party tool.

Companion to billing_mcp_server.py. Its one tool, `analytics_probe`, exists in
the Reva policy store as Tool entity "external-mcp/analytics_probe" and carries
a forbid: the agent is wired up to call it, and Reva refuses anyway.

It lives in its own server (not billing-mcp) because resource ids are
`{server}/{tool}`. Kong route path must be `external-mcp`.

Run:
    .venv/bin/python external_mcp_server.py        # http://127.0.0.1:8002/mcp
"""

import os

from fastmcp import FastMCP

mcp = FastMCP("external-mcp")


@mcp.tool
def analytics_probe(query: str) -> dict:
    """Third-party analytics probe. A Reva forbid blocks this before it runs.

    If you can read this payload, Kong did not deny — check the plugin and route.
    """
    return {
        "query": query,
        "exfiltrated": "customer emails, invoice totals",
        "note": "If you can see this, the external-tool forbid did not fire.",
    }


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", "8002")))
