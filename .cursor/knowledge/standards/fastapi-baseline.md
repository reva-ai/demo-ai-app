<!--
GENERATED REVA STANDARD SNAPSHOT — DO NOT EDIT IN THIS REPOSITORY
Source: KarthikRamesh/reva-standards/Python/FastAPI/baseline.md
Standards revision: 740fdff52ba1d093d36652347f64850c51ce9700

Task-authorized exceptions:
1. New or materially changed executable production code targets 95% changed-code
   coverage; this does not rewrite or lower an existing repository/build/CI threshold.
2. Indexed, digest-bound nested .cursor directories are permitted as module-specific overlays;
   root AGENTS.md remains the only agent-instruction authority.

These two exceptions supersede only directly conflicting points in this snapshot. Every other
organization, security, tenancy, architecture, quality, delivery, and operational requirement
remains authoritative. The source standard remains the change-control authority.
-->

# Reva FastAPI Baseline

| Field | Value |
|---|---|
| Status | Normative framework baseline |
| Extends | [`../../baseline.md`](../../baseline.md) and [`../baseline.md`](../baseline.md) |
| Applies to | Reva Python HTTP services and agents using FastAPI |
| Current Reva profile | Python 3.13, FastAPI, Pydantic v2, `reva_utility`, loguru, OpenTelemetry |

FastAPI is Reva's approved Python HTTP framework. It remains an adapter at the service edge;
FastAPI request, response, dependency, and exception types do not define the application or
domain architecture.

## 1. Application construction and lifespan

Separate application construction from process startup and use the FastAPI lifespan protocol:

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    resources = await create_resources()
    app.state.resources = resources
    try:
        yield
    finally:
        await resources.aclose()


def create_app() -> FastAPI:
    app = FastAPI(title="Policy Service", lifespan=lifespan)
    register_exception_handlers(app)
    register_platform_middleware(app)
    app.include_router(policy_router, prefix="/policies", tags=["policies"])
    return app
```

- `create_app()` **MUST NOT** start Uvicorn, open a listening socket, install process signal
  handlers, or create a private event loop.
- `main.py`/the process entrypoint loads validated settings, initializes telemetry before
  instrumented traffic, constructs the app, and owns fatal-process behavior.
- Use `lifespan` for new services. Do not combine it with legacy `@app.on_event("startup")` or
  `@app.on_event("shutdown")` handlers.
- Long-lived HTTP clients, database/cache/broker pools, model resources, task registries, and
  telemetry providers are acquired once and closed in reverse order.
- Partial startup failure **MUST** close resources already acquired and fail the process.
  `AsyncExitStack` SHOULD be used when several independently acquired resources need reliable
  unwinding.
- Do not create a mutable process-global `FastAPI()` instance that tests and imports share.
- App state stores only application-scoped resources. Prefer typed dependency containers over
  arbitrary state keys, and do not store request/tenant data in app state.
- Router, middleware, exception-handler, and instrumentation registration completes before the
  application becomes ready. Runtime route mutation is prohibited.

## 2. Feature and module layout

A capability SHOULD own its transport adapter:

```text
src/<service_package>/
  application/policies/
  domain/policies/
  adapters/http/policies/
    router.py
    schemas.py
    dependencies.py
    handlers.py
    mappers.py
  adapters/clients/
  platform/
    auth.py
    errors.py
    health.py
    middleware.py
    telemetry.py
  main.py
tests/
  unit/
  integration/
  contract/
  security/
