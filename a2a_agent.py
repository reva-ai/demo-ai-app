"""Shared plumbing for exposing a sub-agent over the A2A protocol.

Why A2A (and not MCP) for sub-agents: agent-to-agent delegation is a first-class
concept in A2A. The orchestrator sends a standard `message/send`; Kong fronts this
route and asks Reva to authorize the `invokeAgent` before the message is delivered.

Forwarding (A2A-native metadata + W3C header):
  - `metadata.chatHistory` : [{role, content}, …]
  - `metadata.traceparent` : same W3C trace (also on the HTTP `traceparent` header)
  - `contextId`            : session.id
  - message text parts     : current turn

`context.hops` is built by Kong, not by this app.

Each concrete agent supplies one async handler; everything else is boilerplate.
"""

from __future__ import annotations

import os
from typing import Any, Awaitable, Callable

import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils import new_agent_text_message
from starlette.requests import Request
from starlette.responses import JSONResponse

# handler(text, history, user, session_id, *, traceparent) -> reply text
Handler = Callable[..., Awaitable[str]]


def _header_traceparent(context: RequestContext) -> str | None:
    """Prefer the W3C HTTP header; fall back to A2A metadata."""
    call = getattr(context, "call_context", None)
    state = getattr(call, "state", None) or {}
    headers = state.get("headers") if isinstance(state, dict) else None
    if isinstance(headers, dict):
        for key in ("traceparent", "Traceparent"):
            if headers.get(key):
                return headers[key]
    for attr in ("headers", "metadata"):
        blob = getattr(call, attr, None)
        if isinstance(blob, dict):
            for key in ("traceparent", "Traceparent"):
                if blob.get(key):
                    return blob[key]
    return None


class _HandlerExecutor(AgentExecutor):
    """Adapts a plain async handler to the A2A executor interface."""

    def __init__(self, handler: Handler) -> None:
        self._handler = handler

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        text = context.get_user_input()
        meta = (context.message.metadata if context.message else None) or {}
        history = meta.get("chatHistory") or []
        if not isinstance(history, list):
            history = []
        user = meta.get("user")
        traceparent = _header_traceparent(context) or meta.get("traceparent")
        reply = await self._handler(
            text,
            history,
            user,
            context.context_id,
            traceparent=traceparent,
        )
        await event_queue.enqueue_event(new_agent_text_message(reply, context.context_id))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("cancellation is not supported in this demo")


def build_app(
    *,
    name: str,
    description: str,
    skills: list[AgentSkill],
    handler: Handler,
    url: str | None = None,
):
    """Build the runnable A2A Starlette app for one sub-agent."""
    card = AgentCard(
        name=name,
        description=description,
        url=url or os.environ.get("A2A_PUBLIC_URL", f"http://localhost:{os.environ.get('PORT', '8003')}/"),
        version="1.0.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=skills,
    )
    request_handler = DefaultRequestHandler(
        agent_executor=_HandlerExecutor(handler),
        task_store=InMemoryTaskStore(),
    )
    app = A2AStarletteApplication(agent_card=card, http_handler=request_handler).build()
    # Plain liveness check - no A2A/Reva plumbing, just proves the process is up.
    # Render's free tier sleeps an idle service, so this is also what a
    # keep-warm loop should hit rather than guessing at an A2A-shaped request.
    app.add_route("/healthz", _healthz, methods=["GET"])
    return app


async def _healthz(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


def run(app, default_port: str) -> None:
    """Serve the A2A app; Render injects $PORT, locally falls back."""
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", default_port)))
