# Agentic demo

Billing-support chat app. The browser talks to `agent-app`. Every model call, tool call, and agent handoff goes through your Kong gateway, and a plugin on Kong calls Reva for allow or deny. This repo does not contain that plugin and does not talk to Reva itself.

Nothing here is tied to a particular host. Each service is one Python process. Run them on a laptop, in containers, or on any platform that can set environment variables and route HTTP.

## Architecture

```
User
  │
  ▼
agent-app                         chat UI + /chat
  │
  └─ A2A  ──► Kong ──► billing-support-agent
                          │
                          ├─ LLM ──► Kong ──► upstream model
                          │
                          ├─ A2A ──► Kong ──► ticketing-agent
                          │                     ├─ LLM ──► Kong ──► upstream model
                          │                     └─ MCP ──► Kong ──► ticketing-mcp
                          │
                          └─ A2A ──► Kong ──► booking-agent
                                                ├─ LLM ──► Kong ──► upstream model
                                                └─ MCP ──► Kong ──► booking-mcp
```

Sub-agents are reached with A2A `message/send`. Tools are reached with MCP. Both go through Kong, so Reva sees `invokeAgent` and `invokeTool` rather than a raw HTTP call that skips the plugin.

## Services

| Process | Role | Listen | Health |
|---------|------|--------|--------|
| `agent-app` | Chat UI. `POST /chat` calls `billing-support-agent` through Kong. | `8000` | `GET /healthz` |
| `billing-support-agent` | Orchestrator. Own model call, then delegates to the two specialists. | `8002` | `GET /healthz` |
| `ticketing-agent` | Opens, closes, and checks tickets via `ticketing-mcp`. | `8003` | `GET /healthz` |
| `booking-agent` | Lists and books callback slots via `booking-mcp`. | `8004` | `GET /healthz` |
| `ticketing-mcp` | Canned tools: `open_ticket`, `close_ticket`, `get_ticket_status`. | `8005` | `GET /healthz` |
| `booking-mcp` | Canned tools: `list_slots`, `book_slot`. | `8006` | `GET /healthz` |

Ports above are the defaults when `PORT` is unset. A host that injects `PORT` overrides them. Every process binds `0.0.0.0`.

Kong must be able to reach the three agents and both MCP servers. The agent processes must be able to reach Kong. If Kong is not on the same machine, publish those processes on addresses Kong can call.

## Prerequisites

- Python 3.12 or newer
- A Kong (or compatible) gateway in front of the model, the MCP servers, and the A2A agents, with your Reva plugin on those routes

Install once:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` before starting the agents. See the per-process tables below for which values each one actually reads.

## Run locally

Start the processes from the repo root, in this order. The agents load `.env` from the current directory. The MCP servers do not read `.env`; their defaults are enough locally.

```bash
# MCP servers — no Kong settings
python ticketing_mcp_server.py          # http://127.0.0.1:8005/mcp
python booking_mcp_server.py            # http://127.0.0.1:8006/mcp

# agents — need the Kong variables in .env
python billing_support_agent_server.py  # http://127.0.0.1:8002/
python ticketing_agent_server.py        # http://127.0.0.1:8003/
python booking_agent_server.py          # http://127.0.0.1:8004/

# UI
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

Point Kong's upstreams at those local URLs (or at whatever public address you published them on):

| Kong route the app calls | Upstream |
|--------------------------|----------|
| `{KONG_LLM_URL}` | your model provider |
| `{KONG_MCP_URL}/ticketing-mcp/mcp` | `ticketing-mcp` |
| `{KONG_MCP_URL}/booking-mcp/mcp` | `booking-mcp` |
| `{KONG_A2A_URL}/billing-support-agent` | `billing-support-agent` |
| `{KONG_A2A_URL}/ticketing-agent` | `ticketing-agent` |
| `{KONG_A2A_URL}/booking-agent` | `booking-agent` |

Server and agent names in those paths are load-bearing. Reva resource ids use `{server}/{tool}` for tools and the agent name for A2A agents.

## Run on any host

Same six commands. Give each process its own environment (container, VM, platform service — it does not matter). Install dependencies with `pip install -r requirements.txt`, then start the command for that process. Set `PORT` to the port the host assigned, and set `PUBLIC_URL` to the URL Kong uses as that service's upstream when a policy matches agents by URL.

A single image is enough for containers. Pass each service's variables at runtime. `.env` is for a local run and is not something to bake into an image. Override the command per container:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# command is set per service; see the tables below
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Use each service's `/healthz` as the liveness check. MCP health checks are plain HTTP, not an MCP request.

## Environment variables

Locally, one `.env` in the repo root is enough. `agent-app` loads that file next to `main.py`. The three agents load it from the working directory via `gateway.py`, so start them from the repo root. Variables a process does not use are ignored.

On a host, set only the rows marked required for that process.

### agent-app

Chat UI. One outbound hop: A2A `message/send` to `billing-support-agent`.

