<!--
GENERATED REVA STANDARD SNAPSHOT — DO NOT EDIT IN THIS REPOSITORY
Source: KarthikRamesh/reva-standards/Python/baseline.md
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

# Reva Python Baseline

| Field | Value |
|---|---|
| Status | Normative language baseline |
| Extends | [`../baseline.md`](../baseline.md) |
| Applies to | Reva Python services, workers, jobs, agents, and shared libraries |
| Current Reva profile | Python 3.13, `reva_utility`, loguru, pytest, OpenTelemetry |

This document defines Python-specific rules. Framework documents such as
[`FastAPI/baseline.md`](FastAPI/baseline.md) add transport-specific requirements. If this
document and the company baseline differ, the stricter rule applies unless the documented
precedence or an approved exception says otherwise.

## 1. Runtime, packaging, and dependency policy

- Deployable code **MUST** use the Python minor supplied by the Reva standard image and central
  CI template. The current target is Python 3.13.
- `pyproject.toml` **MUST** be the source of truth for project metadata, the supported Python
  range, runtime dependencies, development groups, build configuration, and tool settings.
- New repositories **MUST** commit a complete, reproducible lock file. `uv.lock` is the target
  format when the central pipeline supports `uv`; another approved resolver MAY be used only
  when it provides equivalent transitive locking and frozen CI installation.
- CI **MUST** install from the committed lock without resolving newer versions. Direct and
  transitive dependency changes are reviewed through the lock-file diff.
- Runtime libraries belong in the runtime dependency set. Test, lint, type-check, and build
  tools belong in development groups and **MUST NOT** be installed in the final runtime image.
- A package **MUST NOT** import a dependency that is absent from its declared metadata.
- Unpinned VCS URLs, mutable branches/tags, local paths, credentials in dependency URLs, and
  dependency installation from an unreviewed index are prohibited in release code.
- Shared packages **MUST** declare `Requires-Python`, expose a deliberate public API, include a
  `py.typed` marker when distributing type information, and build both wheel and source
  distribution in CI.
- The build backend and lock tool are repository-wide decisions. A repository **MUST NOT** mix
  `setup.py`, ad hoc `requirements.txt` generation, and `pyproject.toml` as competing sources of
  truth.
- Virtual environments, caches, local `.env` files, coverage output, and generated distributions
  **MUST NOT** be committed.

### 1.1 Legacy migration

An existing repository that still uses `setup.py` or `requirements.txt` MAY retain them during
a bounded migration, but it:

1. keeps the current installation path reproducible;
2. adds missing dependency declarations and a supported-Python constraint immediately;
3. does not use the legacy structure as the template for new repositories;
4. records the target `pyproject.toml`/lock migration with an owner; and
5. does not combine an unrelated feature change with a repository-wide packaging rewrite.

## 2. Project and package layout

New deployable services SHOULD use a `src` layout:

```text
pyproject.toml
uv.lock
src/
  <service_package>/
    __init__.py
    application/
    domain/
    adapters/
      http/
      persistence/
      clients/
      messaging/
    platform/
      auth/
      config/
      logging/
      telemetry/
      health/
    main.py
tests/
  unit/
  integration/
  contract/
  security/
```

- Organize application behavior by business capability. Do not grow unrelated global
  `services.py`, `helpers.py`, or `utils.py` dumping grounds.
- Domain and application modules **MUST NOT** import FastAPI request/response types, concrete
  database drivers, cloud SDK clients, or deployment configuration.
- Adapters implement application-owned ports. Dependency direction points inward.
- `main.py` is a composition/process boundary, not a container for routes and business logic.
- `__init__.py` exposes only a deliberate stable package API. Wildcard imports and recursive
  re-export trees are prohibited.
- Import cycles are prohibited. Imports **MUST NOT** trigger network calls, load models, create
  event loops, configure process-wide logging repeatedly, or read deployment secrets.
- A file should own one cohesive concept. Split it when unrelated reasons to change, complex
  branching, or test setup indicate more than one responsibility; do not split merely to meet
  an arbitrary line count.
- Tests may mirror the source capability tree. Shared fixtures live at the narrowest useful
  scope rather than in one process-global `conftest.py`.

