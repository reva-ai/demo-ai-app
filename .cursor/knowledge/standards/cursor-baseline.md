<!--
GENERATED REVA STANDARD SNAPSHOT — DO NOT EDIT IN THIS REPOSITORY
Source: KarthikRamesh/reva-standards/cursor-baseline.md
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

# Reva Cursor Engineering Baseline

| Field | Value |
|---|---|
| Status | Normative organization baseline |
| Applies to | Cursor IDE, Cursor Agent, Cursor CLI, background/cloud agents, and repository-owned Cursor configuration used for Reva engineering |
| Extends | [`baseline.md`](baseline.md) |
| Research input | [`Cursor.md`](Cursor.md), which remains non-normative |
| Configuration owner | Reva Platform Engineering with Security Engineering review |
| Review trigger | Pinned Cursor upgrade, rules/skills/hooks format change, material security finding, or at least every six months |

This baseline defines how Reva turns the engineering standards into version-controlled Cursor
context for more than 300 service, web-application, delivery, infrastructure, chart, and
test-automation repositories.
It governs the files that guide Cursor; it does not replace the applicable engineering
baselines or the CI, architecture, security, and release controls that enforce them.

## 1. Outcomes and non-goals

The Reva Cursor configuration **MUST**:

- give an agent the minimum authoritative context needed for the files being changed;
- make organization, language, framework, data-technology, infrastructure, delivery, testing,
  and repository instructions composable;
- work when a developer opens one governed repository and remain usable in a domain-scoped
  multi-root workspace;
- preserve Reva authorization, tenant isolation, reactive/async behavior, observability,
  testing, and delivery invariants;
- expose repeatable development and verification workflows as skills and commands;
- keep team knowledge reviewable in Git rather than in an individual's private memory;
- protect sensitive files from indexing and model access;
- make configuration drift detectable; and
- keep every self-improvement proposal human-reviewed and reversible.

This baseline does **not** claim that prompt context can enforce a standard. Cursor rules,
`AGENTS.md`, skills, commands, and memories are probabilistic guidance. CI, branch protection,
architecture fitness tests, dependency policies, secret scanning, and production controls are
the authoritative enforcement layer.

## 2. Authority and precedence

Cursor and its agents apply instructions in this Reva order:

1. law, contract, data-residency obligations, and Reva security policy;
2. enforced Cursor Team/Enterprise policy;
3. [`baseline.md`](baseline.md) and this Cursor baseline;
4. the applicable language, infrastructure, delivery, or testing baseline and its Cursor
   profile;
5. the applicable framework/data-technology baseline and its Cursor profile;
6. repository-local architecture, commands, and approved ADRs;
7. task-specific user instructions that remain inside the allowed security and production
   authority; and
8. personal Cursor preferences and memories.

More-specific instructions may strengthen or specialize a broader requirement. They **MUST
NOT** silently weaken authorization, tenant isolation, secret handling, data protection,
coverage, trace propagation, release governance, or a required hard gate.

When instructions conflict, Cursor **MUST**:

1. stop the affected change;
2. identify the conflicting files/rules;
3. use the stricter safe behavior temporarily;
4. ask for a decision from the appropriate owner; and
5. resolve the conflict through a reviewed standards/ADR change rather than an improvised
   local exception.

An explicit prompt does not authorize disabling PEP/PDP checks, exposing secrets, editing
production/release history, force-pushing `main`, or bypassing a required CI gate.

## 3. Composable repository model

Every governed repository receives a generated composition of these profiles:

| Layer | Source | Examples |
|---|---|---|
| Organization | repository root pack in this standards repository | Reva security, tenancy, delivery, Cursor governance |
| Language | `Java/`, `Python/`, `Golang/`, or `Node/` | toolchain, naming, language tests, logging |
| Framework/data | `SpringBoot/`, `R2DBC/`, `MongoDB/`, `FastAPI/`, `GIN/`, `GorillaMux/`, `CHI/`, `Fastify/`, or `NextJS/` | adapter lifecycle, middleware, persistence, rendering/caching, framework testing |
| Infrastructure | `OpenTofu/` or `Helm/` | state/chart contracts, policy, delivery, drift, runtime safety |
| Delivery | `GitLab/` | pipeline architecture, identity, runners, policy, evidence, promotion, and operations |
| Testing | `Katalon/` | test architecture, artifacts, execution, evidence, and quality |
| Repository | maintained in the target repository | purpose, modules, ports, owners, commands, local ADRs |

