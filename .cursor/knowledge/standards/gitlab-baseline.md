<!--
GENERATED REVA STANDARD SNAPSHOT — DO NOT EDIT IN THIS REPOSITORY
Source: KarthikRamesh/reva-standards/GitLab/baseline.md
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

# Reva GitLab CI/CD Engineering Baseline

| Field | Reva standard |
|---|---|
| Status | Normative delivery-platform baseline |
| Extends | [`../baseline.md`](../baseline.md) and [`../cursor-baseline.md`](../cursor-baseline.md) |
| Applies to | Reva GitLab pipelines, reusable CI components/templates, security policies, runners, artifacts, releases, and deployment orchestration |
| Current compatibility | Central include-based child pipelines from `devops/core-devops-pipeline` |
| Target architecture | Thin project orchestrators consuming immutable typed CI/CD components with group-enforced policy |
| Cloud identity target | GitLab ID tokens exchanged for short-lived AWS credentials |
| Configuration owner | Platform Engineering; Security owns enforced security policy and exception review |
| Production authority | Protected environments, separation of duties, ticketed approval, and explicit human authorization |

GitLab CI/CD is part of Reva's production architecture. Pipeline configuration is executable
code with access to source, build artifacts, registries, cloud identities, and deployment
systems. A pipeline that happens to pass is not necessarily reproducible, secure, observable,
or authorized.

The keywords **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** have their RFC
2119/RFC 8174 meanings. Repository instructions may strengthen this baseline but may not
silently weaken it. An exception requires the exact rule and scope, risk, compensating
control, accountable owner, approval, expiry, migration, validation, and rollback.

## 1. Outcomes and principles

Reva pipelines MUST be:

- thin at the consuming repository and centrally reusable;
- deterministic from a reviewed commit, immutable dependencies, and pinned tooling;
- fail-closed for quality, security, authorization, and deployment gates;
- free of long-lived cloud credentials and plaintext secrets;
- isolated by trust level, environment, repository, and workload risk;
- efficient through change detection, DAG scheduling, bounded artifacts, and measured caches;
- auditable from commit through immutable build, scan, promotion, and deployment;
- compatible with Reva language, OpenTofu, Helm, container, EKS, Istio, IRSA, and release
  contracts;
- observable without leaking source, variables, tokens, customer data, plans, or manifests;
  and
- operated through reviewed Git changes rather than console-only pipeline logic.

A prompt, component, template, manual job, or passing pipeline MUST NOT expand the user's
authority. Cursor and other agents do not receive permission to deploy, publish, mutate
infrastructure, change production/DR, rewrite release history, or bypass a control merely
because a CI job exists.

## 2. Verified current state, target state, and migration debt

### 2.1 Verified Reva state

As verified from the live Reva workspace on 2026-07-30:

- `devops/core-devops-pipeline` owns the common and language pipeline templates;
- service repositories use root child triggers and `include:project` to consume those
  templates;
- representative repositories still pin included templates to `ref: main`;
- duplicate branch/MR prevention is not yet consistently complete;
- the central templates still contain `CI_JOB_TOKEN` usage and some privileged
  Docker/QEMU-oriented build paths; and
- no tracked organization CI component catalog, `id_tokens:` adoption, or group pipeline
  execution policy was found in the verified central template surface.

This current include-based architecture is a compatibility fact. Mutable refs, incomplete
workflow rules, broad job-token use, privileged builders, and absence of policy/OIDC controls
are migration debt. They are not examples to copy into new pipeline design.

### 2.2 Approved target

The target is:

1. one Platform-owned CI component/catalog source with semantic releases and immutable pins;
2. root `.gitlab-ci.yml` files that contain only workflow, stage topology, typed component
   inputs/includes, and bounded module triggers;
3. group-linked pipeline execution, scan, and merge-approval policies for mandatory controls;
4. GitLab `id_tokens:` exchanged for short-lived, claim-bound AWS credentials;
5. ephemeral isolated runners using the approved autoscaler or Kubernetes executor;
6. rootless image builds through the approved BuildKit/buildah path;
7. immutable artifacts, SBOMs, provenance, signatures, and deployment verification; and
8. central DORA, pipeline, runner, reliability, and cost telemetry.

This target is adopted in controlled waves. A project MUST NOT invent private components,
policies, runner patterns, or identity flows while the shared platform is being built.

### 2.3 Version and tier verification

GitLab changes quickly. Before using a keyword or administrative control, Platform
Engineering MUST record and test:

- the exact GitLab server offering, tier, and version;
- the exact GitLab Runner version and executor/plugin versions;
- feature flags and availability for CI/CD components, inputs, policies, approvals, ID
  tokens, artifact access, and Kubernetes Agent behavior;
- the self-managed catalog and component-mirroring model, when applicable;
- CI lint behavior for the fully merged configuration; and
- upgrade and rollback evidence on representative Java, Go, Python, Node, OpenTofu, Helm,
  Lambda, and monorepo pipelines.

No research-document version claim automatically changes the Reva platform pin. A feature
that is beta, experimental, unavailable on the approved tier, or untested on the Reva
instance cannot be a mandatory dependency. Its safe compatibility path MUST remain until the
target control is proven.

## 3. Ownership and Reva delivery boundaries

