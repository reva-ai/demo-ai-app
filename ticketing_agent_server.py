"""ticketing-agent — a sub-agent the orchestrator delegates to, exposed as MCP.

Why MCP and not a plain HTTP endpoint: Kong only authorizes traffic on its
routes. As an MCP server, "orchestrator delegates to ticketing" is an MCP tool
call that traverses Kong and can be allowed or denied by Reva.

Kong route / path segment must be `ticketing-agent` so resource ids match
`ticketing-agent/{tool}`.

Run:
    .venv/bin/python ticketing_agent_server.py       # http://127.0.0.1:8003/mcp
"""

import os

from fastmcp import FastMCP

import gateway

mcp = FastMCP("ticketing-agent")

# This sub-agent is itself an agent: when asked to open a ticket it does its own
# reasoning by calling a model through Kong under its OWN identity
# ("ticketing-agent"). That second model call is authorized by Reva separately
# from the orchestrator's — which is what makes this genuine agent-to-agent.
AGENT_ID = "ticketing-agent"
_TICKETS: dict[str, dict] = {}


async def _triage(summary: str) -> dict:
    """Ask a model (as this agent) to classify the issue. Returns triage or a note."""
    try:
        r = await gateway.chat(
            [
                {"role": "system", "content": "You are a support ticketing agent. Reply in one short "
                 "line: a priority (LOW, MEDIUM, or HIGH) and a five-word triage note."},
                {"role": "user", "content": summary},
            ],
            agent_id=AGENT_ID,
        )
        return {"triage": (r.choices[0].message.content or "").strip(),
                "reasoned_by": f"{AGENT_ID} (own model call via Kong)"}
    except Exception as e:  # noqa: BLE001
        if isinstance(e, gateway.AuthorizationDenied) or "Blocked by Reva" in str(e):
            return {"triage": None,
                    "note": f"{AGENT_ID}'s own model call was DENIED by Reva — ticket opened without triage."}
        return {"triage": None, "note": f"{AGENT_ID} could not reason: {str(e)[:100]}"}


@mcp.tool
async def create_ticket(customer_id: str, summary: str) -> dict:
    """Open a support ticket. The ticketing-agent triages it via its own model call."""
    ticket_id = f"TKT-{1000 + len(_TICKETS)}"
    _TICKETS[ticket_id] = {"customer_id": customer_id, "summary": summary, "status": "open"}
    result = {"ticket_id": ticket_id, "status": "open", "customer_id": customer_id}
    result.update(await _triage(summary))
    return result


@mcp.tool
def close_ticket(ticket_id: str) -> dict:
    """Close an open support ticket. Privileged: a policy may forbid this."""
    if ticket_id not in _TICKETS:
        return {"error": "no such ticket", "ticket_id": ticket_id}
    _TICKETS[ticket_id]["status"] = "closed"
    return {"ticket_id": ticket_id, "status": "closed"}


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", "8003")))
