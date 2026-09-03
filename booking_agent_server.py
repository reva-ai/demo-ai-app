"""booking-agent — the second sub-agent, exposed over A2A for the same reason.
Companion to ticketing_agent_server.py, structurally identical: a real LLM
tool-calling loop against its own MCP server (booking-mcp), no keyword logic
anywhere in this file.

Kong A2A route path segment must be `booking-agent`.

Run:
    .venv/bin/python booking_agent_server.py         # http://127.0.0.1:8004/
"""

from __future__ import annotations

import json
import logging

from a2a.types import AgentSkill

import a2a_agent
import gateway
import llm_agent

log = logging.getLogger("demo.booking")

AGENT_ID = "booking-agent"
MCP_SERVER = "booking-mcp"

SYSTEM = """You are a scheduling agent for customer support callbacks. Use \
your tools to list available callback slots and book a slot for the user's \
request. Use tools when needed, then reply in clear, natural language — \
never claim a slot is booked unless a tool told you it was.

Some tools may be refused by policy. If that happens, say so plainly."""


async def handle(
    text: str,
    history: list[dict],
    user: str | None,
    session_id: str | None,
    *,
    traceparent: str | None = None,
) -> str:
    """Delegated task from the orchestrator."""
    log.info("a2a handle text_len=%d history=%d user=%s", len(text or ""), len(history or []), user or "-")
    emit = llm_agent.log_emit(log)
    full_history = llm_agent.build_history(history, text)
    tools = await llm_agent.discover_mcp_tools(
        MCP_SERVER, agent_id=AGENT_ID, user=user, traceparent=traceparent, emit=emit,
    )
    execute = llm_agent.mcp_tool_executor(
        MCP_SERVER, agent_id=AGENT_ID, user=user, session_id=session_id,
        traceparent=traceparent, history=full_history, emit=emit,
    )
    try:
        reply = await llm_agent.run_loop(
            text, agent_id=AGENT_ID, system=SYSTEM, tools=tools, execute_tool=execute,
            user=user, emit=emit, history=history, session_id=session_id,
            traceparent=traceparent,
        )
    except gateway.AuthorizationDenied:
        return json.dumps({
            "reply": "I could not check availability — my own model call was denied by Reva.",
            "note": f"{AGENT_ID}'s own model call was DENIED by Reva.",
        })
    return json.dumps({"reply": reply, "reasoned_by": f"{AGENT_ID} (own tool-calling loop via Kong)"})


SKILLS = [
    AgentSkill(
        id="list_slots",
        name="List slots",
        description="List available callback slots via the agent's own tool-calling loop.",
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
    description="Scheduling sub-agent: lists and books customer callback slots via its own MCP tools.",
    skills=SKILLS,
    handler=handle,
)


if __name__ == "__main__":
    a2a_agent.run(app, default_port="8004")