The profile source is intentionally layered. A framework pack contains only the delta from its
language pack. Language, infrastructure, delivery, and testing packs contain only their delta
from the organization pack. A repository may select orthogonal infrastructure, delivery, or
testing packs alongside one language chain when tracked evidence proves those technologies
are maintained in that repository. A materialized configuration **MUST** include every
selected inheritance chain and must not copy the same always-applied rule under several
names.

Every governed Reva target has the repository contract's tracked root GitLab pipeline.
Write-mode attestation therefore selects the orthogonal `reva-gitlab` profile for every
materialized target; a missing root pipeline fails rather than producing a non-deliverable
pack. A central delivery repository may select GitLab without a language profile.

The delta rule applies to materialized rules, skills, subagents, commands, knowledge, and
ignore patterns. Source-profile `AGENTS.md` files in this standards repository are detailed
standalone review checklists, as requested for each profile; the composer **MUST NOT**
concatenate them. It renders one compact service `AGENTS.md` from declared service metadata
that is digest-bound to the materialized pack and selected knowledge links. Repository
path/slug are verified against the effective Reva GitLab fetch and push origins. Profiles are
derived from structured dependency declarations rather than comments. Build/lock/workspace,
root CI, recursively referenced canonical local CI, and command facts are verified from
regular tracked `HEAD` files. Owner and runtime remain declared facts until a separately
governed central inventory attests them and must not be described as machine-verified.

Each source profile contains:

```text
<profile>/
  AGENTS.md
  baseline.md
  .cursor/
    reva-profile.json
    agents/<subagent>.md
    rules/<rule>/RULE.md
    skills/<skill>/SKILL.md
    commands/<command>.md
    knowledge/<profile>-profile.md
  .cursorignore
  .cursorindexingignore
```

The organization source profile additionally owns hooks, MCP defaults, schemas, templates,
release records, runtime/CI pins, ownership policy, and validation tooling.

## 4. Required materialized repository layout

Every Reva repository managed through this Cursor pack **MUST** contain:

```text
<governed-repository>/
  AGENTS.md
  .cursor/
    rules/
    skills/
    agents/
    commands/
    knowledge/
      standards/
      repository-profile.md
      repository-context-proposals.md
    hooks/
    hooks.json
    reva-profile.json
    mcp.json
    releases/current.json
    schemas/reva-cursor-release.schema.json
    schemas/reva-materialized-profile.schema.json
    tools/validate-materialized-cursor-pack.mjs
  .cursorignore
  .cursorindexingignore
```

The materialized `AGENTS.md` includes organization, selected profile, and service-local
instructions without becoming a copy of the full standards library. It points to detailed
knowledge files and records exact repository commands. Selected baseline snapshots under
`knowledge/standards/` are immutable generated evidence. The repository profile and context
proposal file are explicitly repository-owned and excluded from generated-content hashes.

Repositories **MUST NOT** introduce a new `.cursorrules` file. It is a legacy unscoped format.
Existing `.cursorrules` content is migrated into scoped rules or `AGENTS.md` and then removed.

In a materialized Cursor service, `AGENTS.md` is the only agent-instruction source of truth.
Unmanaged `CLAUDE.md`, nested `AGENTS.md`, alternate `.agents`, `.claude`, or `.codex`
configuration trees, nested `.cursor` trees, and nested Cursor ignore files are prohibited.
Compatibility mirrors MAY be introduced only through a future schema-governed inventory that
hashes and validates them. This closes implicit Cursor discovery paths that otherwise bypass the
reviewed pack.

