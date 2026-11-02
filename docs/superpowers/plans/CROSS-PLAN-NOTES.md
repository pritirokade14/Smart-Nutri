# Cross-plan notes (to reconcile once Plans 2–8 are written)

Open items raised by the plan writers on 2026-11-03:
1. Fixture layout — contract says `packages/test-fixtures/expected/<product>.<member>.json`; Plan 2 Task 10 updates packages/test-fixtures/README.md to match. Plans 3–6 follow the contract.
2. Spec §5 drift — `POST /v1/analyze` also accepts `barcode` (OFF products have no product_id); `POST /v1/scans/label` takes an uploaded storage path (signed-URL upload) instead of multipart. Update the spec when Plan 3/4 land.
3. Spec §4 drift — `meal_logs` adds `account_id` (RLS) and `client_id` (offline idempotency); Plan 2 adds `rate_limit_counters` and `explanation_cache` tables.
4. Cross-plan names to verify: ORM classes (`ProductRecord`, `OffCacheRecord`, `MemberRecord`, `ScanRecord` — Plan 2 names win), `LLMProvider.chat_json`, `load_prompt` (Plan 4), `get_product`, `product_row_to_scoring`, `off_to_product` (Plan 3).
5. F7 AI explanation is implemented in Plan 5 (M3); Plan 7 (M5) must reuse it rather than re-implement.
6. New scoring reason/claim codes from the Plan 1 final fix wave need i18n keys (packages/i18n) and fixtures (packages/test-fixtures) in Plan 2 Task 8/10 and Plan 3 Task 6: allergen_unrecognised, condition_unrecognised, ingredients_missing, infant_caffeine, infant_sugar_high, infant_salt_high, child_salt_high, added_sugars; claim keys no_refined_sugar, diabetic_friendly; claim reasons refined_sugar_ingredient, no_standard; params "basis", "mark", "reason":"low_confidence".
7. Scoring contracts for Plan 2 consumers: Product/Member reject bare str for tuple fields; Status ordering only via Status.worst()/rank (StrEnum compares alphabetically); load_config() result is shared — treat as read-only (deep-freeze deferred); members API must require birth_year (age None skips child/infant rules — parked S7); restrict conditions to the canonical enum + aliases.
