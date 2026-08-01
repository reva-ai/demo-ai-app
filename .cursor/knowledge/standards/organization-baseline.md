<!--
GENERATED REVA STANDARD SNAPSHOT — DO NOT EDIT IN THIS REPOSITORY
Source: KarthikRamesh/reva-standards/baseline.md
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

# Reva Engineering Baseline

| Field | Value |
|---|---|
| Status | Normative company baseline |
| Applies to | Reva backend services, web applications, jobs, workers, shared libraries, CI/CD definitions, infrastructure definitions, deployment charts, and automated test systems |
| Audience | Engineers, reviewers, platform engineers, security engineers, and coding agents |
| Review trigger | At least annually and on a supported runtime, security model, or platform-contract change |

This document defines the minimum engineering standard shared by Reva software and the
infrastructure, delivery, and automated-test assets that prove and operate it. Language,
framework, data, infrastructure, delivery, and testing baselines refine it; they do not
replace it.
Service-runtime requirements apply directly to services. A non-runtime profile applies the
security, supply-chain, delivery, observability, evidence, change-control, and Reva
architecture requirements relevant to that artifact and defines the technology-specific
mechanism in its own baseline.

## 1. Requirements language and precedence

**MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** have the meanings defined in
RFC 2119 and RFC 8174.

Requirements apply in this order:

1. legal, contractual, data-residency, and security obligations;
2. this company baseline;
3. the applicable language, infrastructure, delivery, or testing baseline;
4. the applicable framework or data-technology baseline; and
5. an approved, narrowly scoped ADR.

Where two rules conflict, use the stricter safe rule and escalate the conflict. Never resolve
an ambiguity by weakening authorization, tenant isolation, secret handling, auditability, or
data protection.

## 2. Reva architecture invariants

These rules are non-negotiable across languages.

### 2.1 Authorization and identity

- A protected operation **MUST** be authorized by the Reva PDP through an approved PEP:
  `pep-sdk`, the language shared-library integration, Kong, or the Istio/Envoy enforcement
  path.
- Services **MUST NOT** implement a parallel authorization system, hand-written role checks,
  or policy decisions from unverified JWT claims.
- When application-layer PEP enforcement owns a route, Go handlers **MUST** use the
  appropriate `RestrictV2Gin`, `RestrictV2Chi`, `RestrictV2Mux`, or `RestrictV2HTTP`
  integration; Python handlers **MUST** use `@restrict`; and Java/Node services **MUST** use
  the approved PEP SDK/shared integration. A route enforced by a verified Kong or
  Istio/Envoy PEP instead **MUST** document that ownership and pass route-to-policy inventory
  tests.
- Authentication establishes identity; authorization establishes permission. A valid token is
  never sufficient evidence that an action is allowed.
- A deny, timeout, malformed response, or unavailable PDP **MUST fail closed** for a protected
  operation. An intentionally public operation is explicitly classified and inventoried; it
  is not implemented as a PDP-failure fallback.
- Resource identifiers and attributes sent to the PDP **MUST** be structurally validated and
  canonical before authorization. The application **MUST** consume the same canonical values;
  different PEP/handler parsers or normalizations that could authorize one object and operate
  on another are prohibited.
- Authorization-disable flags, default identities, and magic “system user” bypasses are
  permitted only in isolated local/test profiles. Deployed configuration **MUST** reject them
  at startup and CI/policy checks **MUST** prevent their release.
- AI agent and tool hops **MUST** receive normal PDP evaluation. Flows subject to Intent-Based
  Access Control **MUST** call the IBAC judge between hops and enforce its result.

### 2.2 Tenant isolation and request context

- Every tenant-scoped request **MUST** have one authoritative tenant identity derived from a
  trusted, authenticated boundary. Client-controlled `Origin`, host, query, body, or arbitrary
  internal header values **MUST NOT** be treated as authoritative identity.
- External ingress **MUST** remove client-supplied internal identity headers before trusted
  values are injected.
- Reva inter-service calls **MUST** propagate the established `domain` and `username` context
  and the W3C trace context.
- Tenant context **MUST** use request-local async/context mechanisms. It **MUST NOT** be kept in
  process-global mutable state or thread-local state that is unsafe for the language's async
  model.
- Every tenant-scoped read, write, cache key, event, and background job **MUST** preserve tenant
  isolation. Repository APIs SHOULD make a missing tenant context impossible or fail closed.
- Each tenant-scoped data path **MUST** have automated negative tests proving tenant A cannot
  read, update, delete, or infer tenant B's data.
- A hybrid/data-residency tenant **MUST NOT** silently fall back to shared storage. Missing or
  invalid routing state is a service-unavailable condition.

### 2.3 Shared libraries and platform contracts

- Java services **MUST** inherit the Reva parent and use `shared-library-java`.
- Go services **MUST** use the canonical module
  `gitlab.com/reva.ai/development/shared-library-golang`. Older
  `gitlab.com/reva-ai/...`/`github.com/reva-ai/...` imports are migration debt and **MUST NOT**
  be copied into new code.