## 3. File, module, and identifier naming

### 3.1 Files and packages

| Artifact | Required pattern | Example |
|---|---|---|
| Import package | short lowercase name; underscores only where clarity or an established API requires them | `reva_utility` |
| Module/file | lowercase `snake_case.py` | `policy_store_client.py` |
| Unit test | `test_<unit>.py` | `test_policy_evaluator.py` |
| Integration test | `test_<boundary>_integration.py` | `test_redis_cache_integration.py` |
| Contract test | `test_<contract>_contract.py` | `test_pdp_contract.py` |
| Migration | tool-required revision plus a descriptive slug | `20260729_add_policy_version.py` |
| CLI module | descriptive module with an explicit `main()` | `rebuild_policy_index.py` |

- Module names are importable identifiers: no hyphens, spaces, uppercase letters, or vague
  sequence names such as `utils2.py`.
- Do not use a standard-library or common third-party package name for a local module
  (`logging.py`, `typing.py`, `fastapi.py`, `pydantic.py`, `httpx.py`).
- Singular/plural naming reflects ownership: a module that defines one aggregate may be
  singular; a collection resource path may be plural.

### 3.2 Identifiers and variables

| Item | Standard |
|---|---|
| Function, method, local variable, parameter | `snake_case` |
| Class, exception, protocol, enum | `CapWords` |
| Module-level constant | `UPPER_SNAKE_CASE` |
| Non-public module/member | one leading underscore |
| Boolean | predicate form: `is_ready`, `has_access`, `can_retry`, `should_audit` |
| Factory | `create_<thing>` or `build_<thing>` |
| Event handler | `handle_<event>` |
| Identifier | domain name plus `_id`: `tenant_id`, `policy_store_id` |
| Value with a unit | suffix such as `_ms`, `_seconds`, `_bytes`, `_percent` |
| Type variable | descriptive `...T`, or `_T` only when truly generic and local |

- Exception class names **MUST** end in `Error`. Never shadow Python built-ins such as
  `BaseException`, `Exception`, `id`, `type`, `input`, or `list`.
- Acronyms read as words inside names: `http_client`, `parse_jwt`, `pdp_response`, and
  `policy_id`. Preserve different casing only at a public wire boundary.
- Coroutines are named by intent (`fetch_policy`), not by an `_async` suffix.
- Collection names are plural; a mapping name communicates both sides when they are not
  obvious (`policy_by_id`).
- Avoid generic names such as `data`, `info`, `obj`, `item`, `manager`, `helper`, `result`, and
  `temp` when a domain name exists.
- A name communicates side effects: use `save_policy` or `publish_decision`, not `get_policy`,
  when state changes.
- Short names are limited to conventional, tiny scopes such as `i` in a bounded enumeration.
  Security, tenant, money, time, and policy values always use explicit names.
- Double-underscore names are reserved for Python-defined protocols. Name mangling is not an
  access-control mechanism.

## 4. Formatting, linting, and static analysis

- Ruff is the Reva Python formatter, import sorter, and primary linter. Format and lint checks
  **MUST** run in CI and **MUST NOT** mutate files in the check job.
- A repository **MUST** use one strict type checker—mypy or Pyright—configured in
  `pyproject.toml`. New repositories SHOULD use the centrally selected checker once the shared
  template defines one.
- Public functions, application/service methods, adapter ports, configuration, DTOs, and all
  I/O boundaries **MUST** have complete parameter and return annotations.
- CI **MUST** reject unused suppressions. A `# noqa` or type-ignore comment is localized to the
  relevant code, names the rule where supported, explains why, and has a removal condition if
  temporary.
- Generated code is excluded only through a reviewed central configuration. Production logic
  is not broadly excluded to make checks green.
- Complexity and dependency-cycle checks SHOULD be enabled centrally. A threshold is a review
  signal, not permission to create many trivial forwarding functions.

## 5. Types and data modeling

- External JSON, headers, messages, cache values, database rows, and untyped SDK results are
  untrusted until parsed into a typed boundary model.
