# Plan 12: Food Diary Slices 3–6: Household Units and Indian Foods, Custom Foods and Recipes, Favourites and Recents, the Weight Log and Progress

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The account holder logs Indian home food in household units (katori, roti, tbsp…) with grams always shown, finds generic foods (USDA FoodData Central) and documented Indian dishes, creates their own foods and recipes, re-logs favourites and recents in one tap, and keeps a manual weight log with an honest trend, weekly rate, projection and taper, on Android and web, with every number decided by the API.

**Architecture:**
- **API first, one slice at a time.** Four migrations chain from the current head `0009_diary_days_slots_entries`: `0010` units and foods, `0011` custom foods and recipes, `0012` favourites, `0013` weight logs.
- New feature folders: `app/features/foods/` (units, `to_grams`, food loading, the seed, search, detail, portion overrides), `custom_foods/`, `recipes/`, `favourites/`, `weights/`. One new pure engine module, `app/scoring/weight_trend.py`, reads new keys in `targets.yaml`.
- Diary entries stay `meal_logs` rows with a full `food_snapshot`, so history never changes when a food, an override, a recipe or the seed changes. `meals_log` gains `food_id`, `custom_food_id`, `recipe_id` and a `quantity` + `unit` portion.
- **Then, per slice:** shared golden fixtures (unit conversions, recipe sums with unknowns, weight-trend maths), i18n, `just contract`, then **Android ∥ web**, then the `nutrition-safety-reviewer` gate.
- Targets stay information: `analyze()` and the verdict modules never import `foods`, `custom_foods`, `recipes`, `favourites`, `weights` or `weight_trend`. Custom foods never reach a verdict.

**Tech Stack:** as Plan 11. API: Python 3.13, FastAPI, SQLAlchemy 2 async + Alembic, pytest, Hypothesis (new dev dependency), `decimal`, `zoneinfo`. Android: Flutter, Riverpod 3, go_router, drift (offline queue), the generated `smartnutri_api`. Web: Next.js 16, TanStack Query, next-intl, `@smartnutri/api-client`. Tests: pytest, flutter_test, Vitest, Playwright.

**Spec:** `docs/research/food-diary/FEATURE_SPEC.md` (binding).
- Slices 3, 4, 5 and 6 are rows 3–6 of section 10. Sections implemented: 5.4, 5.6–5.11, 6 (conventions), 6.3, 6.4, 6.5, 6.6, 6.7, 7 (general), 7.3, 7.4, 7.5 (progress, without adaptive), 7.6, 7.7, 7.8, 8 (`units.*`, `foods.*`, `recipes.*`, `weight.*`), 9.2, 9.3, 9.5, 9.6.
- Binding answers in `docs/research/food-diary/DECISIONS.md`: Q1, Q4, Q6 **as replaced by Q6b**, Q7, Q9, Q13. **Q3: adaptive TDEE is slice 7 and is not in this plan.**
- Prepared data (read before the slice-3 tasks): `docs/research/food-diary/data/household_units.csv` (71 rows), `usda_ingredients.csv` (141 rows), `indian_dishes_recipes.md` (30 recipes, all `[assumed — needs dietitian]`), `NIN_permission_request.md`.
- Current interfaces: Plan 10 (Rulings D1–D20), Plan 11 (Rulings E1–E24) and `.superpowers/sdd/plan-11-food-diary-s2/api-report.md`. **Existing names and shapes win** over the spec; each such case is a ruling below.

## Rulings made while writing this plan

**Migrations and seed data**
- **G1 (migrations):** `0010_diary_foods_units` (`down_revision = "0009_diary_days_slots_entries"`), `0011_diary_custom_foods_recipes`, `0012_diary_favourites`, `0013_diary_weight_logs`. These match spec 5.11. Every new table gets `ENABLE` + `FORCE ROW LEVEL SECURITY`, the 0009 `_lock_down` privileges (or the read-only variant for reference tables) and a `tests/db` case.
- **G2 (no `pg_trgm`):** the reference set is ~160 rows (141 FDC foods, 21 dishes). `foods.search_text` (lower-cased name plus aliases, written by the seed) is matched with `ILIKE` and ranked in Python. This avoids the Supabase `extensions`-schema question. Revisit when `foods` passes 5,000 rows (IFCT).
- **G3 (seed outside migrations):** migration `0010` seeds only `household_units` (17 constant rows, kept equal to `household_units.yaml` by a test, as 0009 did for slot defaults). Foods, dishes, densities and global portions are loaded by an idempotent job, `python -m app.jobs.seed_foods` (upsert by `(source, source_code)`, so food ids stay stable across reseeds). The job is appended to the `db-migrate` recipe in the justfile. Data files live in `apps/api/app/features/foods/data/` with a `PENDING DIETITIAN REVIEW` header. `usda_fdc_foods.csv` is a byte copy of the research CSV (tested).
- **G4 (unit set, Q6b):** 17 codes: `g`, `ml`, `serving`, `piece`, `piece_small`, `piece_medium`, `piece_large`, `roti`, `slice`, `katori` (200 ml, the default, CSV `katori_nin_m`), `katori_small` (115 ml, `katori_nin_xs`), `katori_medium` (155 ml, `katori_nin_s`), `katori_large` (360 ml, `katori_nin_l`), `cup` (200 ml), `glass` (250 ml), `tbsp` (15 ml), `tsp` (5 ml).
  - The CSV's `katori` row (150 ml) is superseded by Q6b and not seeded.
  - `ladle`, `handful`, `bowl` and `plate` have no source, so they are not seeded.
  - Size words in the CSV (egg large/medium/small, banana medium/small, "medium" onion…) map to `piece_large`/`piece_medium`/`piece_small`. A single fruit with no size (mango, guava) and one almond map to `piece`; bread slices to `slice`; packaged roti to `roti`.
  - `naan_*` rows are not seeded: their FDC ids (171845, 174077) are not in the 141-row ingredient set.
  - Every value stays PENDING DIETITIAN REVIEW. Labels always show the ml beside the name (`unit.ml_hint`), because the binding "medium" katori (155 ml) is smaller than the default (200 ml).
- **G5 (empty per-piece grams stay unknown):** the 12 CSV rows with no grams (`phulka`, `roti_homemade_medium`, `paratha`, `idli`, `dosa_plain`, `vada`, `puri`, `samosa`, `laddoo`, `papad`, `pakora_one`, `upma_poha_cup`) are listed in `food_portions.yaml` under `unknown_piece_weights`, each with its CSV note, and produce **no** portion row and no unit grams. Such a unit simply does not resolve for that food. The picker never offers it, and the user may set their own value (a per-food override). A test proves that no seeded number exists for any CSV row whose `grams` cell is empty, and that every seeded number equals its CSV cell.
- **G6 (derived densities):** the 20 `density_*` rows (FDC "1 cup" grams ÷ 236.588 ml) go into `foods.density_g_per_ml` with `density_source = "fdc_derived"`, PENDING DIETITIAN REVIEW. `to_grams` uses them. Without them "1 katori dal" could never convert. Sunflower oil (171017) has no density, so "1 tbsp sunflower oil" does not resolve; that is on the dietitian list.
- **G7 (which dishes are seeded):** a dish is seeded only when (a) every ingredient is an FDC row in the CSV and (b) the doc gives a cooked yield in grams. **21 dishes are seeded.**
  - **Blocked** (a core ingredient has no FDC row): poha (7), paneer bhurji (12).
  - **Needs weighing** (a yield given only as a count, with no grams): roti (1), idli (9), dosa (10), paratha (23), puri (24), boiled egg (26), besan chilla (28). They stay in `indian_dishes.yaml` with `status: needs_weighing` and switch on automatically once a dietitian adds `cooked_weight_g` (tested). Users still find packaged roti (FDC 171844 and 174075, which have `roti` grams), the FDC egg rows (with `piece_*` grams), quick add and their own recipes.
  - Water is never an ingredient; it is already inside the cooked weight. Where the doc offers an alternative ("oil 5 g (or ghee 5 g)"), the first-named ingredient is used. Sambar is seeded as documented: its GAP items (sambar powder, drumstick) are not in its ingredient list, and the gap is noted in `notes`.
- **G8 (dish nutrients, no invented totals):** the seed computes `per_100 = Σ(ingredient per_100 × grams / 100) × 100 / cooked_weight_g` in `Decimal`.
  - A nutrient unknown on **any** ingredient is **null** in the dish. `foods.per_100` has no "incomplete" marker, so a partial sum is never stored looking complete.
  - Saturated fat is null for every FDC row and dish: the CSV has no such column.
  - Salt comes from sodium through the existing `Nutrients.salt()` rule (sodium × 2.5 / 1000).
  - `serving_g` is set only where the doc says the batch is N servings (egg bhurji: 1; masala omelette: 1). A "1 katori" serving does not resolve without a density, so most dishes offer `g` (and `serving` where known), plus any katori grams the user sets.
- **G9 (names and aliases):** `name_en` is the FDC description or our dish name. Food names are data, not UI strings. `name_hi`/`name_mr` stay null. Romanised aliases (atta, besan, suji, toor dal, chawal, dahi…) live in `aliases.yaml`; Devanagari aliases come later with the native review. The spec's `is_cooked` column is omitted: no rule reads it.
- **G10 (attribution, Q1):** new i18n keys `attribution.usda_fdc` ("Nutrition data: USDA FoodData Central (public domain)") and `attribution.smartnutri_recipe` ("Recipe by SmartNutri from USDA FoodData Central ingredients. Pending dietitian review.").
  - The credit shows on search hits, the portion picker, diary entries, recipe ingredients, and the How we score page (`methodology.food_data.*`, with the USDA citation).
  - `MealOut` and `RecentItem` gain `attributions: list[str]`. The existing `attribution` keeps its meaning, and `attribution.off` wins when any ingredient is from OFF (ODbL credit is mandatory).
  - Each food row stores `licence` (`CC0 1.0`). IFCT rows are added only after NIN's written permission.

**Units and logging**
- **G11 (`to_grams`):** the result is the amount in the food's **basis** (grams, or ml for an ml-basis food). It follows the order in spec 5.6:
  1. a mass unit;
  2. `serving` → `serving_g`;
  3. a portion row (the user override first, then the global row);
  4. a volume unit with a density;
  5. a volume unit on an ml-basis food.

  For an ml-basis food, the mass unit `g` needs a density. Otherwise it returns `None`, and the API never assumes ml = g. Limits: `quantity` ≤ 1000 for every unit except `g` and `ml` (≤ 5000), and a result above 5000 is `422 quantity_out_of_range`.
- **G12 (portion forms):** `MealIn` gains a flat `quantity` + `unit` pair as the third portion form, beside the existing `grams` and `servings`.
  - Every new entry stores `quantity` and `unit`: the `grams` form becomes `unit = g`, and `servings` becomes `unit = serving`. Legacy rows stay NULL.
  - `food_snapshot.units` stores every unit that resolved at log time. `MealPatch` resolves a new `quantity` + `unit` **only** from that snapshot, so a later override never rewrites history. A unit not in it is `422 unit_grams_unknown`.
  - `MealOut` gains `portion_units` (from the snapshot) for the edit sheet. The edit sheet shows grams only and no nutrient preview; the saved values come back from the API.
