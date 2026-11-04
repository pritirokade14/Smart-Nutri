# ADR 0017: Meal logs for Open Food Facts products

- **Status:** Accepted (nutrition-safety ruling M1, 2026-11-04). ODbL reading and the consent basis are pending lawyer review (see Consequences).
- **Date:** 2026-11-03

Resolves CROSS-PLAN-NOTES item 11 (Plan 6, M4).

## Context

`meal_logs.product_id` was `NOT NULL` with a foreign key to `products`. Most barcode scans resolve to Open Food Facts (OFF), and OFF data must stay in `off_product_cache`, apart from `products` (ODbL, AGENTS rule 8). Without a decision, a user could not log "I ate this" for most scanned packs.

Two options were on the table: create a minimal `products` row for each OFF product, or let a meal log reference an OFF barcode directly.

## Decision

A meal log references **exactly one** of our own product (`product_id`) or an OFF barcode (`off_barcode`), enforced by `ck_meal_logs_product_ref` (`num_nonnulls(product_id, off_barcode) = 1`). Migration `0003_plan6_meal_logs_off` makes `product_id` nullable and adds `off_barcode`, plus two snapshots, `product_name` and `grade`.

- We create no `products` rows for OFF products. `products` stays our own catalogue (label scans and user entries). Its `source` check (`label`, `user`) is unchanged.
- At log time the API resolves the product the same way `POST /v1/analyze` does (own catalogue, then the OFF cache, then OFF). It stores the nutrient snapshot (`per_100g × grams / 100`), the name and the Nutri-Score grade that the engine calculated. History never depends on a cache entry that may expire.
- The API returns `attribution: "attribution.off"` on logs of OFF products. Clients credit OFF **wherever** they show an OFF name or grade from a meal log: the log list, the day and week summaries, history and any share or export (AGENTS rule 8).
- `POST /v1/meals` takes `product_id` **or** `barcode` (the `AnalyzeRequest` pattern), with `invalid_product_ref` (422) when both or neither are sent.

## Consequences

- A meal log stores the name, grade and portion nutrients of one OFF product, scaled to what the user ate. It does not store the OFF record. We judge this an insubstantial extract and a produced work. Still, a person must review this ODbL reading before public launch.
- Downgrading past 0003 deletes OFF-only logs, because they cannot satisfy `NOT NULL product_id`.
- Alternatives and compare also accept a barcode, so OFF products work end to end. See the Plan 6 report.

## Consent basis for meal logs (ruling M1 S4)

Meal logs follow ruling G1 (ADR 0018): the `/v1/meals` routes need only the `terms` consent, not `health_data`.

- A meal log is personal data about one family member: what they ate, when, and how much. It is not a health field (allergens, conditions, goal, height, weight), and logging it does not need `health_data` consent.
- It is protected by the `terms` consent and by account scoping: every query is scoped by `account_id`, RLS is enabled and forced on `meal_logs`, and another account's member returns 404.
- Summaries compare the logs with daily limits chosen by the member's age, and protein targets with their weight. Those inputs are already stored under the members `health_data` check, so a summary reads them but never writes them.
- **Revisit with the lawyer (DPDP Act 2023).** A per-member food diary could be read as health-related personal data. The lawyer reviewing the privacy policy must confirm that `terms` plus account scoping is enough, or tell us to gate meal logging on `health_data`. If the gate changes, it is one line in `app/core/consent.py` (`REQUIRED["meals"]`).