Verified repository commands are deliberately canonical and deterministic. Every command is
one direct invocation with no environment prefix, shell wrapper, chain, background process,
comment, pipe, redirection, substitution, grouping, external path, or alternate build/config
file. The executable is an approved bare tool or a tracked executable wrapper. Its goal/task/
subcommand/script must match the declared role, use the root manifest, and contain no
unattested second operation. Install commands are lock-bound (`npm ci`, frozen pnpm/Yarn/uv,
synced Poetry, hashed requirements, or approved build-tool dependency resolution); coverage
and integration commands must state their coverage/integration semantics.

## 5. `AGENTS.md` standard

The root `AGENTS.md` is the fast, human-readable operating contract. It **MUST** state:

- repository purpose and ownership;
- instruction precedence and applicable profile IDs;
- module/dependency boundaries;
- canonical setup, build, test, lint, coverage, and local-run commands;
- security, authorization, tenancy, secrets, and data-handling invariants;
- logging, tracing, metrics, health, and shutdown expectations;
- CI, container, Helm, and release constraints;
- dangerous actions that require confirmation;
- Definition of Done; and
- links to knowledge, runbooks, ADRs, and the source standard revision.

Instructions are concrete and command-oriented. Avoid aspirations such as “write clean code”
without defining the observable rule or gate.

In a materialized repository, nested `AGENTS.md` files are prohibited because they create an
unhashed alternate instruction path. Module- or adapter-specific guidance belongs in the
inventory-governed repository profile, scoped rules, knowledge, or an approved future schema
extension.

Keep `AGENTS.md` reviewable. Large reference material belongs in `.cursor/knowledge/`; long
procedures belong in skills.

## 6. Project Rules standard

### 6.1 Source format

New Reva rule sources use the folder form:

```text
.cursor/rules/<lowercase-hyphen-name>/RULE.md
```

Only these frontmatter fields are permitted:

```yaml
---
description: "One sentence describing when the rule is relevant"
globs: **/*.java, **/pom.xml
alwaysApply: false
---
```

`description`, `globs`, and `alwaysApply` are the complete supported Reva schema. Unsupported
fields such as `priority`, `tags`, `owner`, or invented activation modes are prohibited.

The pinned Cursor release **MUST** be tested to confirm that folder-form `RULE.md` files load in
Settings and appear in the used-rules indicator. If the approved release has the documented
folder-discovery defect, the distribution tool may emit flat `.mdc` compatibility files from
the same source. A repository **MUST NOT** commit both forms simultaneously because duplicate
rules waste context and can create conflicting behavior.

### 6.2 Rule selection

Use rules as follows:

| Requirement | Rule type |
|---|---|
| Tiny organization invariant needed in every session | `alwaysApply: true` |
| Language/framework instruction activated by source files | `globs` with `alwaysApply: false` |
| Guidance chosen from its description | `description` with no globs and `alwaysApply: false` |
| Rare instruction used only by explicit request | Manual rule or, preferably, a skill/command |

Always-applied content is a token tax. A materialized repository SHOULD have no more than two
small always-applied project rules: the organization invariant and the governed
self-improvement rule. Organization security requirements SHOULD also be installed as enforced
Team Rules where the Cursor plan supports them.

Reva enforces the representative activation and word limits in
[`.cursor/knowledge/context-budget.md`](.cursor/knowledge/context-budget.md). A broad glob is a
reviewed context-budget change, not a convenience edit.

Every rule **MUST**:

- be focused on one stable concern;
- state observable instructions and prohibited behavior;
- use the narrowest correct globs;
- remain below 500 lines, with a much smaller normal target;
- point to knowledge or a baseline for detail rather than paste it;
- contain no secrets, environment-specific credentials, or volatile service inventory; and
- be validated after a pinned Cursor upgrade.

## 7. Knowledge and memory standard

`.cursor/knowledge/` is Reva's committed knowledge layer. Cursor does not treat this folder as
magical memory; rules, skills, commands, or the agent explicitly read these files when needed.

Knowledge files contain:

- stable architecture and vocabulary;
- repository/module maps;
- canonical commands and verified tool versions;
- approved patterns and counterexamples;
- operational constraints and dependency ownership;
- migration debt clearly labeled as non-standard;
- links to source code, CI, Helm, architecture decisions, and runbooks; and
- review checklists too detailed for an always-on rule.

