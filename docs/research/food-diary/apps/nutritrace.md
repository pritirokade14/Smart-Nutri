# NutriTrace: clean-room feature study

Subject: https://github.com/traceapps/nutritrace (AGPL-3.0). Svelte 5 in compatibility mode (Svelte 4 syntax), Express + better-sqlite3, PWA plus Android via Capacitor, self-hosted.
Method: shallow clone, read-only. Code is described in my own words; nothing is copied. No keys or endpoints used.
Scope limit: only the repo's own README, ROADMAP, CHANGELOG, ARCHITECTURE and docs/*.md were read. The hosted docs site and GitHub issues were **not** fetched (no web tool in this run), so issue-driven detail comes only from bug numbers quoted in code comments and the changelog. [unverified] marks guesses.
Commit studied: default branch HEAD at clone time (2026-11-07).

## 0. Headline findings

1. **Adaptive TDEE is a plain 35-day linear regression, not an EMA or Kalman trend.** Intake minus (weight slope x 7,700 kcal/kg) over days that have both intake and weight, needing at least 21 such days (details in section 3).
2. **There is no goal-based macro or target engine.** The BMR formula runs once, in the onboarding wizard, to seed a fixed calorie goal. Protein, carb and fat goals are not derived from the goal or from body data. The user sets them (grams or percent of calories) or applies a template. SmartNutri's "targets from goal and body data" is therefore something to build, not to port.
3. **"Dynamic" mode is not a formula.** It takes yesterday's wearable calories-out times a factor of 0.8, 1.0 or 1.2. It needs a connected device.
4. The diary is stored as one row per day with items as a JSON array, merged per item by uuid with tombstones. It is robust against stale clients but hard to query.
5. Real bugs found in the maths (UTC vs local dates, x-axis compression). See section 11.

## 1. User flow and screens

Evidence: `src/App.svelte`, `src/routes/*.svelte`, `README.md`.

