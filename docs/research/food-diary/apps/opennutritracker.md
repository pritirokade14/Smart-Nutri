# OpenNutriTracker: clean-room feature study

Study of OpenNutriTracker (ONT) for SmartNutri's planned single-user food diary.

- Repo: https://github.com/simonoppowa/OpenNutriTracker (GPL-3.0, Flutter). Read at commit `ca8f51de`, dated 2026-10-30, app version 2.6.0+68.
- Method: shallow clone, read only. Nothing from the repo was built or run.
- Clean-room rule: everything below is described in our own words and notation. No code, strings, assets or icons are copied. GPL code must not be ported. The underlying maths (IOM equations, WHO energy densities) come from published sources and are not ONT's property.
- Paths are relative to the repo root. `[unverified]` marks guesses.
- Public research (issues, discussions, store listing) was not fetched live. WebFetch was not loaded in this run. We used the repo's own README and `docs/` instead, notably `docs/competitive-feature-gaps.md` and `docs/tdee-iom-2005-verification.md`. Re-check live issues if needed.

## 0. What ONT is

- Local-first calorie, macro and micronutrient tracker for Android and iOS. No account, no analytics.
- Storage is encrypted Hive boxes on the device (README "Privacy").
- Food data comes from Open Food Facts (OFF) plus an ONT-run Supabase "reference backend" that serves USDA FoodData Central, German BLS and others.
- Optional AI meal parsing (text or photo) uses the user's own API key. The model never supplies nutrition numbers (README "AI meal assistance").
- Closest to our scope. It is a single-user diary with targets, and it has multi-profile support we do not need.

## 1. User flow and screens

Source: `lib/features/*`, `lib/core/presentation/main_screen.dart`, README feature list.

**Onboarding** (`features/onboarding/onboarding_screen.dart`)
- Paged flow, declared as one ordered enum so inserting a page does not retarget jumps. Pages:
  1. Intro.
  2. About you: gender and birthday.
  3. Body measurements: height and weight, with metric or imperial toggles seeded from the device locale on a first run only.
  4. Activity level (four choices).
  5. Goal (lose, maintain or gain). The app suggests a goal from weight versus target but never preselects it (`onboarding/domain/entity/goal_suggestion_entity.dart`).
  6. Other options: which food databases to search.
  7. Overview of the computed target.
- Next is blocked until valid. A blocked tap reveals the errors on untouched fields.
- Height, weight and age have hard bounds plus softer "plausible" bounds. Values outside the plausible range are accepted once the user confirms them (`core/utils/bounds/ranges_const.dart`).
- Weight is logged as the first weight-log entry at the end of onboarding.

**Main shell**: Home, Diary, Trends, Profile (plus Settings). `core/presentation/main_screen.dart`.

**Home** (`features/home/`)
- A progress ring shows "calories left".
- Carbs, fat and protein bars show intake against goal.
- Four meal sections: breakfast, lunch, dinner, snack. Each shows its entries and a per-meal kcal target.
- The day's activity list, and a water chip.
- Over goal flips the ring label and colour (`home/presentation/widgets/dashboard_widget.dart`).

**Diary** (`features/diary/`)
- Month calendar. Each logged day gets a good or poor marker.
- The selected day's totals and entries sit below.
- Entries can be sorted by time or by macro contribution, and dragged between meals.
- Copy an entry to another day (`docs/competitive-feature-gaps.md` cites `day_info_widget.dart`).
- Day navigation is by tapping the calendar. Future days are [unverified].

**Add food** (`features/add_meal/presentation/add_meal_screen.dart` and `widgets/`)
- Tabs or methods: search (food and OFF), recent and favourites, barcode scanner, quick add, custom meal, recipes, and multi-item AI text or photo.
- A "log tray" and bulk-add bloc let several items be queued, then logged together (`bloc/bulk_add_bloc.dart`).
- **Quick add**: a title plus kcal, with optional macros. It is stored as a custom meal with unit grams and the kcal as the per-100 value (`widgets/quick_add_bottom_sheet.dart`, around line 175).
- **Custom meal**: name, optional brand, optional barcode (format check 8 to 14 digits, with a stricter EAN-13 check-digit), optional photo, per-100 nutrition.
- **Meal detail** (`features/meal_detail/`): amount plus a unit dropdown with a live kcal and macro preview, then Add.

