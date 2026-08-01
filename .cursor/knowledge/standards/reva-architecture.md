<!--
GENERATED REVA STANDARD SNAPSHOT — DO NOT EDIT IN THIS REPOSITORY
Source: KarthikRamesh/reva-standards/.cursor/knowledge/reva-architecture.md
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

# Reva architecture knowledge for Cursor

This is a routing document for Cursor. The normative requirements remain in
[`../../baseline.md`](../../baseline.md), and product-level facts must be verified from the
live Reva workspace before implementation.

## Product model

Reva is a policy and guardrail platform for human and non-human identities, including AI
agents.

| Component | Responsibility |
|---|---|
| PAP | Policy authoring, versioning, approval, and publication |
| PDP | Evaluates subject/action/resource/context and returns allow or deny |
| PEP | Intercepts a protected operation, calls the PDP, and enforces the decision |
| PIP | Supplies authoritative attributes for evaluation |
| IBAC | Evaluates intent drift between AI-agent/tool hops |

The common protected request path is:

```text
caller
  -> approved application SDK, Kong PEP, or Istio/Envoy PEP
  -> pdp-edge evaluation
  -> Cedar/OPA engine plus authoritative attributes
  -> allow or deny
  -> application operation only after allow
```

AI flows add PDP evaluation at each protected hop and the required IBAC judgment between
agent/tool hops.

## Non-negotiable boundaries

- Authentication establishes identity; it is not authorization.
- Protected operations fail closed on deny, timeout, malformed response, or unavailable PDP.
- Public operations are explicitly classified; they are never a PDP-failure fallback.
- Authorization-relevant IDs and attributes are validated and canonical before evaluation.
  The handler consumes exactly those canonical values.
- Client-controlled hosts, paths, query/body fields, `Origin`, or untrusted internal headers do
  not establish tenant identity.
- External ingress strips client-supplied internal identity headers before trusted injection.
- Inter-service calls propagate trusted tenant/user context and W3C trace context.
- Service-local role checks, JWT claim authorization, fallback users, and duplicate PDP clients
  are prohibited.

## Shared implementation routes

| Profile | Approved route |
|---|---|
| Java | Reva Java PEP/shared integration and `shared-library-java` |
| Python | `reva_utility` and lowercase `@restrict` |
| Go | canonical `shared-library-golang` with `RestrictV2Gin`, `RestrictV2Chi`, `RestrictV2Mux`, or `RestrictV2HTTP` |
| Node | approved Node PEP/shared integration |
| Next.js | server-only client to the approved Reva BFF/service; browser/proxy/session checks are UX or defense in depth, never the authoritative PDP decision |
| Mesh/gateway | verified Kong or Istio/Envoy PEP with route-to-policy inventory tests |

Do not run both an application PEP and mesh PEP accidentally. Defense in depth requires
explicit ownership, equivalent canonical mapping, and tests for both decisions.

Next.js server components, route handlers, and server actions do not create a new policy
plane. Product data and mutations flow through the canonical BFF/service and deployed Reva
PEP/PDP path. Direct product-database access or a UI-local authorization engine requires an
approved architecture/security ADR. Tenant- or user-sensitive rendering and cache entries
must include the complete isolation identity and must never cross principals.

## Data and runtime

- Secrets come from AWS Secrets Manager through IRSA/EKS Pod Identity and Kubernetes secret
  mounting. They are not committed or placed in plaintext Helm values.
- Service code logs only to stdout/stderr using the profile logger.
- Telemetry uses bounded dimensions and never exposes tokens, policies, PII, sensitive request
  bodies, or tenant database names.
- Every remote/store call has a deadline. Retries are bounded, jittered, and limited to safe
  transient/idempotent work.
- `/health` is readiness-compatible. Liveness does not restart an instance merely because a
  dependency is down.
- SIGTERM makes readiness false, stops new work, drains, closes resources, flushes telemetry,
  and exits within the configured grace period.
- Container filesystems are not application state. AWS access uses workload identity.

## Delivery contract

A deployable application or backend repository has:

- `.gitlab-ci.yml` using the approved central language pipeline;
- standard build/runtime image contract;
- Helm values with resources, probes, autoscaling, service account/IRSA, and secret references;
- OpenAPI/event contracts as applicable;
- executable unit/integration/contract/security tests;
- coverage enforcement;
- vulnerability, secret, dependency, license/policy, SBOM, and image gates; and
- rollout/rollback/runbook ownership.

Cursor must inspect the live service, central CI template, Dockerfile, Helm chart/values, and
mapping repositories before changing this contract.

The GitLab delivery profile governs the pipeline definition around this contract. Repository
pipelines stay thin, consume centrally owned versioned interfaces, use short-lived workload
identity, preserve immutable build/scan/SBOM/provenance evidence through promotion, and cannot
weaken organization execution/scan/approval policies. GitLab does not replace Reva's
OpenTofu remote-state, Helm/GitOps, environment-approval, or release-mapping authorities.

## Sources to verify

In `/Users/karthikramesh/Projects/Reva`:

- `CLAUDE.md` and `AGENTS.md` — workspace navigation and operating rules;
- `development/architecture/` — canonical product decisions;
- `development/reva-schema/schema.json` — Cedar entities/actions;
- `development/shared-library-{java,golang,python}` — live shared integrations;
- `development/reva-parent/pom.xml` — live Java parent;
- `development/ui-monorepo/`, `development/platform-ops-ui/`, and
  `development/website/` — verified Next.js implementation state and migration evidence;
- `devops/core-devops-pipeline/` — CI implementation;
- `devops/dockerfiles/` — standard images;
- verified `devops/terraform-aws-*` modules and their consuming `devops/tf-deploy-*` layers —
  OpenTofu module/live-root behavior;
- `devops/helm-reva-*-app/` — chart contract;
- `devops/helm-values-repository/` — environment overrides; and
- `devops/reva-platform-client-mapping/` — logical-to-registry mapping.

Katalon project locations and shared test-core coordinates are not inferred from a repository
name. Resolve them from tracked project/build files and the central CI includes before citing
or changing them.

Generated indexes and this file help navigation; live files win when implementation facts have
drifted.
