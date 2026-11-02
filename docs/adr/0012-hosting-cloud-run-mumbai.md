# ADR 0012: Host API and web on Cloud Run in Mumbai

- **Status:** Accepted
- **Date:** 2026-11-02

## Context

We need hosting for:
- the FastAPI service
- the Next.js web app, with server rendering for public SEO pages and client rendering for the logged-in app

The Android app ships through Google Play. Data lives in Supabase Mumbai (ADR 0003). Options for the web app were Firebase Hosting (static only, which no longer fits a server-rendered Next.js app), Vercel (excellent DX, but the Hobby plan forbids commercial use and Pro is per-seat), and Cloud Run.

## Decision

Run **both the API and the web app on Google Cloud Run in `asia-south1` (Mumbai)**, in one Google Cloud project:

| Service | Image | Prod settings |
|---|---|---|
| `smartnutri-api` | Python 3.13 + uv | `min-instances=1`, secrets from Secret Manager |
| `smartnutri-web` | Next.js `output: "standalone"`, Node 24 | `min-instances=1`, public env only, ISR cache for public pages |

Each service has a matching `-dev` version, which scales to zero.

- Custom domain: the web app on the apex domain, the API on `api.` (mapped via Cloud Run domain mapping or a load balancer).
- Deploys go from GitHub Actions with Workload Identity Federation (no long-lived keys).

## Consequences

- Both services run next to the Mumbai database, with one bill and one IAM model. It is cheap at low traffic (free tier, then pay per use).
- Keeping one instance warm per service costs a little but removes cold starts at launch.
- The ISR cache lives per instance. If it is inconsistent across instances, add a CDN (Cloud CDN) in front of the public pages.
- Firebase Hosting is no longer needed, so the docs referencing it are updated.
