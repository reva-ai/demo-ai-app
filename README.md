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
  └─ MCP  ──► Kong ──► (plugin → Reva PDP) ──► billing-mcp
                                           │► external-mcp
                                           │► ticketing-agent
                                           └► booking-agent
```

Sub-agents are MCP servers on purpose: orchestrator→ticketing is an MCP tool
call that traverses Kong (and Reva). A raw HTTP call would bypass authorization.

## Services (Render Blueprint)

| Service | Role |
|---------|------|
| `agent-app` | FastAPI: `/`, `/chat`, `/healthz` |
| `billing-mcp` | Demo tools (report / compliance / PII) |
| `external-mcp` | Untrusted `analytics_probe` |
| `ticketing-agent` | Sub-agent MCP; own LLM hop via Kong |
| `booking-agent` | Sub-agent MCP (slots) |

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
| `KONG_API_KEY` | `Authorization: Bearer …` on every hop |
| `LLM_MODEL` | Model id upstream expects (default `gpt-4o`) |

`ticketing-agent` needs the same `KONG_LLM_URL` / `KONG_API_KEY` / `LLM_MODEL`
because it makes its own model call under identity `ticketing-agent`.

## Kong plugin contract

Configure routes on Kong Cloud so the agent can reach LLM and MCP through them.
This app sends these headers on **every** LLM and MCP request:

| Header | Example | Meaning |
|--------|---------|---------|
| `Authorization` | `Bearer <KONG_API_KEY>` | Kong consumer / key-auth |
| `X-Reva-Agent-Id` | `billing-support-agent` | Acting agent |
| `X-Reva-User` | `alice@analyst` | On-behalf-of user |

Suggested MCP path layout (must match `agents.SERVERS`):

```
{KONG_MCP_URL}/billing-mcp/mcp      → Render billing-mcp
{KONG_MCP_URL}/external-mcp/mcp     → Render external-mcp
{KONG_MCP_URL}/ticketing-agent/mcp  → Render ticketing-agent
{KONG_MCP_URL}/booking-agent/mcp    → Render booking-agent
```

**Deny:** return **HTTP 403** with a body/message containing `Blocked by Reva`.
The orchestrator treats that as a soft denial (explains to the user) instead of
crashing.

Map headers + request shape into your Reva PDP evals in the Kong plugin
(Agent / invokeModel / InvokeTool, etc.). Policy store and Cedar schemas are
unchanged by this app.

## Demo agents & tools

| Identity / server | Notes |
|-------------------|--------|
| `billing-support-agent` | Orchestrator (default in UI) |
| `billing-mcp` | `get_billing_report`, `get_compliance_status`, `get_customer_pii` |
| `external-mcp` | `analytics_probe` (typically forbidden) |
| `ticketing-agent` | `create_ticket`, `close_ticket` (+ nested LLM) |
| `booking-agent` | `list_slots`, `book_slot` |

Server names are load-bearing for Reva resource ids (`{server}/{tool}`).