- Python services **MUST** use the `reva_utility` package.
- Teams **MUST NOT** duplicate authorization, encryption, request-context, standard error, ID,
  or telemetry helpers already supplied by a supported Reva library.
- A defect in a shared cross-cutting concern SHOULD be fixed in the shared library and then
  rolled out, rather than patched differently in each service.
- “Provided by the shared library” is not a security exemption. Shared code **MUST** meet the
  same body/header limits, timeout, redaction, trace, fail-closed, and test requirements, and
  consuming services **MUST** move to the approved remediated version.

### 2.4 Browser, server-rendering, and API boundaries

- Browser code, UI route guards, middleware/proxy checks, hidden controls, and session presence
  improve user experience or defense in depth; they **MUST NOT** be the authoritative
  authorization decision for a protected operation.
- A web application **MUST** call the approved Reva BFF or service contract for product data
  and protected mutations. Direct access from a frontend application to a product database or
  a parallel application-local policy system requires an approved architecture and security
  ADR.
- Server-rendered and cached output **MUST** preserve tenant and identity isolation. A cache
  entry, tag, revalidation path, prefetch, or rendered artifact must not allow one tenant's or
  user's protected data to be reused for another.
- Server-only modules, secrets, internal service credentials, and privileged SDKs **MUST NOT**
  cross the browser bundle boundary. Public/browser configuration is non-secret by definition.
- Every protected server action, route handler, and backend-for-frontend request is an
  externally reachable server boundary and **MUST** validate input, authenticate, authorize
  through the approved Reva path, enforce resource limits, and emit safe telemetry.

## 3. Verified platform profile and target state

The service's Reva parent, shared library, CI template, and standard image describe the
verified current compatibility profile. They do not make an end-of-life component acceptable.
Current state and target posture are:

| Stack | Reva baseline |
|---|---|
| Java | Current: Java 21/Spring Boot 3.2.2; target: one centrally managed, vendor-supported Spring Boot line while preserving WebFlux/R2DBC |
| Go | Go 1.26.x organization target; Gin/Chi supported, gorilla/mux supported for existing services |
| Python | Python 3.13; FastAPI; `reva_utility`; loguru |
| Node.js | Node.js 24; TypeScript; Fastify 5; pino |
| Next.js | Target Next.js 16.2.11, React 19.2, TypeScript 5.9+, and Node.js 24; current Reva applications span older/unpinned lines and require an incremental centrally owned migration |
| OpenTofu | Verified current pipelines span 1.9.0 and 1.10.2; target 1.12.x with module/live-root separation and encrypted, segmented remote state |
| Helm | Verified current Helm 3 charts require a values-schema migration; target is deterministic rendering and schema-validated values, with Helm 4 only through a coordinated migration |
| Katalon | Verified current project 11.0.1; target 11.4-compatible Studio/KRE with thin Katalon adapters over a Gradle-tested JVM core |
| GitLab | Current Reva delivery uses central project includes with migration debt around mutable references and legacy privileged build patterns; target is governed versioned components, policy-enforced gates, workload identity, and immutable promotion evidence |
| Telemetry | Micrometer + Brave for Java; OpenTelemetry for Go, Python, and Node |
| Runtime | OCI container on EKS, Istio sidecar, Prometheus/New Relic/Grafana telemetry |

An upstream release does not change this table automatically. A runtime or framework upgrade
**MUST**:

- have a named owner and compatibility matrix;
- pass unit, integration, contract, security, performance, rollout, and rollback validation;
- verify Reva shared-library compatibility;
- update CI and standard container images;
- check Istio, Helm, health, shutdown, and telemetry behavior; and
- use an ADR for a major version or architecture-model change.

Unsupported or end-of-life dependencies **MUST** have an approved migration plan and
time-bounded risk acceptance.

Spring Boot 3.2.x has ended open-source support. Reva's current 3.2.2 parent therefore requires
a priority central upgrade. Until that program lands, services inherit the parent for binary
compatibility and **MUST NOT** create a different private Spring version stack through
per-service overrides. The central upgrade must align the Spring Boot BOM, Spring Framework,
Actuator, Security, Data, Reactor, shared libraries, templates, tests, and runtime images.

## 4. Repository and service contract

Every deployable application or backend service **MUST** provide all applicable items below.

### 4.1 Required repository artifacts

- A root `.gitlab-ci.yml` including the approved language template from
  `devops/core-devops-pipeline`.
- Pipeline variables `SERVICE_NAME`, `PORT_NUMBER`, and
  `SERVICE_CONTAINER_REGISTRY_NAME` with registry names verified in the platform mapping
  repository.
