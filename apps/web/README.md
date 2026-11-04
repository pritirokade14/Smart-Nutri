# SmartNutri Web App (Next.js)

The SmartNutri AI web app: the same features as the Android app (scan, a verdict for each family member, food log, voice), plus public pages: home, "How we score", and product pages.

> Built (Next.js 16) and merged to `main`. Layout and rules are in [AGENTS.md](AGENTS.md).

## Setup

Requirements: Node 24 and pnpm (the repo is a pnpm workspace).

```bash
just setup      # installs workspace deps, generates the API client and tokens
cp apps/web/.env.example apps/web/.env.local   # fill in the NEXT_PUBLIC_* values
just web        # dev server at http://localhost:3000
```

## Environment

Only public values go here, because anything named `NEXT_PUBLIC_*` is sent to the browser:

```
NEXT_PUBLIC_SUPABASE_URL=https://<project>.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=<sb_publishable_... key>
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_POSTHOG_KEY=
```

## Test

```bash
just test-web   # Vitest
just e2e        # Playwright
```

See [AGENTS.md](AGENTS.md) for the layout and rules: server vs client components, public vs app routes, the generated client, i18n and tokens.
