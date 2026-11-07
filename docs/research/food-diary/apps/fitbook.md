# FitBook feature study

- **Repo:** https://github.com/brandonp2412/FitBook, shallow clone read on 2026-11-07.
- **Licence (confirmed from `LICENSE.md`): MIT.** The README states MIT and the file is the standard MIT text. One thing to note: the copyright line reads **"Copyright (c) 2024 Flexify"**, not FitBook or the repo owner. It looks inherited from the author's sibling app Flexify. If we ever adapt code, keep this notice with credit to FitBook and check that line then.
- **Policy for us:** MIT allows adapting with the notice kept. Even so, this doc describes behaviour and does not paste code.
- **Stack:** Flutter, Drift (SQLite), Provider state, schema version 57 (`lib/database/database.dart`). It is offline-first, a single user, with no accounts and no server.
- **Rough scale:** about 88k Dart lines, of which about 28k are generated.

## 1. User flow and screens

Bottom tabs (default `DiaryPage, GraphPage, FoodPage, WeightPage`, configurable in Settings > Tabs; `lib/bottom_nav.dart`, `lib/settings/tab_settings.dart`).

1. **Diary** (`lib/diary/diary_page.dart`, `diary_list.dart`). Entries are grouped by day. For today it shows a "Today progress" card with a bar per calories, protein, carbs and fat against the daily target. Each list row shows the day total, which can be formatted as used/target, remaining, or both (setting `diarySummary`: `division`, `remaining`, `both`, `none`). Search, filters (food group, start and end date), multi-select, repeat entry, and an add button with a speed dial.
2. **Add or edit a diary entry** (`edit_diary_page.dart`, 1.3k lines). Search or pick a food or a meal, enter quantity and unit (dropdown), pick the date and time, and see computed totals. A barcode scan is available (`scan_barcode.dart`). The last-used unit is remembered.
3. **Quick add** (`quick_add_page.dart`). Type calories and macros only. It creates or reuses a food named "Quick-add" and logs it, and the form prefills from the last quick add.
4. **Food** tab (`lib/food/`). A list of foods and meals with favourites, an editor for custom foods (a large nutrient form), a meal editor, and a food filter by group.
5. **Search Open Food Facts** (`search_open_food_facts.dart`). Imports a product into the local foods table.
6. **Graph** (`graph_page.dart`, `app_line.dart`, `app_line_chart.dart`). A metric dropdown (calories, body weight, or any enabled nutrient field), a period picker (day, week, month, year), a date range, and chart series toggles: value, goal line and trend line.
7. **Weight** (`lib/weight/`). A list of weigh-ins, an add and edit screen with unit and optional photo.
8. **Settings** (`lib/settings/`). Diary, food, weight, chart and appearance settings, backup and import/export, an OFF login, and reminders.

## 2. Data model (`lib/database/*.dart`, Drift)

| Table | Fields | Relations and indexes |
|---|---|---|
| `foods` | id, name, barcode, favorite, created, food_group, image_file, small_image, big_image, **`serving_size` real, `serving_unit` text**, `serving_description_1..9_g`, `serving_weight_1..9_g`, `_200_calorie_weight_g`, **about 100 nullable real nutrient columns**: calories, protein_g, fat_g, carbohydrate_g, fiber_g, sugars_g, added_sugar_g, sodium_mg, cholesterol_mg, vitamins, minerals, amino acids, fatty acids and more | indexes: (favorite desc, created desc), barcode |
| `diaries` | id, `food` nullable FK to foods, `meal` nullable FK to meals, created datetime, **quantity real, unit text** | indexes: created desc, (food, created desc), meal |
| `meals` | id, name, created, favorite, image_file | |
| `meal_foods` | id, meal FK, food FK, quantity real, unit text | indexes on meal and on food |
| `weights` | id, created, unit text (kg or lb), amount real, image nullable | index on created |
| `settings` (single row) | **targets:** dailyCalories, dailyCarb, dailyFat, dailyProtein, dailyFiber (all nullable ints) and **targetWeight** (real); **autoCalc** (bool); diarySummary, entryUnit, foodUnit, fields (CSV of tracked nutrients), tabs, convertWeight, graphSeries, locale, backup path, OFF login, UI flags and chart options | one row |
| `metadata` | buildNumber | |