- A standard language Dockerfile or an inline Dockerfile conforming to the same contract.
- Per-environment Helm values in `devops/helm-values-repository` when the service is deployed.
- An OpenAPI contract for HTTP APIs.
- A README with purpose, local run, test, configuration, dependency, and deployment guidance.
- An ownership mechanism such as `CODEOWNERS` or an equivalent documented owner.

The four deployability artifacts—CI, container build, Helm values, and health/shutdown
behavior—are one contract. A new service is incomplete if any one is missing.

### 4.2 Naming

| Item | Standard |
|---|---|
| Repository and logical service name | lowercase kebab-case |
| Container registry short name | lowercase, no hyphens; use the mapping repository |
| Kubernetes/Helm name | DNS-compatible lowercase kebab-case |
| Environment configuration key | uppercase snake case only at process boundaries |
| Secret name | describes purpose, never includes a secret value |
| HTTP path | lowercase nouns with hyphens; no verbs unless modeling an operation |
| JSON field | lower camel case unless an established public contract says otherwise |
| Database identifier | lowercase snake case, unquoted where supported |
| Event/topic | documented company convention including domain and version |

Language baselines define source-file, package, type, function, and variable naming.

Names **MUST** describe domain intent. Avoid generic containers such as `data`, `info`,
`manager`, `helper`, `util`, `temp`, or `obj` unless the concept is genuinely generic and
bounded. Boolean names SHOULD read as predicates (`isReady`, `hasAccess`, `canRetry`).
Units belong in names when the type does not encode them (`timeoutMs`, `sizeBytes`).

### 4.3 Repository boundaries

The Reva workspace contains independent repositories. A cross-repository change **MUST**:

- identify every affected repository before editing;
- use one commit per repository with a shared ticket/slug;
- release producers before consumers and deployment pins last;
- avoid updating Helm image tags before CI has built the image; and
- never push directly to `main` or modify production/release history without approval.

## 5. Code and design practices

### 5.1 Dependency direction

Services SHOULD use a pragmatic ports-and-adapters structure:

```text
transport -> application/use cases -> domain
                         ^             |
                         |             v
                    outbound ports <- adapters
```

- Domain and application code **MUST NOT** depend on web-framework request/context types,
  database clients, cloud SDKs, or telemetry exporters.
- Handlers/controllers adapt transport DTOs to application inputs. They do not contain
  business rules.
- Persistence and remote-client implementations sit behind narrow interfaces owned by the
  application/domain side.
- Dependencies **MUST** be injected explicitly through constructors/factories or the language's
  approved compile-time/static mechanism. Hidden service locators and mutable globals are
  prohibited.
- A service MAY use a simpler layered structure when its size does not justify more ceremony,
  but the dependency direction and transport isolation still apply.

### 5.2 Modularity and change size

- Modules and packages **MUST** have one coherent responsibility and an explicit public
  surface.
- Cyclic dependencies are prohibited.
- Export/public only what another module needs.
- Prefer small, reviewable changes. Large generated or mechanical changes should be separated
  from behavioral changes.
- Comments explain constraints and rationale, not syntax. Ticket numbers belong in history,
  not permanent code comments.
- Feature flags are temporary release controls, not permanent forks. Every flag needs an
  owner, expiry/removal condition, and safe default.

### 5.3 Async and concurrency

- Blocking I/O **MUST NOT** run on event-loop/reactive threads.
- Every asynchronous operation **MUST** propagate cancellation, deadlines, trace context, and
  tenant context.
- Concurrency **MUST** be bounded. Unbounded goroutines, tasks, promises, reactive `flatMap`,
  worker queues, or fan-out are prohibited.
- Background work that must survive a request **MUST** use a durable queue/workflow. In-process
  “fire and forget” is permitted only for explicitly best-effort, loss-tolerant work.
- Shared mutable state needs a documented synchronization/ownership model and race tests where
  the language supports them.
- Do not retry or continue an operation after its request context is cancelled unless the
  business operation is deliberately detached and durable.

### 5.4 IDs, time, and money

- Use Reva's approved ID helper: `NanoIdUtil` for Java, `nanoid` for Python where established,
  and standard UUIDs for Go unless the domain contract specifies otherwise.
- Do not invent ID or cryptographic randomness algorithms.
- Store instants in UTC and include timezone/offset in external representations. Inject a
  clock in time-dependent domain logic.
- Use decimal/fixed-precision representations for money. Binary floating point is prohibited
  for monetary values.
- Units and precision **MUST** be explicit in API and persistence contracts.

## 6. HTTP and API standards

### 6.1 Contract-first behavior

- Every HTTP endpoint **MUST** be represented in an OpenAPI document and validated in CI.
- Request and response DTOs **MUST** be separate from persistence/domain entities.
- Unknown, immutable, server-managed, and sensitive fields **MUST NOT** be mass-assigned.
- Input validation occurs at the boundary, while domain invariants remain enforced in the
  domain/application layer.
- API compatibility follows semantic versioning of the contract. Breaking changes require a
  new version or an explicitly managed migration.