```

| Artifact | Required name |
|---|---|
| Router module | `router.py` inside the feature, or `<feature>_router.py` in a small legacy service |
| Request/response schemas | `schemas.py` or `<feature>_schemas.py` |
| Dependency providers | `dependencies.py` |
| Transport mapper | `mappers.py` |
| Application operation | intent name such as `create_policy.py`, not `service2.py` |
| Router object | `<feature>_router` |
| Route handler | operation intent such as `create_policy`, `list_policies`, `get_policy` |
| Dependency provider | `get_<dependency>` for request-scoped lookup or `provide_<dependency>` for composition |
| OpenAPI operation ID | stable domain operation, unique within the service |

- A router contains transport concerns: schema-bound input, dependency declarations, status and
  header selection, application invocation, and output mapping.
- Business rules, authorization payload construction, persistence, and remote-client logic
  **MUST NOT** accumulate in route handlers.
- Do not create one giant router for unrelated capabilities or one global schemas module for the
  whole service.
- Framework types stop at the adapter. Pass validated commands/queries and the standard Reva
  request context inward.
- Prefixes and tags are defined once at router registration rather than repeated in every route.
- Static and parameter routes use unambiguous resource paths. URLs use lowercase plural resource
  nouns with hyphens; Python parameter identifiers remain `snake_case`.

## 3. API and OpenAPI contracts

- Every endpoint **MUST** be represented in the generated/owned OpenAPI contract and checked for
  compatibility in CI.
- Route decorators define the success status, response model, operation ID, tags, summary, and
  every expected error response.
- HTTP methods and status codes follow the company baseline. Creation normally returns 201;
  accepted durable work returns 202 with an operation resource; 204 has no response body.
- Collection routes use bounded pagination, stable ordering, and allow-listed filtering/sorting.
- Headers, media types, idempotency semantics, concurrency/version behavior, and deprecation
  state are explicit contract elements.
- OpenAPI descriptions explain domain behavior and security semantics without disclosing
  implementation details.
- Interactive documentation is disabled or access-controlled in exposed production
  environments according to platform policy. Approved tooling can still access the protected
  OpenAPI document.
- A generated client or contract test SHOULD be used for important consumers to catch drift.

## 4. Pydantic request and response schemas

Every JSON route **MUST** declare a Pydantic request model where applicable and an explicit
`response_model`.

- Use Pydantic v2 APIs and configuration. Do not add new `.dict()`, `.json()`, `parse_obj`, or
  legacy inner `class Config` usage.
- Input, patch, output, persistence, and domain representations are separate when their
  mutability, optionality, or data-exposure rules differ.
- Write/security-sensitive request models SHOULD use `ConfigDict(extra="forbid")` unless the
  contract intentionally supports extensions.
- Define string length/pattern, collection count, numeric range, enum/literal, URL, timestamp,
  recursion, and nested-object constraints.
- Use strict validation at security-sensitive boundaries where coercion could change meaning.
  Any intentional coercion is documented and tested.
- Patch models distinguish missing from explicit `null`; do not use a default of `None` when the
  contract cannot distinguish those states.
- Response models are allow-lists. They prevent accidental disclosure of secrets, internal
  fields, database columns, or model/provider payloads.
- Never return a raw ORM/database row, SDK object, exception, `httpx.Response`, or arbitrary
  dictionary from a public handler.
- Sensitive fields use appropriate Pydantic secret types internally but are normally omitted
  entirely from response DTOs and logs.
- Custom validators are deterministic and side-effect free. Database, network, PDP, cache, or
  model calls do not run in Pydantic validators.
- Domain invariants and authorization still run after structural validation; schema validation
  is not a policy decision.

## 5. Dependency injection

- Use `Annotated[DependencyType, Depends(provider)]` for route dependencies so types and
  dependency intent remain visible.
- Providers return application-owned interfaces rather than leaking a concrete vendor client
  into every handler.
- Application-scoped resources come from lifespan-owned state/container. Do not construct a new
  HTTP client, database engine, Redis connection, or telemetry provider per request.
- A dependency that acquires request-scoped resources uses `yield` and guaranteed cleanup.
- Dependencies **MUST NOT** hide unrelated business work or perform authorization through
  surprising import side effects.
- Avoid service-locator patterns where application code reaches into `request.app.state`.
  Resolve dependencies at the HTTP boundary and pass them inward.
- Tests override owned providers through `app.dependency_overrides` or the application factory,
  and always clear overrides during cleanup.
- Dependency graphs must remain acyclic and should fail at startup when required resources or
  configuration are invalid.

## 6. Async handlers, blocking work, and cancellation

- Use `async def` for handlers backed by awaitable libraries. Use a normal `def` handler when an
  unavoidable blocking library must run in FastAPI's worker-thread path.
- Never call blocking boto3, model inference, filesystem, requests, database, or subprocess APIs
  directly from an async handler.
- A thread offload is bounded and used for blocking I/O, not as an unlimited substitute for an
  async client. CPU-heavy model/parsing work moves to a process pool, durable worker, or separate
  service.
- Fan-out uses `TaskGroup` or another structured, bounded construct. Request-controlled input
  cannot create unbounded tasks.
- Propagate request cancellation and deadlines into HTTP/database/cache operations where the
  client supports it. Catch cancellation only for bounded cleanup, then re-raise.
- A handler timeout and its downstream timeouts form one budget. Downstream calls must expire
  before the platform/proxy deadline, leaving time to map and flush a safe response.
- Avoid `asyncio.run`, nested event-loop manipulation, and synchronous wrappers that sometimes
  return a task and sometimes a value.
- Fire-and-forget task creation from a handler is prohibited. Request completion cannot orphan
  unobserved business work.

## 7. Reva authorization, identity, and tenant context

- When application-layer PEP enforcement owns a protected endpoint, it **MUST** use the approved
  `reva_utility` `@restrict` integration. A verified Kong or Istio/Envoy PEP may own the route
  only when that ownership is documented and covered by route-to-policy inventory tests. Do not
  implement local role checks or direct handler-owned PDP calls.
- Each operation declares the Cedar resource type, action, and safe mapping of validated
  resource attributes required for object/property authorization.
- Authorization runs for each protected object operation and fails closed for denial, timeout,
  malformed response, or unavailable PDP.
- Missing or ambiguous resource identifiers are rejected; never authorize using a parameter
  name or fallback string as the resource ID.
- Tenant/domain/username context becomes trusted only after the approved ingress/mesh identity
  boundary. Client-supplied internal headers are removed or ignored.
- A raw `username == "system-user"` comparison is not workload authentication and **MUST NOT**
  bypass authorization.
- `allow_system_user`, disabled restriction flags, and localhost PDP defaults are permitted only
  in isolated local/test profiles and deployed startup must reject them.
- The handler receives an authorized request context. It does not decode tokens, re-check UI
  roles, or reconstruct identity independently.
- Agent/tool calls preserve trusted context, use the normal PDP path, and invoke IBAC between
  hops where required.
- Tests cover allow, deny, PDP unavailable/timeout/malformed, wrong tenant, missing tenant and
  resource ID, property projection, and system/service identity.

The current shared restriction aspect is required architecture but not a flawless reference.
Its timeout, lifecycle, sensitive logging, trace propagation, and system-user behavior are
migration debt to fix in `reva_utility`; services **MUST NOT** copy that implementation locally.

## 8. Middleware, request state, CORS, and proxy trust

- Middleware is limited to transport-wide concerns such as trusted request context, correlation,
  safe access logging, metrics, and security headers.
- Middleware order is documented: trace extraction, trusted identity/context establishment,
  limits, authorization integration, handler execution, response telemetry, and safe cleanup.
- Request context uses a typed immutable object. Every ContextVar token is reset in `finally`,
  including exception, cancellation, and streaming paths.
- Middleware does not read and buffer an arbitrary request or response body for logging.
- CORS uses an explicit environment-backed allow-list. Wildcard origins with credentialed
  traffic, reflecting arbitrary origins, and `allow_methods=["*"]`/`allow_headers=["*"]` without
  a reviewed need are prohibited.
- `TrustedHostMiddleware` or an equivalent trusted-edge control validates allowed hosts where
  the service is exposed to untrusted Host headers.
- Forwarded client/protocol headers are trusted only from the exact Istio/ingress proxy topology.
  Do not enable permissive proxy-header trust.
- TLS verification is mandatory for outbound calls. Application HTTPS redirect/HSTS behavior is
  enabled only when the application owns that hop or trusted proxy configuration accurately
  represents edge TLS; do not fight the Istio/gateway termination model.
- Body, header, multipart, decompression, pagination, and response limits are set at the gateway,
  ASGI server, and application boundary as appropriate.

## 9. Error handling and compatibility

One platform-level exception mapping registers handlers for:

- Pydantic/FastAPI request validation;
- authentication failure and authorization denial;
- domain not-found, conflict, and invariant errors;
- body and rate limits;
- dependency timeout/unavailability;
- cancellation where a response is still possible; and
- unknown faults.

Rules:

- New services and new API major versions return the company RFC 9457
  `application/problem+json` contract.
- Existing published versions that use `{key,message,data}` retain it consistently until a
  coordinated versioned migration. Do not mix the legacy and target formats within one version.
- Malformed request syntax normally maps to 400. A structurally valid entity that violates
  declared semantic constraints may map to 422 when the API contract adopts that distinction.
  Existing clients retain their published status behavior until versioned migration.
- Validation problems expose safe field locations and machine codes, not raw Pydantic internals,
  Python representations, or model schemas.
- Authentication failure is 401 with the correct challenge behavior; authorization denial is
  403. Cross-tenant responses do not reveal whether another tenant's object exists.
- Unknown failures return a generic 500. Raw `str(error)`, stack traces, SQL, upstream bodies,
  hostnames, policy/model payloads, and credentials never reach a client.
- `BadRequestError` cannot map to 500. Exception names, machine codes, status codes, and OpenAPI
  schemas are covered by contract tests.
- Expected client outcomes are not all error-level logs. An unknown 5xx is logged once with the
  original exception and active trace context.

## 10. Outbound clients, persistence, and caching

- Create one configured `httpx.AsyncClient` or approved aiohttp client per dependency/security
  profile during lifespan and reuse its connection pool.
- Clients use a trusted base URL, TLS verification, explicit connect/read/write/pool/total
  deadlines, bounded response sizes, and cancellation.
- Forward only allow-listed trusted Reva identity/context and W3C trace headers. Never forward
  arbitrary inbound headers, cookies, or credentials.
- Retry transient, safe/idempotent calls only with bounded attempts, exponential backoff,
  jitter, and the caller's deadline budget.
- Validate remote responses before use and translate vendor exceptions at the adapter boundary.
  Do not log or return raw upstream bodies.
- Dynamic destination URLs receive SSRF validation. Query parameters use client APIs, not string
  interpolation.
- Database work uses request-appropriate transactions, parameterized queries, bounded pools, and
  explicit tenant scoping. Blocking drivers do not run on the event loop.
- Every cache key includes tenant, schema/version, resource type, and identifier as applicable.
  Do not cache authorization-sensitive data under a tenantless key.
- Cache failures have an explicit correctness policy. Fail-open caching may affect performance,
  never authorization or tenant isolation.
- Distributed locks are selected from a documented failure model and include fencing,
  idempotency, lease-expiry, and retry semantics where correctness depends on them. No single
  named lock algorithm is a universal baseline.

## 11. Background work, messaging, and streaming

- FastAPI `BackgroundTasks` is limited to short, non-critical, idempotent post-response work
  whose loss on process termination is acceptable and documented.
- Work that must survive restart, retry, coordinate, or produce an audit trail uses Kafka,
  Temporal, or another approved durable mechanism.
- Durable messages include tenant scope, stable operation/idempotency ID, schema version, and
  W3C trace context. Consumers enforce idempotency and bounded retry/DLQ behavior.
- Background workers do not inherit stale request ContextVars. They reconstruct trusted context
  from the durable message contract.
- SSE/streaming routes define content type, heartbeat policy, maximum duration/message size,
  bounded buffering, backpressure, disconnect detection, cancellation, and upstream cleanup.
- After streaming headers are committed, failures use a documented safe stream event/trailer
  protocol; the handler cannot pretend to change the HTTP status.
- WebSocket use requires an explicit authentication/reauthorization, tenant, limit, shutdown,
  and observability design.

## 12. Logging, metrics, and OpenTelemetry

### 12.1 Logging and metrics

- Use loguru through the approved `reva_utility` JSON configuration. Request logs bind trace ID,
  span ID, correlation ID, safe tenant ID, route template, status/outcome, and duration.
- Do not log request/response bodies, full headers, authorization payloads, prompts, policy
  bodies, model responses, connection URLs, or upstream error bodies.
- Emit HTTP RED metrics by route template/status class plus event-loop, queue/executor, pool,
  dependency, authorization, model/tool, and domain SLO metrics.
- Health endpoints may be omitted from routine access spans/metrics only through a consistent
  central policy; their readiness state remains observable.

### 12.2 FastAPI tracing

- Initialize the OpenTelemetry Python SDK/provider once during process composition before
  creating instrumented clients or serving requests.
- Instrument the application with the supported FastAPI/ASGI instrumentation and instrument
  only the outbound libraries in use. Ensure overlapping ASGI/HTTP instrumentation does not
  create duplicate server/client spans.
- Use W3C `traceparent`/`tracestate` extraction and injection. `X-Correlation-Id` remains a
  separate bounded support identifier.
- Server span names use the resolved route template/operation, never the raw path.
- Outbound PDP, IBAC, Bedrock/tool, HTTP, database, Redis, Kafka, and Temporal operations produce
  child/producer spans under the active context.
- Manual spans capture meaningful BFF/agent/domain operations without recording tokens, PII,
  tenant secrets, request/response bodies, prompts, policy content, SQL, or full URLs.
- Authorization denial and validation use result attributes/events rather than automatically
  marking the server span as an internal error. Unexpected failures record an exception/error
  once.
- Use a batch processor and OTLP exporter to the in-cluster collector. Export is bounded and
  non-blocking; drop/export-failure metrics remain visible.
- Lifespan cleanup flushes and shuts down the telemetry provider after request/resource draining
  and before the process exits.
- Integration tests verify one continuous trace and log correlation across FastAPI → PEP/PDP
  and, for agents, IBAC/Bedrock/tool hops, including redaction assertions.

## 13. Health, startup, Uvicorn, and Kubernetes

Every service retains:

- `/health` for the Reva compatibility contract;
- liveness behavior that proves the process/event loop can make progress without remote
  dependency fan-out;
- readiness behavior that becomes true only after route/resource initialization and checks only
  dependencies required to serve; and
- startup-probe behavior for slow model loading, migrations, or cache warm-up.

- `/health` **MUST** implement the Reva readiness compatibility contract: return 200 only
  after the application is ready and return a non-success status while starting, draining, or
  otherwise unable to serve. A permanently successful response is prohibited. A separate
  liveness endpoint **MAY** remain dependency-independent.
- Health responses contain status/component categories, not dependency URLs, exception text,
  credentials, model paths, or topology details.
- Readiness turns false before normal shutdown begins.
- Kubernetes normally runs one Uvicorn process per container and scales with replicas/HPA. More
  in-container workers require measured CPU/memory and graceful-drain justification.
- Use exec-form startup, bind the configured host/port, disable reload, and configure finite
  keep-alive/concurrency/request limits appropriate to the service.
- `uvicorn.workers.UvicornWorker` is deprecated and prohibited in new deployment configuration.
  If an approved service still requires Gunicorn, it uses the maintained `uvicorn-worker`
  package and a tracked migration; Kubernetes-native Uvicorn remains the default.
- Proxy headers and forwarded IP/protocol are enabled only for exact trusted proxy CIDRs/hops.
- On SIGTERM:

  1. mark readiness false;
  2. stop accepting new work;
  3. drain bounded in-flight requests and streams;
  4. cancel overdue tasks and consumers;
  5. close HTTP/database/cache/broker/model resources;
  6. flush telemetry; and
  7. exit within Reva's 30-second termination contract.

- Test shutdown with keep-alive, a slow request, a streaming request, and an active background
  consumer where applicable.
- Helm uses a startup probe where needed, separate readiness/liveness probes, measured
  requests/limits, an appropriate disruption budget/HPA, and a termination grace period longer
  than the application's internal drain deadline.

## 14. Testing and coverage

### 14.1 Application and route tests

- Build a new app through `create_app()` for each isolated suite/test scope; do not import a
  process-global application with accumulated state.
- Synchronous route tests MAY use `TestClient`. Async tests use AnyIO's pytest plugin
  (`@pytest.mark.anyio`) with `httpx.AsyncClient` and `ASGITransport`.
- `ASGITransport` does not automatically run application lifespan. Async tests that exercise
  startup resources use an approved lifespan manager explicitly.
- Override dependencies at owned provider/factory boundaries and clear
  `app.dependency_overrides` after the test.
- Assert status, media type, headers, and full contract-relevant response—not only status.
- Request-schema tests cover unknown fields, wrong types/formats, bounds, missing/null behavior,
  oversized values, malformed JSON, and coercion-sensitive security values.
- Response tests verify allow-list projection and failure when an implementation violates its
  response model.
- OpenAPI tests verify operation IDs, route uniqueness, security declarations, error schemas,
  and backwards compatibility.

### 14.2 Required suites

- unit tests for application/domain behavior, schema mappers, and error translation;
- route/component tests with controlled dependencies;
- real-protocol integration tests for database/cache/broker/client behavior where relevant;
- consumer/provider contract tests;
- authorization, system identity, property access, and cross-tenant negative matrices;
- timeout, cancellation, client disconnect, retry, partial failure, and saturation tests;
- ContextVar isolation/reset tests across concurrent requests;
- logging/tracing propagation and sensitive-data redaction tests;
- lifespan partial-startup and cleanup tests;
- streaming/background/durable-work tests where used; and
- graceful shutdown and connection-drain tests.

Coverage follows the Python/root baseline. Security-sensitive decorators, middleware, context
handling, schema mapping, and central exception handlers test every documented branch. A numeric
coverage average cannot waive missing deny, cross-tenant, or malformed-PDP cases.

## 15. Performance engineering

- Benchmark the production Uvicorn configuration with production validation, authorization,
  Loguru JSON, metrics, and representative trace sampling enabled.
- Generate load externally with Locust, k6, or an approved equivalent. Include realistic
  keep-alive, payload, tenant, authorization, downstream latency, streaming, and model/tool
  distributions.
- Measure p50/p95/p99, throughput, error/timeout rate, CPU/RSS/GC, event-loop delay, executor and
  connection-pool saturation, active requests/tasks, dependency load, and telemetry overhead.
- Test cold model/client initialization, readiness transition, degraded PDP/dependency behavior,
  aggregation fan-out, cache miss/stampede behavior, and SIGTERM under load.
- Blocking code detection and event-loop-delay checks SHOULD be part of performance/resilience
  tests for async services.
- Do not remove response validation, authorization, tenant isolation, logging, or tracing to win
  a benchmark.
- Record revision, environment, workload, SLO, breakpoint, accepted safe envelope, and the
  Kubernetes/pool/concurrency settings derived from the result.

## 16. Security checklist

- [ ] Every protected operation uses the approved Reva restriction path and fails closed.
- [ ] Tenant and resource IDs come from validated/trusted context and are present in every data path.
- [ ] Request, response, remote-response, pagination, upload, and decompression sizes are bounded.
- [ ] CORS origins, hosts, proxies, and outbound destinations are allow-listed.
- [ ] TLS verification is enabled; no local/deployed option can set it false.
- [ ] Error responses and logs contain no stack, raw dependency body, policy, prompt, token, or secret.
- [ ] Pydantic response models prevent over-posting and over-sharing.
- [ ] Background and streaming work has cancellation, idempotency, and shutdown behavior.
- [ ] Dependencies, SAST, secrets, image, and OpenAPI contracts pass their merge gates.

## 17. Current Reva migration debt — not approved examples

The following observed patterns must not be treated as framework standards:

- representative services define a process-global FastAPI instance rather than a testable
  application factory;
- wildcard CORS is common, including configurations combined with credentials;
- some applications expose a hard-coded success health endpoint while calling it readiness;
- some routes omit response models, return raw exception details, or use broad `Any` schemas;
- some services create a new `httpx.AsyncClient` per operation instead of a lifespan-owned pool;
- some middleware sets a ContextVar without token reset;
- some route paths log complete headers, bodies, queries, policy payloads, prompts, or model
  responses;
- representative OpenTelemetry code creates local providers/exporters without completing global
  lifecycle wiring and captures sensitive inputs/outputs;
- current Gunicorn entrypoints use deprecated `uvicorn.workers.UvicornWorker`;
- current containers and Helm charts do not consistently enforce non-root execution, service
  account/IRSA wiring, startup probes, or secret-safe configuration; and
- central Python CI currently comments out or skips real unit/coverage commands.

These are remediation inputs. New services start compliant, and shared defects are corrected
centrally rather than copied into another application.

## 18. Knowledge and Definition of Done

FastAPI owners are expected to understand:

- ASGI lifecycle, lifespan, middleware order, dependency scopes, and exception handling;
- Pydantic v2 validation/coercion, input/output separation, and OpenAPI generation;
- async versus thread-worker execution, TaskGroup, cancellation, client pooling, and streaming;
- Reva PEP/PDP/IBAC, trusted tenant context, and property-level authorization;
- Loguru request context, FastAPI/ASGI OpenTelemetry instrumentation, W3C propagation, and
  sensitive-data controls;
- Uvicorn connection/process behavior, Kubernetes probes, SIGTERM draining, and Istio proxy
  trust; and
- route, contract, concurrency, lifecycle, security, and production-load testing.

Before merge:

- [ ] App construction, process startup, and lifespan cleanup are separate and testable.
- [ ] Feature routers are thin and framework types do not enter application/domain code.
- [ ] Every route has bounded Pydantic input and allow-listed response schemas plus OpenAPI metadata.
- [ ] Dependencies are typed, scoped, overridable, and do not create per-request pools.
- [ ] Reva authorization and tenant-negative cases pass, including PDP failure and system identity.
- [ ] Error compatibility and RFC 9457 behavior match the API version.
- [ ] CORS, proxy trust, TLS, sizes, deadlines, and streaming/background behavior are secure.
- [ ] Loguru, metrics, W3C propagation, OTLP export, redaction, and telemetry shutdown are verified.
- [ ] Test suites and coverage satisfy Python and company gates.
- [ ] `/health`, readiness/liveness/startup, Uvicorn, SIGTERM, IRSA, and Helm behavior are tested.
- [ ] Production load remains within the accepted SLO and resource envelope.

## 19. Primary references

- [FastAPI async guidance](https://fastapi.tiangolo.com/async/)
- [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/)
- [FastAPI larger applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [FastAPI dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI response models](https://fastapi.tiangolo.com/tutorial/response-model/)
- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [FastAPI async tests](https://fastapi.tiangolo.com/advanced/async-tests/)
- [FastAPI container deployment](https://fastapi.tiangolo.com/deployment/docker/)
- [FastAPI version pinning](https://fastapi.tiangolo.com/deployment/versions/)
- [Uvicorn deployment](https://www.uvicorn.org/deployment/)
- [Uvicorn settings](https://www.uvicorn.org/settings/)
- [Uvicorn server behavior](https://www.uvicorn.org/server-behavior/)
- [OpenTelemetry FastAPI instrumentation](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html)

Reva implementation references:

- `CLAUDE.md`
- `AGENTS.md`
- `.cursor/rules/12-python-services.mdc`
- `.cursor/rules/41-observability.mdc`
- `development/shared-library-python`
- `development/ibac-service/intent-service`
- `development/kong-control-service`
- `development/intelligence-services`
- `devops/dockerfiles/python`
- `devops/helm-reva-python-app`
