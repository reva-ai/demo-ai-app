"""ticketing-agent — a sub-agent reached over A2A through Kong. It is itself a
full LLM agent: given the delegated request (+ history), it runs a real
OpenAI tool-calling loop against its own MCP server (ticketing-mcp) before
replying. No keyword logic anywhere in this file — every decision (open vs.
close vs. check status vs. do nothing) is the model's own tool-calling choice.

Run:
    .venv/bin/python ticketing_agent_server.py       # http://127.0.0.1:8003/
"""

from __future__ import annotations

import json
import logging

from a2a.types import AgentSkill

import a2a_agent
import gateway
import llm_agent

log = logging.getLogger("demo.ticketing")

AGENT_ID = "ticketing-agent"
MCP_SERVER = "ticketing-mcp"

SYSTEM = """You are a support ticketing agent. Use your tools to open \
tickets, close tickets, and check ticket status for the user's request. Use \
tools when needed, then reply in clear, natural language summarizing what \
happened — never invent a ticket id or status a tool did not give you.

Some tools may be refused by policy. If that happens, say so plainly and \
continue with what you can do."""


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
            "reply": "I could not act on that — my own model call was denied by Reva.",
            "note": f"{AGENT_ID}'s own model call was DENIED by Reva.",
        })
    return json.dumps({"reply": reply, "reasoned_by": f"{AGENT_ID} (own tool-calling loop via Kong)"})


SKILLS = [
    AgentSkill(
        id="create_ticket",
        name="Create ticket",
        description="Open a support ticket via the agent's own tool-calling loop.",
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
    AgentSkill(
        id="check_ticket_status",
        name="Check ticket status",
        description="Look up an existing ticket's status.",
        tags=["ticketing", "support"],
        examples=["What's the status of ticket TKT-1000?"],
    ),
]


app = a2a_agent.build_app(
    name="ticketing-agent",
    description="Support ticketing sub-agent: opens, closes, and checks tickets via its own MCP tools.",
    skills=SKILLS,
    handler=handle,
)


if __name__ == "__main__":
    a2a_agent.run(app, default_port="8003")
