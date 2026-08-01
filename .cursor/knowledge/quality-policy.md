# Quality and coverage adoption

For new or materially modified executable production code, add direct behavior tests designed
to achieve at least 95% line/statement coverage of the changed executable code.
This is an organization adoption target. It does not assert that `demo-ai-app` already has a
repository-wide 95% gate or changed-line measurement.

Rules:

- preserve and pass every existing configured threshold;
- never lower, exclude, rename, or annotate production code to improve a percentage;
- test security, tenant, validation, error, timeout, cancellation, retry, and fallback paths
  regardless of aggregate coverage;
- use integration/contract tests for persistence, protocols, generated schemas, and deployment
  behavior that mocks cannot prove; and
- report actual measured coverage and every unmeasured gap.

Helm, Terraform/OpenTofu, GitLab CI, Docker, and Istio use build-failing behavior matrices for
branches, policy decisions, rendering/planning, failures, upgrades, rollbacks, and contracts.
