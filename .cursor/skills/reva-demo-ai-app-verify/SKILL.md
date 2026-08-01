---
name: reva-demo-ai-app-verify
description: "Verify a demo-ai-app change against Reva contracts and repository gates. Use before handoff."
---

# Verify a change

1. Review the diff for scope, generated files, secrets, auth/tenant behavior, compatibility, and module boundaries.
2. Run module-targeted checks, then the configured root format/lint/type/test/coverage/build gates.
3. Confirm new behavior tests target at least 95% changed executable code where measurable; report actual evidence.
4. Run Cursor validators when context changed.
5. Report commands/results, skipped checks, CI-only checks, and remaining risk without claiming unrun success.
