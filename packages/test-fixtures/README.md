# packages/test-fixtures

Shared, realistic test cases: Indian products and family members, with the **verdict the rules engine must produce for each member**. The API, the Android app and the web app all test against the same files, so they can't disagree about what "Avoid for Dad" means.

## Contents

```
members/<id>.json                 # e.g. diabetic_adult, milk_allergic_child, jain_adult, bp_parent, infant, palm_alert_adult (optional "custom_alerts")
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
responses/methodology.json         # GET /v1/methodology?language=en body (Methodology)
responses/voice/answer_avoid.json  # POST /v1/voice/ask body (VoiceAnswer): sf_biscuit + diabetic_adult, source "llm"
responses/voice/answer_avoid_fallback.json  # the same with source "fallback"
responses/voice/answer_avoid_text_only.json  # the same with audio_base64 null (over the inline audio cap: text only)
```

- **`index.json`:** `{"reference_date": "2026-01-01", "account_id": "<uuid>", "products": {"<product>": "<uuid>"}, "members": {"<member>": "<uuid>"}, "scans": {"<product>": "<uuid>"}}`. UUIDs are `uuid5(NAMESPACE_URL, "https://smartnutri.app/test-fixtures/<kind>/<name>")`.
- **`analyze/<product>.json`:** `{scan_id, product, report, verdicts, explanation}`. `verdicts` holds one entry per member, sorted by member file name (`alert_child`, `alert_infant`, ...): `{member_id, member_name, relation, is_primary, status, reasons: [{code, severity, params}], profile_set_up}`. Fixture members are all `relation: "other"`, `is_primary: false`. `explanation` is always the "unavailable" object (`{text: null, tips: [], language: "en", source: "unavailable", prompt_version, member_refs: {}}`): the goldens never call an LLM. To find the verdict for `<product>.<member>`, look up `index.json` `members[<member>]` and match `member_id`; it agrees with `expected/<product>.<member>.json` (status, then codes and severities in order).
- **`public/<product>.json`:** `{product, report, score_label: "calculated_by_smartnutri"}`. No member data.
- `profile_set_up` is display metadata (false when the member has no birth year, so age/allergies/diet may not be set). It is false only for the members with `"age": null` (`no_age`, `alert_no_age`) and never affects status or reasons.
- Fixture products are served as our own verified catalogue products (`product.source = "smartnutri"`, `attribution = null`, `barcode = null`). Ages are turned into birth years against the fixed `reference_date`, which is also the engine's "today", so the files never change on 1 January.
- All files use sorted keys, 2-space indent and a trailing newline.

The products mirror the Plan 1 engine fixtures (`sf_biscuit`, `namkeen`, `curd`, `oats`, `cola`, `water`, `no_ingredients`) plus real packs added over time. `kiwi_yogurt` (Plan 5) is synthetic: it carries a typed-in allergen (kiwi) and a sweetener for the alert members.

Plan 5 members: `kiwi_child` (free-text allergen `kiwi`), and members with `custom_alerts` at every age band: `palm_alert_adult` (30), `alert_child` (9), `alert_infant` (1) and `alert_no_age` (`null`). Together they emit `custom_alert` (e.g. `sf_biscuit`, `kiwi_yogurt`) and `custom_alert_unknown` (`no_ingredients`), which `tests/fixtures/test_shared_fixtures.py` checks.

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

