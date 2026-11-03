# packages/test-fixtures

Shared, realistic test cases: Indian products and family members, with the **verdict the rules engine must produce for each member**. The API, the Android app and the web app all test against the same files, so they can't disagree about what "Avoid for Dad" means.

## Contents

```
members/<id>.json                 # e.g. diabetic_adult, milk_allergic_child, jain_adult, bp_parent, infant
products/<name>.json              # per_100g nutrition, serving_size_g, ingredients, claims, "source"
expected/<name>.<member>.json     # { "status": "avoid", "reasons": [{"code": "...", "severity": "avoid"}, ...] } (engine order)
responses/                        # generated golden API responses (see "Golden API responses")
```

Each expected file is `{"status": "ok|caution|unknown|avoid", "reasons": [{"code": "<reason code>", "severity": "<status>"}]}`. `reasons` keeps the engine's order; Android (Dart) and web (TypeScript) tests compare status, then codes and severities in that order.

`expected/` is **generated from the rules engine** (not independently endorsed) and hand-checked by the `nutrition-safety-reviewer`. Workflow, from `apps/api`:

```
uv run python scripts/generate_fixture_expectations.py          # --check (default): prints a diff, exit 1 if anything differs
uv run python scripts/generate_fixture_expectations.py --write  # writes/removes only the files that differ and lists them
```

Changing any expectation needs the `nutrition-safety-reviewer`. The product and member loaders are strict: unknown JSON keys are rejected, and `category` (products) and `diet` (members) are required.

## Golden API responses (`responses/`)

Real API response bodies built from these fixtures, for the Android and web tests. They are **generated**, never edited by hand:

```
cd apps/api && uv run python scripts/export_fixture_responses.py
```

`tests/api/analyze/test_shared_fixtures.py` fails when they are stale, and also checks that every verdict in them equals `expected/`.

```
responses/index.json               # fixture name -> fixed UUID, plus the reference date
responses/analyze/<product>.json   # POST /v1/analyze body (AnalyzeOut) for the product and ALL members
responses/public/<product>.json    # GET /v1/products/{barcode}/public body (PublicProductOut)
```

- **`index.json`:** `{"reference_date": "2026-01-01", "account_id": "<uuid>", "products": {"<product>": "<uuid>"}, "members": {"<member>": "<uuid>"}, "scans": {"<product>": "<uuid>"}}`. UUIDs are `uuid5(NAMESPACE_URL, "https://smartnutri.app/test-fixtures/<kind>/<name>")`.
- **`analyze/<product>.json`:** `{scan_id, product, report, verdicts, explanation: null, tips: []}`. `verdicts` holds one entry per member, sorted by member file name (`bp_parent`, `diabetic_adult`, ...): `{member_id, member_name, status, reasons: [{code, severity, params}], profile_set_up}`. To find the verdict for `<product>.<member>`, look up `index.json` `members[<member>]` and match `member_id`; it agrees with `expected/<product>.<member>.json` (status, then codes and severities in order).
- **`public/<product>.json`:** `{product, report, score_label: "calculated_by_smartnutri"}`. No member data.
- `profile_set_up` is display metadata (false when the member has no birth year, so age/allergies/diet may not be set). It is true for every fixture member and never affects status or reasons.
- Fixture products are served as our own verified catalogue products (`product.source = "smartnutri"`, `attribution = null`, `barcode = null`). Ages are turned into birth years against the fixed `reference_date`, which is also the engine's "today", so the files never change on 1 January.
- All files use sorted keys, 2-space indent and a trailing newline.

The products mirror the Plan 1 engine fixtures (`sf_biscuit`, `namkeen`, `curd`, `oats`, `cola`, `water`, `no_ingredients`) plus real packs added over time.

## Confirm-screen drafts (`drafts/`)

Label drafts and the exact save each client must send for scripted user actions (Ruling R21). **Both clients render their confirm screen only from `draft.confirm`** (computed by the API with the same helpers that enforce `POST /v1/products`) and assert their request bodies against `expected.json`. They are **generated**, never edited by hand:

```
cd apps/api && uv run python scripts/export_draft_fixtures.py          # --check (default): diff, exit 1 if stale
cd apps/api && uv run python scripts/export_draft_fixtures.py --write  # write only the files that differ
```

`tests/fixtures/test_draft_fixtures.py` fails when the files are stale; `tests/api/products/test_draft_fixture_saves.py` posts every body in `expected.json` to the real endpoint and checks the stored row. Cases (raw extractions) live in the script. A change needs `nutrition-safety-reviewer`.

```
drafts/<case>.json     # ProductDraft exactly as POST /v1/scans/label returns it in `draft`
drafts/expected.json   # {"format_version": 1, "cases": {"<case>": {...}}}
```

Cases: `clean`, `basis_mismatch_both_columns`, `basis_mismatch_one_column`, `derived_from_serving`, `per_serving_only_no_serving`, `derived_basis_mismatch`, `unit_unconfirmed_sodium_per_100g`, `unit_unconfirmed_sodium_per_serving`, `upper_bound_protein_per_100g`, `upper_bound_protein_per_serving`, `category_check`, `category_unknown`, `low_confidence`, `implausible_value`, `devanagari`.

**`draft.confirm`** (the hints):