| Concern | Canonical Reva owner |
|---|---|
| Common/language pipeline behavior | `devops/core-devops-pipeline` |
| Standard language container builds | `devops/dockerfiles/{java,go,python,nodejs,rust}` |
| Reusable Helm chart contract | `devops/helm-reva-{java,go,nodejs,python,rust}-{app,job}` |
| Environment/service Helm values | `devops/helm-values-repository` |
| OpenTofu modules and live roots | `devops/terraform-aws-*` and `devops/tf-deploy-*` |
| Logical-to-registry names | `devops/reva-platform-client-mapping` |
| Stable released image pins | `devops/reva-release-mapping/stable-versions` |
| Product/security architecture | `development/architecture` |
| Component catalog, runners, policies | Platform Engineering target ownership |

These are independent Git repositories. A pipeline change that spans repositories MUST list:

- every repository and file group;
- producer and consumer contracts;
- current and target component/template revisions;
- rollout order and compatibility window;
- security, identity, artifact, deployment, and rollback effects; and
- the owner of each required merge and release.

When commits are requested, use one commit per repository with a shared change identifier.
Do not publish a component before its tests and release evidence pass. Do not change a
consumer pin before the component version exists. Do not change Helm image tags before the
image is built and verified. Historical stable-version files are release records, not a
general CI edit surface.

## 4. Canonical files and naming

### 4.1 Consumer repository layout

```text
.
├── .gitlab-ci.yml
├── .gitlab/
│   └── ci/
│       ├── workflow.yml
│       ├── rules/
│       │   └── changes.yml
│       └── jobs/
│           ├── verify.yml
│           └── release.yml
├── ci/
│   ├── scripts/
│   │   ├── verify-coverage.sh
│   │   └── build-image.sh
│   └── fixtures/
├── CODEOWNERS
└── <language manifests and source>
```

The root `.gitlab-ci.yml` is the canonical entry point. It SHOULD normally contain:

- `workflow:rules`;
- an intentionally small `stages` list;
- immutable includes/components with typed inputs;
- variables that are non-secret repository contract values; and
- parent-child triggers for independently deployable modules.

Business logic, multi-step shell, scanner configuration, and repeated job bodies do not
belong in the root orchestrator.

### 4.2 Component project layout

```text
.
├── .gitlab-ci.yml
├── templates/
│   ├── java-service.yml
│   ├── opentofu-plan/
│   │   └── template.yml
│   └── helm-verify/
│       └── template.yml
├── tests/
│   ├── consumers/
│   └── expected/
├── ci/scripts/
├── README.md
├── CHANGELOG.md
├── LICENSE
└── CODEOWNERS
```

Each component uses one supported GitLab component layout. A component directory owns one
`template.yml`; a simple component may use `templates/<name>.yml`. Component source,
documentation, examples, tests, and release metadata evolve together.

### 4.3 File naming

| Item | Standard |
|---|---|
| Root pipeline | `.gitlab-ci.yml` exactly |
| CI fragments | lowercase kebab-case `.yml` under `.gitlab/ci/` |
| Components | lowercase kebab-case name under `templates/` |
| Shell scripts | lowercase kebab-case `.sh` under `ci/scripts/` |
| Python/Node helper scripts | ecosystem naming convention under `ci/scripts/` |
| Security policy | `.gitlab/security-policies/policy.yml` in the policy project |
| Ownership | `CODEOWNERS` with the platform/security paths explicitly owned |
| Test fixtures | lowercase kebab-case names describing the archetype and scenario |
| Generated child config | deterministic name under a protected ephemeral artifact path |

Use `.yml` for GitLab CI sources unless an existing owned repository has deliberately
standardized `.yaml`. Do not mix extensions inside one pipeline tree without a migration
reason.

### 4.4 Jobs, templates, inputs, and variables

- Job names use `stage:module:action`, for example `test:bff:unit` or
  `scan:policy-engine:container`.
- Hidden reusable jobs begin with `.`, for example `.node:test`.
- Policy-injected jobs use a unique organization prefix such as
  `reva-policy:security:sast` to avoid collisions.
- Component inputs use descriptive lowercase kebab-case or the centrally selected
  lower-snake-case convention consistently within the catalog. A catalog MUST choose one and
  lint it.
- CI/CD variables use `UPPER_SNAKE_CASE`.
- `CI_*` is GitLab-reserved and MUST NOT be shadowed.
- Reva service contract variables retain their established names:
  `SERVICE_NAME`, `PORT_NUMBER`, and `SERVICE_CONTAINER_REGISTRY_NAME`.
- Boolean inputs are typed booleans where `spec:inputs` supports them. Legacy variable
  booleans use documented `"true"`/`"false"` strings and are parsed explicitly.
- Names include units when the value does not encode them:
  `TIMEOUT_SECONDS`, `ARTIFACT_RETENTION_DAYS`, `MEMORY_LIMIT_MIB`.
- Environment names use stable lowercase paths such as `review/<slug>`, `development`,
  `staging`, and `production`; display aliases do not create a second environment identity.
- `resource_group` names identify the serialized mutable target, not the job or commit.

Generic names such as `build`, `test2`, `job`, `tmp`, `script`, `token`, and `deploy-prod-new`
are prohibited when the module, action, resource, or credential purpose is known.

## 5. Pipeline topology