**Edit and delete**
- Entries are editable on `features/edit_meal/` and deletable from the diary or home.
- Delete dialog copy is tested (`test/unit_test/delete_dialog_copy_test.dart`).
- Totals are kept consistent by a tracked-day lock plus a reconciler and repair utilities (see section 6).

**Empty and error states**
- Search separates "remote returned zero rows" from "remote failed". A failed provider must not read as "no matching foods" (`search_products_usecase.dart`, `remoteSourceFailed`).
- A partial-results notice and a no-results widget exist (`widgets/partial_results_notice.dart`, `no_results_widget.dart`).
- A storage-recovery screen covers corrupt Hive data (`core/presentation/storage_recovery_app.dart`).
- A disclaimer dialog is shown on first launch (`home_bloc.dart`, `showDisclaimerDialog`).

## 2. Data model and storage

Storage: local Hive boxes, AES-256 encrypted, key in the platform keystore (`core/utils/secure_app_storage_provider.dart`). Pure on-device. There is no Supabase user data. The ONT Supabase is a read-only food reference with an anonymous key.

| Entity | Fields (names paraphrased) | Source |
|---|---|---|
| User | birthday, height cm, weight kg, gender (male, female, non-binary), goal (lose, maintain, gain), activity level (4), optional weekly weight rate kg, optional calories profile (non-binary only), optional target weight kg, taper-enabled flag | `core/domain/entity/user_entity.dart`, `core/data/dbo/user_dbo.dart` |
| Config | units (food, height, body weight), energy unit kcal or kJ, per-meal kcal share map, macro percentage overrides, user kcal offset, day-start offset (hours and minutes), food-source toggles, per-nutrient goal overrides, workout kcal multiplier (0.5 to 1.0), disclaimer flags | `core/domain/entity/config_entity.dart` (about 42 Hive fields) |
| Meal (food) | code or barcode, name, brands, images, quantity and unit, serving quantity, serving unit, serving size text, nutrients per 100 g or ml, source (OFF, FDC/backend, custom, recipe, and others), backend source code, portions list (backend only, not persisted), custom image path | `features/add_meal/domain/entity/meal_entity.dart`, `core/data/dbo/meal_dbo.dart` |
| Nutrients | about 24 per-100 values: energy kcal, carbs, fat, protein, sugar, fibre, saturated fat, sodium, minerals, vitamins. Every field nullable | `meal_nutriments_entity.dart`, `meal_nutriments_dbo.dart` |
| Intake (diary entry) | id, unit string, amount, meal slot (breakfast, lunch, dinner, snack), full **snapshot** of the meal, timestamp | `core/domain/entity/intake_entity.dart` |
| TrackedDay | day, calorie goal and tracked, carbs, fat and protein goal and tracked, optional per-nutrient goals and tracked (fibre, sat fat, sugars, sodium, calcium, iron, potassium, magnesium, B12) | `tracked_day_entity.dart`, `tracked_day_dbo.dart` (19 fields) |
| WeightLog | date, weight kg, optional note. Keyed by local day as `yyyy-MM-dd` | `weight_log_entity.dart`, `weight_log_dbo.dart` |
| Recipe | id, name, description, ingredient list (each a meal snapshot plus amount, unit and grams), total weight g, nutrients per 100 g, servings count, tags, image, timestamps | `recipe_entity.dart`, `recipe_ingredient_entity.dart` |
| Other | physical activity and user activity (workouts, burned kcal), water intake (ml), fasting session, favourites, custom activity templates, remote-search cache | `core/data/dbo/*` |

Design points:
- A diary entry stores a snapshot of the food, so later edits or upstream changes to the food do not rewrite history.
- The daily goal is also stored on each TrackedDay, so a past day keeps the goal it had.
- Nutrients are stored per 100 g or ml. "Per unit" is value divided by 100, then times grams.
- The `unit` string on the entry is a small closed vocabulary (see section 4).
- Export and import are documented in `docs/export-format.md`, as JSON or CSV zip.

## 3. Target maths

Files: `lib/core/utils/calc/{tdee_calc,pal_calc,calorie_goal_calc,macro_calc}.dart`, `core/utils/bounds/ranges_const.dart`, `docs/tdee-iom-2005-verification.md`.

