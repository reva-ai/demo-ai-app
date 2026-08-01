<!--
GENERATED REVA STANDARD SNAPSHOT — DO NOT EDIT IN THIS REPOSITORY
Source: KarthikRamesh/reva-standards/.cursor/knowledge/cursor-operating-model.md
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

# Cursor operating model

## What each surface is for

| Surface | Use | Do not use it for |
|---|---|---|
| Team Rule | Small enforced organization invariant across projects | Language globs or long procedures |
| `AGENTS.md` | Human-readable repository contract, commands, architecture | Large reference manual |
| Project Rule | Focused persistent/scoped behavior | Multi-step runbook |
| Skill | On-demand procedure with progressive disclosure | Permanent safety invariant |
| Custom subagent | Bounded delegated specialist or independent review | Extra authority or sole approval of its own work |
| Command | Short reusable prompt/entry point | Duplicated skill body |
| Knowledge | Detailed committed facts/checklists | Automatic native memory |
| Hook | Local agent-loop guardrail/audit | Server-side CI enforcement |
| `.cursorignore` | Hard block on sensitive content | Index-performance tuning alone |
| `.cursorindexingignore` | Exclude noisy/generated content from embeddings | Protect a secret |
| MCP | Approved external tools/resources | Unreviewed access or authorization bypass |
| Memory | Personal convenience/candidate learning | Shared organization policy |

## Profile composition

Select:

1. `reva-org`;
2. at most one language profile;
3. zero or more compatible framework/data profiles; and
4. zero or more evidence-backed infrastructure/delivery/testing profiles; and
5. one repository-local profile.

At least one language, infrastructure, delivery, or testing profile is required.
Infrastructure, delivery, and testing profiles are orthogonal: they may stand alone in a
dedicated repository or accompany a language chain when the same repository owns those
artifacts.

Examples:

```text
reva-org -> reva-java -> reva-springboot -> reva-r2dbc + reva-gitlab -> service-local
reva-org -> reva-java -> reva-springboot -> reva-mongodb + reva-gitlab -> service-local
reva-org -> reva-python -> reva-fastapi + reva-gitlab -> service-local
reva-org -> reva-go -> reva-gin + reva-gitlab -> service-local
reva-org -> reva-node -> reva-fastify + reva-gitlab -> service-local
reva-org -> reva-node -> reva-nextjs + reva-gitlab -> web-application-local
reva-org -> reva-opentofu + reva-gitlab -> infrastructure-local
reva-org -> reva-helm + reva-gitlab -> chart-local
reva-org -> reva-katalon + reva-gitlab -> test-automation-local
reva-org -> reva-gitlab -> delivery-local
reva-org -> reva-java + reva-katalon + reva-gitlab -> test-automation-local
```

The profile manifest lists source artifacts and parent inheritance. It is a Reva distribution
manifest, not a native Cursor configuration file. Every governed target is attested from its
required tracked root GitLab pipeline, so every materialized target chain includes
`reva-gitlab`; the standalone example represents a central delivery repository.

## Activation budget

- Organization: at most two small always-applied project rules in a generated repository.
- Technology profiles: glob-attached rules only; no copy of the organization invariant.
- Long workflows: skills.
- Bounded parallel/specialist review: custom subagents with inherited model and parent
  verification.
- Detailed architecture: knowledge.
- Commands: unique profile-qualified names because commands from multi-root workspaces are not
  scoped.

The profile validator rejects unsupported frontmatter, missing files, and naming collisions.
Platform rollout additionally measures always-on tokens and verifies actual activation in the
pinned Cursor build.

## Rule format compatibility

The source standard uses `.cursor/rules/<name>/RULE.md`. The pinned Cursor release must show
each rule in Settings and the used-rules indicator.

If a verified product defect prevents folder discovery:

1. keep `RULE.md` as the reviewed source;
2. have the distribution process generate one flat `.mdc` per source rule;
3. record the Cursor version and exception;
4. do not materialize both source and compatibility form; and
5. remove the exception after the pinned build passes discovery tests.

Hand-maintained duplicate formats are prohibited.

## Context selection

Cursor should start with the nearest `AGENTS.md` and applicable rules. It reads knowledge only
when the task requires it and uses `@file`/explicit file paths for authoritative source.

For a material change:

1. locate the repository root;
2. read applicable profile manifests;
3. inspect service code/tests/build/CI;
4. load only relevant knowledge;
5. create a bounded plan;
6. implement and verify; and
7. report evidence and remaining risk.

Avoid attaching whole repositories, generated trees, or large research documents when a
specific baseline/knowledge section is enough.

## Multi-root behavior

- Prefer one repo or a domain-scoped workspace of at most five materialized service roots.
- Treat each root as an independent Git repository.
- Rules from a root remain scoped to that root's matching files.
- Skills, custom subagents, and commands from all roots may be visible. The materializer
  service-qualifies their emitted names.
- The same always rule in many roots may load many times. The five-root limit bounds that cost;
  Team Rules provide hard organization enforcement but do not justify opening the full estate.
- Creating a rule through Cursor UI may target the first workspace root; inspect the path.

## Debugging context

When a rule or skill appears not to work:

1. check the pinned Cursor version/update channel;
2. open Cursor Settings and confirm the artifact is discovered;
3. inspect the used-rules indicator for the current request;
4. validate frontmatter and the matching glob/path;
5. reference a matching file explicitly;
6. temporarily test a rule as always-applied only in a local branch;
7. check nested and multi-root placement;
8. check duplicate names/copies; and
9. record a product defect/exception rather than silently adding another copy.

## Cloud/background agents

Cloud/background agents get only the repository content, configured environment, approved
network/tool access, and injected team controls. They do not inherit a developer's unstored
context.

Repository instructions therefore include deterministic setup and verification commands.
Credentials are provisioned by the platform, never stored in rules/skills. Destructive,
production, or release operations remain outside background-agent authority unless a dedicated
reviewed workflow grants them.