- Services SHOULD generate clients/server interfaces where supported to prevent contract drift.

### 6.2 Resource and method semantics

- Use HTTP methods according to RFC semantics: GET/HEAD are safe; PUT/DELETE are idempotent;
  POST is not assumed idempotent.
- Do not mutate state from GET.
- Return the most specific standard status code; do not return `200` with an error payload.
- Long-running operations SHOULD return an operation resource or use an asynchronous workflow.
- Collection endpoints **MUST** use bounded pagination. Unbounded list/export endpoints are
  prohibited.
- Filtering and sorting fields **MUST** be allow-listed; raw client-provided column/expression
  interpolation is prohibited.
- Create/update endpoints with retry risk SHOULD support a tenant-scoped idempotency key and
  define retention, conflict, and replay semantics.

### 6.3 Error contract

New services and new API major versions **MUST** use RFC 9457
`application/problem+json`. An existing published API version **MUST** retain its documented
Reva error envelope until a coordinated, versioned migration; do not mix two error formats
inside one API version. The target problem contract normally includes:

| Field | Requirement |
|---|---|
| `type` | Stable URI identifying the problem class |
| `title` | Stable human-readable summary |
| `status` | Same status as the HTTP response |
| `detail` | Safe, occurrence-specific guidance; never internal debugging data |
| `instance` | Opaque occurrence identifier or URI |
| `correlationId` | Reva extension allowing support correlation |
| `errors` | Optional structured field violations for validation failures |

Problem responses **MUST NOT** expose stack traces, SQL, internal hostnames, secret/config
values, token contents, policy documents, or dependency implementation details. Clients
**MUST NOT** parse human-readable `detail`; machine decisions use type/status/extensions.

### 6.4 Outbound clients

- Use the language's approved shared HTTP client wrapper when available.
- Clients **MUST** set connect, request, response, and total deadlines appropriate to the
  caller's remaining budget.
- Connection pools/clients are long-lived and reused; creating one per request is prohibited.
- Propagate trace, tenant, and caller identity context only to trusted destinations.
- Validate TLS and destination allow-lists. Dynamic outbound URLs require SSRF controls.
- Treat remote responses as untrusted input and validate their size, status, schema, and
  content type.

## 7. Security baseline

### 7.1 Secure-by-default rules

- Apply OWASP API Security Top 10 controls during design and review, especially object- and
  property-level authorization, resource-consumption limits, SSRF, inventory, and unsafe
  third-party API consumption.
- Public inputs are untrusted regardless of validation performed by an upstream proxy.
- Bind values through driver/query APIs. Concatenating untrusted values into SQL, MongoDB
  operators, shell commands, templates, log formats, paths, or URLs is prohibited.
- Set explicit request-header, body, upload, decompression, nesting, pagination, and
  concurrency limits.
- CORS uses an explicit allow-list. Wildcard origins with credentials are prohibited.
- Webhooks use signature verification over the raw body, timestamp tolerance, and replay
  protection. A static API key alone is insufficient.
- Sensitive operations require audit events independent of sampled telemetry.

### 7.2 Secrets and AWS access

- Secrets come from AWS Secrets Manager through IRSA/EKS Pod Identity and Kubernetes secret
  references.
- Real plaintext secrets in source, images, Helm values, logs, test fixtures, example files,
  and general configuration are prohibited. Tests use obviously synthetic values or generate
  ephemeral credentials at runtime.
- Long-lived AWS access keys in workload environment variables are prohibited.
- Each AWS-using service receives a dedicated least-privilege IAM role; roles are not shared
  across unrelated services.
- Secret values use redacting/secret types where the ecosystem supports them and are never
  rendered through default object stringification.
- Rotation and revocation behavior **MUST** be designed and tested, not only documented.

### 7.3 Encryption and sensitive data

- Use the approved Reva encryption utility and managed KMS keys. Custom cryptography is
  prohibited.
- Service-to-service traffic uses Istio mTLS; do not add plaintext bypass routes.
- PII and credentials **MUST NOT** be stored in Cedar attributes or telemetry.
- Data classification determines encryption, access, retention, backup, and deletion controls.
- Logs, traces, metrics, crash reports, test snapshots, and DLQs are data stores and receive
  the same classification review as primary databases.

### 7.4 Dependency and supply-chain security

- Pin direct dependencies and commit the ecosystem lock/checksum file.
- CI **MUST** run the approved SAST, secret, dependency vulnerability, license/policy, and
  container image scans.
- Critical/high findings are fixed before release unless security approves a time-bound risk
  exception with compensating controls.
- Base images use the Reva standard, a non-root runtime user, a minimal final stage, and no
  package manager/build credentials in the final image.
- Build outputs are reproducible where practical and identify source revision and version.
- Generated SBOMs and signed provenance SHOULD be added as the central pipeline supports them.

## 8. Configuration

- Configuration is typed, validated at startup, and fails fast for missing/invalid required
  values.
