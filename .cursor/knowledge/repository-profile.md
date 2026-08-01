# Repository profile

## Purpose

Billing-support agentic app hosted on **Render**. Every LLM and MCP hop goes through your **cloud-hosted Kong**; a Kong plugin you write there calls **Reva PDP** for allow/deny. This repo does **not** contain a Kong plugin or talk to Reva directly.

## Selected profiles

- `reva-org`
- `reva-python`
- `reva-fastapi`
- `reva-agentic`
- `reva-gitlab`

## Commands

- Setup: `python -m pip install -r requirements.txt`

## Boundaries

- Treat every module in the module index as an ownership boundary.
- Verify cross-module imports and contracts before moving code or changing shared types.
- Preserve the current build graph and deployable-unit boundaries.
- Repository facts are evidence-derived but must be rechecked when manifests or CI change.