- **G13 (error codes):** existing names win.
  - Reused: `invalid_product_ref` (not the spec's `invalid_food_ref`), `search_query_too_short` (not `query_too_short`), `implausible_value` (custom-food values), `portion_required`, `serving_size_unknown`, `copy_source_empty`, `copy_too_many`, `date_in_future`, `date_too_old`.
  - New, each with `error.<code>` in en, hi and mr, added by the task that first raises it: `unit_grams_unknown`, `unit_not_supported`, `quantity_out_of_range`, `food_not_found`, `custom_food_not_found`, `custom_food_nutrients_empty`, `barcode_already_used`, `recipe_not_found`, `recipe_ingredient_limit`, `recipe_weight_invalid`, `favourite_not_found`, `favourite_limit`, `weight_out_of_range`, `weight_needs_confirm`, `weight_not_found`, `date_range_too_long`.
- **G14 (the one client computation, spec 7):** the portion picker previews `quantity × grams_per_unit × per_100 / 100`, rounded half-up to 1 dp.
  - `grams_per_unit` and `per_100` come from `foods_get`; the client never converts a unit itself.
  - The arithmetic is exact decimal on the JSON number strings (BigInt-scaled, no new dependency), so `1.15 × 100 / 100` previews `1.2` and not the float `1.1`.
  - `packages/test-fixtures/units/conversions.json` proves on all three platforms that the preview equals the API's displayed value. On save, the API's numbers are the ones stored.
- **G15 (hidden numbers, Q7):** `foods_get.per_100`, every number in `RecipeOut` and every weight value are redacted with the primary member's `numbers_display`.
  - `hide_energy` nulls energy. `hide_all` nulls every nutrient and every kg, including `weight_needs_confirm.details.previous`.
  - Search hits carry no nutrients. `CustomFoodOut` is **not** redacted: it is the label the user typed, and they need it to edit. This is flagged for the reviewer.
  - Under `hide_all`, weight responses keep a normalised `y` (0–1) so the chart keeps its shape with no digits (spec 6.5).
- **G16 (search):** `foods_search` returns `{items, partial, failed_sources}` with **no cursor**, like `products_search`, at most `limit` (default 20, max 50).
  - Groups: `mine` (custom foods and recipes, slice 4), `indian` (seeded foods and dishes), `packaged` (own catalogue and OFF). "Recents that match" is not a separate group; the Recent segment covers it.
  - A new `products.search.search_products_status()` reports OFF trouble (throttled, or a silent `OffUnavailable`) as `partial: true`. `search_products()` keeps its behaviour by calling it.
- **G17 (barcode for logging):** a new `GET /v1/foods/barcode/{barcode}` (`foods_by_barcode`) checks the user's own custom foods first, then products and OFF. `products_get_by_barcode`, `resolve_ref` and `analyze` are unchanged, so custom foods never reach a verdict.

**Custom foods and recipes**
- **G18 (update = PUT):** `custom_foods_update` is `PUT /v1/custom-foods/{id}`, a full replace. A PATCH with "null = unchanged" (Ruling E10) could never clear a nutrient back to unknown. An absent nutrient is unknown.
- **G19 (recipe sums with unknowns):**
  - `recipes.per_100g` stores the **sum of the known parts** for each nutrient, plus `incomplete_nutrients`. The recipe screen shows such a value as "at least X" (`diary.week.at_least`) with the incomplete marker. A nutrient no ingredient knows is null.
  - A **diary entry** from a recipe nulls every incomplete nutrient in its `food_snapshot.per_100`, so the day total is flagged incomplete and `remaining` is null, as in slice 2. A partial value is never counted as complete.
- **G20 (recipe weight):** the basis weight is `cooked_weight_g`, or else the raw total.
  - An ml-basis ingredient counts toward the raw total only through its density. Without one, `cooked_weight_g` is required: `422 recipe_weight_invalid` with `details.reason = "cooked_weight_required"`.
  - The cooked weight must be within 0.2–3 × the raw total: `422 recipe_weight_invalid` with `reason = "out_of_range"`.
- **G21 (deletes keep history):** deleting a custom food or recipe sets `meal_logs` and `recipe_ingredients` refs to NULL (the snapshot keeps the name and values) and cascades `favourites`.
  - Recents skip entries whose ref is now NULL.
  - Re-logging a favourite meal nulls any id that no longer exists.
  - The `0011` ref check allows a NULL id for `custom_food` and `recipe` rows (spec 5.1).
- **G22 (ingredient refs):** flat, exactly one of `food_id`, `custom_food_id`, `product_id`, `barcode`, like `MealIn`. Otherwise `422 invalid_product_ref`.

**Favourites**
- **G23 (foods and meals):** `favourites.kind` is `food` or `meal`.
  - A **meal** favourite snapshots the entries of one logged slot on one day (≤ 50, the copy rules) under a user-typed name (1–40 code points).
  - The name is user text, like slot labels: stored as typed, never translated, never sent to analytics, logs or prompts.
  - A meal favourite is re-logged by `favourites_log`, with copy semantics (a `client_id` derived per item; each item counts against `meal_logs`). On Android this is online-only, like copy.
  - A **food** favourite is logged through `meals_log` with its default quantity and unit, so Android can queue it offline.
  - The list is not paginated (at most 200 per member, `favourite_limit`).

**Weights**
- **G24 (trend):** a time-aware exponential average on calendar days with `trend.alpha_per_day = 0.25`.
  - Its mean lag of (1 − α)/α = 3 days matches a centred 7-day moving average, as the brief asks. The spec's 0.1 is slice 7's adaptive key, and is not added here.
  - A weigh-in more than 3 % from the trend is an outlier: kept for display, left out of the trend. A **second** weigh-in in a row beyond the band on the same side means a real change, and both are then accepted (algorithm in Task 22).
  - The trend is computed over the member's full history, so it does not depend on the window.
  - The weekly rate is `T(last) − T(last − 7 days)` in kg, and as a % of `T(last)`.
- **G25 (weight used by targets, spec 4.9):** with at least `trend.min_weigh_ins_for_trend` (3) non-outlier weigh-ins up to the target date, `W` is the trend weight on that date. Otherwise it is `members.weight_kg`. The taper (already in `targets.compute`) therefore follows the trend, not a one-day water swing. `TargetsOut.explanation` gains `weight_source: "trend" | "latest" | null`, frozen in `inputs`.
- **G26 (one source of weight):**
  - `weights_put` writes `members.weight_kg` when its date is the latest, in the same transaction.
  - A members create or update that sets the **primary** member's `weight_kg` (already gated by `health_data`) upserts that local day's weigh-in, so the profile and the log never disagree.
  - The `0013` back-fill adds one row per member whose `weight_kg` is within 2–300, dated by the member's `updated_at` in the account zone.
- **G27 (projection and cards):**
  - `projection_reason` gains `reached`, for a trend within `goal_rates.taper.maintenance_band_kg` (0.5 kg) of the target.
  - `flags: ["rapid_loss"]` is set when each of the last three 7-day rates is a loss faster than `safety.rapid_loss_pct_bw_per_week` (1.5 %). It shows a neutral card (spec 4.11).
  - The low-intake card needs slice 7's eligible-day rules, so it is deferred there. The optional weekly reminder (spec 7.8) is deferred too.
- **G28 (weigh-in writes):** `PUT /v1/weights/{date}` returns 200 whether it creates or replaces a row.
  - `weight_needs_confirm` fires when the value is outside `plausible.weight_kg` (30–200), or when it changed by more than `plausible.weight_change_kg_per_day` (2.0, new key) × the days since the nearest earlier weigh-in (minimum 1 day).
  - A repeated `client_id` returns the stored row.
- **G29 (placement):** Progress is a third Diary view (Day | Week | Progress). The weight chart is a `CustomPainter` on Android and inline SVG on web; no chart dependency is added.

**Clients and order**
- **G30 (Android queue):** drift schema v3 (slice 3: `foodId`, `quantity`, `unit`), v4 (slice 4: `customFoodId`, `recipeId`), v5 (slice 6: a `PendingWeighIns` table). Each step has an `onUpgrade` and a migration test. Edit, delete, copy, favourite meals, custom-food and recipe writes stay online-only.
- **G31 (order):** slices run in order 3 → 4 → 5 → 6, because the migrations chain and each slice regenerates the contract. Inside a slice, the marked groups run in parallel. Task 22 (the pure trend) may start at any time.
- **G32 (ADRs):** ADR 0024 "Foods and household units: USDA FoodData Central and documented dishes; `to_grams` refuses to guess" (Task 3) and ADR 0025 "Weight trend and the weight used for daily guides" (Task 22).

## Global Constraints

Health-app rules (root `AGENTS.md`, non-negotiable):
1. **The rules engine decides; targets are information.** Clients never compute a total, remaining, a unit conversion, a recipe sum, a trend, a rate or a projection. The portion preview (G14) is the one exception, and it is fixture-proven. `analyze` is byte-identical with and without diary data.
2. **Never invent nutrition data.** Missing is `null`, never 0. A per-piece weight, density, yield or nutrient with no source stays unknown (G5–G8). Incomplete totals are flagged and `remaining` is then null.
3. **Unknown is not safe.** Unknown and incomplete use the grey "not enough data" style, never green. Weight, rate, "over" and progress never use verdict colours or the danger token. No streaks, ratings or celebration.
4. **Reference values live in data, marked pending review.**
   - Unit volumes, per-food grams, densities and dishes: `app/features/foods/data/*`, header `PENDING DIETITIAN REVIEW`.
   - Trend, projection and safety constants: `app/scoring/data/targets.yaml` (`PENDING CLINICIAN REVIEW`), each with a `section_sources` entry.
5. **Secrets stay server-side.** Nothing new is public config.
6. **No health data in analytics.** No new events. `diary_entry_added {method}` keeps its enum (`search`, `recent`, `favourite`, `custom`, `recipe` are already in it). Never sent: any weight, food name, custom-food or recipe name, favourite-meal name, unit or nutrient.
7. **No medical claims.** `diary.disclaimer` and "Pending clinician review" wherever a target, weight rate or projection shows. Copy must pass `test_new_copy_no_claims.py` (for example, never "manage").
8. **Strings only in `packages/i18n`** (en, hi, mr). hi and mr machine drafts go in `NATIVE_REVIEW.md` under "Plan 12 slice N". Marathi plurals print the number with `{count}` inside the plural, never `#` (Plan 11 fix round). User text (custom-food, recipe and favourite-meal names) never passes through i18n.
9. **Never hand-edit generated code.** `just` is not installed for agents: run the justfile recipe lines by hand (`.superpowers/sdd/RULES-FOR-AGENTS.md`).
10. **Feature parity.** A slice is done only when the API, Android and web all ship it and its shared fixtures pass on all three.

Slice rules:
- **Solo only (Q9):** every new route uses `targets_service.resolve_member` (foreign member → 404, non-primary → `422 diary_member_not_enabled`). Custom foods, recipes and portion overrides belong to the account; favourites and weights belong to the member.
- **Consent (Q13):**
  - `/v1/foods`, `/v1/custom-foods`, `/v1/recipes` and `/v1/favourites` gate on `terms` by prefix (`CONSENT_GATES`).
  - `/v1/weights` is gated per route: `REQUIRED["weights"] = ("terms", "health_data")`, and `REQUIRED["weights_erase"] = ("terms",)` for delete.
  - The gate runs before `limit()`.
- **Rate limits:** foods search uses the existing `search` bucket; `foods_get` uses `product_lookups`; writes use `diary_writes` (200/day); weigh-ins use a new `weights` bucket (day, 30, `rate_limit_weights_per_day`).
- **Decimals:** API arithmetic in `Decimal`, rounded half-up for display only. Stored snapshots stay unrounded (Plan 6 F1).
- **Account deletion:** each new account-owned table joins `ACCOUNT_OWNED_TABLES`. The final order is: `recipe_ingredients`, `favourites`, `meal_logs`, `meal_slots`, `recipes`, `food_portions`, `custom_foods`, `weight_logs`, `diary_days`, `diary_goal_settings`, `members`, `scans`, `product_reports`, `account_user_types`, `consents`. `test_delete_me.py` covers each one.
- **Android:** run `dart format --set-exit-if-changed lib test` before `flutter analyze && flutter test` (CI fails on unformatted Dart).
- **Commits:** Conventional Commits with a scope, ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Run `gitleaks protect --staged --no-banner` before each commit. Never push.

## Review Focus

1. **A unit that cannot be converted gets guessed.** Examples: "2 idli" or "1 roti" of a home-made dish with no weighed piece, "1 katori" of a food with no density and a gram basis, "1 tbsp sunflower oil". Expected: the unit is never offered, and a forced request is `422 unit_grams_unknown`; grams never equal the quantity. Owned by:
   - Task 2: `test_refuses_count_unit_without_portion`, `test_refuses_volume_without_density_on_gram_basis`, `test_never_returns_quantity_itself` (Hypothesis);
   - Task 3: `test_no_seeded_number_for_empty_csv_cells`;
   - Task 4: `test_detail_lists_only_resolving_units`;
   - Tasks 7 and 8: `picker offers only the API's units`.
2. **A partial sum counted as complete.** Examples: a dish with a spice whose sugar is unknown; a user recipe with one ingredient lacking fibre. Expected: the dish's sugar is null; the recipe shows "at least" with the incomplete marker; an entry from either is incomplete, and the day's `remaining` for that nutrient is null. Owned by:
   - Task 3: `test_dish_nutrient_null_if_any_ingredient_unknown`;
   - Task 12: `test_recipe_entry_nulls_incomplete_nutrients`, `test_day_incomplete_after_recipe_entry` and fixture `recipe_missing_fibre`;
   - Tasks 14 and 15: `incomplete recipe nutrient renders at least, never a plain number`.
3. **Hidden numbers leaking through a new surface.** With `hide_all`, a digit can still appear through:
   - the portion preview, the recipe per serving, or a favourite-meal row;
   - the weight chart axis, the weekly rate or the projection;
   - the unusual-weight confirm message, or an Android pending weigh-in.

   Expected: no digit anywhere except grams and dates. Owned by:
   - Task 4: `test_food_detail_redacted`;
   - Task 12: `test_recipe_out_redacted`;
   - Task 23: `test_weights_hidden_every_surface`, `test_needs_confirm_hides_previous`;
   - Tasks 7, 8, 14, 15, 24 and 25: the `hide_all … no digits` tests.
4. **History drift.** Editing a user override, a custom food or a recipe, deleting a custom food, or reseeding the foods must not change any past entry. A PATCH with the same quantity and unit must give an identical snapshot. Owned by:
   - Task 5: `test_override_change_keeps_past_entry`, `test_patch_same_portion_identical_snapshot`;
   - Task 3: `test_reseed_keeps_food_ids_and_entries`;
   - Task 12: `test_recipe_edit_keeps_past_entries`;
   - Task 11: `test_delete_custom_food_keeps_history_and_recents_skip_it`.
5. **Weight noise moving the target.** Cases: a single +4 % weigh-in (water or a wrong scale); a real step change (two weigh-ins in a row); only two weigh-ins; a deleted latest weigh-in. Expected: the single outlier is shown hollow and left out of the trend and of `W`; the step change is accepted; fewer than 3 weigh-ins use the latest weight; delete falls back to the previous one. Owned by:
   - Task 22: fixtures `single_outlier`, `step_change_two_in_a_row`;
   - Task 23: `test_targets_use_trend_weight_after_three`, `test_targets_ignore_outlier`, `test_delete_latest_restores_previous_weight`.

## Task overview: platform, order, parallelism

| Task | Platform | Depends on | Parallel group |
|---|---|---|---|
| 0. Housekeeping: parity and context docs; robust public-product e2e | Docs + Web | — | any time (∥ Task 1) |
| **Slice 3: units and Indian foods** | | | |
| 1. Migration 0010, models, unit rows, RLS | API (db) | — | **A** (alone) |
| 2. Typed units, `to_grams`, food loading, unit fixtures | API | 1 | **B**: 2 ∥ 3 |
| 3. Seed data, dishes, the seed job, ADR 0024 | API | 1 | **B**: 2 ∥ 3 |
| 4. Foods routes: search, detail, units, portion overrides | API | 2, 3 | **C**: 4 ∥ 5 |
| 5. Meals for foods: quantity + unit, snapshot, patch, copy, recents | API | 2 | **C**: 4 ∥ 5 |
| 6. i18n, How we score food data, contract | API + shared | 4, 5 | — |
| 7. Food search, portion picker, attribution, queue v3 | Android | 6 | **D**: 7 ∥ 8 |
| 8. Food search, portion picker, attribution, e2e | Web | 6 | **D**: 7 ∥ 8 |
| 9. Slice-3 gate | All | 1–8 | — |
| **Slice 4: custom foods and recipes** | | | |
| 10. Migration 0011, models, resolve for custom foods and recipes | API (db) | 9 | **E** (alone) |
| 11. Custom foods CRUD | API | 10 | **F**: 11 ∥ 12 |
| 12. Recipes, recipe fixtures, logging custom foods and recipes | API | 10 | **F**: 11 ∥ 12 |
| 13. Search and detail for my foods, barcode route, i18n, contract | API + shared | 11, 12 | — |
| 14. Custom food form, my foods, recipe builder, queue v4 | Android | 13 | **G**: 14 ∥ 15 |
| 15. Custom food form, my foods, recipe builder, e2e | Web | 13 | **G**: 14 ∥ 15 |
| 16. Slice-4 gate | All | 10–15 | — |
| **Slice 5: favourites and recents** | | | |
| 17. Migration 0012, favourites routes, recents star, i18n, contract | API + shared | 16 | — |
| 18. Favourites segment, star, save meal, log again | Android | 17 | **H**: 18 ∥ 19 |
| 19. Favourites segment, star, save meal, log again, e2e | Web | 17 | **H**: 18 ∥ 19 |
| 20. Slice-5 gate | All | 17–19 | — |
| **Slice 6: weight log, trend, taper** | | | |
| 21. Migration 0013 with back-fill, model, weigh-in store | API (db) | 20 | **I**: 21 ∥ 22 |
| 22. Pure weight trend, YAML keys, weight fixtures, ADR 0025 | API (engine) | — | **I**: 21 ∥ 22 |
| 23. Weights routes, trend weight in targets, members sync, i18n, contract | API + shared | 21, 22 | — |
| 24. Progress view, weight log, queue v5 | Android | 23 | **J**: 24 ∥ 25 |
| 25. Progress view, weight log, e2e | Web | 23 | **J**: 24 ∥ 25 |
| 26. Slice-6 gate and final docs | All | 21–25 | — |

Agents:
- API tasks: `api-builder` (sonnet). Tasks 2, 3, 12 and 22 touch health maths or fixtures: use the `scoring-rule` skill for 22.
- Android tasks: `flutter-builder`. Web tasks: `web-builder`.
- Gates: `nutrition-safety-reviewer` (opus). Task 0: `web-builder`.

Parallel pairs and their files:
- **2 ∥ 3:** Task 2 owns `foods/{units,resolve}.py` and `packages/test-fixtures/units/`. Task 3 owns `foods/{seed,recipe_math}.py`, `foods/data/*` except `household_units.yaml`, `app/jobs/seed_foods.py`, the justfile and ADR 0024.
- **4 ∥ 5:** Task 4 owns `foods/{schemas,service,router}.py`, `products/search.py`, `main.py` and `core/consent.py`. Task 5 owns `meals/{schemas,service,copy}.py` and `diary/{service,schemas}.py`.
- **11 ∥ 12:** both add one router line to `main.py` and one `CONSENT_GATES` entry (merge carefully). Task 11 owns `custom_foods/*`. Task 12 owns `recipes/*`, `meals/*`, `diary/{service,schemas}.py` and `packages/test-fixtures/recipes/`.
- **21 ∥ 22:** Task 21 owns the migration, `weights/{models,store}.py` and `tests/db`. Task 22 owns `scoring/weight_trend.py`, `targets.yaml`, `packages/test-fixtures/weights/` and ADR 0025.
- **Client pairs:** Android and web files are always disjoint.

## File Map

```
apps/api/
  pyproject.toml (hypothesis, dev)                                         # T2
  alembic/versions/0010_diary_foods_units.py                              # T1
  alembic/versions/0011_diary_custom_foods_recipes.py                     # T10
  alembic/versions/0012_diary_favourites.py                               # T17
  alembic/versions/0013_diary_weight_logs.py                              # T21
  app/features/foods/{__init__,models}.py, data/household_units.yaml       # T1
  app/features/foods/{units,resolve}.py                                   # T2 (resolve extended in T10)
  app/features/foods/{seed,recipe_math}.py, data/{usda_fdc_foods.csv,food_portions.yaml,aliases.yaml,indian_dishes.yaml}   # T3
  app/jobs/seed_foods.py, justfile (db-migrate)                           # T3
  app/features/foods/{schemas,service,router}.py                          # T4, T13
  app/features/products/search.py (search_products_status)               # T4
  app/features/meals/{models,schemas,service,copy}.py                     # T1, T5, T12
  app/features/diary/{service,schemas}.py (recents)                       # T5, T12, T17
  app/features/custom_foods/{__init__,models,schemas,service,router}.py   # T10 (models), T11
  app/features/recipes/{__init__,models,schemas,service,router}.py        # T10 (models), T12
  app/features/favourites/{__init__,models,schemas,service,router}.py     # T17
  app/features/weights/{__init__,models,store,trend_source}.py            # T21 (models, store), T23
  app/features/weights/{schemas,service,router}.py                        # T23
  app/scoring/weight_trend.py, app/scoring/data/targets.yaml              # T22
  app/features/targets/{service,schemas,mapping}.py, app/features/diary/frozen.py  # T23 (weight in use)
  app/features/members/service.py                                         # T23 (weigh-in sync)
  app/core/{consent,config,ratelimit}.py, app/main.py                     # T4, T11, T12, T17, T23
  app/features/me/service.py (ACCOUNT_OWNED_TABLES)                       # T1, T10, T17, T21
  scripts/{generate_unit_expectations,generate_dish_expectations,generate_recipe_expectations,generate_weight_expectations}.py   # T2, T3, T12, T22
  tests/db/*                                                              # T1, T10, T17, T21
  tests/unit/foods/*, tests/api/foods/*                                   # T2–T5, T13
  tests/api/{custom_foods,recipes,favourites,weights}/*                   # T11, T12, T17, T23
  tests/unit/scoring/{test_weight_trend,test_targets_yaml}.py             # T22
packages/test-fixtures/{units,foods,recipes,weights}/**, README.md        # T2, T3, T12, T22
packages/i18n/messages/{en,hi,mr}.json, NATIVE_REVIEW.md                  # T6, T13, T17, T23 (+ error keys in API tasks)
packages/api-contract/**                                                  # T6, T13, T17, T23 (generated)
docs/adr/0024-foods-household-units.md, docs/adr/0025-weight-trend.md    # T3, T22
apps/app/lib/features/{foods,recipes,favourites,weights}/**, lib/features/diary/**, lib/core/storage/meal_queue.dart   # T7, T14, T18, T24
apps/web/src/features/{foods,recipes,favourites,weights}/**, src/features/diary/**, src/app/[locale]/(app)/diary/**, e2e/diary-*.spec.ts, e2e/stub-api.mjs   # T8, T15, T19, T25
docs/FEATURE_PARITY.md, CONTEXT.md                                        # T0, T9, T16, T20, T26
apps/web/e2e/public-product.spec.ts                                       # T0
```

---

### Task 0 (Docs + Web): Housekeeping: parity and context docs; a robust public-product e2e *(any time; parallel with Task 1)*

Use the `web-feature` skill for the e2e part.

**Files:**
- Modify: `docs/FEATURE_PARITY.md`, `CONTEXT.md`, `apps/web/e2e/public-product.spec.ts`

- [ ] **Step 1: Reproduce the flake.** Run `cd apps/web && pnpm build && pnpm exec playwright test e2e/public-product.spec.ts --repeat-each=30 --trace=retain-on-failure`. Record in the report which step stalls (`page.goto` waiting for `load`, the server render, or a late resource) and the slowest passing duration.
- [ ] **Step 2: Make the spec robust.** In both tests:
  - `page.goto(url, { waitUntil: "domcontentloaded", timeout: 60_000 })`, then keep the status and URL asserts.
  - The heading and "calculated by SmartNutri" asserts (they auto-wait).
  - Then `await page.waitForLoadState("load", { timeout: 60_000 })` **in place of** `networkidle` before checking `violations` (CSP violations fire while resources load; `networkidle` can hang on a long-poll).
  - Add `test.describe.configure({ timeout: 90_000 })` with a comment that gives the reason from Step 1. Keep the 60 s navigation timeout only if Step 1 showed passing runs slower than 15 s; otherwise use 30 s and say so.
- [ ] **Step 3: Verify.** Run the Step 1 command again. Expected: 30/30 pass. Then `pnpm e2e` → all green.
- [ ] **Step 4: Update the docs.**
  - `FEATURE_PARITY.md`:
    - F21 status: "merged (PR #7) and live on dev".
    - F22: "slices 2 and 2b merged (PR #9, `8f7f456`) and live on dev; dev DB at `0009_diary_days_slots_entries`", with meal-slot management included.
    - Add rows F23 "Household units, portion picker, generic and Indian foods", F24 "Custom foods and recipes", F25 "Favourites and recents", F26 "Weight log, trend and progress". Mark each ⬜ for Plan 12.
    - The "Honest state" line now counts F1–F22.
  - `CONTEXT.md`:
    - Section 7: say the dev DB is at `0009`, and add the plan rows 10 (merged, PR #7), 11 (merged, PR #9) and 12 (this plan, not started).
    - Section 8: Plan 10 and 11 merged and live; slice 2b included.
    - Section 9: add three USER items:
      - send the NIN letter (`docs/research/food-diary/data/NIN_permission_request.md`, Q1);
      - a dietitian review of `household_units.csv`, the derived densities and `indian_dishes_recipes.md`, including weighing roti, phulka, paratha, idli, dosa, puri, vada, samosa, laddoo and besan chilla, and the katori sizes (Q6b);
      - re-verify the USDA FDC licence before launch.
- [ ] **Step 5: Commit.** First `test(web): make the public product e2e robust`, then `docs: slices 1, 2 and 2b merged and live; Plan 12 rows`.

---

## Slice 3: units and Indian foods

### Task 1 (API, db): Migration 0010, models, unit rows, RLS

Use the `api-endpoint` skill. Spec: 5 (preamble), 5.1 (`meal_logs`: `food_id`, `quantity`, `unit`), 5.6, 5.7, 9.5 (RLS). Rulings G1–G4, G12.

**Files:**
- Create: `apps/api/alembic/versions/0010_diary_foods_units.py`, `apps/api/app/features/foods/{__init__,models}.py`, `apps/api/app/features/foods/data/household_units.yaml`, `apps/api/tests/unit/foods/test_unit_rows.py`
- Modify:
  - `apps/api/app/features/meals/models.py`
  - `apps/api/app/features/me/service.py` (add `food_portions` after `meal_slots`)
  - `apps/api/tests/db/{conftest,test_rls,test_grants,test_constraints,test_migrations,test_meal_logs}.py`, `apps/api/tests/api/test_delete_me.py`

**Interfaces:**
- Produces, in the migration:
  - `household_units`: `code` text PK; `kind` text, check in (`mass`, `volume`, `count`); `ml` numeric NULL; `grams` numeric NULL; `sort` int.
    - Check: (`mass`, grams > 0, ml NULL) or (`volume`, ml > 0, grams NULL) or (`count`, both NULL).
    - Seeded from the constant `UNIT_ROWS: tuple[tuple[str, str, str | None, str | None, int], ...]` (code, kind, ml, grams, sort), in the G4 order: `g, ml, serving, piece, piece_small, piece_medium, piece_large, roti, slice, katori, katori_small, katori_medium, katori_large, cup, glass, tbsp, tsp`.
  - `foods`:
    - `id` uuid PK (`gen_random_uuid()`);
    - `source` text, check in (`usda_fdc`, `smartnutri_recipe`); `source_code` text; unique `(source, source_code)`;
    - `name_en` text; `name_hi`, `name_mr` text NULL; `aliases` text[] default `{}`; `search_text` text;
    - `basis` text, check in (`g`, `ml`); `per_100` jsonb (keys = `scoring.Nutrients` field names, null = unknown);
    - `density_g_per_ml` numeric NULL (> 0); `density_source` text NULL; `serving_g` numeric NULL (> 0);
    - `recipe` jsonb NULL (dish ingredients, for display);
    - `licence` text; `data_version` text; `review_status` text default `'pending_dietitian_review'`; `created_at`, `updated_at`.
  - `food_portions`:
    - `id`; `account_id` uuid NULL (FK accounts, cascade; NULL = global);
    - `food_id` uuid NULL (FK foods, cascade), `product_id` uuid NULL (FK products, cascade), `off_barcode` text NULL; check `num_nonnulls(food_id, product_id, off_barcode) = 1` (0011 adds `custom_food_id`);
    - `unit` text (FK `household_units(code)`); `grams_per_unit` numeric, check `> 0 and <= 2000`;
    - `source` text, check in (`smartnutri_measured`, `reference_table`, `user`, `label`); check `(account_id IS NULL) = (source <> 'user')`;
    - `csv_key` text NULL; `created_at`, `updated_at`.
    - Partial unique indexes `uq_food_portions_food` on `(coalesce(account_id, '00000000-0000-0000-0000-000000000000'::uuid), food_id, unit) WHERE food_id IS NOT NULL`, and the same for `product_id` and `off_barcode`.
  - `meal_logs`:
    - `food_id` uuid NULL (FK foods, NO ACTION); `quantity` numeric NULL (check `> 0 and <= 5000`); `unit` text NULL (FK `household_units(code)`); check `num_nonnulls(quantity, unit) in (0, 2)`.
    - `ck_meal_logs_source_kind` adds `food`. `ck_meal_logs_ref` adds the branch `(source_kind = 'food' AND food_id IS NOT NULL AND product_id IS NULL AND off_barcode IS NULL AND grams IS NOT NULL)`, and `food_id IS NULL` on the other branches. (Drop by the plain names and create with `op.f`, as 0009 did.)
  - Privileges:
    - `foods` and `household_units`: `REVOKE ALL … FROM PUBLIC, anon, authenticated`; `GRANT SELECT … TO authenticated`; `GRANT ALL … TO service_role`; ENABLE + FORCE RLS; policy `<t>_read FOR SELECT TO authenticated USING (true)`.
    - `food_portions`: the same, with policy `food_portions_read FOR SELECT TO authenticated USING (account_id IS NULL OR account_id = (SELECT auth.uid()))`.
  - Downgrade: deletes `meal_logs` rows with `source_kind = 'food'` (documented in the docstring), restores the 0009 checks, drops the columns and the three tables.
- Produces, in `foods/models.py`: `HouseholdUnit`, `Food`, `FoodPortion` (SQLAlchemy, `Numeric(asdecimal=True)` for the numeric columns). Also `MealLog.food_id`, `MealLog.quantity`, `MealLog.unit`.
- Produces `household_units.yaml`:
  - header `# PENDING DIETITIAN REVIEW (Q6, Q6b). Read by app/features/foods only.`;
  - `units:` with `{code, kind, ml, grams, sort, csv_key, note}` for the 17 rows;
  - `not_seeded:` with `{csv_key, reason}` for `katori` (superseded by Q6b), `ladle`, `handful`, `bowl` and `plate` (no source).

- [ ] **Step 1: Write the failing tests.**
  - `tests/unit/foods/test_unit_rows.py`:
    - `test_migration_rows_equal_yaml`
    - `test_katori_default_200_and_nin_sizes` (`katori` 200, `katori_small` 115, `katori_medium` 155, `katori_large` 360)
    - `test_yaml_values_equal_csv_cells` (each `csv_key` row's ml or grams equals the research CSV cell)
  - `tests/db/test_rls.py`:
    - `foods`, `household_units` and `food_portions` join `TABLES` and the expected policy set;
    - `test_reference_tables_read_only` (authenticated can SELECT and every write is 42501);
    - `test_food_portions_global_and_own_rows_only` (A sees global plus A's rows, never B's).
  - `tests/db/test_constraints.py`:
    - `test_food_entry_needs_food_id_and_grams`
    - `test_product_entry_rejects_food_id`
    - `test_quantity_and_unit_together`
    - `test_unit_must_exist`
    - `test_portion_exactly_one_ref`
    - `test_global_portion_not_user_source`
    - `test_portion_unique_per_owner_ref_unit`
  - `tests/db/test_migrations.py`: `test_0010_upgrade_downgrade` (the downgrade removes `food` entries and keeps product and quick-add entries).
  - `tests/api/test_delete_me.py`: user portion rows are erased; global rows stay.
- [ ] **Step 2: Run** `cd apps/api && uv run pytest tests/unit/foods tests/db tests/api/test_delete_me.py -q` → FAIL.
- [ ] **Step 3: Implement** the migration, models, YAML and `ACCOUNT_OWNED_TABLES`.
- [ ] **Step 4: Run** the same command → PASS, then the full `uv run pytest -q`.
- [ ] **Step 5: Commit** `feat(api): migration 0010 foods, household units and food portions`.

---

### Task 2 (API): Typed units, `to_grams`, food loading and the unit fixtures *(parallel with Task 3)*

Spec: 5.6 (`to_grams`), 9.2. Rulings G4, G5, G11, G14.

**Files:**
- Create:
  - `apps/api/app/features/foods/units.py`, `apps/api/app/features/foods/resolve.py`
  - `packages/test-fixtures/units/conversions.json`, `apps/api/scripts/generate_unit_expectations.py`
  - `apps/api/tests/unit/foods/test_units.py`, `apps/api/tests/api/foods/test_resolve.py`
- Modify: `apps/api/pyproject.toml` (`uv add --dev hypothesis`), `packages/test-fixtures/README.md` ("Unit conversions" section)

**Interfaces:**
- Produces, in `units.py` (pure, `Decimal` only):

```python
UnitCode = Literal["g", "ml", "serving", "piece", "piece_small", "piece_medium", "piece_large",
                   "roti", "slice", "katori", "katori_small", "katori_medium", "katori_large",
                   "cup", "glass", "tbsp", "tsp"]
UnitKind = Literal["mass", "volume", "count"]
Basis = Literal["g", "ml"]
UnitSource = Literal["mass", "serving", "portion_user", "portion_global", "density", "volume_basis"]
MAX_AMOUNT = Decimal(5000)            # basis amount (g or ml) per entry or ingredient
MAX_QUANTITY = Decimal(1000)          # every unit except g and ml (those: MAX_AMOUNT)

@dataclass(frozen=True, slots=True)
class Unit: code: str; kind: UnitKind; ml: Decimal | None; grams: Decimal | None; sort: int

@dataclass(frozen=True, slots=True)
class FoodUnits:
    basis: Basis
    serving_g: Decimal | None = None
    density_g_per_ml: Decimal | None = None
    global_portions: Mapping[str, Decimal] = field(default_factory=dict)
    user_portions: Mapping[str, Decimal] = field(default_factory=dict)

@dataclass(frozen=True, slots=True)
class ResolvedUnit: code: str; grams_per_unit: Decimal; source: UnitSource

def to_grams(quantity: Decimal, unit: Unit, food: FoodUnits) -> Decimal | None
def resolve_units(food: FoodUnits, table: Mapping[str, Unit]) -> list[ResolvedUnit]   # every resolving unit, table sort order
def default_unit(resolved: Sequence[ResolvedUnit]) -> str     # serving > first count unit > katori > g (> ml)
def settable_units(food: FoodUnits, table: Mapping[str, Unit]) -> list[str]  # count/volume codes, not serving, that do not resolve
def portion_amount(quantity: Decimal, unit_code: str, food: FoodUnits, table: Mapping[str, Unit]) -> Decimal
    # 422 unit_not_supported (unknown code), quantity_out_of_range (bounds, result > 5000), unit_grams_unknown (None)
```

- Produces, in `resolve.py` (DB; slice 4 adds the `custom_food` and `recipe` kinds):

```python
FoodKind = Literal["food", "product", "off"]
@dataclass(frozen=True, slots=True)
class FoodRef: kind: FoodKind; id: str                     # uuid string, or the barcode for off
@dataclass(frozen=True, slots=True)
class LoadedFood:
    ref: FoodRef; name: str; brand: str | None; basis: Basis
    per_100: scoring.Nutrients                               # unrounded; None = unknown
    units: FoodUnits; grade: str | None                      # grade: products only (as log_meal computes it)
    attribution: str | None; attributions: tuple[str, ...]; licence: str | None
    source: str | None; dish: Mapping[str, Any] | None
    food_id: UUID | None; product_id: UUID | None; off_barcode: str | None
async def unit_table(session: AsyncSession) -> dict[str, Unit]
async def load_food(session: AsyncSession, off: OffClient, ref: FoodRef, *, account_id: UUID,
                    settings: Settings) -> LoadedFood
    # food: 404 food_not_found; product/off: products_service.resolve_ref errors. User portions are this account's rows.
def ref_from_ids(*, food_id: UUID | None, product_id: UUID | None, barcode: str | None) -> FoodRef
    # exactly one, else 422 invalid_product_ref
```

- [ ] **Step 1: Write the failing tests** in `tests/unit/foods/test_units.py`. These cases decide the behaviour:

```python
def test_katori_of_cooked_dal_uses_density():          # 1 katori (200 ml) x 0.71 = 142
    assert to_grams(D("1"), KATORI, FoodUnits("g", density_g_per_ml=D("0.71"))) == D("142.00")
def test_nin_katori_sizes():                           # 115/155/360 ml x 0.71 = 81.65, 110.05, 255.6
def test_user_override_beats_global_beats_density():   # roti: user 35 > global 68; 2 roti = 70
def test_serving_needs_serving_g():                    # None without serving_g; 2 x 30 = 60
def test_refuses_count_unit_without_portion():         # piece / roti with no portion -> None
def test_refuses_volume_without_density_on_gram_basis():  # katori, tbsp on basis g, no density -> None
def test_ml_basis_volume_is_ml():                      # 1 glass of an ml-basis food = 250
def test_ml_basis_mass_needs_density():                # g on basis ml: None without density
def test_portion_amount_bounds():                      # 1001 katori -> quantity_out_of_range; 30 katori_large x 1.0 -> 10800 > 5000 -> quantity_out_of_range
def test_resolve_units_order_and_default():            # cooked dal: g, ml, katori... default katori; packaged roti: default roti
def test_settable_units_excludes_mass_and_serving():
# Hypothesis properties (spec 9.2):
def test_linearity(q, k): ...                          # to_grams(k*q) == k*to_grams(q), exact (basis g)
def test_monotonic(q1, q2): ...
def test_mass_unit_ignores_food(food, q): ...          # to_grams(q, g, basis-g food) == q
def test_never_returns_quantity_itself(food, unit, q): ...  # a count or volume unit with nothing to convert by returns None, never q
def test_result_positive_when_resolved(...): ...
def test_conversions_fixture():                        # every case in packages/test-fixtures/units/conversions.json
```

  - `conversions.json` holds about 20 cases. Each is `{case, food: {basis, serving_g, density_g_per_ml, global_portions, user_portions}, unit, quantity, per_100 (synthetic test values), expected: {grams_per_unit, amount | null, error | null, preview (1 dp NutrientSnapshot keys)}}`. Include:
    - the katori and NIN sizes; `tbsp` canola (15 × 0.921 = 13.815); a glass of milk (250 × 1.031 = 257.75);
    - 2 packaged roti (136); the override; a serving; the two refusals; the ml basis; a bound error;
    - two rounding traps: `per_100.fibre_g = 1.15` × 100 g → preview `1.2`, and `10.016` × 250 g → `25.0`.
  - The file is written by `scripts/generate_unit_expectations.py` (`--check` by default, `--write`) from `units.py` and the existing `meals.service._portion`/`_round1`.
  - `tests/api/foods/test_resolve.py`:
    - `test_load_food_seed_row` (units from global portions and density);
    - `test_load_food_user_portion_scoped_to_account`;
    - `test_load_product_units_serving_and_override`;
    - `test_unknown_food_404`;
    - `test_ref_from_ids_exactly_one`.
- [ ] **Step 2: Run** `uv run pytest tests/unit/foods/test_units.py tests/api/foods/test_resolve.py -q` → FAIL.
- [ ] **Step 3: Implement** `units.py` and `resolve.py` (portion and density values as `Decimal`), then run the script with `--write`.
- [ ] **Step 4: Run** → PASS; `uv run python -m scripts.generate_unit_expectations --check` → no diff.
- [ ] **Step 5: Commit** `feat(api): typed household units and to_grams that refuses to guess`.

---

### Task 3 (API): Seed data, documented dishes, the seed job, ADR 0024 *(parallel with Task 2)*

Spec: 5.7, 5.9 (sum rule), section 10 row 3. Rulings G3, G5–G10, G32.

**Files:**
- Create:
  - `apps/api/app/features/foods/data/{usda_fdc_foods.csv, food_portions.yaml, aliases.yaml, indian_dishes.yaml}`
  - `apps/api/app/features/foods/{recipe_math,seed}.py`, `apps/api/app/jobs/seed_foods.py`
  - `apps/api/scripts/generate_dish_expectations.py`, `packages/test-fixtures/foods/dishes.json`
  - `apps/api/tests/unit/foods/{test_seed_data,test_recipe_math,test_dishes}.py`, `apps/api/tests/api/foods/test_seed_job.py`
  - `docs/adr/0024-foods-household-units.md`
- Modify: `justfile` (`db-migrate` adds `cd apps/api && uv run python -m app.jobs.seed_foods`), `packages/test-fixtures/README.md` ("Seeded dishes")

**Interfaces:**
- **Data files** (every one starts with `PENDING DIETITIAN REVIEW`):
  - `usda_fdc_foods.csv`: a byte copy of `docs/research/food-diary/data/usda_ingredients.csv`. Mapping: `sugar_g` → `sugars_g`, `fibre_g` → `fiber_g`, `sodium_mg` → `sodium_mg`; `sat_fat_g`, `salt_g` and `fvl_percent` are null; a blank cell is null.
  - `food_portions.yaml`:
    - `portions:` `{csv_key, fdc_id, unit, grams}` for the 19 rows whose FDC id is in the CSV (G4 mapping);
    - `densities:` `{csv_key, fdc_id, density_g_per_ml}` (20 rows);
    - `not_seeded:` `{csv_key, reason}` for `naan_*`;
    - `unknown_piece_weights:` `{csv_key, note}` for the 12 G5 rows.
  - `aliases.yaml`: `{fdc_id: [romanised aliases]}`.
  - `indian_dishes.yaml`: one entry per recipe in the doc (all 30): `{code, doc_section, name_en, aliases, status: seeded | blocked | needs_weighing, reason, cooked_weight_g, servings, ingredients: [{fdc_id, grams}], notes}`.
- Produces, in `recipe_math.py` (pure; Task 12 reuses it):

```python
NUTRIENT_KEYS = ("energy_kcal", "sugars_g", "salt_g", "protein_g", "fat_g", "sat_fat_g", "carbs_g", "fibre_g")  # = NutrientSnapshot
def snapshot_per_100(n: scoring.Nutrients) -> dict[str, Decimal | None]    # sanitized, salt from salt()/sodium, fiber -> fibre
def to_nutrients(per_100: Mapping[str, Decimal | None]) -> scoring.Nutrients  # back to field names (salt_g set, sodium None)
@dataclass(frozen=True, slots=True)
class Amount: grams: Decimal; per_100: Mapping[str, Decimal | None]
@dataclass(frozen=True, slots=True)
class Sums: totals: dict[str, Decimal | None]; incomplete: tuple[str, ...]   # known-part sums; None when no amount knows it
def sum_nutrients(amounts: Sequence[Amount]) -> Sums
def per_100_from(sums: Sums, basis_weight_g: Decimal, *, strict: bool) -> dict[str, Decimal | None]
    # strict=True -> every incomplete nutrient is None (dishes, entry snapshots); strict=False -> known-part value (recipe view)
```

- Produces, in `seed.py` and the job:

```python
@dataclass(frozen=True, slots=True)
class SeedReport: foods: int; dishes_seeded: int; dishes_excluded: dict[str, str]; portions: int; densities: int
def load_seed_data(data_dir: Path = DATA_DIR) -> SeedData        # parses and validates; pure
async def seed_foods(session: AsyncSession) -> SeedReport        # idempotent upsert; commits
# app/jobs/seed_foods.py: `python -m app.jobs.seed_foods [--check]` (--check prints the report, writes nothing)
```

  - FDC rows: `source = usda_fdc`, `source_code = fdc_id`, `basis = g`, `licence = "CC0 1.0"`, `data_version = "fdc_sr_legacy_2018_04"`, and `search_text = lower(name + " " + " ".join(aliases))`.
  - Dishes: `source = smartnutri_recipe`, `source_code = code`, `per_100 = to_nutrients(per_100_from(sum_nutrients(...), cooked_weight_g, strict=True))`, `serving_g = cooked_weight_g / servings` when `servings` is set, and `recipe = {ingredients: [{fdc_id, name, grams}], cooked_weight_g, servings, review: "assumed_needs_dietitian"}`.

- [ ] **Step 1: Write the failing tests.**
  - `test_seed_data.py`:
    - `test_fdc_csv_is_byte_copy_of_research`
    - `test_every_csv_unit_row_classified_once` (each of the 71 `unit_key`s appears exactly once across `household_units.yaml` units/not_seeded and `food_portions.yaml` portions/densities/not_seeded/unknown_piece_weights)
    - `test_no_seeded_number_for_empty_csv_cells`
    - `test_seeded_numbers_equal_csv_cells`
    - `test_portion_and_density_fdc_ids_exist`
  - `test_dishes.py`:
    - `test_dishes_match_research_doc` (parses every `` `NNNNNN` … N g `` pair in `indian_dishes_recipes.md` and compares it with the YAML ingredient list, section by section)
    - `test_seeded_count_21`
    - `test_poha_and_paneer_bhurji_blocked`
    - `test_piece_dishes_need_weighing` (roti, idli, dosa, paratha, puri, boiled egg, besan chilla)
    - `test_needs_weighing_switches_on_with_cooked_weight` (a copy of the YAML with `cooked_weight_g` added for roti → seeded)
    - `test_dish_nutrient_null_if_any_ingredient_unknown` (dal tadka: an ingredient with blank `sugar_g` → `sugars_g` null)
    - `test_dish_sat_fat_always_null`
    - `test_dishes_fixture` (`packages/test-fixtures/foods/dishes.json`, generated by `generate_dish_expectations.py`)
    - a hand check: curd rice energy per 100 g = Σᵢ(eᵢ × gᵢ / 100) / 300 × 100 over its six ingredients (rice 150, curd 120, milk 30, salt 1, mustard seed 0.5, oil 3 g), with each eᵢ read from the CSV in the test.
  - `test_recipe_math.py`:
    - `test_sum_known_parts_and_incomplete`
    - `test_all_unknown_is_none`
    - `test_strict_nulls_incomplete`
    - `test_snapshot_per_100_salt_from_sodium`
    - `test_to_nutrients_round_trip`
  - `test_seed_job.py`:
    - `test_seed_is_idempotent`
    - `test_reseed_keeps_food_ids_and_entries` (an entry logged before a reseed keeps its `food_id` and snapshot)
    - `test_check_mode_writes_nothing`
- [ ] **Step 2: Run** `uv run pytest tests/unit/foods tests/api/foods/test_seed_job.py -q` → FAIL.
- [ ] **Step 3: Implement** the data files (transcribe the dishes from the doc by hand; the doc test catches slips), `recipe_math.py`, `seed.py`, the job and the justfile line. Write ADR 0024: the decisions Q1, Q6b and G2–G11, the dietitian gate, and the IFCT switch after NIN permission.
- [ ] **Step 4: Run** → PASS; `generate_dish_expectations.py --check` → no diff; `uv run python -m app.jobs.seed_foods --check` against the test DB prints 141 foods, 21 dishes, 9 dishes excluded with reasons, 19 portions and 20 densities.
- [ ] **Step 5: Commit** `feat(api): seed USDA foods, household portions and documented Indian dishes`.

---

### Task 4 (API): Foods routes: search, detail, units, portion overrides *(parallel with Task 5)*

Spec: 6.3 (the `foods_*` rows), 7.3, 7.4. Rulings G14–G16.

**Files:**
- Create: `apps/api/app/features/foods/{schemas,service,router}.py`, `apps/api/tests/api/foods/{test_search,test_detail,test_portions,test_consent}.py`
- Modify: `apps/api/app/features/products/search.py` (`search_products_status`), `apps/api/app/main.py` (router; `CONSENT_GATES["/v1/foods"] = "foods"`), `apps/api/app/core/consent.py` (`"foods": ("terms",)`), `packages/i18n/messages/{en,hi,mr}.json` (the `error.*` keys for `unit_grams_unknown`, `unit_not_supported`, `quantity_out_of_range`, `food_not_found`)

**Interfaces:**
- Consumes: Task 2 `load_food`, `unit_table`, `resolve_units`, `default_unit`, `settable_units`; Task 3 seeded rows; `meals.service.hidden_for_member`; `targets_service.resolve_member`.
- Produces:

```text
GET  /v1/foods/search?q&kinds&limit   foods_search  -> FoodSearchOut {items: FoodHit[], partial: bool, failed_sources: ["off"]}
     q 2-80 chars after normalise_query (else 422 search_query_too_short); kinds ⊆ food,product (slice 4 adds custom_food,recipe); limit 1-50, default 20
     FoodHit {kind: food|product|off, id, name, brand, group: indian|packaged, is_dish, grade|null, attribution|null, attributions}
     order: indian group (rank: name prefix, then word prefix in search_text, then substring; ties by name length, name), then packaged (search_products_status order)
GET  /v1/foods/units                  foods_units_list -> UnitOut[] {code, kind, ml|null, grams|null}
GET  /v1/foods/{kind}/{id}            foods_get -> FoodDetailOut          (bucket product_lookups)
     FoodDetailOut {kind, id, name, brand, basis, per_100: NutrientSnapshot (unrounded; null = unknown or hidden),
       units: FoodUnitOut[] {code, kind, ml|null, grams_per_unit (unrounded), source, user_override: bool},
       default_unit, settable_units: [code], serving_g|null, attribution|null, attributions, licence|null,
       dish: {ingredients: [{name, grams}], cooked_weight_g, servings|null}|null, review_pending: bool, numbers_hidden}
PUT  /v1/foods/{kind}/{id}/portions/{unit}  foods_portion_put {grams_per_unit: 0<x<=2000} -> FoodDetailOut   (bucket diary_writes)
     unit must be count or volume and not serving, else 422 unit_not_supported; kind food|product|off
DELETE /v1/foods/{kind}/{id}/portions/{unit}  foods_portion_delete -> 204 (idempotent)
```

  - `search_products_status(session, off, q, limit, *, account_id, settings) -> tuple[list[SearchHit], bool]`: the bool is true when OFF was throttled or unavailable. `search_products` returns `[0]` of it, so its current behaviour is unchanged.
  - Declare `/search`, `/units` and (in Task 13) `/barcode/{barcode}` before `/{kind}/{id}`. `kind` is an enum path parameter.

- [ ] **Step 1: Write the failing tests.**
  - `test_search.py`:
    - `test_search_finds_dish_by_alias` ("dal" finds "Dal tadka (toor)" and FDC 172437)
    - `test_indian_before_packaged`
    - `test_rank_prefix_first`
    - `test_query_too_short`
    - `test_off_down_returns_partial` (a fake OFF raises `OffUnavailable`: `partial: true`, `failed_sources: ["off"]`, foods still returned)
    - `test_hits_have_no_nutrients`
    - `test_attribution_on_hits` (`attribution.usda_fdc`, `attribution.smartnutri_recipe`, `attribution.off`)
  - `test_detail.py`:
    - `test_detail_lists_only_resolving_units` (packaged roti: `g`, `roti`; the plain dish dal tadka: only `g`)
    - `test_default_unit`
    - `test_settable_units`
    - `test_dish_shows_ingredients_and_review_pending`
    - `test_food_detail_redacted` (`hide_energy` → `per_100.energy_kcal` null; `hide_all` → every nutrient null; the units stay)
    - `test_unknown_food_404`
    - `test_non_primary_member_422`
  - `test_portions.py`:
    - `test_put_override_then_detail_marks_user_override`
    - `test_override_scoped_to_account` (B never sees A's override)
    - `test_put_mass_or_serving_refused` (`unit_not_supported`)
    - `test_put_bounds` (0 and 2001 → `validation_error`)
    - `test_delete_restores_global`
    - `test_product_override_by_barcode`
    - `test_rate_limited`
  - `test_consent.py`: every `foods_*` route needs `terms`, and the gate runs before the rate limiter.
- [ ] **Step 2: Run** `uv run pytest tests/api/foods -q` → FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** → PASS; `uv run pytest -q` → PASS.
- [ ] **Step 5: Commit** `feat(api): foods search, detail, units and portion overrides`.

---

### Task 5 (API): Meals for foods: quantity + unit, snapshot, patch, copy, recents *(parallel with Task 4)*

Spec: 5.1 (`meal_logs`), 6.2 (`MealIn` v2), 9.2 (round trip), 9.3. Rulings G10–G13.

**Files:**
- Modify: `apps/api/app/features/meals/{schemas,service,copy}.py`, `apps/api/app/features/diary/{service,schemas}.py` (recents)
- Test: `apps/api/tests/api/meals/{test_meals_foods,test_meals_update,test_copy}.py`, `apps/api/tests/api/diary/test_recents.py`

**Interfaces:**
- Consumes: Task 2 `ref_from_ids`, `load_food`, `portion_amount`, `resolve_units`, `unit_table`.
- Produces:
  - `MealIn` gains `food_id: UUID | None`, `quantity: float | None (gt=0, le=5000)` and `unit: UnitCode | None`.
    - Refs: exactly one of `product_id`, `barcode`, `food_id`, `quick` (else `invalid_product_ref`).
    - Portion: exactly one of `grams`, `servings`, `quantity`+`unit` (else `portion_required`; `quantity` without `unit` → `validation_error`).
  - `MealPatch` gains `quantity` + `unit` (both or neither; exclusive with `grams`/`servings`).
  - `MealOut` gains `food_id`, `quantity`, `unit`, `basis: Literal["g", "ml"]`, `attributions: list[str]` and `portion_units: list[PortionUnitOut {code, grams_per_unit}]` (from the snapshot). `SourceKind` adds `food`.
  - `food_snapshot` for every non-quick entry: `{name, brand, basis, per_100 (NUTRIENT_KEYS, unrounded), units: {code: grams_per_unit}, attribution, attributions, licence, source}`.
  - `RecentItem` gains `food_id`, `quantity`, `unit` and `attributions`; `source_kind` adds `food`. The de-duplication key becomes `(source_kind, ref id)`; rows whose ref is NULL are skipped.
- Logging a `food_id` (and a product with `quantity` + `unit`): `load_food` → `portion_amount` → `snapshot(per_100, amount)` → a row with `source_kind = food`, `grade` null, and `product_name` = the food name.
  - The `grams` form stores `unit = g`, `quantity = grams`. The `servings` form stores `unit = serving`.
  - `copy.py` carries `food_id`, `quantity` and `unit`.

- [ ] **Step 1: Write the failing tests.**
  - `test_meals_foods.py`:
    - `test_log_food_katori` (cooked dal: 1 katori → `grams` 142, `unit` `katori`, `quantity` 1, nutrients = `per_100 × 1.42` unrounded in the row, 1 dp in `MealOut`)
    - `test_log_food_count_unit_unknown_422` (`unit_grams_unknown`)
    - `test_log_food_quantity_out_of_range`
    - `test_log_product_with_user_piece_override`
    - `test_grams_form_stores_unit_g`
    - `test_food_entry_attribution_usda`
    - `test_dish_entry_incomplete_from_null_sugar` (`incomplete` lists `sugars_g` and `sat_fat_g`)
    - `test_two_refs_invalid_product_ref`
    - `test_offline_retry_client_id_returns_same_row`
  - `test_meals_update.py`:
    - `test_patch_quantity_unit_from_snapshot`
    - `test_patch_same_portion_identical_snapshot`
    - `test_override_change_keeps_past_entry` (put a user override after logging: the entry is unchanged, and a PATCH to the same unit still uses the snapshot's grams)
    - `test_patch_unit_not_in_snapshot_422`
  - `test_copy.py`: `test_copy_carries_food_quantity_unit`.
  - `test_recents.py`:
    - `test_recents_dedupe_by_food`
    - `test_recents_carry_quantity_unit`
    - `test_legacy_rows_have_null_unit`
- [ ] **Step 2: Run** `uv run pytest tests/api/meals tests/api/diary/test_recents.py -q` → FAIL.
- [ ] **Step 3: Implement.** Keep `snapshot()` and `food_snapshot()` the only builders: `food_snapshot()` gains `units` and `attributions` parameters.
- [ ] **Step 4: Run** → PASS; `uv run pytest -q` → PASS (the diary and meal fixtures are unchanged).
- [ ] **Step 5: Commit** `feat(api): log generic foods and household units in the diary`.

---

### Task 6 (API + shared): i18n, How we score food data, contract

Spec: 8 (`units.*`, `foods.*`), 9.5 (contract). Rulings G10, G13.

**Files:**
- Modify: `packages/i18n/messages/{en,hi,mr}.json`, `packages/i18n/NATIVE_REVIEW.md` (section "Plan 12 slice 3"), `packages/api-contract/**` (generated), `apps/app/lib/l10n/*.arb` (generated), `apps/app/lib/core/network/api_client.dart` and the web error mapping (only the new codes: minimal compile fixes)

**Interfaces:**
- New keys, with en drafts (ICU; mr plurals with `{count}`, never `#`):
  - `unit.{g,ml,serving,piece,piece_small,piece_medium,piece_large,roti,slice,katori,katori_small,katori_medium,katori_large,cup,glass,tbsp,tsp}`, for example `{count, plural, one {katori} other {katoris}}` and `{count, plural, one {small katori} other {small katoris}}`.
  - `unit.ml_hint` "{ml} ml"; `unit.grams_hint` "1 {unit} ≈ {grams} g"; `unit.amount_hint_ml` "1 {unit} ≈ {amount} ml"; `unit.edit_grams` "Edit grams for this measure"; `unit.set_grams` "Set grams for {unit}"; `unit.your_value` "Your value"; `unit.reset_grams` "Use the standard value"; `unit.unknown` "We don't know the grams for this measure yet. Enter grams, or set your own value."
  - `foods.search_placeholder` "Search foods, dishes or brands"; `foods.group.indian` "Indian foods"; `foods.group.packaged` "Packaged products"; `foods.partial_results` "Some results couldn't load. Try again."; `foods.no_results`; `foods.kind.{food,dish,product}`; `foods.dish_ingredients` "Made with"; `foods.review_pending` "Household measures and Indian dishes are pending dietitian review."; `foods.preview_note` "Estimate. The saved values come from SmartNutri."; `foods.not_known` "Not known"; `foods.portion.{title,quantity,save}`.
  - `diary.portion_line` "{quantity} {unit} · {grams} g"; `diary.portion_line_ml` "{quantity} {unit} · {amount} ml".
  - `attribution.usda_fdc`, `attribution.smartnutri_recipe` (G10).
  - `methodology.food_data.title` "Food data and household measures"; `methodology.food_data.body`: the USDA citation ("U.S. Department of Agriculture, Agricultural Research Service. FoodData Central. fdc.nal.usda.gov"), ICMR-NIN 2024 Annexure I for spoons and katoris, dishes calculated from their ingredients, and pending dietitian review.

- [ ] **Step 1: Write the failing check.** `pnpm --filter @smartnutri/i18n test` (`check-keys.mjs` parity) and `uv run pytest tests/unit/test_error_codes_i18n.py tests/unit/test_new_copy_no_claims.py -q` should pass before the edit and keep passing after it. `tests/api/test_openapi.py` → FAIL (drift from Tasks 4–5).
- [ ] **Step 2: Add the keys** in en, then hi and mr (machine drafts), and list them in `NATIVE_REVIEW.md` with the flags to check: the plural forms of the unit names, the word for katori in Marathi ("वाटी"), "≈", and that the dietitian note does not read as a medical claim.
- [ ] **Step 3: Regenerate** `pnpm --filter @smartnutri/i18n build`, then `cd apps/app && flutter gen-l10n`; then the justfile `contract` lines (export openapi, the Dart generator plus `dart format lib`, the TS client).
- [ ] **Step 4: Run** `uv run pytest -q`; `dart analyze` in `packages/api-contract/dart`; `cd apps/app && dart format --set-exit-if-changed lib test && flutter analyze && flutter test`; `cd apps/web && pnpm lint && npx tsc --noEmit && pnpm test` → PASS (minimal compile fixes only).
- [ ] **Step 5: Commit** `chore(contract): foods, units and diary portions` (contract and clients) and `feat(i18n): units, foods and food-data credits`.

---

### Task 7 (Android): Food search, portion picker, attribution, offline queue v3 *(parallel with Task 8)*

Use the `flutter-feature` skill. Spec: 7 (general, preview), 7.3 (search), 7.4. Rulings G10, G12, G14, G15, G30.

**Files:**
- Create:
  - `apps/app/lib/features/foods/data/foods_repository.dart`
  - `apps/app/lib/features/foods/domain/{portion_preview.dart, unit_label.dart}`
  - `apps/app/lib/features/foods/presentation/{foods_providers.dart, food_search_view.dart, portion_picker_sheet.dart}`
  - `apps/app/lib/shared/widgets/source_attribution.dart`
  - `apps/app/test/features/foods/{portion_preview_test.dart, portion_picker_test.dart, food_search_test.dart, unit_label_test.dart}`, `apps/app/test/core/storage/meal_queue_v3_migration_test.dart`
- Modify:
  - `apps/app/lib/features/diary/presentation/{add_food_sheet.dart, entry_tile.dart, edit_entry_sheet.dart}`
  - `apps/app/lib/features/meals/{domain/meal_draft.dart, data/meal_sync.dart}`, `apps/app/lib/core/storage/meal_queue.dart` (+ regenerated `.g.dart`)
  - the How we score screen (the `methodology.food_data` section)

**Interfaces:**
- Consumes: the generated `foodsSearch`, `foodsGet`, `foodsUnitsList`, `foodsPortionPut`, `foodsPortionDelete`, and `mealsLog`/`mealsUpdate` with `foodId`, `quantity` and `unit`; `RecentItem` with `quantity`, `unit` and `attributions`.
- `portion_preview.dart` (pure; the only arithmetic): `NutrientPreview previewPortion(Map<String, num?> per100, num quantity, num gramsPerUnit)` returns `String?` 1-dp values per key. It uses exact decimal maths: parse each number's `toString()` into a `BigInt` mantissa and scale, multiply, divide by 100, round half-up to 1 dp. Null stays null. No dependency is added.
- `source_attribution.dart`: `SourceAttribution(keys: List<String>)` renders each attribution key through l10n. It replaces direct uses of `OffAttribution` on diary surfaces; `OffAttribution` stays for scan and product screens.
- **Search segment** (replaces "opens the existing product search" in `add_food_sheet.dart`):
  - one box, debounced 300 ms;
  - groups `foods.group.indian` and `foods.group.packaged`, each hit with a kind badge (`foods.kind.dish` when `isDish`) and its credit;
  - the `foods.partial_results` note when `partial`; `foods.no_results` only when nothing came back and `partial` is false.
  - A tap opens the portion picker.
- **Portion picker sheet:**
  - unit chips from `units` (labels `unit.<code>` with `count` = quantity, plus `unit.ml_hint` for volume units), `defaultUnit` preselected;
  - a quantity stepper with fraction chips ¼, ½, 1, 1½, 2 and free input;
  - always the line `unit.grams_hint` with `gramsPerUnit`;
  - "Edit grams for this measure" (`foodsPortionPut`, then reload) and "Use the standard value" when `userOverride` is set;
  - "Set grams for …" listing `settableUnits`;
  - a live preview (`previewPortion`) with `foods.not_known` for null and `foods.preview_note`. Nothing for a hidden nutrient: under `numbersHidden` the preview row is not shown at all;
  - for a dish, `foods.dish_ingredients` plus `foods.review_pending`;
  - the slot chips and Save. Errors `unit_grams_unknown` and `quantity_out_of_range` map to their messages.
- **Entries and recents:** `entry_tile.dart` shows `diary.portion_line` (or `portion_line_ml` when `basis == ml`) when `unit` is set, else the existing grams or servings line, plus `SourceAttribution(attributions)`. A recent tap logs its last `quantity` + `unit` (or grams for a legacy row).
- **Edit sheet:** unit chips from `portionUnits`, a quantity field and the grams line. No nutrient preview (G12).
- **Queue v3:** `PendingMeals` gains `foodId`, `quantity` and `unit`. `MealSync.toMealIn` sends them. A queued food row shows its name and `diary.waiting_sync`, never a number.
- `diary_entry_added {method: search}` from the search segment and `{method: recent}` from recents.

- [ ] **Step 1: Write the failing tests.**
  - `portion_preview_test.dart`: `matches units/conversions.json` (every case's `preview` from `per_100`, `quantity`, `grams_per_unit`, including the 1.15 trap).
  - `portion_picker_test.dart`:
    - `picker offers only the API's units`
    - `default unit preselected`
    - `grams always shown`
    - `edit grams saves override and reloads`
    - `settable unit sets grams`
    - `unknown nutrient shows not known`
    - `hide_all shows no preview digits` (only grams and the quantity appear)
    - `dish shows ingredients and review note`
    - `unit_grams_unknown maps to message`
  - `food_search_test.dart`:
    - `groups indian before packaged`
    - `partial shows note not empty state`
    - `hits show credit`
    - `search tap sends diary_entry_added method search only`
  - `unit_label_test.dart`: `katori sizes show ml`, `plural forms per locale`.
  - `meal_queue_v3_migration_test.dart`: `v2 rows migrate and sync` and `queued food row has no numbers`.
- [ ] **Step 2: Run them** to verify they fail.
- [ ] **Step 3: Implement**, then run `dart run build_runner build --delete-conflicting-outputs`.
- [ ] **Step 4: Run** `dart format --set-exit-if-changed lib test && flutter analyze && flutter test` → PASS.
- [ ] **Step 5: Commit** `feat(app): food search, portion picker with household units, queue v3`.

---

### Task 8 (Web): Food search, portion picker, attribution, e2e *(parallel with Task 7)*

Use the `web-feature` skill. Spec: 7 (general), 7.3, 7.4, 9.6 (e2e 1). Rulings G10, G12, G14, G15.

**Files:**
- Create:
  - `apps/web/src/features/foods/{api/foods.ts, hooks/useFoods.ts, lib/preview.ts, lib/unitLabel.ts}`
  - `apps/web/src/features/foods/components/{FoodSearch.tsx, PortionPicker.tsx, SourceCredit.tsx}`
  - `apps/web/tests/features/foods/{preview.test.ts, PortionPicker.test.tsx, FoodSearch.test.tsx, unitLabel.test.ts}`, `apps/web/e2e/diary-foods.spec.ts`
- Modify:
  - `apps/web/src/features/diary/components/{AddFoodPanel.tsx, EntryRow.tsx, EditEntryDialog.tsx}`
  - the How we score page (the `methodology.food_data` section)
  - `apps/web/e2e/stub-api.mjs` (the `foods_*` routes and food entries)

**Interfaces:**
- Same behaviour as Task 7. Differences:
  - The panel is a dialog or side panel.
  - `preview.ts` uses `BigInt`-scaled decimals on `String(n)`.
  - `SourceCredit` renders each attribution key.
  - The web is online-only (the existing note).

- [ ] **Step 1: Write the failing tests.**
  - `preview.test.ts`: `matches units/conversions.json`.
  - `PortionPicker.test.tsx`: the same nine cases as Task 7 `portion_picker_test.dart`.
  - `FoodSearch.test.tsx`: the four search cases as in Task 7.
  - `unitLabel.test.ts`: as in Task 7.
  - `e2e/diary-foods.spec.ts` (spec e2e 1, adapted): search "roti", pick packaged roti, choose 2 roti, see "2 roti · 136 g", save, and the entry shows the portion line and the USDA credit. Then search "dal", pick cooked toor dal and choose katori ("1 katori ≈ 142 g"). Edit to 3 roti. Delete.
- [ ] **Step 2: Run them** to verify they fail.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `pnpm lint && npx tsc --noEmit && pnpm test && pnpm e2e` → PASS.
- [ ] **Step 5: Commit** `feat(web): food search and household-unit portion picker`.

---

### Task 9: Slice-3 gate: safety review, parity, docs

**Files:**
- Modify: `docs/FEATURE_PARITY.md` (F23 → 🟡 "code complete; units and dishes pending dietitian review"), `CONTEXT.md` (Plan 12 slice 3 status; migration 0010; `just db-migrate` now runs the seed), this plan (tick the boxes)

- [ ] **Step 1: Run everything:**
  - `cd apps/api && uv run pytest -q && uv run ruff check . && uv run ruff format --check .`
  - the `--check` mode of `generate_unit_expectations.py`, `generate_dish_expectations.py`, `generate_diary_expectations.py` and `generate_target_expectations.py`
  - `dart analyze` in `packages/api-contract/dart`
  - `cd apps/app && dart format --set-exit-if-changed lib test && flutter analyze && flutter test`
  - `cd apps/web && pnpm lint && npx tsc --noEmit && pnpm test && pnpm e2e`
  - Expected: all green; `units/conversions.json` passes on all three.
- [ ] **Step 2: Dispatch** `nutrition-safety-reviewer` on the slice diff. Scope:
  - `to_grams` refusals and every seeded number against the CSV (G4–G6);
  - the dish rules (G7, G8) and `dishes.json` (hand-check dal tadka, curd rice and chai);
  - "unknown never 0" for dish entries;
  - the katori labels (the "medium < default" wording);
  - the preview arithmetic and its hidden state;
  - attribution on every diary surface (ODbL and USDA);
  - the copy for `foods.review_pending` and `methodology.food_data`;
  - that `analyze` imports nothing from `foods`.
- [ ] **Step 3: Fix** every blocking finding (each fix with its test), then re-run Step 1.
- [ ] **Step 4: Commit** `docs: Plan 12 slice 3 parity, context and review`.

---

## Slice 4: custom foods and recipes

### Task 10 (API, db): Migration 0011, models, resolve for custom foods and recipes

Use the `api-endpoint` skill. Spec: 5.1 (`custom_food_id`, `recipe_id`), 5.6 (`food_portions.custom_food_id`), 5.8, 5.9, 9.5. Rulings G1, G19–G22.

**Files:**
- Create: `apps/api/alembic/versions/0011_diary_custom_foods_recipes.py`, `apps/api/app/features/custom_foods/{__init__,models}.py`, `apps/api/app/features/recipes/{__init__,models}.py`
- Modify:
  - `apps/api/app/features/foods/{models,resolve}.py`, `apps/api/app/features/meals/models.py`
  - `apps/api/app/features/me/service.py` (order: `recipe_ingredients` first, `recipes` after `meal_slots`, `custom_foods` after `food_portions`)
  - `apps/api/tests/db/*`, `apps/api/tests/api/test_delete_me.py`, `apps/api/tests/api/foods/test_resolve.py`

**Interfaces:**
- Produces, in the migration (all account-owned, the 0009 `_lock_down`):
  - `custom_foods`:
    - `id`, `account_id`; `name` text (1–80); `brand` text NULL; `basis` text (`g`, `ml`);
    - `per_100` jsonb (Nutrients field names); `entered` jsonb (`{values_per: "100" | "serving", serving_g, nutrients}` as typed);
    - `serving_g` numeric NULL; `density_g_per_ml` numeric NULL (0.2–2.0); `barcode` text NULL, unique `(account_id, barcode)`; `client_id` uuid NULL, unique `(account_id, client_id)`;
    - `created_at`, `updated_at`.
  - `recipes`:
    - `id`, `account_id`; `name` text (1–80); `servings` numeric NULL (0 < x ≤ 100); `cooked_weight_g` numeric NULL (0 < x ≤ 20000);
    - `total_raw_g` numeric NULL; `per_100g` jsonb (NUTRIENT_KEYS, known-part sums, unrounded); `incomplete_nutrients` text[] default `{}`;
    - `client_id` uuid NULL, unique `(account_id, client_id)`; timestamps.
  - `recipe_ingredients`:
    - `id`; `recipe_id` (FK cascade); `account_id`; `position` int; unique `(recipe_id, position)`;
    - `source_kind` text, check in (`product`, `off`, `food`, `custom_food`);
    - `product_id`, `off_barcode`, `food_id`, `custom_food_id` (FK custom_foods ON DELETE SET NULL);
    - `name` text; `quantity` numeric; `unit` text (FK household_units); `grams` numeric (basis amount); `basis` text; `weight_g` numeric NULL (mass for the raw total);
    - `per_100` jsonb (snapshot); `attribution` text NULL.
    - Check: the ref columns match `source_kind`, and `custom_food_id` may be NULL only for `custom_food` (G21).
  - `food_portions.custom_food_id` (FK cascade), the check widened to 4 refs, and a partial unique index for `custom_food_id`.
  - `meal_logs.custom_food_id`, `meal_logs.recipe_id` (FK ON DELETE SET NULL). `ck_meal_logs_source_kind` adds `custom_food` and `recipe`. `ck_meal_logs_ref` adds `(source_kind IN ('custom_food','recipe') AND product_id IS NULL AND off_barcode IS NULL AND food_id IS NULL AND grams IS NOT NULL AND num_nonnulls(custom_food_id, recipe_id) <= 1)`, plus the matching column per kind.
  - Downgrade: deletes `custom_food`/`recipe` entries and user portions with `custom_food_id`, then drops everything (documented).
- Produces, in `resolve.py`: `FoodKind` adds `custom_food` and `recipe`. `load_food` loads:
  - custom foods (account-scoped, 404 `custom_food_not_found`; units: basis, `serving_g`, density, user portions);
  - recipes (404 `recipe_not_found`; basis g; `serving_g = basis_weight / servings`; `per_100` = `to_nutrients(per_100_from(..., strict=True))`, so incomplete nutrients are None; `attributions` from the ingredients).
  - `ref_from_ids` gains `custom_food_id` and `recipe_id`.

- [ ] **Step 1: Write the failing tests.**
  - `tests/db/test_rls.py`: the three tables join `OWNED`, `TABLES` and the policy set; hidden from other accounts; writes denied.
  - `tests/db/test_constraints.py`:
    - `test_custom_food_barcode_unique_per_account`
    - `test_recipe_ingredient_ref_matches_kind`
    - `test_custom_food_delete_sets_entry_and_ingredient_null`
    - `test_meal_log_custom_food_null_allowed_after_delete`
    - `test_portion_custom_food_ref`
  - `tests/db/test_migrations.py`: `test_0011_upgrade_downgrade`.
  - `test_delete_me.py`: all three erased.
  - `test_resolve.py`:
    - `test_load_custom_food_units`
    - `test_load_recipe_strict_per_100` (an incomplete nutrient is None)
    - `test_custom_food_other_account_404`
- [ ] **Step 2: Run** `uv run pytest tests/db tests/api/foods/test_resolve.py tests/api/test_delete_me.py -q` → FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** → PASS; full suite PASS.
- [ ] **Step 5: Commit** `feat(api): migration 0011 custom foods and recipes`.

---

### Task 11 (API): Custom foods CRUD *(parallel with Task 12)*

Spec: 5.8, 6.3 (the `custom_foods_*` rows), 7.6. Rulings G15, G18, G21.

**Files:**
- Create: `apps/api/app/features/custom_foods/{schemas,service,router}.py`, `apps/api/tests/api/custom_foods/{test_create,test_update_delete,test_list}.py`
- Modify: `apps/api/app/main.py` (`CONSENT_GATES["/v1/custom-foods"] = "custom_foods"`), `apps/api/app/core/consent.py`, `packages/i18n/messages/*` (the `error.*` keys `custom_food_not_found`, `custom_food_nutrients_empty`, `barcode_already_used`)

**Interfaces:**
- Produces:

```text
CustomNutrientsIn {energy_kcal, protein_g, carbs_g, sugars_g, fat_g, sat_fat_g, fibre_g, salt_g, sodium_mg}  all optional, >= 0; absent = unknown
CustomFoodIn {name (1-80, trimmed), brand? (<=80), basis: g|ml, values_per: "100"|"serving", serving_g? (>0, basis units;
              required when values_per = serving), nutrients: CustomNutrientsIn, density_g_per_ml? (0.2-2.0),
              barcode? (normalize_barcode, else 422 invalid_barcode), portions?: [{unit, grams_per_unit}] (<=10, count/volume units), client_id?}
CustomFoodOut {id, name, brand, basis, per_100: NutrientSnapshot (unrounded), entered (as typed), serving_g, density_g_per_ml,
               barcode, portions: [{unit, grams_per_unit}], created_at, updated_at}       # not redacted (G15)
GET    /v1/custom-foods           custom_foods_list   -> {items: CustomFoodOut[], next_cursor}   (limit 1-100, default 50; cursor = opaque (updated_at, id))
POST   /v1/custom-foods           custom_foods_create -> 201 (200 on a repeated client_id)        (bucket diary_writes)
PUT    /v1/custom-foods/{id}      custom_foods_update -> CustomFoodOut (full replace; portions replaced)   (diary_writes)
DELETE /v1/custom-foods/{id}      custom_foods_delete -> 204
```

  - Rules:
    - `values_per = serving` → `per_100 = value × 100 / serving_g`.
    - Energy or at least one of protein, carbs and fat must be known, else `422 custom_food_nutrients_empty`.
    - Salt and sodium follow `Nutrients.salt()`.
    - The stored `per_100` passes `implausible_fields` (else `422 implausible_value`).
    - A duplicate barcode in the account is `422 barcode_already_used`.
    - Never in the public catalogue, never fed to `analyze`.

- [ ] **Step 1: Write the failing tests.**
  - `test_create.py`:
    - `test_create_per_100`
    - `test_create_per_serving_converts` (12 g protein per 30 g serving → 40 per 100)
    - `test_blank_stays_null_never_zero`
    - `test_nutrients_empty_422`
    - `test_implausible_422`
    - `test_barcode_duplicate_422`
    - `test_client_id_retry_200` (including the concurrent race, as in `meals_log`)
    - `test_portions_created_as_user_rows`
    - `test_ml_basis_with_density`
  - `test_update_delete.py`:
    - `test_put_replaces_and_can_clear_nutrient`
    - `test_delete_custom_food_keeps_history_and_recents_skip_it` (log, delete: the entry keeps its name and values with `custom_food_id` null, and recents leave it out)
    - `test_other_account_404`
    - `test_custom_food_never_reaches_analyze` (the import graph: `analyze` does not import `custom_foods`; `products_get_by_barcode` for that barcode does not return the custom food)
  - `test_list.py`: `test_cursor_stable`, `test_limit_bounds`.
- [ ] **Step 2: Run** `uv run pytest tests/api/custom_foods -q` → FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat(api): custom foods`.

---

### Task 12 (API): Recipes, recipe fixtures, logging custom foods and recipes *(parallel with Task 11)*

Spec: 5.9, 6.3 (the `recipes_*` rows), 7.7, 9.3. Rulings G15, G19–G22.

**Files:**
- Create:
  - `apps/api/app/features/recipes/{schemas,service,router}.py`
  - `apps/api/scripts/generate_recipe_expectations.py`, `packages/test-fixtures/recipes/{inputs,expected}/*.json`
  - `apps/api/tests/api/recipes/{test_recipes,test_recipe_fixtures}.py`
- Modify:
  - `apps/api/app/features/meals/{schemas,service,copy}.py`, `apps/api/app/features/diary/{service,schemas}.py`
  - `apps/api/app/main.py`, `apps/api/app/core/consent.py`
  - `packages/i18n/messages/*` (the `error.*` keys `recipe_not_found`, `recipe_ingredient_limit`, `recipe_weight_invalid`, `custom_food_not_found` if Task 11 has not merged yet)
  - `packages/test-fixtures/README.md` ("Recipes")
- Test: `apps/api/tests/api/meals/test_meals_custom_recipe.py`, `apps/api/tests/api/diary/test_recents.py`

**Interfaces:**
- Consumes: Task 3 `recipe_math`; Task 10 `load_food` for the `custom_food` and `recipe` kinds.
- Produces:

```text
RecipeIngredientIn {food_id?|custom_food_id?|product_id?|barcode?, quantity (>0), unit: UnitCode}     # exactly one ref (invalid_product_ref)
RecipeIn {name (1-80, trimmed), servings? (0<x<=100), cooked_weight_g? (0<x<=20000), ingredients: 1-50 (else recipe_ingredient_limit), client_id?}
RecipeOut {id, name, servings, cooked_weight_g, total_raw_g|null, basis_weight_g, per_100g: NutrientSnapshot (1 dp; known-part sums),
           per_serving: NutrientSnapshot|null (1 dp), incomplete_nutrients: [key], attributions,
           ingredients: [{position, source_kind, food_id, custom_food_id, product_id, barcode, name, quantity, unit, grams, attribution, available}],
           numbers_hidden, updated_at}                                                    # numbers redacted (G15)
RecipeSummaryOut {id, name, servings, incomplete_nutrients, updated_at}
GET /v1/recipes recipes_list -> {items, next_cursor};  GET /v1/recipes/{id} recipes_get;  POST recipes_create -> 201 (200 on client_id);
PUT /v1/recipes/{id} recipes_update;  DELETE recipes_delete -> 204          (writes: bucket diary_writes)
```

  - Each ingredient: `load_food` → `portion_amount` (a failure is `422 unit_grams_unknown` with `details.position`) → snapshot `per_100` (NUTRIENT_KEYS) → `Amount`.
  - Then `sum_nutrients`. `total_raw_g` = Σ weight (ml-basis ingredients only through density; else None). The basis weight follows G20.
  - Stored `per_100g = per_100_from(sums, basis, strict=False)` and `incomplete_nutrients = sums.incomplete`.
  - `available` is false when `custom_food_id` became NULL after a delete. A PUT must then replace that ingredient (`invalid_product_ref` if it is re-sent without a ref).
  - `MealIn`/`MealOut`/`RecentItem` gain `custom_food_id` and `recipe_id`; `SourceKind` adds `custom_food` and `recipe`.
    - A recipe entry's snapshot uses `per_100_from(..., strict=True)` (G19), units `g` and `serving`, and the ingredients' `attributions`.
    - A custom-food entry's attribution is null.
  - `copy.py` carries both ids.
- **Recipe fixtures** (`packages/test-fixtures/recipes/`, generated by `generate_recipe_expectations.py`, `--check`/`--write`). Inputs use synthetic ingredients with per_100 and grams. Expected = `{total_raw_g, basis_weight_g, per_100g, per_serving, incomplete_nutrients, entry_snapshot_per_100}`. Cases:
  - `recipe_complete`;
  - `recipe_missing_fibre` (one of three ingredients has fibre null: fibre is a known-part sum and listed incomplete, and the entry snapshot's fibre is null);
  - `recipe_all_unknown_sat_fat` (null);
  - `recipe_cooked_weight` (400 g raw, 300 g cooked);
  - `recipe_servings_4`;
  - `recipe_ml_ingredient_density`;
  - `recipe_ml_ingredient_no_density_needs_cooked_weight` (expected error);
  - `recipe_weight_out_of_range` (cooked > 3 × raw, expected error).

- [ ] **Step 1: Write the failing tests.**
  - `test_recipe_fixtures.py`:
    - `test_matches_fixtures`
    - a hand check of `recipe_missing_fibre`: fibre per 100 g = (f₁·g₁ + f₂·g₂)/basis × 100 with ingredient 3 left out, and the entry snapshot's fibre is None.
  - `test_recipes.py`:
    - `test_create_get_list`
    - `test_ingredient_limit_51`
    - `test_unit_grams_unknown_has_position`
    - `test_weight_invalid_reasons`
    - `test_recipe_out_redacted` (`hide_all`: `per_100g` and `per_serving` all null, and `incomplete_nutrients` stays)
    - `test_recipe_edit_keeps_past_entries`
    - `test_deleted_custom_ingredient_unavailable`
    - `test_off_ingredient_attribution_kept`
    - `test_other_account_404`
    - `test_client_id_retry`
  - `test_meals_custom_recipe.py`:
    - `test_log_recipe_serving`
    - `test_recipe_entry_nulls_incomplete_nutrients`
    - `test_day_incomplete_after_recipe_entry` (a recipe whose one ingredient lacks protein, logged on a day with a ready target: the day has `incomplete.protein_g` true and `remaining.protein_g` null, while `remaining.energy_kcal` is still a number)
    - `test_log_custom_food_katori_via_density`
    - `test_log_deleted_recipe_404`
  - `test_recents.py`: `test_recents_include_custom_and_recipe`, `test_recents_skip_null_refs`.
- [ ] **Step 2: Run** `uv run pytest tests/api/recipes tests/api/meals tests/api/diary/test_recents.py -q` → FAIL.
- [ ] **Step 3: Implement**, then run the fixture script with `--write`.
- [ ] **Step 4: Run** → PASS; `--check` → no diff; full suite PASS.
- [ ] **Step 5: Commit** `feat(api): recipes from ingredients, and logging custom foods and recipes`.

---

### Task 13 (API + shared): Search and detail for my foods, the barcode route, i18n, contract

Spec: 6.3 (search order, barcode), 7.3, 7.6, 7.7, 8. Rulings G16, G17.

**Files:**
- Modify:
  - `apps/api/app/features/foods/{schemas,service,router}.py`
  - `packages/i18n/messages/{en,hi,mr}.json`, `packages/i18n/NATIVE_REVIEW.md` ("Plan 12 slice 4")
  - `packages/api-contract/**` (generated), the ARB files (generated), plus minimal client compile fixes
- Test: `apps/api/tests/api/foods/{test_search,test_detail,test_barcode}.py`

**Interfaces:**
- `foods_search` `kinds` adds `custom_food` and `recipe` (default: all). The group `mine` comes first: the account's custom foods and recipes by name rank. `FoodHit.kind` adds both.
- `foods_get` accepts `custom_food` (units, user portions, `settable_units`; `per_100` redacted like other foods) and `recipe` (units `g` and `serving`, `per_100` strict and redacted, plus `recipe_incomplete: [key]`). `foods_portion_*` accepts `custom_food`.
- New: `GET /v1/foods/barcode/{barcode}` `foods_by_barcode` → `FoodDetailOut`. It returns the account's custom food with that barcode, else the product or OFF detail. Errors: `invalid_barcode`, `product_not_found`, `off_unavailable`. Bucket `product_lookups`.
- New keys (en drafts):
  - `foods.group.mine` "My foods and recipes"; `foods.kind.{custom_food,recipe}`; `foods.new_food` "New food"; `foods.new_recipe` "New recipe"; `foods.my_foods` "My foods and recipes"; `foods.values_per.{100g,100ml,serving}`.
  - `custom_food.{title,name,brand,basis_g,basis_ml,serving_size,density,density_hint,barcode,portions,save,saved,delete,delete_confirm,history_kept}` and `custom_food.field.{sugars,sat_fat,salt,sodium}`. Energy, protein, fat, carbs and fibre reuse `diary.quick_add.*`.
  - `recipes.{title,name,ingredients,add_ingredient,servings,cooked_weight,cooked_weight_tip,per_serving,per_100g,incomplete,ingredient_unavailable,log_serving,delete_confirm,saved,empty}`, where `recipes.incomplete` is "Some ingredients don't show this value, so the real amount may be higher." and `recipes.cooked_weight_tip` is "Weigh the pot after cooking for the best accuracy."

- [ ] **Step 1: Write the failing tests.**
  - `test_search.py`: `test_mine_first`, `test_other_accounts_custom_foods_never_found`.
  - `test_detail.py`: `test_custom_food_detail_units`, `test_recipe_detail_strict_and_incomplete`.
  - `test_barcode.py`: `test_own_custom_food_first`, `test_falls_back_to_product`, `test_other_account_custom_barcode_not_used`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement.** Then add the keys and the NATIVE_REVIEW flags ("cooked weight", "per serving", "values per 100 g", and that `recipes.incomplete` stays tentative). Regenerate i18n and the ARB files, then the contract.
- [ ] **Step 4: Run** the full checks as Task 6 Step 4 → PASS.
- [ ] **Step 5: Commit** `feat(api): my foods in search, barcode lookup for logging`, `feat(i18n): custom foods and recipes`, `chore(contract): custom foods and recipes`.

---

### Task 14 (Android): Custom food form, my foods, recipe builder, queue v4 *(parallel with Task 15)*

Use the `flutter-feature` skill. Spec: 7.3 (create, barcode), 7.6, 7.7, 9.6 (e2e 5 as a widget flow). Rulings G18–G21, G30.

**Files:**
- Create:
  - `apps/app/lib/features/foods/presentation/{custom_food_form.dart, my_foods_screen.dart}`
  - `apps/app/lib/features/recipes/{data/recipes_repository.dart, presentation/recipe_builder_screen.dart, presentation/recipe_nutrients.dart}`
  - `apps/app/test/features/foods/{custom_food_form_test.dart, my_foods_test.dart}`, `apps/app/test/features/recipes/{recipe_builder_test.dart, recipe_nutrients_test.dart}`, `apps/app/test/core/storage/meal_queue_v4_migration_test.dart`
- Modify: `apps/app/lib/features/diary/presentation/add_food_sheet.dart` (the Create segment, `mine` group, barcode via `foodsByBarcode`), the router (`/diary/foods/new`, `/diary/foods/:id`, `/diary/recipes/new`, `/diary/recipes/:id`, `/diary/my-foods`), `meal_queue.dart` (v4: `customFoodId`, `recipeId`), `meal_draft.dart`, `meal_sync.dart`, Profile "Diary and daily guide" (a My foods entry)

**Interfaces:**
- **Custom food form:**
  - name, brand, basis (g or ml), values per 100 or per serving (with serving size), the nutrient fields with `foods.blank_is_unknown`, density (ml basis), barcode, and optional household-unit grams (count and volume units from `foodsUnitsList`);
  - blank fields are sent as absent, never 0;
  - errors come from the API (`custom_food_nutrients_empty`, `implausible_value`, `barcode_already_used`);
  - delete shows `custom_food.history_kept`. The form is online-only.
- **My foods screen:** the custom foods and recipes lists, paginated by cursor, with edit and delete.
- **Recipe builder:**
  - a name; ingredients added through the same food search and portion picker (Task 7) in "ingredient" mode (no slot, nothing logged);
  - servings, and cooked weight with `recipes.cooked_weight_tip`;
  - before saving, the ingredient list only (no numbers);
  - after saving, `RecipeNutrients` renders `per_100g` and `per_serving` from `RecipeOut`. A key in `incomplete_nutrients` shows `diary.week.at_least` plus the grey incomplete marker and `recipes.incomplete`. A null shows `foods.not_known`.
  - An ingredient with `available == false` shows `recipes.ingredient_unavailable` and must be replaced before saving.
  - "Log a serving" opens the portion picker for the `recipe` kind.
- **Barcode in the diary:** `foodsByBarcode` first, then the portion picker. The existing verdict screen stays reachable ("See if it suits you"), and the verdict is unchanged.
- **Queue v4:** custom-food and recipe entries can be queued offline (`diary_entry_added` method `custom` or `recipe`).

- [ ] **Step 1: Write the failing tests.**
  - `custom_food_form_test.dart`:
    - `blank sends absent not zero`
    - `per serving sends values_per serving`
    - `api errors map to messages`
    - `delete shows history kept note`
  - `my_foods_test.dart`: `lists custom foods and recipes`, `paginates`.
  - `recipe_builder_test.dart`:
    - `adds ingredient through picker without logging`
    - `no numbers before save`
    - `unavailable ingredient blocks save`
    - `log a serving opens recipe picker`
  - `recipe_nutrients_test.dart`:
    - `renders recipes/expected recipe_missing_fibre` (fibre shows "At least …" with the incomplete marker)
    - `incomplete recipe nutrient renders at least, never a plain number`
    - `hide_all shows no digits` (a redacted `RecipeOut`)
  - `meal_queue_v4_migration_test.dart`: `v3 rows migrate`, `queued recipe entry syncs with recipe_id`.
- [ ] **Step 2: Run them** to verify they fail.
- [ ] **Step 3: Implement**, then run `build_runner`.
- [ ] **Step 4: Run** `dart format --set-exit-if-changed lib test && flutter analyze && flutter test` → PASS.
- [ ] **Step 5: Commit** `feat(app): custom foods, my foods and the recipe builder`.

---

### Task 15 (Web): Custom food form, my foods, recipe builder, e2e *(parallel with Task 14)*

Use the `web-feature` skill. Spec: 7.3, 7.6, 7.7, 9.6 (e2e 5). Rulings G18–G21.

**Files:**
- Create:
  - `apps/web/src/features/foods/components/{CustomFoodForm.tsx, MyFoods.tsx}`
  - `apps/web/src/features/recipes/{api/recipes.ts, hooks/useRecipes.ts, components/RecipeBuilder.tsx, components/RecipeNutrients.tsx}`
  - pages `apps/web/src/app/[locale]/(app)/diary/{foods/new, foods/[id], recipes/new, recipes/[id], my-foods}/page.tsx`
  - tests `apps/web/tests/features/foods/{CustomFoodForm,MyFoods}.test.tsx`, `apps/web/tests/features/recipes/{RecipeBuilder,RecipeNutrients}.test.tsx`, `apps/web/e2e/diary-recipes.spec.ts`
- Modify: `AddFoodPanel.tsx` (Create segment, `mine` group, barcode via `foods_by_barcode`), `stub-api.mjs`, the Profile diary settings (a My foods link)

**Interfaces:**
- The same behaviour as Task 14, online-only.

- [ ] **Step 1: Write the failing tests:** the same cases as Task 14 (component tests). Plus `e2e/diary-recipes.spec.ts`: create a recipe from two ingredients with 2 servings and a cooked weight → the saved recipe shows "At least" on the incomplete nutrient → log one serving → the entry shows on the day with its credit.
- [ ] **Step 2: Run them** to verify they fail.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `pnpm lint && npx tsc --noEmit && pnpm test && pnpm e2e` → PASS.
- [ ] **Step 5: Commit** `feat(web): custom foods, my foods and the recipe builder`.

---

### Task 16: Slice-4 gate: safety review, parity, docs

**Files:** `docs/FEATURE_PARITY.md` (F24 → 🟡), `CONTEXT.md` (migration 0011), this plan.

- [ ] **Step 1: Run everything** as Task 9 Step 1, plus `generate_recipe_expectations.py --check`.
- [ ] **Step 2: Dispatch** `nutrition-safety-reviewer` on the slice diff. Scope:
  - G19 (known-part sums versus entry snapshots) against `recipes/expected`;
  - the "at least" rendering on both clients;
  - custom foods kept out of verdicts (G17, the import graph);
  - the blank-is-unknown form copy;
  - the plausibility checks on typed values;
  - deletes keeping history (G21);
  - redaction (G15), including the unredacted `CustomFoodOut`;
  - ODbL credit for OFF ingredients inside recipes.
- [ ] **Step 3: Fix** blocking findings with tests, then re-run Step 1.
- [ ] **Step 4: Commit** `docs: Plan 12 slice 4 parity, context and review`.

---

## Slice 5: favourites and recents

### Task 17 (API + shared): Migration 0012, favourites routes, the recents star, i18n, contract

Use the `api-endpoint` skill. Spec: 5.10, 6.4, 7.3 (recent, favourites), 9.5. Rulings G1, G21, G23.

**Files:**
- Create:
  - `apps/api/alembic/versions/0012_diary_favourites.py`
  - `apps/api/app/features/favourites/{__init__,models,schemas,service,router}.py`
  - `apps/api/tests/api/favourites/{test_food_favourites,test_meal_favourites,test_log}.py`
- Modify:
  - `apps/api/app/features/diary/{service,schemas}.py` (`RecentItem.favourite_id`)
  - `apps/api/app/features/meals/copy.py` (extract the snapshot-to-entry step, so that copy and favourite meals share it)
  - `apps/api/app/main.py`, `apps/api/app/core/consent.py`, `apps/api/app/features/me/service.py` (`favourites` after `recipe_ingredients`)
  - `apps/api/tests/db/*`, `apps/api/tests/api/test_delete_me.py`
  - `packages/i18n/*`, `NATIVE_REVIEW.md` ("Plan 12 slice 5"), the contract (generated)

**Interfaces:**
- Produces, in the migration, the table `favourites` (member-scoped, with the composite FK `(member_id, account_id) → members(id, account_id)` ON DELETE CASCADE, the 0009 `_lock_down`):
  - `id`, `account_id`, `member_id`; `kind` text (`food`, `meal`); `source_kind` text NULL (`product`, `off`, `food`, `custom_food`, `recipe`; NULL for meals);
  - `product_id`, `off_barcode`, `food_id`, `custom_food_id` (FK cascade), `recipe_id` (FK cascade);
  - `name` text (a snapshot for foods; the user-typed name, 1–40 code points, for meals);
  - `default_quantity` numeric NULL; `default_unit` text NULL (FK household_units);
  - `items` jsonb NULL (meals: a list of `{source_kind, product_id, off_barcode, food_id, custom_food_id, recipe_id, product_name, grade, grams, quantity, unit, nutrients, food_snapshot}`);
  - `client_id` uuid NULL, unique `(account_id, client_id)`; `created_at`.
  - Checks: `kind = 'food'` ⇔ exactly one ref matching `source_kind` and `items IS NULL`; `kind = 'meal'` ⇔ no ref and `items IS NOT NULL`.
  - Partial unique indexes `(member_id, <ref>) WHERE <ref> IS NOT NULL`, one per ref column.
- Routes (terms by prefix; writes use `diary_writes`; `targets_service.resolve_member`):

```text
GET    /v1/favourites?member_id          favourites_list -> {items: FavouriteOut[]}   (newest first; <= 200, no cursor)
POST   /v1/favourites                    favourites_add  {member_id?, product_id?|barcode?|food_id?|custom_food_id?|recipe_id?,
                                          default_quantity?, default_unit?} -> 201 FavouriteOut (200 if it exists)
POST   /v1/favourites/meals              favourites_add_meal {member_id?, from_date, from_slot_id, name, client_id?} -> 201 FavouriteOut
                                          (errors: copy_source_empty, copy_too_many (>50), meal_slot_not_found, date_in_future)
POST   /v1/favourites/{id}/log           favourites_log {meal_slot_id?, local_date?, client_id (required)} -> 201 {created: MealOut[]}
                                          (200 on retry; meal favourites only, else 422 validation_error; each item counts against meal_logs)
DELETE /v1/favourites/{id}               favourites_delete -> 204
FavouriteOut {id, member_id, kind, source_kind, product_id, barcode, food_id, custom_food_id, recipe_id, name,
              default_quantity, default_unit, item_count, items: [{name, quantity, unit, grams, source_kind, attributions}]|null,
              attributions, created_at}
```

  - More than 200 favourites per member is `422 favourite_limit`; an unknown id is `404 favourite_not_found`.
  - `favourites_log` builds entries from the item snapshots, as copy does: `client_id = uuid5(request.client_id, f"{fav.id}:{index}")`, `eaten_at` from `local_date` (Ruling E8) or now, and the slot from `meal_slot_id` or the server's pick. Any `custom_food_id`/`recipe_id` that no longer exists becomes NULL (G21). The response is redacted like every `MealOut`.
  - `RecentItem.favourite_id`: the member's food favourite for the same ref, else null.
- New keys:
  - `foods.favourites` "Favourites";
  - `favourites.{add,remove,added,save_meal,meal_name,meal_name_hint,meal_items,log_again,empty,limit}`, where `favourites.meal_items` is `{count, plural, one {# item} other {# items}}` (mr with `{count}`) and `favourites.meal_name_hint` is "Names you type are kept exactly as you type them.";
  - errors `favourite_not_found`, `favourite_limit`.

- [ ] **Step 1: Write the failing tests.**
  - `tests/db`: RLS, constraints (`test_food_favourite_exactly_one_ref`, `test_meal_favourite_has_items_no_ref`, `test_unique_food_favourite_per_member`, `test_custom_food_delete_cascades_favourite`), `test_0012_upgrade_downgrade`, and delete-me.
  - `test_food_favourites.py`:
    - `test_add_returns_201_then_200`
    - `test_limit_200`
    - `test_list_newest_first`
    - `test_recents_star_id`
    - `test_non_primary_422`
    - `test_other_account_404`
  - `test_meal_favourites.py`:
    - `test_save_meal_snapshots_slot_entries`
    - `test_empty_slot_copy_source_empty`
    - `test_name_kept_as_typed_and_never_in_analytics_or_logs` (a payload test, as for slot labels)
  - `test_log.py`:
    - `test_log_meal_creates_entries_from_snapshots`
    - `test_retry_returns_same_rows_200`
    - `test_deleted_custom_food_item_logs_with_null_ref`
    - `test_counts_against_meal_logs`
    - `test_food_favourite_log_422`
    - `test_log_redacted_under_hide_all`
- [ ] **Step 2: Run** `uv run pytest tests/db tests/api/favourites tests/api/diary/test_recents.py -q` → FAIL.
- [ ] **Step 3: Implement**, then add the keys and the NATIVE_REVIEW flags, regenerate i18n and the ARB files, then the contract.
- [ ] **Step 4: Run** the full checks as Task 6 Step 4 → PASS.
- [ ] **Step 5: Commit** `feat(api): favourite foods and meals, and the recents star`, `feat(i18n): favourites`, `chore(contract): favourites`.

---

### Task 18 (Android): Favourites segment, star, save meal, log again *(parallel with Task 19)*

Use the `flutter-feature` skill. Spec: 7.3 (favourites), 7.4 (the "Add to favourites" toggle). Rulings G23, G30.

**Files:**
- Create: `apps/app/lib/features/favourites/{data/favourites_repository.dart, presentation/favourites_segment.dart, presentation/favourite_star.dart, presentation/save_meal_favourite_sheet.dart}`, `apps/app/test/features/favourites/{favourites_segment_test.dart, favourite_star_test.dart, save_meal_test.dart}`
- Modify: `add_food_sheet.dart` (a Favourites segment after Recent), `portion_picker_sheet.dart` (an "Add to favourites" toggle that saves the chosen quantity and unit as the default), `slot_section.dart` (slot menu: `favourites.save_meal`), recent rows (star)

**Interfaces:**
- **Favourites segment:**
  - Food favourites: one tap logs `defaultQuantity` + `defaultUnit` through `mealsLog`, which can be queued offline (`method: favourite`). A long press opens the portion picker.
  - Meal favourites: show the name (user text, exactly as typed) and `favourites.meal_items`; "Log again" calls `favouritesLog`, online-only, with a fresh `client_id` per action that is reused on retry. The toast shows the count only.
- **Star:** toggles `favouritesAdd`/`favouritesDelete` on recents and in the picker, using `favouriteId`.
- **Save meal sheet:** a name field (1–40 code points, `favourites.meal_name_hint`) → `favouritesAddMeal` for that slot and day.
- No name, unit or number is ever sent to analytics.

- [ ] **Step 1: Write the failing tests.**
  - `favourites_segment_test.dart`:
    - `food favourite tap logs default portion with method favourite`
    - `food favourite queues offline`
    - `meal favourite log again sends client_id and toasts count only under hide_all`
    - `retry reuses client_id`
    - `empty state`
  - `favourite_star_test.dart`: `star toggles add and delete`, `limit error shows message`.
  - `save_meal_test.dart`:
    - `name kept exactly as typed in hi and mr`
    - `empty slot shows copy_source_empty message`
    - `name never in analytics`
- [ ] **Step 2: Run them** to verify they fail.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `dart format --set-exit-if-changed lib test && flutter analyze && flutter test` → PASS.
- [ ] **Step 5: Commit** `feat(app): favourite foods and meals`.

---

### Task 19 (Web): Favourites segment, star, save meal, log again, e2e *(parallel with Task 18)*

Use the `web-feature` skill. Rulings G23.

**Files:**
- Create: `apps/web/src/features/favourites/{api/favourites.ts, hooks/useFavourites.ts, components/FavouritesSegment.tsx, components/FavouriteStar.tsx, components/SaveMealFavouriteDialog.tsx}`, `apps/web/tests/features/favourites/*.test.tsx`, `apps/web/e2e/diary-favourites.spec.ts`
- Modify: `AddFoodPanel.tsx`, `PortionPicker.tsx`, `SlotSection.tsx`, `stub-api.mjs`

- [ ] **Step 1: Write the failing tests:** the Task 18 cases (component tests; no offline case). Plus `e2e/diary-favourites.spec.ts`: star a recent → it appears under Favourites → one tap logs it. Then save Breakfast as "My usual breakfast" → on the next day, "Log again" adds its items.
- [ ] **Step 2: Run them** to verify they fail.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `pnpm lint && npx tsc --noEmit && pnpm test && pnpm e2e` → PASS.
- [ ] **Step 5: Commit** `feat(web): favourite foods and meals`.

---

### Task 20: Slice-5 gate

**Files:** `docs/FEATURE_PARITY.md` (F25 → 🟡), `CONTEXT.md` (migration 0012), this plan.

- [ ] **Step 1: Run everything** as Task 9 Step 1.
- [ ] **Step 2: Dispatch** `nutrition-safety-reviewer`. Scope:
  - hidden numbers on favourite rows, log-again toasts and the star;
  - favourite-meal names as user text (never analytics, logs or prompts; no translation);
  - re-log snapshot semantics and their staleness (copy rules);
  - deleted refs (G21).
- [ ] **Step 3: Fix** blocking findings with tests, then re-run Step 1.
- [ ] **Step 4: Commit** `docs: Plan 12 slice 5 parity, context and review`.

---

## Slice 6: the weight log, trend and taper

### Task 21 (API, db): Migration 0013 with back-fill, model, weigh-in store *(parallel with Task 22)*

Use the `api-endpoint` skill. Spec: 5.4, 5.11 (back-fill), 9.5. Rulings G1, G26.

**Files:**
- Create: `apps/api/alembic/versions/0013_diary_weight_logs.py`, `apps/api/app/features/weights/{__init__,models,store}.py`, `apps/api/tests/api/weights/test_store.py`
- Modify: `apps/api/app/features/me/service.py` (`weight_logs` before `diary_days`), `apps/api/tests/db/*`, `apps/api/tests/api/test_delete_me.py`

**Interfaces:**
- Produces, in the migration, the table `weight_logs` (member-scoped, with the composite FK and `_lock_down`):
  - `id`, `account_id`, `member_id`; `local_date` date, unique `(member_id, local_date)`;
  - `weight_kg` numeric, check 2–300; `measured_at` timestamptz;
  - `source` text default `'manual'`, check in (`manual`) (Q4);
  - `client_id` uuid NULL, unique `(account_id, client_id)`; `created_at`, `updated_at`.
  - Back-fill: for each member with `weight_kg` between 2 and 300, one row with `local_date = (members.updated_at AT TIME ZONE accounts.timezone)::date`, `measured_at = members.updated_at` and `source = 'manual'`. The downgrade drops the table (documented: weigh-ins are lost; `members.weight_kg` keeps the latest).
- Produces, in `weights/store.py` (no import of `diary`, `targets` or `weights.service`, so members and targets can import it without a cycle):

```python
async def upsert_weigh_in(session: AsyncSession, member: Member, day: date, weight_kg: Decimal,
                          measured_at: datetime, client_id: UUID | None = None) -> WeightLog    # one per day; replaces
async def list_weigh_ins(session: AsyncSession, member: Member, *, until: date | None = None,
                         since: date | None = None) -> list[WeightLog]                          # oldest first
async def delete_weigh_in(session: AsyncSession, member: Member, day: date) -> WeightLog | None
async def latest(session: AsyncSession, member: Member) -> WeightLog | None
```

- [ ] **Step 1: Write the failing tests.**
  - `tests/db`:
    - RLS (`OWNED`, `KEY` = `id`, the policy set);
    - `test_one_weigh_in_per_day`
    - `test_weight_range_check`
    - `test_source_manual_only`
    - `test_0013_backfill_dates_in_account_zone` (an account in `America/New_York`, a member updated at 2026-11-07T02:00Z → local date 2026-11-06; a member with weight 400 → no row)
    - `test_0013_downgrade`
  - delete-me erases `weight_logs`.
  - `test_store.py`: `test_upsert_replaces_same_day`, `test_list_order_and_bounds`, `test_delete_returns_row`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** → PASS; full suite PASS.
- [ ] **Step 5: Commit** `feat(api): migration 0013 weight logs with back-fill`.

---

### Task 22 (API, engine): Pure weight trend, YAML keys, weight fixtures, ADR 0025 *(parallel with Task 21; may start any time)*

Use the `scoring-rule` skill. Spec: 4.5, 4.9, 4.10 (step 2), 4.11 (rapid loss), 6.5 (`WeightTrendOut`). Rulings G24, G25, G27, G28, G32.

**Files:**
- Create: `apps/api/app/scoring/weight_trend.py`, `apps/api/tests/unit/scoring/test_weight_trend.py`, `apps/api/scripts/generate_weight_expectations.py`, `packages/test-fixtures/weights/{inputs,expected}/*.json`, `docs/adr/0025-weight-trend.md`
- Modify: `apps/api/app/scoring/data/targets.yaml`, `apps/api/tests/unit/scoring/test_targets_yaml.py` (the import graph: `verdict.py` and the analyze service must not import `weight_trend`), `packages/test-fixtures/README.md` ("Weight trend")

**Interfaces:**
- `targets.yaml` additions (PENDING CLINICIAN REVIEW; each has a `section_sources` entry `smartnutri_working_values`, with `icmr_nin_2024` and `cdc_weight_loss` where relevant):

```yaml
trend:
  min_weigh_ins_for_trend: 3        # spec 4.9
  alpha_per_day: 0.25               # ~7-day smoothing: mean lag (1-a)/a = 3 days, like a centred 7-day average
  outlier_pct_from_trend: 3.0       # spec 4.10
  min_weigh_ins_for_rate: 3
  rate_window_days: 7
projection: {min_weigh_ins: 6, min_span_days: 14, max_horizon_days: 730}
safety: {rapid_loss_pct_bw_per_week: 1.5, rapid_loss_weeks: 3}
# plausible: gains weight_change_kg_per_day: 2.0   (spec 6.5)
```

- Produces, in `weight_trend.py` (pure, `Decimal`; reads `cfg.targets`):

```python
@dataclass(frozen=True, slots=True)
class WeighIn: day: date; kg: Decimal
@dataclass(frozen=True, slots=True)
class TrendPoint: day: date; kg: Decimal; outlier: bool
@dataclass(frozen=True, slots=True)
class TrendResult:
    points: tuple[TrendPoint, ...]                  # every weigh-in, oldest first
    trend: tuple[tuple[date, Decimal], ...]         # one value per non-outlier weigh-in date (unrounded)
    def at(self, day: date) -> Decimal | None       # trend at the latest non-outlier weigh-in <= day
def compute_trend(weigh_ins: Sequence[WeighIn], cfg: ScoringConfig | None = None) -> TrendResult
def weight_for_targets(weigh_ins: Sequence[WeighIn], day: date, cfg=None) -> Decimal | None   # trend at day if >= 3 non-outliers <= day, else None
def weekly_rate(result: TrendResult, cfg=None, *, end: date | None = None) -> tuple[Decimal, Decimal] | None   # (kg, pct of T(end)); None per G24
def rapid_loss(result: TrendResult, cfg=None) -> bool
ProjectionReason = Literal["ready", "too_few_weigh_ins", "moving_away", "no_target", "too_far", "reached"]
def projection(result: TrendResult, target_kg: Decimal | None, cfg=None) -> tuple[ProjectionReason, date | None]
def shape(values: Sequence[Decimal | None]) -> list[Decimal | None]   # (v - min)/(max - min), 2 dp half-up; all equal -> 0.5; None stays None
```

- The trend algorithm (the signature does not decide it):

```text
T = None; pending = None                       # pending: (weigh-in, T before it) for a first out-of-band weigh-in
for w in weigh_ins (oldest first):
    if T is None: T = w.kg; accept(w); continue
    out = |w.kg - T| / T * 100 > outlier_pct
    if not out:
        pending = None; T = step(T, w); accept(w)
    elif pending is not None and sign(w.kg - T) == sign(pending.w.kg - T):
        T = step(T, pending.w); un-mark pending.w as outlier; accept(pending.w)   # two in a row on one side: a real change
        T = step(T, w); accept(w); pending = None
    else:
        mark w outlier; pending = (w, T)               # T unchanged
step(T, w) = T + (1 - (1 - alpha) ** g) * (w.kg - T), with g = days since the previously ACCEPTED weigh-in (>= 1)
```

  - Weekly rate: `T(last) − T(last − 7)`, where `last` is the latest non-outlier date. It needs ≥ 3 non-outlier weigh-ins and some non-outlier weigh-in on or before `last − 7`. The pct is `kg / T(last) × 100`.
  - Rapid loss: the rates ending at `last`, `last − 7` and `last − 14` are all ≤ −1.5 %.
  - Projection precedence: `no_target` → `reached` (|T(last) − target| ≤ `goal_rates.taper.maintenance_band_kg`) → `too_few_weigh_ins` (< 6 non-outliers, or a span < 14 days) → `moving_away` (the rate is null, zero or the wrong sign) → `too_far` (> 730 days) → `ready`. The date is `last + ceil((target − T(last)) / (rate_kg / 7))`.
- **Weight fixtures** (`packages/test-fixtures/weights/`). Inputs are `{weigh_ins, target_kg, numbers_display}`; expected is the exact `WeightTrendOut` JSON (Task 23 shape, kg rounded 2 dp half-up, `y` from `shape`), generated by the script. Cases:
  - `three_constant`;
  - `gap_calendar_days`;
  - `single_outlier`;
  - `step_change_two_in_a_row`;
  - `too_few_for_rate`;
  - `weekly_rate_loss`;
  - `rapid_loss_three_weeks`;
  - `projection_ready`, `projection_too_few`, `projection_moving_away`, `projection_too_far`, `projection_reached`, `no_target`;
  - `hide_all` (every kg null, `y` kept).

- [ ] **Step 1: Write the failing tests** in `test_weight_trend.py`:

```python
def test_ema_hand_example():
    # 80.0 (d0), 79.6 (d1): a1 = 0.25 -> T = 79.9; 79.2 (d3, gap 2): a2 = 1 - 0.75**2 = 0.4375 -> T = 79.59375
    r = compute_trend([W(d0, "80.0"), W(d1, "79.6"), W(d3, "79.2")])
    assert r.at(d3) == D("79.59375")
def test_single_outlier_excluded():        # then 82.5 on d4: |82.5 - 79.59375| / 79.59375 = 3.65 % > 3 -> outlier, T unchanged
def test_step_change_two_in_a_row_accepted():
def test_weight_for_targets_needs_three(): # 2 weigh-ins -> None; 3 x 76.2 -> 76.2 (spec G5 trend)
def test_weekly_rate_and_pct():
def test_rapid_loss_needs_three_windows():
def test_projection_reasons():             # one per reason, precedence order
def test_shape_constant_is_half():
def test_matches_fixtures():               # packages/test-fixtures/weights
def test_yaml_keys_read_and_sourced():     # extends test_targets_yaml (every new key read, sourced, header present)
```

- [ ] **Step 2: Run** `uv run pytest tests/unit/scoring/test_weight_trend.py tests/unit/scoring/test_targets_yaml.py -q` → FAIL.
- [ ] **Step 3: Implement.** Then run the script with `--write`. Write ADR 0025: G24–G28, why 0.25 and not 0.1, and that slice 7 adds its own adaptive keys.
- [ ] **Step 4: Run** → PASS; `--check` → no diff.
- [ ] **Step 5: Commit** `feat(scoring): weight trend, weekly rate and projection`.

---

### Task 23 (API + shared): Weights routes, the trend weight in targets, members sync, i18n, contract

Use the `api-endpoint` skill. Spec: 4.9, 6.5, 6.6, 9.5. Rulings G15, G25–G28.

**Files:**
- Create: `apps/api/app/features/weights/{trend_source,schemas,service,router}.py`, `apps/api/tests/api/weights/{test_put,test_list_delete,test_trend,test_consent,test_targets_weight}.py`
- Modify:
  - `apps/api/app/features/targets/{service,schemas,mapping}.py`, `apps/api/app/features/diary/frozen.py` (`weight_source` in `inputs`)
  - `apps/api/app/features/members/service.py`
  - `apps/api/app/core/{consent,config,ratelimit}.py`, `apps/api/app/main.py`
  - `packages/i18n/*`, `NATIVE_REVIEW.md` ("Plan 12 slice 6"), the contract (generated)

**Interfaces:**
- Consumes: Task 21 `store`; Task 22 `weight_trend`; `diary.days.day_targets` (recompute today); `targets_service.resolve_member`; `meals.service.hidden_for_member`.
- Produces:

```text
WeightIn {member_id?, weight_kg (2-300, else 422 weight_out_of_range; 2 dp), confirm_unusual: bool = false, client_id?}
WeightOut {date, weight_kg|null (hidden), measured_at, source: "manual", client_id, numbers_hidden}
PUT    /v1/weights/{date}          weights_put -> 200 WeightOut   (terms + health_data; bucket weights 30/day)
       422 weight_needs_confirm {details: {previous: kg|null (null under hide_all), previous_date}} per G28;
       date_in_future; date_too_old (> 400 days). Sets members.weight_kg when date >= the latest; recomputes today's frozen targets.
GET    /v1/weights?member_id&from&to   weights_list -> {items: WeightOut[] (oldest first), numbers_hidden}
       default the last 90 local days; > 400 days -> 422 date_range_too_long
DELETE /v1/weights/{date}?member_id    weights_delete -> 204 (terms only); 404 weight_not_found;
       members.weight_kg <- the latest remaining row (unchanged if none); recomputes today
GET    /v1/weights/trend?member_id&days   weights_trend_get (days in 30|90|365, default 90)
       -> WeightTrendOut {member_id, days, from, to, points: [{date, weight_kg|null, outlier, y}], trend: [{date, trend_kg|null, y}],
          weekly_rate: {kg, pct_bw}|null, projection: {target_kg|null, date}|null, projection_reason, flags: ["rapid_loss"],
          numbers_hidden, pending_clinician_review: true}
       (computed over the full history, then sliced to the window; kg 2 dp; target from the goal settings; hide_all -> every kg,
        rate and target null, `y` kept; hide_energy changes nothing here)
```

  - `trend_source.py`: `async def weight_in_use(session, member, day, cfg=None) -> tuple[Decimal | None, Literal["trend", "latest"] | None]`. It uses `store.list_weigh_ins(until=day)` → `weight_for_targets`, falling back to `members.weight_kg` ("latest").
  - `targets_service.targets_for_today` uses it (`replace(body, weight_kg=…)`); `targets_preview` keeps the typed overrides. `Explanation`/`TargetsOut.explanation` gains `weight_source` (redacted with the explanation), stored in the frozen `inputs`.
  - `members_service.create_member`/`update_member`: when the primary member's `weight_kg` is written, call `store.upsert_weigh_in(member, account local today, kg, now)` in the same transaction (G26).
  - Consent: `REQUIRED["weights"] = ("terms", "health_data")` on the put, list and trend routes; `REQUIRED["weights_erase"] = ("terms",)` on delete. `BUCKETS["weights"] = ("day", "rate_limit_weights_per_day")`, with the setting set to 30.
- New keys (en drafts):
  - `diary.view.progress` "Progress";
  - `weight.title` "Weight", `weight.add` "Add a weigh-in", `weight.edit`, `weight.delete`, `weight.delete_confirm`, `weight.kg_value` "{value} kg", `weight.date`, `weight.tip_same_time` "Same time of day, for example after waking.";
  - `weight.confirm_unusual` "This is quite different from your last weigh-in ({previous} kg). Save anyway?", `weight.confirm_unusual_hidden` "This is quite different from your last weigh-in. Save anyway?", `weight.save_anyway`;
  - `weight.trend` "Trend", `weight.weekly_rate` "About {kg} kg a week ({pct}% of body weight)", `weight.projection` "At this pace you'd reach {target} kg around {date}.";
  - `weight.no_projection.{too_few_weigh_ins,moving_away,no_target,too_far,reached}`;
  - `weight.outlier` "Left out of the trend";
  - `weight.rapid_loss` "Your weight is going down faster than 1.5% a week. A slower pace is usually easier to keep up." (neutral; no link, Q14);
  - `weight.consent` "To keep a weight log, allow SmartNutri to use your health details.";
  - `weight.empty`, `weight.range.{30,90,365}`, `weight.check_entry` "Check this weigh-in";
  - `targets.how.weight_trend` "Weight used: {value} kg (your trend)", `targets.how.weight_latest` "Weight used: {value} kg (your latest weigh-in)";
  - errors `weight_out_of_range`, `weight_needs_confirm`, `weight_not_found`, `date_range_too_long`.

- [ ] **Step 1: Write the failing tests.**
  - `test_put.py`:
    - `test_put_creates_then_replaces_200`
    - `test_sets_member_weight_when_latest`
    - `test_older_date_keeps_member_weight`
    - `test_out_of_range_422`
    - `test_needs_confirm_plausible_and_daily_change` (78 → 82 the next day = 4 kg/day)
    - `test_confirm_unusual_saves`
    - `test_needs_confirm_hides_previous` (`hide_all`)
    - `test_future_and_too_old`
    - `test_client_id_retry` (including the concurrent race)
    - `test_recomputes_today_targets`
    - `test_rate_limited`
  - `test_list_delete.py`:
    - `test_default_90_days`
    - `test_range_too_long`
    - `test_delete_latest_restores_previous_weight`
    - `test_delete_last_row_keeps_member_weight`
    - `test_delete_404`
  - `test_trend.py`: `test_matches_weight_fixtures` (seed each fixture's weigh-ins and goal, then compare with `expected/`); `test_weights_hidden_every_surface` (`hide_all`: list, put, trend and the error details carry no kg; `y` is kept).
  - `test_consent.py`:
    - `test_put_list_trend_need_health_data` (403 with `details.purposes`)
    - `test_delete_needs_only_terms`
    - `test_gate_before_rate_limit`
  - `test_targets_weight.py`:
    - `test_targets_use_trend_weight_after_three` (G5 profile, three weigh-ins of 76.2, target 75 → energy 1940, flag `taper_active`, `weight_source` "trend")
    - `test_two_weigh_ins_use_latest`
    - `test_targets_ignore_outlier`
    - `test_member_update_upserts_weigh_in`
    - `test_frozen_past_day_unchanged_by_new_weigh_in`
    - `test_verdict_invariance_with_weights` (`analyze` is byte-identical)
- [ ] **Step 2: Run** `uv run pytest tests/api/weights tests/api/members -q` → FAIL.
- [ ] **Step 3: Implement**, then add the keys and the NATIVE_REVIEW flags (the tone of `weight.rapid_loss` and `weight.confirm_unusual`, the `{pct}` decimal, the Marathi date), regenerate i18n and the ARB files, then the contract.
- [ ] **Step 4: Run** the full checks as Task 6 Step 4, and `generate_target_expectations.py --check` (the existing target fixtures must not change) → PASS.
- [ ] **Step 5: Commit** `feat(api): weight log, trend and the trend weight in daily guides`, `feat(i18n): weight and progress`, `chore(contract): weights`.

---

### Task 24 (Android): Progress view, weight log, queue v5 *(parallel with Task 25)*

Use the `flutter-feature` skill. Spec: 7 (offline weights), 7.5 (progress), 7.8, 9.6. Rulings G15, G27–G30.

**Files:**
- Create:
  - `apps/app/lib/features/weights/data/weights_repository.dart`
  - `apps/app/lib/features/weights/presentation/{progress_view.dart, weight_chart.dart, weigh_in_sheet.dart, weight_list.dart, weights_providers.dart}`
  - `apps/app/test/features/weights/{progress_view_test.dart, weight_chart_test.dart, weigh_in_test.dart}`, `apps/app/test/core/storage/meal_queue_v5_migration_test.dart`
- Modify:
  - `apps/app/lib/features/diary/presentation/diary_screen.dart` (Day | Week | Progress)
  - `apps/app/lib/core/storage/meal_queue.dart` (v5: `PendingWeighIns {localDate, weightKg, confirmUnusual, clientId, status}`), the sync service
  - Profile "Diary and daily guide" (a Weight entry)
  - the targets "How we got this" (`weight_source` copy)

**Interfaces:**
- **Progress view:**
  - range chips (`weight.range.*`);
  - `WeightChart`: raw dots from `points` (outliers hollow, with `weight.outlier` as the semantics label) and the trend line from `trend`. Both are drawn from `y`. The axis labels come from kg only when `numbersHidden.macros` is false (`hide_all` → no axis digits). Brand token for the line, neutral for the dots, never a verdict or danger token;
  - `weight.weekly_rate` when `weeklyRate` is set;
  - `weight.projection` only when `projectionReason == ready`, else `weight.no_projection.<reason>`;
  - the `weight.rapid_loss` card when `flags` has it;
  - the taper or goal-reached flag copy from today's targets (`targets.flag.taper_active`, `goal_weight_reached`);
  - `diary.disclaimer` and pending review;
  - without `health_data`: the `weight.consent` card (the existing consent flow) and nothing else.
- **Weigh-in sheet:** date (default today, from `DiaryDayOut.today`) and kg, with `weight.tip_same_time`. `weight_needs_confirm` shows `weight.confirm_unusual` (or `_hidden` when `previous` is null) → resend with `confirmUnusual: true`.
- **Weight list:** with edit and delete.
- **Offline (queue v5):** a weigh-in made offline is queued and shown with `diary.waiting_sync`, without its number under `hide_all`. On sync, `weight_needs_confirm` marks the row `weight.check_entry` and asks the user. Delete is online-only.

- [ ] **Step 1: Write the failing tests.**
  - `progress_view_test.dart`:
    - `renders weights/expected weekly_rate_loss`
    - `projection only when ready` (each reason's copy)
    - `rapid loss card neutral`
    - `hide_all leaves no digits on progress` (the `hide_all` fixture: no digits except dates)
    - `consent card without health_data`
    - `no streak or rating text`
  - `weight_chart_test.dart`: `outlier drawn hollow`, `line uses brand token not danger`, `draws from y only`.
  - `weigh_in_test.dart`:
    - `needs confirm then save anyway`
    - `hidden previous shows hidden copy`
    - `offline weigh-in queues and shows waiting`
    - `sync needs confirm marks check entry`
  - `meal_queue_v5_migration_test.dart`: `v4 opens at v5 with empty weigh-ins`.
- [ ] **Step 2: Run them** to verify they fail.
- [ ] **Step 3: Implement**, then run `build_runner`.
- [ ] **Step 4: Run** `dart format --set-exit-if-changed lib test && flutter analyze && flutter test` → PASS.
- [ ] **Step 5: Commit** `feat(app): weight log and progress view`.

---

### Task 25 (Web): Progress view, weight log, e2e *(parallel with Task 24)*

Use the `web-feature` skill. Spec: 7.5, 7.8, 9.6 (e2e 6, 7 and 8 for Progress). Rulings G15, G27–G29.

**Files:**
- Create:
  - `apps/web/src/features/weights/{api/weights.ts, hooks/useWeights.ts}`
  - `apps/web/src/features/weights/components/{ProgressView.tsx, WeightChart.tsx, WeighInDialog.tsx, WeightList.tsx}`
  - `apps/web/tests/features/weights/*.test.tsx`, `apps/web/e2e/diary-progress.spec.ts`
- Modify: `apps/web/src/features/diary/components/DiaryView.tsx` (the third view), the Profile diary settings (Weight link), the targets explanation (`weight_source`), `stub-api.mjs`

**Interfaces:**
- The same behaviour as Task 24, online-only. `WeightChart` is inline SVG with a `<title>` and an accessible table fallback listing the dates (and kg when shown).

- [ ] **Step 1: Write the failing tests:** the Task 24 component cases (no offline). Plus `e2e/diary-progress.spec.ts`:
  - add two weigh-ins → the trend shows, and the "Not enough weigh-ins yet" reason (no projection);
  - add a third weigh-in that needs confirmation → "Save anyway";
  - switch Hide all numbers → no digits on Progress;
  - withdraw `health_data` (the stub) → the consent card shows and the diary day still loads.
- [ ] **Step 2: Run them** to verify they fail.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `pnpm lint && npx tsc --noEmit && pnpm test && pnpm e2e` → PASS.
- [ ] **Step 5: Commit** `feat(web): weight log and progress view`.

---

### Task 26: Slice-6 gate and final docs

**Files:**
- Modify: `docs/FEATURE_PARITY.md` (F26 → 🟡), `CONTEXT.md` (Plan 12 code complete; migrations 0010–0013; the open items from Task 0 remain; `ADAPTIVE_TDEE` is slice 7), this plan.

- [ ] **Step 1: Run everything** as Task 9 Step 1, plus `generate_weight_expectations.py --check` and `generate_recipe_expectations.py --check`.
- [ ] **Step 2: Dispatch** `nutrition-safety-reviewer`. Scope:
  - the trend algorithm and the 0.25 choice (ADR 0025);
  - outlier and step-change handling;
  - `W` for targets and the taper against the target goldens (unchanged) and `test_targets_weight.py`;
  - the rapid-loss copy and the absence of a support link (Q14);
  - hidden numbers on every weight surface, including offline rows and confirm messages;
  - the `health_data` gating and erasure on `terms` (Q13);
  - neutral chart colours;
  - the members-sync rule (G26);
  - the back-fill.
- [ ] **Step 3: Fix** blocking findings with tests, then re-run Step 1.
- [ ] **Step 4: Commit** `docs: Plan 12 slice 6 parity, context and review`.
