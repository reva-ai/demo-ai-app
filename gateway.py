"""Every outbound call this app makes goes through Kong.

Nothing here talks to an LLM provider or an MCP server directly. Both go
through cloud-hosted Kong routes; Kong's custom plugin calls Reva PDP before
proxying. Identity for that plugin rides in X-Reva-Agent-Id / X-Reva-User.

Deny contract: Kong should respond HTTP 403 with a body/message containing
"Blocked by Reva". Callers treat that as a soft denial, not a crash.
"""

from __future__ import annotations

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


def _identity_headers(*, agent_id: str | None = None, user: str | None = None) -> dict[str, str]:
    headers: dict[str, str] = {}
    if agent_id:
        headers["X-Reva-Agent-Id"] = agent_id
    if user:
        headers["X-Reva-User"] = user
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
) -> Any:
    """One LLM turn, routed through Kong.

    `agent_id` and `user` become X-Reva-* headers for the Kong plugin to map
    into a Reva PDP evaluation before the request reaches the upstream model.
    """
    client = AsyncOpenAI(
        api_key=_require_key(),
        base_url=_require_llm_url(),
        default_headers=_identity_headers(agent_id=agent_id, user=user),
    )
    kwargs: dict[str, Any] = {"model": model or LLM_MODEL, "messages": messages}
    if tools:
        kwargs["tools"] = tools
    try:
        return await client.chat.completions.create(**kwargs)
    except APIStatusError as e:
        _raise_if_denied(e)
        raise
    except Exception as e:  # noqa: BLE001
        _raise_if_denied(e)
        raise


def _mcp_client(server: str, *, agent_id: str | None = None, user: str | None = None) -> Client:
    headers = {
        "Authorization": f"Bearer {_require_key()}",
        **_identity_headers(agent_id=agent_id, user=user),
    }
    return Client(
        StreamableHttpTransport(
            url=f"{_require_mcp_url()}/{server}/mcp",
            headers=headers,
        )
    )


async def list_tools(server: str, *, agent_id: str | None = None, user: str | None = None) -> list[dict[str, Any]]:
    """Discover an MCP server's tools via Kong, shaped for the OpenAI tools param.

    Tool names are prefixed with the server so the orchestrator can route a
    tool_call back to the right server later. The separator is `__` because
    OpenAI rejects `/` in function names — and `/` is what Reva resource ids
    typically use, so the two conventions are translated at this boundary.
    """
    try:
        async with _mcp_client(server, agent_id=agent_id, user=user) as c:
            return [
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
    except Exception as e:  # noqa: BLE001
        _raise_if_denied(e)
        raise


async def call_tool(server: str, tool: str, arguments: dict[str, Any],
                    *, agent_id: str | None = None, user: str | None = None) -> Any:
    """Invoke one MCP tool through Kong.

    A Reva denial surfaces as AuthorizationDenied — the tool's code never runs.
    Callers should catch it and tell the user they were not authorized.
    """
    try:
        async with _mcp_client(server, agent_id=agent_id, user=user) as c:
            result = await c.call_tool(tool, arguments)
            return result.structured_content or result.content
    except AuthorizationDenied:
        raise
    except Exception as e:  # noqa: BLE001
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


async def send_agent(agent: str, text: str, *,
                     history: list[dict[str, Any]] | None = None,
                     session_id: str | None = None,
                     agent_id: str | None = None, user: str | None = None) -> str:
    """Delegate to a sub-agent via A2A `message/send`, routed through Kong.

    The conversation travels the A2A-native way: the current turn as the message
    text, prior turns in `metadata.chatHistory`, and the thread as `contextId`.
    Kong reads that standard body to authorize the `invokeAgent` with Reva; a
    denial comes back as HTTP 403 and surfaces here as AuthorizationDenied.
    """
    url = f"{_require_a2a_url()}/{agent}"
    message = Message(
        message_id=str(uuid.uuid4()),
        role=Role.user,
        parts=[Part(root=TextPart(text=text))],
        context_id=session_id,
        metadata={"chatHistory": history or [], "user": user},
    )
    request = SendMessageRequest(id=str(uuid.uuid4()), params=MessageSendParams(message=message))
    headers = {"Authorization": f"Bearer {_require_key()}", **_identity_headers(agent_id=agent_id, user=user)}
    try:
        async with httpx.AsyncClient(headers=headers, timeout=90.0) as hc:
            client = A2AClient(httpx_client=hc, url=url)
            resp = await client.send_message(request)
    except AuthorizationDenied:
        raise
    except Exception as e:  # noqa: BLE001
        _raise_if_denied(e)
        raise
    return _extract_a2a_text(resp)
