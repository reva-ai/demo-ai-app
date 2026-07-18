"""booking-agent — the second sub-agent, exposed over A2A for the same reason.

Companion to ticketing_agent_server.py. Two sub-agents rather than one because
agent-to-agent traffic needs a choice: a policy can permit one delegation while
forbidding the other.

Kong A2A route path segment must be `booking-agent`.

Run:
    .venv/bin/python booking_agent_server.py         # http://127.0.0.1:8004/
"""

from __future__ import annotations

import re
from typing import Any

from a2a.types import AgentSkill

import a2a_agent

_SLOTS = ["2026-07-14T10:00Z", "2026-07-14T14:00Z", "2026-07-15T09:00Z"]
_SLOT_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z")


async def handle(
    text: str,
    history: list[dict[str, Any]],
    user: str | None,
    session_id: str | None,
    *,
    traceparent: str | None = None,
) -> str:
    """Delegated task from the orchestrator: list or book a callback slot."""
    del history, user, session_id, traceparent  # no nested Kong calls
    lowered = text.lower()
    if "list" in lowered or "available" in lowered or "slot" in lowered and "book" not in lowered:
        return "Available callback slots: " + ", ".join(_SLOTS)

    wanted = _SLOT_RE.search(text)
    slot = wanted.group(0) if wanted else _SLOTS[0]
    if slot not in _SLOTS:
        return f"Slot {slot} is unavailable. Options: " + ", ".join(_SLOTS)
    return f"Booked callback slot {slot}."


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
