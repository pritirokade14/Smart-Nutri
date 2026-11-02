# packages/test-fixtures

Shared, realistic test cases: Indian products and family members, with the **verdict the rules engine must produce for each member**. The API, the Android app and the web app all test against the same files, so they can't disagree about what "Avoid for Dad" means.

## Contents

```
members/<id>.json                 # e.g. diabetic_adult, milk_allergic_child, jain_adult, bp_parent, infant
products/<name>.json              # per_100g nutrition, serving_size_g, ingredients, claims, "source"
expected/<name>.<member>.json     # { "status": "avoid", "reasons": [{"code": "...", "severity": "avoid"}, ...] } (engine order)
```

Each expected file is `{"status": "ok|caution|unknown|avoid", "reasons": [{"code": "<reason code>", "severity": "<status>"}]}`. `reasons` keeps the engine's order; Android (Dart) and web (TypeScript) tests compare status, then codes and severities in that order.

`expected/` is **generated from the rules engine** (not independently endorsed) and hand-checked by the `nutrition-safety-reviewer`. Workflow, from `apps/api`:

```
uv run python scripts/generate_fixture_expectations.py          # --check (default): prints a diff, exit 1 if anything differs
uv run python scripts/generate_fixture_expectations.py --write  # writes/removes only the files that differ and lists them
```

Changing any expectation needs the `nutrition-safety-reviewer`. The product and member loaders are strict: unknown JSON keys are rejected, and `category` (products) and `diet` (members) are required.

The products mirror the Plan 1 engine fixtures (`sf_biscuit`, `namkeen`, `curd`, `oats`, `cola`, `water`, `no_ingredients`) plus real packs added over time.

## How each project uses them

| Project | Test |
|---|---|
| `apps/api` | `tests/fixtures` loads every product and member, runs `analyze()`, and asserts `expected/` exactly (status, reason codes and severities) |
| `apps/app` | Widget tests feed the expected API response to the verdict screen and check status text, colour token and reason strings |
| `apps/web` | Vitest component tests do the same for the web verdict components; Playwright uses a few for end-to-end checks |

## Rules

- **The API test is the source of truth.** If a rule change alters a verdict:
  1. Update `expected/` in the same PR.
  2. Explain why in the PR.
  3. Get `nutrition-safety-reviewer` approval. CODEOWNERS requires a review for this folder.
- No real people's data. Product data from real packs is fine; note the source in the product file (`"source": "pack photo 2026-11"`, or the Open Food Facts barcode with attribution).
- Keep fixture JSON valid against the contract schemas in `packages/api-contract/openapi.json`.

## Disputed, pending engine follow-up (PENDING CLINICIAN REVIEW)

These expectations record current engine output that a reviewer disputes. They will change when the engine does.

- `expected/namkeen.diabetic_adult.json` is `ok`, but the product is high in salt and saturated fat (2.5 g salt, 10 g sat fat per 100 g). A dietitian would expect `caution` for a person with diabetes. Engine follow-up ruling R12 will add a blood-sugar caution for high_in salt/sat_fat.
- `expected/cola.no_age.json`, `expected/namkeen.no_age.json` and `expected/no_ingredients.no_age.json` are `ok`, because child and infant rules are skipped when age is unknown. Engine follow-up ruling R13 will return `unknown` (`age_unknown`) when a child/infant rule would flag.
