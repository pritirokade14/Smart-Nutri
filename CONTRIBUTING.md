# Contributing

## Workflow

1. Branch off `v1-rebuild` (after v1 ships, off `main`): `feat/<area>-<short-name>`, e.g. `feat/scan-label-confirm`.
2. Pick the next unchecked task in the active plan (`docs/superpowers/plans/`). Write the failing test first.
3. **Build vertical slices:**
   1. The API endpoint and its tests.
   2. Run `just contract` and commit `packages/api-contract` (`openapi.json` plus both generated clients).
   3. The Android screen (`apps/app`) and the web page (`apps/web`) together, against the regenerated clients.
   4. Shared fixtures (`packages/test-fixtures`) pass on all three.
4. Keep commits small. Use Conventional Commits with a scope:
   - `feat(scoring): …`, `fix(app): …`, `feat(web): …`, `chore(api): …`, `chore(contract): …`, `docs: …`, `test(api): …`
   - Scopes: `scoring`, `api`, `app`, `web`, `contract`, `i18n`, `tokens`, `fixtures`, `supabase`, `docs`, `ci`.
5. Open a PR into the parent branch and fill in the checklist below.

## Branch protection and required reviews

- `main` and `v1-rebuild` are protected: no direct pushes, CI must pass, and at least one approval is needed.
- `.github/CODEOWNERS` requires an owner's review for:
  - `apps/api/app/scoring/`
  - `apps/api/app/prompts/`
  - `packages/test-fixtures/`
  - Verdict, allergy and analysis UI in `apps/app` and `apps/web`
- Before requesting that review, run the `nutrition-safety-reviewer` agent and paste its verdict into the PR.

## PR checklist

- [ ] Tests added or updated, and passing locally (`just test`)
- [ ] Lint clean (`just lint`)
- [ ] **Parity:** the feature works on API + Android + web, or the PR says which slice is still pending
- [ ] **Contract:** if the API schema changed, `just contract` was run and `packages/api-contract` is committed (CI fails on drift)
- [ ] **Strings:** new user-facing text is in `packages/i18n/messages/{en,hi,mr}.json` (all three), and `just i18n` was run
- [ ] **Design tokens:** colours and spacing come from `packages/design-tokens`; nothing is hard-coded
- [ ] **Fixtures:** if a verdict can change, `packages/test-fixtures` expectations are updated and explained
- [ ] No hand-edited generated code (clients, ARB, tokens)
- [ ] No secrets, real user data or label photos with personal info. The pre-commit gitleaks check passed.
- [ ] If scoring, allergen, diet, claim or prompt logic changed: `nutrition-safety-reviewer` verdict attached, with threshold changes explained
- [ ] If a significant decision was made: ADR added in `docs/adr/`

## Pre-commit hooks

`just setup` installs them. They run ruff (Python), `dart format` (Android app), Biome (web) and **gitleaks**. Don't bypass them with `--no-verify`. If a hook is wrong, fix the hook config in a separate PR.

## Code style

- **Python:** ruff, type hints everywhere, frozen dataclasses or Pydantic models, no bare `except`.
- **Dart:** `flutter_lints`, Riverpod providers, feature-first folders, no business logic in widgets.
- **TypeScript:** Biome, strict mode, Server Components by default, client components only where needed.
- **Docs:** short sentences, plain English. Link to sources for any health number.