- `Any` is prohibited in production code except at a localized interoperability boundary where
  `object` plus narrowing or a typed adapter cannot represent the API. The exception requires a
  comment and validation before the value moves inward.
- Prefer abstract input types and concrete return types: accept `Mapping`, `Sequence`, or an
  owned `Protocol` when appropriate; return a known application-owned representation.
- Use Pydantic models for external/configuration validation, dataclasses for suitable internal
  value objects, `TypedDict` for a genuinely mapping-shaped contract, and protocols for
  structural ports. Raw nested dictionaries are not the default domain model.
- Mutable defaults are prohibited. Use `None` plus construction or `default_factory`.
- Collection ownership is explicit. Do not expose a mutable list/dictionary that another layer
  can mutate unexpectedly.
- Use `Enum`/literal unions for closed wire values and exhaustive handling for closed states.
- Use timezone-aware UTC timestamps at boundaries and RFC 3339 strings in APIs. Naive datetimes
  are prohibited in persisted or cross-service contracts.
- Monetary values use `Decimal` or an approved money value object with explicit scale and
  currency, never binary `float`.
- DTOs, domain models, persistence records, and telemetry attributes are separate concerns. A
  validated request model is not automatically safe to persist or return.

## 6. Functions, modules, and dependency management

- Functions perform one coherent operation and make I/O and state changes visible in their
  names and signatures.
- Prefer keyword-only parameters or a typed parameter object when multiple same-typed or
  optional arguments would be ambiguous.
- Boolean flags that choose unrelated behavior are prohibited; use separate functions or a
  discriminated command.
- Dependencies are passed through constructors/factories/providers. Importing and mutating a
  process-global client from business code is prohibited.
- Pure domain/policy functions stay separate from I/O and should be table-, property-, and
  mutation-tested where risk warrants.
- Catch an exception only to translate it, add actionable context, compensate, or recover.
  Preserve the cause with `raise ... from error`.
- Do not catch `BaseException`. A broad `except Exception` is allowed only at a true process,
  task, or transport boundary and still must preserve cancellation and safe diagnostics.
- Comments explain invariants, threat assumptions, units, or non-obvious trade-offs. Docstrings
  are required for public libraries and public behavior whose contract is not evident from its
  type signature.

## 7. Async I/O, concurrency, and cancellation

- Use `async def` only when the function performs awaitable work or must implement an async
  protocol. Do not mark CPU-bound or blocking code async.
- Blocking filesystem, boto3, model-inference, database, subprocess, or HTTP work **MUST NOT**
  run on an event-loop thread. Use a supported async client, a synchronous framework worker
  path, a bounded thread offload for blocking I/O, or a process/dedicated service for CPU-heavy
  work.
- `asyncio.TaskGroup` is the preferred structured-concurrency primitive when sibling tasks have
  one lifetime. Unstructured `create_task()` calls are prohibited unless an application-owned
  task registry observes errors, owns cancellation, and closes the task at shutdown.
- `asyncio.gather()` and task creation operate only over bounded cardinality. Use a semaphore,
  bounded queue, batch, or worker pool for request-derived collections.
- Every remote and data-store call has explicit finite connect/read/write/pool/total timeouts
  bounded by the caller deadline.
- Cancellation propagates inward. Code that catches `asyncio.CancelledError` performs bounded
  cleanup and re-raises it. `asyncio.shield()` requires a documented correctness reason.
- Do not call `asyncio.run()` or manipulate an event loop inside an already running service.
  Libraries expose awaitable APIs and let the application own the loop.
- Queue sizes, executor sizes, thread counts, connection pools, and pending work are bounded and
  observable.
- A timeout does not imply the underlying blocking work stopped. Thread-offloaded operations
  require idempotency and capacity controls; CPU work belongs in a cancellable process or
  durable job where needed.
- Long-lived HTTP, database, cache, broker, and telemetry clients are constructed once per
  dependency/security profile and closed during application shutdown. Per-request clients are
  prohibited.

## 8. Request context, configuration, and secrets

### 8.1 Request-local context

- Prefer explicit context parameters in application interfaces. Use `ContextVar` only for
  cross-cutting request state that cannot be passed cleanly, such as log correlation.