**Energy equation.** ONT does **not** use Mifflin-St Jeor or Harris-Benedict. It uses the IOM 2005 (US National Academies) adult TEE equations, the combined set from p. 204. They give total daily energy directly, so there is no separate BMR step. In our notation, with W kg, H metres, A years:

- Male: `TEE = 864 - 9.72*A + PA*(14.2*W + 503*H)`
- Female: `TEE = 387 - 7.31*A + PA*(10.9*W + 660.7*H)`
- PA multiplies both the weight and the height terms. ONT had this wrong (PA applied to weight only), under-stating TDEE by 109 to 489 kcal/day for non-sedentary users, and fixed it (issue #987, `docs/tdee-iom-2005-verification.md`).

**Activity.** There are four categories. Each is mapped to a representative PAL value and then to a PA coefficient by band:

| Category | PAL representative | PA male | PA female |
|---|---|---|---|
| Sedentary | 1.25 | 1.00 | 1.00 |
| Low active | 1.5 | 1.12 | 1.14 |
| Active | 1.75 | 1.27 | 1.27 |
| Very active | 2.2 | 1.54 | 1.45 |

Bands are PAL < 1.4, < 1.6, < 1.9, else. The code's comment says the four PAL representatives are the project's own choice and are not in IOM. Only the band edges and PA values are sourced.

**Non-binary users**: use the mean of the male and female results by default. The user can instead pick a female-typical or male-typical reference (`calories_profile`). Not relevant for us.

**Goal adjustment.** Daily goal = TDEE + goal adjustment + user offset + today's activity kcal.
- Default adjustment: lose = -500 kcal, maintain = 0, gain = +500 kcal.
- If the user sets a weekly rate r (kg/week, signed): `adjustment = r * 1100`. The constant is 7700 kcal per kg divided by 7 days.
- Optional **taper**, off by default, needs a target weight. With d the absolute distance to target in kg:
  - Past or at target (direction-aware): adjustment is 0.
  - d <= 1: 0.
  - d >= 5: full adjustment.
  - Between: linear from 1 to 5, `adj * (d - 1) / 4`.
- Free user offset in kcal (Settings). The offset is not clamped [unverified].
- Activity kcal logged today are **added** to the goal (see section 6). Imported health workouts are scaled by 0.5 to 1.0 (section 6).

**Floors and warnings** (soft, never blocking):
- Below 1500 kcal for male, below 1200 for others, a warning card shows "consult a professional". `CalorieGoalCalc.isBelowRecommendedDailyKcalFloor`. The check is strict less-than.
- Under 19 years, the form says the adult equations are being used. Minimum age is 13.
- There is no hard minimum and no cap on the deficit rate [unverified: weekly-rate dialog bounds were not read].

**Macros.**
- Macros are percentages of the calorie goal, not per-kg. Defaults are 60% carbs, 25% fat, 15% protein (WHO TRS 916 per the README).
- Grams = `kcal * pct / density`. Density: carbs 4, protein 4, fat 9 kcal/g.
- The user can override the three percentages (`userCarbGoalPct` and the like in config).
- There is no protein-per-kg logic and no muscle-gain preset. A "build muscle" goal is only a +500 kcal surplus with the default split.

**Per-meal targets.** Share of daily kcal per slot: default 30/40/20/10 (breakfast, lunch, dinner, snack). Presets: Mediterranean 25/45/20/10, two-meal 40/0/50/10, one-meal-a-day 0/0/100/0, five-small 20/25/25/30 (`core/domain/entity/meal_pattern_entity.dart`). Per-meal target = `daily goal * share / 100`.

**Other calcs present:** BMI (WHO), a healthy-weight range, DRI reference bars for ten micronutrients (`dri_reference.dart`), MET-based activity burn using the 2024 Compendium.

## 4. Units and servings

Files: `features/meal_detail/util/meal_quantity_converter.dart`, `features/add_meal/util/portion_unit.dart`, `core/utils/calc/unit_calc.dart`, `core/domain/usecase/compute_recipe_nutrition_usecase.dart`.

- **Base unit**: every food is per 100 g or ml. ml is treated 1:1 with g everywhere (the recipe code states this as a v1 simplification). There is no density table.
- **Dropdown units**: grams and ml (shown as g or ml per the food), oz, fl oz, and "serving". Imperial display is a user preference.
- **Conversion to base** (`convertQuantityToBaseUnit`):
  - g or ml: as is.
  - oz: times 28.3495. fl oz: times 29.5735.
  - serving: times the food's serving grams.
  - A named portion (backend foods only): times that portion's gram weight.
- **Serving grams** come from OFF's numeric serving quantity. If missing, the code parses the last "NN g" or "NN ml" out of the serving text. "12 oz (355 ml)" gives 355. A serving with no metric figure ("1 egg") gives null, and the amount is left as entered, so "1 serving" is logged as 1 g (a known edge, see section 8).
- **Stored unit string**: a small closed set: `g`, `ml`, `oz`, `fl oz`, `serving`. Extra backend portions are encoded as `serving#1`, `serving#2`. The suffix is stripped before storage. Reason: the stored string is part of the export format and a positional QR-share payload, so it must not carry dataset prose. This is a thoughtful backward-compatibility choice.
- **Custom units / household measures**: none for user-defined foods (no "1 katori = 150 g"). Only g or ml, plus a serving size the user can enter on a custom meal [unverified: custom-meal serving fields].
- **Display**: kcal or kJ switch is display-only, factor 4.184, and storage is always kcal. Heights in cm or ft/in, weights in kg, lb or stone.
- **Recipes**: each ingredient is converted to grams. Recipe per-100 g equals the sum of `(ingredient per-100 * grams / 100)` divided by total grams. A nutrient that is null on every ingredient stays null on the recipe. A recipe with N servings exposes a serving of total grams divided by N.

## 5. Food database

Files: `features/add_meal/data/data_sources/{off_data_source,sp_food_data_source}.dart`, `data/repository/products_repository.dart`, `domain/usecase/search_products_usecase.dart`, `scanner/domain/usecase/search_product_by_barcode_usecase.dart`, `core/data/data_source/remote_search_cache_data_source.dart`.

- **Sources**:
  - Open Food Facts (text search plus product by barcode). Requests send a User-Agent naming the app. Country boost is applied on the device. Timeout 60 s.
  - ONT Supabase reference backend: USDA FoodData Central, German BLS, with INDB and TBCA in the schema but empty. Self-hostable (`docs/supabase-self-hosting.md`). We must not use their endpoint.
  - Local: user custom meals, recipes, favourites, recent intake.
- **Search order**: custom-meal matches and recent items first, then remote. Results are de-duplicated. Short as-you-type queries are local-only (`skipRemote`) and there is a debounce (`search_debounce.dart`). Relevance ranking exists (`meal_relevance_ranker.dart`, `soft_text_score.dart`).
- **Barcode lookup order**: (1) the user's own custom meal with that barcode, (2) a full cached OFF record (instant and offline), (3) live OFF, whose result is then cached and also refreshes any favourite of that product. Recipes are not scannable by design. A manual barcode paste is provided.
- **Caching**: remote results are cached locally. Entries are pruned after 90 days unless touched. Logging an item refreshes its timestamp and does a background refresh from OFF. A thin search hit is "hydrated" to the full record on open, with a soft failure that still allows a macros-only log.
- **Offline**: diary, custom meals, recipes and cached foods all work offline. Live search and first-time scans need a network. Failure is surfaced, not hidden.
- **Attribution/licence**: OFF is ODbL. ONT gives the datasets credit in the Sources screen and README. We must do the same (project rule 8).

## 6. Aggregation

- **Per entry**: `kcal = grams_in_base_unit * (energy_per_100 / 100)`, and the same for carbs, fat and protein (`IntakeEntity.totalKcal` and friends). A missing nutrient counts as 0 (`?? 0`). This is a flaw for us (section 10).
- **Daily totals** are persisted on the TrackedDay record, updated by read-modify-write when an entry is added (`meal_detail_bloc.dart` `addIntake`, `addDayCaloriesTracked`, `addDayMacrosTracked`). Totals are not recomputed from entries on read.
  - Because of this there is a tracked-day lock, and a rollback that restores the previous totals and deletes the entry if the totals update fails ("all or nothing", #1461).
  - There is also a reconciler and a total-repair utility (`core/utils/tracked_day_reconciler.dart`, `tracked_day_total_repair.dart`). These exist because the cached-total design drifted.
- **Home** (`home_bloc.dart`) sums the four meal lists, computes goal via `GetKcalGoalUsecase`, then `kcal_left = goal - intake`.
- **Over goal**: the dashboard shows the overshoot amount and flips the colour. Left greater than goal (negative intake) is capped in display [unverified detail].
- **Exercise**: burned kcal of today's activities are summed and **added to the goal** (eat-back model), not subtracted from intake. Imported health-app workouts are multiplied by a factor from 0.5 to 1.0, suggested from body composition via an energy-compensation paper (Careau et al. 2021): about 0.72 by default, interpolated by body fat or BMI (`workout_compensation_calc.dart`). The 28% default and the 29.7% / 45.7% ends are in the file's comments.
- **Day rating**: a day is "good" if intake is within 500 kcal over goal or within 1000 kcal under goal, else "poor" (`tracked_day_entity.dart`, constants `maxKcalDifferenceOverGoal` = 500 and `maxKcalDifferenceUnderGoal` = 1000). A day with nothing logged is untracked.
- **Weekly views**: Trends has 7, 30, 90 days and all-time windows. It shows calories against the goal line, daily macro averages, a micronutrient day and week view, water, and weight (`features/trends/`).
- **Micronutrient panel**: ten nutrients, per day and week, with optional reference-intake bars.

## 7. Progress

- **Weight log**: one entry per local day (key `yyyy-MM-dd`), optional note. Added in onboarding and on demand. Delete finds the row by the stored day key, not the displayed date, because a time-zone change can shift the date (#1418, `weight_log_entity.dart`).
- **Chart**: raw dots plus an optional trailing 7-day moving average anchored on entry dates (`weight_moving_average.dart`). Points backed by fewer than 2 samples can be dropped. The window uses calendar arithmetic so DST does not drop entries. A dashed target-weight line is drawn.
- **Projection**: least-squares line through the weight points gives kg per week, and weeks to target `ceil((target - latest) / slope / 7)` only when the trend moves toward the target and the horizon is under 3650 days (`trends_calc.dart`, `weightProjection`). Needs 2+ points. Honest: no date is promised if the user is heading away.
- **Streak**: current and longest run of consecutive "good" days in the window. An untracked or poor day breaks the run (`streakStats`). The README says "no streak guilt" and no unrequested notifications.
- **Goal completion**: the taper (section 3) eases the deficit to maintenance near target. Whether a "goal reached" screen exists is [unverified].
- BMI card and healthy-weight range on Profile.

## 8. Edge cases

- **Missing nutrients**: stored as null per field. Per entry, null energy contributes 0 kcal silently. `kcalForQuantity` does return null when there is no energy. Recipes keep a nutrient null only if all ingredients lack it. The UI hides unknown micros.
- **Rounding**: ONT keeps full-precision doubles in storage. Display rounding is per surface. Unit helpers round on purpose: lb to 1 decimal, kg from lb to 2 decimals, cm to whole numbers, stone/lb rolls over at 14 so "9 st 14 lb" cannot appear for 10 st.
- **Day boundary**: a configurable "diary day starts at HH:MM" offset (night shifts, late snacks). An entry before the offset files under the previous calendar day. Timestamps stay wall-clock, and only the day label shifts. There were real bugs (#586): "today" must be resolved through the offset before querying by day label, and a picked calendar date must not itself be offset (`day_boundary_calc.dart`, with a test clock hook).
- **Time zone**: the weight log is keyed by local day and carries a note on time-zone drift (#1418). Diary entries are wall-clock local [unverified for travel across zones].
- **Units without gram weights**: "1 serving" with no metric serving logs the raw number as grams. The converter comment says it deliberately "leaves the amount alone rather than guessing", and the caller is meant to show a visible weight. A known sharp edge.
- **Age**: `age = floor(days since birthday / 365)`, which drifts by leap days (`user_entity.dart`). Minor.
- **Concurrency**: overlapping `addIntake` calls lose updates on the read-modify-write totals. A batch must be awaited one at a time.
- **Hive corruption**: an integrity exception, a recovery screen, and "delete all my data".

## 9. Tests

Dirs: `test/unit_test/`, `test/features/*`, `test/widget_test/`, `integration_test/`. About 835 Dart files under lib and test combined; the tests are numerous and unusually specific.

- **Target maths**: `tdee_calc_test` (male, female, non-binary mean), `calorie_goal_calc_test` (default -500/0/+500, weekly-rate adjustment, user offset, goal minus intake), `calorie_taper_test` (off, null target, maintain, lose and gain at 5 kg, mid-taper, 1 kg, at and past target), `healthy_weight_calc_test`, `workout_compensation_calc_test`.
- **Aggregation**: `intake_repository_test`, `tracked_day_total_repair_test`, `tracked_day_listed_day_test`, `meal_detail_add_intake_rollback_test`, `daily_nutrient_panel_goal_reference_test`.
- **Units and portions**: `portion_unit_test`, `portion_label_test`, `unit_dropdown_item_test`, `locale_units_test`, `edit_meal_simple_mode_scale_test`.
- **Food and search**: `sp_food_data_source_portions_test`, `sp_food_data_source_ranking_test`, `off_name_fallback_test`, `custom_meal_data_source_test`, `compute_recipe_nutrition_usecase_test`, `quick_add_round_trip_test`, `bulk_add_bloc_test`, `resolver_sibling_selection_test`.
- **Progress**: `trends_calc_test` (streaks: all days, gap, current run, empty; projection: fewer than 2 points, steady loss, flat, moving away).
- **Day and calendar**: `diary_day_selection_offset_test`.
- **Import/export**: `import_data_usecase_upsert_test`, `import_meals_json_usecase_test`, `json_recipe_importer_test`, `export_write_verifier_test`.
- **Other**: l10n parity checks, store-declaration checks, a few widget tests. Tests are pure-function heavy and have no fixtures of shared expected values across platforms.
- Not seen: tests for the PA band edges at exactly 1.4, 1.6, 1.9 [unverified].

## 10. Ideas to adopt and weaknesses to avoid

### Adopt (in our own design)

1. **Cited, data-driven targets with a bracket-correct published equation.** Pick one sourced equation (Mifflin-St Jeor or IOM), put constants in a data file with a source note, and add a golden-value test per sex and activity band. ONT's PA-bracket bug (109 to 489 kcal/day) shows why: write the formula with explicit parentheses and test against hand-computed values. This also fits our rule that thresholds live in data and clinical numbers are marked pending review.
2. **Snapshot the food on every diary entry, and store the day's goal on the day record.** History must not change when a food or the profile changes. Store nutrients per 100 g and compute entry values from grams.
3. **Closed, export-safe unit vocabulary.** Store grams as the canonical quantity plus a small unit code, and keep portion labels out of stored values. For India add household units with explicit gram weights (katori, roti, glass), each carrying a gram weight, never a guess.
4. **Barcode order: your own foods, then local cache, then live lookup, then write back to cache.** Plus an offline-first diary, and a failure state distinct from "no results". Search should rank custom foods and recent items first.
5. **Soft safety rails, not hard blocks.** Low-calorie floor warning, plausible-range confirm on height and weight, adult-equation notice for young users. Matches our "information, not medical advice" copy.
6. **Honest progress maths**: 7-day moving average over raw weigh-ins, a least-squares weekly rate, and a projection only when the trend heads toward the target. Add a taper near the target weight so the last kilograms become maintenance.
7. **Day-start offset**, if the diary has late-night eaters, with the lesson learned: resolve "today" through the offset before querying, and never offset a picked calendar date.
8. **Recipe nutrition**: sum ingredient grams, divide by cooked or total weight, keep a nutrient unknown if no ingredient knows it, and offer a servings count.
9. **AI only parses language, never supplies numbers.** Nutrition comes only from the database. This is the same rule as our rules-engine principle.
10. **Per-meal kcal share presets** (a good simple way to show "remaining for dinner").

### Weaknesses to avoid

1. **Cached running totals with read-modify-write.** This caused lost updates, a lock, rollback code and repair utilities. Compute day totals from entries in a query or a database view, or update them in one transaction. We have Postgres, so use a view or aggregate query.
2. **Missing nutrient counted as zero.** A logged food with no energy silently adds 0 kcal, and an unknown looks like a real zero. For us: an unknown value should show "incomplete" on the entry and the day, and must never feed a green "on track" state (rule 3: unknown is not safe).
3. **"1 serving" with no gram weight logs 1 g.** Block the log or ask for grams; never default silently.
4. **Fixed macro percentages (60/25/15) and no protein-per-kg.** Poor fit for our "build muscle" user and for diabetes (high carb share). Drive protein from body weight (g/kg, in a data file) and let carbs and fat fill the rest. Thresholds go in YAML with a clinician-review flag.
5. **Fixed 500 kcal goal steps and `age = days/365`.** Use calendar age and a rate-based adjustment with caps (clamp the weekly rate and the minimum calories), validated server-side.
6. **Eat-back exercise added to the goal.** Easy to over-credit. If we support exercise, make it opt-in, discount it, and show it separately.
7. **Treating ml as g everywhere.** Fine for water-like foods, wrong for oil, honey and milk. Add a density field where known, else say so.
8. **No shared test fixtures.** Our fixtures plus the three-platform rule should be stricter than ONT's pure unit tests.
9. **Clients computing targets.** ONT does everything on the phone. We must keep targets and verdict-like numbers in the API so Android and web cannot disagree.
10. **Day rating thresholds (+500 / -1000) are arbitrary** and do not depend on the goal type. A "poor" day for a bulking user could be a fine day. Make tolerances goal-aware and in data.
11. **Licence**: ONT is GPL-3.0. Do not copy code, strings or UI assets. This document is the only thing derived from it.

## Sources

Web (not fetched live in this run; cited from the repo copies):
- https://github.com/simonoppowa/OpenNutriTracker
- https://hosted.weblate.org/engage/opennutritracker/ (translations, from README)
- IOM 2005 DRI for Energy, https://doi.org/10.17226/10490 (cited by ONT; equation on p. 204)

Repo files read (commit `ca8f51de9ece6020ab1257b72e86d8955bdd0ace`):
- `README.md`
- `docs/tdee-iom-2005-verification.md`, `docs/competitive-feature-gaps.md` (listing), `docs/export-format.md` (listing only)
- `lib/core/utils/calc/tdee_calc.dart`, `pal_calc.dart`, `calorie_goal_calc.dart`, `macro_calc.dart`, `unit_calc.dart`, `day_boundary_calc.dart`, `workout_compensation_calc.dart`, `weight_moving_average.dart`
- `lib/core/utils/bounds/ranges_const.dart`, `lib/core/utils/barcode_validator.dart`
- `lib/core/domain/entity/user_entity.dart`, `intake_entity.dart`, `tracked_day_entity.dart`, `weight_log_entity.dart`, `recipe_entity.dart`, `recipe_ingredient_entity.dart`, `meal_pattern_entity.dart`, `config_entity.dart`, `user_pal_entity.dart`, `day_rating.dart`
- `lib/core/domain/usecase/get_kcal_goal_usecase.dart`, `get_macro_goal_usecase.dart`, `compute_recipe_nutrition_usecase.dart`
- `lib/core/data/dbo/*` (field layout), `lib/core/data/data_source/remote_search_cache_data_source.dart`
- `lib/features/add_meal/domain/entity/meal_entity.dart`, `meal_nutriments_entity.dart`, `domain/usecase/search_products_usecase.dart`, `util/portion_unit.dart`, `presentation/widgets/quick_add_bottom_sheet.dart`
- `lib/features/meal_detail/util/meal_quantity_converter.dart`, `presentation/bloc/meal_detail_bloc.dart`
- `lib/features/scanner/domain/usecase/search_product_by_barcode_usecase.dart`
- `lib/features/home/presentation/bloc/home_bloc.dart`, `widgets/dashboard_widget.dart`
- `lib/features/trends/presentation/trends_calc.dart`
- `lib/features/onboarding/onboarding_screen.dart`, `presentation/bloc/onboarding_bloc.dart`, `domain/entity/goal_suggestion_entity.dart`
- `test/unit_test/` (file names and the group/test titles in `calorie_goal_calc_test`, `tdee_calc_test`, `calorie_taper_test`, `trends_calc_test`)