- Defaults are safe for local development and **MUST NOT** silently enable insecure production
  behavior.
- Configuration precedence and ownership must be documented. Avoid reading configuration
  directly throughout business code; inject a typed configuration object.
- Environment variables are process-boundary configuration, not a secret store.
- Runtime configuration changes require schema validation, staged rollout, last-known-good
  behavior, and rollback.
- A missing hybrid/deployment-mode setting is not equivalent to `SHARED`; explicit enums and
  fail-closed behavior are required.
- Feature and kill-switch configuration must be observable without logging its sensitive
  values.

## 9. Logging, metrics, and distributed tracing

Telemetry is a product contract across all Reva languages. It must let operators correlate
one request across edge, mesh, service, asynchronous messaging, and data layers without
leaking customer data.

### 9.1 Structured logging

- Services log structured JSON to stdout/stderr only. File logging in containers is
  prohibited.
- Use SLF4J for Java, zap for Go, loguru through `reva_utility` for Python, and pino/Fastify
  logging for Node.
- `System.out`, `fmt.Println`, `print`, and `console.log` are prohibited for service logging.
- Every request log includes, when available: timestamp, severity, service name/version,
  deployment environment, trace ID, span ID, correlation ID, safe tenant key, operation/route,
  outcome, and duration.
- Log parameterized fields, not string-built JSON.
- Do not log request/response bodies by default. Tokens, cookies, API keys, credentials,
  policy bodies, PII, model prompts/responses, and database connection strings are prohibited.
- Expected client errors use appropriate levels and do not generate duplicate stack traces at
  every layer. Log an exception once at the boundary that owns remediation.
- High-cardinality values belong in logs/traces, not metric labels.

### 9.2 Metrics

Each service **MUST** expose:

- request rate, error count, and duration histograms (RED);
- saturation/queue/pool metrics for constrained resources;
- runtime/process metrics;
- outbound dependency latency/error metrics;
- authorization decision outcome and latency without policy/subject secrets;
- readiness state and build/service version; and
- domain metrics required for SLOs.

Metric names, units, and labels follow Prometheus and OpenTelemetry semantic conventions.
Labels **MUST** have bounded cardinality. Raw paths, user IDs, request IDs, trace IDs, resource
IDs, error messages, and unbounded tenant IDs are prohibited metric labels. Per-tenant SLA
measurement should use an approved bounded mapping or telemetry backend attribute strategy,
not an unbounded Prometheus label.

### 9.3 Distributed tracing contract

All stacks **MUST**:

1. extract and validate incoming W3C `traceparent` and `tracestate`;
2. create a server/consumer span using the extracted parent;
3. keep the active context across async boundaries;
4. create client/producer spans for outbound operations;
5. inject updated W3C context into trusted outbound HTTP, gRPC, Kafka, workflow, and job
   carriers; and
6. record trace and span IDs in structured logs.

Reva uses Micrometer Tracing + Brave for Java and OpenTelemetry SDK/instrumentation for Go,
Python, and Node. Java services **MUST NOT** add a second OpenTelemetry Java SDK that conflicts
with the Reva parent.

`X-Correlation-Id` is a support-facing correlation value, not a replacement for
`traceparent`. The trusted edge validates or generates it with a bounded format; services
propagate it as ordinary request context and still create/propagate standards-compliant trace
context.

Required resource attributes are:

- `service.name`;
- `service.namespace=reva`;
- `service.version`;
- `deployment.environment.name`;
- appropriate Kubernetes resource attributes supplied by the collector/agent; and
- a stable instrumentation library/scope name.

Span names follow stable route/operation templates (`GET /policy-stores/{id}`), never raw URLs,
IDs, SQL text, or error messages. Use official OpenTelemetry HTTP, RPC, database, messaging,
and FaaS semantic conventions.

Add manual spans only for meaningful application operations not already captured by automatic
instrumentation: authorization evaluation, durable workflow steps, external model/tool calls,
and expensive domain computations. Avoid a span per small function.

The Istio `Telemetry` API and application instrumentation **MUST** export to the same
collector/backend. Mesh and application spans must use distinguishable scope/service
attributes and form one trace rather than competing trace trees. At AWS boundaries, capture
available CloudFront/API Gateway/Lambda identifiers such as `x-amz-cf-id`,
`x-amzn-RequestId`, and `x-amzn-Trace-Id` as safe correlation attributes; do not pretend those
vendor IDs are W3C parent span IDs unless a supported integration actually bridges them.

For messaging, a producer injects context into message headers. A consumer extracts it and
creates a consumer/process span; it does not reuse a producer span as the active span. Batched
messages with different parents use links or one processing trace per message according to
the OpenTelemetry messaging conventions.

Span status and errors:

- expected business denial/validation is represented by the correct HTTP/result attributes;
  it is not automatically an internal exception;
- unexpected failures record the exception through the instrumentation API and set error
  status once;