### 5.1 Workflow rules

Every root pipeline MUST declare `workflow:rules` that:

- creates merge request pipelines;
- prevents a duplicate branch pipeline when the branch has an open merge request;
- supports default-branch and protected-tag release behavior deliberately;
- treats schedules, API/trigger, parent, and multi-project sources explicitly; and
- does not accidentally suppress policy-injected mandatory jobs.

`only` and `except` are prohibited in new configuration. Migrate them to `rules` with
behavioral tests. A catch-all `when: always` is not acceptable when it creates duplicate
branch and merge-request pipelines.

### 5.2 Stages and DAG

Use a readable stage spine appropriate to the repository, normally a subset of:

```text
validate -> build -> test -> scan -> package -> publish -> deploy -> verify
```

Use `needs:` to shorten the critical path where dependencies are real. A job MUST NOT list
an unrelated dependency merely to impose an ordering preference. Observe the instance's
tested `needs` limit and keep the graph understandable. Optional jobs use the approved
optional-needs behavior so pipeline creation does not fail when a rule omits them.

Jobs that need no upstream artifact set `dependencies: []` or the equivalent explicit
artifact policy. With `needs`, declare whether each needed job's artifacts are required.

### 5.3 Cancellation, timeout, and retry

- Non-mutating jobs SHOULD be `interruptible: true`.
- Auto-cancel redundant pipelines only after protected/release behavior is verified.
- Deploy, release, signing, state apply, and migration jobs are not cancelled in a way that
  can leave an ambiguous external mutation.
- Every job has a bounded timeout based on measured behavior.
- `retry` is limited to identified infrastructure failure classes or documented exit codes.
  Blanket retry of application/test/script failures is prohibited.
- A retry MUST NOT repeat a non-idempotent publish, deploy, migration, or apply without an
  idempotency and reconciliation design.

### 5.4 Mutable targets

Every job that mutates a shared environment, release identity, package version, image tag,
Helm release, or OpenTofu state uses a stable `resource_group` or a stronger platform
serialization mechanism. The key includes the target environment/state/release, not the
pipeline ID.

Serialization does not replace approvals, exact-artifact verification, or idempotency.

## 6. Reuse, includes, and CI/CD components

### 6.1 Current include compatibility

Until the component platform is approved:

- consumers use the owned common/language include contract from
  `devops/core-devops-pipeline`;
- new consumers MUST use the centrally approved immutable ref once available;
- `ref: main` remains visible migration debt with an owner and upgrade plan;
- changes to shared templates require representative consumer tests before merge; and
- a project MUST NOT copy the central template to avoid a shared fix.

Mutable branch refs, including `main`, MUST NOT be introduced in a new production pipeline.
Existing mutable consumers are migrated through tested releases, not silently rewritten in
an unrelated feature.

### 6.2 Component target

Shared pipeline behavior SHOULD move to versioned CI/CD components when the approved GitLab
instance supports the required feature set.

Each component MUST:

- have one coherent responsibility;
- define typed, described, validated `spec:inputs`;
- expose job prefix/name and stage inputs where collision or composition requires them;
- avoid undeclared custom variables as a substitute for typed inputs;
- use unique internal job/template names;
- contain no repository-specific secret, account, role, tenant, or environment default;
- pin its tooling image by immutable digest through the approved image promotion process;
- avoid depending on ambient global `before_script`, cache, services, or stages;
- minimize artifact and credential access;
- document outputs, reports, permissions, runner capabilities, and failure behavior;
- include positive, negative, composition, security, and representative consumer tests; and
- be released through SemVer with changelog, deprecation window, and rollback.

Consumers pin a full immutable commit SHA or approved full SemVer release. `main`, mutable
tags, partial versions, and `~latest` are prohibited for governed production consumers.

Third-party or GitLab-maintained components are not trusted automatically. Reva MUST audit
the source, images, token use, artifacts, network access, licensing, update ownership, and
self-managed mirroring behavior, then pin the approved mirror/revision.

### 6.3 YAML reuse

- Prefer components for cross-repository reuse.
- Use `extends` for job inheritance across included files.
- Use `!reference` only for narrow reviewed key reuse.
- YAML anchors are file-local and MUST NOT be designed as cross-include behavior.
- Deep inheritance chains, global defaults with hidden behavior, and giant shared
  `before_script` blocks are prohibited.
- Inline shell longer than three simple lines moves to a committed reviewed script or pinned
  tooling image.

All Bash scripts begin with `#!/usr/bin/env bash`, use `set -euo pipefail`, quote variables,
handle temporary files safely, propagate exit status, and pass ShellCheck. A script logs
actions, not credentials or full command environments.

## 7. Monorepos and multi-project pipelines

### 7.1 Parent-child standard

One deployable module receives one child pipeline. The root parent:

- detects affected modules;
- includes shared-library paths in consumer fan-out;
- triggers only required children;
- uses the centrally approved status-mirroring strategy; the current Reva compatibility
  contract is `strategy: depend`;
- forwards only explicitly required non-secret variables; and
- makes child failure fail the parent/MR.

Change detection uses `rules:changes:paths` with `compare_to` against the approved base.
Plain `changes` is not sufficient for new branches. For merged-results pipelines, test for
over-triggering and keep paths narrow.