```bash
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

| Variable | Required | Purpose |
|----------|----------|---------|
| `KONG_A2A_URL` | yes | A2A base on Kong, no trailing slash. The app calls `{KONG_A2A_URL}/billing-support-agent`. |
| `KONG_API_KEY` | yes | Kong key-auth. Sent as the `apikey` header. |
| `PUBLIC_URL` | no | This process's public URL. Sent as `X-Reva-Agent-Id`. Omit it and the header is left off. |
| `LOG_LEVEL` | no | `DEBUG`, `INFO`, `WARNING`, … Default `DEBUG`. |
| `OPENAI_LOG` | no | OpenAI SDK HTTP logging. Default `debug`. |
| `PORT` | no | Pass it to uvicorn as `--port`. Default `8000` in the command above. |

### billing-support-agent

Orchestrator. Own model call, then A2A to `ticketing-agent` and `booking-agent`.

```bash
python billing_support_agent_server.py
```

| Variable | Required | Purpose |
|----------|----------|---------|
| `KONG_LLM_URL` | yes | OpenAI-compatible base on Kong, no trailing slash. |
| `KONG_A2A_URL` | yes | A2A base. Calls `{KONG_A2A_URL}/ticketing-agent` and `{KONG_A2A_URL}/booking-agent`. |
| `KONG_API_KEY` | yes | Kong key-auth (`apikey` header). |
| `LLM_MODEL` | no | Model id the upstream expects. Default `gpt-4o`. |
| `PUBLIC_URL` | no | This process's public URL, sent as `X-Reva-Agent-Id`. |
| `A2A_PUBLIC_URL` | no | URL written on the agent card. When unset: `http://localhost:$PORT/` if `PORT` is set, otherwise `http://localhost:8003/`. |
| `PORT` | no | Listen port. Default `8002`. |

### ticketing-agent

Own model call, then MCP tools on `ticketing-mcp`.

```bash
python ticketing_agent_server.py
```

| Variable | Required | Purpose |
|----------|----------|---------|
| `KONG_LLM_URL` | yes | OpenAI-compatible base on Kong, no trailing slash. |
| `KONG_MCP_URL` | yes | MCP base. Calls `{KONG_MCP_URL}/ticketing-mcp/mcp`. |
| `KONG_API_KEY` | yes | Kong key-auth (`apikey` header). |
| `LLM_MODEL` | no | Model id the upstream expects. Default `gpt-4o`. |
| `PUBLIC_URL` | no | This process's public URL, sent as `X-Reva-Agent-Id`. |
| `A2A_PUBLIC_URL` | no | URL written on the agent card. When unset: `http://localhost:$PORT/` if `PORT` is set, otherwise `http://localhost:8003/`. |
| `PORT` | no | Listen port. Default `8003`. |

### booking-agent

Own model call, then MCP tools on `booking-mcp`. Same variables as `ticketing-agent`, except the MCP path is `{KONG_MCP_URL}/booking-mcp/mcp`.

```bash
python booking_agent_server.py
```

| Variable | Required | Purpose |
|----------|----------|---------|
| `KONG_LLM_URL` | yes | OpenAI-compatible base on Kong, no trailing slash. |
| `KONG_MCP_URL` | yes | MCP base. Calls `{KONG_MCP_URL}/booking-mcp/mcp`. |
| `KONG_API_KEY` | yes | Kong key-auth (`apikey` header). |
| `LLM_MODEL` | no | Model id the upstream expects. Default `gpt-4o`. |
| `PUBLIC_URL` | no | This process's public URL, sent as `X-Reva-Agent-Id`. |
| `A2A_PUBLIC_URL` | no | URL written on the agent card. When unset: `http://localhost:$PORT/` if `PORT` is set, otherwise `http://localhost:8003/`. |
| `PORT` | no | Listen port. Default `8004`. |

### ticketing-mcp

No Kong variables. Does not read `.env`.

```bash
python ticketing_mcp_server.py
```

| Variable | Required | Purpose |
|----------|----------|---------|
| `PORT` | no | Listen port. Default `8005`. MCP endpoint is `/mcp`. |

### booking-mcp

No Kong variables. Does not read `.env`.

```bash
python booking_mcp_server.py
```

| Variable | Required | Purpose |
|----------|----------|---------|
| `PORT` | no | Listen port. Default `8006`. MCP endpoint is `/mcp`. |

## What Kong has to do

These headers go out on every hop the app makes:

| Header | Value | Meaning |
|--------|-------|---------|
| `Authorization` | `Bearer <jwt>` with `sub` set to the UI user (for example `alice@analyst`) | User identity. The JWT is unsigned; a real deployment can put Kong JWT or OIDC in front. |
| `apikey` | `KONG_API_KEY` | Kong key-auth. |
| `X-Reva-Agent-Id` | `PUBLIC_URL` | This service's identity. Sent only when `PUBLIC_URL` is set. Match it to the upstream URL your policy uses for the agent. |
| `X-Reva-Session-Id` | conversation id | Groups turns into one session. |
| `traceparent` | W3C trace id | One trace per chat turn. Forward it upstream when it is already present. |

A denial is HTTP 403 with a body that contains `Blocked by Reva`. The app treats that as a soft refusal and explains it in the chat instead of crashing.

`RUNNING-AGAINST-REVA-PDP.md` covers the same app pointed at the `reva-ai-governance` gateway.