- cancellations and deadline exhaustion are distinguished from internal failures; and
- retry attempts are represented without creating misleading independent root traces.

### 9.4 Tenant and sensitive trace attributes

- The approved safe tenant correlation field is `reva.tenant.id`. It MUST be a stable opaque
  internal identifier, not a tenant name, email, hostname, or secret.
- Add it only after trusted tenant resolution. Never copy an unverified external header into
  telemetry.
- `reva.authorization.decision` MAY record `allow` or `deny`; policy contents, token claims,
  raw subject identifiers, and sensitive resource attributes are prohibited.
- Baggage is not trusted storage. Only allow-listed, non-sensitive fields may enter baggage,
  and baggage **MUST** be removed before calls to third-party/untrusted destinations.
- Collector redaction/filter rules are defense in depth; instrumentation must minimize data at
  source.

### 9.5 Sampling and export

- Sampling is centrally governed. Services respect the upstream parent decision.
- Production head sampling SHOULD be parent-based with a ratio-based root policy. Large
  environments SHOULD use collector tail sampling to retain errors, high-latency traces,
  security-relevant operations, and rollout cohorts.
- Audit/compliance events **MUST NOT** depend on trace sampling.
- Export is batched, bounded, asynchronous, and directed to the in-cluster collector. A
  telemetry backend outage **MUST NOT** block or crash the request path.
- Queue overflow/drop counts and exporter failures **MUST** be observable.

### 9.6 Telemetry verification

CI or an integration environment **MUST** test trace continuity for each service stack:

- send a known valid `traceparent`;
- verify the service joins that trace;
- verify an outbound test call receives a child context;
- assert tenant/correlation fields appear only after trusted resolution; and
- assert secrets and representative PII are absent from captured logs and spans.

Cross-service smoke tests SHOULD verify one trace through ingress, PEP/PDP, service, and a
downstream dependency.

## 10. Resilience and runtime behavior

### 10.1 Deadlines, retries, and circuit breaking

- Every remote or data-store operation **MUST** have an explicit finite timeout bounded by the
  caller's remaining deadline.
- Timeouts decrease toward inner dependencies, leaving time for the caller to handle failure.
- Retry only transient failures, only with bounded attempts, exponential backoff, and jitter.
- Non-idempotent writes are not retried unless protected by an idempotency mechanism.
- Avoid layered retries. Ordinarily one outer layer owns the retry budget.
- Connection pools, pending queues, concurrency, and request bodies **MUST** be bounded.
- Circuit breaking/outlier detection needs observable state and a recovery strategy.
- Do not catch an error merely to return an empty success or stale data without making that
  degradation explicit in the contract.

### 10.2 Health and graceful shutdown

Every backend service **MUST** retain the Reva `/health` compatibility endpoint. It **MUST**
return HTTP 200 only when the instance is ready to receive traffic; it returns a non-success
status while starting, draining, or otherwise not ready. Framework profiles **MAY** add
separate `/live`, `/ready`, startup, or management endpoints, and Helm probes **MUST** target
the endpoint that represents their intended state.

Every service **MUST** implement:

| Endpoint/state | Meaning |
|---|---|
| Liveness | Process can continue; does not fail merely because a dependency is temporarily down |
| Readiness | Instance can safely receive new traffic and required dependencies are usable |
| Startup | Used when initialization can exceed normal liveness timing |

Health endpoints are low cost, expose no secrets, and normally do not require application
authentication because kubelet must call them. Network policy still limits unnecessary public
exposure.

On SIGTERM the service **MUST**:

1. stop becoming eligible for new traffic;
2. stop accepting new work;
3. drain bounded in-flight work;
4. stop consumers/workers without losing ownership semantics;
5. flush bounded telemetry and close pools/clients; and
6. exit before Kubernetes `terminationGracePeriodSeconds`.

Shutdown is tested under real requests and consumer work. A fixed sleep is not a shutdown
implementation.

### 10.3 Messaging and workflows

- Events include schema version, event ID, occurred time, tenant context, producer, and trace
  context.
- Consumers assume at-least-once delivery and are idempotent.
- Partition keys preserve required ordering; tenant ordering requirements are explicit.
- Schemas have compatibility checks. Poison messages go to a defined DLQ/quarantine path with
  alerts and replay ownership.
- Acknowledgement/commit occurs only after durable processing or an explicitly designed handoff.
- Workflow/activity timeouts, retries, and idempotency reflect business semantics, not generic
  defaults.

## 11. Data and persistence

- The service owning data is the only writer unless a documented contract says otherwise.
- Use migrations/changesets for schema and index evolution; runtime implicit schema/index
  mutation is prohibited in production.
- Queries bind values and are tenant-scoped by construction.
- Transactions are as short as correctness permits. Do not hold transactions across remote
  network calls.
- Optimistic concurrency/version fields SHOULD protect concurrent updates where last-write-wins
  is unsafe.
- Cache keys include tenant and schema/version namespace. Cache invalidation and stale-data
  tolerance are documented.
