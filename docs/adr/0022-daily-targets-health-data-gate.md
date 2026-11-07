# ADR 0022: Daily targets are information computed by the API; `health_data` gates them

- **Status:** Accepted (Food Diary decision Q13, 2026-11-07). Legal review pending, as for ADR 0018.
- **Date:** 2026-11-07

## Context

The Food Diary adds a daily guide for each member: calories, protein, fat and carbs, computed from age, sex, height, weight, an optional body-fat percentage, activity and a goal. This is body data and, for the pregnancy answer, health data. It is also not a safety function: no verdict, allergen state or score reads it, and `analyze` responses are identical with and without it (`tests/api/targets/test_invariance.py`).

ADR 0018 ruled that withdrawing a consent stops processing and keeps what is stored, and ruling G1 kept verdicts running on stored allergies because ignoring them could show `ok` to an allergic member. Targets have no such reason to keep running after a withdrawal.

## Decision

Daily targets are **information the API computes**; the rules engine (`app/scoring/targets.py`) decides every number and clients only render them. `health_data` gates them.

- **Targets routes** (`GET /v1/targets`, `GET` and `PUT /v1/targets/settings`, `POST /v1/targets/preview`) need `terms` and `health_data` (`REQUIRED["targets"]`). They are gated per route, first, so a refused call costs no rate-limit quota.
- **Withdrawal stops the processing and keeps the stored settings** (ADR 0018 option 1). `GET /v1/targets` answers `403 consent_required` until the user consents again, and the settings are still there afterwards. Clients show an inline "allow health details" card, not a redirect loop.
- **Delete and display need only `terms`** (`REQUIRED["targets_prefs"]`). `DELETE /v1/targets/settings` is erasure and is never gated by `health_data`. `PUT /v1/targets/display` (the eye toggle) only reduces what is shown, so hiding numbers works even after a withdrawal and never revalidates stored settings.
- **Food logging stays on `terms`**, as ruled for meal logs (ADR 0017). The meals summary takes its protein target from the engine only while `health_data` is active, and otherwise uses the legacy rule; it hides numbers the user chose to hide either way.
- **Body fat** (`members.body_fat_pct`) is a member health field like height and weight: writing a value needs `health_data`, clearing it never does.
- **Erasure:** `DELETE /v1/me` removes `diary_goal_settings` before `members` (`ACCOUNT_OWNED_TABLES`).
- **Thresholds** stay in `app/scoring/data/targets.yaml`, marked PENDING CLINICIAN REVIEW, with one row per number on the clinician sheet.

## Consequences

- A user who withdraws `health_data` loses the daily guide until they consent again, but not their food log or their saved settings.
- Targets and the weight log (a later slice) share the `targets` consent mapping, so the clients' existing `consent_required` handling needs one inline exception: the Home card must show a grant button rather than redirecting.
- The lawyer's question from ADR 0018 (DPDP) applies here too: confirm that keeping stored settings after a withdrawal, without processing them, is acceptable.

## Addendum (2026-11-08): delete all weigh-ins

`DELETE /v1/weights` (`weights_delete_all`) erases every weigh-in of the self member and returns `{deleted: n}`. Like `DELETE /v1/targets/settings` and the single `DELETE /v1/weights/{day}`, it needs only `terms` (`REQUIRED["weights_erase"]`): erasure is never gated by `health_data`. It does not rewrite `members.weight_kg` (the profile keeps its last known weight), recomputes today's targets only while `health_data` is active, follows `DIARY_FAMILY_ENABLED`, and has its own bucket (`rate_limit_weights_erase_per_day`, 10 a day; single delete stays unlimited).