Facts with a material security, version, or deployment consequence are verified from the live
repository or platform source before use. Generated catalogs and private Cursor memories are
navigation aids, never the final authority.

Cursor Memories are per-user and may be unavailable under Privacy Mode. A memory **MUST NOT**
be relied upon for organization policy, architecture, a secret, production state, or a shared
decision. When a useful memory should become team knowledge, the agent proposes a reviewed
change to the appropriate knowledge/rule file.

## 8. Skills standard

Procedural work belongs in:

```text
.cursor/skills/<lowercase-hyphen-name>/SKILL.md
```

Every skill **MUST** have:

```yaml
---
name: reva-example-skill
description: "What the skill accomplishes and when Cursor should use it."
---
```

The `name` exactly matches the folder. Optional `paths` narrow applicability.
`disable-model-invocation: true` is used only when a skill must be explicitly invoked; its
manual-only effect is documented.

Skills use progressive disclosure:

1. route from a precise description;
2. give a bounded ordered procedure;
3. read only the required baseline/knowledge/reference;
4. inspect the repository before selecting commands or files;
5. verify the result proportionally to risk; and
6. report evidence, remaining debt, and any unexecuted gate.

A skill **MUST NOT** grant permission, bypass a hook, weaken a rule, hide a failing test, or
perform a production/release action without the authority required by the backend baseline.
Skills do not embed tokens or MCP credentials.

Skill names are organization-prefixed (`reva-...`) and unique across profile layers so they
remain unambiguous in multi-root workspaces.

## 9. Commands standard

Reusable team prompts live in `.cursor/commands/*.md`. Commands are short entry points for
repeatable workflows such as planning, verification, security review, and onboarding.

Commands:

- use unique profile-qualified names;
- identify the applicable skill when a procedure already exists;
- require inspection before edits;
- require evidence rather than self-attestation;
- never contain secrets or environment-specific identifiers; and
- remain safe if surfaced without scoping in a multi-root workspace.

A complex or reference-heavy command is converted to a skill. Commands and skills may coexist;
they must not contain divergent copies of the same workflow.

## 9.1 Custom subagents

Repository-defined specialists live at:

```text
.cursor/agents/<lowercase-hyphen-name>.md
```

Reva permits only this reviewed frontmatter:

```yaml
---
name: reva-service-specialist
description: "The bounded task and evidence for which this specialist should be delegated."
model: inherit
readonly: true
---
```

The source name matches the filename. Source-pack names are unique across profiles. The
materializer qualifies emitted rule, skill, command, and subagent names with the verified
service slug because Cursor surfaces skills, commands, and agents from every multi-root
workspace and identical names are ambiguous.

A custom subagent:

- declares `readonly: true`, receives one concrete, bounded task, and loads the minimum
  relevant context;
- reads the same `AGENTS.md`, baselines, rules, and knowledge as the parent;
- never expands tool, repository, production, release, data, or secret authority;
- does not commit, push, deploy, mutate an environment, or bypass a guardrail; an authorized
  parent agent or human performs any required mutation after reviewing the subagent's evidence;
- returns paths/lines, commands/evidence, uncertainty, and unrun checks;
- cannot approve its own implementation as the only reviewer; and
- is integrated and verified by the parent agent.

`model: inherit` avoids stale provider-specific slugs; the Team/Enterprise model allowlist is
the hard control. Subagent availability, model inheritance, discovery, and the Task tool
**MUST** be tested on the exact pinned IDE, CLI, and cloud-agent builds. If unavailable, the
parent performs the same workflow sequentially; it does not silently skip the review.

## 10. Hooks, CLI permissions, and hard local guardrails

Project hooks live in `.cursor/hooks.json`; scripts live in `.cursor/hooks/`. They are a local
agent-loop guardrail and audit surface, not a replacement for server-side CI or Enterprise
policy.

The organization pack provides:

- `beforeShellExecution` protection for destructive Git/filesystem commands and
  production-impacting tools;