- Context values use a typed immutable object, not an unstructured mutable dictionary.
- A `ContextVar` **MUST NOT** have a mutable default.
- Every `token = context_var.set(value)` is paired with `context_var.reset(token)` in `finally`.
  Middleware must remain correct under exceptions, cancellation, streaming, and nested calls.
- New tasks receive only deliberately propagated context. Context is cleared before unrelated
  background jobs are scheduled.
- Tenant, domain, and username values become authoritative only after the approved trusted
  boundary. Raw inbound internal headers are not trusted identity.

### 8.2 Settings and credentials

- Use `pydantic-settings` to parse configuration once at startup into an immutable, typed
  settings object. Business modules **MUST NOT** call `os.getenv` throughout the codebase.
- Security-sensitive settings SHOULD use `SettingsConfigDict(extra="forbid")`, exact enum and
  URL types, field validators, and `SecretStr`/`SecretBytes`.
- Missing production values and unsafe localhost/insecure defaults fail startup. Local defaults
  are limited to an explicit local/test profile.
- `.env` loading is local-development support only and `.env` files are not committed.
- AWS clients use the default SDK credential provider chain with IRSA/EKS Pod Identity. Static
  AWS access key, secret key, or session token settings are prohibited in deployed services.
- Secrets are obtained through the approved Secrets Manager/Kubernetes integration. They are
  never logged, included in telemetry, copied into a ConfigMap, or embedded in an image.
- Configuration errors name the invalid key and rule without printing its sensitive value.

## 9. Errors and recovery

- Domain and application errors carry stable machine codes and structured safe context without
  importing HTTP framework types.
- Infrastructure adapters translate vendor exceptions into application-owned error categories
  while preserving the cause for internal diagnostics.
- New services and new API major versions use the company RFC 9457 problem contract. Existing
  published API versions retain their documented Reva envelope until a coordinated versioned
  migration. One API version **MUST NOT** mix formats ad hoc.
- Unknown exceptions become a safe generic internal error. Stack traces, SDK messages, SQL,
  upstream bodies, internal URLs, prompts, policies, and credentials never reach a client.
- Validation, authentication, authorization denial, not-found, conflict, rate limiting,
  cancellation, dependency timeout, and dependency unavailability remain distinct outcomes.
- Retry only transient failures, only where the operation is safe/idempotent, and only within a
  bounded attempt/deadline budget with jitter. Do not retry authorization denial or validation
  failure.
- Log an exception once at the boundary that owns remediation. Intermediate layers do not log
  and re-raise the same fault.
- Fatal process errors trigger safe diagnostics and bounded shutdown. Library code does not
  call `sys.exit`.

## 10. Reva authorization and tenant isolation

- When application-layer PEP enforcement owns a protected operation, Python services **MUST**
  use `reva_utility` and the approved `@restrict` integration. A verified Kong or Istio/Envoy
  PEP may own the route only when that ownership is documented and covered by route-to-policy
  inventory tests. Hand-written PDP HTTP calls, local role checks, and parallel authorization
  decorators are prohibited.
- A protected operation always fails closed for PDP deny, timeout, malformed response, or
  unavailability.
- An intentionally public route is explicitly classified and inventoried under the company
  baseline; it is not created dynamically as a fallback when authorization fails.
- System/service identity is accepted only from an authenticated workload boundary. A raw
  username/header value **MUST NOT** activate a system-user bypass.
- `allow_system_user`, authorization-disable flags, and permissive localhost PDP defaults are
  prohibited in deployed profiles. Approved local/test-only behavior must be impossible to
  enable accidentally in production.
- Agent and tool hops preserve the normal PDP contract and invoke IBAC between hops where the
  flow requires it.
- Every tenant-scoped database query, cache key, object path, message, lock, idempotency key,
  model/vector namespace, and background job includes the authoritative tenant scope.
- Repository and cache APIs SHOULD require tenant context structurally. Missing context fails
  closed rather than falling back to a shared namespace.
- PostgreSQL RLS is defense in depth when a shared-schema relational design uses it; it is not a
  substitute for application scoping and is not imposed on unrelated persistence technology.

## 11. Logging, metrics, and distributed tracing

