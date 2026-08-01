# demo-ai-app — Reva agent operating contract

Billing-support agentic app hosted on **Render**. Every LLM and MCP hop goes through your **cloud-hosted Kong**; a Kong plugin you write there calls **Reva PDP** for allow/deny. This repo does **not** contain a Kong plugin or talk to Reva directly.

## Instruction precedence

1. The current user request and explicit approvals.
2. This root `AGENTS.md` and root organization rules.
3. The nearest module `.cursor` overlay for module architecture and commands.
4. Tracked repository contracts, ADRs, build files, CI, and tests.

Module overlays narrow the root standard; they never weaken authorization, tenancy, secrets,
quality, observability, compatibility, or production-safety requirements.

## Repository profile

- Repository: `development/demo-ai-app`
- Selected profiles: `reva-org`, `reva-python`, `reva-fastapi`, `reva-agentic`, `reva-gitlab`
- Standards revision: `740fdff52ba1d093d36652347f64850c51ce9700`
- Adoption: progressive and non-breaking; application behavior, build inputs, and runtime
  configuration must not change merely to satisfy Cursor guidance.

This repository has no independently manifested child modules.

## Reva invariants

- Preserve PDP/PEP authorization and fail closed. Reuse the approved Reva SDK, middleware, or
  sidecar; never add hand-written authorization.
- Preserve tenant identity and request context across asynchronous and service boundaries.
- Keep secrets out of source, prompts, logs, traces, Terraform/Helm plaintext, and generated
  context. Use AWS Secrets Manager with IRSA or Pod Identity.
- Use the repository's established structured logger and W3C trace propagation. Do not add a
  competing logging framework or emit sensitive/high-cardinality data.
- Preserve public APIs, schemas, persistence ownership, deployment contracts, and backward
  compatibility unless a versioned migration is explicitly approved.
- Do not modify production, DR, historical release pins, or live infrastructure without a
  separate explicit approval.

## Engineering workflow

1. Read this file, the root repository profile, and the nearest module profile.
2. Identify the owning module, callers, public/data/security contracts, and relevant tests.
3. Make the smallest cohesive change; do not perform opportunistic broad refactors.
4. Add direct behavior tests for every new behavior and regression tests for fixes.
5. Run targeted checks, then the repository's configured full gate.
6. Report exact commands/results, coverage evidence, skipped checks, and remaining risk.

## Verified or convention-derived commands

- Setup: `python -m pip install -r requirements.txt`

Commands listed here are guidance derived from tracked manifests. Tracked wrappers, CI, and
repository documentation remain authoritative when they differ.

## Test and coverage policy

For new or materially modified executable production code, add direct behavior tests designed
to achieve at least 95% line/statement coverage of the changed executable code.
This is the Reva adoption target, not a claim that repository-wide coverage or a changed-code
CI gate already exists. Preserve every currently enforced gate and report measured results and
unmeasured gaps. Use Arrange-Act-Assert or Given-When-Then structure with deterministic names.

Declarative assets use behavior matrices instead of source-line percentages: cover validation,
policy, render/plan, failure, upgrade, rollback, and contract paths with build-failing checks.

## Definition of Done

- The change stays within the owning module and preserves contracts and dependency direction.
- Required security, tenancy, error, observability, and cancellation/failure paths are tested.
- Format, lint, type/static analysis, unit, integration, contract, coverage, and build checks
  pass where configured; omissions are explicitly reported.
- `node .cursor/tools/validate-cursor-config.mjs` and
  `node .cursor/tools/test-hooks.mjs` pass when Cursor context changes.
- No generated artifact, secret, application behavior, build input, deployment value, or
  release pin changed unintentionally.