- `beforeReadFile` defense in depth for sensitive paths; and
- a `stop` review when agent-context files changed.

The source pack denies destructive, publishing, infrastructure-mutating, and environment-dump
commands inside the agent loop. An authorized operator runs such a command manually after
review. Reva does not rely on `permission: "ask"` until the exact pinned Cursor build proves
that it reliably pauses every supported local, remote, sandboxed, and cloud execution path;
that evidence and any change from deny to ask belong in the pack release record.

Hook programs:

- accept exactly one JSON object on stdin;
- emit exactly one valid JSON object on stdout;
- construct JSON with a serializer rather than string interpolation;
- have a bounded timeout;
- fail safely on malformed input;
- do not log payloads that could contain secrets;
- resolve workspace paths from hook input where supported; and
- have deterministic fixture tests.

The reviewed hook implementation uses Node.js. The managed developer image **MUST** expose the
centrally approved Node runtime on `PATH`, and rollout preflight **MUST** execute the hook
fixtures from a representative Java, Python, Go, and Node repository. If a supported developer
platform cannot provide that runtime, Platform Engineering generates and tests an equivalent
signed executable before enabling `failClosed`; it does not leave a hook that blocks all work
because its interpreter is missing.

`.cursorignore` remains the primary hard block for sensitive files because a hook may not run
for every editor-buffer or product path. Hooks are supplementary and Cursor Hooks are treated
as beta until the pinned version's behavior is validated.

The shell hook denies direct references to sensitive paths regardless of the reader or
interpreter, but a textual command hook cannot prove that dynamically constructed paths are
safe. Managed sandbox/filesystem policy, least-privilege credentials, DLP, and server-side
secret scanning remain the hard boundary; the baseline never presents regex matching as an
anti-obfuscation control.

Project `.cursor/cli.json` permissions MAY be generated for a controlled Cursor CLI job. They
are not enabled in the generic pack because an incomplete project allowlist can override a
developer's global configuration or accidentally deny all commands. A CI agent uses an
explicit least-privilege file dedicated to its job.

## 11. MCP governance

The committed default `.cursor/mcp.json` contains no servers. Adding a project MCP server is a
security-sensitive architecture change and requires:

- a named owner and business purpose;
- server/tool allowlisting;
- least-privilege scopes and read/write classification;
- authentication outside Git;
- tenant and user authorization through the normal Reva PEP/PDP path;
- prompt-injection and data-exfiltration analysis;
- audit logging and revocation;
- timeouts, bounded payloads, and failure behavior;
- review of data residency and vendor retention; and
- an approved change to the Enterprise marketplace/MCP allowlist where applicable.

A skill may explain how to call an approved MCP tool; it never grants access by itself.

The generic materialized pack and validator intentionally reject a non-empty project MCP
configuration. Approval is implemented as a reviewed organization/repository profile and pack
release—or as an Enterprise-managed connection—not as a hand edit to generated `mcp.json`.
Until that governed profile exists, no non-empty project MCP is compliant.

## 12. Ignore and indexing policy

Every repository commits both files:

- `.cursorignore` — hard access/indexing exclusion for secrets and sensitive artifacts;
- `.cursorindexingignore` — performance exclusion for generated, cached, vendored, or binary
  content that an agent may still read explicitly when permitted.

`.cursorignore` includes actual `.env` variants, private keys/certificates, credential files,
Terraform state, kubeconfig, local secret overlays, database dumps containing customer data,
and equivalent sensitive artifacts. Safe examples such as `.env.example` remain readable.

`.cursorindexingignore` includes build output, package caches, coverage artifacts, generated
API/client code where the source schema is authoritative, logs, profiler output, dependency
trees, and large local datasets.

Do not use `.cursorignore` as a performance workaround when `.cursorindexingignore` is
sufficient; the hard ignore prevents Agent, Tab, Inline Edit, and references from reading a
file. Ignore changes receive security review and tests demonstrating that required source
files remain visible.

## 13. Reva engineering behavior in Cursor

Before changing code, Cursor **MUST**:

1. read the applicable `AGENTS.md`, rules, and profile manifest;
2. identify the repository boundary and check Git status;
3. locate the relevant baseline and repository-local architecture;
4. inspect current code, build, tests, CI, Docker, and Helm contracts as needed;
5. state every repository/file group for multi-repository work; and
6. identify security, tenant, API, data, and rollout risk.

During implementation, Cursor **MUST**:

- preserve approved dependency direction and naming;
- reuse Reva shared libraries and PEP integrations;
- keep authorization fail-closed and canonical resource mapping identical between PEP and
  application logic;
- avoid secrets, sensitive telemetry, and high-cardinality tenant dimensions;
- propagate W3C trace context and request cancellation;
- keep async/reactive paths non-blocking and bounded;
- add tests with the change; and
- avoid unrelated rewrites.

Before declaring completion, Cursor **MUST**:

- inspect the final diff;
- run the smallest meaningful checks plus every required release gate available locally;
- report commands and outcomes accurately;
- distinguish “not run” from “passed”;
- identify migration debt without presenting it as accepted practice; and
- leave committing, pushing, production, and release actions within the user's granted scope.

Coverage follows [`baseline.md`](baseline.md): changed production code at least 90%
line/statement coverage; repository floor 80% line/statement and 75% branch where supported;
Java additionally meets the 90% JaCoCo line gate. Cursor context **MUST NOT** invent a different
numeric policy.

## 14. Multi-root and estate-scale behavior

The normal developer workspace is a single repository or a domain-scoped multi-root workspace
with at most five materialized service roots. A larger task is split into bounded workspaces or
uses the approved read-only estate index. Opening the entire 300+ repository estate is
prohibited.

For a multi-root workspace:

- each root retains its own `.cursor` and `AGENTS.md`;
- glob-scoped rules apply only to their root;
- skills from every root may be discovered;
- commands are effectively unscoped and therefore use unique Reva-qualified names;
- identical always-applied rules can be loaded repeatedly; and
- agents still respect independent Git histories and commits.

The generated per-repository organization rules remain present so a service opened alone is
safe. On Team/Enterprise, the non-negotiable invariant is also enforced as a Team Rule; this is
an intentional hard-control duplicate and the workspace budget includes it. Do not add a
third workspace copy. The approved five-root maximum bounds project always-rule duplication at
ten rules and 2,250 body words before the separately measured Team Rule/`AGENTS.md` context.

Indexing/context budgets are measured on representative single-root and five-root workspaces.
A standards change that materially increases always-on tokens or indexed files includes
before/after evidence.

## 15. Self-improvement

Cursor may identify an improvement when:

- the same correction occurs at least three times;
- CI repeatedly exposes a missing rule or skill step;
- a runtime/framework upgrade invalidates instructions;
- an incident reveals a missing safety constraint;
- developers repeatedly need the same verified procedure; or
- rules conflict, do not activate, or consume excessive context.

The agent **MUST NOT** silently rewrite its own governing files. It creates a proposal with:

- observation and frequency;
- concrete evidence and affected repositories/profiles;
- proposed target file and exact behavior;
- conflict/token/security analysis;
- hard-gate impact;
- migration and rollback;
- owner and review date; and
- validation proving that Cursor loads the result.

Accepted improvements use a normal reviewed merge request. Rule changes run the pack validator,
update the improvement log, and—when organization-wide—produce generated update PRs rather than
direct pushes across the estate.

Private Memories may suggest a candidate but never count as approval or shared evidence.

## 16. Distribution across governed repositories

Platform Engineering owns a deterministic sync/generation process that:

1. selects the organization plus every structured-evidence-backed language, framework/data,
   infrastructure, delivery, and testing profile;
2. validates their inheritance chain and unique IDs;
3. merges rules, skills, subagents, commands, knowledge, ignore fragments, hooks, and
   templates;
4. renders a repository-specific `AGENTS.md` and knowledge profile;
5. records the standards revision and selected profiles;
6. fails on collisions, unsupported frontmatter, missing files, or duplicate always rules;
7. produces a reviewable diff;
8. never overwrites hand-owned repository context without an explicit merge policy; and
9. rolls changes out through automated merge requests with normal CI and ownership review.

