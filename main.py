"""FastAPI entrypoint for the Kong-fronted agentic demo.

Serves the chat UI and orchestrator. Every LLM and MCP hop the orchestrator
makes goes through cloud-hosted Kong (see gateway.py); Kong's plugin calls
Reva PDP for allow/deny. This process never talks to Reva directly.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

import agents

load_dotenv(Path(__file__).with_name(".env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("demo.main")

_STATIC = Path(__file__).with_name("static")

app = FastAPI(title="Reva Kong Agentic Demo", version="0.2.0")


@app.get("/")
async def index() -> FileResponse:
    """Chat UI — the front door for the demo."""
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

    If an ingress gateway already set `traceparent`, we forward it on every Kong
    hop. We never mint one here — that's Kong's job when the header is absent.
    """
    # W3C Trace Context is a header, not a body field.
    traceparent = request.headers.get("traceparent")
    log.info(
        "chat start agent=%s user=%s model=%s session=%s traceparent=%s msg_len=%d history=%d",
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
