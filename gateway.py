"""Every outbound call this app makes goes through Kong.

Nothing here talks to an LLM provider or an MCP server directly. Both go
through cloud-hosted Kong routes; Kong's custom plugin calls Reva PDP before
proxying.

Identity for that plugin rides in X-Reva-Agent-Id / X-Reva-User.

`traceparent` (W3C Trace Context): this app only *forwards* it when already
present (e.g. from an ingress gateway or from Kong on a nested A2A hop). Kong
generates one when the inbound request has none — that is the gateway's job.

Deny contract: Kong should respond HTTP 403 with a body/message containing
"Blocked by Reva". Callers treat that as a soft denial, not a crash.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any

import httpx
from a2a.client import A2AClient
from a2a.types import Message, MessageSendParams, Part, Role, SendMessageRequest, TextPart
from a2a.utils import get_message_text
from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from openai import APIStatusError, AsyncOpenAI

load_dotenv()

log = logging.getLogger("demo.gateway")

# .strip() defensively: a key pasted into a hosting dashboard often picks up a
# trailing newline, which makes httpx reject the Authorization header.
KONG_API_KEY = os.environ.get("KONG_API_KEY", "").strip()
KONG_LLM_URL = os.environ.get("KONG_LLM_URL", "").rstrip("/")
# Each MCP server hangs off this as /<server-name>/mcp.
KONG_MCP_URL = os.environ.get("KONG_MCP_URL", "").rstrip("/")
# Each A2A sub-agent hangs off this as /<agent-name> (JSON-RPC message/send).
KONG_A2A_URL = os.environ.get("KONG_A2A_URL", "").rstrip("/")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o")


class AuthorizationDenied(Exception):
    """Kong (via Reva) refused this hop. Message always includes 'Blocked by Reva'."""


def _tp(traceparent: str | None) -> str:
    return (traceparent or "")[:50] or "(none)"


def _require_key() -> str:
    if not KONG_API_KEY:
        raise RuntimeError("KONG_API_KEY is unset — copy .env.example to .env and fill it in")
    return KONG_API_KEY


def _require_llm_url() -> str:
    if not KONG_LLM_URL:
        raise RuntimeError("KONG_LLM_URL is unset — copy .env.example to .env and fill it in")
    return KONG_LLM_URL


def _require_mcp_url() -> str:
    if not KONG_MCP_URL:
        raise RuntimeError("KONG_MCP_URL is unset — copy .env.example to .env and fill it in")
    return KONG_MCP_URL


def _require_a2a_url() -> str:
    if not KONG_A2A_URL:
        raise RuntimeError("KONG_A2A_URL is unset — copy .env.example to .env and fill it in")
    return KONG_A2A_URL


def _kong_headers(
    *,
    agent_id: str | None = None,
    user: str | None = None,
    traceparent: str | None = None,
) -> dict[str, str]:
    headers: dict[str, str] = {}
    if agent_id:
        headers["X-Reva-Agent-Id"] = agent_id
    if user:
        headers["X-Reva-User"] = user
    # Only forward — never mint. Missing → Kong generates.
    if traceparent:
        headers["traceparent"] = traceparent
    return headers


def _raise_if_denied(err: Exception) -> None:
    """Re-raise Kong/Reva denials as AuthorizationDenied for callers."""
    status = getattr(err, "status_code", None)
    text = str(err)
    if status == 403 or "Blocked by Reva" in text or "403" in text:
        raise AuthorizationDenied(f"Blocked by Reva: {text}") from err


async def chat(
    messages: list[dict[str, Any]],
    *,
    agent_id: str,
    tools: list[dict[str, Any]] | None = None,
    user: str | None = None,
    model: str | None = None,
    traceparent: str | None = None,
) -> Any:
    """One LLM turn, routed through Kong.

    `agent_id` / `user` → identity headers. `traceparent` is forwarded when the
    caller already has one; otherwise Kong mints it on the gateway.
    """
    used = model or LLM_MODEL
    log.info(
        "kong llm → %s agent=%s user=%s model=%s tools=%d msgs=%d traceparent=%s",
        _require_llm_url(), agent_id, user or "-", used,
        len(tools or []), len(messages), _tp(traceparent),
    )
    client = AsyncOpenAI(
        api_key=_require_key(),
        base_url=_require_llm_url(),
        default_headers=_kong_headers(
            agent_id=agent_id, user=user, traceparent=traceparent
        ),
    )
    kwargs: dict[str, Any] = {"model": used, "messages": messages}
    if tools:
        kwargs["tools"] = tools
    try:
        resp = await client.chat.completions.create(**kwargs)
        choice = resp.choices[0].message if resp.choices else None
        n_tools = len(choice.tool_calls or []) if choice else 0
        log.info("kong llm ← ok agent=%s model=%s tool_calls=%d", agent_id, used, n_tools)
        return resp
    except APIStatusError as e:
        log.warning("kong llm ← http %s agent=%s: %s", e.status_code, agent_id, str(e)[:160])
        try:
            _raise_if_denied(e)
        except AuthorizationDenied:
            log.warning("kong llm ← DENIED agent=%s model=%s", agent_id, used)
            raise
        raise
    except Exception as e:  # noqa: BLE001
        log.warning("kong llm ← error agent=%s: %s", agent_id, str(e)[:160])
        try:
            _raise_if_denied(e)
        except AuthorizationDenied:
            log.warning("kong llm ← DENIED agent=%s model=%s", agent_id, used)
            raise
        raise


def _mcp_client(
    server: str,
    *,
    agent_id: str | None = None,
    user: str | None = None,
    traceparent: str | None = None,
) -> Client:
    headers = {
        "Authorization": f"Bearer {_require_key()}",
        **_kong_headers(agent_id=agent_id, user=user, traceparent=traceparent),
    }
    return Client(
        StreamableHttpTransport(
            url=f"{_require_mcp_url()}/{server}/mcp",
            headers=headers,
        )
    )


async def list_tools(
    server: str,
    *,
    agent_id: str | None = None,
    user: str | None = None,
    traceparent: str | None = None,
) -> list[dict[str, Any]]:
    """Discover an MCP server's tools via Kong, shaped for the OpenAI tools param.

    Tool names are prefixed with the server so the orchestrator can route a
    tool_call back to the right server later. The separator is `__` because
    OpenAI rejects `/` in function names — and `/` is what Reva resource ids
    typically use, so the two conventions are translated at this boundary.
    """
    log.info(
        "kong mcp list_tools → %s/%s agent=%s traceparent=%s",
        _require_mcp_url(), server, agent_id or "-", _tp(traceparent),
    )
    try:
        async with _mcp_client(
            server, agent_id=agent_id, user=user, traceparent=traceparent
        ) as c:
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": f"{server}__{t.name}",
                        "description": t.description or "",
                        "parameters": t.inputSchema,
                    },
                }
                for t in await c.list_tools()
            ]
            log.info("kong mcp list_tools ← ok server=%s n=%d", server, len(tools))
            return tools
    except Exception as e:  # noqa: BLE001
        log.warning("kong mcp list_tools ← error server=%s: %s", server, str(e)[:160])
        _raise_if_denied(e)
        raise


async def call_tool(
    server: str,
    tool: str,
    arguments: dict[str, Any],
    *,
    agent_id: str | None = None,
    user: str | None = None,
    traceparent: str | None = None,
) -> Any:
    """Invoke one MCP tool through Kong.

    A Reva denial surfaces as AuthorizationDenied — the tool's code never runs.
    Callers should catch it and tell the user they were not authorized.
    """
    log.info(
        "kong mcp call → %s/%s tool=%s agent=%s args_keys=%s traceparent=%s",
        _require_mcp_url(), server, tool, agent_id or "-",
        sorted(arguments.keys()) if isinstance(arguments, dict) else "-",
        _tp(traceparent),
    )
    try:
        async with _mcp_client(
            server, agent_id=agent_id, user=user, traceparent=traceparent
        ) as c:
            result = await c.call_tool(tool, arguments)
            log.info("kong mcp call ← ok server=%s tool=%s", server, tool)
            return result.structured_content or result.content
    except AuthorizationDenied:
        log.warning("kong mcp call ← DENIED server=%s tool=%s", server, tool)
        raise
    except Exception as e:  # noqa: BLE001
        log.warning("kong mcp call ← error server=%s tool=%s: %s", server, tool, str(e)[:160])
        _raise_if_denied(e)
        raise


def _extract_a2a_text(resp: Any) -> str:
    """Pull the agent's reply text out of a SendMessageResponse (Message or Task)."""
    root = getattr(resp, "root", resp)
    result = getattr(root, "result", None)
    if result is None:
        return ""
    if getattr(result, "kind", None) == "message" or getattr(result, "parts", None) is not None:
        try:
            return get_message_text(result)
        except Exception:  # noqa: BLE001
            pass
    history = getattr(result, "history", None)
    if history:
        return get_message_text(history[-1])
    status = getattr(result, "status", None)
    if status is not None and getattr(status, "message", None) is not None:
        return get_message_text(status.message)
    return str(result)