Write mode also rejects Git index concealment (`assume-unchanged`, `skip-worktree`, or sparse
entries), ignored or untracked tool configuration, Git replacement refs/grafts, custom clean
filters or working-tree encodings on attested inputs, directory symlinks, multiple fetch/push
URLs, non-SSH/HTTPS origins, origin URL rewrites away from Reva GitLab, and unsupported GitLab
CI include syntax. GitLab local includes use explicit block mappings so their complete
recursive closure can be hashed. Flow/JSON, shorthand, tagged, anchored, aliased, merged,
explicit-key, or escaped-key include representations must be migrated before attestation.

New repositories start compliant from their template. Existing repositories migrate in
waves—reference services first, then one domain at a time. Direct mass pushes to 300
repositories are prohibited.

Remote rules, submodules, packages, or symlinks may be evaluated, but none replaces the
committed generated pack until reliability, auditability, offline behavior, and rollback have
been proven on Reva's pinned Cursor build.

### 16.1 Release and activation gate

The source of truth is [`.cursor/releases/current.json`](.cursor/releases/current.json),
validated against the release schema and executable validator. It records:

- pack status/version and owner;
- exact observed and approved IDE, CLI, and cloud-agent builds;
- the exact Node.js hook runtime plus per-platform evidence;
- the selected rule format;
- the immutable approved standards Git revision;
- required discovery, security, context, multi-root, and rollback evidence; and
- rollout state and prior approved revision.

`draft` is fail-closed for service rollout. The composer accepts
`--allow-draft-release` only for isolated staging/test output, records that exception, and the
normal materialized service validator rejects it without the same explicit test-only flag.
Approval uses a realizable two-object Git contract. `approval.standardsRevision` names the
clean, immutable commit containing every governed source byte. A later clean commit changes
only `.cursor/releases/current.json` to record approval, exact tested build/runtime pins,
passed supported-platform evidence, required GitLab validation, and CODEOWNER review. The
composer verifies ancestry and that release-record-only diff before materialization. This
avoids the impossible requirement for a commit to contain its own hash. It also disables and
rejects replacement objects/grafts, rejects local Git filters, and compares every source byte
consumed during composition with the raw blob in the exact release-record commit, so a
concurrent save cannot enter an approved pack. The materialized validator revalidates the
complete copied release record—required evidence, approval identity/time/pins/platforms,
rollout, and rollback—not merely its artifact digest. An observed local version or a
caller-supplied label is not approval.

## 17. Validation and hard enforcement

The standards repository validator **MUST** check:

- all expected profile manifests and inheritance paths;
- unique profile, rule, skill, and command IDs;
- unique subagent IDs and supported subagent frontmatter;
- JSON validity;
- `RULE.md` frontmatter fields, activation, and line limit;
- `SKILL.md` name/folder equality, description, and optional paths;
- required `AGENTS.md`, baseline, knowledge, command, and ignore files;
- relative links, final newlines, and trailing whitespace;
- no committed `.cursorrules`;
- no duplicate always-applied organization rule; and
- hook configuration plus deterministic hook fixtures.
- the complete release-record structure, evidence relationships, rollout state, rollback
  contract, and raw Git provenance for an approved checkout.

Service CI additionally enforces the actual engineering outcomes:

| Concern | Cursor guidance | Required hard evidence |
|---|---|---|
| Formatting/style | scoped rule and verify skill | formatter/linter required job |
| Type/static correctness | applicable profile rule | compiler/type checker, configuration validation, schema validation, or static analysis |
| Dependency direction | architecture knowledge | ArchUnit, import-linter, dependency-cruiser/boundaries, Go package tests, module tests, or test-core boundaries |
| Tests/coverage | test rule and verify skill | build-failing profile thresholds, declarative matrix evidence, or tested shared-library coverage |
| Authorization/tenancy | organization + profile rules | route inventory, allow/deny/failure, cross-tenant tests |
| API/configuration compatibility | framework/tool knowledge | OpenAPI, plan-policy, values-schema, rendered-manifest, or test-artifact compatibility job |
| Secrets/dependencies/images | ignore/rules/review skill | secret, SAST, SCA, SBOM, license, and image gates |
| Runtime behavior | applicable profile skill | load, cancellation, probe, graceful-shutdown, chart-install, drift, or KRE execution tests |
| Delivery policy | GitLab profile | CI lint/component tests, policy evaluation, least-privilege identity, immutable artifact/provenance, and promotion controls |