```
{"basis_required": bool,              # basis in doubt: offer both columns, never preselect
 "category_required": bool,           # category_unknown/category_check: never preselect
 "columns": {"per_100g": Column|null, "per_serving": Column|null}}   # null = basis not offered
Column = {"printed": bool,            # the draft column of this name holds printed values
          "shared": bool,             # only printed column on a basis mismatch: show it for either basis
          "confirm_fields": [...],    # need an explicit tick when saving with this basis
          "sodium_unit_required": bool,  # show a mg/g picker; send its value when sodium is not null
          "serving_required": bool}   # nutrients are stored only with a confirmed serving: keep save disabled until it is (R23)
```

`serving_required` equals `needs_serving_confirmation(draft, basis)`, the helper `POST /v1/products` enforces with (a per-serving save, or any save of a derived draft). The server still accepts an unconfirmed serving and then stores every nutrient as null; the clients must not send it.

**`expected.json` case:** `{"description", "draft": "<case>.json", "extraction": <raw NutritionExtraction>, "saves": [{"actions", "body", "result"}]}`.

- `actions` (all optional): `pick_basis` (`per_100g`/`per_serving`), `pick_category`, `tick` (list of confirm fields), `sodium_unit` (`mg`/`g`), `edit` (`{field: number|null}` on the shown column, or `serving_size_g`). `{}` means the user changed nothing and pressed save: every case keeps one, the "unconfirmed -> stored null" control.
- **Edit = confirm (R23).** The client adds a field to `confirmed_fields` when the user ticks its box OR edits its value. Editing a field in the chosen column's `confirm_fields`, or ANY edit of `serving_size_g` (typing it when unreadable, or changing it), confirms it with no tick. Editing a field the column does not ask about confirms nothing.
- **`client_blocks`.** A save carries `"client_blocks": true` when the chosen column has `serving_required` and `serving_size_g` is not in `confirmed_fields`. The client keeps save disabled and must never send it; the recorded `result` is only what the server would do if it did (nulls, or 422 `body.serving_size_g`). The key is absent otherwise. A save with no basis chosen is not marked (the missing basis is the block).
- `body` is the `POST /v1/products` body **without `scan_id`** (the client adds it; `barcode` is not sent). Built by this algorithm, which both clients implement:
  1. `basis` = `pick_basis`; else, when `basis_required` is false, the only non-null column; else omitted.
  2. `nutrients` (the nine engine fields plus `added_sugars_g`, `trans_fat_g`) = the draft column named by `basis` if that column is `printed`, else the `shared` column, else all null (with no basis: the shared column, else the first printed one); then `edit`.
  3. `category` = `pick_category`; else the draft's category when `category_required` is false; else omitted.
  4. `sodium_unit` = the action or null. `serving_size_g` = the edit or the draft's. `confirmed_fields` = `tick` plus the edit-confirmed fields (R23), in contract order (engine fields, then `serving_size_g`).
  5. `name`, `brand`, `ingredients`, `allergen_statement`, `may_contain_statement`, `claims`, `veg_mark` copied from the draft.
- `result` is either `{"status": 201, "stored": {"category", "extraction_confidence", "per_100g": {11 fields}, "serving_size_g"}}` (values stored by the server, unrounded) or `{"status": 422, "error": {"code", "fields"}}` (`details.fields` of the error envelope, e.g. `["body.basis"]`, `["body.sodium_unit"]`, or `["carbs_g", "sugars_g"]` for `implausible_value`).

Files use sorted keys, 2-space indent, UTF-8 (Devanagari unescaped) and a trailing newline.

## Rendered reason text (`reason-text/`)

```
reason-text/{en,hi,mr}.json   # [{"key", "member", "product", "reason", "reason_index", "text"}, ...]
```

Golden reasons (every param type: allergen, diet with and without ingredients, sugar numbers, child pct/limit/basis, carbs basis, claim, both `nutrient_missing` variants, `high_in` list, `age_unknown`, a three-item ingredients list) and the exact string each client must show for them. **BOTH clients (Android and web) must render exactly these strings**, byte for byte, in each locale.

- `product`/`member`/`reason_index` point into `responses/analyze/<product>.json` (member by name via `responses/index.json`). Reasons the golden products never emit use `product` and `member` `"synthetic"`; every entry carries the full `reason` (`{code, severity, params}`) so a client can assert from the file alone.
- `key` is the message key the client must pick (`reason.<code>` or a `reason_variant.*`).
- Rules baked in: lists joined with `", "`, numbers with Latin digits and at most 3 decimals, code params mapped through their namespaces (see `packages/i18n/README.md`).
- Files use sorted keys, 2-space indent and a trailing newline. The web test `apps/web/tests/features/analysis/reason-text.test.ts` asserts them; regenerate with `UPDATE_REASON_TEXT=1 pnpm test reason-text` (from `apps/web`) and review the diff. A change needs `nutrition-safety-reviewer`.

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

None currently.

Resolved:

- R12: `expected/namkeen.diabetic_adult.json` is now `caution` (`cardio_risk_high_in`): blood-sugar members get a caution when the product is high_in salt or saturated fat. `sf_biscuit.diabetic_adult` (7 g sat fat per 100 g) gains the same reason; its status stays `avoid`.
- R13: `expected/cola.no_age.json`, `expected/namkeen.no_age.json`, `expected/no_ingredients.no_age.json` and `expected/sf_biscuit.no_age.json` are now `unknown` (`age_unknown`): with no birth year, the child and infant rules are checked at the most protective age, and any flag makes the verdict `unknown`.
