<!--
GENERATED REVA STANDARD SNAPSHOT — DO NOT EDIT IN THIS REPOSITORY
Source: KarthikRamesh/reva-standards/.cursor/knowledge/hard-enforcement.md
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

# Hard-enforcement map

Cursor guidance improves first-pass quality. The following gates make the requirements
non-optional.

## Organization gates

| Standard | Hard gate |
|---|---|
| No secret in source | pre-receive/CI secret scanning plus `.cursorignore` |
| Approved dependencies | lockfile/BOM policy, SCA, license policy, artifact allowlist |
| No critical vulnerable image | blocking image scanner |
| PEP/PDP present | architecture/route inventory plus allow/deny/failure tests |
| Tenant isolation | cross-tenant negative integration tests |
| API compatibility | OpenAPI/schema/event compatibility diff |
| Coverage | build-failing profile threshold |
| Dependency direction | language architecture fitness test |
| Formatting/static correctness | required formatter/linter/compiler/type-check jobs |
| Data/telemetry safety | lint/contract tests and security review |
| Graceful runtime | startup/probe/shutdown integration tests |
| Reproducible delivery | central pipeline, immutable artifacts, SBOM/provenance |

## Language fitness functions

### Java

- Maven `verify`;
- Spotless/static analysis;
- ArchUnit for package/layer rules;
- JaCoCo build-failing 90% line check;
- PIT on security/tenant/domain-critical packages;
- BlockHound for reactive event-loop blocking;
- Testcontainers for PostgreSQL/Mongo/Kafka integration;
- OpenAPI/consumer contract checks.

### Python

- Ruff format and lint;
- strict type checking;
- import-linter for dependency direction;
- pytest/AnyIO plus pytest-cov thresholds;
- Testcontainers/protocol integration;
- pip-audit/SCA, secret and image scanning.

### Go

- `gofmt`/`goimports` verification;
- `go vet`, staticcheck/golangci-lint as approved;
- `go test ./... -race -count=1`;
- atomic coverage threshold;
- fuzz/property tests for parsers/routes;
- govulncheck/SCA, secret and image scanning;
- package-boundary and dependency-policy checks.

### Node/TypeScript

- Prettier formatting;
- type-aware ESLint, including floating-promise and boundary rules;
- strict `tsc --noEmit`;
- Vitest or approved Node runner with V8 coverage thresholds;
- dependency-cruiser/ArchUnitTS or eslint-plugin-boundaries;
- contract and runtime integration tests;
- npm audit/SCA, secret and image scanning.

### Next.js

- ESLint CLI, Prettier, and strict `tsc --noEmit` rather than the removed `next lint`
  command;
- unit/component tests with build-failing V8 coverage and changed-code enforcement;
- Playwright browser tests for critical journeys, authorization failures, tenant isolation,
  accessibility, hydration, and navigation;
- server-action and route-handler contract/security tests treating each entry point as a
  public RPC/HTTP boundary;
- cache-key, tag, invalidation, and cross-tenant negative tests for cached or revalidated
  content;
- production build, bundle-budget, Core Web Vitals, load, and OpenTelemetry propagation
  evidence; and
- dependency/SCA, secret, source-map, CSP/header, and browser/server-boundary checks.

## Infrastructure, delivery, and test-automation fitness functions

### OpenTofu

- `tofu fmt -check -recursive`, `tofu validate`, and declarative `tofu test`;
- TFLint plus Checkov/Trivy configuration scanning;
- saved-plan JSON policy checks with OPA/Conftest and cost evidence with Infracost;
- Terratest or an approved equivalent for deployed behavior;
- encrypted, versioned, segmented remote state with native locking;
- split plan/apply identity and exact saved-plan promotion;
- scheduled drift detection with owned remediation.

### Helm

- `helm lint --strict`, required `values.schema.json`, and deterministic render checks;
- helm-unittest, chart-testing, kubeconform, and OPA/Conftest policy checks;
- Trivy/Checkov chart scanning and a representative kind installation;
- pinned dependencies with committed `Chart.lock`;
- restricted Pod Security, IRSA/external-secret, NetworkPolicy, resource/probe/HPA/PDB checks;
- GitOps diff, upgrade, rollback, and hook/CRD ownership evidence.

### Katalon

- CodeNarc and Spotless for authored Groovy/JVM sources;
- Gradle/JUnit 5 or Spock tests plus JaCoCo for the pure shared test core;
- secret scanning and proof that profiles contain no real credentials;
- XML artifact review, locator-policy checks, and generated-output exclusions;
- KRE console/Docker smoke and sharded regression execution with machine-readable reports;
- hermetic parallel suites, bounded retry, flaky-test quarantine, and license/concurrency
  evidence.

### GitLab

- GitLab CI lint plus isolated contract tests for versioned components and templates;
- policy evaluation proving required security/compliance jobs cannot be bypassed by repository
  YAML;
- protected branches/environments, approval rules, `resource_group`, and controlled manual
  promotion checks;
- short-lived OIDC/workload identity with audience, subject, job-token allowlist, and
  least-privilege tests;
- reproducible build, scan, SBOM, signature/provenance, immutable artifact, and digest
  promotion evidence;
- trusted isolated runner, non-privileged/rootless build, cache isolation, and autoscaling
  validation; and
- parent/child pipeline, rules/changes, cancellation, retry, failure, rollback, and DORA/SLO
  operational tests.

## Coverage

The numeric source is `baseline.md` and the selected technology profile:

- changed production code: at least 90% line/statement;
- repository floor: 80% line/statement;
- branch floor: 75% where supported;
- Java: at least 90% JaCoCo line coverage;
- security/tenant decisions: every outcome directly tested.

OpenTofu and Helm use declarative coverage matrices rather than fabricated source-line
percentages: variables/validations, feature branches, supported examples, render combinations,
policy decisions, install/upgrade/rollback, and failure paths must all have build-failing
evidence. Katalon's pure JVM core follows the numeric code-coverage gate; its thin proprietary
artifact layer uses tagged execution and requirement/risk coverage.

GitLab delivery definitions use a pipeline-contract matrix rather than source-line coverage:
component inputs, rule branches, policy decisions, identity claims, artifact flow, promotion,
failure, retry, cancellation, and rollback paths all require build-failing evidence.

The configured build tool is the authority. A rule, agent narrative, or generated report with
no failing threshold is not enforcement.

## Local versus server controls

| Local Cursor control | Limitation | Server counterpart |
|---|---|---|
| Rule/AGENTS | Model may omit or misapply | Required CI/branch rule |
| Hook | Local/beta; textual shell guards cannot defeat obfuscated or computed paths | Protected sandbox, DLP, pipeline/environment |
| CLI permission | Applies to selected CLI config | CI job IAM/sandbox |
| `.cursorignore` | Repository/project scope; subprocess access depends on sandbox | secret store, OS ACL, and DLP |
| Review skill | Advisory | human/code-owner review |
| Bugbot | Automated reviewer | required status plus human owner |

Never describe a local hook as proof that production or repository policy is secure.
`beforeShellExecution` blocks direct sensitive-path references and common alternate readers,
but cannot recognize every program that computes a path at runtime. Managed Cursor sandbox,
filesystem access control, secret-manager design, DLP, and server-side secret scanning are the
hard boundary against deliberate obfuscation.

## Evidence format

Completion reports name:

- command or CI job;
- commit/diff tested;
- exit status;
- relevant test/coverage/scan summary;
- environment (local/container/CI);
- skipped/unavailable gates; and
- remediation owner for existing debt.

“Looks good,” “should pass,” or “Cursor followed the rule” is not evidence.