Cases: `clean`, `basis_mismatch_both_columns`, `basis_mismatch_one_column`, `derived_from_serving`, `per_serving_only_no_serving`, `derived_basis_mismatch`, `unit_unconfirmed_sodium_per_100g`, `unit_unconfirmed_sodium_per_serving`, `upper_bound_protein_per_100g`, `upper_bound_protein_per_serving`, `category_check`, `category_and_basis`, `category_unknown`, `low_confidence`, `implausible_value`, `devanagari`, and the label accuracy v2 checks: `energy_decimal_shift`, `salt_sodium_mismatch`, `column_mismatch`, plus the engine fixes `sodium_unit_suspect` (EF2: sodium-only label, g read as mg; the user must pick the unit) and `decimal_shift_tight` (EF3: a /10 slip the loose energy tolerance hides). A failed arithmetic check (`energy_mismatch`, `kcal_kj_mismatch`, `salt_sodium_mismatch`, `fat_parts_mismatch`, `decimal_shift:<path>`, `column_mismatch:<field>`) puts the fields it involves in `engine_withheld` and in every offered column's `confirm_fields`, so an unticked one is stored as null.

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
- **Confirmed (R23, R24).** A field is in `confirmed_fields` when the user ticks its box OR edits its value to something DIFFERENT from the value the draft shows. An edit back to the draft's value (or an edit that types the same number) confirms nothing; a clean "edit then revert" is unconfirmed (conservative). For `serving_size_g` the comparison is against the draft's serving (typing a serving when it was unreadable differs from `null`, so it confirms). Editing a field the chosen column does not ask about confirms nothing. Clients show no confirm boxes until a basis is chosen.
- **`client_blocks` (R24).** A save carries `"client_blocks": true` when the client must refuse to send it (keeps save disabled). Clients decide blocked vs sent ONLY by this marker. It is set when ANY of these hold; otherwise the key is absent:
  1. no basis is chosen (`body` has no `basis`);
  2. no category is chosen (`body` has no `category`; category is required on every save);
  3. the chosen column has `sodium_unit_required`, sodium is not blank, and no `sodium_unit` is picked;
  4. the chosen column has `serving_required` and `serving_size_g` is not in `confirmed_fields`.

  The recorded `result` is only what the server would do if the client sent it anyway (the 422 details, or nulls for unconfirmed values).
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

## Meal summaries and share texts (Plan 6: `meals/`, `share/`)

```
meals/week_family.json                          # hand-written input: members, meals over 7 IST days (+2 outside), one OFF product with no sugars
meals/expected/week_family.dad_diabetic.json    # generated: GET /v1/meals/summary?member_id=<dad>&period=week&date=<end_date>
share/share_result.sf_biscuit.json              # generated: result share text per locale + the forbidden words
share/share_weekly.week_family.json             # generated: weekly share text per locale
```

They live outside `expected/`, which holds only `<product>.<member>` verdicts (the expectations script removes anything else there). Regenerate from `apps/api`, never by hand:

```
uv run python scripts/export_meal_fixtures.py          # --check (default): diff, exit 1 if stale
uv run python scripts/export_meal_fixtures.py --write  # write only the files that differ
```

- **Summary:** built with the endpoint's own functions (nutrient snapshot at log time, engine daily limits, `summarise`) on rows with fixed UUIDs (`uuid5(NAMESPACE_URL, ".../member/week_family/<key>")`). `tests/api/meals/test_week_family_fixture.py` inserts the same rows and checks the endpoint returns this file exactly. It covers an over-limit sugar day (2026-10-31), an incomplete day (2026-11-01: an Open Food Facts product with no sugars), the IST boundary (a meal at 18:00 UTC = 23:30 IST counts on 3 Nov) and empty days (bands `unknown`, totals `null`). Ruling M1: a total with no known value is `null`, never `0`; the week band is `over` because one day is (week limits are the daily limit x the days with logged items); protein has a band only once its target is met (`ok`), otherwise `unknown`, and only adults (18+) with a weight have a target. Clients render bands and the incomplete and limits notes from it; they never compute a band.
- **Share texts:** each file has `input`, `rules` (the algorithm both clients implement), `expected` (the exact string per case, then per locale) and, for the result, `forbidden_substrings` per locale (condition and allergen labels and their English words). A share text never includes conditions, allergens, reason codes or nutrient totals. `who` is the first word of the member's name, or `share.relation.<relation>` when the name is blank. Counts are passed as plain Latin-digit strings. **Ruling SH1:** the result file's `cases` are `default` (no member ticked: product and grade only, the default on both clients), `one_member`, `all_members` and `no_link`; the weekly file has `with_link` and `no_link`. The link (`share.link`) is appended only when `SITE_URL` / `NEXT_PUBLIC_SITE_URL` is set; `https://site.example` stands in for it, never a hard-coded domain. Statuses in the result input are the engine's (`expected/sf_biscuit.<member>.json`, checked by `tests/fixtures/test_shared_fixtures.py`).

