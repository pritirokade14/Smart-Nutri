# ADR 0015: Deploy to Cloud Run from GitHub Actions with Workload Identity Federation

- **Status:** Accepted
- **Date:** 2026-11-03

## Context

Dev deploys first ran as `gcloud builds submit` from a laptop. GitHub Actions minutes are free while the repository is public, and a pipeline can enforce "deploy only when all checks and tests are green". Long-lived service-account keys in GitHub would be a standing leak risk.

## Decision

Deploy the dev API and web to Cloud Run (asia-south1) from `.github/workflows/deploy-dev.yml` on push to `main` or manual dispatch.

- **No keys.** GitHub authenticates through Workload Identity Federation (pool `github`, provider `github-smartnutri`) and impersonates the `github-deployer` service account.
- **Restricted trust.** The provider's attribute condition allows only repository `pritirokade14/Smart-Nutri` on `refs/heads/main`. The workflow never uses `pull_request` or `pull_request_target`.
- **Least privilege.** `github-deployer` has `run.admin` (project), `artifactregistry.writer` on the `smartnutri` repository only, and `iam.serviceAccountUser` on the two runtime service accounts only. The API runs as `smartnutri-api-dev` (secret accessor on its three secrets only); the web runs as `smartnutri-web-dev` with no roles.
- **Gate.** The deploy jobs depend on the existing `api` and `web` workflows, reused through `workflow_call`.
- Every action is pinned to a full commit SHA.

## Consequences

- Deploys need no laptop and no stored credentials; pushing to `main` is the deploy trigger.
- Anyone who can push to `main` can deploy to dev, so branch protection on `main` matters.
- Revisit when the repository goes private: Actions minutes are then billed, and we return to local deploys (the earlier rule). WIF can stay as a fallback.
- Public workflow logs must never print secrets; secrets are only referenced by Secret Manager name.
