<!--
GENERATED REVA STANDARD SNAPSHOT — DO NOT EDIT IN THIS REPOSITORY
Source: KarthikRamesh/reva-standards/.cursor/knowledge/context-budget.md
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

# Cursor context budget

Cursor context is a finite engineering resource. Reva keeps mandatory invariants small and
activates detailed guidance only when the file or task needs it.

## Enforced source-pack budget

- Exactly two organization rules are always applied.
- Their combined rule bodies are at most 450 whitespace-delimited words.
- A representative production file in every supported profile chain activates at most eight
  project rules and 2,400 rule-body words.
- A representative test file activates at most ten project rules and 3,200 rule-body words.
- One materialized pack contains at most one language, only its compatible framework/data
  profiles, and any orthogonal infrastructure/delivery/testing profiles proven by tracked
  repository evidence.
- A supported domain multi-root workspace contains at most five materialized service roots,
  bounding duplicated project always rules at ten and 2,250 body words.

These are regression limits, not targets to fill. A smaller applicable set is preferred.
Team Rules and `AGENTS.md` still consume context outside this project-rule measurement, so
rollout qualification must inspect Cursor's actual used-rules indicator and context use.

## Authoring choices

1. Put short non-negotiable safety invariants in the two always-applied rules.
2. Attach language, infrastructure, delivery, and testing engineering rules to their ordinary
   source.
3. Scope framework rules to adapters, routes, configuration, or framework-owned files.
4. Scope data rules to repositories, mappings, migrations, queries, and data configuration.
5. Scope test rules to tests, contracts, and build/test configuration; scope Katalon rules to
   its authored artifacts and shared JVM test-core code.
6. Scope GitLab rules to the root pipeline, local include closure, component/template sources,
   policy definitions, and delivery scripts rather than all application source.
7. Use description-selected rules, knowledge, and skills for detailed workflows that should
   not load on every edit.
8. Link to a baseline rather than duplicating its explanations.

Security is not optional when a narrow glob does not match. The organization invariant,
`AGENTS.md`, hard CI controls, and the applicable baseline remain authoritative. Engineers
must explicitly load the security review skill for a security-, tenant-, identity-, data-, or
boundary-sensitive change.

## Measurement and change control

The source-pack validator evaluates the committed representative paths and fails above the
limits. The materialized-pack validator independently measures the emitted configuration.
Before approving a Cursor release, Platform Engineering also records:

- IDE, CLI, and cloud-agent activation results;
- the actual rules shown as used for representative production and test tasks;
- relevant Team Rule and `AGENTS.md` contribution;
- task-quality and omission checks on reference services; and
- the before/after context measurement for any broadening change.

Adding a broad source glob requires evidence that all profile fixtures remain within budget.
Do not evade a failure by deleting essential controls; consolidate overlap, narrow activation,
or move procedural detail into knowledge and skills.
