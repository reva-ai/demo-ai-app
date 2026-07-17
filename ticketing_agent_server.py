"""ticketing-agent — a sub-agent the orchestrator delegates to over A2A.

Why A2A: agent-to-agent delegation is a first-class A2A operation. The
orchestrator sends a standard `message/send`; Kong fronts this route and asks
Reva to authorize the `invokeAgent` before the message is delivered. The full
conversation rides in the message (text = current turn, `metadata.chatHistory` =
prior turns), so Reva evaluates with the same context the orchestrator had.

This sub-agent is itself an agent: to triage a request it makes its OWN model
call through Kong under identity `ticketing-agent`. That second call is a
separate Reva evaluation — genuine, independently-governed agent-to-agent.

Kong A2A route path segment must be `ticketing-agent` so the resource id matches.

Run:
    .venv/bin/python ticketing_agent_server.py       # http://127.0.0.1:8003/
"""

from __future__ import annotations

from typing import Any

from a2a.types import AgentSkill

import a2a_agent
import gateway

AGENT_ID = "ticketing-agent"
_TICKETS: dict[str, dict] = {}

_TRIAGE_SYSTEM = (
    "You are a support ticketing agent. Reply in one short line: a priority "
    "(LOW, MEDIUM, or HIGH) and a five-word triage note."
)


def _forward(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Prior turns the orchestrator forwarded → messages for our own model call.

    Including them means THIS agent's /llm hop carries the same chatHistory the
    orchestrator's did (Kong reads it straight from the standard messages array)."""
    return [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if isinstance(m, dict) and m.get("role") in ("user", "assistant") and m.get("content")
    ]


async def _triage(summary: str, history: list[dict[str, Any]], user: str | None) -> str:
    """Ask a model (as this agent, via Kong) to classify the issue."""
    messages = [{"role": "system", "content": _TRIAGE_SYSTEM}, *_forward(history)]
    messages.append({"role": "user", "content": f"Triage this support request: {summary}"})
    try:
        r = await gateway.chat(messages, agent_id=AGENT_ID, user=user)
        return (r.choices[0].message.content or "").strip()
    except Exception as e:  # noqa: BLE001
        if isinstance(e, gateway.AuthorizationDenied) or "Blocked by Reva" in str(e):
            raise
        return ""


async def handle(text: str, history: list[dict[str, Any]], user: str | None, session_id: str | None) -> str:
    """Delegated task from the orchestrator. Opens a ticket and triages it."""
    lowered = text.lower()

    if "close" in lowered:
        for tid in _TICKETS:
            if tid.lower() in lowered:
                _TICKETS[tid]["status"] = "closed"
                return f"Closed ticket {tid}."
        return "No matching open ticket to close."

    ticket_id = f"TKT-{1000 + len(_TICKETS)}"
    _TICKETS[ticket_id] = {"summary": text, "status": "open"}
    try:
        triage = await _triage(text, history, user)
    except gateway.AuthorizationDenied:
        return (f"Opened ticket {ticket_id} (status: open), but I could not triage it — "
                "my own model call was denied by Reva.")
    if triage:
        return f"Opened ticket {ticket_id} (status: open). Triage: {triage}"
    return f"Opened ticket {ticket_id} (status: open); triage unavailable right now."


SKILLS = [
    AgentSkill(
        id="create_ticket",
        name="Create ticket",
        description="Open a support ticket and triage it via the agent's own model call.",
        tags=["ticketing", "support"],
        examples=["Open a ticket for customer c1 about a billing discrepancy."],
    ),
    AgentSkill(
        id="close_ticket",
        name="Close ticket",
        description="Close an open support ticket by id. Privileged: a policy may forbid this.",
        tags=["ticketing", "support"],
        examples=["Close ticket TKT-1000."],
    ),
]


app = a2a_agent.build_app(
    name="ticketing-agent",
    description="Support ticketing sub-agent: opens and triages tickets on delegation.",
    skills=SKILLS,
    handler=handle,
)


if __name__ == "__main__":
    a2a_agent.run(app, default_port="8003")
