---
name: api-contract
description: Use after any change to apps/api routes or Pydantic schemas, when the generated Dart (smartnutri_api) or TypeScript (@smartnutri/api-client) client is out of date, when CI reports contract drift, or when coordinating an API change across the Android and web apps.
---

# Keeping the API contract and both clients in sync

`packages/api-contract/openapi.json` is the contract between `apps/api` and both clients. The Dart client (`packages/api-contract/dart`, used by `apps/app`) and the TypeScript client (`packages/api-contract/ts`, used by `apps/web`) are **generated** from it. Nobody edits them by hand.

## Steps

1. **Make the API change first,** with tests passing (`api-endpoint` skill). Every route needs an explicit, stable `operation_id`.
2. **Regenerate:**
   ```bash
   just contract
   ```
   This exports `openapi.json` from the FastAPI app (`apps/api/scripts/export_openapi.py`) without starting a server. It then regenerates `dart/` with swagger_parser and `ts/` with openapi-typescript (types used by openapi-fetch), and formats both.
3. **Review the diff** of `packages/api-contract/`:
   - Added fields or routes are fine.
   - **Removed or renamed fields, routes or `operation_id`s are breaking.** Update both clients in the same PR, or keep the old field with a deprecation.
   - Watch for accidental `additionalProperties`, `Any` or untyped `dict`. Fix the Pydantic schema, not the generated code.
4. **Compile both clients against it:**
   - Android: `cd apps/app && flutter analyze`
   - Web: `cd apps/web && pnpm tsc --noEmit`
   Fix call sites in the apps, never the generated files.
5. **Fixtures:**
   - If response shapes for products or analysis changed, update `packages/test-fixtures` so the files still validate against the schema.
   - If verdicts changed, follow the `scoring-rule` skill.
6. **Strings:** new error or reason codes get keys in `packages/i18n/messages/{en,hi,mr}.json`, then run `just i18n`.
7. **Commit** the API change, `openapi.json`, `dart/` and `ts/` together: `chore(contract): regenerate clients for <feature>`.
8. **Parity hand-off:** list the client work this unblocks. `flutter-builder` and `web-builder` can then run in parallel.

## CI drift check

CI runs `just contract` and then `git diff --exit-code packages/api-contract`. If it fails, run `just contract` locally and commit the result. Don't edit the files to make the diff go away.

## Pitfalls

- Running the generators with different versions locally and in CI. Use the pinned versions (swagger_parser 1.45, openapi-typescript 7.13, openapi-fetch 0.17) from `just setup`.
- Forgetting `operation_id`: FastAPI generates unstable names, and client method names churn.
- Returning SQLAlchemy objects or `dict` from routes. Always declare `response_model`.
- Public (no-auth) routes must be visible as public in the schema, so both clients call them without a token.