Key design facts:
- A **diary row references one food or one meal** (both FKs nullable). The entry stores **no nutrient values**. Nutrients are computed live by SQL from the current food row (see section 4), so editing a food rewrites history. The opposite choice to kcal.
- Nutrient values on a food are **per `serving_size` of `serving_unit`**. The v53 migration comment says v52 wrongly normalised them to per-100g and then reversed it, so per-serving is the stored meaning.
- `serving_weight_N_g` and `serving_description_N_g` come from the CORGIS dataset (up to 9 household measures per food, for example "1 cup = 244 g"). In `lib/` they only appear as labels (`utils.dart`) [unverified: I found no code path that uses them to convert units. They look like stored data only].
- There is no per-weekday target. Targets are one global set in `settings`.
- Meals are saved combinations of foods ("recipes" without steps) with an optional photo.

## 3. Unit and serving model (`lib/utils.dart`)

**Units:** grams, milliliters, milligrams, kilograms, ounces, pounds, cups, tablespoons, teaspoons, liters, kilojoules, plus the special `serving`.

**Fixed gram factors:** ml 1, cup 250, tbsp 15, tsp 5, oz 28.35, lb 453.592, kg 1000, litre 1000, mg 1/1000, kJ 1/4.184. So **volume is treated as water density** (1 ml = 1 g). This is accurate enough for water-like foods and wrong for oil, flour or rice [my reading, not stated by the author].

**Conversions (in words):**
- *Food serving grams* (`servingGrams`, and the SQL twin `servingGramsSql`): no size means 100 g, no unit means the size itself, known unit means size times factor, `serving` means the size as grams, unknown means 100.
- *Entry grams* (`entryQuantityInGramsSql`): `serving` = quantity times the food's serving grams, a known unit means quantity times factor, unknown means the quantity as is.
- *Nutrient for an entry* = (entry grams) × (food nutrient per serving) ÷ (food serving grams). Missing nutrient is treated as 0 in this SQL (`COALESCE(..., 0)`), and a zero serving gives NULL, which becomes 0.
- *Per-100 g display value* (`valuePer100g`) returns **null** (not a guess) when the serving unit cannot become grams (for example `serving` or `unit`).
- *`convertCustomServing`* rebuilds a Food at a custom quantity and unit. It covers calories, protein, fat, carbs and fibre only.
- **Weight units for body weight:** kg and lb, converted with a rough divide or multiply by 2.2 (`edit_weight_page.dart`).

**Open Food Facts mapping** (`mapOpenFoodFacts`): per 100 g or per serving according to the `foodUnit` setting. The serving size comes from the product's serving quantity, or 100 g. Unit is always grams, and kcal is computed from kJ ÷ 4.184. About 40 nutrients are mapped, with missing values left null.

**Starter data:** `assets/food-data.zip` (a JSON of about 7,000 foods derived from CORGIS, per the README) is inserted on first database creation (`onCreate`). A CSV of the same data also sits in `assets/food.csv`. CORGIS is a US dataset. It is not suited to Indian foods.

## 4. Recipe (meal) nutrient calculation

- A "meal" is a list of `meal_foods` (food, quantity, unit). A meal's nutrient per entry is computed in SQL: for each component, grams times nutrient per serving gram, summed, then multiplied by the **diary quantity** (the number of meal servings) (`mealAwareFieldExpr`, `mealFoodsFieldSumSql`).
- A meal has no stored "servings" or yield. Logging 0.5 of a meal halves everything.
- There are no cooked-weight or yield adjustments and no steps or instructions.

## 5. Goals and targets

- **Manual targets:** `dailyCalories`, `dailyProtein`, `dailyCarb`, `dailyFat`, `dailyFiber` and `targetWeight` in `settings`. All are optional. If a target is null, the card shows only the value, with no bar.
- **Auto-calc** (`autoCalc` flag, `getMacros` in `utils.dart`, applied in `edit_weight_page.dart` after every weigh-in): the targets are **overwritten** on each new weight, computed from bodyweight in kg: **calories = 27.5 per kg, protein = 1.6 g per kg, fat = 0.8 g per kg, carbs = 5 g per kg**. The values are truncated to ints.
  - Observation: the macros do not add up to the calories (5×4 + 1.6×4 + 0.8×9 is about 33.6 kcal per kg, not 27.5). So the calorie figure and macro figures are independent rules of thumb. [my arithmetic]
  - No sex, age, height or activity input, no deficit or surplus, and no percent split.
