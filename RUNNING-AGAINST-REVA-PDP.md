# Running this app against the reva-ai-governance gateway

The Kong demo app works against the `reva-ai-governance` plugin. Identity is a
JWT on `Authorization` (`sub` = the UI user). Kong key-auth uses `apikey`.
`X-Reva-Agent-Id` / `X-Reva-User` are not sent (`authorize_agent` is off).

Only the environment differs.

## Local

```sh
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`, pointing at whichever data plane you are running:

```
KONG_LLM_URL=http://localhost:8010/llm
KONG_MCP_URL=http://localhost:8010/mcp
KONG_A2A_URL=http://localhost:8010/a2a
KONG_API_KEY=not-used-by-reva-ai-governance
LLM_MODEL=gpt-4o
```

`KONG_API_KEY` must be non-empty — the app refuses to start without it — but
the reva-ai-governance gateway has no `key-auth`, so the value is not checked.

```sh
./.venv/bin/uvicorn main:app --port 8600
```

Then open http://localhost:8600.

## Render

A second service, separate from the `reva-kong-dataplane` gateway:

| Setting | Value |
|---|---|
| Language | Python 3 |
| Root Directory | `reva-kong-plugin/demo-app` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/healthz` |

Environment variables are the same five, with the gateway's public URL in
place of localhost.

## Verified

Against the hybrid control plane `reva-pdp-hybrid`, 2026-08-25: the agent
invoked the model and then called `get_billing_report` on the billing MCP
server, and the plugin authorized both hops on one traceparent.

    [reva-ai-governance] invokeModel gpt-4o                        allowed=true status=200
    [reva-ai-governance] invokeTool billing-mcp/get_billing_report allowed=true status=200