- Backups require stated RPO/RTO, retention, encryption, and a regularly exercised restore
  procedure. An untested backup is not accepted evidence of recoverability.
- Data deletion and retention include primary storage, replicas, caches, search indexes,
  events/DLQs, logs, traces, and backups according to policy.

Technology-specific rules are in the R2DBC and MongoDB baselines.

## 12. Testing standard

### 12.1 Test portfolio

Every service uses a risk-based portfolio:

| Test type | Required scope |
|---|---|
| Unit | Domain rules, use cases, validation, mapping, error paths |
| Component/slice | Framework adapters with controlled dependencies |
| Integration | Real database/broker/cache through Testcontainers or an equivalent ephemeral environment |
| Contract | OpenAPI/provider-consumer compatibility and shared error/trace contracts |
| Security | Authorization matrix, tenant negative cases, malformed inputs, limits, SSRF/injection as applicable |
| Concurrency | Cancellation, races, backpressure, duplicate delivery, idempotency |
| Performance | Changed hot paths, resource limits, pool behavior, rollout/shutdown where relevant |
| Resilience | Timeout, dependency failure, retry, partial startup, and graceful termination |

Tests must be deterministic, isolated, parallel-safe where claimed, and free of live production
dependencies. Avoid real sleeps; use controllable clocks/schedulers and bounded eventual
assertions.

A bug fix **MUST** add a test that fails before the fix and passes after it.

### 12.2 Coverage policy

Coverage is a guardrail, not proof of correctness.

- No merge may reduce repository coverage unless an approved exception explains the measured
  trade-off.
- Changed production code **MUST** achieve at least 90% line/statement coverage.
- The repository floor is 80% line/statement and 75% branch where the ecosystem measures
  branches.
- Java repositories **MUST** satisfy the Reva standard of at least 90% line coverage through a
  build-failing JaCoCo `check` during `verify`. A report-only parent configuration is not an
  enforcement gate and is migration debt until the parent supplies the check centrally.
- Authorization, tenant isolation, policy evaluation, cryptography integration, money, and
  data-residency routing **MUST** test every documented decision outcome; a numeric average
  cannot waive a missing security branch.
- Generated sources, compiler artifacts, and declarative wiring MAY be excluded only through a
  reviewed central pattern. Production logic may not be annotated away from coverage.
- New repositories start compliant. Existing repositories below the floor use a ratchet:
  coverage does not fall, changed code meets 90%, and a remediation target is tracked.

Teams SHOULD use mutation testing for critical domain/security modules. A high coverage number
with surviving trivial mutants or assertion-free tests is not accepted as strong evidence.

### 12.3 Test quality

- Assert externally meaningful behavior and state, not private implementation call sequences.
- Use table/parameterized tests for rule matrices and boundary values.
- Include success, expected rejection, malformed input, timeout/cancellation, dependency
  failure, and duplicate/replay cases.
- Mock only at owned ports. Integration tests use real protocol implementations where behavior
  matters; do not replace PostgreSQL/MongoDB/Kafka semantics with an incompatible in-memory
  substitute.
- Contract and schema snapshots require semantic review; blindly updating snapshots is
  prohibited.
- Flaky tests are defects. Quarantine requires an owner and short expiry, and cannot silently
  remove a release-critical check.

## 13. Performance engineering

Performance requirements derive from service SLOs and capacity assumptions, not a universal
requests-per-second number.

### 13.1 Required methodology

For a new service or material hot-path/concurrency/pool change:

1. define workload shape, payload distribution, tenant mix, dependency latency, data volume,
   concurrency, and success criteria;
2. capture a versioned baseline in a production-like environment;
3. measure latency percentiles, throughput, errors, CPU, memory, GC/event-loop lag, queue/pool
   saturation, and downstream load;
4. run load, stress/breakpoint, spike, and soak tests as risk warrants;
5. profile before optimizing; and
6. record the result, environment, revision, and accepted capacity limit.

### 13.2 Gates

- A change SHOULD NOT regress p95 latency or sustainable throughput by more than 10% under the
  same controlled workload without explicit approval and explanation.
- Error rate and SLO compliance are hard gates; higher throughput obtained by dropping,
  timing out, or weakening work is not an improvement.
- Pool and worker sizes are determined from measurements and downstream budgets, not copied
  defaults or CPU folklore.
- Load generation runs outside the service under test.
- Performance tests **MUST** use bounded/sanitized data and must not target production without
  explicit operational approval.
- Performance results include traces/profiles that identify the limiting resource and a safe
  operating envelope below the breakpoint.

## 14. CI/CD quality gates

The central GitLab pipeline is the delivery source of truth and is governed by
[`GitLab/baseline.md`](GitLab/baseline.md). A merge pipeline **MUST** fail on:

- formatting/lint violations;
- compilation or strict type-check failures;
- unit/integration/contract test failure;
- coverage below the applicable gate;
- architecture/dependency-rule violations where configured;
- prohibited or leaked secrets;
- unaccepted SAST/dependency/container vulnerabilities;
- invalid OpenAPI/schema contracts;
- failed container build or image scan; and
- missing required artifacts.

Security, test, and coverage jobs **MUST NOT** be made optional to get a merge green. A
temporary failure waiver uses the exception process with an owner and expiry.

Deployments:

- use immutable image tags for releases;
- specify CPU/memory requests and limits based on measurements;
- configure HPA, disruption budget, topology/affinity, and probes for availability needs;
- roll out progressively for high-risk changes;
- expose build/version information for rollback diagnosis; and
- never update production, DR, or historical release mappings without explicit approval.

## 15. Documentation and knowledge baseline

### 15.1 Required service knowledge

At least two engineers owning a service SHOULD be able to:

- explain its domain responsibility and upstream/downstream contracts;
- trace an authorized request through PEP/PDP and tenant resolution;
- run, test, profile, and debug it locally;
- locate its logs, metrics, traces, dashboards, alerts, and SLO;
- explain data ownership, isolation, migration, backup, and restore;
- perform a safe rollout, rollback, and dependency failure drill; and
- rotate/revoke its credentials without exposing them.

Technology-specific competency lists appear in the applicable profile baselines.

### 15.2 Required documentation

Each service README or linked runbook **MUST** document:

- purpose and owner;
- supported runtime and framework;
- local prerequisites/run/test commands;
- API/event contracts and dependencies;
- configuration names without secret values;
- health, metrics, and tracing behavior;
- data ownership and migration procedure;
- deployment and rollback;
- SLOs/alerts and incident runbook; and
- known time-bound exceptions.

Use an ADR for security model, persistence technology, tenant isolation, externally visible
contract, framework/runtime, or major resiliency decisions. ADRs record context, decision,
alternatives, consequences, owner, and review date.

## 16. Definition of Done

An engineering change is done only when all applicable items are true:

### Design and code

- [ ] Dependency direction and module boundaries remain valid.
- [ ] Names follow the company, language, and framework conventions.
- [ ] No blocking/unbounded work was added to an async/reactive path.
- [ ] Public contracts are backward compatible or versioned with a migration.

### Security and tenancy

- [ ] PDP/PEP enforcement remains present and fail-closed.
- [ ] Trusted identity and tenant context are propagated correctly.
- [ ] Cross-tenant negative cases and object/property authorization are tested.
- [ ] Inputs, resource limits, outbound destinations, and error disclosure were reviewed.
- [ ] No secret, PII, token, policy body, or credential enters source or telemetry.

### Quality

- [ ] Formatter, lint, static/type analysis, and architecture checks pass.
- [ ] Unit, integration, contract, security, and applicable concurrency tests pass.
- [ ] Coverage satisfies the language and changed-code gates.
- [ ] A regression test accompanies every bug fix.

### Operations

- [ ] Logs are structured and correlated.
- [ ] Metrics use bounded-cardinality labels and support the SLO.
- [ ] Trace propagation and relevant spans were verified.
- [ ] Timeouts, retries, pools, queues, and shutdown behavior are bounded and tested.
- [ ] Performance was measured when the hot path or resource model changed.
- [ ] Health probes, resources, HPA/PDB, CI, container, and Helm contracts remain complete.

### Delivery

- [ ] Documentation, OpenAPI/schema, runbooks, and ADRs are updated.
- [ ] Dependency and image scans pass or have an approved, expiring exception.
- [ ] Rollout, compatibility, and rollback risks are understood.

## 17. Exceptions and enforcement

An exception is valid only when an ADR records:

- exact rule and affected scope;
- reason compliance is currently impractical;
- security, reliability, and maintenance risk;
- compensating controls;
- accountable owner;
- approval by the affected platform/security owner;
- expiry or review date; and
- migration/removal plan.

Exceptions are not inherited by new services and do not become precedent. Expired exceptions
fail the quality gate.

Rules should be automated in the closest reliable layer: formatter/linter, type checker,
architecture test, unit/contract test, central pipeline, container policy, Helm schema, or
admission policy. A written MUST with no enforcement SHOULD have a tracked enforcement task.

## 18. Primary references

- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
- [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/)
- [OpenTelemetry guidance for sensitive data](https://opentelemetry.io/docs/security/handling-sensitive-data/)
- [RFC 9457 — Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Kubernetes probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/)
- [Kubernetes container lifecycle hooks](https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/)

Reva implementation sources:

- `CLAUDE.md`
- `AGENTS.md`
- `.cursor/rules/41-observability.mdc`
- `.cursor/rules/42-security-boundaries.mdc`
- `development/architecture`
- `development/reva-parent`
- `development/shared-library-java`
- `development/shared-library-golang`
- `development/shared-library-python`
- `devops/core-devops-pipeline`
- `devops/helm-reva-*-app`