Tool-native affected detection such as Turborepo, Nx, Maven reactor, Gradle, Bazel, pnpm
filters, or an explicit dependency graph MAY refine the result, but it MUST be deterministic,
tested against shared-library fan-out, and unable to skip a required security or contract
gate.

Generated child YAML is treated as executable code:

- the generator is committed, linted, tested, and deterministic;
- output is schema/CI-linted before trigger;
- variables are not assumed to interpolate in unsupported include contexts;
- artifacts are short-lived and contain no secret; and
- empty/no-change behavior is explicitly tested.

### 7.2 Cross-project pipelines

Use a multi-project trigger only for a real release/build dependency that cannot be expressed
as an immutable published artifact. Trigger chains are bounded, documented, cycle-tested,
and use explicit job-token allowlists. Prefer publishing a package, image, chart, or module
and allowing consumers to upgrade deliberately.

Module release tags are namespaced, for example `bff/v1.2.3`, and protected. Tag rules use
anchored regular expressions and have positive/negative tests.

## 8. Inputs, configuration, secrets, and identity

### 8.1 Configuration classification

| Class | Approved location |
|---|---|
| Component behavior | typed `spec:inputs` |
| Repository non-secret contract | reviewed YAML or project/group non-secret setting |
| Shared non-secret organization config | closest appropriate group setting |
| Computed job output | bounded `artifacts:reports:dotenv` or typed artifact |
| Build/runtime secret | AWS Secrets Manager or approved external store via short-lived identity |
| Cloud permission | claim-bound GitLab ID token exchanged for short-lived role credentials |
| Workload AWS permission | dedicated Kubernetes service account and IRSA/Pod Identity |

Do not use variable precedence as a hidden configuration API. Policy-controlled values that
must not be overridden belong in the policy layer. Component inputs document allowed
variation; unknown or missing required inputs fail pipeline creation.

Dotenv reports contain no secrets. They have a documented schema, bounded size and lifetime,
and explicit consumers. A job MUST NOT source an arbitrary upstream file as shell code.

### 8.2 Secret rules

- Long-lived AWS access keys in GitLab variables are prohibited.
- New secret values MUST NOT be added to repository, project, group, schedule, trigger, or
  manual-run variables when an approved short-lived/external-secret path exists.
- `masked` is log redaction, not a security boundary.
- `protected` limits ref exposure but does not give job-level least privilege.
- Variables, tokens, ID tokens, temporary AWS credentials, kubeconfig, signing material, and
  decrypted configuration MUST NOT enter cache, artifacts, dotenv, service-container logs,
  debug traces, prompts, or test fixtures.
- `CI_DEBUG_TRACE` and `CI_DEBUG_SERVICES` are prohibited on protected refs and on jobs that
  can receive credentials.
- Secret push protection and pipeline secret detection are mandatory policy controls.
- A detected secret is treated as compromised: stop exposure, rotate/revoke at the issuer,
  determine scope, remove the source/history as required, and document the incident.

### 8.3 GitLab ID tokens and AWS

Cloud jobs use `id_tokens:` with the exact intended audience. The AWS trust policy binds
stable GitLab claims to:

- the approved namespace/project identity;
- protected branch/tag/ref type;
- environment and deployment tier where supported;
- job/pipeline source as required; and
- the least-privilege role for one operation and account.

The job exchanges the token with AWS STS `AssumeRoleWithWebIdentity`. Credentials are
short-lived and remain process-local. The token and STS output are never printed, persisted,
or passed to unrelated jobs.

Plan and apply roles are separate. Build, publish, deploy, and administrative roles are
separate. A component MUST NOT accept an arbitrary role ARN that lets an untrusted consumer
choose a more privileged account; approved role mapping is claim- and policy-controlled.

Runtime service access remains IRSA/Pod Identity through Helm and AWS Secrets Manager. CI
OIDC does not justify placing workload credentials into an image or Helm values.

### 8.4 `CI_JOB_TOKEN`

`CI_JOB_TOKEN` is used only for a supported GitLab API/registry/package action that cannot use
a narrower mechanism. Every source and destination project has an explicit authorized
project/group allowlist. Cross-project use is inventoried and tested. A token MUST NOT be
forwarded to a child, artifact, container layer, remote script, or third-party host merely
for convenience.

## 9. Runner and execution security

### 9.1 Trust classes

Runner fleets are separated by:

- untrusted merge-request/build jobs;
- trusted protected-ref publish jobs;
- production deployment jobs;
- privileged/specialized hardware jobs where a reviewed exception exists; and
- architecture/capability such as Linux AMD64, ARM64, large-memory, or Kubernetes.

Sensitive runners use `run_untagged: false`, protected tags, restricted network paths, and
ephemeral single-use execution. A repository cannot select a higher-trust runner solely by
editing an unprotected pipeline.

### 9.2 Autoscaling and isolation

New fleets use the approved GitLab Runner Autoscaler/fleeting path or Kubernetes executor.
Docker Machine is migration debt and MUST NOT be selected for new fleets. Executors and
plugins are pinned, patched, capacity-limited, and observed.

Runner hosts:

- start from a hardened immutable image;
- have no ambient organization-wide cloud credentials;
- use ephemeral workspaces and secure deletion;
- restrict metadata-service access;
- apply egress controls and approved registry proxies;
- do not mount the host Docker socket into untrusted jobs;
- separate cache by trust boundary; and
- export audit, queue, utilization, and failure telemetry.

