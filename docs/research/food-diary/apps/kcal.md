# kcal feature study (clean-room, ideas only)

- **Repo:** https://github.com/kcal-app/kcal, shallow clone read on 2026-11-07.
- **Licence:** MPL-2.0 (`LICENSE`). This is a file-level copyleft licence, so we take **ideas only**. Nothing below is code. Everything is described in our own words.
- **Stack:** Laravel (PHP 8.4) on Postgres, server-rendered Blade views plus a JSON:API. Self-hosted, multi-user, with foods and recipes shared between users.
- **Stance (README):** a *personal* tracker. It has no external food database, on purpose: the authors avoid noisy crowd data and third-party calls. This matters for SmartNutri, because we do the opposite (OFF plus a curated base).

## 1. User flow and screens

Routes live in `routes/web.php` and the controllers are in `app/Http/Controllers/`.

1. **Journal (day view)** (`JournalEntryController@index`). It shows the chosen date, the entries grouped by meal, the day's nutrient sums and a percentage of goal per nutrient. A goal picker lets you override the goal for that one date.
2. **Add entries** (`create` view). This is a multi-row form with date, meal, amount, unit and an ingredient picker (food or recipe). Rows can be grouped into one entry per date and meal (`group_entries`).
3. **Add from nutrients.** This is manual entry (`createFromNutrients`) for things that are not in the database, so you type calories and macros directly.
4. **Foods, Recipes, Goals, Meals and Profile screens.** Meals are a per-user setting. The user has up to 8 meals, each of which can be renamed, reordered and enabled; the default is 3 enabled.
5. **Entries are not editable.** There is only delete (`destroy`). To correct something you delete and re-add. This is stated in the README.

## 2. Data model (migrations in `database/migrations/`)

All nutrient columns are floats. The "6 nutrients" are calories, fat, cholesterol, sodium, carbohydrates and protein.

| Table | Fields | Relations |
|---|---|---|
| `users` | name, username, password, api_token, `meals` (JSON of 8 `{value,label,weight,enabled}`) | has many goals, journal_dates and journal_entries |
| `foods` (shared) | name, unique slug, detail, brand, source, notes, `serving_size` decimal(14,8), `serving_unit` enum (tsp/tbsp/cup/oz, nullable), `serving_unit_name` (free text such as "slice"), `serving_weight` (grams of ONE serving), 6 nutrients per serving | taggable, journalable |
| `recipes` (shared) | name, slug, description (plus a rich-text delta), time_prep, time_cook, source, `servings` (int), `weight` (total grams, nullable), `volume` (total cups, nullable) | has many steps and separators, ingredient_amounts as parent, taggable, has media |
| `recipe_steps` | recipe_id (cascade), number, step text | belongs to recipe |
| `recipe_separators` | recipe_id, container, weight (order), text | section headings inside a recipe |
| `ingredient_amounts` | **polymorphic on both sides.** `ingredient_id/type` (Food or Recipe), `parent_id/type` (the owning Recipe), amount decimal(14,8), unit enum, detail, weight (sort order) | a recipe's lines, so a recipe can contain a recipe |
| `journal_entries` | user_id, date (indexed), `summary` (generated text), meal (int), **6 nutrient totals stored on the row** | many-to-many to foods and recipes through `journalables` (polymorphic pivot, id plus type) |
| `journalables` | journal_entry_id, journalable_id, journalable_type | pivot |
| `goals` | user_id, name, `days` (bitmask, nullable), calories, fat, cholesterol, sodium, carbs, protein (all nullable) | belongs to user |
| `journal_dates` | user_id, date, nullable goal_id, **unique (date, user_id)** | records which goal applies to a date |
| tags and media | polymorphic | for foods and recipes |

Notes:
- There is **no weight or body-measurement table at all** (no progress or weight history). It is a food and goal tracker only.
- Migration `2021_10_31_193051` widened the decimal precision from (10,8) to (14,8) after overflow. This is a hint to pick wide numeric types up front.

## 3. Unit and serving model (`app/Support/Nutrients.php`, `Models/Traits/Ingredient.php`)

**Unit vocabulary:** cup, gram, oz, serving, tbsp, tsp. Each unit has a type: *volume* (cup, tbsp, tsp), *weight* (gram, oz) or *division* (serving). The constant is 28.349523125 g per oz.

**A food stores nutrients per "serving"**, defined by three fields:
- `serving_size` and `serving_unit`, a volume measure, as on a US label (for example "1/4 cup"). This is optional.
- `serving_weight`, the grams in that serving.
- `serving_unit_name`, a display name (for example "tortilla").

