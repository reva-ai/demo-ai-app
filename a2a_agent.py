"""Shared plumbing for exposing a sub-agent over the A2A protocol.

Why A2A (and not MCP) for sub-agents: agent-to-agent delegation is a first-class
concept in A2A. The orchestrator sends a standard `message/send` whose body
carries the turn's text (the userQuery) and — in the message `metadata` — the
running conversation (`chatHistory`) plus the acting user. Kong sits in front of
each A2A route and reads that standard body to build the Reva PDP payload; no
custom headers, no per-customer code.

Conversation forwarding is A2A-native:
  - `metadata.chatHistory` : [{role, content}, …]  → context.chatHistory
  - `contextId`            : stable thread id       → session.id
  - message text parts     : the current turn       → userQuery

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

# handler(text, chat_history, user, session_id) -> reply text
Handler = Callable[[str, list[dict[str, Any]], str | None, str | None], Awaitable[str]]


class _HandlerExecutor(AgentExecutor):
    """Adapts a plain async handler to the A2A executor interface.

    It pulls the standard A2A conversation off the request — text parts for the
    current turn, `metadata.chatHistory` for prior turns — and hands them to the
    agent's own logic.
    """

    def __init__(self, handler: Handler) -> None:
        self._handler = handler

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        text = context.get_user_input()
        meta = (context.message.metadata if context.message else None) or {}
        history = meta.get("chatHistory") or []
        if not isinstance(history, list):
            history = []
        user = meta.get("user")
        reply = await self._handler(text, history, user, context.context_id)
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
    return A2AStarletteApplication(agent_card=card, http_handler=request_handler).build()


def run(app, default_port: str) -> None:
    """Serve the A2A app; Render injects $PORT, locally falls back."""
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", default_port)))