- **Onboarding wizard** (`src/routes/Wizard.svelte`). Steps, in order: optional user-management setup (admin account), welcome, name (local mode), units (metric/imperial), gender, date of birth, height, weight, target weight, activity level, integrations, notifications, updates, summary. The summary shows the starting TDEE and the starting calorie goal, with the factor maths. Finish writes the profile fields and a fixed calorie goal in one bulk settings call, then shows a short celebration screen and goes home. A skip path exists. Gender and activity are required to continue.
- **Diary** (`src/routes/Diary.svelte`, about 3,700 lines). Date bar with a week strip (`components/diary/WeekStrip.svelte`) for day navigation. Meal sections default to Breakfast, Lunch, Dinner and Snacks, user-renamable (`mealNames` setting, `src/stores/settings.js`). Each section has add-food, a quick-calories button and a per-meal menu (copy to another day, split recipe, drag to another meal or another day in the strip). Widgets: macro ring, day summary, water, body stats (weight entry), fasting, activity, daily note. A bottom bar toggles **consumed / remaining** per calorie and macro, and shows an activity cue when the goal is raised by exercise.
- **Add food**: the Foods page opened in pick mode (`/foods?pick=1&meal=<idx>&date=<date>`), then an add-to-diary sheet (portion, unit, meal). Alternatives: Quick Calories sheet (calories only), Smart Log (voice or text through an AI assistant), a food-photo proposal that the user must confirm, barcode scan.
- **Edit**: tap an item to change quantity or unit, or move it to another meal. Delete asks for confirmation.
- **Other screens**: Goals (modes, readiness card, templates), Statistics (charts of any metric, average/goal/trend lines, range picker), Wellness, Profile, Settings (about 25 sub-pages).
- **Empty and error states**: "Weight not logged" in the weight widget; Adaptive TDEE shows a readiness card with progress until 21 days exist; Dynamic mode buttons are disabled with an explanation when no device is connected (CHANGELOG #147); an offline badge (`offlineState`) shows pending sync; `public/offline.html` is the PWA fallback.

## 2. Data model

Evidence: `server/db.js` (about 1,200 lines; base tables plus many ALTER-based migrations).

SQLite, with soft deletes (`deleted_at`) and `updated_at` added later for sync.

| Table | Key fields | Notes |
|---|---|---|
| `users` | id, username, password_hash, full_name, nickname, birthday, gender, role | Single-user mode runs with `user_id = NULL`. |
| `user_settings` | (user_id, key) PK, value JSON | **Holds the profile and goals**: `height_cm`, `weight_kg`, `target_weight`, `activity`, `tdee`, `goals`, `calorieGoalMode`, `calorieGoalFactor`, `mealNames`. No dedicated profile, goals or targets table. |
| `foods` | name, brand, `nutrition` JSON, `portion` (default 100), `unit` (default g), barcode, category, plus added columns `nutrition_basis`, `alt_units` JSON, `density_g_ml`, `visibility`, `source_id`, `source_app`, `source_external_id`, `source_url` | One row per food. There is no servings table: serving sizes are `portion`+`unit` plus the `alt_units` list `[{abbr, grams}]`. |
| `meals` | name, `nutrition` JSON (cached), `items` JSON, `is_recipe`, portion, unit, `servings` | Meals and recipes share one table. Items are embedded JSON snapshots. |
| `diary` | (date, user_id) UNIQUE, `items` JSON, `body_stats` JSON, `water` JSON, `notes` | **One row per day.** Each item has a client uuid, a `meal` index and cached `nutrition`. Weight lives inside `body_stats` (value plus `weight_unit`). |
| `diary_tombstones` | (user_id, date, kind, uuid) PK | Per-item deletions so sync cannot resurrect items. |
| `activity_log` | date, name, kcal, duration_min, met, source, is_template | Manual exercise. |
| `workouts` | source, source_id, date, calories, hr, gps | Imported from wearables. |
| `wellness_data` | (user_id, date, source, metric_type) UNIQUE, value, metadata | Wearable metrics: `weight_kg`, `calories_out`, `active_calories`, steps, sleep. |
| `fasts` | start_at, end_at (NULL = active), goal_hours (default 16) | Intermittent fasting. |
| other | `sync_deletions`, share tables, token tables, OIDC, `ai_chat_history`, `webhooks`, `api_tokens` | Not relevant to the diary. |

Relations: diary items copy food data at log time (snapshot in the JSON), so editing a food later does not change history. [Inferred from `Nutrition.calculate` reading `item.nutrition`; "stale ingredients" tests exist for recipes.]

## 3. Target maths

### 3.1 Starting estimate (onboarding only)
Evidence: `src/lib/nutrition.js` (`calculateTDEE`), `src/routes/Wizard.svelte` (`calcSummary`).

- Defaults when input is missing: height 170 cm, weight 70 kg, age 30. Wizard clamps age to at least 15.
- **BMR** = 6.25 x height_cm + 9.99 x weight_kg - 4.92 x age + (5 if male, else -161). This is the Mifflin-St Jeor shape with slightly rounded coefficients that differ from the published 10 and 5 (weak point: not the standard constants).
- **Activity factors**: sedentary 1.2, light 1.375, moderate 1.55, active 1.725, very active 1.9. Unknown value falls back to 1.2.
- **TDEE** = round(BMR x factor).
- **Goal calories**: compare target weight with current. If target is below 99% of current, goal = round(0.80 x TDEE). If above 101%, goal = round(1.20 x TDEE). Otherwise goal = TDEE. So the deficit or surplus is a flat plus or minus 20%, independent of how fast the user wants to move. No floor (for example a minimum of about 1,200 kcal) and no cap in the wizard. [verified in `Wizard.svelte`; no floor seen]
- **Water goal** = round to nearest 50 ml of (35 ml x weight_kg + activity bonus 0/350/500/700/1000 ml).
- The result is stored once as a fixed calorie goal, and the profile snapshot (`tdee`, `activity`, etc.) is saved. It is never recomputed unless the user reruns the wizard.

### 3.2 The three calorie-goal modes
Evidence: `src/routes/Goals.svelte` (`_effectiveCalGoal`), `server/index.js`, `ROADMAP.md`.

- **Fixed**: the stored goal (default 2,000 if absent).
- **Dynamic**: effective goal = round(yesterday's calories-out x factor). Calories-out is read for the day before the viewed date from `wellness_data.calories_out`, with source priority garmin > health_connect > fitbit > lifttrace by default (a setting flips lifttrace to first). Returns null if no device has data, and the UI then falls back to the fixed goal.
- **Adaptive**: effective goal = round(learned TDEE x factor), but only when the learned result is `ready`, otherwise the fixed goal is used.
- **Factor**: a three-way choice, 0.8 (lose), 1.0 (maintain), 1.2 (gain), applied to Dynamic and Adaptive. It is a flat percentage, not a kcal-per-day target.
- **Exercise add-back** (Diary): if the user enables activity adjustment, goal for the day = goal + effective active calories, where effective = wearable active calories, manual log, or both depending on a policy (`wearable_wins` default, `manual_wins`, `additive`). Wearable value is the single highest source, to avoid double counting (`server/lib/active-calories.js`). Note this stacks on top of Dynamic mode, which already includes activity [possible double count, unverified in UI].

### 3.3 Adaptive TDEE algorithm (exact)
Evidence: `server/lib/adaptive-tdee.js`, mirrored in `src/lib/adaptive-tdee-local.js` (Android offline), endpoint `GET /api/goals/adaptive-tdee` in `server/index.js`.

Parameters: window W = 35 days ending today; minimum valid days M = 21; energy density E = 7,700 kcal per kg.

Steps, in my notation:
1. **Intake per day** `I_d` = sum over diary items of (calories x quantity). A day with no items, or a total of 0, has no intake (null). So a day the user forgot to log is "missing", not zero. A day with a partial log counts as a full day (weak point).
2. **Weight per day** `w_d`: use a scale reading from `wellness_data` (source priority withings > fitbit > garmin > health_connect), else the manual weight in that day's body stats (lb converted to kg). Sources are not averaged or blended.
3. **Fill gaps**: between two real weights, linearly interpolate each missing day. No extrapolation: days before the first or after the last real weight stay empty.
4. **Valid days**: keep days that have both `I_d` and `w_d` (real or interpolated). Count them as n.
5. **Gate**: if n < 21, return `ready = false`, with `daysAvailable`, `daysRequired = 21`, and null TDEE, trend and confidence.
6. **Slope**: ordinary least squares of weight on the **index of the valid day** (0..n-1), giving slope b in kg per day, and R squared.
7. **Balance**: `B = b x 7700` kcal per day (positive means gaining).
8. **TDEE** = mean(I over valid days) - B. Rounded to whole kcal.
9. **Outputs**: `tdee`, `trendKgPerWeek = round(b x 7, 2 dp)`, `confidence`, `weightSource` (wellness, manual or mixed), `computedAt`.
10. **Confidence** = clamp(0.5 x coverage + 0.5 x R squared, 0.5, 0.95), where coverage = n / 35. It is a UI hint only; it does not change the TDEE.

What is **not** there: no EMA, no weight smoothing or outlier rejection, no water-weight handling, no minimum span or minimum number of real (non-interpolated) weigh-ins, no cap or bounds on the resulting TDEE (a bad logging stretch can give an absurd value, then the goal follows it), no recency weighting inside the window, no goal-aware shrinkage toward the formula estimate, and no minimum-intake check per day. The result is recomputed on every request; nothing is stored.

### 3.4 Macro targets
No derivation. Macro goals live in the `goals` setting as per-nutrient entries `{min, max, isMin, isPercent, sharedGoal, days[7]}`. A percent goal converts to grams as round(calorie goal x pct / 100 / density) with density 4 for protein and carbs, 9 for fat (`src/lib/goal-resolver.js`, `Diary.svelte` `_macroGoal`). Per-weekday targets are supported (`days[]`). Goal templates can be saved and applied. Wizard does not set protein, carbs or fat. [verified by reading `Wizard.svelte` batch payload]

## 4. Units, servings, recipes, custom foods

Evidence: `src/lib/units.js`, `scripts/alt-units-diary.test.js`, `server/routes/foods.js`, `server/routes/meals.js`, `src/lib/nutrition.js`.

- **Units**: catalog of mass (g, mg, kg, oz, lb), volume (ml, l, tsp, tbsp, fl oz, cup), count (piece, slice), plus user-defined custom units. Grams-per-unit table exists only for mass and volume; ml is treated as 1 g unless the food has `density_g_ml`. Cup, piece and custom units are opaque unless the food lists them in `alt_units`.
- **Scaling**: a food has a reference portion (default 100 g). Logging converts the entered amount and unit to a multiplier through a `scaleFactor(fromAmt, fromUnit, toAmt, toUnit, food)` helper that uses `nutrition_basis` (g or ml), density and `alt_units`. Nutrition on the diary item is stored per reference portion and multiplied by `quantity` (`Nutrition.calculate`). A cross-system warning shows when picking ml for a gram-based food with no density.
- **Household units**: `alt_units` is a JSON list on the food (for example one slice = 54.7 g). A past bug (#237) multiplied instead of converting because the list arrived as a string; fixed by tolerant parsing and a 5,000-case randomized test.
- **Custom foods**: create or edit with a full nutrient set (about 35 nutrients, US label order, optional %DV), sodium and salt auto-derived from each other (factor 400 mg sodium per g salt), a barcode, a photo, notes, visibility (private/shared). Creation is idempotent through a `client_key`; barcode dedupes within the user's library.
- **Recipes**: a row in `meals` with `is_recipe = 1`, an embedded ingredient list, cached total nutrition, and a `servings` count. Logging a recipe adds one item; "Split recipe" explodes it into ingredient items (the parent keeps the name and image and the maths sums the children). Imports: Mealie, CookTrace, nutrition CSV (MyFitnessPal, Lose It, Cronometer). [Per-serving division logic not read in detail: unverified.]

## 5. Food database

Evidence: `server/routes/proxy.js`, `src/lib/off-rank.js`, `server/lib/off-local.js`, `public/vendor`, `README.md`.

- **Sources**: the user's own foods first; Open Food Facts (cloud API, or a local Parquet/DuckDB snapshot for air-gapped servers); USDA FoodData Central (needs a free key, server-side or per user); Mealie and CookTrace recipes. A source filter and OFF/USDA quality signals appear in the Foods list.
- **Search**: OFF name search is proxied through the server (host allow-list, rate limit 60 per minute, SSRF-checked redirects, 15 s timeout). Results are re-ranked: OFF's relevance score decides between clearly different matches; within a band of scores within 10% of the best, order by has-photo, then OFF completeness, then has-Nutri-Score. Thin entries sink but are not hidden. Local-mirror results skip the photo tier.
- **Barcode**: on-device scanning with three bundled JS decoders (zxing default, html5-qrcode, quagga2) selectable in settings, then lookup by barcode (OFF or local mirror). A scanned product that already exists in the user's library opens that food instead of duplicating.
- **Label OCR**: an AI "Scan Label" flow exists; the user confirms the result.
- **Offline**: the web app keeps a mirror in IndexedDB (diary, own foods, meals, settings, goals, fasting, profile) and an outbox that is pushed as one sync request when the connection returns, with Web Locks across tabs and exponential backoff 3 s to 30 s. OFF, USDA, uploads, wellness and AI need a connection. Android has its own on-device SQLite mode. A catalog-warm feature pre-caches foods.

## 6. Aggregation

Evidence: `src/lib/nutrition.js`, `src/routes/Diary.svelte`, `src/stores/diary.js`, `server/lib/mcp/tools/daily-totals*.js`.

- **Totals**: computed **on the client** by summing `Nutrition.calculate(item)` over the day's items. The server has its own sum for MCP and REST (`/api/v1/diary/:date/totals`). Two implementations of the same maths [risk of drift].
- **Missing nutrients**: a nutrient absent from an item contributes 0 to the sum, so partial data silently undercounts, and the UI does not mark a total as incomplete [weak point].
- **Remaining** = goal - consumed (shown instead of consumed when toggled). Goal = resolved per weekday value (`resolveGoalFor`), plus effective active calories if enabled. A goal bug (#203) once showed the weekly peak instead of the day's value; the resolver and its tests came from that.
- **Percent-of-calories macro split** shown with `macroPercents`: fat, carb and protein energy divided by their sum.
- **Weekly and range views**: the week strip shows per-day bars. Statistics charts any metric over a range, with average line, goal line, trend line (a linear regression across the plotted points), a 7-vs-previous-7-days delta (hidden under 14 days), and today excluded by default until complete. For range charts a per-weekday goal is averaged (`resolveRangeGoal`). Optional weekly summary email.

## 7. Progress

- **Weight**: entered in the diary body-stats widget (kg or lb), one value per day. Statistics shows the weight series with an optional straight-line regression, not a smoothed trend weight. The adaptive-TDEE card shows trend kg per week from its own regression.
- **Streaks**: only for fasting. Current streak = consecutive days, walking back from today, on which a fast that ended that day met its goal hours; an active fast counts for today once it has reached goal. Longest streak is a single pass over sorted days. Logging streaks are not implemented [roadmap mentions future "30 days hitting protein goal" ideas, ROADMAP.md line ~891].
- **Fasting**: start/end timestamps, preset goals 16, 18, 20, 23 (OMAD) or custom, insights (count, average, longest hours, streaks), offline support.

## 8. Edge cases

- **Missing days**: intake missing means excluded from the adaptive window; weight gaps are interpolated inside the window only. Because the regression x-value is the index among valid days, any excluded days compress the time axis, so the slope per "day" is overstated whenever days are skipped (see section 11).
- **Timezones**: the diary date is a plain local-calendar `YYYY-MM-DD` string built from the device's local date (`localDateStr` in `src/lib/db.js`), so a day is the user's local day. But adaptive TDEE (`_isoDaysAgo`) and fasting streaks use **UTC** dates, and MCP writes are labelled "server-local". Near midnight, or for users far from UTC, the window edge and the streak day can be off by one. Weekday goals deliberately parse as local midnight to avoid this class of bug (`goal-resolver.js`).
- **Concurrency and stale clients**: per-item uuid merge with tombstones, later `updatedAt` wins, delete beats edit. Born from data-loss incidents (diary-merge.js header).
- **Kilojoules**: stored in kcal always; kJ is display only (factor 4.184); a drift bug (#146) came from storing a separate kJ goal.
- **Bad JSON, malformed units**: tolerant parsing and tests.

## 9. API endpoint shapes (described, not copied)

Internal REST (`server/routes/*.js`, mounted under `/api/...`), JSON, cookie auth plus CSRF:
- `diary`: list all; get a day; **PUT a day** with `{items, body_stats, water, notes, deleted_uuids:{items,water}}` (merge, not replace); delete a day; put day completion and per-meal completion flags.
- `foods`, `meals`: list (own, or group catalogue when sharing is on), get one, create (idempotent by `client_key`, upsert by source app plus external id), update, "used" counter, share, copy, bulk share, delete.
- `settings`: get all, put one, **bulk put**, delete one.
- `activity`: get by date, sum by date, range list, create, update, delete. `fasts`: list, active, start, end, patch, delete.
- `sync`: `pull` (changes since a clock) and `push` (outbox), used by Android and the web offline layer.
- `GET /api/goals/adaptive-tdee` returns `{ready, daysAvailable, daysRequired, windowDays, tdee, trendKgPerWeek, confidence, weightSource, computedAt}`.
- `GET /api/wellness/calories-out?date=` returns `{calories_out, source, date}` for the previous day.
- `proxy`: allow-listed GET passthrough for OFF/USDA JSON and a few image hosts.

Public API v1 (`docs/public-api.md`, off by default, bearer personal access tokens with read and write scopes, 60 requests per minute per token, rate-limit headers): read diary day, day totals, goals, meal search and recent, meal by id, steps, body composition, profile (gender and birthday only); write: add a food to a day, add water, add a saved meal, set body stats. Errors: 400 with `{"error"}`, 401, 403, 429 with `Retry-After`. There is also an MCP server (about 20 tools) exposing the same data to AI agents.

## 10. Tests

Evidence: `package.json` (`node --test scripts/*.test.js`), about 100 test files in `scripts/`.

- Plain Node test runner, no framework. Many are **wiring tests** that read source files and assert strings or structure exist (for example `bottom-dock-wiring`, `diary-desktop-wiring`), which are brittle and only detect deletion.
- Good unit tests: `goal-resolver`, `goals-percent-mode`, `alt-units-diary` (randomized, 5,000 cases), `diary-merge` and `diary-merge-echo`, `offline-edits`, `off-search-rank`, `off-nutrition-sets`, `nutrition-import-*`, `sleep-sessions` plus a Kotlin parity test fed from shared JSON fixtures, MCP integration tests.
- **No test file mentions adaptive TDEE** (grep for "tdee" and "adaptive" in `scripts/*.test.js` hits only `off-search-rank.test.js`, for an unrelated reason), and none cover `calculateTDEE`, the dynamic goal or the wizard maths. The most health-relevant maths is untested. [verified by grep]

## 11. Ideas to adopt, and weaknesses

### Strong ideas to adopt
1. **Adaptive TDEE with a readiness gate**: show "n of 21 days" progress and fall back to the formula until ready, so the user never sees a guessed number as learned. Our version should add smoothing, bounds and a minimum number of real weigh-ins.
2. **Missing means missing**: days with no logging are excluded, never counted as 0 kcal. Fits our "never invent nutrition data" rule.
3. **Per-item uuid merge with tombstones** for a diary that syncs from several clients. Prefer real rows (one per entry) in Postgres instead of a JSON array per day.
4. **Consumed / remaining toggle** and a visible cue when the goal includes exercise.
5. **Household units on the food** (`slice = 54.7 g`) and a unit-scaling function covered by a randomized test; density-less ml to g warning.
6. **Weekday-aware goals** with one resolver shared by Diary and Statistics (and the lesson from bug #203: one resolver, tested).
7. **OFF re-ranking** that respects OFF's relevance and only breaks ties on quality; useful for Indian packaged foods that have few photos.
8. **Idempotent create** (`client_key`) and barcode de-dupe in the user's library.
9. **Source priority for wearables and a "highest single source" rule** to avoid double counting.
10. **Confirm-before-save** for photo and AI food proposals (matches our rule).

### Weaknesses and bugs to avoid
1. **Regression x-axis uses the valid-day index, not the calendar day.** Skipped days compress time, so the slope is inflated. Use real day offsets.
2. **UTC dates for the window and fasting streaks** against local-date diary rows: off-by-one near midnight. Store the user's timezone and compute in it.
3. **No bounds on learned TDEE**, no smoothing or outlier rejection, no minimum real weigh-ins (21 valid days can be mostly interpolated), no check that a logged day is plausibly complete. A partial log lowers intake and therefore lowers TDEE and the goal, a risky feedback loop for a health app. Add clamps (for example within a band around the formula estimate), a completeness flag per day, and a "log complete" marker (NutriTrace has a day-completion flag in the diary routes but the TDEE code does not use it [unverified link]).
4. **7,700 kcal/kg is applied as a constant** with no note about water and glycogen swings in short windows.
5. **BMR constants are not the published ones**; deficit is a flat 20% with no floor, so a small user could be pushed under safe intake. Our targets need a minimum-calorie floor, a rate cap (for example a share of body weight per week), and clinician-reviewed thresholds in data files.
6. **No macro derivation** from goal and body data: protein per kg for muscle gain or loss is left to the user. This is the gap SmartNutri wants to fill.
7. **Profile and goals stored as settings JSON**, with no history: changing the goal rewrites the past view. Keep dated goal rows and dated profile or weight rows.
8. **Per-day JSON arrays** make server-side analytics, indexing and RLS hard; totals computed in two places (client and server) can drift.
9. **Missing nutrients count as 0**, so totals silently undercount. Show "incomplete" instead.
10. **Dynamic mode uses yesterday's burn**, which swings day to day; and exercise add-back may double count on top of it.
11. **Tests**: heavy on string-matching wiring tests; none for the core target maths.
12. **Licence**: AGPL. Only ideas were taken; do not copy code, copy, assets or data files.
13. Health claims: the app presents "learned TDEE" and confidence as facts; our copy must say information, not medical advice.

## Sources

Local clone (read only): `/private/tmp/claude-501/-Users-apple-Project-Smart-Nutri/03a02f4d-8568-4ab7-b791-175c46db0417/scratchpad/fooddiary-repos/nutritrace`
- `README.md`, `ROADMAP.md` (Adaptive TDEE section about lines 134-161), `CHANGELOG.md`, `ARCHITECTURE.md`, `docs/public-api.md`, `docs/federation.md`
- `server/db.js` (schema), `server/lib/adaptive-tdee.js`, `server/lib/active-calories.js`, `server/lib/diary-merge.js`, `server/lib/mcp/_diary-write.js`, `server/index.js` (adaptive-tdee and calories-out routes)
- `server/routes/diary.js`, `foods.js`, `meals.js`, `fasts.js`, `activity.js`, `settings.js`, `proxy.js`, `sync.js`
- `src/lib/nutrition.js` (BMR and TDEE, totals), `src/lib/units.js`, `src/lib/goal-resolver.js`, `src/lib/adaptive-tdee-local.js`, `src/lib/off-rank.js`, `src/lib/offline-api.js`, `src/lib/db.js` (`localDateStr`)
- `src/routes/Wizard.svelte`, `Goals.svelte`, `Diary.svelte`, `Statistics.svelte`; `src/stores/fasting.js`, `src/stores/settings.js`; `src/components/foods/BarcodeScanner.svelte`
- `scripts/alt-units-diary.test.js`, `scripts/goal-resolver.test.js`, `package.json`

Public pages: repository https://github.com/traceapps/nutritrace (README and docs only). Hosted docs (traceapps.github.io) and GitHub issues were not fetched.
