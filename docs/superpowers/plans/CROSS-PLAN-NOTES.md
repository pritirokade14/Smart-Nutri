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
Products: Hindi/Marathi ingredient labels; sodium-only label and a salt+sodium label (R22, higher wins); brown dot vs veg/Jain/eggetarian and green dot with gelatin; claim-heavy pack (No Added Sugar with jaggery/date paste, Low Fat, High Protein, Sugar Free with sweeteners); infant cereal with lactose + added sugar for age 0 (R32); sugars null vs diabetic; extraction_confidence 0.5 vs allergic and diabetic members; implausible values (sugars 250 g); a real OFF pack with attribution; products with veg_mark, allergen_statement and may_contain_statement ("Contains: wheat, milk. May contain: nuts").
Members: prediabetes, PCOS, eggetarian, egg/gluten/tree-nut allergies, child aged 4 (2–6 band), infant aged 0, diabetic + hypertensive elder, unrecognised condition.
A family fixture (several members in one analyze call) matching the M3 response shape.

## 9. Member birth year is required (Plan 5 member form, both clients)
Ruling R13 makes the engine return `age_unknown` UNKNOWN when age is missing and a child/infant rule would flag. Plan 5's member create/edit form on Android and web must require birth year (or an age band) so families don't see avoidable unknowns.
