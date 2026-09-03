"""The orchestrator loop, and the identities it runs under.

Three agents, one gateway:

    user -> orchestrator-agent  --LLM-->      Kong -> upstream LLM
                                --MCP-->      Kong -> billing-mcp / external-mcp
                                --A2A-->      Kong -> ticketing-agent / booking-agent

Tools are reached over MCP; sub-agents are reached over the A2A protocol
(message/send). Kong only sees traffic that traverses its routes, so both hops
are governed: "orchestrator delegates to ticketing" is a standard A2A call that
routes through Kong and can be allowed or denied by Reva. The conversation
travels the A2A-native way — current turn as the message text, prior turns in
metadata.chatHistory, thread as contextId — so Reva evaluates with full context.

A denied tool call is NOT an error here. It is fed back to the model as a tool
result saying it was not authorized, so the model explains itself to the user in
plain language instead of the app throwing a stack trace. Denial is a normal
outcome of asking, not a crash.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable

import gateway

log = logging.getLogger("demo.agents")

ORCHESTRATOR_ID = "billing-support-agent"

# Two kinds of downstream, two protocols:
#   TOOL_SERVERS  — plain capabilities, reached over MCP (invokeTool via Kong).
#   AGENT_SERVERS — sub-agents, reached over A2A message/send (invokeAgent via Kong).
# Names must match Kong route path segments and Reva resource ids.
TOOL_SERVERS = ["billing-mcp", "external-mcp"]
AGENT_SERVERS = ["ticketing-agent", "booking-agent"]
SERVERS = TOOL_SERVERS + AGENT_SERVERS

# The orchestrator offers each sub-agent to the model as a single delegate
# function; picking it triggers an A2A hop, not an MCP tool call.
_AGENT_DESCRIPTIONS = {
    "ticketing-agent": "Delegate to the ticketing agent to open/close and triage support tickets.",
    "booking-agent": "Delegate to the booking agent to list or book customer callback slots.",
}


def _agent_function(agent: str) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": f"{agent}__invoke",
            "description": _AGENT_DESCRIPTIONS.get(agent, f"Delegate a task to {agent}."),
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "request": {"type": "string",
                                "description": "The task for the agent, in natural language."}
                },
                "required": ["request"],
            },
        },
    }

SYSTEM = """You are a helpful billing support agent.

Use tools when needed, then answer the user in clear, natural language — like a
support agent, not a log dump. Summarize findings in short sentences or bullets.
Do not paste raw JSON, internal tool names, or phrases like "returned:".