### 11.1 Logging

- Service code uses loguru through the approved `reva_utility` configuration. Do not add
  structlog or another application logging framework.
- Production output is structured JSON to stdout/stderr. File logging, colored production
  formats, and `print()` service logging are prohibited.
- Configure logging once at process composition. Importing a module **MUST NOT** reconfigure
  global logging or install an exception hook repeatedly.
- Bind service/version/environment, trace ID, span ID, correlation ID, safe tenant ID,
  operation, outcome, and duration as structured fields when available.
- Third-party standard-library logging is bridged once into the approved pipeline; application
  modules do not mix logging APIs.
- Never log complete headers, request/response bodies, tokens, cookies, tenant secrets, policy
  bodies, prompts/model responses, Redis/database URLs, or raw upstream errors.
- Redaction happens before formatting/export. Tests verify the prohibited values are absent.

### 11.2 Metrics

- Use the approved Prometheus/OpenTelemetry integration and expose the company metrics endpoint.
- Record HTTP RED, dependency latency/outcome, queue/pool saturation, runtime/process state,
  authorization latency/outcome, and domain SLO metrics.
- Async services SHOULD expose event-loop delay and executor/queue saturation where supported.
- Labels use route/operation templates and bounded values. Tenant IDs, trace/request IDs,
  resource IDs, raw paths, exception messages, and model names supplied by users are prohibited
  labels.

### 11.3 OpenTelemetry

- Application composition initializes one OpenTelemetry SDK/provider before creating
  instrumented clients or serving traffic. Shared libraries use the OpenTelemetry API and
  **MUST NOT** install a competing provider/exporter.
- Export through OTLP to the in-cluster collector using a bounded batch span processor. Export
  failure must not block the request path; drops and exporter errors remain observable.
- Use the W3C Trace Context propagator for `traceparent` and `tracestate`. Baggage is allow-listed
  and contains no credentials, PII, prompts, policy content, or tenant secrets.
- Instrument only libraries actually in use: FastAPI/ASGI, aiohttp/httpx, database drivers,
  Redis, Kafka/Temporal, and supported AWS clients. Avoid duplicate HTTP/server spans from
  overlapping instrumentations.
- Add manual spans around meaningful application boundaries such as PDP/IBAC evaluation,
  Bedrock/tool calls, durable workflow steps, and expensive domain operations—not every
  function.
- Span names and attributes follow OpenTelemetry semantic conventions and use stable,
  low-cardinality route/operation names. Do not record full URLs, SQL text, request bodies,
  model prompts/responses, policy bodies, or user-controlled exception strings.
- Unexpected failures record the exception and error status once. Expected validation and
  authorization outcomes use the correct result attributes and are not automatically internal
  span errors.
- Loguru records include the active `trace_id` and `span_id`; a random policy/correlation ID is
  never represented as a trace ID.
- Sampling is centrally governed and parent-based. Audit events do not depend on trace
  sampling.
- The provider/exporter is flushed and shut down during application lifecycle cleanup within
  the Kubernetes termination budget.

## 12. Security practices

- Validate all external input and remote responses before use. Apply explicit string,
  collection, recursion, upload, decompression, pagination, and response-size limits.
- Dynamic outbound destinations require scheme/host/port/DNS/IP/redirect allow-list checks.
  TLS certificate verification is mandatory.
- SQL uses bound parameters or an approved query builder. User strings never become SQL,
  expression, path, shell, template, or policy fragments through interpolation.
- Unsafe deserialization (`pickle` from untrusted data, permissive YAML object construction),
  `eval`, `exec`, and dynamic import from untrusted input are prohibited.
- Subprocess calls use an argument array and `shell=False`; command and argument choices are
  allow-listed.
- Regular expressions over untrusted input use bounded inputs and receive ReDoS review.
- Cryptography uses approved libraries and platform services. Do not implement cryptographic
  primitives, token validation, or password hashing directly.
- Temporary sensitive files are avoided. When unavoidable they use restrictive permissions,
  bounded lifetime, and guaranteed cleanup.
- Dependency, SAST, secret, license/policy, SBOM, and image scans are merge gates under the
  company baseline.