### 9.3 Container builds

Rootless BuildKit or the centrally approved non-privileged builder is the default. Privileged
Docker-in-Docker is prohibited for ordinary builds. A QEMU/multi-architecture or other
privileged exception requires:

- an isolated ephemeral fleet;
- no protected secrets for untrusted source;
- pinned builder/helper images;
- restricted network and registry scope;
- explicit capability and mount inventory;
- owner, expiry, and migration to a safer path; and
- tests proving artifacts and credentials cannot cross jobs.

Current privileged central paths are migration debt and MUST NOT be duplicated into a new
component.

## 10. Cache, artifacts, and reports

### 10.1 Cache

Cache contains only reconstructable non-secret data. It:

- keys on dependency lock/checksum files and a tool/platform prefix;
- is separated across incompatible runtimes and trust boundaries;
- has one intentional writer and pull-only readers where practical;
- uses bounded fallback keys;
- has retention and lifecycle policy;
- is never relied on for correctness; and
- is poisoned safely—validation still verifies dependency integrity.

Do not cache credentials, signing state, source with restricted data, `.env`, OpenTofu state
or plans, kubeconfig, rendered Secrets, Docker auth, or unverified build outputs.

### 10.2 Artifacts

Artifacts are explicit contracts between jobs. Each declaration identifies:

- producer and consumers;
- paths and schema;
- integrity/digest;
- access level;
- expiration;
- whether the content is sensitive;
- whether it may leave the project; and
- cleanup/retention ownership.

Use GitLab report types for JUnit, coverage, dependency/SBOM, code quality, dotenv, and
OpenTofu plan summaries where the approved instance supports them. Report generation is not
the gate; the producing command must fail on the Reva threshold.

Build once, then promote the same immutable artifact. Rebuilding for staging or production is
prohibited because it breaks provenance and review equivalence.

## 11. Testing and coverage

### 11.1 Pipeline test pyramid

Every pipeline/component change has:

1. YAML/style validation;
2. GitLab CI lint of the fully merged configuration;
3. component/template unit and negative tests;
4. representative consumer pipeline fixtures;
5. security and credential-boundary tests;
6. monorepo/change-detection tests where applicable;
7. artifact/cache/report contract tests;
8. sandbox integration for registry/cloud/cluster operations; and
9. canary rollout/rollback evidence for a central breaking change.

Tests cover push, merge request, default branch, tag, schedule, parent, child, trigger, and
manual sources that the component supports. They prove both job presence and job absence.

A bug fix includes a regression fixture that fails before the fix. A pipeline screenshot or
one successful run is not a durable test.

### 11.2 Application test gates

Every deployable module publishes machine-readable unit/integration results and the
ecosystem's coverage report. Coverage follows the company baseline:

- changed production code at least 90% line/statement coverage;
- repository floor 80% line/statement and 75% branch where supported; and
- Java at least 90% line coverage through a build-failing JaCoCo check.

The build/test tool enforces the number. GitLab's `coverage:` regex or MR widget is
presentation, not enforcement. Authorization, tenant isolation, policy, cryptography, and
other critical branches require explicit behavioral tests regardless of percentage.

Test layers include unit, integration with compatible ephemeral services, contract, security,
concurrency, resilience, and risk-based performance. Flaky tests are defects. Quarantine is
visible, owned, expiring, and cannot remove a release-critical check.

### 11.3 Pipeline and declarative coverage

Pipeline YAML is not judged by source-line coverage. Maintain a behavior matrix for shared
components and critical templates covering:

- every supported pipeline source;
- each input default, boundary, invalid value, and incompatible combination;
- rules/change-detection true and false paths;
- every optional job and dependency;
- success, expected failure, timeout, cancellation, retry, and manual approval;
- artifact/cache present, absent, expired, and unauthorized access;
- protected/unprotected ref and trusted/untrusted runner behavior;
- credential allowed/denied claim matrices;
- publish/deploy serialization and idempotency;
- component upgrade and rollback; and
- policy-injected job collision and stage behavior.

No unexplained behavior row is allowed.

## 12. Security policy and merge governance

### 12.1 Enforced policy target

Mandatory organization controls use a linked Security Policy Project and the
instance-supported pipeline execution, scan execution, and approval policies. Use the
approved `inject_policy` strategy after migration testing. Deprecated compliance-pipeline or
policy strategies MUST NOT be introduced.

Policy jobs:

- use unique `reva-policy:*` names;
- use reserved policy stages where needed and tested;
- cannot be disabled by project YAML;
- pin included configuration and tooling;
- declare failure semantics explicitly;
- have no dependency on untrusted project variables for enforced values; and
- are tested against repositories with unusual stages/workflow rules.

Mandatory policy includes, as applicable:

- secret detection and push protection;
- SAST;
- dependency/SCA and license policy;
- container and IaC/configuration scanning;
- CycloneDX SBOM;
- provenance and signature checks;
- prohibited variable/token/build-pattern checks; and
- final policy/evidence verification.

### 12.2 Merge and release governance

- Default and release branches/tags are protected.
- Direct push and force push are prohibited.
- CODEOWNERS covers `.gitlab-ci.yml`, `.gitlab/ci/**`, `ci/scripts/**`, components, policies,
  runner configuration, deployment configuration, and release metadata.