A Cursor-generated green narrative is never accepted instead of machine-verifiable evidence.

## 18. Enterprise administration

For the managed Cursor estate, administrators SHOULD enforce:

- Privacy Mode and the approved data-use posture;
- SSO/SAML/SCIM and role-based administration;
- model allowlisting and approved update channel/version;
- sandbox, network, Git, and auto-run policy;
- MCP/plugin marketplace allowlisting;
- organization Team Rules and Team Hooks where supported;
- `.cursor` directory protection and ignore policy;
- audit-log export to the approved SIEM; and
- Bugbot/review policy with the same security baseline.

Team Rules are administered in the Cursor dashboard and are not made effective merely by
committing a template file. The standards repository keeps the reviewed source text and rollout
instructions.

## 19. Definition of Done for a Cursor profile change

- [ ] The profile extends the correct parent and references its normative baseline.
- [ ] `AGENTS.md` is concrete, scoped, and consistent with broader instructions.
- [ ] Rules are focused, correctly activated, below 500 lines, and use only supported fields.
- [ ] Skills have unique matching names, precise descriptions, bounded procedures, and
      proportional verification.
- [ ] Custom subagents have unique matching names, `model: inherit`, `readonly: true`, bounded
      authority, and a parent-verification contract.
- [ ] Commands are unique and do not duplicate skill bodies.
- [ ] Knowledge distinguishes verified current state, approved target, and migration debt.
- [ ] Ignore patterns protect secrets without hiding required source.
- [ ] Hooks emit valid JSON, pass fixtures, and are not represented as server-side enforcement.
- [ ] The profile validator, Markdown checks, and link checks pass.
- [ ] The pinned Cursor build lists and activates the expected rules/skills.
- [ ] Hard CI/architecture/security gates exist for every requirement described as mandatory.
- [ ] The standards revision, owner, rollout, and rollback are documented.

## 20. Exceptions and changes

An exception follows [`baseline.md`](baseline.md) and additionally records:

- affected Cursor version, profile, repositories, and configuration files;
- whether the failure is rule discovery, tool behavior, indexing, hook, permission, or skill
  behavior;
- compensating hard controls;
- security/data exposure;
- expiry and owner; and
- tested exit/migration path.

Cursor changes rapidly. No release note automatically changes the Reva standard. Platform
Engineering validates the candidate build against rule discovery, nested instructions, skills,
commands, hooks, ignores, MCP policy, multi-root behavior, privacy, and rollback before
changing the approved version.

The release record pins the IDE, CLI, and cloud-agent builds separately. An observed local
version is not an approved organization pin, and a missing cloud-agent build identifier blocks
rollout rather than being inferred from the IDE or CLI version.

## 21. Primary references

- [Cursor Rules](https://cursor.com/docs/rules)
- [Cursor Agent Skills](https://cursor.com/docs/skills)
- [Cursor Subagents](https://cursor.com/docs/subagents)
- [Cursor Hooks](https://cursor.com/docs/hooks)
- [Cursor Commands](https://docs.cursor.com/en/agent/chat/commands)
- [Cursor CLI permissions](https://docs.cursor.com/cli/reference/permissions)
- [Cursor multi-root workspaces](https://cursor.com/changelog/04-24-26)
- [AGENTS.md open standard](https://agents.md/)
- [`Cursor.md`](Cursor.md) — Reva research and scale analysis
- [`baseline.md`](baseline.md) — Reva engineering baseline
- [`Node/NextJS/baseline.md`](Node/NextJS/baseline.md) — Next.js framework baseline
- [`GitLab/baseline.md`](GitLab/baseline.md) — GitLab delivery baseline