## Focused modes and protein (Plan 9: `modes/`, `protein/`)

`modes/layouts.json` is **hand-written, reviewed, and the single source of truth** for each user type's tab bar, Home cards and "More". Both clients mirror it as constants and their tests compare the constants with the file; `apps/api/tests/fixtures/test_mode_layouts.py` checks that `priority` equals `USER_TYPE_PRIORITY` and `default_type` equals `DEFAULT_TYPE`, and the invariants below.

- **Tabs:** five per mode; `home` first, `scan` second, `profile` last (ruling P9-R5 for the tab sets the decisions left open).
- **More** = `destinations` minus the mode's `tabs`, in `destinations` order (for gym: history, family, search, how_we_score). Nothing is deleted from any mode, so scan, results (opened from scan, history, search and the Home recent list) and allergy entry (family members) are reachable in all six.
- **Allergy card (P9-R7):** when any member has an allergen, every mode's Home shows `allergy_check` first (`always_first_card_when_any_member_has_allergens`). It is injected by this rule, so it is listed in `home_cards` only for `allergy_diet`.
- The scan CTAs (barcode, label photo, manual) sit above the cards and are not cards. `recent_scans` is always last.
- Clients never compute verdicts, bands or limits for a card: they render existing API data.

| Card | Data | Notes |
|---|---|---|
| `allergy_check` | `members_list` | who has which allergy; "Unknown means we couldn't check, so it is never marked safe"; a CTA to add allergies when none are set (allergy mode only) |
| `today_sugar_salt` | `meals_summary` (primary member, day) | bands from tokens; `unknown` is grey |
| `today_targets` | `targets_get` (primary member, today), `meals_summary` | the API's calories, protein, fat and carbs, an eye toggle (`targets_display_put`), "{eaten} of {target}" for energy and protein from `meals_summary`; grey "not enough data" for `needs_body_data`; an inline grant button on `consent_required` (never a redirect); no ring or "over" arithmetic in slice 1 |
| `today_protein` | `meals_summary` (primary member, day) | total vs `limits.protein_target_g`, `protein_left_g`; "no target" note; kcal shown without a target |
| `protein_swaps` | link | "Find higher-protein options" opens the Protein screen |
| `protein_claims_tip` | static copy | protein claims are checked against the nutrition table |
| `claims_tip` | static copy | "Sugar-free? We check claims" |
| `not_covered` | static copy | thyroid, cholesterol, kidney disease, pregnancy are not covered yet |
| `family_strip` | `members_list` | members and "Add member" |
| `weekly_family` | `meals_week_counts` | counts only |
| `unknown_explainer` | static copy | why `unknown` is not safe |
| `custom_alerts_setup` | `members_list` | CTA to switch on alerts |
| `recent_scans` | existing recent list | always last |

The protein g/kg per goal moved from `thresholds.yaml` to `apps/api/app/scoring/data/targets.yaml` (`protein.*`, Plan 10), and Lose Weight is now 1.2 g/kg (Q8, was 0.83). Daily-limit protein targets read it through `targets.protein_g_per_kg()`.

`protein/price_per_scoop.json` holds hand-written cases for the client-only arithmetic `price_per_scoop = price * serving_size_g / pack_size_g`, rounded to 2 dp (half up). It is `null` when any input is missing or <= 0. The price is typed by the user and never saved. `members/build_muscle_adult.json` (age 25, goal `build_muscle`) and `products/whey_powder.json` (synthetic, category `supplement`) feed the protein target, claim checks and the supplement rules; their `expected/` files are generated like the others.

