# ADR 0001: Monorepo layout

- **Status:** Accepted (revised 2026-11-02 for ADR 0008: Flutter for Android, Next.js for web)
- **Date:** 2026-11-02

## Context

The project has:
- a Flutter Android app
- a Next.js web app
- a Python API
- Supabase config
- shared contracts, translations, design tokens and test fixtures
- specs, plans and ADRs that span all of them

A small team is building v1 in about 15 days, with every feature on both clients. API changes, both clients and the shared packages usually change in the same PR.

## Decision

Use one repository with this layout:

```
apps/api/                FastAPI (feature-based) + rules engine + Alembic
apps/app/                Flutter Android app
apps/web/                Next.js 16 web app
packages/api-contract/   openapi.json + generated Dart and TypeScript clients
packages/i18n/           single source of UI strings (en, hi, mr)
packages/design-tokens/  verdict/grade colours, spacing, type → Dart + CSS
packages/test-fixtures/  shared products + expected verdicts
supabase/                auth config, hooks, email templates (no schema)
docs/  .claude/  .github/
```

Tooling:
- **JavaScript side:** a pnpm workspace (`pnpm-workspace.yaml`) covers `apps/web` and the JS packages. pnpm handles linking; no Nx or Turborepo.
- **Python:** `uv` in `apps/api`.
- **Dart:** `pubspec` path dependencies. Use Melos or pub workspaces only if a second Dart package beyond the generated client appears.
- **One entry point:** a root `justfile` runs everything (`just setup`, `just dev`, `just test`, `just contract`, `just android`).
- **Pre-commit hooks:** gitleaks, ruff, Biome, `dart format`.

## Consequences

- One PR can change the API, both clients and the shared packages together. Contract drift is caught in CI.
- CI uses path filters (`apps/api/**`, `apps/app/**`, `apps/web/**`, `packages/**`), so each pipeline runs only when needed.
- Three toolchains (uv, Flutter, pnpm) must be installed. `just` hides most of the difference.
- Access control is per repository. If outside contributors arrive later (for example a dietitian-dashboard vendor), consider splitting that app out.
