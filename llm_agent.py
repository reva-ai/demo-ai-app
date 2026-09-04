"""Shared LLM tool-calling loop used by every agent in this app.

Every agent (billing-support-agent, ticketing-agent, booking-agent) is built
the same way: a2a_agent.py exposes it over A2A, and this module runs its
OpenAI-style tool-calling loop against gateway.py. What "tool" means differs
per agent — A2A delegate calls for billing-support-agent, MCP tool calls for
ticketing-agent/booking-agent — but the loop itself, and the rule that every
branch is a real model tool-call decision (never a keyword/regex guess), is
identical everywhere. Canned/deterministic behavior belongs only inside an
MCP tool's own return value, never here.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Awaitable, Callable

import gateway

Emit = Callable[[dict[str, Any]], None]
ToolExecutor = Callable[[str, dict[str, Any]], Awaitable[str]]

_THINK = re.compile(r"<thinking>.*?</thinking>", re.DOTALL | re.IGNORECASE)


def strip_thinking(text: str | None) -> str:
    return _THINK.sub("", text or "").strip()


def is_denial(err: Exception) -> bool:
    if isinstance(err, gateway.AuthorizationDenied):
        return True
    s = str(err)
    return "Blocked by Reva" in s or "403" in s


def log_emit(logger: logging.Logger) -> Emit:
    """An Emit for agents with no live UI to stream to — just log the event."""
    def _emit(event: dict[str, Any]) -> None:
        logger.info("trace %s", event)
    return _emit


def normalize_history(history: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    return [
        {"role": m["role"], "content": m["content"]}
        for m in (history or [])
        if isinstance(m, dict) and m.get("role") in ("user", "assistant") and m.get("content")
    ]


def build_history(history: list[dict[str, Any]] | None, message: str) -> list[dict[str, Any]]:
    """Prior turns + the current message — forwarded on every nested MCP/A2A
    call so Reva evaluates with full context."""
    return normalize_history(history) + [{"role": "user", "content": message}]


def parse_reply_envelope(reply: str) -> dict[str, Any]:
    """Every agent replies with a small JSON envelope: always `reply`, optionally
    `reasoned_by` or `note` so a caller with a live UI can show a trace card for
    what happened one hop down. Plain text still works: becomes {"reply": text}.
    """
    try:
        data = json.loads(reply)
    except (ValueError, TypeError):
        data = None
    if isinstance(data, dict) and (
        data.get("reply") is not None or data.get("reasoned_by") or data.get("note") or data.get("error")
    ):
        if "reply" not in data and not data.get("error"):
            data = {**data, "reply": reply}
        return data
    return {"reply": reply}


def emit_nested_card(server: str, payload: dict[str, Any], emit: Emit) -> None:
    nested_model = gateway.LLM_MODEL
    if payload.get("error"):
        # Never reached Kong at all - a bad config or network failure, not a
        # verdict. Rendered as a plain note (type=error), never an allowed/
        # denied card, so it can't be mistaken for something Reva decided.
        emit({"type": "error",
              "text": f"{server}'s own model call errored, not via Reva: {payload['error']}"})
    elif payload.get("reasoned_by"):
        emit({"type": "allowed", "kind": "model", "server": server, "tool": nested_model})
    elif "DENIED by Reva" in str(payload.get("note", "")):
        emit({"type": "denied", "kind": "model", "server": server, "tool": nested_model})


async def run_loop(
    message: str,
    *,
    agent_id: str,
    system: str,
    tools: list[dict[str, Any]],
    execute_tool: ToolExecutor,
    user: str | None,
    emit: Emit,
    model: str | None = None,
    history: list[dict[str, Any]] | None = None,
    session_id: str | None = None,
    traceparent: str | None = None,
    max_turns: int = 6,
) -> str:
    """Run one OpenAI-style tool-calling loop to completion; return reply text.

    `execute_tool(name, arguments)` is awaited for every tool call and must
    return a JSON string; this loop never knows whether that executor speaks
    MCP or A2A — that split lives entirely in which executor the caller passes.

    Raises gateway.AuthorizationDenied if the model call itself is denied, or
    the original exception for any other failure (bad config, network) —
    callers decide how to phrase either. Never swallowed into a plain string
    return: that would look identical to a real reply and, via reasoned_by in
    the caller's envelope, identical to a Reva-permitted call in the trace. A
    denied *tool* call is not raised: it is fed back to the model as a tool
    result (see the executors below), so the model can explain itself instead
    of the loop crashing.
    """
    used_model = model or gateway.LLM_MODEL
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        *build_history(history, message),
    ]
    for _turn in range(max_turns):
        try:
            response = await gateway.chat(
                messages, agent_id=agent_id, tools=tools or None, user=user,
                model=model, traceparent=traceparent, session_id=session_id,
            )
        except Exception as e:  # noqa: BLE001
            if is_denial(e):
                emit({"type": "denied", "kind": "model", "server": agent_id, "tool": used_model})
                raise gateway.AuthorizationDenied(str(e)) from e
            emit({"type": "error", "server": "llm", "tool": used_model, "text": str(e)[:160]})
            raise

        emit({"type": "allowed", "kind": "model", "server": agent_id, "tool": used_model})
        choice = response.choices[0].message
        if not choice.tool_calls:
            return strip_thinking(choice.content) or "…"

        messages.append({
            "role": "assistant",
            "content": choice.content or None,
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments or "{}"}}
                for tc in choice.tool_calls
            ],
        })
        for tc in choice.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            result = await execute_tool(tc.function.name, args)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    return "I hit the step limit while working on that. Please try a simpler request."


# ---- MCP-backed tools: ticketing-agent, booking-agent (one server each) ----

async def discover_mcp_tools(
    server: str, *, agent_id: str, user: str | None, traceparent: str | None, emit: Emit,
) -> list[dict[str, Any]]:
    try:
        return await gateway.list_tools(server, agent_id=agent_id, user=user, traceparent=traceparent)
    except Exception as e:  # noqa: BLE001
        emit({"type": "warn", "text": f"{server} unreachable: {str(e)[:80]}"})
        return []


def mcp_tool_executor(
    server: str, *, agent_id: str, user: str | None, session_id: str | None,
    traceparent: str | None, history: list[dict[str, Any]] | None, emit: Emit,
) -> ToolExecutor:
    async def execute(name: str, arguments: dict[str, Any]) -> str:
        _, tool = name.split("__", 1)
        emit({"type": "tool_call", "server": server, "tool": tool, "arguments": arguments})
        try:
            result = await gateway.call_tool(
                server, tool, arguments, agent_id=agent_id, user=user,
                traceparent=traceparent, session_id=session_id, history=history,
            )
        except Exception as e:  # noqa: BLE001
            if is_denial(e):
                emit({"type": "denied", "server": server, "tool": tool})
                return json.dumps({"error": "not_authorized",
                                    "detail": f"Reva denied {server}/{tool}. The tool did not run."})
            emit({"type": "error", "server": server, "tool": tool, "text": str(e)[:120]})
            return json.dumps({"error": "tool_failed", "detail": str(e)[:200]})
        emit({"type": "allowed", "server": server, "tool": tool, "result": result})
        return json.dumps(result, default=str)
    return execute


# ---- A2A-backed delegate "tools": billing-support-agent ----

def delegate_tool_defs(agents: list[str], descriptions: dict[str, str] | None = None) -> list[dict[str, Any]]:
    descriptions = descriptions or {}
    return [
        {
            "type": "function",
            "function": {
                "name": f"{agent}__invoke",
                "description": descriptions.get(agent, f"Delegate a task to {agent}."),
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
        for agent in agents
    ]


def a2a_delegate_executor(
    *, agent_id: str, user: str | None, session_id: str | None,
    traceparent: str | None, history: list[dict[str, Any]] | None, emit: Emit,
) -> ToolExecutor:
    async def execute(name: str, arguments: dict[str, Any]) -> str:
        server, _ = name.split("__", 1)  # "<agent>__invoke" -> "<agent>"
        request_text = (arguments or {}).get("request") or json.dumps(arguments, default=str)
        emit({"type": "tool_call", "kind": "agent", "server": server, "tool": "invoke", "arguments": arguments})
        try:
            reply = await gateway.send_agent(
                server, request_text, history=history, session_id=session_id,
                agent_id=agent_id, user=user, traceparent=traceparent,
            )
        except Exception as e:  # noqa: BLE001
            if is_denial(e):
                emit({"type": "denied", "kind": "agent", "server": server, "tool": "invoke"})
                return json.dumps({"error": "not_authorized",
                                    "detail": f"Reva denied delegation to {server}. The agent was never invoked."})
            emit({"type": "error", "server": server, "tool": "invoke", "text": str(e)[:120]})
            return json.dumps({"error": "agent_failed", "detail": str(e)[:200]})
        payload = parse_reply_envelope(reply)
        emit({"type": "allowed", "kind": "agent", "server": server, "tool": "invoke", "result": payload})
        emit_nested_card(server, payload, emit)
        return json.dumps(payload, default=str)
    return execute
