# ADR 0015: Deploy to Cloud Run from GitHub Actions with Workload Identity Federation

- **Status:** Accepted
- **Date:** 2026-11-03

## Context

Dev deploys first ran as `gcloud builds submit` from a laptop. GitHub Actions minutes are free while the repository is public, and a pipeline can enforce "deploy only when all checks and tests are green". Long-lived service-account keys in GitHub would be a standing leak risk.

## Decision

Deploy the dev API and web to Cloud Run (asia-south1) from `.github/workflows/deploy-dev.yml` on push to `main` or manual dispatch.

- **No keys.** GitHub authenticates through Workload Identity Federation (pool `github`, provider `github-smartnutri`) and impersonates the `github-deployer` service account.
- **Restricted trust.** The provider's attribute condition allows only repository id `1443053989` and owner id `263351064` (immutable, so a rename or recreate cannot match), `refs/heads/main`, the workflow file `deploy-dev.yml@refs/heads/main`, and `push` / `workflow_dispatch` events. The IAM binding is on the repository id. The workflow never uses `pull_request` or `pull_request_target`.
- **Branch protection on `main` is REQUIRED** (pull request, required checks, no force push, no bypass). Anyone who can change the workflow on `main` can deploy to dev, so this is part of the trust boundary, not a nicety.
- **Least privilege.** `github-deployer` has `run.developer` on the two dev services only (no project-level Cloud Run role), `artifactregistry.writer` on the `smartnutri` repository only, and `iam.serviceAccountUser` on the two runtime service accounts only. The API runs as `smartnutri-api-dev` (secret accessor on its three secrets only); the web runs as `smartnutri-web-dev` with no roles.
- **Gate.** The deploy jobs depend on the existing `api`, `web` and `security` workflows, reused through `workflow_call`.
- **Safe rollout.** Each revision is deployed by image digest with no traffic and a `c<sha7>` tag, smoke-tested on the tag URL, then given traffic.
- Every action is pinned to a full commit SHA.

## Consequences

- The Cloud Run services are created once by `scripts/setup-github-deploy.sh` (placeholder image) so the deployer needs only service-level roles.
- Deploys need no laptop and no stored credentials; pushing to `main` is the deploy trigger.
- Revisit when the repository goes private: Actions minutes are then billed, and we return to local deploys (the earlier rule). WIF can stay as a fallback.
- Public workflow logs must never print secrets; secrets are only referenced by Secret Manager name.