## 13. Testing and coverage

- pytest is the standard runner. Async repositories use AnyIO's pytest plugin
  (`@pytest.mark.anyio`) or the centrally approved equivalent with an explicit
  event-loop/lifespan policy.
- Test names communicate behavior:
  `test_<operation>_<scenario>_<expected_result>`.
- Use Arrange/Act/Assert or Given/When/Then consistently. Assertions verify the meaningful
  result, side effects, and relevant negative behavior—not only that code did not raise.
- Unit tests are deterministic and do not call live PDP, AWS, databases, caches, brokers, or
  external HTTP endpoints.
- Integration tests use ephemeral real protocol dependencies where driver/transaction/encoding
  behavior matters. Contract tests validate OpenAPI, shared error, authorization, telemetry,
  and downstream-client contracts.
- Required security tests include allow/deny/PDP failure, malformed authorization responses,
  wrong tenant, missing tenant/resource ID, property-level access, SSRF/injection limits, and
  redaction.
- Concurrency tests cover cancellation, deadline exhaustion, bounded fan-out, race-sensitive
  updates, duplicate delivery/idempotency, queue saturation, and shutdown with work in flight.
- Fakes implement owned ports. Mock at a boundary the code owns; do not mock every internal
  function or framework implementation detail.
- Restore environment, ContextVars, logging handlers, clocks, patches, and global state after
  every test. Tests declared parallel-safe must not share mutable process state.
- A bug fix adds a regression test that fails before the fix.

Coverage follows the company baseline:

- changed production code: at least 90% line/statement coverage;
- repository floor: 80% line/statement and 75% branch coverage;
- security/tenant decision paths: every documented outcome tested; and
- generated code and reviewed declarative wiring are the only routine exclusions.

Existing repositories below the floor use the root-baseline ratchet. Coverage is not a substitute
for assertions, contract tests, mutation testing, or threat-based cases. Use mutation testing
selectively for policy/security/domain modules and property-based testing for parsers, identifier
rules, authorization matrices, and invariants.

## 14. Performance and diagnostics

- Every service establishes an SLO and a repeatable production-build load baseline before
  choosing worker, pool, queue, or replica counts.
- Use Locust, k6, or another approved external generator for service tests; use
  `pytest-benchmark` only for isolated microbenchmarks.
- Measure p50/p95/p99 latency, sustainable throughput, errors, CPU, RSS, allocation/GC,
  event-loop delay, executor and connection-pool saturation, downstream load, and telemetry
  overhead.
- Include realistic payload sizes, tenant distribution, authorization/PDP latency, downstream
  degradation, cold model/client initialization, keep-alive behavior, and shutdown.
- CPU profiles, allocation profiles, task dumps, and heap artifacts may contain sensitive data
  and receive restricted handling.
- Optimize measured bottlenecks. Do not disable validation, authorization, tenant scoping,
  logging, or tracing to improve a benchmark.
- Document the safe operating envelope below the breakpoint and use it to set Kubernetes
  requests/limits, HPA behavior, queues, pools, and concurrency.

## 15. Build, CI, container, and Kubernetes runtime

Required CI stages are:

1. frozen dependency/lock validation;
2. Ruff formatting check and lint;
3. strict type checking;
4. unit, integration, contract, and applicable security tests with coverage;
5. OpenAPI/schema compatibility checks;
6. SAST, dependency, secret, license/policy, and SBOM checks;
7. wheel/application build; and
8. standard image build and blocking vulnerability scan.

- A missing test command, `pass` placeholder, commented-out coverage command, or non-blocking
  HIGH/CRITICAL scan is not a passing gate.
- The runtime image uses the Reva Python 3.13 base pattern, contains only runtime dependencies,
  runs as a fixed non-root user, and has no build credentials or compiler toolchain.
- The filesystem SHOULD be read-only with a controlled writable temporary volume where needed.
  Drop Linux capabilities, disallow privilege escalation, and use the platform seccomp profile.
- The process uses exec-form startup so it receives SIGTERM as PID 1. Development reloaders are
  prohibited in deployed images.
- Kubernetes normally scales one application process per container. Multiple in-container
  workers require measured justification and memory/shutdown validation.
