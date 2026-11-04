# SmartNutri AI

**Scan any packaged food and see whether it's right for each person in your family**: diabetes, blood pressure, kids, allergies, Jain or vegan diets. Then log what you actually eat. In English, हिंदी and मराठी, with voice.

> Status: all 9 v1 plans are code complete, merged to `main` and deployed to dev. Launch steps (prod, Play Store, reviews) are tracked in [CONTEXT.md](CONTEXT.md) and `docs/launch/RELEASE_CHECKLIST.md`.

## Platforms

| Platform | Built with | Notes |
|---|---|---|
| **Android app** | Flutter | Camera barcode and label scanning, voice |
| **Web app** | Next.js 16 | Same features as Android (full parity), plus public pages Google can index: home, "How we score", product pages |

Both clients use the same FastAPI backend, the same rules engine and the same Supabase account.

## Why

- India has ~101M people with diabetes and ~136M with prediabetes.
- Most shoppers read only the expiry date on a pack, and "sugar-free" or "no added sugar" claims often hide maltodextrin or glucose syrup.
- Barcode-only apps miss most Indian products. SmartNutri also reads the label photo, so it works on any pack.

## What v1 does

| Feature | Detail |
|---|---|
| Scan | Barcode first, label photo as fallback (AI extraction that you confirm) |
| Family profiles | Separate conditions, allergies, diet and goal for each member |
| Verdict for each member | `OK` / `Caution` / `Unknown` / `Avoid`, with reasons |
| Rules engine | Nutri-Score 2023, "high in" warnings, allergen synonyms, Jain and vegan checks, hidden sugars |
| Claim checker | "Sugar-free? It contains maltodextrin." |
| Scan-to-log | Daily and weekly sugar, salt and protein for each member |
| Explanations and voice | Questions and answers in en, hi and mr, via the CallMissed STT, LLM and TTS APIs |

Not medical advice. Thresholds are pending clinician review.

## Repository layout

```
apps/api/                FastAPI + rules engine + Alembic   → apps/api/README.md
apps/app/                Flutter Android app                → apps/app/README.md
apps/web/                Next.js web app                    → apps/web/README.md
packages/api-contract/   openapi.json + generated Dart and TypeScript clients
packages/i18n/           all user-facing strings (en, hi, mr)
packages/design-tokens/  colours, spacing, verdict colours → Dart + CSS
packages/test-fixtures/  shared products and expected verdicts
supabase/                Auth config, hooks, email templates
docs/                    Product, architecture, ADRs, research, specs, plans
```

## Quick start

Prerequisites:
- [uv](https://docs.astral.sh/uv/) (installs Python 3.13)
- Node 24 + pnpm
- Flutter stable (upgrade before Plan 3: `flutter upgrade`)
- Docker (for local Supabase)
- `just`: `brew install just`
- `pre-commit`: `uv tool install pre-commit`
- `gitleaks` (already installed on the main dev machine): `brew install gitleaks`

```bash
just setup      # install deps for api, web, packages; install git hooks
just test       # API, Android and web tests
just dev        # local Supabase + API + web app
just android    # run the Android app on an emulator or device
```

Full setup (Supabase project, CallMissed key, Google OAuth, Android signing) is added in the plans. See `docs/superpowers/plans/`.

## Documentation

- [Product](docs/PRODUCT.md): users, scope, roadmap
- [Architecture](docs/ARCHITECTURE.md): system design and data flow
- [Decisions (ADRs)](docs/adr/)
- [Research](docs/research/): users, competitors, tech stack, regulation
- [v1 design spec](docs/superpowers/specs/2026-11-02-smartnutri-v1-design.md)
- [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)

## Credits

Product data partly from [Open Food Facts](https://world.openfoodfacts.org) (ODbL).