Some tools may be refused by policy. If that happens, say plainly that you are
not authorized for that action and continue with what you can do. Never invent
data you could not retrieve, and never pretend a refused call succeeded."""


def _is_denial(err: Exception) -> bool:
    if isinstance(err, gateway.AuthorizationDenied):
        return True
    s = str(err)
    return "Blocked by Reva" in s or "403" in s


async def _available_tools(
    emit: Callable[[dict], None], servers: list[str] | None = None,
    *, agent_id: str | None = None, user: str | None = None,
    traceparent: str | None = None,
) -> list[dict[str, Any]]:
    """Discover tools from each selected server. A server that is down is skipped
    rather than fatal — the demo should degrade, not collapse.

    Deselecting a server here is NOT authorization. It only stops the orchestrator
    offering those tools to the model. Reva's job is to refuse tools the agent does
    reach for; a tool never offered was never authorized or denied.
    """
    tools: list[dict[str, Any]] = []
    for server in (servers if servers is not None else SERVERS):
        if server in AGENT_SERVERS:
            # A2A sub-agent: one delegate function, no MCP discovery hop.
            tools.append(_agent_function(server))
            continue
        try:
            tools.extend(await gateway.list_tools(
                server, agent_id=agent_id, user=user, traceparent=traceparent,
            ))
        except Exception as e:  # noqa: BLE001
            emit({"type": "warn", "text": f"{server} unreachable: {str(e)[:80]}"})
    return tools


async def _run_tool(name: str, arguments: dict, emit: Callable[[dict], None],
                    *, agent_id: str | None = None, user: str | None = None,
                    history: list[dict[str, Any]] | None = None,
                    session_id: str | None = None,
                    traceparent: str | None = None) -> str:
    """Execute one tool call and return what the model should see as its result.

    Sub-agents (AGENT_SERVERS) go over A2A: the conversation is forwarded as the
    message text + metadata.chatHistory so the sub-agent — and Reva — see full
    context. Everything else is an MCP tool call.
    """
    server, tool = name.split("__", 1)
    emit({"type": "tool_call", "server": server, "tool": tool, "arguments": arguments})
    log.info("orchestrator call %s/%s agent=%s", server, tool, agent_id or "-")

    if server in AGENT_SERVERS:
        request_text = arguments.get("request") if isinstance(arguments, dict) else None
        request_text = request_text or json.dumps(arguments, default=str)
        try:
            reply = await gateway.send_agent(
                server, request_text, history=history, session_id=session_id,
                agent_id=agent_id, user=user, traceparent=traceparent,
            )
        except Exception as e:  # noqa: BLE001
            if _is_denial(e):
                log.warning("orchestrator DENIED a2a %s", server)
                emit({"type": "denied", "server": server, "tool": tool})
                return json.dumps(
                    {"error": "not_authorized",
                     "detail": f"Reva denied delegation to {server}. The agent was never invoked."}
                )
            log.warning("orchestrator a2a error %s: %s", server, str(e)[:120])
            emit({"type": "error", "server": server, "tool": tool, "text": str(e)[:120]})
            return json.dumps({"error": "agent_failed", "detail": str(e)[:200]})
        payload = _parse_agent_payload(reply)
        emit({"type": "allowed", "server": server, "tool": tool, "result": payload})
        _emit_nested_model(server, payload, emit)
        return json.dumps(payload, default=str)

    try:
        result = await gateway.call_tool(
            server, tool, arguments, agent_id=agent_id, user=user,
            traceparent=traceparent, session_id=session_id, history=history,
        )
    except Exception as e:  # noqa: BLE001
        if _is_denial(e):
            log.warning("orchestrator DENIED tool %s/%s", server, tool)
            emit({"type": "denied", "server": server, "tool": tool})
            return json.dumps(
                {"error": "not_authorized",
                 "detail": f"Reva denied {server}/{tool}. The tool did not run."}
            )
        log.warning("orchestrator tool error %s/%s: %s", server, tool, str(e)[:120])
        emit({"type": "error", "server": server, "tool": tool, "text": str(e)[:120]})
        return json.dumps({"error": "tool_failed", "detail": str(e)[:200]})
    emit({"type": "allowed", "server": server, "tool": tool, "result": result})
    if isinstance(result, dict):
        _emit_nested_model(server, result, emit)
    return json.dumps(result, default=str)


def _parse_agent_payload(reply: str) -> dict[str, Any]:
    """Normalize an A2A reply into a structured dict for the model / fallback.

    Ticketing returns a JSON envelope with `reply` (+ optional reasoned_by/note).
    Booking (and any plain-text agent) becomes {"reply": "<text>"}.
    """
    try:
        data = json.loads(reply)
    except (ValueError, TypeError):
        data = None
    if isinstance(data, dict) and (data.get("reply") is not None or data.get("reasoned_by")
                                   or data.get("note") or data.get("error")):
        if "reply" not in data and not data.get("error"):
            data = {**data, "reply": reply}
        return data
    return {"reply": reply}


def _emit_nested_model(server: str, payload: dict[str, Any], emit: Callable[[dict], None]) -> None:
    """If a sub-agent made its own model call, surface that as a second trace card."""
    nested_model = gateway.LLM_MODEL
    if payload.get("reasoned_by"):
        emit({"type": "allowed", "kind": "model", "server": server, "tool": nested_model})
    elif "DENIED by Reva" in str(payload.get("note", "")):
        emit({"type": "denied", "kind": "model", "server": server, "tool": nested_model})


_THINK = re.compile(r"<thinking>.*?</thinking>", re.DOTALL | re.IGNORECASE)


def _strip_thinking(text: str | None) -> str:
    """Some models emit <thinking>…</thinking> next to tool calls; strip it."""
    return _THINK.sub("", text or "").strip()


def _phrase(name: str, result_json: str) -> str:
    """Fallback user-facing text when we cannot ask the model to summarize.

    Primary path: the model reads the structured tool/agent JSON and writes the
    reply itself. This only runs for keyword-fallback / non-tool-capable models.
    """
    server, tool = name.split("__", 1)
    try:
        data = json.loads(result_json)
    except (ValueError, TypeError):
        data = None
    if isinstance(data, dict) and data.get("reply"):
        return str(data["reply"])
    if isinstance(data, dict) and data.get("error") == "not_authorized":
        if server in AGENT_SERVERS:
            return (
                f"I couldn't delegate that to {server} — Reva blocked the hand-off at Kong, "
                "so the agent was never invoked."
            )
        return (
            f"I couldn't complete that — I'm not authorized to use {server}/{tool}. "
            "Reva blocked it at Kong, so the tool never ran."
        )
    if isinstance(data, dict) and data.get("error"):
        return f"I couldn't complete {tool}: {data.get('detail') or data.get('error')}"
    if not isinstance(data, dict):
        return "I finished that request, but got an unexpected result back."

    # MCP tool fixtures only — agents return {reply} above.
    cid = data.get("customerId") or data.get("customer_id")
    if tool == "get_billing_report":
        return (
            f"Here's the billing summary for customer {cid}:\n"
            f"• Invoices on file: {data.get('invoices')}\n"
            f"• Outstanding balance: {data.get('currency')} {data.get('outstanding')}"
        )
    if tool == "get_compliance_status":
        return (
            f"Compliance status for customer {cid}:\n"
            f"• KYC: {data.get('kyc')}\n"
            f"• Standing: {data.get('standing')}"
        )
    if tool == "get_customer_pii":
        return (
            f"Customer profile for {cid}:\n"
            f"• SSN: {data.get('ssn')}\n"
            f"• Date of birth: {data.get('dob')}"
        )
    if tool == "analytics_probe":
        return f"Analytics probe result: {data.get('note') or json.dumps(data, default=str)}"
    return f"Done — I have the result for {tool}."


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
        return "ticketing-agent", "invoke", {"request": message}
    if on("booking-agent") and ("book" in m or "appointment" in m or "slot" in m):
        return "booking-agent", "invoke", {"request": message}
    return None


async def _run_fallback(
    message: str, servers: list[str] | None, emit: Callable[[dict], None],
    *, agent_id: str | None = None, user: str | None = None,
    history: list[dict[str, Any]] | None = None, session_id: str | None = None,
    traceparent: str | None = None,
) -> str | None:
    """If the prompt maps to a tool, call it directly and phrase the outcome."""
    intent = _fallback_intent(message, servers)
    if not intent:
        return None
    server, tool, args = intent
    result = await _run_tool(
        f"{server}__{tool}", args, emit, agent_id=agent_id, user=user,
        history=history, session_id=session_id, traceparent=traceparent,
    )
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
    session_id: str | None = None,
    traceparent: str | None = None,
    max_turns: int = 6,
) -> str:
    """Run the agent loop for one user message. `emit` streams trace events to the UI.

    `agent_id` is the identity the loop runs under. It is a parameter, not a
    constant, because swapping it is the sharpest demonstration in the demo:
    the same user, prompt, and model, under an identity no permit covers, gets
    refused. Reva evaluates the agent — not just the request.

    `traceparent`: reuse ingress if present; otherwise mint once for this turn
    and send it on every Kong hop so RTG sees one shared trace. Kong still
    mints only when a hop has none. `context.hops` remains Kong's job.

    max_turns bounds the loop: a model that keeps calling denied tools would
    otherwise retry forever, and each retry is a real authorization request.
    """
    if not traceparent:
        traceparent = gateway.mint_traceparent()
    emit({"type": "trace", "traceparent": traceparent})
    log.info(
        "orchestrate start agent=%s user=%s model=%s session=%s traceparent=%s",
        agent_id, user, model or gateway.LLM_MODEL, session_id or "-",
        (traceparent or "")[:50] or "(none)",
    )

    # The conversation to forward on A2A delegations: prior user/assistant turns
    # plus the current message. Sub-agents receive this as metadata.chatHistory so
    # Reva evaluates the invokeAgent hop with the same context the orchestrator has.
    # Built before the checkpoint call below, which needs it too.
    convo: list[dict[str, Any]] = [
        {"role": m["role"], "content": m["content"]}
        for m in (history or [])
        if isinstance(m, dict) and m.get("role") in ("user", "assistant") and m.get("content")
    ]
    convo.append({"role": "user", "content": message})

    # Checkpoint: is `user` allowed to invoke this agent at all, before it does
    # anything? The browser calls this process directly (never through Kong),
    # so without this the "user invokes the orchestrator" hop would never be
    # evaluated by Reva at all. This call goes out through Kong to a route
    # pointing back at this same service (see a2a_agent mount in main.py) —
    # by the time our own handler answers it, Reva has already decided.
    try:
        await gateway.send_agent(
            agent_id, message, history=convo[:-1], session_id=session_id,
            user=user, traceparent=traceparent,
        )
    except gateway.AuthorizationDenied:
        emit({"type": "denied", "kind": "agent", "server": agent_id})
        return f"Reva denied '{user}' permission to invoke '{agent_id}'."
    emit({"type": "allowed", "kind": "agent", "server": agent_id})

    tools = await _available_tools(
        emit, servers, agent_id=agent_id, user=user, traceparent=traceparent,
    )
    used_model = model or gateway.LLM_MODEL
    # Withhold tools from models that can't do OpenAI-style tool-calling reliably
    # (e.g. Nova). The keyword→tool fallback still runs tools through Kong/Reva.
    tool_capable = "nova" not in (used_model or "").lower()
    send_tools = tools if tool_capable else None

    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM}, *convo]

    async def _llm() -> Any:
        return await gateway.chat(
            messages, agent_id=agent_id, tools=send_tools or None, user=user, model=model,
            traceparent=traceparent, session_id=session_id,
        )

    # Models that can't tool-call (e.g. Nova): one LLM attempt, then keyword fallback.
    if not tool_capable:
        try:
            response = await gateway.chat(
                messages, agent_id=agent_id, tools=None, user=user, model=model,
                traceparent=traceparent, session_id=session_id,
            )
        except Exception as e:  # noqa: BLE001
            if _is_denial(e):
                emit({"type": "denied", "kind": "model", "server": agent_id, "tool": used_model})
                return (
                    f"Reva denied '{agent_id}' permission to call {used_model}. "
                    "The model was never contacted."
                )
            emit({"type": "allowed", "kind": "model", "server": agent_id, "tool": used_model})
            fb = await _run_fallback(
                message, servers, emit, agent_id=agent_id, user=user,
                history=convo, session_id=session_id, traceparent=traceparent,
            )
            return fb if fb is not None else f"The model call failed: {str(e)[:160]}"
        emit({"type": "allowed", "kind": "model", "server": agent_id, "tool": used_model})
        fb = await _run_fallback(
            message, servers, emit, agent_id=agent_id, user=user,
            history=convo, session_id=session_id, traceparent=traceparent,
        )
        if fb is not None:
            return fb
        return _strip_thinking(response.choices[0].message.content) or "…"

    # Tool-capable path: run tools, then ask the model to write a natural reply.
    for turn in range(max_turns):
        try:
            response = await _llm()
        except Exception as e:  # noqa: BLE001
            if _is_denial(e):
                emit({"type": "denied", "kind": "model", "server": agent_id, "tool": used_model})
                return (
                    f"Reva denied '{agent_id}' permission to call {used_model}. "
                    "The model was never contacted."
                )
            emit({"type": "allowed", "kind": "model", "server": agent_id, "tool": used_model})
            if turn == 0:
                fb = await _run_fallback(
                    message, servers, emit, agent_id=agent_id, user=user,
                    history=convo, session_id=session_id, traceparent=traceparent,
                )
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
            text = _strip_thinking(choice.content)
            if turn == 0:
                # Prefer a real tool hop when intent is clear so Reva still demos.
                fb = await _run_fallback(
                    message, servers, emit, agent_id=agent_id, user=user,
                    history=convo, session_id=session_id, traceparent=traceparent,
                )
                if fb is not None:
                    return fb
            return text or "…"

        messages.append({
            "role": "assistant",
            "content": choice.content or None,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments or "{}",
                    },
                }
                for tc in choice.tool_calls
            ],
        })
        for tc in choice.tool_calls:
            result = await _run_tool(
                tc.function.name,
                json.loads(tc.function.arguments or "{}"),
                emit,
                agent_id=agent_id,
                user=user,
                history=convo,
                session_id=session_id,
                traceparent=traceparent,
            )
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    return "I hit the step limit while working on that. Please try a simpler request."
