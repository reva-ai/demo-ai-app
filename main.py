"""FastAPI entrypoint for the Kong-fronted agentic demo.

Serves the chat UI and orchestrator. Every LLM and MCP hop the orchestrator
makes goes through cloud-hosted Kong (see gateway.py); Kong's plugin calls
Reva Trust Gateway for allow/deny. This process never talks to Reva directly.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

load_dotenv(Path(__file__).with_name(".env"))

# Permanently on: DEBUG by default (LOG_LEVEL can still override), and
# OPENAI_LOG defaults to debug too, set before `import agents` pulls in
# gateway.py's `from openai import AsyncOpenAI` so the SDK's own logger
# picks it up. Together these show the raw request/response behind a
# truncated error like gateway.py's `str(e)[:160]`.
os.environ.setdefault("OPENAI_LOG", "debug")

import agents  # noqa: E402 — after the OPENAI_LOG default above, on purpose
import gateway  # noqa: E402
import a2a_agent  # noqa: E402
from a2a.types import AgentSkill  # noqa: E402

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "DEBUG").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("demo.main")

_STATIC = Path(__file__).with_name("static")

app = FastAPI(title="Reva Kong Agentic Demo", version="0.2.0")


async def _checkpoint_handler(
    text: str,
    history: list[dict[str, Any]],
    user: str | None,
    session_id: str | None,
    *,
    traceparent: str | None = None,
) -> str:
    """Answers the self-referential A2A call orchestrate() makes on itself.

    By the time this runs, Kong has already asked Reva to authorize invoking
    this agent and proxied the call through — that decision already happened.
    This handler's only job is to complete the round trip; it must NOT invoke
    orchestrate() itself, or every chat message would re-enter this same
    check in a loop.
    """
    del history, user, session_id, traceparent
    log.info("self-checkpoint answered text_len=%d", len(text or ""))
    return "ok"


_a2a_app = a2a_agent.build_app(
    name=agents.ORCHESTRATOR_ID,
    description="Billing support orchestrator — this endpoint exists only so "
                "Kong/Reva can authorize 'invoke this agent' before a chat "
                "turn starts; it does no real work.",
    skills=[
        AgentSkill(
            id="checkpoint",
            name="Authorization checkpoint",
            description="Always answers 'ok'. Real work happens via /chat, "
                        "only after this call is authorized.",
            tags=["internal"],
            examples=[],
        ),
    ],
    handler=_checkpoint_handler,
    url=f"{gateway.AGENT_URL}/a2a/" if gateway.AGENT_URL else None,
)
# Mounted, not run standalone: this service already runs its own uvicorn
# (main:app) per render.yaml. a2a_agent.run() is for the separate sub-agent
# processes (ticketing-agent, booking-agent), not this one.
app.mount("/a2a", _a2a_app)


@app.get("/")
async def index() -> FileResponse:
    """Chat UI — the front door for the demo."""
    return FileResponse(_STATIC / "index.html")


@app.get("/ui")
async def index_alias() -> FileResponse:
    """Same page under a second path.

    Render's free tier fronts the service with a hibernation proxy that
    answers "/" itself, so the request never reaches this app and the UI
    appears to 404. Any other path passes through untouched.
    """
    return FileResponse(_STATIC / "index.html")


class ChatRequest(BaseModel):
    message: str
    user: str = "alice@analyst"
    # Identity the orchestrator runs under. Client-chosen on purpose: swap it
    # mid-demo and watch the Reva verdict flip (via Kong).
    agent_id: str = agents.ORCHESTRATOR_ID
    model: str | None = None  # None -> LLM_MODEL from env.
    servers: list[str] | None = None
    # Prior turns [{role, content}, …] the client carries across a session.
    history: list[dict[str, Any]] | None = None
    # Stable thread id for the conversation → A2A contextId → Reva session.id.
    session_id: str | None = None


@app.post("/chat")
async def chat(req: ChatRequest, request: Request) -> StreamingResponse:
    """Server-sent events: trace events as they happen, then the final reply.

    Ingress `traceparent` is forwarded when present. If absent, the orchestrator
    mints one for the turn and sends it on every Kong hop.
    """
    # W3C Trace Context is a header, not a body field.
    traceparent = request.headers.get("traceparent")
    log.info(
        "chat start agent=%s user=%s model=%s session=%s ingress_traceparent=%s "
        "msg_len=%d history=%d",
        req.agent_id, req.user, req.model or "(default)", req.session_id or "-",
        traceparent or "(none)", len(req.message or ""), len(req.history or []),
    )
    queue: asyncio.Queue = asyncio.Queue()

    async def run() -> None:
        try:
            reply = await agents.orchestrate(
                req.message, user=req.user, agent_id=req.agent_id,
                model=req.model, servers=req.servers, history=req.history,
                session_id=req.session_id, traceparent=traceparent,
                emit=queue.put_nowait,
            )
            log.info("chat done agent=%s reply_len=%d", req.agent_id, len(reply or ""))
            queue.put_nowait({"type": "reply", "text": reply})
        except Exception as e:  # noqa: BLE001
            log.exception("chat failed agent=%s: %s", req.agent_id, e)
            queue.put_nowait({"type": "error", "text": str(e)[:200]})
        finally:
            queue.put_nowait(None)

    async def stream():
        task = asyncio.create_task(run())
        try:
            while (event := await queue.get()) is not None:
                yield f"data: {json.dumps(event, default=str)}\n\n"
        finally:
            task.cancel()

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