- No per-weekday targets, no rest or training day variants.

## 6. Aggregation and remaining

- The diary stream (`diary_state.dart`) selects diary rows joined to foods and meals, with the nutrient expressions computed in SQL, newest first, limited to 100 rows by default (`limit`).
- `groupByDay` (`diary_stats_utils.dart`) groups by **local calendar day** and sums calories, protein, fat, carbs and fibre.
- **Remaining** = target minus current, formatted with locale-aware numbers (`diary_list.dart` `_summaryText`). It can be negative when over the target, and nothing clamps it.
- The progress bar value is clamped to 0..1 (`diary_page.dart` `_summaryCard`), and it is hidden when the target is null or zero.
- Graph bucketing (`bucketGraphData`): sum per day, then for week, month or year the **average per day that has data** (not per calendar day), the most recent N buckets, oldest to newest. Days with no entries therefore do not drag the average down.

## 7. Weight and progress

- `weights` holds timestamped weigh-ins in kg or lb, optional photo. An add or edit page has a unit toggle and a "convert to" preference (`convertWeight`) that rewrites the stored value and unit on save.
- Graph metric "body-weight" shows the series, with an optional **goal line** (the `targetWeight`) and an optional **trend line** (a straight-line fit with slope and intercept, `_calcTrend` in `app_line.dart`).
- A "positive reinforcement" toast (`shouldNotify` in `utils.dart`) appears with 30% probability when the new weight moves toward the target and is within 1 unit of it.
- Graph goal lines exist for calories, protein, fat, carbs and weight. The target is constant over time, so past days are compared against today's target.
- No BMI, no rate-of-loss or ETA, no weekly average weight.

## 8. Edge cases found

- Orphans: older versions left diary rows pointing at deleted foods or meals. Migration 51 to 52 clears the dangling references and deletes dangling `meal_foods`, and `beforeOpen` repeats this idempotently. FKs are enforced with `PRAGMA foreign_keys = ON`.
- Migration 52 corrupted nutrient values by wrongly normalising them, and 52 to 53 applied an exact inverse. A cautionary tale for data migrations (`database.dart`).
- A debug-only foreign key check runs after migrations.
- Units that cannot convert throw. SQL falls back to treating the quantity as grams.
- Empty `serving_size` falls back to 100 g.
- `valuePer100g` returns null for non-weight serving units rather than inventing a number.
- The diary preview total in `edit_diary_page.dart` divides quantity by serving size without converting units, whereas the stored SQL converts through grams. A mismatch is possible when the entry unit differs from the food unit [unverified; I read only the getter, not the full unit-dropdown logic].
- Graph averaging per day-with-data (see section 6). Day boundaries use device local time.
- Weight kg/lb uses 2.2, so a round trip can drift.
- The diary `limit` of 100 rows means today's totals could be incomplete for a very busy history [unverified].

## 9. Tests (`test/`, `integration_test/`)

- `nutrient_calc_test.dart`: the SQL expression converts ounce entries to grams, applies a meal-food serving unit conversion, and so on (in-memory DB).
- `per_100g_test.dart`: normalising gram servings, converting units first, and returning null for serving or unit.
- `serving_unit_bug_test.dart`: custom serving conversion for gram and non-gram bases, and throws on `serving`.
- `meal_test.dart`: create, edit, delete and search meals and removing a food.
- `diary_page_test`, `diary_state_date_filter_test`, `edit_diary(ies)_test`, `quick_add*_test`, `weight_page_test`, `edit_weight_page_test`, `graph_page_test`, `app_line_chart*_test`.
- Data safety: `database_foreign_keys_test`, `database_bootstrap_isolation_test`, `import_data_test`, `automatic_backup_test`, `delete_records_test`.
- `test/drift/db/migration_test.dart` and `schema_validation_test.dart` with stored schema snapshots (`drift_schemas/db`, one JSON per version) check migrations from every old version.
- `integration_test/`: performance, screenshots and Windows smoke tests.
- Good test hygiene for the calculation core; the targets and auto-calc maths had no dedicated test among the file names I listed [unverified].