- Services retain the Reva `/health` compatibility endpoint, return 200 from it only when
  ready, expose distinct readiness/liveness behavior where probes need it, and complete
  graceful shutdown within 30 seconds.
- Helm wiring includes resource requests/limits, the intended service account/IRSA identity,
  startup/readiness/liveness probes, and a termination grace period consistent with application
  deadlines. Secrets are never rendered into a ConfigMap.

## 16. Current Reva migration debt — not approved examples

The following observed patterns are migration evidence, not permission to repeat them:

- `shared-library-python` still uses legacy packaging, advertises Python 3.7+, runs a Python 3.10
  packaging job, and has incomplete/unpinned dependency declarations.
- Some Python services have no executable tests or coverage gate even though central CI prints a
  test stage.
- The current shared logging configuration emits a colored human format and configures logging
  through import side effects rather than the target JSON lifecycle.
- The shared exception package shadows Python's built-in `BaseException`, exposes the legacy
  `{key,message,data}` envelope, and currently maps a bad-request type to HTTP 500.
- The current request ContextVar uses a mutable dictionary default, and representative
  middleware sets context without resetting its token.
- The current restriction aspect can use a localhost PDP default, has paths without finite
  HTTP timeout, logs policy/context payloads, invents a policy trace ID, and contains a
  header-derived system-user path.
- Some clients use tenantless cache keys, mutate shared context dictionaries, create
  per-operation clients, or log full upstream bodies/URLs.
- Some images run as root; existing Helm templates do not consistently wire service accounts,
  hardened security contexts, startup probes, or secret-safe configuration.

New code **MUST NOT** normalize these patterns. Fix shared cross-cutting defects in
`reva_utility`/central templates and migrate consumers rather than adding service-local copies.

## 17. Knowledge and Definition of Done

Service owners are expected to understand:

- Python object and import semantics, typing/narrowing, exception chaining, and packaging;
- the event loop, TaskGroup, cancellation, ContextVars, thread/process offload, and pool limits;
- Pydantic validation/settings and the difference between runtime validation and static types;
- pytest fixture scope, async testing, property/mutation testing, and coverage limitations;
- Loguru structured context and OpenTelemetry initialization/propagation;
- Reva PEP/PDP/IBAC, tenant isolation, IRSA, CI, Helm, Kubernetes probes, and shutdown; and
- profiling CPU, allocation, tasks, pools, and event-loop saturation.

Before merge:

- [ ] Files, packages, variables, types, exceptions, tests, and constants follow the naming rules.
- [ ] `pyproject.toml`, supported Python range, dependency declarations, and frozen lock agree.
- [ ] Ruff and strict type checking pass without unjustified suppressions.
- [ ] Async work, cancellation, timeouts, concurrency, pools, ContextVars, and cleanup are bounded.
- [ ] `reva_utility`/`@restrict` is used and tenant-negative/security tests pass.
- [ ] Loguru redaction and W3C trace/log correlation are verified.
- [ ] Tests and coverage satisfy the root baseline.
- [ ] Production startup, probes, SIGTERM drain, telemetry flush, IRSA, and image scans pass.
- [ ] Any retained legacy behavior has an owner, expiry, compatibility reason, and migration plan.

## 18. Primary references

- [PEP 8 — Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Python typing best practices](https://typing.python.org/en/latest/reference/best_practices.html)
- [Python `asyncio` task and structured-concurrency documentation](https://docs.python.org/3.13/library/asyncio-task.html)
- [PyPA `src` layout discussion](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [Python packaging projects tutorial](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/)
- [Pydantic settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [pytest documentation](https://docs.pytest.org/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [OpenTelemetry Python instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/)

Reva implementation references:

- `CLAUDE.md`
- `AGENTS.md`
- `.cursor/rules/12-python-services.mdc`
- `.cursor/rules/41-observability.mdc`
- `development/shared-library-python`
- `development/ibac-service`
- `development/intelligence-services`
- `devops/core-devops-pipeline/language/python/pipeline-template.yml`
- `devops/dockerfiles/python`
- `devops/helm-reva-python-app`