async def send_agent(
    agent: str,
    text: str,
    *,
    history: list[dict[str, Any]] | None = None,
    session_id: str | None = None,
    agent_id: str | None = None,
    user: str | None = None,
    traceparent: str | None = None,
) -> str:
    """Delegate to a sub-agent via A2A `message/send`, routed through Kong.

    Conversation travels A2A-natively (text + metadata.chatHistory + contextId).
    If `traceparent` is already known, it is forwarded so Kong keeps the same
    trace; if absent, Kong generates one and should forward it upstream.
    """
    url = f"{_require_a2a_url()}/{agent}"
    log.info(
        "kong a2a → %s agent_id=%s user=%s session=%s history=%d text_len=%d traceparent=%s",
        url, agent_id or "-", user or "-", session_id or "-",
        len(history or []), len(text or ""), _tp(traceparent),
    )
    message = Message(
        message_id=str(uuid.uuid4()),
        role=Role.user,
        parts=[Part(root=TextPart(text=text))],
        context_id=session_id,
        metadata={
            "chatHistory": history or [],
            "user": user,
            "traceparent": traceparent,
        },
    )
    request = SendMessageRequest(id=str(uuid.uuid4()), params=MessageSendParams(message=message))
    headers = {
        "Authorization": f"Bearer {_require_key()}",
        **_kong_headers(agent_id=agent_id, user=user, traceparent=traceparent),
    }
    try:
        async with httpx.AsyncClient(headers=headers, timeout=90.0) as hc:
            client = A2AClient(httpx_client=hc, url=url)
            resp = await client.send_message(request)
    except AuthorizationDenied:
        log.warning("kong a2a ← DENIED agent=%s", agent)
        raise
    except Exception as e:  # noqa: BLE001
        log.warning("kong a2a ← error agent=%s: %s", agent, str(e)[:160])
        _raise_if_denied(e)
        raise
    text_out = _extract_a2a_text(resp)
    log.info("kong a2a ← ok agent=%s reply_len=%d", agent, len(text_out or ""))
    return text_out