## Daily targets (Plan 10: `targets/`)

`targets/inputs/<stem>.json` is hand-written; `targets/expected/<stem>.json` is **generated** by `apps/api/scripts/generate_target_expectations.py` from the real engine (`app/scoring/targets.py`) and the API's own mapping (`app/features/targets/mapping.py`), then dumped with sorted keys, 2-space indent and a trailing newline. Run it from `apps/api`: `uv run python scripts/generate_target_expectations.py` checks (exit 1 if stale), `--write` updates. `apps/api/tests/fixtures/test_target_fixtures.py` fails when an expected file is stale and also pins the hand-checked goldens (spec 4.12). Review every change with `nutrition-safety-reviewer`; never edit an expected file by hand.

- **Input:** `{"as_of": "2026-11-07", "stored": false, "body": {"age", "sex", "height_cm", "weight_kg", "body_fat_pct", "goal"}, "settings": {...} | null}`. `settings` carries the `GoalSettingsIn` fields without `member_id`; `null` gives status `none`. `stored: false` (default) is the preview and PUT path: the body-fat and settings rules run first. `stored: true` is the GET path for settings saved earlier: only `compute` runs. `age` is the engine age (`youngest_age`), not a birth year. Numbers are read as `Decimal(str(x))`.
- **Expected:** the `TargetsOut` JSON the API returns (member id fixed to `uuid5(NAMESPACE_URL, "https://smartnutri.app/test-fixtures/members/self")`), or `{"error": {"code", "details"}}` when a rule refuses the input.
- **Cases:** the golden examples `g1_build_muscle`, `g2_lose_adjusted`, `g3_eat_healthy`, `g4_floor`, `g5_taper` (the trend weight 76.2 kg is the body weight, Ruling D18), `g8_sex_other`, `g11_lean_mass`, `g12_lean_mass_bmi30`; the minor and underweight rules `g6_minor`, `g7_underweight_lose`; one case per activity factor and sex; the floors, the rate and deficit caps, the taper, the protein cap, the BMI 29.9 and 30.0 and body-fat 2.9 / 3 / 70 / 70.1 / blank boundaries, Devine ideal weight, the lean-mass factor per goal, ages 18 / 78 / 79, each missing field, pregnancy, a stored "lose" that no longer validates (`underweight_at_read`), no settings (`none`), and the hidden numbers (`g1_hide_energy`, `g1_hide_all`, `g4_hide_all`).
- **Hidden numbers (Ruling D11):** `hide_energy` nulls every energy number; `hide_all` also nulls protein, fat, carbs and every explanation number except `protein_basis`. The pace (`rate`, `rate_options`) and the flags stay, but under `hide_all` the pace is a percent of body weight per week only (`kg_per_week` is null, since kg divided by the percent gives the body weight). A client shows `targets.flag.floor_applied_hidden` instead of the floor number, and `targets.flag.carbs_below_reference_hidden` when macros are hidden. Sex "other" or not given always gets the 1,500 kcal floor (Q11b); `floor_other_female` pins it.
- **`direction_defaults.json`** maps each goal to the direction the setup screen preselects (build muscle and weight gain: gain; weight loss: lose; eat healthy and no goal: maintain). It equals `targets.default_direction` (tested), and each client checks its own copy against the file.
- Clients render these numbers and flags and never compute a target, a pace in kg, a remaining value or a flag.

## Diary days (Plan 11: `diary/`)

`diary/inputs/<stem>.json` is hand-written; `diary/expected/<stem>.json` is **generated** by `apps/api/scripts/generate_diary_expectations.py` from the API's own `build_day` and `build_week` (`app/features/diary/aggregate.py`), then dumped with sorted keys, 2-space indent and a trailing newline. Run it from `apps/api`: `uv run python scripts/generate_diary_expectations.py` checks (exit 1 if stale), `--write` updates. `apps/api/tests/fixtures/test_diary_fixtures.py` fails when an expected file is stale and pins the hand-worked numbers. Review every change with `nutrition-safety-reviewer`; never edit an expected file by hand.

