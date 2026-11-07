# ADR 0024: Foods and household units: USDA FoodData Central and documented dishes; `to_grams` refuses to guess

- **Status:** Accepted (Plan 12 slice 3, Rulings G2-G11, 2026-11-07). Every household measure, density, dish and yield is PENDING DIETITIAN REVIEW.
- **Date:** 2026-11-07

## Context

A person logs "1 katori dal" or "2 roti", not grams. To turn a household unit into grams we need a volume for the katori, a density for the food, or a weighed piece. We have few of those, and the one source of Indian food composition we would prefer (IFCT 2017, ICMR-NIN) needs written permission for commercial use, which has not arrived (Q1). A wrong guess here is a wrong calorie count that looks exact, so the rule is to refuse rather than assume.

## Decision

- **Food data (Q1).** The `foods` table holds 141 USDA FoodData Central SR Legacy rows (public domain, CC0 1.0) and 21 Indian dishes built as documented recipes from those rows (`smartnutri_recipe`). Every dish lists its ingredients and grams, and its nutrients are calculated, never typed. IFCT rows are added only after NIN's written permission; the permission reference then goes in `licence`. The USDA licence is re-verified before launch. USDA credit shows on every surface that shows the data (search hits, the portion picker, diary entries, recipe ingredients, the How we score page).
- **Units (Q6, Q6b).** 17 unit codes. The default katori is **200 ml** (ICMR-NIN 2024 standard cup C7), with small, medium and large at 115, 155 and 360 ml. The "medium" katori (155 ml) is smaller than the default (200 ml), so the label always shows the ml beside the name. `cup` 200 ml, `glass` 250 ml, `tbsp` 15 ml, `tsp` 5 ml. The CSV's 150 ml `katori` row is superseded. `ladle`, `handful`, `bowl` and `plate` have no source and are not seeded.
- **`to_grams` refuses to guess (G11).** In order: a mass unit; `serving` with the food's `serving_g`; a portion row (the user's own value first, then ours); a volume unit with a density; a volume unit on an ml-basis food. Otherwise there is no result: the unit is not offered and a forced request is `422 unit_grams_unknown`. The API never assumes 1 ml = 1 g and never returns the quantity itself. The result is in the food's basis (grams, or ml). Limits: quantity at most 1000 (5000 for `g` and `ml`), and a result above 5000 is `422 quantity_out_of_range`.
- **Empty per-piece grams stay unknown (G5).** 12 CSV rows have no grams (phulka, home-made roti, paratha, idli, dosa, vada, puri, samosa, laddoo, papad, pakora, upma cup). They are listed under `unknown_piece_weights` and produce no portion row. The user may set their own value per food. A test proves that no seeded number exists for an empty CSV cell and that every seeded number equals its CSV cell.
- **Derived densities (G6).** 20 densities (FDC "1 cup" grams / 236.588 ml) go in `foods.density_g_per_ml` with `density_source = 'fdc_derived'`. Without them "1 katori dal" could never convert. Sunflower oil has none, so "1 tbsp sunflower oil" does not resolve.
- **Dishes (G7, G8).** A dish is seeded only when every ingredient is an FDC row and the doc gives a cooked yield in grams: 21 of 30. Poha and paneer bhurji are blocked (no FDC row). Roti, idli, dosa, paratha, puri, boiled egg and besan chilla need weighing: they switch on by themselves when a dietitian adds `cooked_weight_g`. A nutrient unknown on **any** ingredient is null in the dish (`foods.per_100` has no "incomplete" marker, so a partial sum is never stored looking complete). Saturated fat is null everywhere (the CSV has no such column). Salt comes from sodium (sodium x 2.5 / 1000).
- **Search (G2).** No `pg_trgm`: about 160 rows are matched with `ILIKE` over `search_text` (name plus aliases) and ranked in Python. Revisit at 5,000 rows (IFCT).
- **Seed outside migrations (G3).** Migration 0010 seeds only the 17 unit rows. Foods, dishes, densities and portions load through the idempotent job `python -m app.jobs.seed_foods` (upsert by `(source, source_code)`), so a food keeps its id across reseeds and an old diary entry keeps its `food_id` and its full `food_snapshot`.

## Consequences

- A wrong or missing household measure shows as "we don't know the grams", never as a confident number. The cost is that some foods only offer grams until a dietitian weighs them.
- A katori of a food with no density cannot be logged by volume; the user can set their own grams for that food.
- Dish nutrients are lower-trust than label values: the doc's recipes and yields are assumptions. The dishes carry `review_status = 'pending_dietitian_review'` and the picker says so.
- Adding IFCT later is a data change (new `source`, new seed rows), not a schema change.