- Authors and committers do not approve their own production/security-sensitive change.
- Critical/high findings block merge unless Security approves a scoped expiring exception.
- Required pipeline and policy checks cannot be skipped through commit text or optional jobs.
- Merge trains/merged-results pipelines SHOULD be used after the complete Reva pipeline is
  tested under their diff and change-detection semantics.

## 13. Supply-chain integrity

The delivery chain MUST:

- pin tool, build, helper, service, and base images by approved immutable identity;
- use deterministic dependency installs from committed lock/checksum files;
- generate a CycloneDX SBOM for released software and images;
- record source commit, build component/tool versions, runner identity class, artifact digest,
  tests, scans, and policy results;
- sign released images and applicable artifacts with the approved keyless OIDC/cosign path;
- verify signature, issuer, and certificate identity before deployment;
- scan final images, not only source or builder stages;
- enforce approved registries, licenses, and vulnerability policy; and
- retain evidence according to audit and incident requirements.

Do not claim a high SLSA level merely because a job emits provenance. A provenance statement
created by the same mutable job on a broadly trusted runner is forgeable. Assurance claims
must match actual isolated-builder and control evidence.

Dependencies and automated updates use reviewed merge requests. A dependency bot does not
bypass test, scan, ownership, or component compatibility gates.

## 14. OpenTofu and Helm integration

### 14.1 OpenTofu

GitLab orchestrates the Reva OpenTofu gate defined by the selected `reva-opentofu` profile:

```text
fmt -> backend-free init/validate -> native tests -> tflint -> scan/policy
    -> saved plan -> cost -> protected exact-plan apply -> drift
```

- The plan role is read-only OIDC; apply uses a separate least-privilege OIDC role.
- Apply consumes the exact reviewed encrypted saved plan and never re-plans.
- One `resource_group` serializes one state unit.
- State, saved plans, and plan JSON are secret-bearing and tightly access/retention
  controlled.
- Routine `-target`, manual state mutation, and blind force-unlock are prohibited.
- Reva's normative default remains the encrypted segmented S3/KMS backend defined by the
  OpenTofu profile. GitLab-managed HTTP state requires a separate architecture/security
  decision; a generic GitLab example does not override that Reva standard.

### 14.2 Helm

GitLab orchestrates the Reva Helm gate defined by the selected `reva-helm` profile:

```text
dependency lock -> lint/schema -> semantic unit/render matrix -> kube schema
    -> policy/scan -> docs/package/SBOM/signature -> kind install/upgrade/smoke
```

The chart, dependencies, values inputs, rendered artifact, test evidence, and workload image
are immutable and digest-bound. Rendered Secrets are never unrestricted artifacts. Helm
deployment uses protected approvals, stable serialization, finite timeouts, and the approved
GitOps/CD path. A pipeline MUST NOT add `--force`, skip waits/policy, or directly edit a
production value to make an upgrade pass.

## 15. Deployment, release, and production authority

### 15.1 Promotion

Build once, scan once, sign once, and promote the same digest through environments.
Environment configuration is separately reviewed and does not rebuild the artifact.

Deploy jobs:

- run only from approved protected refs;
- use protected environments and required approvals;
- declare `environment:name`, URL where safe, and correct deployment tier;
- use the least-privilege identity for one environment;
- serialize the mutable target;
- verify artifact digest, signature, provenance, policy, and approvals;
- execute health/smoke and rollback/roll-forward evidence; and
- emit a durable sanitized deployment record.

Production and DR require explicit user authority in addition to GitLab approvals. An agent
does not press a manual job, call the pipeline API, alter environment protection, or change a
release pin without that authority.

### 15.2 Kubernetes

Prefer the approved GitOps controller for reconciliation. If GitLab requires direct
Kubernetes access, use the approved GitLab Agent integration with scoped project/group,
protected-ref, environment, and impersonation rules. Certificate-based cluster integration
is prohibited.

Cluster credentials, kubeconfig, and service-account tokens never become generic variables
or artifacts. The deploy identity cannot alter unrelated namespaces or cluster-scoped
security controls.

### 15.3 Releases and rollback

- Release tags are protected, immutable, and SemVer or the documented namespaced module
  format.
- Release creation uses the centrally approved `glab`/GitLab release path and pinned CLI
  image; deprecated release tooling is not introduced.
- Database/CRD/state migration makes rollback a domain procedure, not simply a GitLab retry.
- Rollback normally redeploys a previously verified immutable artifact through the same
  gates. It does not rewrite history or restore stale infrastructure state.
- Historical `stable-versions/v1.X.yaml` files are not edited to conceal a bad release.

## 16. Observability, distributed tracing, and audit

### 16.1 Pipeline telemetry

Platform Engineering collects:

- pipeline creation, queue, and end-to-end duration;
- job queue/run duration and retry/failure class;
- critical-path and stage wait;
- runner saturation, provisioning latency, utilization, and eviction/interruption;
- cache hit/miss and artifact transfer/storage;
- test failure/flakiness and scan latency;
- deployment frequency, lead time, change-failure rate, and recovery time; and
- cost by runner class, project group, and workload archetype.