- **Input (day):** `{"as_of", "date", "timezone", "targets_case", "targets_status", "numbers_display", "partial_logged", "slots"?, "entries": [{"slot", "local_time", "source_kind", "name", "grams", "nutrients": {8 keys}}]}`. `targets_case` names a `targets/inputs` stem, computed as a stored guide (`stored: true`); `null` means no target; `targets_status: "consent_required"` forces that status and no target. `slots` default to the four default slots; an explicit list gives `{key, label_key, custom_label, position, archived}`.
- **Input (week):** `"kind": "week"` and `days: [{date, targets_case, partial_logged, entries}]`; `date` is the last day, and a day that is not listed is empty with no frozen row.
- **Expected:** the `DiaryDayOut` or `DiaryWeekOut` JSON the API returns. Ids are `uuid5(NAMESPACE_URL, "https://smartnutri.app/test-fixtures/diary/<stem>/<key>")`.
- **Rules the cases pin:** a total is the sum of the known values and a nutrient unknown on any entry is `incomplete` (the total is a lower bound); nothing logged is `null`, never 0. `remaining = target - eaten` (1 dp, half up; negative means over) is `null` as a whole unless the day's target is `ready`, and `null` per nutrient when incomplete or hidden; with nothing logged it equals the target. `progress = eaten / target` (2 dp; 0 with nothing logged) with the same rules, and a hidden value keeps only a shape rounded to the nearest 0.25. The week average covers days with items that are not marked partial, and an average with an unknown value on any averaged day is flagged incomplete.
- **Cases:** `day_complete_under`, `day_over_energy`, `day_incomplete_energy`, `day_quick_add_kcal_only`, `day_empty`, `day_no_target`, `day_consent_required`, `day_paused_pregnancy`, `day_hide_energy`, `day_hide_all`, `day_half_up`, `day_archived_slot`, `week_mixed`, `week_hide_all`.
- Clients render these numbers and never compute a total, a remaining value, a progress fraction, a date or a default slot.

## Weight trend (Plan 12: `weights/`)

`weights/inputs/<stem>.json` is hand-written; `weights/expected/<stem>.json` is **generated** by `apps/api/scripts/generate_weight_expectations.py` from the real maths (`app/scoring/weight_trend.py`), then dumped with sorted keys, 2-space indent and a trailing newline. Run it from `apps/api`: `uv run python scripts/generate_weight_expectations.py` checks (exit 1 if stale), `--write` updates. `apps/api/tests/unit/scoring/test_weight_trend.py` fails when an expected file is stale and pins the hand-worked numbers. Review every change with `nutrition-safety-reviewer`; never edit an expected file by hand.

- **Input:** `{"weigh_ins": [{"date", "weight_kg"}], "target_kg": number | null, "numbers_display": "show" | "hide_energy" | "hide_all"}`. The full history, oldest first.
- **Expected:** the `WeightTrendOut` body without the request envelope (`member_id`, `days`, `from`, `to`): `points[{date, weight_kg, outlier, y}]`, `trend[{date, trend_kg, y}]`, `weekly_rate {kg, pct_bw} | null`, `projection {target_kg, date} | null`, `projection_reason`, `flags`, `numbers_hidden`, `pending_clinician_review`. kg and pct are 2 dp half-up. `y` is `(v - min) / (max - min)` (2 dp half-up, 0.5 when all are equal) over the weigh-ins and the trend values together. Under `hide_all` every kg, the rate and the target are null and `y` is kept.
- **Cases:** `three_constant`, `gap_calendar_days`, `single_outlier`, `step_change_two_in_a_row`, `too_few_for_rate`, `weekly_rate_loss`, `rapid_loss_three_weeks`, `projection_{ready,too_few,moving_away,too_far,reached}`, `no_target`, `hide_all`.
- **Clients** never compute the trend. They may use these files to test that they render the API's JSON, including the hollow outlier points and the null kg under `hide_all`.

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
