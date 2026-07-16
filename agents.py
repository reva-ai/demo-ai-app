"""The orchestrator loop, and the identities it runs under.

Three agents, one gateway:

    user -> orchestrator-agent  --LLM-->      Kong -> upstream LLM
                                --MCP-->      Kong -> billing-mcp / external-mcp
                                --MCP-->      Kong -> ticketing-agent / booking-agent

The sub-agents are reached as MCP servers rather than as direct HTTP calls.
Kong only sees traffic that traverses its routes; a plain agent-to-agent HTTP
request would never hit the Reva plugin. Exposing each sub-agent as an MCP
server makes "orchestrator delegates to ticketing" an MCP tool call — so it
routes through Kong and can be allowed or denied by Reva.

A denied tool call is NOT an error here. It is fed back to the model as a tool
result saying it was not authorized, so the model explains itself to the user in
plain language instead of the app throwing a stack trace. Denial is a normal
outcome of asking, not a crash.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable

import gateway

ORCHESTRATOR_ID = "billing-support-agent"

# MCP server path segments under KONG_MCP_URL. Names must match Kong routes
# and Reva Tool resource ids (typically "{server}/{tool}").
SERVERS = ["billing-mcp", "external-mcp", "ticketing-agent", "booking-agent"]

SYSTEM = """You are a billing support orchestrator.