Labels are bounded. Raw source paths, branch names with user data, commit messages, variable
values, tokens, tenant/user/resource identifiers, job logs, and error text do not become
metric labels.

### 16.2 Trace correlation

Where approved GitLab/runner/job OpenTelemetry integration exists, CI execution spans MAY be
exported to the organization collector. They:

- use stable pipeline/job/component operation names;
- correlate with GitLab pipeline ID, job ID, project ID, commit SHA, and deployment ID only
  under the approved data-classification/retention policy;
- exclude secret values, ID tokens, temporary credentials, source content, plan/state,
  rendered Secrets, test customer data, and raw command output;
- are asynchronous and bounded; and
- do not change a gate outcome if telemetry export fails.

CI execution traces are separate from application distributed traces. A service pipeline
MUST test the language/framework's W3C `traceparent`/`tracestate` contract through ingress,
PEP/PDP, service, messaging/workflow, and downstream boundaries where the change affects it.
A trace or deployment ID MAY be linked as sanitized release evidence, but CI must never
fabricate an application parent span or treat a GitLab job ID as W3C trace context.

Audit events for policy, approval, protected settings, runner registration, token scope,
variables, deployment, and release are streamed to the approved SIEM. Sampled traces do not
replace durable audit.

## 17. Reliability, performance, and cost

### 17.1 Reliability

- Pipeline configuration creation failure is a release blocker.
- Critical central components maintain an availability objective and tested rollback to the
  previous release.
- Component/catalog changes use canary consumers before estate rollout.
- Runner capacity has headroom, disruption behavior, and failover by trust/capability class.
- External registries, scanners, and package repositories have bounded timeouts and defined
  fail-open/fail-closed decisions. Security gates fail closed unless an approved incident
  exception says otherwise.
- Scheduled pipelines have owners and alert when they stop running.
- Manual jobs have expiry/eligibility behavior and cannot apply a plan/artifact after its
  attestation expires.

### 17.2 Performance method

For a material pipeline/component/runner change, record before and after:

- representative repository archetypes and revisions;
- pipeline and critical-path p50/p95/p99;
- queue and runner provisioning duration;
- cache hit ratio and artifact transfer volume;
- CPU, memory, disk, network, and concurrency;
- test/shard distribution and slowest jobs;
- failures, retries, cancellations, and flakiness; and
- storage/compute/network cost.

A change SHOULD NOT regress the controlled p95 critical path by more than 10% without
explicit explanation and approval. Faster execution achieved by skipping tests, refresh,
scans, signature checks, cleanup, or deployment verification is not an improvement.

Use `rules:changes:compare_to`, parent-child pipelines, `needs`, interruptible jobs,
lockfile-keyed distributed cache, bounded artifacts, test sharding, and right-sized runners
based on evidence. Do not add capacity before identifying unnecessary work.

### 17.3 Cost

Runner fleets, caches, artifacts, registries, logs, SBOMs, provenance, and telemetry all have
retention and cost owners. Track cost per successful verified pipeline and per runner class.
Use spot/preemptible capacity only for restart-safe non-production jobs with scoped retry.
Protected publish/deploy capacity prioritizes predictability and isolation over the lowest
unit price.

## 18. Required verification

The repository MUST expose deterministic wrapper commands through Make, Task, or reviewed
scripts. The logical GitLab gate includes:

1. YAML format and `yamllint`;
2. ShellCheck and helper-script lint/type checks;
3. local schema validation;
4. GitLab `/ci/lint` validation of the fully merged configuration;
5. workflow and rules behavior matrix;
6. component/template unit, negative, and representative consumer tests;
7. monorepo affected/fan-out tests;
8. artifact/cache/report contract tests;
9. secret, SAST, dependency/license, container, and IaC/config scans;
10. SBOM, provenance, and signature generation/verification;
11. sandbox registry/cloud/cluster integration where applicable;
12. performance/cost comparison for a material change; and
13. canary pipeline plus rollback for a shared component/policy/runner release.

The exact commands come from the owning repository and approved central pipeline. A generic
`gitlab-ci-local` run MAY provide fast feedback but is community tooling and cannot replace
server-side merged CI lint or policy execution.

A validator report is not proof that mandatory jobs executed. Verification inspects the
fully expanded/merged pipeline and the resulting required-job evidence.

## 19. Prohibited patterns

Reva pipelines MUST NOT:

1. copy central job logic into consumer repositories;
2. introduce `ref: main`, `@~latest`, partial versions, or mutable production includes;
3. hide business logic in a giant root `.gitlab-ci.yml`;
4. rely on `only/except`, plain monorepo `changes`, or duplicate branch/MR pipelines;
5. inline long shell, `curl | sh`, `eval`, or source an untrusted dotenv/script;
6. shadow `CI_*` or use ambiguous variable precedence as an API;
7. store long-lived cloud keys or treat masking as secret security;
8. print environments, tokens, ID-token claims, STS output, kubeconfig, or secrets;
9. use privileged DinD, host Docker socket, or high-trust runners by default;
10. use unscoped `CI_JOB_TOKEN` for cross-project access;
11. cache credentials or pass all upstream artifacts implicitly;
12. mark required tests, scans, coverage, policy, signing, or deployment verification
    optional;
