# Reva organization standard

Repository: `development/demo-ai-app`

Standards source: `KarthikRamesh/reva-standards`

Standards revision: `740fdff52ba1d093d36652347f64850c51ce9700`

The complete selected baseline snapshots and core organization knowledge are digest-recorded in
`.cursor/knowledge/standards/manifest.json`. Load the organization/Cursor baselines plus the
narrowest selected language, framework, data, delivery, or infrastructure baseline before a
material change; do not infer a standard from this summary alone.

Reva is a policy and guardrail platform for human and non-human identities. The authorization
hot path is PEP to PDP, with PIP-owned attributes and PAP-owned policy administration. Agentic
flows additionally preserve IBAC intent checks between hops where integrated.

Cross-repository invariants:

- reuse shared language libraries and approved PEP/PDP integration;
- propagate tenant and identity context without unsafe defaults;
- use structured redacted logging, metrics, and W3C traces;
- source secrets through Secrets Manager and workload identity;
- prefer reactive, async, cancellation-aware request paths;
- preserve CI, Docker, Helm, health, shutdown, and release contracts; and
- verify assumptions from tracked source, architecture decisions, schemas, and delivery files.