## 10. Best ideas and weaknesses

**Ideas worth borrowing (MIT, may adapt later with credit)**
1. **Quantity plus unit on every diary row, resolved to grams in one place.** A single "to grams" function, mirrored in SQL, keeps totals consistent across the list, the day card and the graphs.
2. **`serving` as a first-class unit** that multiplies the food's own serving grams. Good for "1 roti", "1 katori".
3. **Null-safe normalisation.** `valuePer100g` refuses to guess. It fits our "never invent data" rule.
4. **Summary mode** for the day: used/target, remaining, both, or none, as a user setting. Plus a bar clamped at 100%.
5. **Quick-add** for logging calories and macros without a food, with prefill from the last entry.
6. **Graph model:** daily totals bucketed to week, month or year and averaged over days that have data. Goal line and trend line are toggles.
7. **Weight with kg/lb, a goal line, a trend fit** and an optional photo. A simple, well-understood slice.
8. **Migrations discipline:** versioned schema snapshots, a migration test per version, FK enforcement and idempotent orphan repair.
9. **Meals** as saved combos, with favourites and recent entries, for fast repeat logging.
10. **Auto targets from weight** as an opt-in (but see weaknesses).

**Weaknesses (do not copy)**
- Totals computed live from the current food, so editing a food silently changes all past days. We should snapshot nutrients at log time, or version the foods.
- Auto-calc: a bare rule of thumb (27.5 kcal/kg and so on) with no sex, age, height, activity or goal, and macros that are inconsistent with the calories. It also overwrites the user's manual targets on every weigh-in. This is a health-advice risk for us. Any formula needs a clinician review and the `PENDING CLINICIAN REVIEW` mark under our rules.
- One global target and no weekday variants. Past days are judged against today's target.
- A very wide `foods` table (about 100 nullable columns), and missing values count as 0 in totals, which silently undercounts. We need unknown to stay unknown.
- Volume equals water density (cup = 250 g). Wrong for many Indian staples (rice, atta, dal, oil).
- US-centred CORGIS seed data and US serving descriptions.
- The CORGIS 9-serving columns look unused for conversion, which wastes the best data in the set.
- No cross-device sync, one person, no accounts.
- The meal model has no yield or cooked weight, and no ingredient scaling beyond a multiplier.
- Weight conversion uses 2.2, not 2.20462.
- Day grouping by the device's local time zone. The Flutter-only logic means a web client would need to copy it. For SmartNutri the day boundary must be decided once (server, user time zone).

## Sources

Read in the clone at `.../scratchpad/fooddiary-repos/FitBook/`:
- `LICENSE.md` (MIT, "Copyright (c) 2024 Flexify"), `README.md`, `AGENTS.md`, `ROADMAP.md` (localisation only), `pubspec.yaml`
- `lib/database/database.dart` (`onCreate`, `onUpgrade`, `beforeOpen`, migrations 40 to 55, `schemaVersion` 57), `foods.dart`, `diaries.dart`, `meals.dart`, `meal_foods.dart`, `weights.dart`, `settings.dart`, `metadata.dart`
- `lib/utils.dart` (unit conversion, SQL builders, `getMacros`, `shouldNotify`, `bucketGraphData`, `mapOpenFoodFacts`)
- `lib/constants.dart`
- `lib/diary/diary_page.dart`, `diary_state.dart`, `diary_stats_utils.dart`, `stats.dart`, `diary_list.dart` (`_summaryText`), `edit_diary_page.dart` (partial)
- `lib/quick_add_page.dart`, `lib/weight/edit_weight_page.dart`, `lib/graph_page.dart`, `lib/app_line.dart` (partial)
- `lib/bottom_nav.dart`, `lib/settings/diary_settings.dart`
- `test/` file names and `nutrient_calc_test.dart`, `per_100g_test.dart`, `serving_unit_bug_test.dart`, `meal_test.dart` test names
- `assets/` listing (`food-data.zip`, `food.csv` header)

Not read in depth: `edit_food_page.dart`, `edit_meal_page.dart`, `import_data.dart`, `search_open_food_facts.dart`, the generated Drift files, and the contents of `food-data.zip`.
