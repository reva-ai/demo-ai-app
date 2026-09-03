"""booking-agent — the second sub-agent, exposed over A2A for the same reason.

Companion to ticketing_agent_server.py. Two sub-agents rather than one because
agent-to-agent traffic needs a choice: a policy can permit one delegation while
forbidding the other.

Kong A2A route path segment must be `booking-agent`.

Like ticketing-agent, this agent makes its own model call (as booking-agent,
via Kong) to interpret the request — a real, independently-governed hop, not
just string matching. The model picks a slot; this code still validates that
pick against the real slot list before ever confirming a booking, so a model
cannot hallucinate a booking for a slot that doesn't exist.

Run:
    .venv/bin/python booking_agent_server.py         # http://127.0.0.1:8004/
"""

from __future__ import annotations

import logging
from typing import Any

from a2a.types import AgentSkill

import a2a_agent
import gateway

log = logging.getLogger("demo.booking")

AGENT_ID = "booking-agent"
_SLOTS = ["2026-07-14T10:00Z", "2026-07-14T14:00Z", "2026-07-15T09:00Z"]

_SYSTEM = (
    "You are a scheduling agent for support callbacks. The only real slots "
    "are: " + ", ".join(_SLOTS) + ". Reply with exactly one of: "
    "LIST (the user wants to see availability), one of the slot timestamps "
    "above verbatim (the user wants to book that specific slot), or NONE "
    "(they want a time that isn't in the list). No other text."
)


def _forward(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if isinstance(m, dict) and m.get("role") in ("user", "assistant") and m.get("content")
    ]


async def _interpret(
    text: str, history: list[dict[str, Any]], user: str | None,
    *, traceparent: str | None, session_id: str | None,
) -> str:
    """Ask a model (as this agent, via Kong) which slot the request means."""
    messages = [{"role": "system", "content": _SYSTEM}, *_forward(history),
                {"role": "user", "content": text}]
    log.info("interpret via kong agent=%s user=%s traceparent=%s",
              AGENT_ID, user or "-", (traceparent or "")[:50] or "(none)")
    r = await gateway.chat(
        messages, agent_id=AGENT_ID, user=user, traceparent=traceparent,
        session_id=session_id,
    )
    return (r.choices[0].message.content or "").strip()


async def handle(
    text: str,
    history: list[dict[str, Any]],
    user: str | None,
    session_id: str | None,
    *,
    traceparent: str | None = None,
) -> str:
    """Delegated task from the orchestrator: list or book a callback slot."""
    log.info("a2a handle text_len=%d history=%d user=%s", len(text or ""), len(history or []), user or "-")
    try:
        verdict = await _interpret(text, history, user, traceparent=traceparent,
                                   session_id=session_id)
    except gateway.AuthorizationDenied:
        log.warning("booking model call DENIED by Reva")
        return "I could not check availability — my own model call was denied by Reva."
    except Exception as e:  # noqa: BLE001
        log.warning("booking model call failed: %s", str(e)[:160])
        return "Available callback slots: " + ", ".join(_SLOTS)

    if verdict in _SLOTS:
        return f"Booked callback slot {verdict}."
    if verdict == "NONE":
        return "That time isn't available. Options: " + ", ".join(_SLOTS)
    return "Available callback slots: " + ", ".join(_SLOTS)


SKILLS = [
    AgentSkill(
        id="list_slots",
        name="List slots",
        description="List available callback slots for a customer support call.",
        tags=["booking", "scheduling"],
        examples=["What callback slots are available?"],
    ),
    AgentSkill(
        id="book_slot",
        name="Book slot",
        description="Book a callback slot for a customer.",
        tags=["booking", "scheduling"],
        examples=["Book the 2026-07-14T10:00Z callback slot for customer c1."],
    ),
]


app = a2a_agent.build_app(
    name="booking-agent",
    description="Scheduling sub-agent: lists and books customer callback slots on delegation.",
    skills=SKILLS,
    handler=handle,
)


if __name__ == "__main__":
    a2a_agent.run(app, default_port="8004")
