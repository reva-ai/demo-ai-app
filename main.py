"""FastAPI entrypoint for the Kong-fronted agentic demo.

Serves the chat UI. /chat is a thin client: it makes one real, Kong-mediated
A2A call to billing-support-agent (gateway.send_agent) — the exact same
mechanism billing-support-agent itself uses to delegate to ticketing-agent /
booking-agent — and streams the trace + final reply back over SSE. This
process holds no orchestration logic of its own; it is a caller, not an agent.
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
# OPENAI_LOG defaults to debug too, set before `import gateway` pulls in
# `from openai import AsyncOpenAI` so the SDK's own logger picks it up.
os.environ.setdefault("OPENAI_LOG", "debug")

import gateway  # noqa: E402
import llm_agent  # noqa: E402

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "DEBUG").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("demo.main")

_STATIC = Path(__file__).with_name("static")
ORCHESTRATOR_ID = "billing-support-agent"

app = FastAPI(title="Reva Kong Agentic Demo", version="0.3.0")


@app.get("/")
async def index() -> FileResponse:
    """Chat UI — the front door for the demo."""
    return FileResponse(_STATIC / "index.html")


class ChatRequest(BaseModel):
    message: str
    user: str = "alice@analyst"
    # Identity the request is addressed to. Client-chosen on purpose: swap it
    # mid-demo and watch the Reva verdict flip (via Kong).
    agent_id: str = ORCHESTRATOR_ID
    # Prior turns [{role, content}, …] the client carries across a session.
    history: list[dict[str, Any]] | None = None
    # Stable thread id for the conversation → A2A contextId → Reva session.id.
    session_id: str | None = None


@app.post("/chat")
async def chat(req: ChatRequest, request: Request) -> StreamingResponse:
    """Server-sent events: trace events as they happen, then the final reply.

    Ingress `traceparent` is forwarded when present. If absent, one is minted
    for this turn and sent on the Kong hop below.
    """
    traceparent = request.headers.get("traceparent") or gateway.mint_traceparent()
    log.info(
        "chat start agent=%s user=%s session=%s ingress_traceparent=%s "
        "msg_len=%d history=%d",
        req.agent_id, req.user, req.session_id or "-",
        request.headers.get("traceparent") or "(none)",
        len(req.message or ""), len(req.history or []),
    )
    queue: asyncio.Queue = asyncio.Queue()

    async def run() -> None:
        try:
            queue.put_nowait({"type": "trace", "traceparent": traceparent})
            queue.put_nowait({"type": "tool_call", "kind": "agent",
                               "server": req.agent_id, "tool": "invoke"})
            reply_raw = await gateway.send_agent(
                req.agent_id, req.message,
                history=llm_agent.normalize_history(req.history),
                session_id=req.session_id, user=req.user, traceparent=traceparent,
            )
            payload = llm_agent.parse_reply_envelope(reply_raw)
            queue.put_nowait({"type": "allowed", "kind": "agent",
                               "server": req.agent_id, "tool": "invoke", "result": payload})
            llm_agent.emit_nested_card(req.agent_id, payload, queue.put_nowait)
            reply = payload.get("reply", reply_raw)
            log.info("chat done agent=%s reply_len=%d", req.agent_id, len(reply or ""))
            queue.put_nowait({"type": "reply", "text": reply})
        except gateway.AuthorizationDenied:
            log.warning("chat DENIED agent=%s", req.agent_id)
            queue.put_nowait({"type": "denied", "kind": "agent",
                               "server": req.agent_id, "tool": "invoke"})
            queue.put_nowait({"type": "reply",
                               "text": f"Reva denied '{req.user}' permission to invoke '{req.agent_id}'."})
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
