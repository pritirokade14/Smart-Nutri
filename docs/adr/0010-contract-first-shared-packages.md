# ADR 0010: Contract-first API and shared packages

- **Status:** Accepted
- **Date:** 2026-11-02

## Context

Two clients (Flutter Android and Next.js web) must behave identically against one API. The prototype failed through silent mismatches: the profile field names differed, and the goal was never sent. Hand-writing two API clients, two sets of strings and two colour schemes would make that worse.

## Decision

Four shared packages in `packages/`:

1. **`api-contract/`**
   - FastAPI exports `openapi.json` (`just contract`), committed to the repo.
   - Clients are generated from it: Dart with swagger_parser 1.45 (`smartnutri_api`), and TypeScript with openapi-typescript 7.13 + openapi-fetch 0.17 (`@smartnutri/api-client`).
   - CI fails if the exported spec differs from the committed one, or if the generated clients are stale.
2. **`i18n/`**
   - `messages/{en,hi,mr}.json` is the single source of every UI string and every reason-code label.
   - A script generates the Flutter ARB files. next-intl reads the JSON directly.
3. **`design-tokens/`**
   - `tokens.json` holds the verdict colours (`ok`, `caution`, `unknown`, `avoid`), grade colours A–E, spacing and type.
   - style-dictionary 5 generates Dart constants and CSS variables for the Tailwind 4 `@theme`.
4. **`test-fixtures/`**
   - `products/*.json` holds real Indian products with the expected per-member verdicts and reason codes.
   - It is used by API tests, Flutter widget tests and web component tests.

## Consequences

- A field rename breaks compilation in both clients instead of failing silently.
- Translations and verdict colours cannot diverge between platforms.
- Adds a codegen step to the workflow (`just contract`, `just i18n`, `just tokens`). The skills `api-endpoint` and `flutter-feature`, and a web equivalent, must include it.
- Generated code is committed, so diffs can be large. Reviewers skip `generated/` folders.