13. blanket-retry a script/deploy/apply or ignore a failed cleanup;
14. rebuild an artifact separately for production;
15. publish unsigned/unscanned mutable images or charts;
16. re-plan OpenTofu at apply or expose state/plan JSON;
17. force Helm upgrades, expose rendered Secrets, or bypass GitOps;
18. use certificate-based Kubernetes integration;
19. deploy to production/DR or rewrite release pins without explicit authority; or
20. silently edit governing Cursor/standards files while fixing a pipeline.

## 20. Standard change workflow

1. Read the nearest `AGENTS.md`, this baseline, profile knowledge, repository README/ADRs,
   root/recursive CI includes, scripts, manifests, CODEOWNERS, and central template/component
   revision.
2. Resolve the actual Git root and inspect status. Preserve unrelated work.
3. Expand the current pipeline model: sources, workflow, includes, inputs/variables, stages,
   jobs/rules/needs, artifacts/cache, identities, runners, policies, environments, and
   downstream triggers.
4. Identify every affected independent repository and consumer. Classify the change as local
   compatible, shared additive, deprecating, or breaking.
5. Define positive and negative behavior matrix cases before editing.
6. Change the owning component/template/script and consumer contract together; avoid
   unrelated refactors.
7. Run fast YAML/script/rules/component tests, then server CI lint and the full approved
   verification wrapper.
8. Inspect the merged pipeline and final diff for skipped jobs, secrets, mutable refs,
   authority expansion, runner/artifact changes, and production/release impact.
9. Canary shared changes on representative repositories; publish a SemVer release only after
   evidence passes.
10. Report exact checks, results, artifacts, skipped/CI-only gates, rollout, rollback, and
    remaining debt.

Do not commit, push, publish, trigger a mutation job, deploy, change protected settings, or
touch production/release state unless the user explicitly grants that scope.

## 21. Definition of Done

- [ ] The owning repository, central template/component, consumers, and rollout order are
      known.
- [ ] Current Reva compatibility and target controls are not conflated.
- [ ] Root CI remains thin; files, jobs, templates, inputs, variables, environments, and
      scripts follow naming standards.
- [ ] Workflow prevents duplicates and handles every supported pipeline source.
- [ ] Rules, DAG, child/multi-project triggers, serialization, timeout, cancellation, and
      retry behavior are tested.
- [ ] Includes/components/tooling images are immutable and reproducible.
- [ ] No plaintext or long-lived secret, broad job token, ambient cloud identity, or
      privilege escalation was introduced.
- [ ] OIDC claims/roles, protected refs/environments, separation of duties, and explicit
      production authority are preserved.
- [ ] Runner isolation, rootless build, cache, artifact, report, and cleanup contracts pass.
- [ ] Language tests and build-failing coverage meet the company profile.
- [ ] Mandatory security scans, SBOM, provenance, signature, policy, and merge gates are
      present and non-optional.
- [ ] OpenTofu exact-plan and Helm immutable-render/delivery contracts remain valid.
- [ ] Application W3C distributed tracing and redacted pipeline telemetry are verified where
      affected.
- [ ] Performance/cost evidence exists for a material topology/component/runner change.
- [ ] Production, DR, release history, and protected settings were not changed without
      separate authority.
- [ ] The final report distinguishes passed, failed, skipped, unavailable, and CI-only
      checks.

## 22. Standards improvement

This profile inherits the organization self-improvement process. Repeated review findings,
component drift, skipped jobs, credential incidents, runner failures, excessive pipeline
cost, rule-activation defects, or recurring authoring work SHOULD become an evidence-backed
proposal to the central standards source.

The proposal identifies:

- observation and frequency;
- affected repositories/profiles and current/target state;
- exact component, rule, skill, knowledge, validator, or hard gate to change;
- compatibility, security, token/context, runner, and production impact;
- behavior tests and canary consumers;
- owner, review date, rollout, deprecation, rollback, and success measures.

An agent MUST NOT silently rewrite baselines, rules, skills, manifests, policies, hooks,
ignore files, component pins, or protected GitLab settings. Reusable learning is reviewed,
versioned, validated, and distributed through ordinary merge requests.

## 23. Primary references

- [GitLab CI/CD YAML](https://docs.gitlab.com/ci/yaml/)
- [GitLab CI/CD components](https://docs.gitlab.com/ci/components/)
- [GitLab CI/CD inputs](https://docs.gitlab.com/ci/inputs/)
- [GitLab pipeline execution policies](https://docs.gitlab.com/user/application_security/policies/pipeline_execution_policies/)
- [GitLab scan execution policies](https://docs.gitlab.com/user/application_security/policies/scan_execution_policies/)
- [GitLab ID tokens](https://docs.gitlab.com/ci/secrets/id_token_authentication/)
- [GitLab AWS OIDC](https://docs.gitlab.com/ci/cloud_services/aws/)
- [GitLab CI job token](https://docs.gitlab.com/ci/jobs/ci_job_token/)
- [GitLab Runner autoscaling](https://docs.gitlab.com/runner/executors/docker_autoscaler/)
- [GitLab Kubernetes Agent CI/CD workflow](https://docs.gitlab.com/user/clusters/agent/ci_cd_workflow/)
- [`../OpenTofu/baseline.md`](../OpenTofu/baseline.md)
- [`../Helm/baseline.md`](../Helm/baseline.md)
