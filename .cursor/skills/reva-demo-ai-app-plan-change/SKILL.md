---
name: reva-demo-ai-app-plan-change
description: "Plan a bounded, compatible change in demo-ai-app. Use before multi-file, module, persistence, security, or contract work."
---

# Plan a change

1. Identify the goal, owning module, callers, contracts, data stores, auth/tenant path, and delivery artifacts.
2. Inspect current implementation and tests; do not plan from repository names alone.
3. Separate required edits from optional debt. Preserve existing behavior unless migration is authorized.
4. Define targeted tests, 95% changed-code evidence, full gates, rollback, and risks.
5. List exact files and commands before implementation.
