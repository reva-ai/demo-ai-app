# Reva × Kong — Agentic Demo

Billing-support agentic app hosted on **Render**. Every LLM and MCP hop goes
through your **cloud-hosted Kong**; a Kong plugin you write there calls **Reva
PDP** for allow/deny. This repo does **not** contain a Kong plugin or talk to
Reva directly.

## Architecture

```
User
  │
  ▼
agent-app (Render)   chat UI + orchestrator
  │
  ├─ LLM  ──► Kong ──► (plugin → Reva PDP) ──► upstream model
  │
  ├─ MCP  ──► Kong ──► (plugin → Reva PDP) ──► billing-mcp
  │                                        └► external-mcp
  │
  └─ A2A  ──► Kong ──► (plugin → Reva PDP) ──► ticketing-agent
                                           └► booking-agent
```

Tools are reached over **MCP**; sub-agents over the **A2A protocol**
(`message/send`). Both traverse Kong, so orchestrator→ticketing is a standard
A2A call that Reva authorizes (`invokeAgent`). A raw HTTP call would bypass it.
The conversation travels the A2A-native way — current turn as the message text,
prior turns in `metadata.chatHistory`, thread as `contextId` — so Reva evaluates
with full context and no custom headers.

## Services (Render Blueprint)

| Service | Role |
|---------|------|
| `agent-app` | FastAPI: `/`, `/chat`, `/healthz` |
| `billing-mcp` | Demo tools (report / compliance / PII) |
| `external-mcp` | Untrusted `analytics_probe` |
| `ticketing-agent` | Sub-agent A2A; own LLM hop via Kong |
| `booking-agent` | Sub-agent A2A (slots) |

Deploy: push the repo → Render → New → Blueprint → select the repo (`render.yaml`).

## Local run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill KONG_* and LLM_MODEL

# terminals: MCP servers (or use Render URLs via Kong only)
python billing_mcp_server.py &
python external_mcp_server.py &
python ticketing_agent_server.py &
python booking_agent_server.py &

uvicorn main:app --reload --port 8000
```

Open http://localhost:8000

## Env vars

| Variable | Purpose |
|----------|---------|
| `KONG_LLM_URL` | OpenAI-compatible base on Kong (no trailing slash) |
| `KONG_MCP_URL` | MCP proxy base; app calls `{KONG_MCP_URL}/{server}/mcp` |
| `KONG_A2A_URL` | A2A proxy base; app calls `{KONG_A2A_URL}/{agent}` (message/send) |
| `KONG_API_KEY` | `Authorization: Bearer …` on every hop |
| `LLM_MODEL` | Model id upstream expects (default `gpt-4o`) |

`ticketing-agent` needs the same `KONG_LLM_URL` / `KONG_API_KEY` / `LLM_MODEL`
because it makes its own model call under identity `ticketing-agent`.

## Kong plugin contract

Configure routes on Kong Cloud so the agent can reach LLM, MCP, and A2A through
them. This app sends only **identity** headers on every hop (never conversation):

| Header | Example | Meaning |
|--------|---------|---------|
| `Authorization` | `Bearer <KONG_API_KEY>` | Kong consumer / key-auth |
| `X-Reva-Agent-Id` | `billing-support-agent` | Acting agent (subject) |
| `X-Reva-User` | `alice@analyst` | On-behalf-of user (principal) |

The **conversation** is read by Kong from the standard request body — no custom
headers:

| Hop | userQuery | chatHistory | session.id |
|-----|-----------|-------------|------------|
| LLM (`/llm`) | last `user` message | OpenAI `messages[]` | request id |
| MCP tool (`/mcp/*`) | tool arguments | — | `mcp-session-id` |
| A2A agent (`/a2a/*`) | message text `parts[]` | `message.metadata.chatHistory` | `message.contextId` |

Path layout (segments must match `agents.TOOL_SERVERS` / `agents.AGENT_SERVERS`):

```
{KONG_MCP_URL}/billing-mcp/mcp      → Render billing-mcp
{KONG_MCP_URL}/external-mcp/mcp     → Render external-mcp
{KONG_A2A_URL}/ticketing-agent      → Render ticketing-agent (A2A message/send)
{KONG_A2A_URL}/booking-agent        → Render booking-agent   (A2A message/send)
```

**Deny:** return **HTTP 403** with a body/message containing `Blocked by Reva`.
The orchestrator treats that as a soft denial (explains to the user) instead of
crashing.

Map identity headers + standard request body into your Reva PDP evals in the Kong
plugin (invokeModel / invokeTool / invokeAgent). Policy store and Cedar schemas
are unchanged by this app.

## Demo agents & tools

| Identity / server | Notes |
|-------------------|--------|
| `billing-support-agent` | Orchestrator (default in UI) |
| `billing-mcp` | `get_billing_report`, `get_compliance_status`, `get_customer_pii` |
| `external-mcp` | `analytics_probe` (typically forbidden) |
| `ticketing-agent` | A2A sub-agent: opens/triages tickets (+ nested LLM) |
| `booking-agent` | A2A sub-agent: lists/books callback slots |

Server names are load-bearing for Reva resource ids (`{server}/{tool}` for tools,
`{agent}` for A2A agents).
