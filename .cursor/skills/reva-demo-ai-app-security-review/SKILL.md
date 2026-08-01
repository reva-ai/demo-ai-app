---
name: reva-demo-ai-app-security-review
description: "Review demo-ai-app authorization, tenancy, secrets, data, and observability. Use for security-sensitive changes."
---

# Security review

1. Trace identity, tenant, resource, action, policy, input, persistence, downstream, and output boundaries.
2. Verify approved PEP/PDP integration and fail-closed behavior.
3. Check secrets, IAM, encryption, logging/tracing/metrics redaction, retries, timeouts, cancellation, and safe errors.
4. Require allow, deny, dependency-failure, wrong/missing tenant, malformed, and leakage regression tests as applicable.
5. Report findings by severity with precise paths and evidence. Do not mutate production or weaken controls.
