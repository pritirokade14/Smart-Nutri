# Cross-plan notes (to reconcile once Plans 2–8 are written)

Open items raised by the plan writers on 2026-11-03:
1. Fixture layout — contract says `packages/test-fixtures/expected/<product>.<member>.json`; Plan 2 Task 10 updates packages/test-fixtures/README.md to match. Plans 3–6 follow the contract.
2. Spec §5 drift — `POST /v1/analyze` also accepts `barcode` (OFF products have no product_id); `POST /v1/scans/label` takes an uploaded storage path (signed-URL upload) instead of multipart. Update the spec when Plan 3/4 land.
3. Spec §4 drift — `meal_logs` adds `account_id` (RLS) and `client_id` (offline idempotency); Plan 2 adds `rate_limit_counters` and `explanation_cache` tables.
4. Cross-plan names to verify: ORM classes (`ProductRecord`, `OffCacheRecord`, `MemberRecord`, `ScanRecord` — Plan 2 names win), `LLMProvider.chat_json`, `load_prompt` (Plan 4), `get_product`, `product_row_to_scoring`, `off_to_product` (Plan 3).
5. F7 AI explanation is implemented in Plan 5 (M3); Plan 7 (M5) must reuse it rather than re-implement.
6. New scoring reason/claim codes from the Plan 1 final fix wave need i18n keys (packages/i18n) and fixtures (packages/test-fixtures) in Plan 2 Task 8/10 and Plan 3 Task 6: allergen_unrecognised, condition_unrecognised, ingredients_missing, infant_caffeine, infant_sugar_high, infant_salt_high, child_salt_high, added_sugars; claim keys no_refined_sugar, diabetic_friendly; claim reasons refined_sugar_ingredient, no_standard; params "basis", "mark", "reason":"low_confidence".
7. Scoring contracts for Plan 2 consumers: Product/Member reject bare str for tuple fields; Status ordering only via Status.worst()/rank (StrEnum compares alphabetically); load_config() result is shared — treat as read-only (deep-freeze deferred); members API must require birth_year (age None skips child/infant rules — parked S7); restrict conditions to the canonical enum + aliases.

## 8. Shared-fixture coverage to add in Plan 3 (M1) — from the Plan 2 Task 10 safety review
Products: a label missing saturated fat and salt vs a diabetic (R25 → nutrient_missing); Hindi/Marathi ingredient labels; sodium-only label and a salt+sodium label (R22, higher wins); brown dot vs veg/Jain/eggetarian and green dot with gelatin; claim-heavy pack (No Added Sugar with jaggery/date paste, Low Fat, High Protein, Sugar Free with sweeteners); infant cereal with lactose + added sugar for age 0 (R32); sugars null vs diabetic; extraction_confidence 0.5 vs allergic and diabetic members; implausible values (sugars 250 g); a real OFF pack with attribution; products with veg_mark, allergen_statement and may_contain_statement ("Contains: wheat, milk. May contain: nuts").
Members: prediabetes, PCOS, eggetarian, egg/gluten/tree-nut allergies, child aged 4 (2–6 band), infant aged 0, diabetic + hypertensive elder, unrecognised condition.
A family fixture (several members in one analyze call) matching the M3 response shape.

## 9. Member birth year is required (Plan 5 member form, both clients)
Ruling R13 makes the engine return `age_unknown` UNKNOWN when age is missing and a child/infant rule would flag. Plan 5's member create/edit form on Android and web must require birth year (or an age band) so families don't see avoidable unknowns.

## 10. Account deletion must also clean Supabase Auth and Storage (Plan 8 / M6)
Also decide what `ensure_account` (GET /v1/me) does for a soft-deleted account (`deleted_at` set) that logs in again: 410 or reactivate. Today it returns it as live.
`accounts.id` has no FK to `auth.users` (Plan 2 Task 4). Deleting an account must delete the Supabase Auth user (admin API, server-side) and the account's Storage objects (`scans.image_path`), and deleting an auth user out-of-band must not leave health data orphaned — add an auth hook or a periodic sweep. Cascades inside `public` are already in the baseline (tested).

## 11. `meal_logs.product_id` is NOT NULL (FK to `products`); OFF data stays in `off_product_cache`
Plans 3 and 6: logging or explaining a product known only from Open Food Facts needs a `products` row. Create a minimal `products` row (barcode, name, source='off', no ODbL nutrient copy) that points to the cache, or make product_id nullable with an `off_barcode` column — decide in Plan 3 Task 1 and record an ADR. Do not copy ODbL data into `products` (AGENTS rule 8).

## 12. Plan 5 / Plan 6 must not recreate baseline tables
The Plan 2 baseline (`0001_baseline`) already creates members, consents and meal_logs with the final Plan 2 class names (`Member`, `Consent`, `MealLog`) and a stricter meal_logs policy (account_id AND member ownership). Plan 5 Task 3 and Plan 6 Task 2: consume these models, do not add MemberRow/ConsentRow/MealLogRow or a new migration for them; new columns go in a new revision. Keep their RLS tests as regression tests against the baseline. Writes from clients never go through the Supabase Data API (ADR 0013): `authenticated` has SELECT only.

## 13. Client verdict UI: collapse duplicate `nutrient_missing` lines (Plan 3)
The engine emits `nutrient_missing` once per (nutrient, rule). A member with diabetes and hypertension and no salt value gets two `nutrient_missing` reasons for salt. Both clients should show one line per missing nutrient. Also implement the `reason_variant.*` selection rules from `packages/i18n/README.md` and test them in each client.

## 14. Android release readiness (Plan 8 / M6, before any Play upload)
From the Plan 2 Task 11 review: the release build is still signed with the debug key (Flutter template). Add a signing config from `android/key.properties` (git-ignored, upload keystore), enable R8 minify/shrink with keep rules for Supabase/Sentry/retrofit, declare `<uses-feature android:name="android.hardware.camera" android:required="false"/>` (and microphone) so devices without them still see the app, and remove the template TODOs. Check Hindi/Marathi (Devanagari) rendering with the theme's text styles in Plan 3 UI work.

## 15. Production database role (Plan 8 / M6)
The API connects to dev as `postgres` (owner, BYPASSRLS). Before prod, create a dedicated role with BYPASSRLS and DML-only grants on app tables (no DDL, not owner), used by the API; migrations keep using the owner role. ADR 0013 follow-up.

## 16. `products.per_100g` JSONB keys = scoring `Nutrients` field names (Plan 3 Task 3)
`record_to_product` reads `products.per_100g` with the engine's `Nutrients` field names as keys (energy_kcal, protein_g, carbs_g, sugars_g, fat_g, sat_fat_g, fiber_g, salt_g, sodium_mg, fvl_percent). Plan 4 (label scan → confirmed product) must write exactly these keys. An own product with NULL `extraction_confidence` is treated as 1.0 when verified, 0.5 otherwise (below the 0.7 floor, so allergic members never get `ok`).

## 17. Public product page vs per-IP rate limit (Plan 3 Task 9 / Plan 8)
The web server renders `/[locale]/p/[barcode]` by calling `GET /v1/products/{barcode}/public`. All those calls come from the web service's egress IP, so they share one `public` bucket. M1 relies on Next's data cache (`revalidate: 3600`). If crawling causes 429s, add a server-to-server header key (Secret Manager, web server only) with its own larger bucket.