Use the tools available to you to answer the user. Some tools may refuse to run:
you are not authorized to call them. When that happens, tell the user plainly
which action was refused and move on. Never invent data you could not retrieve,
and never pretend a refused call succeeded."""


def _is_denial(err: Exception) -> bool:
    if isinstance(err, gateway.AuthorizationDenied):
        return True
    s = str(err)
    return "Blocked by Reva" in s or "403" in s


async def _available_tools(
    emit: Callable[[dict], None], servers: list[str] | None = None,
    *, agent_id: str | None = None, user: str | None = None,
) -> list[dict[str, Any]]:
    """Discover tools from each selected server. A server that is down is skipped
    rather than fatal — the demo should degrade, not collapse.

    Deselecting a server here is NOT authorization. It only stops the orchestrator
    offering those tools to the model. Reva's job is to refuse tools the agent does
    reach for; a tool never offered was never authorized or denied.
    """
    tools: list[dict[str, Any]] = []
    for server in (servers if servers is not None else SERVERS):
        try:
            tools.extend(await gateway.list_tools(server, agent_id=agent_id, user=user))
        except Exception as e:  # noqa: BLE001
            emit({"type": "warn", "text": f"{server} unreachable: {str(e)[:80]}"})
    return tools


async def _run_tool(name: str, arguments: dict, emit: Callable[[dict], None],
                    *, agent_id: str | None = None, user: str | None = None) -> str:
    """Execute one tool call and return what the model should see as its result."""
    server, tool = name.split("__", 1)
    emit({"type": "tool_call", "server": server, "tool": tool, "arguments": arguments})
    try:
        result = await gateway.call_tool(server, tool, arguments, agent_id=agent_id, user=user)
    except Exception as e:  # noqa: BLE001
        if _is_denial(e):
            emit({"type": "denied", "server": server, "tool": tool})
            return json.dumps(
                {"error": "not_authorized",
                 "detail": f"Reva denied {server}/{tool}. The tool did not run."}
            )
        emit({"type": "error", "server": server, "tool": tool, "text": str(e)[:120]})
        return json.dumps({"error": "tool_failed", "detail": str(e)[:200]})
    emit({"type": "allowed", "server": server, "tool": tool, "result": result})
    # If the tool was itself a reasoning agent, it made its OWN model call inside.
    # Surface that nested authorization as its own trace card so the whole
    # agent-to-agent chain is visible: two agents, each thinking, each governed.
    if isinstance(result, dict):
        nested_model = gateway.LLM_MODEL
        if result.get("reasoned_by"):
            emit({"type": "allowed", "kind": "model", "server": server, "tool": nested_model})
        elif "DENIED by Reva" in str(result.get("note", "")):
            emit({"type": "denied", "kind": "model", "server": server, "tool": nested_model})
    return json.dumps(result, default=str)


_THINK = re.compile(r"<thinking>.*?</thinking>", re.DOTALL | re.IGNORECASE)


def _strip_thinking(text: str | None) -> str:
    """Some models emit <thinking>…</thinking> next to tool calls; strip it."""
    return _THINK.sub("", text or "").strip()


def _phrase(name: str, result_json: str) -> str:
    """Turn a tool result (or a Reva denial) into a sentence for the user."""
    server, tool = name.split("__", 1)
    try:
        data = json.loads(result_json)
    except (ValueError, TypeError):
        data = None
    if isinstance(data, dict) and data.get("error") == "not_authorized":
        return f"I'm not authorized to use {server}/{tool} — Reva blocked it at Kong, so it never ran."
    if isinstance(data, dict) and data.get("error"):
        return f"The {server}/{tool} call couldn't complete: {data.get('detail') or data.get('error')}"
    return f"{server}/{tool} returned: {result_json}"


def _fallback_intent(message: str, servers: list[str] | None) -> tuple[str, str, dict] | None:
    """Map a demo prompt straight to a tool call when the model skips tools.

    The call still goes through Kong and Reva; only tool *selection* is
    deterministic. Scoped to servers that are switched on.
    """
    m = message.lower()
    allowed = set(servers if servers is not None else SERVERS)
    cid = re.search(r"\bc\d+\b", message, re.IGNORECASE)
    customer = cid.group(0) if cid else "c1"

    def on(s: str) -> bool:
        return s in allowed

    if on("billing-mcp") and ("pii" in m or "personal" in m):
        return "billing-mcp", "get_customer_pii", {"customer_id": customer}
    if on("billing-mcp") and "compliance" in m:
        return "billing-mcp", "get_compliance_status", {"customer_id": customer}
    if on("billing-mcp") and ("billing" in m or "report" in m or "invoice" in m):
        return "billing-mcp", "get_billing_report", {"customer_id": customer}
    if on("external-mcp") and ("probe" in m or "analytics" in m or "external" in m):
        return "external-mcp", "analytics_probe", {"query": message}
    if on("ticketing-agent") and "ticket" in m:
        return "ticketing-agent", "create_ticket", {"customer_id": customer, "summary": message}
    if on("booking-agent") and ("book" in m or "appointment" in m or "slot" in m):
        return "booking-agent", "book_slot", {"customer_id": customer, "slot": "2026-07-14T10:00Z"}
    return None


async def _run_fallback(
    message: str, servers: list[str] | None, emit: Callable[[dict], None],
    *, agent_id: str | None = None, user: str | None = None,
) -> str | None:
    """If the prompt maps to a tool, call it directly and phrase the outcome."""
    intent = _fallback_intent(message, servers)
    if not intent:
        return None
    server, tool, args = intent
    result = await _run_tool(f"{server}__{tool}", args, emit, agent_id=agent_id, user=user)
    return _phrase(f"{server}__{tool}", result)


async def orchestrate(
    message: str,
    *,
    user: str,
    emit: Callable[[dict], None],
    agent_id: str = ORCHESTRATOR_ID,
    model: str | None = None,
    servers: list[str] | None = None,
    history: list[dict[str, Any]] | None = None,
    max_turns: int = 6,
) -> str:
    """Run the agent loop for one user message. `emit` streams trace events to the UI.

    `agent_id` is the identity the loop runs under. It is a parameter, not a
    constant, because swapping it is the sharpest demonstration in the demo:
    the same user, prompt, and model, under an identity no permit covers, gets
    refused. Reva evaluates the agent — not just the request.

    max_turns bounds the loop: a model that keeps calling denied tools would
    otherwise retry forever, and each retry is a real authorization request.
    """
    tools = await _available_tools(emit, servers, agent_id=agent_id, user=user)
    used_model = model or gateway.LLM_MODEL
    # Withhold tools from models that can't do OpenAI-style tool-calling reliably
    # (e.g. Nova). The keyword→tool fallback still runs tools through Kong/Reva.
    tool_capable = "nova" not in (used_model or "").lower()
    send_tools = tools if tool_capable else None
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM}]
    if history:
        messages.extend(
            {"role": m["role"], "content": m["content"]}
            for m in history
            if isinstance(m, dict) and m.get("role") and m.get("content")
        )
    messages.append({"role": "user", "content": message})

    del max_turns  # single turn for models that can't sustain a multi-turn tool loop
    try:
        response = await gateway.chat(
            messages, agent_id=agent_id, tools=send_tools or None, user=user, model=model
        )
    except Exception as e:  # noqa: BLE001
        if _is_denial(e):
            emit({"type": "denied", "kind": "model", "server": agent_id, "tool": used_model})
            return (
                f"Reva denied '{agent_id}' permission to call {used_model}. "
                "The model was never contacted."
            )
        # Reva let the call through; the model itself failed. Show the model as
        # allowed, then fall back to invoking the tool the user clearly wanted.
        emit({"type": "allowed", "kind": "model", "server": agent_id, "tool": used_model})
        fb = await _run_fallback(message, servers, emit, agent_id=agent_id, user=user)
        if fb is not None:
            return fb
        if "ToolUse" in str(e) or "424" in str(e):
            return ("I couldn't act on that with the tools currently switched on. "
                    "Enable the tool that fits the request and try again.")
        emit({"type": "error", "server": "llm", "tool": used_model, "text": str(e)[:160]})
        return f"The model call failed: {str(e)[:160]}"

    emit({"type": "allowed", "kind": "model", "server": agent_id, "tool": used_model})
    choice = response.choices[0].message

    if not choice.tool_calls:
        fb = await _run_fallback(message, servers, emit, agent_id=agent_id, user=user)
        return fb if fb is not None else (_strip_thinking(choice.content) or "…")

    replies = [
        _phrase(
            tc.function.name,
            await _run_tool(tc.function.name, json.loads(tc.function.arguments or "{}"), emit,
                            agent_id=agent_id, user=user),
        )
        for tc in choice.tool_calls
    ]
    return "\n".join(replies)
