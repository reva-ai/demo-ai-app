# demo-ai-app Cursor environment

This repository contains a generated Reva Cursor context for `development/demo-ai-app`.

- Root `AGENTS.md` and root rules own organization, security, delivery, and quality policy.
- Module `.cursor` overlays contain only module architecture, contracts, testing guidance,
  and module-qualified skills.
- Root hooks and an empty-by-default MCP configuration are the only tool authority.
- The context is progressive and non-breaking; it does not modify application source, build
  manifests, runtime configuration, deployment values, or release mappings.

Start with `AGENTS.md`, then load the applicable immutable baseline snapshots listed in
`.cursor/knowledge/standards/manifest.json`, the nearest module profile, and the narrowest
matching skill.
Validate changes with `node .cursor/tools/validate-cursor-config.mjs`.