**Which units a food supports** (`getUnitsSupportedAttribute`):
- `serving` is always allowed.
- All units of the same type as the food's `serving_unit` are allowed, so a cup-based food allows tsp, tbsp and cup.
- If there is a `serving_weight`, gram and oz are allowed.
- Volume units come in for recipes that have a `volume`.

**Food multiplier** (`calculateFoodNutrientMultiplier`), in words:
- oz: grams = amount × 28.3495, divided by serving_weight.
- serving: the amount itself.
- gram: amount divided by serving_weight.
- A volume unit that equals the food's unit, or a food with no unit: multiplier 1.
- Volume to volume goes through fixed ratios (tsp:tbsp:cup is 48:16:1).
- The result for volume units is `ratio / serving_size × amount`.
- Any other combination throws a `DomainException`.
- Result = nutrient per serving × multiplier.

There is **no density**. A volume unit can never be converted to grams, so a food needs a gram weight entered by the user to allow gram logging.

**Display extras:**
- Amounts accept and render fractions such as 1/3 and 2/3 (`Support/Number.php`).
- Pluralisation of units is handled, including the serving name.
- Calories and macros are rounded for display in "label style" (`Nutrients::round`): 5 kcal steps under 50 and 10 kcal above, with sodium treated similarly, and so on.

## 4. Recipe nutrient calculation

(`Models/Traits/HasIngredients.php`, `Models/Recipe.php`, `Nutrients::calculateRecipeNutrientAmount`)

- A recipe's **total** for a nutrient is the plain sum of each ingredient line's nutrient. Each line is a food or another recipe, with an amount and unit, computed with the multipliers above.
- **Per serving** = total ÷ `servings`, then rounded for display.
- **Logging a recipe in the journal**, by unit:
  - `serving`: per-serving value × amount.
  - gram or oz: amount in grams ÷ recipe `weight`, times the total.
  - tsp, tbsp or cup: amount divided by the recipe `volume` (in cups), times the total.
- So a recipe supports weight units only if the user entered a cooked `weight`, and volume units only if they entered a `volume`. Otherwise only servings are offered.
- Recipes can be duplicated in one transaction (copies tags, lines, steps and separators).
- Nested recipes work through the polymorphic ingredient line. No cycle guard was found [unverified: I did not search for one].

## 5. Goals and targets

- A **goal** is a named set of per-day targets (calories, fat, cholesterol, sodium, carbs, protein). Every field is nullable.
- **Per weekday:** `days` is a bitmask (Mon=1, Tue=2, Wed=4, Thu=8, Fri=16, Sat=32, Sun=64). A goal can cover any set of days. The request validation accepts values 0 to 64.
- **Resolution for a date** (`User::getGoalByDate`):
  1. Get or create the `journal_dates` row for that date.
  2. If that row already has a goal (an explicit override or an earlier snapshot), use it.
  3. Otherwise take the first goal whose bitmask includes that weekday, and **save the link on the date row**. This freezes history: later edits to weekday defaults do not rewrite past days (the link, not the numbers, is frozen).
  4. No match means no goal for the day.
- **No macro split formula and no calorie formula.** The user types gram and calorie targets by hand. There is no BMR, TDEE or percent-split logic. The README says it deliberately gives no diet guidance.
- Reference daily values exist in code (`Nutrients::all`: 2000 kcal, 275 g carbs, 78 g fat, 50 g protein, 2300 mg sodium, 300 mg cholesterol). They are US label values and are used as defaults only [unverified where they are displayed].

## 6. Aggregation and remaining

(`JournalEntryController@index`)
- Load the user's entries for the date. The day sum per nutrient is a sum of the stored entry columns, rounded.
- Progress per nutrient = sum ÷ goal × 100, shown as a percent. It is computed only when the goal for that nutrient is above 0.
- There is **no explicit "remaining" number** in the controller, only percent of goal [unverified for the view layer; I did not read the Blade templates in depth].
- **Snapshot design:** each entry stores its own nutrient totals plus a text summary. Editing a food or recipe later does not change history (README: "entries are not editable"). Totals are added in a single pass when saving, grouped per date and meal if requested.
- Meal grouping uses the entry's `meal` integer, matched to the user's meal settings.

## 7. Weight and progress

None. No weight, no charts and no trends. History is only the journal itself.

## 8. Edge cases found

- Unsupported unit pairs throw an exception (so a UI must only offer supported units, which `units_supported` does).
- A food with no `serving_unit` and no name works as "count of the item" (for example "2 onions"), and the summary text pluralises the food name.
- A recipe with no `weight` or `volume` cannot be logged in grams or cups.
- Serving sizes that look like fractions (1/3, 2/3) are matched using fraction logic, so float noise does not break the display.
- A goal bitmask can overlap between goals. The first match wins (query has no explicit order, so the pick is not deterministic) [unverified].
- Division by zero is possible if `serving_weight` or recipe `weight`/`volume` is 0. Nothing clearly guards it [unverified].
- A decimal overflow bug was fixed by widening columns (see section 2).
- A missing nutrient is stored as 0 (`default(0)`), not null. This is the opposite of SmartNutri's rule that a missing value is `None`.

## 9. Tests (`tests/`)

- Unit tests: nutrient rounding (including an invalid nutrient name), number and fraction parsing, array formatting, and validation rules (positive decimal or fraction, "uses ingredient trait", in-array, array-not-empty).
- Feature tests: food multiplier validity and invalid cases, recipe nutrient amounts (`tests/Feature/Support/NutrientsTest.php`).
- HTTP controller tests for the journal, goals, foods, recipes, meals, profile, users, auth and the ingredient picker.
- JSON:API tests for each resource.
- There are no tests of weekday goal resolution as a pure unit; it is exercised through the controller and API tests [unverified, not read in detail].

## 10. Best ideas and weaknesses

**Ideas worth borrowing**
1. **Units have a type** (weight, volume, division), and each food declares which types it supports. The UI only offers valid units, so a conversion never throws in normal use.
2. **Snapshot at log time.** Store the computed nutrients on the entry so history survives edits to foods. Pair this with a stored reference to the food for display and re-logging.
3. **Weekday goals stored as a bitmask with a frozen per-date link** (`journal_dates`). It gives training-day vs rest-day targets and keeps past days stable. In SQL we would use a 7-bit smallint or a `days int[]`, and a `daily_targets_snapshot` per date.
4. **Recipes as polymorphic lines** (food or recipe). Totals are a sum and per-serving is total ÷ servings. Add cooked weight to allow gram logging.
5. **Fraction input** ("1/2", "1 1/3") for household measures, which suits Indian cooking (katori, half roti).
6. **Manual "nutrients only" entry** as an escape hatch for unlisted food.
7. A per-user list of enabled and renamed meals.

**Weaknesses (do not copy)**
- No weight or progress tracking, no calorie or macro-split maths.
- Missing nutrient stored as 0, which silently under-counts. It conflicts with our "unknown is not safe" rule.
- Entries cannot be edited.
- US units only (tsp, tbsp, cup, oz). Nothing for katori, roti, piece, ml or litre.
- No density, so volume to grams is impossible.
- Float columns for money-like precision, and only 6 nutrients (no fibre, sugar or added sugar).
- Shared global foods and recipes between all users, with no per-user custom-food ownership.
- Polymorphic ids without foreign keys (journalables, ingredient_amounts), so there is no referential integrity.

## Sources

Read in the clone at `.../scratchpad/fooddiary-repos/kcal/`:
- `LICENSE`, `README.md`, `AGENTS.md`
- `database/migrations/2020_12_21_214128_create_foods_table.php`, `2020_12_21_215932_create_recipes_table.php`, `2020_12_22_051133_create_recipe_steps_table.php`, `2020_12_31_180016_create_journal_entries_table.php`, `2021_01_01_170724_create_journalables_table.php`, `2021_01_22_212856_create_ingredient_amounts_table.php`, `2021_02_13_052427_create_goals_table.php`, `2021_03_26_052715_create_recipe_separators_table.php`, `2021_05_15_082223_create_journal_dates_table.php`, `2021_10_31_193051_fix_decimal_fields_precision.php`
- `app/Support/Nutrients.php`, `app/Support/Number.php`
- `app/Models/Food.php`, `Recipe.php`, `IngredientAmount.php`, `Goal.php`, `JournalDate.php`, `JournalEntry.php`, `User.php`
- `app/Models/Traits/Ingredient.php`, `HasIngredients.php`
- `app/Http/Controllers/JournalEntryController.php`, `GoalController.php`
- `app/Http/Requests/UpdateGoalRequest.php`
- `routes/api.php`
- `tests/` (file listing and test names in `tests/Unit/Support/NutrientsTest.php`, `tests/Feature/Support/NutrientsTest.php`)

Not read in depth: Blade views, `StoreJournalEntryRequest`, the JSON:API schema classes and the factories.
