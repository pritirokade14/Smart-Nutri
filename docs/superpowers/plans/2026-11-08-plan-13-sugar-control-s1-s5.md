# Plan 13: Sugar Control Slices S1–S5: Glucose Log, Day Timeline with Meals and Carbs, Patterns, Lab Log, Doctor Report

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The account holder logs their own glucose readings (mg/dL or mmol/L) and lab results beside the food they already log, sees one merged day timeline with carbs per meal, reads simple descriptive patterns against a range only they set, and downloads a doctor report (PDF in en, hi or mr, plus CSV), on Android and web, as a logbook that never advises, alarms or estimates.

**Architecture:**
- **API first, one slice at a time.** Three migrations chain from the live head `0013_diary_weight_logs`: `0014` (sugar settings and readings), `0015` (carb guides), `0016` (lab results). S3 and S5 add no table.
- New feature folders: `app/features/sugar/` (settings, member resolution, day timeline, summary, report), `app/features/glucose/` (readings), `app/features/labs/` (lab log). One new pure module, `app/scoring/glucose.py`, reads a new `app/scoring/data/glucose.yaml`. Verdict code never imports either.
- The timeline is built on the diary's own `diary.service.get_day`, so carbs per meal and the unknown rule are identical to the Diary. Nothing in the diary is duplicated.
- **Per slice:** shared golden fixtures (unit conversions, link windows, statistics, lab conversions, report snapshot), i18n, `just contract`, then **Android ∥ web**, then the `nutrition-safety-reviewer` gate.
- No LLM call, no analytics event, no stored report. All numbers come from the API; clients render.

**Tech Stack:** as Plan 12. API: Python 3.13, FastAPI, SQLAlchemy 2 async + Alembic, pytest + Hypothesis, `decimal`, `statistics`, `zoneinfo`; S5 adds WeasyPrint (fallback fpdf2 + uharfbuzz), `pypdf` and `fontTools` (dev), and the Noto Sans and Noto Sans Devanagari fonts (OFL). Android: Flutter, Riverpod 3, go_router, drift (offline queue), the generated `smartnutri_api`, `share_plus` (already used by share). Web: Next.js 16, TanStack Query, next-intl, `@smartnutri/api-client`. Tests: pytest, flutter_test, Vitest, Playwright.

**Spec:** `docs/research/sugar-control/FEATURE_SPEC.md` (binding; decisions Q1–Q18 in `DECISIONS.md` applied).
- Slices S1–S5 are rows S1–S5 of spec §15. Sections implemented: 1.4, 4, 5.1, 5.2, 5.4, 6.1, 6.2, 7, 8, 11, 12 (S1–S5 parts), 13 (S1–S5 screens), 14 (S1–S5 tests).
- **Not in this plan:** S6 "meals and your readings" (`SUGAR_INSIGHTS_ENABLED`), S7 GI and GL (`glycaemic_reference`, the `foods_get` extension), S8 reminders. Nothing here adds a field, key or toggle for them.
- `docs/research/sugar-control/SHORTLIST.md` "Regulatory: do NOT build" is binding (restated in Global Constraints).
- Current interfaces: Plans 10–12 and `.superpowers/sdd/plan-12-food-diary-s3-6/api-report-s*.md`. **Existing names and shapes win** over the spec; each case is a ruling below.

## Rulings made while writing this plan

**Migrations, tables, docs**
- **H1 (migrations):** `0014_sugar_settings_glucose` (`down_revision = "0013_diary_weight_logs"`), `0015_sugar_carb_guides`, `0016_sugar_lab_results`. The reading's meal-link columns (`linked_local_date`, `linked_meal_slot_id`, `link_source`) are created in **0014** with their checks, so S2 needs no `ALTER`; the S1 API never writes them (tested). Every new table gets the 0013 `_lock_down` (owner-read for `authenticated`, writes by the service role, `ENABLE` + `FORCE ROW LEVEL SECURITY`) and a `tests/db` RLS case.
- **H2 (foreign keys):** member-owned tables use the composite FK `(member_id, account_id) → members(id, account_id) ON DELETE CASCADE`. The slot FKs `(linked_meal_slot_id, member_id)` and `carb_guides (meal_slot_id, member_id) → meal_slots(id, member_id)` have **no ON DELETE action** (NO ACTION), like `meal_logs → meal_slots` (Plan 11 E3): slots are archived, never hard-deleted except with their member, and a spec-style `SET NULL (column)` would break the `num_nonnulls(...) in (0, 2)` check. Supabase runs Postgres 17 (`supabase/config.toml`), so the spec's PG15 question is moot.
- **H3 (erasure order):** `ACCOUNT_OWNED_TABLES` gains `lab_results`, `glucose_readings`, `carb_guides`, `sugar_settings`, inserted right after `weight_logs` (before `favourites`, `meal_logs` and `meal_slots`, because the slot FKs are NO ACTION). `test_delete_me.py` covers each.
- **H4 (numbers taken):** ADR 0023 already exists (diary days), so the spec's "ADR 0023" becomes **ADR 0026** "Sugar Control is information-only logging", and the PDF engine choice is **ADR 0027**. FEATURE_PARITY F22 is taken: Sugar Control gets rows **F27** (glucose log), **F28** (day timeline and carbs), **F29** (patterns), **F30** (labs), **F31** (doctor report).
- **H5 (YAML home):** `app/scoring/data/glucose.yaml`, loaded into a new `ScoringConfig.glucose` field (default factory, like `targets`). Header: `# PENDING CLINICIAN REVIEW. Read only by app/scoring/glucose.py. Never read by verdict rules.` Every number gets a `section_sources` entry in `thresholds.yaml` and a row in the clinician sheet (`scripts/clinician_review_sheet.py` → `docs/launch/clinician-review.md`).

**Units and maths**
- **H6 (conversion factor, verified):** `units.mgdl_per_mmoll: 18.016`. Verified 2026-11-08 against PubChem CID 5793 (D-glucose, C6H12O6, molecular weight 180.16 g/mol): 1 mmol/L = 180.16 mg/L = 18.016 mg/dL. Still `PENDING CLINICIAN REVIEW` because some Indian labs print a factor of 18 [unverified which]. The YAML comment cites the PubChem URL.
- **H7 (lab factors):** HbA1c uses the NGSP master equation, verified 2026-11-08 at ngsp.org/ifccngsp.asp: `NGSP % = 0.09148 × IFCC (mmol/mol) + 2.152`, and its exact algebraic inverse `IFCC = (NGSP − 2.152) / 0.09148`. The spec's rounded `2.15` and `10.929` are replaced, so a round trip is exact. Cholesterol (total, LDL, HDL) `38.67`, verified (PubChem CID 5997, 386.7 g/mol). Triglycerides `88.57` is marked `[unverified: the conventional lab factor; PubChem triolein CID 5497163, 885.4 g/mol, gives 88.54]`.
- **H8 (unit codes):** wire codes are identifiers: `mg_dl`, `mmol_l` (glucose and lipids), `pct`, `mmol_mol` (HbA1c). The spec's `%` is `pct`. The unit is required on every write and never inferred from magnitude.
- **H9 (precision and rounding):** everything is `Decimal`, `ROUND_HALF_UP`.
  - Glucose: mg/dL input in whole numbers, mmol/L to 1 dp, else `422 glucose_precision`. Stored `value_mgdl = round(entered × 18.016, 1)`.
  - Display: in the entered unit, the entered value exactly; mmol/L → mg/dL as `round(value_mgdl, 0)`; mg/dL → mmol/L as `round(value_mgdl / 18.016, 1)`.
  - Statistics run on unrounded `value_mgdl` and are rounded only for display. An SD in mmol/L is `round(sd_mgdl / 18.016, 1)`.
  - Labs: HbA1c `pct` 1 dp, `mmol_mol` whole; lipids `mg_dl` whole, `mmol_l` 2 dp; lab glucose as readings. Finer input is `422 lab_precision` (new code).
- **H10 (back-entry, Q15):** measured on **local dates** in the account zone: `today − local_date(measured_at) ≤ 90` is accepted, 91 is `measured_at_too_old`. Future: more than 300 s ahead of now is `measured_at_in_future`; up to 300 s is stored as sent.
- **H11 (SD: the brief overrides spec §5.4):** spec §5.4 says "no SD"; the 2026-11-08 brief asks for "mean and SD". The summary returns the **sample standard deviation** (n − 1; null when n < 2) as a plain descriptive number labelled "Spread (standard deviation)", beside the mean. There is still no coefficient of variation, variability index, score, band, estimate or forecast, and no copy interprets the SD. Flagged to the user and to the safety reviewer (Task 22).
- **H12 ("time in range" wording):** the brief's "time-in-range" is the spec's within-range share: the field is `within_range`, the copy is "of your readings were within the range you set". The words "time in range" never appear (a CGM measure); a copy test bans them. It is returned only when the user has set a range **and** the period has at least 10 readings.
- **H13 (quartiles):** `statistics.quantiles(values, n=4, method="inclusive")` (Hyndman and Fan type 7) for n ≥ 2; n = 1 gives q1 = median = q3 = the value. The within-range percentages are whole numbers that sum to 100 by the largest-remainder method (ties go to within, then below, then above).

**API**
- **H14 (consent keys):** `REQUIRED["sugar"] = ("terms", "health_data")` (every read, write and restore); `REQUIRED["sugar_prefs"] = ("terms",)` (`sugar_unit_put`, and the CSV report); `REQUIRED["sugar_erase"] = ("terms",)` (`glucose_delete`, `labs_delete`, `sugar_settings_delete`), mirroring `weights_erase`. Gated **per route** (not `CONSENT_GATES`), gate before `limit()`. `sugar_report_create` uses a dependency that reads the body's `format` (FastAPI shares the body), so a refused PDF costs no quota (Q13).
- **H15 (member resolution):** `sugar.members.sugar_member()` wraps `targets_service.resolve_member` semantics with its own flag `SUGAR_FAMILY_ENABLED` (setting `sugar_family_enabled = False`) and error `422 sugar_member_not_enabled`. It also adopts the spec §12.6 proposal: a primary member whose `youngest_age` (Ruling D2) is under `minors.min_age` (18) gets `422 sugar_not_available_minor` on every `sugar`-gated route; an unknown age is allowed. Erasure, `sugar_unit_put` and the CSV stay available.
- **H16 (consent text):** `CURRENT_VERSIONS["health_data"]` becomes `"2026-11-08"`, and `consent.health_data.body` names glucose readings and lab results (and weigh-ins, which the current text omits). Existing users re-grant at first use through the existing `consent_required` / stale-version flow (spec §12.5, R15). A lawyer item is added to CONTEXT.md.
- **H17 (scrubbing):** `scrub_event` already drops every request body, query string, local variable and exception message, so no field list is added. Task 5 adds a regression test that a glucose create body and a report request never reach a scrubbed event. Logs carry counts and codes only (tested by log capture).
- **H18 (delete and restore):** delete is idempotent (a second delete returns the first `deleted_at`). `restore_until = deleted_at + 30 days`; restore works while `now ≤ restore_until`, else `410 glucose_restore_expired` (`lab_restore_expired`). Restoring a live row returns it unchanged. Get and patch on a deleted row are `404`. The retention job hard-deletes rows with `deleted_at < now − 30 days` (Q16).
- **H19 (meal link, S2):**
  - `link` omitted means auto-suggest for `before_meal` and `after_meal` (`link_source = 'auto'`); `null` means no link; an object is a user link (`'user'`).
  - The linked date must be the reading's local date or the day before or after (`422 glucose_link_not_allowed`, `details.reason = "date"`). `fasting`, `bedtime` and `random` cannot be linked (`reason = "context"`).
  - On PATCH, an `auto` link is recomputed when `measured_at` or `context` changes and `link` is not sent; a `user` link is kept, unless the new context cannot be linked, which clears it.
  - A link target slot must be the member's (`meal_slot_not_found`, as `meals_log` returns it); an archived slot with no entries that day is `422 meal_slot_archived`. A meal with no entries yet may be linked (`meal_has_items: false`).
  - `GET /v1/glucose/link-suggestion` returns a wrapper `{link: {…} | null}` (generators handle an object better than a bare null).
- **H20 (timeline):** meal items are built from `diary.service.get_day` (the same slots, `MealOut` entries, totals and `incomplete`). Items are sorted by time (a meal at its first entry's `eaten_at`, a reading at `measured_at`); ties put the meal first, then by id. Under `hide_all`, carbs are null (`numbers_hidden` echoed); glucose and lab values are never hidden (spec §6.1).
- **H21 (carb guide, Q6):** `PUT /v1/sugar/settings` keeps the spec body; `carb_guide` absent means unchanged (so S1 clients keep working). Disabling the guide **deletes** its rows, so nothing lingers to pre-fill (Q6). "Same for all" writes one row per active slot; a slot created later has no guide.
- **H22 (input hints and reference values from the API):** `SugarSettingsOut` carries `input_hints` (per unit: hard and confirm bounds, step) and the general-reference values (Q4 card) from YAML, so clients never hard-code a number. `packages/test-fixtures/sugar/units.json` pins the same numbers on all three platforms.
- **H23 (report):**
  - The feature name `reports` is taken (product problem reports), so the doctor report lives in `app/features/sugar/report/`, `operation_id = sugar_report_create`.
  - The PDF is rendered in a thread (`run_in_threadpool`). The response has `Content-Disposition: attachment; filename="smartnutri-glucose-<from>-<to>.<ext>"` (no name in the filename) and `Cache-Control: no-store`.
  - `include_meal_readings` is **not** added (S6 adds it).
  - The CSV never contains the member's name; `include_name` applies to the PDF header only. CSV headers and enum values are codes; slot names are translated per `language` (custom labels as typed).
  - Under `hide_all`, carbs are left out of the report and the report says so (`sugar.report.carbs_hidden`).
- **H24 (PDF engine):** WeasyPrint (BSD; Pango and HarfBuzz shape Devanagari) is primary. Task 29 decides by fixed criteria and records ADR 0027; the fallback is fpdf2 with `set_text_shaping` through uharfbuzz [verify in Task 29], which needs no system libraries. All three languages ship either way (Q9).

**Clients**
- **H25 (modes, Q18):** `layouts.json` gains the destination `sugar`. The `health_condition` mode (which serves the Sugar Control chip until the separate chip rename) gets tabs `home, scan, diary, sugar, profile`; Family moves to More. Sugar appears in More in every other mode (the reachability rule). The spec's Heart-Health split waits for the chip rename. S2 adds the Home cards `sugar_latest` and `meal_carbs` before the existing `health_condition` cards (`not_covered` stays: existing names win). Both client tasks of a slice apply the **identical** JSON diff given here (identical hunks merge cleanly); the Android task also updates `apps/api/tests/fixtures/test_mode_layouts.py`.
- **H26 (feature folders):** Android `lib/features/sugar/` (tab, timeline, patterns, report, settings, intro), `lib/features/glucose/` (reading sheet, repository, sync), `lib/features/labs/`. Web `src/features/{sugar,glucose,labs}/`, routes `/[locale]/sugar`, `/sugar/patterns`, `/sugar/labs`, `/sugar/report`, `/sugar/settings`, `/sugar/deleted`.
- **H27 (Android queue):** drift schema v7 adds `PendingGlucose` (with nullable link columns `linkChoice` `auto|none|user`, `linkDate`, `linkSlotId`, used from S2); v8 adds `PendingLabs`. A queued item that syncs into `consent_required` stays queued (never dropped) and the consent card shows. Edit, delete, restore and reports are online-only.
- **H28 (intro, spec §11):** the Sugar tab shows a three-step intro while `SugarSettingsOut.configured` is false. Step 2 saves the unit with `sugar_unit_put` (terms only, creates the row), the optional range with `sugar_settings_put` (health_data; the consent dialog opens if needed), and the optional condition through the existing member PATCH (health_data). "Just look around" saves the default unit.
- **H29 (copy):** the spec's "SmartNutri does not diagnose or treat" trips the repo's `BANNED` regex (`diagnos\w*`, `treat`). `sugar.disclaimer` is "Information, not medical advice. Values are as you entered them." and the report subtitle and footer follow the same rule. No `sugar.chip` key is added (the chip rename is separate).
- **H30 (order):** slice APIs run in order S1 → S5 (migrations chain and every slice regenerates the contract). The pure engine tasks 12, 18 and 24 may start any time after Task 2. A slice's client tasks may run while the next slice's API tasks run (disjoint files).

## Global Constraints

Health-app rules (root `AGENTS.md`, non-negotiable):
1. **The rules engine decides; Sugar Control is information.** Clients never convert a unit, compute a statistic, a range position, a link, a carb total or a lab conversion. `analyze` is byte-identical with and without Sugar Control data (tested in S1, S2 and S4). `app/scoring/verdict.py`, `conditions.py` and the analyze service never import `glucose`.
2. **Never invent data.** A missing carb value keeps the meal total incomplete ("at least"). No default range (Q4), no default carb guide (Q6), no estimated value of any kind.
3. **Unknown is not safe.** Range notes, insufficient windows and incomplete carbs use neutral or grey tokens, never verdict colours or the danger token.
4. **Numbers live in YAML**, marked `PENDING CLINICIAN REVIEW`, with `section_sources` entries and clinician-sheet rows (H5).
5. **Secrets stay server-side.** No new public config.
6. **No analytics events (Q17).** No event or property name contains `glucose`, `lab`, `sugar`, `reminder` or `a1c` on any platform; the three `ALLOWED_EVENTS` lists are unchanged. Notes are never logged, translated or sent to any model.
7. **No medical claims.** "Information, not medical advice" on every Sugar Control screen with numbers, plus "pending clinician review" where a YAML number applies. Copy passes `test_sugar_copy.py` (H29).
8. **Strings only in `packages/i18n`** (en, hi, mr). hi and mr machine drafts go in `NATIVE_REVIEW.md` under "Plan 13 slice SN". Marathi plurals print the number with `{count}` inside the plural, never `#`. User text (notes, custom slot labels) never passes through i18n.
9. **Never hand-edit generated code.** `just` is not installed for agents: run the justfile recipe lines by hand (`.superpowers/sdd/RULES-FOR-AGENTS.md`).
10. **Feature parity.** A slice is done only when API, Android and web ship it and its shared fixtures pass on all three.

**DO-NOT-BUILD (SHORTLIST.md, binding):** no insulin or medicine dose calculation, correction factor, carb ratio, bolus, insulin or carbs on board, or any insulin or medicine field; no dose or timing advice; no diagnosis or risk scoring and no "you may have"; no treatment targets, hypo or hyper alarms, push alerts on readings, or colour-coded danger states; no CGM, pump or closed-loop automation and no accuracy claims; no model output changing a number (Sugar Control makes no LLM call); no "treats, manages or cures" copy; **HbA1c is logged as entered and never estimated** (no eA1c, no GMI, no average-to-A1c formula). Also no glucose prediction or forecast and no variability score (spec §1.4).

Slice rules:
- **Solo only:** every route resolves the member through `sugar_member` (H15).
- **Rate limits** (`BUCKETS` + `Settings`): `glucose_writes` (day, 200: create, patch, restore), `sugar_settings` (day, 30), `lab_writes` (day, 50), `sugar_reports` (day, 20).
- **Decimals:** API arithmetic in `Decimal`, half-up for display only.
- **Errors:** `ErrorEnvelope`, each new code with `error.<code>` in en, hi and mr, added by the task that first raises it, and mapped in the Android `apps/app/lib/core/network/api_client.dart` error map (its test requires every `error.*` key).
- **Android:** run `dart format --set-exit-if-changed lib test` before `flutter analyze && flutter test` (CI fails on unformatted Dart).
- **Commits:** Conventional Commits with a scope, ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Run `gitleaks protect --staged --no-banner` **as its own command, with no pipe** (a pipe such as `| tail` hides its exit code), and commit only if it exits 0. Never push.

## Review Focus

1. **A unit mix-up stored as a plausible number.** Examples: 6.1 typed with mg/dL selected; 110 typed with mmol/L selected; a request with no unit; a range typed in mmol/L and then the display switched to mg/dL. Expected: the first two are `glucose_out_of_range` in the typed unit; no unit is `validation_error`, never a guess; the range survives the switch unchanged. Owned by:
   - Task 2: fixture rows `mmol_value_with_mgdl_unit`, `mgdl_value_with_mmol_unit`; `test_never_infers_unit` (Hypothesis);
   - Task 3: `test_range_survives_unit_switch`;
   - Task 4: `test_unit_required_never_inferred`;
   - Tasks 6 and 7: `unusual confirm shows both units`.
2. **Time-zone and midnight errors.** A reading at 23:59 local; the account zone changed afterwards; back-entry at exactly 90 days in a non-IST zone; an after-meal reading at 00:30 after a 22:00 dinner. Expected: local date and window frozen at write; 90 local days accepted, 91 refused; the reading links to the previous day's dinner. Owned by:
   - Task 4: `test_local_date_frozen_on_timezone_change`, `test_back_entry_90_days_account_zone`;
   - Task 12: fixture `after_midnight_previous_dinner`;
   - Task 18: fixtures `window_edges`, `frozen_minutes_dst_zone`.
3. **A deleted reading or lab leaking.** A soft-deleted row showing in the day timeline, the summary, the duplicate check, a meal's `readings_linked`, the CSV or the PDF, or restorable after the purge. Expected: gone from every surface at once; `410` after 30 days; purged by the retention job. Owned by:
   - Task 4: `test_deleted_hidden_from_list_and_duplicate_check`;
   - Task 5: `test_retention_purges_only_expired_readings`;
   - Task 14: `test_deleted_reading_not_in_day_or_links`;
   - Task 19: `test_summary_ignores_deleted`;
   - Task 25: `test_deleted_lab_hidden_and_purged`;
   - Task 30: `test_report_excludes_deleted`.
4. **Advice or alarm creep.** A very-low note appearing with the flag off or the YAML value null; a range label with no range set; a red or verdict colour on a reading, window or "over guide" line; SD or within-range copy that judges; an "estimated A1c" anywhere. Expected: none of these, on any platform. Owned by:
   - Task 2: `test_very_low_note_gated_twice`, `test_no_high_note_exists`;
   - Task 5: `test_sugar_copy.py`;
   - Task 19: `test_no_range_no_within_share`;
   - Task 24: `test_no_estimate_anywhere`;
   - Tasks 6, 7, 15, 16, 20, 21: `no verdict or danger token in sugar features`.
5. **Consent withdrawn mid-use.** `health_data` withdrawn while readings are queued on the phone, or while the report screen is open. Expected: screens show the consent card; stored rows stay; delete still works; the queued reading stays queued (never dropped, never uploaded without consent); the CSV still downloads; the PDF is `403`. Owned by:
   - Task 4: `test_routes_need_health_data_except_erase`;
   - Task 6: `queued reading kept on consent_required`;
   - Task 31: `test_csv_on_terms_after_withdrawal`, `test_pdf_refused_after_withdrawal_no_quota_used`;
   - Tasks 32 and 33: `only CSV offered after withdrawal`.

## Task overview: platform, order, parallelism

| Task | Platform | Depends on | Parallel group |
|---|---|---|---|
| **Slice S1: glucose log core** | | | |
| 1. Migration 0014, models, RLS, erasure, ADR 0026 | API (db) | — | **A**: 1 ∥ 2 |
| 2. `glucose.py` units, limits, range position, low note; `glucose.yaml`; unit fixture | API (engine) | — | **A**: 1 ∥ 2 |
| 3. Sugar member, consent keys, flags, buckets, settings routes | API | 1, 2 | — |
| 4. Glucose routes: create, list, get, patch, delete, restore, deleted list | API | 3 | — |
| 5. Retention, invariance, analytics and copy guards, i18n, tokens, consent bump, contract | API + shared | 4 | — |
| 6. Sugar tab, day list, reading sheet, undo, queue v7, modes | Android | 5 | **B**: 6 ∥ 7 |
| 7. Sugar tab, day list, reading sheet, undo, modes, e2e | Web | 5 | **B**: 6 ∥ 7 |
| 8. Sugar settings, recently deleted, intro | Android | 6 | **C**: 8 ∥ 9 |
| 9. Sugar settings, recently deleted, intro, e2e | Web | 7 | **C**: 8 ∥ 9 |
| 10. Slice-S1 gate | All | 1–9 | — |
| **Slice S2: timeline, meal link, carbs, carb guide** | | | |
| 11. Migration 0015 `carb_guides` | API (db) | 10 | **D**: 11 ∥ 12 |
| 12. Pure `link_candidate`, link fixture | API (engine) | 2 | **D**: 11 ∥ 12 (may start after 2) |
| 13. Links on create and patch, link-suggestion route | API | 11, 12 | — |
| 14. Carb guide in settings, `sugar_day_get`, i18n, contract | API + shared | 13 | — |
| 15. Day timeline, link control, meal carbs, guide, Home cards | Android | 14 | **E**: 15 ∥ 16 |
| 16. Day timeline, link control, meal carbs, guide, Home cards, e2e | Web | 14 | **E**: 15 ∥ 16 |
| 17. Slice-S2 gate | All | 11–16 | — |
| **Slice S3: patterns** | | | |
| 18. Pure statistics, stats fixtures | API (engine) | 2 | may start after 2 |
| 19. `sugar_summary_get`, i18n, contract | API + shared | 17, 18 | — |
| 20. Patterns screen | Android | 19 | **F**: 20 ∥ 21 |
| 21. Patterns screen, e2e | Web | 19 | **F**: 20 ∥ 21 |
| 22. Slice-S3 gate | All | 18–21 | — |
| **Slice S4: lab log** | | | |
| 23. Migration 0016 `lab_results` | API (db) | 22 | **G**: 23 ∥ 24 |
| 24. Pure lab conversions, lab fixture, no-estimate test | API (engine) | 2 | **G**: 23 ∥ 24 (may start after 2) |
| 25. Labs routes, trend, retention, summary labs, i18n, contract | API + shared | 23, 24 | — |
| 26. Labs list, form, trend, queue v8 | Android | 25 | **H**: 26 ∥ 27 |
| 27. Labs list, form, trend, e2e | Web | 25 | **H**: 26 ∥ 27 |
| 28. Slice-S4 gate | All | 23–27 | — |
| **Slice S5: doctor report** | | | |
| 29. PDF engine decision, fonts, image, ADR 0027 | API | 28 | **I**: 29 ∥ 30 |
| 30. Report data, CSV writer, CSV goldens | API | 28 | **I**: 29 ∥ 30 |
| 31. PDF renderer, `sugar_report_create`, snapshots, i18n, contract | API + shared | 29, 30 | — |
| 32. Report screen, share | Android | 31 | **J**: 32 ∥ 33 |
| 33. Report screen, download, e2e | Web | 31 | **J**: 32 ∥ 33 |
| 34. Slice-S5 gate and final docs | All | 29–33 | — |

Agents: API tasks `api-builder` (sonnet), using `api-endpoint`; tasks 2, 12, 18 and 24 also use `scoring-rule`. Android tasks `flutter-builder` (`flutter-feature`). Web tasks `web-builder` (`web-feature`). Gates: `nutrition-safety-reviewer` (opus); every slice touches health data, so every slice is reviewed.

Parallel pairs and their files:
- **1 ∥ 2:** Task 1 owns the migration, `glucose/models.py`, `sugar/models.py`, `me/service.py`, `tests/db`, ADR 0026. Task 2 owns `scoring/{glucose,config}.py`, `glucose.yaml`, `thresholds.yaml` (`section_sources`), the clinician sheet, `packages/test-fixtures/sugar/units.json`.
- **11 ∥ 12, 23 ∥ 24:** the migration task owns its migration, models and `tests/db`; the engine task owns `glucose.py`, `glucose.yaml` and its fixture folder. Tasks 12, 18 and 24 each append a disjoint YAML section (`link`, `pattern`/`within_range`/`summary`, `labs`); merge carefully if two run at once.
- **29 ∥ 30:** Task 29 owns `sugar/report/pdf_engine.py`, `sugar/report/fonts/`, the Dockerfile, `pyproject.toml`, ADR 0027. Task 30 owns `sugar/report/{data,csv_writer}.py` and `packages/test-fixtures/sugar/report/`.
- **Client pairs:** Android and web files are disjoint, except the identical `layouts.json` hunk (H25).

## File Map

```
apps/api/
  alembic/versions/0014_sugar_settings_glucose.py                          # T1
  alembic/versions/0015_sugar_carb_guides.py                               # T11
  alembic/versions/0016_sugar_lab_results.py                               # T23
  app/scoring/glucose.py, app/scoring/config.py (glucose field)            # T2, T12, T18, T24
  app/scoring/data/glucose.yaml, data/thresholds.yaml (section_sources)    # T2, T12, T18, T24
  app/features/sugar/{__init__,models,members,schemas,service,router}.py   # T1 (models), T3, T14, T19
  app/features/sugar/{timeline,summary}.py                                 # T14, T19
  app/features/sugar/report/{__init__,data,csv_writer,pdf,pdf_engine,router}.py, templates/, fonts/   # T29–T31
  app/features/glucose/{__init__,models,schemas,service,links,router}.py   # T1 (models), T4, T13
  app/features/labs/{__init__,models,schemas,service,router}.py            # T23 (models), T25
  app/core/{consent,config,ratelimit}.py, app/main.py                      # T3, T4, T25, T31
  app/features/consents/policy.py                                          # T5
  app/features/me/service.py (ACCOUNT_OWNED_TABLES)                        # T1, T11, T23
  app/jobs/retention.py                                                    # T5, T25
  Dockerfile, pyproject.toml                                               # T29
  scripts/{generate_sugar_unit_expectations,generate_sugar_link_expectations,generate_sugar_stats_expectations,generate_sugar_lab_expectations,generate_sugar_report_expectations}.py   # T2, T12, T18, T24, T30/T31
  tests/db/*, tests/api/test_delete_me.py                                  # T1, T11, T23
  tests/unit/scoring/test_glucose_*.py                                     # T2, T12, T18, T24
  tests/api/{sugar,glucose,labs}/*, tests/unit/{test_sugar_copy,test_sugar_privacy}.py   # T3–T5, T13, T14, T19, T25, T29–T31
scripts/clinician_review_sheet.py, docs/launch/clinician-review.md         # T2 (+ T12, T18, T24 rows)
packages/test-fixtures/sugar/{units.json,links.json,labs.json}, stats/{inputs,expected}/, report/   # T2, T12, T24, T18, T30/T31
packages/test-fixtures/modes/layouts.json, README.md                       # T6/T7, T15/T16 (identical hunks); README by each fixture task
packages/i18n/messages/{en,hi,mr}.json, NATIVE_REVIEW.md                   # T5, T14, T19, T25, T31 (+ error keys in API tasks)
packages/design-tokens/tokens.json (+ generated)                           # T5
packages/api-contract/** (generated)                                       # T5, T14, T19, T25, T31
docs/adr/0026-sugar-control-information-only.md, 0027-sugar-report-pdf-engine.md   # T1, T29
apps/app/lib/features/{sugar,glucose,labs}/**, lib/features/modes/mode_layouts.dart, lib/core/storage/meal_queue.dart   # T6, T8, T15, T20, T26, T32
apps/web/src/features/{sugar,glucose,labs}/**, src/features/modes/layouts.ts, src/app/[locale]/(app)/sugar/**, e2e/sugar-*.spec.ts, e2e/stub-api.mjs   # T7, T9, T16, T21, T27, T33
docs/FEATURE_PARITY.md, CONTEXT.md                                         # T10, T17, T22, T28, T34
```

---

## Slice S1: glucose log core

### Task 1 (API, db): Migration 0014, models, RLS, erasure, ADR 0026 *(parallel with Task 2)*

Use the `api-endpoint` skill. Spec: 4.4, 4.5, 12.1, 12.2 (`sugar_settings`, `glucose_readings`), 12.5, 12.6. Rulings H1–H4.

**Files:**
- Create: `apps/api/alembic/versions/0014_sugar_settings_glucose.py`, `apps/api/app/features/{sugar,glucose}/{__init__,models}.py`, `docs/adr/0026-sugar-control-information-only.md`
- Modify: `apps/api/app/features/me/service.py`, `apps/api/tests/db/{conftest,test_rls,test_grants,test_constraints,test_migrations}.py`, `apps/api/tests/api/test_delete_me.py`

**Interfaces:**
- Produces, in the migration (both tables with the composite member FK, `_lock_down`, `ix_<t>_account_id`):
  - `sugar_settings`: `member_id` uuid PK; `account_id` uuid NOT NULL; `glucose_unit` text NOT NULL default `'mg_dl'`, check in (`mg_dl`, `mmol_l`); `range_low_mgdl`, `range_high_mgdl` numeric NULL, check `num_nonnulls(...) in (0, 2)`, `range_low_mgdl < range_high_mgdl`, each within 20–600; `carb_guide_enabled` boolean NOT NULL default false; `created_at`, `updated_at`.
  - `glucose_readings`:
    - `id` uuid PK; `account_id`, `member_id`; `measured_at` timestamptz; `local_date` date; `local_minute` smallint check 0–1439;
    - `value_mgdl` numeric(5,1) check 20–600; `entered_value` numeric; `entered_unit` text check in (`mg_dl`, `mmol_l`);
    - `context` text default `'random'`, check in (`fasting`, `before_meal`, `after_meal`, `bedtime`, `random`); `after_meal_timing` text NULL check in (`about_1h`, `about_2h`, `not_sure`), and check `(context = 'after_meal') = (after_meal_timing IS NOT NULL)`;
    - `linked_local_date` date NULL, `linked_meal_slot_id` uuid NULL, `link_source` text NULL check in (`auto`, `user`); checks `num_nonnulls(linked_local_date, linked_meal_slot_id, link_source) in (0, 3)` and `link_source IS NULL OR context in ('before_meal', 'after_meal')`; FK `(linked_meal_slot_id, member_id) → meal_slots(id, member_id)` (NO ACTION, H2);
    - `note` text NULL check `char_length(note) between 1 and 200`; `source` text default `'manual'` check in (`manual`) (Q11);
    - `client_id` uuid NULL, unique `(account_id, client_id)`; `deleted_at` timestamptz NULL; `created_at`, `updated_at`;
    - indexes `ix_glucose_readings_member_live (member_id, local_date) WHERE deleted_at IS NULL`, `ix_glucose_readings_member_measured (member_id, measured_at)`, `ix_glucose_readings_deleted (deleted_at) WHERE deleted_at IS NOT NULL` (retention).
  - Downgrade drops both tables (docstring: readings are lost).
- Produces models `SugarSettings` (`sugar/models.py`) and `GlucoseReading` (`glucose/models.py`), `Numeric(asdecimal=True)`.
- `ACCOUNT_OWNED_TABLES` per H3 (this task adds `glucose_readings`, `sugar_settings`; later tasks add `carb_guides` and `lab_results` in their places).
- ADR 0026: the DO-NOT-BUILD list as an architectural constraint; no LLM; no analytics events (Q17); report never stored (Q9); `health_data` gating with erasure and CSV on `terms` (Q13); the invariance test; the decisions Q1–Q18 in one table with where each is enforced.

- [ ] **Step 1: Write the failing tests.**
  - `tests/db/test_rls.py`: both tables join `OWNED` and the expected policy set; `test_sugar_tables_owner_only` (account B cannot select A's rows; every write as `authenticated` is 42501).
  - `tests/db/test_grants.py`: the `_lock_down` privileges for both tables.
  - `tests/db/test_constraints.py`:
    - `test_timing_set_iff_after_meal`
    - `test_link_all_or_nothing_and_meal_contexts_only`
    - `test_link_slot_must_belong_to_member` (another member's slot id → FK violation)
    - `test_value_mgdl_backstop_20_600`
    - `test_range_both_or_neither_and_ordered`
    - `test_source_manual_only`
    - `test_client_id_unique_per_account`
  - `tests/db/test_migrations.py`: `test_0014_upgrade_downgrade`.
  - `tests/api/test_delete_me.py`: `test_delete_me_erases_sugar_settings_and_readings` (including soft-deleted rows).
- [ ] **Step 2: Run** `cd apps/api && uv run pytest tests/db tests/api/test_delete_me.py -q` → FAIL.
- [ ] **Step 3: Implement** the migration, models, the erasure order and ADR 0026.
- [ ] **Step 4: Run** the same command → PASS, then `uv run pytest -q`.
- [ ] **Step 5: Commit** `feat(api): migration 0014 sugar settings and glucose readings`.

---

### Task 2 (API, engine): `glucose.py` units, limits, range position, low note; `glucose.yaml`; the unit fixture *(parallel with Task 1)*

Use the `scoring-rule` skill. Spec: 4.1, 4.3, 4.4, 12.3, 14.1, 14.6 (Q3, Q4). Rulings H5, H6, H8–H10, H22.

**Files:**
- Create: `apps/api/app/scoring/glucose.py`, `apps/api/app/scoring/data/glucose.yaml`, `apps/api/tests/unit/scoring/test_glucose_units.py`, `apps/api/scripts/generate_sugar_unit_expectations.py`, `packages/test-fixtures/sugar/units.json`
- Modify: `apps/api/app/scoring/config.py` (`glucose: Mapping[str, Any]` with a default factory), `apps/api/app/scoring/data/thresholds.yaml` (`section_sources`: `glucose_log` → `smartnutri_working_values`; `general_reference` → `ada_standards_of_care` with `url_verified: false`; `glucose_units` → a new source `pubchem_glucose_5793`), `scripts/clinician_review_sheet.py` and `docs/launch/clinician-review.md` (glucose rows with units), `apps/api/tests/unit/scoring/test_targets_yaml.py` or a new `test_glucose_yaml.py` (import graph), `packages/test-fixtures/README.md` ("Sugar Control")

**Interfaces:**
- `glucose.yaml` (S1 keys; later tasks append):

```yaml
# PENDING CLINICIAN REVIEW. Read only by app/scoring/glucose.py. Never read by verdict rules.
version: 1
units:
  mgdl_per_mmoll: 18.016   # PubChem CID 5793, 180.16 g/mol (verified 2026-11-08); some labs use 18
limits:
  hard_mgdl: {min: 20, max: 600}      # [unverified] usual home-meter display range
  confirm_mgdl: {min: 40, max: 400}   # "is this the number you meant to type?"
info:
  very_low_note_below_mgdl: null      # Q3: null until a clinician signs off a number (candidate 54, [unverified])
time: {max_back_days: 90, future_skew_s: 300, duplicate_window_s: 120}
retention: {restore_days: 30}
minors: {min_age: 18}
general_reference:                    # Q4: information card only, never applied
  before_meal_mgdl: {low: 80, high: 130}
  after_meal_peak_below_mgdl: 180
  source: ada_standards_of_care
  url_verified: false
```

- Produces, in `glucose.py` (pure, `Decimal`, reads `cfg.glucose`):

```python
GlucoseUnit = Literal["mg_dl", "mmol_l"]
RangePosition = Literal["below", "within", "above", "no_range"]
@dataclass(frozen=True, slots=True)
class Display: value: Decimal; unit: GlucoseUnit
@dataclass(frozen=True, slots=True)
class UserRange: low_mgdl: Decimal; high_mgdl: Decimal
class GlucoseInputError(Exception): code: str; details: dict   # glucose_precision | glucose_out_of_range | glucose_needs_confirm
def to_mgdl(value: Decimal, unit: GlucoseUnit, cfg=None) -> Decimal                 # precision check, then round 1 dp
def check_value(value: Decimal, unit: GlucoseUnit, *, confirm_unusual: bool, cfg=None) -> Decimal
    # -> value_mgdl; raises out_of_range (details {min, max, unit} in the typed unit) before needs_confirm
    # (details {value, unit, other_value, other_unit})
def display(value_mgdl: Decimal, preferred: GlucoseUnit, *, entered: Display | None = None, cfg=None) -> Display
def other_unit(unit: GlucoseUnit) -> GlucoseUnit
def range_position(value_mgdl: Decimal, user_range: UserRange | None) -> RangePosition   # bounds inclusive within
def very_low_note(value_mgdl: Decimal, *, flag_enabled: bool, cfg=None) -> bool          # False unless flag AND YAML value set AND below
def input_hints(cfg=None) -> dict[GlucoseUnit, dict[str, Decimal]]   # {min, max, confirm_min, confirm_max, step}, in each unit
```

  - `input_hints` in mmol/L are the tightest 1-dp values that pass the mg/dL bounds: hard 1.2–33.3, confirm 2.3–22.2 (because 1.1 × 18.016 = 19.8 < 20 and 33.4 × 18.016 = 601.7 > 600).
- `units.json`: `{factor, input_hints, cases: [{case, value, unit, preferred, confirm_unusual, expected: {value_mgdl, display, display_other, error, details}}]}`, written by the script (`--check` default, `--write`). Cases include:
  - `mgdl_whole` 110 mg/dL → stored 110.0, mmol display 6.1;
  - `mmol_entry` 6.2 mmol/L → stored 111.7, display mg/dL 112, display mmol/L 6.2 (entered exactly);
  - `mmol_7_0` → 126.1 stored, 126 mg/dL;
  - boundaries 19 / 20 / 600 / 601 mg/dL and 1.1 / 1.2 / 33.3 / 33.4 mmol/L;
  - confirm 39 / 40 / 400 / 401 mg/dL (with and without `confirm_unusual`);
  - precision 110.5 mg/dL and 6.25 mmol/L → `glucose_precision`;
  - `mmol_value_with_mgdl_unit` 6.1 mg/dL → `glucose_out_of_range`; `mgdl_value_with_mmol_unit` 110 mmol/L → `glucose_out_of_range`.

- [ ] **Step 1: Write the failing tests** in `test_glucose_units.py`:

```python
def test_mmol_entry_stores_one_decimal():      # to_mgdl(D("6.2"), "mmol_l") == D("111.7")
def test_display_in_entered_unit_is_exact():   # entered 6.2 mmol/L, preferred mmol_l -> 6.2
def test_display_converts_half_up():           # 110.0 mg/dL -> 6.1 mmol/L; 111.7 -> 112 mg/dL
def test_precision_errors():                   # 110.5 mg_dl, 6.25 mmol_l -> glucose_precision
def test_out_of_range_before_confirm():        # 601 with confirm_unusual=True -> out_of_range
def test_needs_confirm_details_both_units():
def test_range_position_inclusive_bounds():    # low and high themselves are "within"
def test_no_range_is_no_range():
def test_very_low_note_gated_twice():          # flag off -> False; YAML null -> False; both on and below -> True
def test_no_high_note_exists():                # glucose.py exposes no high-reading note (name check)
def test_input_hints_mmol():                   # 1.2, 33.3, 2.3, 22.2
# Hypothesis (spec 14.1):
def test_mgdl_round_trip(v):                   # every whole 20..600: display(to_mgdl(v), "mg_dl") == v
def test_mmol_round_trip(v):                   # every 1-dp 1.2..33.3: entered shown exactly; |stored - v*18.016| <= 0.05;
                                               # display(stored, "mmol_l") without entered == v
def test_monotonic(a, b):
def test_never_infers_unit(v):                 # the result follows the stated unit for 6.0 and 110 in both units
def test_units_fixture():                      # packages/test-fixtures/sugar/units.json
def test_yaml_header_and_sources():            # header present; every key read; section_sources entries exist
def test_verdict_modules_never_import_glucose():   # verdict.py, conditions.py, analyze service import graph
```

- [ ] **Step 2: Run** `uv run pytest tests/unit/scoring/test_glucose_units.py -q` → FAIL.
- [ ] **Step 3: Implement** `glucose.py`, the YAML, the config field, the sources, the clinician rows; run the script with `--write`.
- [ ] **Step 4: Run** → PASS; `uv run python -m scripts.generate_sugar_unit_expectations --check` → no diff; `uv run pytest tests/unit/test_clinician_review_sheet.py -q` → PASS.
- [ ] **Step 5: Commit** `feat(scoring): glucose units, limits and range position (pending clinician review)`.

---

### Task 3 (API): Sugar member, consent keys, flags, buckets, settings routes

Use the `api-endpoint` skill. Spec: 4.1, 4.3 (range, reference card), 12.4 (`sugar_settings_*`, `sugar_unit_put`), 12.5, 12.6 (minors). Rulings H14, H15, H22.

**Files:**
- Create: `apps/api/app/features/sugar/{members,schemas,service,router}.py`, `apps/api/tests/api/sugar/{test_settings,test_members,test_consent}.py`
- Modify: `apps/api/app/core/consent.py` (`sugar`, `sugar_prefs`, `sugar_erase`), `apps/api/app/core/config.py` (`sugar_family_enabled`, `sugar_low_note_enabled`, `rate_limit_glucose_writes_per_day = 200`, `rate_limit_sugar_settings_per_day = 30`), `apps/api/app/core/ratelimit.py`, `apps/api/app/main.py`, `packages/i18n/messages/{en,hi,mr}.json` (`error.sugar_member_not_enabled`, `error.sugar_range_invalid`, `error.sugar_not_available_minor`)

**Interfaces:**
- Consumes: Task 1 `SugarSettings`; Task 2 `to_mgdl`, `display`, `input_hints`, config; `members_service.get_or_create_primary`, `get_member`; the targets `youngest_age`.
- Produces:

```python
# sugar/members.py
async def sugar_member(session: AsyncSession, account_id: UUID, member_id: UUID | None, settings: Settings,
                       *, today: date, check_minor: bool = True) -> Member
    # None -> primary; foreign -> 404 member_not_found; non-primary while off -> 422 sugar_member_not_enabled;
    # check_minor and youngest_age < minors.min_age -> 422 sugar_not_available_minor
# sugar/service.py
async def get_settings_row(session, member) -> SugarSettings | None
async def user_range(session, member) -> UserRange | None
async def preferred_unit(session, member) -> GlucoseUnit          # 'mg_dl' without a row
def settings_out(member, row: SugarSettings | None) -> SugarSettingsOut
```

```text
SugarSettingsOut {member_id, configured: bool, glucose_unit,
  range: {low, high, unit, low_mgdl, high_mgdl} | null,        # low/high in the preferred unit
  input_hints: {mg_dl: Hints, mmol_l: Hints},                  # Hints {min, max, confirm_min, confirm_max, step}
  reference: {before_meal: {low, high}, after_meal_peak_below, unit: "mg_dl", url_verified: false},
  pending_clinician_review: true}
GET    /v1/sugar/settings          sugar_settings_get     (sugar)             -> SugarSettingsOut (defaults without a row)
PUT    /v1/sugar/settings          sugar_settings_put     (sugar; sugar_settings)
       {member_id?, glucose_unit, range: {low, high, unit} | null} -> SugarSettingsOut
       422 sugar_range_invalid details.reason: precision | out_of_range | order
PUT    /v1/sugar/settings/unit     sugar_unit_put         (sugar_prefs; sugar_settings) {member_id?, glucose_unit} -> SugarSettingsOut
DELETE /v1/sugar/settings          sugar_settings_delete  (sugar_erase) -> 204, clears the range (S2: and the guide); keeps the unit
```

  - The member for `sugar_unit_put` and `sugar_settings_delete` resolves with `check_minor=False`.

- [ ] **Step 1: Write the failing tests.**
  - `test_settings.py`:
    - `test_defaults_without_row` (`configured` false, `mg_dl`, `range` null: Q4)
    - `test_put_range_mmol_stored_mgdl` (4.0–7.0 mmol/L → 72.1 and 126.1; shown back as 4.0 and 7.0)
    - `test_range_survives_unit_switch`
    - `test_range_invalid_reasons` (precision, out of range, low ≥ high)
    - `test_unit_put_creates_row_on_terms_only`
    - `test_delete_clears_range_keeps_unit`
    - `test_reference_and_hints_from_yaml`
    - `test_no_code_path_writes_range_except_put` (Q4: grep-style check that only `sugar/service.py` assigns `range_low_mgdl`)
  - `test_members.py`: `test_non_primary_refused_while_flag_off`, `test_foreign_member_404`, `test_minor_refused_unknown_age_allowed`, `test_unit_put_and_delete_allowed_for_minor`.
  - `test_consent.py`: `test_get_put_need_health_data` (403 with `details.purposes`), `test_unit_put_and_delete_need_terms_only`, `test_gate_before_rate_limit`.
- [ ] **Step 2: Run** `uv run pytest tests/api/sugar -q` → FAIL.
- [ ] **Step 3: Implement**, with the three `error.*` keys (en, hi, mr; NATIVE_REVIEW "Plan 13 slice S1").
- [ ] **Step 4: Run** → PASS; full suite PASS.
- [ ] **Step 5: Commit** `feat(api): sugar settings with a user-set range only`.

---

### Task 4 (API): Glucose routes: create, list, get, patch, delete, restore, deleted list

Use the `api-endpoint` skill. Spec: 4.1–4.6, 12.4 (`glucose_*` except link-suggestion), 14.3, 14.6 (Q15, Q16). Rulings H9, H10, H14, H18.

**Files:**
- Create: `apps/api/app/features/glucose/{schemas,service,router}.py`, `apps/api/tests/api/glucose/{test_create,test_list_get,test_patch,test_delete_restore,test_consent}.py`
- Modify: `apps/api/app/main.py`, `apps/api/app/core/ratelimit.py` (`glucose_writes`), `packages/i18n/*` (the `error.*` keys below)

**Interfaces:**
- Consumes: Task 2 `check_value`, `display`, `range_position`, `very_low_note`; Task 3 `sugar_member`, `user_range`, `preferred_unit`; `core.time.local_date_of`, `local_clock`; `core.cursor`.
- Produces:

```text
GlucoseIn {member_id?, value: number, unit: "mg_dl"|"mmol_l" (required), measured_at? (default now),
           context? (default "random"), after_meal_timing?, note? (1-200 chars; "" -> null; stored as typed),
           confirm_unusual = false, confirm_duplicate = false, client_id?}
GlucosePatch {value?, unit? (both or neither), measured_at?, context?, after_meal_timing?, note? (null clears),
              confirm_unusual = false, confirm_duplicate = false}
GlucoseOut {id, member_id, measured_at, local_date, local_time "HH:MM", value_mgdl (unrounded),
            entered {value, unit}, display {value, unit}, display_other {value, unit}, context, after_meal_timing,
            range_position, very_low_note: bool, link: null (S2 fills it), note, source: "manual",
            created_at, updated_at, deleted_at}
GlucoseDeletedOut {id, deleted_at, restore_until}
POST   /v1/glucose                 glucose_create        (sugar; glucose_writes) -> 201, 200 on a repeated client_id (also on a race)
GET    /v1/glucose?member_id&from&to&context&limit&cursor   glucose_list  (sugar) -> {items, next_cursor}
       newest first (measured_at desc, id); default the last 7 local days; > 92 days -> 422 date_range_too_long; limit 1-200, default 100
GET    /v1/glucose/deleted         glucose_deleted_list  (sugar) -> {items: GlucoseOut[]}  inside the restore window, newest deleted first
GET    /v1/glucose/{id}            glucose_get           (sugar)
PATCH  /v1/glucose/{id}            glucose_update        (sugar; glucose_writes)
DELETE /v1/glucose/{id}            glucose_delete        (sugar_erase) -> 200 GlucoseDeletedOut (idempotent)
POST   /v1/glucose/{id}/restore    glucose_restore       (sugar; glucose_writes) -> GlucoseOut; 410 glucose_restore_expired
```

  - Validation order on create and patch: unit and precision → hard limits → timing (`glucose_timing_required`; timing sent with another context → `validation_error`) → time (`measured_at_in_future`, `measured_at_too_old`) → confirm (`glucose_needs_confirm`) → duplicate (`409 glucose_possible_duplicate` with `details {existing_id, time, value, unit}`: a live reading of the same member within ±120 s with the same `value_mgdl`, unless `confirm_duplicate`).
  - `local_date` and `local_minute` come from `measured_at` in the account zone at write; a patch of `measured_at` recomputes them; a zone change never moves them.
  - `display` uses the preferred unit (the entered value when the units match); `very_low_note` reads `settings.sugar_low_note_enabled`.
  - New error codes (en, hi, mr): `glucose_out_of_range`, `glucose_needs_confirm`, `glucose_precision`, `glucose_possible_duplicate`, `glucose_timing_required`, `glucose_not_found`, `glucose_restore_expired`, `measured_at_in_future`, `measured_at_too_old`.

- [ ] **Step 1: Write the failing tests.**
  - `test_create.py`:
    - `test_create_mgdl_and_mmol` (fixture rows from `sugar/units.json` through the API)
    - `test_unit_required_never_inferred` (no unit → `validation_error`; 6.0 and 110 follow the stated unit)
    - `test_confirm_then_save`, `test_out_of_range_details_in_typed_unit`
    - `test_timing_required_iff_after_meal`
    - `test_future_skew_300s_ok_301_refused`
    - `test_back_entry_90_days_account_zone` (account in `America/New_York`: 90 local days accepted, 91 refused)
    - `test_duplicate_409_then_confirm` and `test_different_value_close_in_time_allowed`
    - `test_client_id_repeat_returns_original_200` (body differs) and `test_parallel_same_client_id_one_row`
    - `test_note_stored_as_typed_never_logged` (log capture holds neither the value nor the note)
    - `test_link_never_written_in_s1` (`linked_*` columns stay null)
    - `test_very_low_note_off_by_default` (Q3: 25 mg/dL → false with the shipped flag and YAML)
    - `test_rate_limited`
  - `test_list_get.py`: `test_list_newest_first_and_cursor`, `test_default_7_days_and_92_day_cap`, `test_context_filter`, `test_local_date_frozen_on_timezone_change`, `test_range_position_follows_settings`, `test_foreign_reading_404`.
  - `test_patch.py`: `test_patch_value_and_unit_together`, `test_patch_measured_at_recomputes_local`, `test_patch_runs_same_validation`, `test_patch_deleted_404`.
  - `test_delete_restore.py`:
    - `test_delete_returns_restore_until` (+30 days) and `test_delete_idempotent`
    - `test_deleted_hidden_from_list_and_duplicate_check`
    - `test_restore_on_day_30_ok_after_410` (Q16, with a pinned clock)
    - `test_deleted_list_window_only`
  - `test_consent.py`: `test_routes_need_health_data_except_erase` (every route but delete → 403; delete works on `terms` alone and keeps erasing after withdrawal), `test_withdrawal_keeps_rows_and_reconsent_shows_them`, `test_gate_before_rate_limit`, `test_minor_refused`.
- [ ] **Step 2: Run** `uv run pytest tests/api/glucose -q` → FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** → PASS; full suite PASS.
- [ ] **Step 5: Commit** `feat(api): glucose readings with soft delete, restore and idempotent create`.

---

### Task 5 (API + shared): Retention, invariance, analytics and copy guards, i18n, tokens, consent bump, contract

Spec: 4.5 (purge), 12.5 (consent text), 12.6, 13.1 (tokens), 13.4, 14.3. Rulings H4, H16, H17, H29.

**Files:**
- Create: `apps/api/tests/api/sugar/test_invariance.py`, `apps/api/tests/unit/test_sugar_copy.py`, `apps/api/tests/unit/test_sugar_privacy.py`
- Modify:
  - `apps/api/app/jobs/retention.py` (readings purge, counts only; `RetentionResult.readings_purged`), `apps/api/tests/unit/test_retention.py`
  - `apps/api/app/features/consents/policy.py` (`health_data` → `"2026-11-08"`)
  - `packages/i18n/messages/{en,hi,mr}.json`, `packages/i18n/NATIVE_REVIEW.md` ("Plan 13 slice S1")
  - `packages/design-tokens/tokens.json` (+ `just tokens` outputs)
  - `packages/api-contract/**` (generated), `apps/app/lib/l10n/*.arb` (generated), the Android error map (new codes only)

**Interfaces:**
- Retention: `delete from glucose_readings where deleted_at < :now - interval '30 days'` in the existing row transaction (the window from `glucose.yaml retention.restore_days`); `--dry-run` reports the count only.
- `test_sugar_copy.py` scans every `sugar.*` key, `consent.health_data.body` and the sugar `error.*` keys in en, hi and mr against the shared `BANNED` / `BANNED_NATIVE` plus:

```python
SUGAR_BANNED = re.compile(r"\b(spikes?|control(s|led|ling)?|alarms?|danger\w*|risks?|"
                          r"estimat\w*|e?a1c estimate|gmi|time in range|diabetics?|patients?|"
                          r"normal|abnormal|good|bad|safe|unsafe|target)\b", re.IGNORECASE)
SUGAR_BANNED_NATIVE = ("खतरा", "जोखिम", "नियंत्रण", "धोका", "अनुमानित")   # not "सामान्य": it also means "general"
```

  and checks that `sugar.disclaimer` contains "not medical advice" in en. It also asserts that hi and mr have the same key set as en.
- `test_sugar_privacy.py`: `test_allowed_events_have_no_sugar_names` (the three `ALLOWED_EVENTS` lists and their property keys contain none of `glucose|lab|sugar|reminder|a1c`); `test_scrubbed_event_has_no_glucose_body` (H17); `test_logs_have_no_values_or_notes` (log capture over a create, patch and delete).
- `test_invariance.py`: `test_analyze_identical_with_sugar_data` (the full verdict fixture set through `analyze`, before and after adding readings and a range for the member: byte-identical bodies).
- Tokens: `sugar.reading`, `sugar.reading-muted`, `sugar.meal`, `sugar.pattern-band`, `sugar.pattern-median`, derived from the brand and neutral palettes (never a verdict colour).
- **New i18n keys (S1), en drafts** (the spec §13.4 table, adjusted by H29):
  - `nav.sugar` "Sugar"; `sugar.title` "Sugar"; `sugar.disclaimer` "Information, not medical advice. Values are as you entered them."; `sugar.pending_review` "Some numbers here are pending clinician review."; `sugar.add_reading`; `sugar.reading.value` "Reading"; `sugar.unit.mg_dl`, `sugar.unit.mmol_l`; `sugar.value_unit` "{value} {unit}";
  - `sugar.context.{fasting,before_meal,after_meal,bedtime,random}`; `sugar.timing.{about_1h,about_2h,not_sure}`; `sugar.time` "Time"; `sugar.note` "Note (optional)";
  - `sugar.range.{below,within,above}`;
  - `sugar.confirm_unusual` "Is this the number you meant to type? {value} {unit} ({other_value} {other_unit})"; `sugar.confirm_duplicate` "You saved {value} {unit} at {time} already. Save this one too?"; `sugar.save_anyway`;
  - `sugar.very_low_note` "If you feel unwell, follow the plan your doctor gave you, or get medical help." (written now; never returned until sign-off and the flag, Q3);
  - `sugar.deleted` "Reading deleted."; `sugar.undo`; `sugar.recently_deleted`; `sugar.recently_deleted.help` "Deleted items stay here for 30 days, then they are removed for good."; `sugar.restore`; `sugar.empty` "No readings yet. Add one when you next check."; `sugar.queued` "Waiting to sync"; `sugar.check_entry` "Check this reading"; `sugar.consent_card` "To log readings and lab results, allow SmartNutri to use your health details.";
  - `sugar.no_alerts` "SmartNutri does not notify you about readings." (the key name is code; alarms stay banned in copy);
  - `sugar.settings.{title,unit,range,range_help,reference_card,reference_unverified}` (spec §13.4 text for `range_help` and `reference_card`; `reference_unverified` "Source not yet checked by a clinician.");
  - `sugar.intro.{more_q,diabetes,prediabetes,pcos,prefer_not,just_watching,profile_note,what,start,look_around,adults_note}` (spec §11 text; `adults_note` "Sugar Control is for adults.");
  - `consent.health_data.body`: "SmartNutri uses the allergies, health conditions, goal, height, weight, weigh-ins, glucose readings and lab results you enter, to check products and show your own logs. This is information, not medical advice. You can withdraw this consent at any time."

- [ ] **Step 1: Write the failing tests:** the three new test files and `test_retention_purges_only_expired_readings` (a row deleted 31 days ago is purged, 29 days ago kept, live rows kept; dry run counts only). `tests/api/test_openapi.py` → FAIL (drift from Tasks 3–4).
- [ ] **Step 2: Run** `uv run pytest tests/unit/test_sugar_copy.py tests/unit/test_sugar_privacy.py tests/unit/test_retention.py tests/api/sugar/test_invariance.py -q` → FAIL.
- [ ] **Step 3: Implement** the purge and the consent bump; add the keys in en, then hi and mr (machine drafts) with NATIVE_REVIEW flags (the neutral tone of the range labels and the low note; that "control" words such as "नियंत्रण" are absent; mg/dL and mmol/L kept in Latin script); `pnpm --filter @smartnutri/i18n build`, `cd apps/app && flutter gen-l10n`; `just tokens` lines; the justfile `contract` lines.
- [ ] **Step 4: Run** `uv run pytest -q && uv run ruff check . && uv run ruff format --check .`; `generate_sugar_unit_expectations --check`; `dart analyze` in `packages/api-contract/dart`; `cd apps/app && dart format --set-exit-if-changed lib test && flutter analyze && flutter test`; `cd apps/web && pnpm lint && npx tsc --noEmit && pnpm test` → PASS (minimal compile fixes only).
- [ ] **Step 5: Commit** `feat(api): purge expired deleted readings; sugar privacy and copy guards`, `feat(i18n): sugar control slice S1 and the health_data text`, `chore(contract): sugar settings and glucose`.

---

### Task 6 (Android): Sugar tab, day list, reading sheet, undo, queue v7, modes *(parallel with Task 7)*

Use the `flutter-feature` skill. Spec: 4, 13.1, 13.2 (screens 1, 2), 13.3, 14.5. Rulings H25–H27.

**Files:**
- Create:
  - `apps/app/lib/features/glucose/data/{glucose_repository.dart, glucose_sync.dart}`, `apps/app/lib/features/glucose/presentation/{reading_sheet.dart, reading_tile.dart, glucose_providers.dart}`
  - `apps/app/lib/features/sugar/presentation/{sugar_screen.dart, sugar_providers.dart, sugar_consent_card.dart}`
  - `apps/app/test/features/glucose/{reading_sheet_test.dart, reading_tile_test.dart, glucose_sync_test.dart, units_fixture_test.dart}`, `apps/app/test/features/sugar/{sugar_screen_test.dart, no_verdict_tokens_test.dart}`, `apps/app/test/core/storage/meal_queue_v7_migration_test.dart`
- Modify: `apps/app/lib/core/storage/meal_queue.dart` (v7; regenerated `.g.dart`), `apps/app/lib/core/router/app_router.dart`, `apps/app/lib/features/modes/mode_layouts.dart`, the modes tests, `packages/test-fixtures/modes/layouts.json` (the H25 hunk), `apps/api/tests/fixtures/test_mode_layouts.py`

**Interfaces:**
- `layouts.json` hunk (identical in Task 7): `destinations` gains `"sugar"` after `"diary"`; `modes.health_condition.tabs` = `["home", "scan", "diary", "sugar", "profile"]`. `test_mode_layouts.py` expects the new tabs and that `health_condition` More lists `family`.
- Consumes: the generated `glucoseCreate`, `glucoseList`, `glucoseUpdate`, `glucoseDelete`, `glucoseRestore`, `sugarSettingsGet`; `GlucoseOut`, `SugarSettingsOut.inputHints`.
- **Sugar tab:** the latest reading card (`display` plus `sugar.range.*` text and an icon when `rangePosition != no_range`, in the `sugar.reading` token); "Add reading"; today's readings (from `glucoseList` for today, API order unchanged), each `ReadingTile` (time, display value and unit, context and timing chip, range text, a note icon when `note` is set); `sugar.disclaimer`, `sugar.pending_review`, `sugar.no_alerts`; `sugar.empty`. Without `health_data`, the consent card only.
- **Reading sheet:** a large numeric field; unit chips (preferred preselected); Save disabled outside `inputHints` for the selected unit (the only client check); context chips (default `random`); timing chips only for `after_meal` (required there); time (default now, back to 90 days); note. `glucose_needs_confirm` → `sugar.confirm_unusual` with both units from `details` → resend with `confirmUnusual`; `409 glucose_possible_duplicate` → `sugar.confirm_duplicate` → resend with `confirmDuplicate`. The low-note line shows only when the response has `veryLowNote: true`, as plain text with no colour, icon or sound.
- **Delete:** swipe or menu → `glucoseDelete` → snackbar `sugar.deleted` + `sugar.undo` for 8 s → `glucoseRestore`.
- **Queue v7** (H27): `PendingGlucose {clientId, memberId?, value, unit, measuredAt, context, afterMealTiming?, note?, confirmUnusual, confirmDuplicate, linkChoice?, linkDate?, linkSlotId?, status}`. Offline save queues and shows `sugar.queued`. On sync: `needs_confirm` / `possible_duplicate` → `sugar.check_entry` and the confirm dialog; `consent_required` → the row stays queued and the consent card shows.
- No analytics call anywhere under `features/{sugar,glucose}`.

- [ ] **Step 1: Write the failing tests.**
  - `units_fixture_test.dart`: `input hints match sugar/units.json`, `display rows render value and unit as given`.
  - `reading_sheet_test.dart`:
    - `save disabled outside hints per unit`
    - `timing required only for after meal`
    - `unusual confirm shows both units`
    - `duplicate confirm resends with flag`
    - `low note only when veryLowNote true and never coloured`
    - `no unit is ever inferred` (switching units never rewrites the typed number)
  - `reading_tile_test.dart`: `range text only when position set`, `note shows icon not text`.
  - `sugar_screen_test.dart`: `renders API order unchanged`, `empty state`, `consent card without health_data`, `delete then undo restores`, `disclaimer and no-alerts line shown`.
  - `glucose_sync_test.dart`: `offline save queues and shows waiting`, `sync needs confirm marks check entry`, `queued reading kept on consent_required`, `repeat client id is success`.
  - `meal_queue_v7_migration_test.dart`: `v6 opens at v7 with empty glucose queue`.
  - `no_verdict_tokens_test.dart`: no file under `lib/features/{sugar,glucose}` references a verdict colour, `danger` or the analytics client.
  - the modes tests: Sugar is a tab in `health_condition`, in More elsewhere; reachability for `sugar`.
- [ ] **Step 2: Run them** to verify they fail.
- [ ] **Step 3: Implement**, then `dart run build_runner build --delete-conflicting-outputs`.
- [ ] **Step 4: Run** `dart format --set-exit-if-changed lib test && flutter analyze && flutter test`; `cd apps/api && uv run pytest tests/fixtures/test_mode_layouts.py -q` → PASS.
- [ ] **Step 5: Commit** `feat(app): sugar tab and glucose reading log with offline queue`.

---

### Task 7 (Web): Sugar tab, day list, reading sheet, undo, modes, e2e *(parallel with Task 6)*

Use the `web-feature` skill. Spec: as Task 6. Rulings H25, H26.

**Files:**
- Create: `apps/web/src/features/glucose/{api/glucose.ts, hooks/useGlucose.ts, components/{ReadingDialog.tsx, ReadingRow.tsx}}`, `apps/web/src/features/sugar/{api/settings.ts, hooks/useSugarSettings.ts, components/{SugarView.tsx, SugarConsentCard.tsx}}`, `apps/web/src/app/[locale]/(app)/sugar/page.tsx`, `apps/web/tests/features/{glucose,sugar}/*.test.tsx`, `apps/web/e2e/sugar-log.spec.ts`
- Modify: `apps/web/src/features/modes/layouts.ts`, `apps/web/src/components/shell/AppNav.tsx` (the `sugar` destination), the modes tests, `packages/test-fixtures/modes/layouts.json` (the identical H25 hunk), `apps/web/e2e/stub-api.mjs`

**Interfaces:** the Task 6 behaviour, online-only (the existing online-only note; no queue).

- [ ] **Step 1: Write the failing tests:** the Task 6 component cases (no offline) as Vitest tests, `units.test.ts` against `sugar/units.json`, `noVerdictTokens.test.ts` (no `verdict-` or `danger` CSS variable and no analytics import under `src/features/{sugar,glucose}`), the modes cases. Plus `e2e/sugar-log.spec.ts`: add 6.2 mmol/L → shown as 6.2; add 450 mg/dL → confirm shows both units → save; add the same value within 2 minutes → duplicate confirm; delete → Undo → back; withdraw `health_data` in the stub → the consent card shows and the Diary still loads.
- [ ] **Step 2: Run them** to verify they fail.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `pnpm lint && npx tsc --noEmit && pnpm test && pnpm e2e` → PASS.
- [ ] **Step 5: Commit** `feat(web): sugar tab and glucose reading log`.

---

### Task 8 (Android): Sugar settings, recently deleted, intro *(parallel with Task 9)*

Use the `flutter-feature` skill. Spec: 4.3, 4.5, 11, 13.2 (screen 9), 14.6 (Q4). Rulings H22, H28.

**Files:**
- Create: `apps/app/lib/features/sugar/presentation/{sugar_settings_screen.dart, recently_deleted_screen.dart, sugar_intro.dart}`, `apps/app/test/features/sugar/{sugar_settings_test.dart, recently_deleted_test.dart, sugar_intro_test.dart}`
- Modify: `apps/app/lib/features/sugar/presentation/sugar_screen.dart` (entries to Settings and the intro), the router, Profile (a "Sugar settings" entry)

**Interfaces:**
- **Settings:** unit (`sugarUnitPut`); "Your range (optional)" empty by default, two fields in the preferred unit with `sugar.settings.range_help`, Save → `sugarSettingsPut`, Clear → `sugarSettingsDelete`; the reference card from `reference` (never a button that copies it in; `sugar.settings.reference_unverified` while `urlVerified` is false); a link to Recently deleted and to the diary number settings.
- **Recently deleted:** `glucoseDeletedList` with Restore per row; `glucose_restore_expired` → removed from the list with `error.glucose_restore_expired`; `sugar.recently_deleted.help`.
- **Intro (H28):** three steps; step 1 the optional condition question (multi-select for the first three; "Prefer not to say" and "just watching" save nothing; picking a condition confirms, then PATCHes the primary member's `conditions` through the existing members flow with the consent dialog if needed); step 2 unit, optional range, skip prominent; step 3 `sugar.intro.what` + `sugar.disclaimer` + `sugar.intro.adults_note`, "Start with a reading" and "Just look around".

- [ ] **Step 1: Write the failing tests.**
  - `sugar_settings_test.dart`: `range empty by default`, `reference card never applied` (no control writes it to the range), `unit switch keeps range digits from API`, `clear range calls delete`, `range invalid maps reason`.
  - `recently_deleted_test.dart`: `restore removes from list`, `expired shows message`.
  - `sugar_intro_test.dart`: `shown while not configured`, `look around saves unit only`, `condition saved only after confirm and consent`, `prefer not to say saves nothing`.
- [ ] **Step 2: Run them** to verify they fail.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `dart format --set-exit-if-changed lib test && flutter analyze && flutter test` → PASS.
- [ ] **Step 5: Commit** `feat(app): sugar settings, recently deleted and intro`.

---

### Task 9 (Web): Sugar settings, recently deleted, intro, e2e *(parallel with Task 8)*

Use the `web-feature` skill.

**Files:**
- Create: `apps/web/src/features/sugar/components/{SugarSettings.tsx, RecentlyDeleted.tsx, SugarIntro.tsx}`, `apps/web/src/app/[locale]/(app)/sugar/{settings,deleted}/page.tsx`, `apps/web/tests/features/sugar/{SugarSettings,RecentlyDeleted,SugarIntro}.test.tsx`, `apps/web/e2e/sugar-settings.spec.ts`
- Modify: `SugarView.tsx` (intro and links), the Profile page (link), `stub-api.mjs`

**Interfaces:** the Task 8 behaviour.

- [ ] **Step 1: Write the failing tests:** the Task 8 cases. Plus `e2e/sugar-settings.spec.ts`: first visit shows the intro; "Just look around" → the tab; set a range 4.0–7.0 mmol/L → a reading of 8.0 shows "Above your range"; switch to mg/dL → the range shows 72–126; delete a reading, open Recently deleted, Restore.
- [ ] **Step 2: Run them** to verify they fail.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `pnpm lint && npx tsc --noEmit && pnpm test && pnpm e2e` → PASS.
- [ ] **Step 5: Commit** `feat(web): sugar settings, recently deleted and intro`.

---

### Task 10: Slice-S1 gate: safety review, parity, docs

**Files:**
- Modify: `docs/FEATURE_PARITY.md` (rows F27–F31 added; F27 → 🟡 "code complete; numbers pending clinician review"), `CONTEXT.md` (Plan 13 S1 status; migration 0014; USER items: clinician sign-off on `glucose.yaml` including the very-low value and 18 vs 18.016; lawyer items on the health_data text, keeping data after withdrawal and minors), this plan (tick the boxes)

- [ ] **Step 1: Run everything:** `cd apps/api && uv run pytest -q && uv run ruff check . && uv run ruff format --check .`; `generate_sugar_unit_expectations --check` and the existing `generate_*_expectations --check` scripts; `dart analyze` in `packages/api-contract/dart`; `cd apps/app && dart format --set-exit-if-changed lib test && flutter analyze && flutter test`; `cd apps/web && pnpm lint && npx tsc --noEmit && pnpm test && pnpm e2e`. Expected: all green; `sugar/units.json` passes on all three.
- [ ] **Step 2: Dispatch** `nutrition-safety-reviewer` on the slice diff. Scope: the DO-NOT-BUILD list; `glucose.yaml` values and sources (H6); conversion and rounding; the confirm wording ("typing", not health); Q3 double gate; Q4 (no default range, reference card never applied); range labels neutral; no verdict colours; consent per route and the health_data text bump (H16); minors (H15); soft delete and the purge (Q16); no analytics and no logged values; `analyze` invariance; the copy and its hi and mr drafts.
- [ ] **Step 3: Fix** every blocking finding (each with its test), then re-run Step 1.
- [ ] **Step 4: Commit** `docs: Plan 13 slice S1 parity, context and review`.

---

## Slice S2: timeline, meal link, carbs per meal, carb guide

### Task 11 (API, db): Migration 0015 `carb_guides` *(parallel with Task 12)*

Use the `api-endpoint` skill. Spec: 6.2, 12.2 (`carb_guides`). Rulings H1–H3, H21.

**Files:**
- Create: `apps/api/alembic/versions/0015_sugar_carb_guides.py`
- Modify: `apps/api/app/features/sugar/models.py` (`CarbGuide`), `apps/api/app/features/me/service.py` (`carb_guides` per H3), `apps/api/tests/db/*`, `apps/api/tests/api/test_delete_me.py`

**Interfaces:**
- `carb_guides`: PK `(member_id, meal_slot_id)`; `account_id`; `grams` numeric check `>= 5 and <= 200`; `created_at`, `updated_at`; the composite member FK (cascade); FK `(meal_slot_id, member_id) → meal_slots(id, member_id)` (NO ACTION); `_lock_down`.

- [ ] **Step 1: Write the failing tests:** RLS and grants for `carb_guides`; `test_carb_guide_bounds_5_200`; `test_carb_guide_slot_of_same_member`; `test_0015_upgrade_downgrade`; delete-me erases `carb_guides`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4: Run** → PASS; full suite PASS.
- [ ] **Step 5: Commit** `feat(api): migration 0015 carb guides`.

---

### Task 12 (API, engine): Pure `link_candidate`, link fixture *(parallel with Task 11; may start after Task 2)*

Use the `scoring-rule` skill. Spec: 5.2, 14.2 (link suggestion). Ruling H19.

**Files:**
- Create: `apps/api/tests/unit/scoring/test_glucose_links.py`, `apps/api/scripts/generate_sugar_link_expectations.py`, `packages/test-fixtures/sugar/links.json`
- Modify: `apps/api/app/scoring/glucose.py`, `glucose.yaml`, the clinician sheet, `packages/test-fixtures/README.md`

**Interfaces:**
- YAML: `link: {after_meal_min_minutes: 15, after_meal_max_minutes: 240, before_meal_max_minutes: 60}`.
- Produces:

```python
@dataclass(frozen=True, slots=True)
class MealWindow: local_date: date; meal_slot_id: UUID; first_at: datetime; last_at: datetime; position: int
LinkContext = Literal["fasting", "before_meal", "after_meal", "bedtime", "random"]
def link_candidate(measured_at: datetime, context: LinkContext, meals: Sequence[MealWindow], cfg=None) -> MealWindow | None
    # after_meal: last_at in [measured_at - 240 min, measured_at - 15 min], latest last_at wins;
    # before_meal: first_at in [measured_at, measured_at + 60 min], earliest first_at wins;
    # bounds inclusive; ties -> lower position, then meal_slot_id; other contexts -> None.
    # The caller passes the meals of the reading's local date and the days either side.
```

- `links.json` cases: `after_14_none`, `after_15`, `after_240`, `after_241_none`, `nearest_wins`, `after_midnight_previous_dinner` (reading 00:30, dinner's last entry 22:00 the day before), `before_0`, `before_60`, `before_61_none`, `fasting_never`, `random_never`, `tie_lower_position`.

- [ ] **Step 1: Write the failing tests:** one test per fixture case through `test_links_fixture()`, plus `test_unlinkable_contexts_return_none` and `test_yaml_link_keys_read_and_sourced`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement**; the script with `--write`. **Step 4: Run** → PASS; `--check` → no diff.
- [ ] **Step 5: Commit** `feat(scoring): meal link windows for glucose readings`.

---

### Task 13 (API): Links on create and patch, the link-suggestion route

Use the `api-endpoint` skill. Spec: 5.2, 12.4 (`link`, `glucose_link_suggest`). Ruling H19.

**Files:**
- Create: `apps/api/app/features/glucose/links.py`, `apps/api/tests/api/glucose/{test_links,test_link_suggestion}.py`
- Modify: `apps/api/app/features/glucose/{schemas,service,router}.py`, `packages/i18n/*` (`error.glucose_link_not_allowed`)

**Interfaces:**
- Consumes: Task 12 `link_candidate`; `meals_service.list_meals_by_date`; `slots_service.list_slots(include_archived=True)`.
- Produces:

```python
# glucose/links.py
async def meal_windows(session, member, around: date) -> list[MealWindow]          # around-1 .. around+1, from meal_logs.eaten_at
async def resolve_link(session, member, reading_measured_at, context, link: LinkIn | None | Unset)
    -> tuple[date, UUID, Literal["auto", "user"]] | None                           # H19 rules and errors
async def link_out(session, member, reading: GlucoseReading) -> LinkOut | None
```

```text
GlucoseIn and GlucosePatch gain  link?: {local_date, meal_slot_id} | null   (omitted = auto on create; unchanged on patch per H19)
LinkOut {local_date, meal_slot_id, slot_label_key, slot_custom_label, source: "auto"|"user", meal_has_items}
GlucoseOut.link: LinkOut | null
GET /v1/glucose/link-suggestion?member_id&measured_at&context   glucose_link_suggest (sugar)
    -> LinkSuggestionOut {link: {local_date, meal_slot_id, slot_label_key, slot_custom_label} | null}
```

- [ ] **Step 1: Write the failing tests.**
  - `test_links.py`:
    - `test_after_meal_auto_links_lunch` (`link` omitted; source `auto`)
    - `test_null_link_means_none`
    - `test_user_link_kept_on_measured_at_change`
    - `test_auto_link_recomputed_on_edit`
    - `test_context_change_to_random_clears_link`
    - `test_link_not_allowed_for_fasting` (`reason` context) and `test_link_date_more_than_one_day_away` (`reason` date)
    - `test_foreign_slot_refused`, `test_archived_slot_without_entries_refused`, `test_archived_slot_with_entries_ok`
    - `test_meal_without_items_flagged` (entries deleted after linking → `meal_has_items` false, link kept)
  - `test_link_suggestion.py`: `test_suggestion_matches_fixture_window`, `test_no_candidate_returns_null_link`, `test_needs_health_data`.
- [ ] **Step 2: Run** `uv run pytest tests/api/glucose -q` → FAIL.
- [ ] **Step 3: Implement** (with `error.glucose_link_not_allowed` in en, hi, mr).
- [ ] **Step 4: Run** → PASS; full suite PASS.
- [ ] **Step 5: Commit** `feat(api): link a glucose reading to a diary meal`.

---

### Task 14 (API + shared): Carb guide in settings, `sugar_day_get`, i18n, contract

Use the `api-endpoint` skill. Spec: 5.1, 6.1, 6.2, 12.4 (`sugar_day_get`, settings `carb_guide`), 14.6 (Q6). Rulings H20, H21.

**Files:**
- Create: `apps/api/app/features/sugar/timeline.py`, `apps/api/tests/api/sugar/{test_carb_guide,test_day}.py`
- Modify: `apps/api/app/features/sugar/{schemas,service,router}.py`, `glucose.yaml` (`carb_guide: {min_g: 5, max_g: 200}`, bounds only, no default), the clinician sheet, `apps/api/tests/api/sugar/test_invariance.py` (with guides), `packages/i18n/*`, `NATIVE_REVIEW.md` ("Plan 13 slice S2"), the contract (generated)

**Interfaces:**
- Consumes: `diary.service.get_day`; Task 13 `link_out`; Task 4 `GlucoseOut` builder.
- Produces:

```text
PUT /v1/sugar/settings body gains  carb_guide?: {enabled, same_for_all_g?, per_slot?: [{meal_slot_id, grams}]}
    enabled=true needs exactly one of same_for_all_g / per_slot (else validation_error); grams 5-200 (else 422 carb_guide_out_of_range);
    a slot not the member's -> meal_slot_not_found; enabled=false deletes the rows (H21)
SugarSettingsOut gains  carb_guide: {enabled, per_slot: [{meal_slot_id, grams}]}      # never pre-filled
DELETE /v1/sugar/settings also deletes the guide rows and sets carb_guide_enabled = false
GET /v1/sugar/day?member_id&date   sugar_day_get (sugar) -> SugarDayOut
SugarDayOut {member_id, date, today, timezone, items: (MealItem | ReadingItem)[], carbs_day: {total_g|null, incomplete},
             numbers_hidden, pending_clinician_review: true}
MealItem {kind: "meal", meal_slot_id, label_key, custom_label, first_at, last_at, entries: MealOut[],
          carbs: {total_g|null, incomplete}, carb_guide_g: number|null, readings_linked: uuid[]}
ReadingItem {kind: "reading", reading: GlucoseOut}
```

  - `timeline.py`: `async def build_day(session, member, day, settings) -> SugarDayOut`. A meal item exists for each slot with at least one entry that day. Carbs come from that slot's `totals.carbs_g` and `incomplete.carbs_g` (identical to `diary_day_get`). `readings_linked` lists live readings with `linked_local_date = day` and that slot. Sort per H20. Under `hide_all`, every carbs value and `carb_guide_g` are null. 422 `date_in_future`.
  - Dart and TS: the union is a discriminated `kind` (check what the generators emit; if a `oneOf` is awkward, emit one `TimelineItem` model with `kind` and nullable `meal` / `reading` objects instead, and record the ruling).
- New keys (en drafts): `sugar.timeline.title` "Your day"; `sugar.meal.carbs` "{grams} g carbs"; `sugar.meal.carbs_incomplete` "At least {grams} g carbs. Some items have no carb value."; `sugar.meal.carbs_hidden` "Carbs hidden by your number settings"; `sugar.meal.guide_of` "{grams} g of your {guide} g guide"; `sugar.meal.guide_over` "{grams} g · your guide is {guide} g"; `sugar.meal.guide_of_incomplete` "At least {grams} g of your {guide} g guide"; `sugar.meal.readings_linked` "{count, plural, one {{count} reading} other {{count} readings}} linked"; `sugar.link.{linked_to,change,none,meal_empty,pick}`; `sugar.settings.{carb_guide,carb_guide_help,carb_guide_same,carb_guide_per_slot}` (spec text; no number in any of them); `home.card.sugar_latest.title`, `home.card.meal_carbs.title`; errors `glucose_link_not_allowed` (Task 13), `carb_guide_out_of_range`.

- [ ] **Step 1: Write the failing tests.**
  - `test_carb_guide.py`: `test_guide_off_for_new_member` (Q6), `test_same_for_all_writes_every_active_slot`, `test_per_slot`, `test_bounds`, `test_disable_deletes_rows`, `test_yaml_has_no_suggested_grams`, `test_put_without_carb_guide_leaves_it`.
  - `test_day.py`:
    - `test_carbs_identical_to_diary_day` (the diary fixture week: each meal's carbs equal `diary_day_get` slot totals)
    - `test_incomplete_meal_carbs_flagged`
    - `test_items_sorted_meal_first_on_tie`
    - `test_readings_linked_across_midnight`
    - `test_deleted_reading_not_in_day_or_links`
    - `test_hide_all_nulls_carbs_keeps_glucose`
    - `test_guide_only_when_enabled`
    - `test_future_date_422`, `test_needs_health_data`
  - `test_invariance.py` extended with carb guides.
- [ ] **Step 2: Run** `uv run pytest tests/api/sugar -q` → FAIL.
- [ ] **Step 3: Implement**; keys and NATIVE_REVIEW flags ("guide" must not read as a prescription; "over" wording neutral); regenerate i18n, ARB and the contract.
- [ ] **Step 4: Run** the full checks as Task 5 Step 4 → PASS.
- [ ] **Step 5: Commit** `feat(api): sugar day timeline with carbs per meal and an optional carb guide`, `feat(i18n): sugar control slice S2`, `chore(contract): sugar timeline and links`.

---

### Task 15 (Android): Day timeline, link control, meal carbs, guide, Home cards *(parallel with Task 16)*

Use the `flutter-feature` skill. Spec: 5.1, 5.2, 6.1, 6.2, 13.2 (screens 2, 3, 9), 13.3. Rulings H19–H21, H25.

**Files:**
- Create: `apps/app/lib/features/sugar/presentation/{day_timeline.dart, meal_card.dart, link_control.dart, carb_guide_settings.dart}`, `apps/app/lib/features/home/presentation/cards/{sugar_latest_card.dart, meal_carbs_card.dart}`, `apps/app/test/features/sugar/{day_timeline_test.dart, link_control_test.dart, carb_guide_test.dart}`, `apps/app/test/features/home/sugar_cards_test.dart`
- Modify: `sugar_screen.dart` (today's timeline replaces the S1 day list), `reading_sheet.dart` (link control), `glucose_sync.dart` (send `link` per `linkChoice`), `sugar_settings_screen.dart` (carb guide), `mode_layouts.dart`, `layouts.json` (hunk below), `test_mode_layouts.py`

**Interfaces:**
- `layouts.json` hunk (identical in Task 16): `modes.health_condition.home_cards` = `["sugar_latest", "meal_carbs", "today_sugar_salt", "claims_tip", "not_covered", "recent_scans"]`.
- **Timeline:** a date switcher (back from `today`, never forward); `MealItem` cards (slot name from `labelKey` or `customLabel` as typed, entries with the diary entry tile, carbs per H20 copy, guide text when `carbGuideG` is set, `sugar.meal.readings_linked`); `ReadingItem` rows; API order unchanged. Tap a meal → its linked readings; tap a reading → edit sheet. Delete → undo snackbar.
- **Link control** (sheet, for before/after meal): on time or context change, `glucoseLinkSuggest` → "Linked to {meal} · Change" / "No link"; Change opens the day's meals (and the previous day's after midnight). Saving sends `link` omitted (auto, unchanged suggestion), `null` (No link) or the picked meal. Offline: `linkChoice` stored in the queue.
- **Carb guide settings:** off by default; on → an **empty** field ("same for all meals") or per-slot fields; no placeholder number.
- **Home cards:** `sugar_latest` (latest reading in the last 90 days via `glucoseList`, else `sugar.empty`), `meal_carbs` (today's `SugarDayOut` meals with carbs; hidden carbs copy under `hide_all`).

- [ ] **Step 1: Write the failing tests.**
  - `day_timeline_test.dart`: `renders API order unchanged`, `incomplete carbs shows at least`, `guide over is neutral text no warning icon`, `hide_all shows carbs hidden copy and still shows glucose`, `custom slot label shown as typed`.
  - `link_control_test.dart`: `suggestion shown and changeable`, `no link sends null`, `unchanged suggestion omits link`, `offline keeps link choice`.
  - `carb_guide_test.dart`: `off by default with empty field`, `no number prefilled anywhere`, `out of range maps error`.
  - `sugar_cards_test.dart`: `latest card`, `meal carbs card`, `cards only in health_condition`.
  - `no_verdict_tokens_test.dart` still green over the new files.
- [ ] **Step 2: Run them** to verify they fail. **Step 3: Implement.** **Step 4: Run** `dart format --set-exit-if-changed lib test && flutter analyze && flutter test` → PASS.
- [ ] **Step 5: Commit** `feat(app): sugar day timeline, meal links, carbs and carb guide`.

---

### Task 16 (Web): Day timeline, link control, meal carbs, guide, Home cards, e2e *(parallel with Task 15)*

Use the `web-feature` skill.

**Files:**
- Create: `apps/web/src/features/sugar/components/{DayTimeline.tsx, MealCard.tsx, LinkControl.tsx, CarbGuideSettings.tsx}`, `apps/web/src/features/home/components/cards/{SugarLatestCard.tsx, MealCarbsCard.tsx}`, tests, `apps/web/e2e/sugar-timeline.spec.ts`
- Modify: `SugarView.tsx`, `ReadingDialog.tsx`, `SugarSettings.tsx`, `HomeView.tsx`, `layouts.ts`, `layouts.json` (identical hunk), `stub-api.mjs`

**Interfaces:** the Task 15 behaviour, online-only.

- [ ] **Step 1: Write the failing tests:** the Task 15 cases (no offline). Plus `e2e/sugar-timeline.spec.ts`: log lunch in the Diary; add an after-meal reading 2 h later → "Linked to Lunch"; the timeline shows lunch with its carbs, then the reading; Change → No link; turn on a 45 g guide → "38 g of your 45 g guide"; Hide all numbers → carbs hidden, glucose shown.
- [ ] **Step 2: Run them** to verify they fail. **Step 3: Implement.** **Step 4: Run** `pnpm lint && npx tsc --noEmit && pnpm test && pnpm e2e` → PASS.
- [ ] **Step 5: Commit** `feat(web): sugar day timeline, meal links, carbs and carb guide`.

---

### Task 17: Slice-S2 gate

**Files:** `docs/FEATURE_PARITY.md` (F28 → 🟡), `CONTEXT.md` (migration 0015), this plan.

- [ ] **Step 1: Run everything** as Task 10 Step 1, plus `generate_sugar_link_expectations --check`.
- [ ] **Step 2: Dispatch** `nutrition-safety-reviewer`. Scope: link windows and the midnight case; auto versus user links (H19); carbs equal to the diary and the unknown rule; the guide (Q6: off, no number anywhere, neutral "over" wording, never a target); `hide_all` on the timeline and the Home cards; no verdict colours; invariance with guides.
- [ ] **Step 3: Fix** blocking findings with tests; re-run Step 1.
- [ ] **Step 4: Commit** `docs: Plan 13 slice S2 parity, context and review`.

---

## Slice S3: patterns

### Task 18 (API, engine): Pure statistics, stats fixtures *(may start after Task 2)*

Use the `scoring-rule` skill. Spec: 5.4, 14.2. Rulings H9, H11–H13.

**Files:**
- Create: `apps/api/tests/unit/scoring/test_glucose_stats.py`, `apps/api/scripts/generate_sugar_stats_expectations.py`, `packages/test-fixtures/sugar/stats/{inputs,expected}/*.json`
- Modify: `glucose.py`, `glucose.yaml`, the clinician sheet, `packages/test-fixtures/README.md`

**Interfaces:**
- YAML:

```yaml
pattern:
  min_readings_per_window: 5
  windows:                       # local time, start inclusive, end exclusive (minutes)
    - {code: late_night,    start: 0,    end: 240}
    - {code: early_morning, start: 240,  end: 480}
    - {code: morning,       start: 480,  end: 720}
    - {code: afternoon,     start: 720,  end: 960}
    - {code: evening,       start: 960,  end: 1200}
    - {code: night,         start: 1200, end: 1440}
within_range: {min_readings: 10}
summary: {min_days: 7, max_days: 92}
```

- Produces:

```python
@dataclass(frozen=True, slots=True)
class ReadingPoint: local_date: date; local_minute: int; value_mgdl: Decimal; context: str; after_meal_timing: str | None
@dataclass(frozen=True, slots=True)
class Stats: n: int; mean: Decimal; sd: Decimal | None; median: Decimal; q1: Decimal; q3: Decimal; min: Decimal; max: Decimal  # mg/dL, unrounded
def describe(values: Sequence[Decimal]) -> Stats | None              # None when empty; sd None when n < 2 (sample SD)
def summary_by_context(points) -> list[tuple[str, str | None, Stats]]   # order: fasting, before_meal, after_meal by timing
                                                                       # (about_1h, about_2h, not_sure), bedtime, random; empty groups omitted
@dataclass(frozen=True, slots=True)
class WindowStats: code: str; start: int; end: int; n: int; insufficient: bool; median: Decimal | None; q1: Decimal | None; q3: Decimal | None
def pattern_by_window(points, cfg=None) -> list[WindowStats]          # all six windows, always
WithinStatus = Literal["ready", "no_range", "too_few_readings"]
@dataclass(frozen=True, slots=True)
class WithinShare: below: int; within: int; above: int; total: int; pct_below: int; pct_within: int; pct_above: int
def within_range_share(points, user_range: UserRange | None, cfg=None) -> tuple[WithinStatus, WithinShare | None]
def display_stats(s: Stats, unit: GlucoseUnit, cfg=None) -> dict[str, Decimal | int | None]   # H9 rounding; sd scaled
```

- Fixtures (`inputs`: `{unit, range: {low_mgdl, high_mgdl} | null, readings: [ReadingPoint]}`; `expected`: the `SugarSummaryOut` statistics blocks, generated): `four_values_hand` (100, 110, 120, 130 mg/dL), `odd_count`, `even_with_ties`, `single_reading` (sd null, q1 = q3 = value), `mmol_display`, `after_meal_timing_split`, `window_edges` (minutes 239, 240, 1439, 0), `window_insufficient` (4 readings), `frozen_minutes_dst_zone` (readings written in `Europe/London` across the DST change keep their minutes), `within_no_range`, `within_too_few_9`, `within_boundaries` (values equal to low and high count as within), `pct_largest_remainder` (one each → 34 within, 33 below, 33 above).

- [ ] **Step 1: Write the failing tests:**

```python
def test_four_values_hand():
    s = describe([D(100), D(110), D(120), D(130)])
    assert (s.mean, s.median, s.q1, s.q3) == (D(115), D(115), D("107.5"), D("122.5"))
    assert round(s.sd, 4) == D("12.9099")              # sqrt(500/3); displayed 13 mg/dL, 0.7 mmol/L
def test_single_reading_sd_none():
def test_quartile_method_is_inclusive():               # equals statistics.quantiles(method="inclusive")
def test_windows_edges_and_insufficient():
def test_within_needs_range_and_ten():
def test_within_bounds_inclusive():
def test_pct_sums_to_100_largest_remainder():
def test_no_cv_or_score_exported():                    # glucose.py has no cv/variability/score/estimate/forecast names
def test_stats_fixtures():                             # packages/test-fixtures/sugar/stats
```

- [ ] **Step 2: Run** → FAIL. **Step 3: Implement**; the script with `--write`. **Step 4: Run** → PASS; `--check` → no diff.
- [ ] **Step 5: Commit** `feat(scoring): descriptive glucose statistics and time-of-day windows`.

---

### Task 19 (API + shared): `sugar_summary_get`, i18n, contract

Use the `api-endpoint` skill. Spec: 5.4, 12.4 (`sugar_summary_get`). Rulings H11–H13.

**Files:**
- Create: `apps/api/app/features/sugar/summary.py`, `apps/api/tests/api/sugar/test_summary.py`
- Modify: `apps/api/app/features/sugar/{schemas,router}.py`, `packages/i18n/*`, `NATIVE_REVIEW.md` ("Plan 13 slice S3"), the contract

**Interfaces:**
- Consumes: Task 18 functions; Task 3 `user_range`, `preferred_unit`.
- Produces:

```text
GET /v1/sugar/summary?member_id&from&to   sugar_summary_get (sugar)
    7-92 days inclusive (date_range_too_short / date_range_too_long); to > today -> date_in_future
SugarSummaryOut {member_id, from, to, unit, readings, days_with_readings, first_date|null, last_date|null,
  overall: StatsOut|null, by_context: [{context, after_meal_timing|null, stats: StatsOut}],
  windows: [{code, start "HH:MM", end "HH:MM", n, insufficient, median|null, q1|null, q3|null}],
  within_range_status: "ready"|"no_range"|"too_few_readings",
  within_range: {low, high, unit, below, within, above, total, pct_below, pct_within, pct_above}|null,
  pending_clinician_review: true}
StatsOut {n, mean, sd|null, median, q1, q3, min, max}     # display unit, H9 rounding
```

  - `summary.py`: `async def build_summary(session, member, frm, to, today) -> SugarSummaryOut` (live readings only, by frozen `local_date`). Task 25 adds `labs_latest`.
- New keys (en drafts): `sugar.patterns.title` "Patterns"; `sugar.patterns.range.{7,14,30,90}` "{count} days"; `sugar.patterns.readings_days` (spec plural); `sugar.patterns.not_enough` "Not enough readings"; `sugar.patterns.{median,middle_half,lowest,highest,average}` (spec text); `sugar.patterns.sd` "Spread (standard deviation)"; `sugar.patterns.sd_help` "How far readings usually sit from the average. Shown as information only."; `sugar.patterns.overall` "All readings"; `sugar.patterns.window.{late_night,early_morning,morning,afternoon,evening,night}`; `sugar.patterns.window_range` "{start}–{end}"; `sugar.patterns.within_share` "{within} of {total} readings were within the range you set ({low}–{high} {unit})."; `sugar.patterns.within_none` "Set your own range in Sugar settings to see this."; `sugar.patterns.within_few` "This shows once you have at least 10 readings in the period."; `sugar.patterns.table` "Table view"; error `date_range_too_short`.

- [ ] **Step 1: Write the failing tests** (`test_summary.py`):
  - `test_matches_stats_fixtures` (seed each input, compare with `expected/`)
  - `test_summary_ignores_deleted`
  - `test_no_range_no_within_share` (Q4) and `test_too_few_readings_status`
  - `test_mmol_display_and_sd_scaled`
  - `test_range_bounds_7_92` and `test_future_to_422`
  - `test_response_has_no_cv_score_or_estimate_fields` (schema walk)
  - `test_needs_health_data`
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement**; keys with NATIVE_REVIEW flags (that "spread" carries no judgement); regenerate i18n, ARB, contract. **Step 4: Run** the full checks as Task 5 Step 4 → PASS.
- [ ] **Step 5: Commit** `feat(api): sugar patterns summary`, `feat(i18n): sugar control slice S3`, `chore(contract): sugar summary`.

---

### Task 20 (Android): Patterns screen *(parallel with Task 21)*

Use the `flutter-feature` skill. Spec: 5.4, 13.1 (charts have tables), 13.2 (screen 4). Rulings H11, H12.

**Files:**
- Create: `apps/app/lib/features/sugar/presentation/{patterns_screen.dart, pattern_chart.dart, stats_table.dart}`, `apps/app/test/features/sugar/{patterns_screen_test.dart, pattern_chart_test.dart, stats_fixture_test.dart}`
- Modify: `sugar_screen.dart` (entry), the router

**Interfaces:**
- Range chips 7, 14, 30, 90 days ending `today` (from `SugarDayOut.today`, never the device date).
- `readings_days` line; the overall and by-context table (n, average, spread, middle value, middle half `q1–q3`, lowest, highest), in the API's unit and values.
- `PatternChart` (`CustomPainter`): per window a band q1–q3 (`sugar.pattern-band`) and a median tick (`sugar.pattern-median`); an insufficient window greyed with `sugar.patterns.not_enough`; n under each window; no range lines unless the user set a range (then a thin neutral band labelled "your range"); a table view toggle with the same numbers.
- Within-range: the `within_share` sentence and a three-part neutral bar from `pct_*` when `ready`; otherwise `within_none` or `within_few`.
- `sugar.disclaimer` and `sugar.pending_review`.

- [ ] **Step 1: Write the failing tests:**
  - `stats_fixture_test.dart`: `renders every expected stats fixture value verbatim` (no client arithmetic).
  - `patterns_screen_test.dart`: `no within share without range`, `too few copy below ten`, `sd label and help shown, no judgement words`, `today comes from API`.
  - `pattern_chart_test.dart`: `insufficient window greyed with label`, `band and median use sugar tokens not verdict`, `table view has same numbers`, `no range band without user range`.
- [ ] **Step 2: Run them** to verify they fail. **Step 3: Implement.** **Step 4: Run** `dart format --set-exit-if-changed lib test && flutter analyze && flutter test` → PASS.
- [ ] **Step 5: Commit** `feat(app): sugar patterns`.

---

### Task 21 (Web): Patterns screen, e2e *(parallel with Task 20)*

Use the `web-feature` skill.

**Files:**
- Create: `apps/web/src/features/sugar/components/{PatternsView.tsx, PatternChart.tsx, StatsTable.tsx}`, `apps/web/src/app/[locale]/(app)/sugar/patterns/page.tsx`, tests, `apps/web/e2e/sugar-patterns.spec.ts`
- Modify: `SugarView.tsx` (link), `stub-api.mjs`

**Interfaces:** the Task 20 behaviour; `PatternChart` is inline SVG with `<title>` and an accessible table.

- [ ] **Step 1: Write the failing tests:** the Task 20 cases. Plus `e2e/sugar-patterns.spec.ts`: with the stub's 14-day fixture, switch 7 → 30 days; a greyed window shows "Not enough readings"; without a range the share is absent; set a range → the share sentence appears.
- [ ] **Step 2: Run them** to verify they fail. **Step 3: Implement.** **Step 4: Run** `pnpm lint && npx tsc --noEmit && pnpm test && pnpm e2e` → PASS.
- [ ] **Step 5: Commit** `feat(web): sugar patterns`.

---

### Task 22: Slice-S3 gate

**Files:** `docs/FEATURE_PARITY.md` (F29 → 🟡), `CONTEXT.md`, this plan.

- [ ] **Step 1: Run everything** as Task 10 Step 1, plus `generate_sugar_stats_expectations --check`.
- [ ] **Step 2: Dispatch** `nutrition-safety-reviewer`. Scope: the quartile method and hand checks; **the SD ruling H11** (brief versus spec §5.4: confirm it stays descriptive, or ask the user to drop it); the within-range wording (H12) and its gates; window edges and frozen minutes; no CV, score, estimate or forecast; neutral chart colours; table equivalents.
- [ ] **Step 3: Fix** blocking findings with tests; re-run Step 1.
- [ ] **Step 4: Commit** `docs: Plan 13 slice S3 parity, context and review`.

---

## Slice S4: lab log

### Task 23 (API, db): Migration 0016 `lab_results` *(parallel with Task 24)*

Use the `api-endpoint` skill. Spec: 7, 12.2 (`lab_results`). Rulings H1–H3.

**Files:**
- Create: `apps/api/alembic/versions/0016_sugar_lab_results.py`, `apps/api/app/features/labs/{__init__,models}.py`
- Modify: `apps/api/app/features/me/service.py` (`lab_results` per H3), `apps/api/tests/db/*`, `apps/api/tests/api/test_delete_me.py`

**Interfaces:**
- `lab_results`: `id`; `account_id`, `member_id` (composite FK); `test` text check in (`hba1c`, `fasting_glucose`, `total_cholesterol`, `ldl`, `hdl`, `triglycerides`); `taken_on` date; `value_canonical` numeric; `entered_value` numeric; `entered_unit` text check in (`pct`, `mmol_mol`, `mg_dl`, `mmol_l`) plus check `(test = 'hba1c') = (entered_unit in ('pct', 'mmol_mol'))`; `note` text NULL (1–200); `client_id` uuid NULL unique `(account_id, client_id)`; `deleted_at`; timestamps; indexes `(member_id, test, taken_on) WHERE deleted_at IS NULL` and the retention partial index; `_lock_down`. No range, band or estimate column exists.

- [ ] **Step 1: Write the failing tests:** RLS, grants; `test_lab_unit_matches_test`; `test_lab_test_closed_set`; `test_0016_upgrade_downgrade`; delete-me erases `lab_results` (including soft-deleted).
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat(api): migration 0016 lab results`.

---

### Task 24 (API, engine): Pure lab conversions, lab fixture, the no-estimate test *(parallel with Task 23; may start after Task 2)*

Use the `scoring-rule` skill. Spec: 7.1, 7.2, 14.1 (labs), 14.2 (no estimate). Rulings H7–H9.

**Files:**
- Create: `apps/api/tests/unit/scoring/test_glucose_labs.py`, `apps/api/tests/unit/test_no_estimate.py`, `apps/api/scripts/generate_sugar_lab_expectations.py`, `packages/test-fixtures/sugar/labs.json`
- Modify: `glucose.py`, `glucose.yaml`, `thresholds.yaml` (`section_sources.labs_units` → `ngsp_ifcc_master_equation`, `pubchem_cholesterol_5997`, `smartnutri_working_values`), the clinician sheet, `packages/test-fixtures/README.md`

**Interfaces:**
- YAML:

```yaml
labs:
  taken_on_max_back_years: 10
  tests:
    hba1c:             {canonical: pct,   units: [pct, mmol_mol], hard: {min: 3, max: 20},   confirm: {min: 4, max: 15},
                        ngsp_slope: 0.09148, ngsp_intercept: 2.152}        # ngsp.org master equation (verified 2026-11-08)
    fasting_glucose:   {canonical: mg_dl, units: [mg_dl, mmol_l], hard: {min: 20, max: 600}, confirm: {min: 40, max: 400}, factor: glucose}
    total_cholesterol: {canonical: mg_dl, units: [mg_dl, mmol_l], hard: {min: 50, max: 600}, confirm: {min: 100, max: 400}, factor: 38.67}
    ldl:               {canonical: mg_dl, units: [mg_dl, mmol_l], hard: {min: 10, max: 500}, confirm: {min: 30, max: 300}, factor: 38.67}
    hdl:               {canonical: mg_dl, units: [mg_dl, mmol_l], hard: {min: 5, max: 200},  confirm: {min: 15, max: 120}, factor: 38.67}
    triglycerides:     {canonical: mg_dl, units: [mg_dl, mmol_l], hard: {min: 10, max: 5000}, confirm: {min: 30, max: 1000},
                        factor: 88.57}   # [unverified] conventional; PubChem triolein 885.4 g/mol gives 88.54
```

  (The confirm bands other than HbA1c are SmartNutri working values, PENDING CLINICIAN REVIEW.)
- Produces:

```python
LabTest = Literal["hba1c", "fasting_glucose", "total_cholesterol", "ldl", "hdl", "triglycerides"]
LabUnit = Literal["pct", "mmol_mol", "mg_dl", "mmol_l"]
class LabInputError(Exception): code: str; details: dict  # lab_unit_not_allowed | lab_precision | lab_out_of_range | lab_needs_confirm
def lab_to_canonical(test: LabTest, value: Decimal, unit: LabUnit, *, confirm_unusual: bool, cfg=None) -> Decimal
    # hba1c canonical pct (2 dp); others mg/dL (1 dp); limits checked on canonical
def lab_display(test, canonical: Decimal, unit: LabUnit, *, entered: tuple[Decimal, LabUnit] | None = None, cfg=None) -> Decimal
    # entered value exactly when units match; else converted and rounded per H9
def lab_other_unit(test: LabTest, unit: LabUnit) -> LabUnit
def lab_change(test, latest: Decimal, previous: Decimal, unit: LabUnit, cfg=None) -> Decimal
    # both canonical values converted to `unit` unrounded, subtracted, rounded per H9
```

- `labs.json` cases: `hba1c_7_0_pct` → 53 mmol/mol; `hba1c_53_mmol` → 7.0 %; `hba1c_48_mmol` → 6.5 %; `chol_5_17_mmol` → canonical 199.9, displayed 200 mg/dL; `chol_200_mgdl` → 5.17 mmol/L; `tg_1_7_mmol` → 150.6 mg/dL; `tg_150_mgdl` → 1.69 mmol/L; `fasting_glucose_mmol` (uses 18.016); errors `hba1c_in_mg_dl` (`lab_unit_not_allowed`), `hba1c_2_9` (`lab_out_of_range`), `hba1c_16` (`lab_needs_confirm`), `ldl_3_123_mmol` (`lab_precision`); `change_hba1c` (7.2 % then 6.8 % → −0.4 %).
- `test_no_estimate.py` (`test_no_estimate_anywhere`): walks every schema and property name in `packages/api-contract/openapi.json`, every `sugar.*` i18n key and value (en), and every public name in `glucose.py`; fails on `estimat`, `ea1c`, `gmi`, `a1c_estimate`, `predict`, `forecast`. A second test asserts no function in `glucose.py` takes `ReadingPoint` values and returns a `pct`/HbA1c-typed value (signature check by annotation).

- [ ] **Step 1: Write the failing tests:** `test_labs_fixture()`, `test_hba1c_round_trip_exact` (Hypothesis over 1-dp % in 4.0–15.0: % → mmol/mol → % returns the entry), `test_lipid_factors_from_yaml`, `test_allowed_units_per_test`, `test_no_estimate_anywhere`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement**; the script with `--write`. **Step 4: Run** → PASS; `--check` → no diff.
- [ ] **Step 5: Commit** `feat(scoring): lab unit conversions as entered, never estimated`.

---

### Task 25 (API + shared): Labs routes, trend, retention, summary labs, i18n, contract

Use the `api-endpoint` skill. Spec: 7.2, 12.4 (`labs_*`), 14.6 (Q16). Rulings H14, H18.

**Files:**
- Create: `apps/api/app/features/labs/{schemas,service,router}.py`, `apps/api/tests/api/labs/{test_crud,test_trend,test_consent}.py`
- Modify: `apps/api/app/main.py`, `apps/api/app/core/{config,ratelimit}.py` (`lab_writes` 50/day), `apps/api/app/jobs/retention.py` (labs purge), `apps/api/app/features/sugar/{summary,schemas}.py` (`labs_latest`), `apps/api/tests/api/sugar/test_invariance.py` (with labs), `packages/i18n/*`, `NATIVE_REVIEW.md` ("Plan 13 slice S4"), the contract

**Interfaces:**

```text
LabIn {member_id?, test, value, unit, taken_on (date), note?, confirm_unusual = false, client_id?}
LabPatch {value?, unit? (both or neither), taken_on?, note?, confirm_unusual = false}      # test is not editable
LabOut {id, member_id, test, taken_on, value_canonical, entered {value, unit}, display {value, unit},
        converted {value, unit} | null, note, created_at, updated_at, deleted_at}
POST   /v1/labs                labs_create          (sugar; lab_writes) 201 / 200 on repeat client_id
GET    /v1/labs?member_id&test&limit&cursor   labs_list (sugar) newest taken_on first
GET    /v1/labs/deleted        labs_deleted_list    (sugar)
PATCH  /v1/labs/{id}           labs_update          (sugar; lab_writes)
DELETE /v1/labs/{id}           labs_delete          (sugar_erase) -> 200 {id, deleted_at, restore_until}
POST   /v1/labs/{id}/restore   labs_restore         (sugar; lab_writes); 410 lab_restore_expired
GET    /v1/labs/trend?member_id&test   labs_trend_get (sugar)
       -> {test, unit, points: [{id, taken_on, display {value, unit}, entered {value, unit}}] (oldest first),
           change_since_previous: {value, unit, previous_on} | null}
           unit = the entered unit of the newest point (H7/H9); null change with fewer than 2 points
SugarSummaryOut gains labs_latest: [{test, taken_on, display, converted}]   # latest live result per test inside [from, to]
```

  - `taken_on` in the future (account local today) → `taken_on_in_future`; more than 10 years back → `taken_on_too_old`. `display` is the entered unit; `converted` the other unit.
  - Retention purges lab rows with `deleted_at` older than 30 days (`RetentionResult.labs_purged`).
- New keys (en drafts): `sugar.labs.title` "Lab results"; `sugar.labs.add`; `sugar.labs.test.{hba1c,fasting_glucose,total_cholesterol,ldl,hdl,triglycerides}`; `sugar.labs.unit.{pct,mmol_mol}` "% / mmol/mol"; `sugar.labs.taken_on` "Test date"; `sugar.labs.converted` "{value} {unit} (converted)"; `sugar.labs.change` "Change since your previous result: {change} {unit} (on {date})"; `sugar.labs.as_entered` "As you entered it from your lab report"; `sugar.labs.no_ranges` "Labs print their own reference ranges. SmartNutri shows your values only."; `sugar.labs.deleted` "Lab result deleted."; `sugar.labs.empty`; `sugar.labs.latest` "Latest lab results"; errors `lab_unit_not_allowed`, `lab_out_of_range`, `lab_needs_confirm`, `lab_precision`, `lab_not_found`, `lab_restore_expired`, `taken_on_in_future`, `taken_on_too_old`.

- [ ] **Step 1: Write the failing tests.**
  - `test_crud.py`: `test_create_matches_lab_fixture`, `test_unit_not_allowed_for_test`, `test_confirm_then_save`, `test_taken_on_future_and_ten_years`, `test_client_id_repeat`, `test_test_not_patchable`, `test_deleted_lab_hidden_and_purged` (with the retention job), `test_restore_day_30_then_410`, `test_out_has_no_range_band_or_estimate_field`.
  - `test_trend.py`: `test_points_oldest_first_in_newest_unit`, `test_change_since_previous` (−0.4 %), `test_single_point_no_change`, `test_summary_labs_latest_in_period`.
  - `test_consent.py`: `test_labs_need_health_data_except_delete`, `test_gate_before_rate_limit`, `test_minor_refused`.
  - `test_invariance.py` extended with labs.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement**; keys with NATIVE_REVIEW flags (test names as Indian lab reports print them; "HbA1c" kept in Latin script); regenerate i18n, ARB, contract. **Step 4: Run** the full checks as Task 5 Step 4, plus `test_no_estimate.py` (now including the regenerated `openapi.json`) → PASS.
- [ ] **Step 5: Commit** `feat(api): lab results log with trends`, `feat(i18n): sugar control slice S4`, `chore(contract): labs`.

---

### Task 26 (Android): Labs list, form, trend, queue v8 *(parallel with Task 27)*

Use the `flutter-feature` skill. Spec: 7, 13.2 (screen 6, recently deleted). Ruling H27.

**Files:**
- Create: `apps/app/lib/features/labs/data/{labs_repository.dart, labs_sync.dart}`, `apps/app/lib/features/labs/presentation/{labs_screen.dart, lab_form_sheet.dart, lab_trend_view.dart, labs_providers.dart}`, `apps/app/test/features/labs/{labs_screen_test.dart, lab_form_test.dart, lab_trend_test.dart, labs_fixture_test.dart}`, `apps/app/test/core/storage/meal_queue_v8_migration_test.dart`
- Modify: `meal_queue.dart` (v8 `PendingLabs {clientId, memberId?, test, value, unit, takenOn, note?, confirmUnusual, status}`), `recently_deleted_screen.dart` (labs too, with `labsRestore`), `sugar_screen.dart` (entry), the router, `no_verdict_tokens_test.dart` (covers `features/labs`)

**Interfaces:**
- **Labs list:** grouped by test, latest display value and date, `sugar.labs.as_entered`, `sugar.labs.no_ranges`.
- **Form:** test picker; unit chips from the test's allowed units only; value; date (not future); note. `lab_needs_confirm` → confirm with both units (from `details`) → resend.
- **Trend:** points only (no connecting line, no band, no colour judgement) and a table; `sugar.labs.change` when `changeSincePrevious` is set; `converted` shown as "(converted)".
- Offline: queue v8; `consent_required` keeps the row queued.

- [ ] **Step 1: Write the failing tests:** `labs_fixture_test.dart` (display rows of `sugar/labs.json` render verbatim), `lab_form_test.dart` (`units offered per test only`, `needs confirm resends`, `future date blocked`), `lab_trend_test.dart` (`points without connecting lines`, `change line`, `no range or band drawn`), `labs_screen_test.dart` (`grouped latest`, `no ranges note`), queue v8 migration and `queued lab kept on consent_required`, recently deleted with labs.
- [ ] **Step 2: Run them** to verify they fail. **Step 3: Implement**, then `build_runner`. **Step 4: Run** `dart format --set-exit-if-changed lib test && flutter analyze && flutter test` → PASS.
- [ ] **Step 5: Commit** `feat(app): lab results log and trends`.

---

### Task 27 (Web): Labs list, form, trend, e2e *(parallel with Task 26)*

Use the `web-feature` skill.

**Files:**
- Create: `apps/web/src/features/labs/{api/labs.ts, hooks/useLabs.ts, components/{LabsView.tsx, LabForm.tsx, LabTrend.tsx}}`, `apps/web/src/app/[locale]/(app)/sugar/labs/page.tsx`, tests, `apps/web/e2e/sugar-labs.spec.ts`
- Modify: `RecentlyDeleted.tsx` (labs), `SugarView.tsx` (link), `noVerdictTokens.test.ts` (covers `features/labs`), `stub-api.mjs`

**Interfaces:** the Task 26 behaviour, online-only; `LabTrend` is SVG points plus a table.

- [ ] **Step 1: Write the failing tests:** the Task 26 component cases (no offline). Plus `e2e/sugar-labs.spec.ts`: add HbA1c 7.2 % then 6.8 % → "53 mmol/mol (converted)" style line and "Change since your previous result: -0.4 %"; HbA1c offers only % and mmol/mol; delete → Recently deleted lists it → Restore.
- [ ] **Step 2: Run them** to verify they fail. **Step 3: Implement.** **Step 4: Run** `pnpm lint && npx tsc --noEmit && pnpm test && pnpm e2e` → PASS.
- [ ] **Step 5: Commit** `feat(web): lab results log and trends`.

---

### Task 28: Slice-S4 gate

**Files:** `docs/FEATURE_PARITY.md` (F30 → 🟡), `CONTEXT.md` (migration 0016; USER: clinician sign-off on the lab factors, the triglyceride factor and the confirm bands), this plan.

- [ ] **Step 1: Run everything** as Task 10 Step 1, plus `generate_sugar_lab_expectations --check`.
- [ ] **Step 2: Dispatch** `nutrition-safety-reviewer`. Scope: the NGSP equation and lipid factors (H7); units per test; no ranges, bands, derived values or estimates (`test_no_estimate.py`); points-only trends; consent and erasure; queue behaviour on withdrawal; copy.
- [ ] **Step 3: Fix** blocking findings with tests; re-run Step 1.
- [ ] **Step 4: Commit** `docs: Plan 13 slice S4 parity, context and review`.

---

## Slice S5: doctor report

### Task 29 (API): PDF engine decision, fonts, image, ADR 0027 *(parallel with Task 30)*

Spec: 8.1 (engine, fonts), 14.4 (Devanagari), R14. Ruling H24.

**Files:**
- Create: `apps/api/app/features/sugar/report/{__init__,pdf_engine}.py`, `apps/api/app/features/sugar/report/fonts/{NotoSans-Regular.ttf, NotoSans-Bold.ttf, NotoSansDevanagari-Regular.ttf, NotoSansDevanagari-Bold.ttf, OFL.txt, SOURCES.md}`, `apps/api/tests/unit/sugar/test_pdf_engine.py`, `docs/adr/0027-sugar-report-pdf-engine.md`
- Modify: `apps/api/pyproject.toml` (`weasyprint`; dev `pypdf`, `fonttools`), `apps/api/uv.lock`, `apps/api/Dockerfile` (apt: `libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b` [verify the exact package set for the pinned WeasyPrint]), the API `AGENTS.md` (local prerequisite: `brew install pango` on macOS)

**Interfaces:**
- Produces:

```python
FONT_DIR: Path
def render_pdf(html: str) -> bytes                    # engine behind one function; no network, no file writes outside memory
def font_covers(text: str, language: Language) -> list[str]   # characters missing from the language's Noto font cmap (fontTools)
```

  - Fonts are loaded only from `FONT_DIR` through `@font-face` with `file://` URLs; WeasyPrint's `url_fetcher` refuses every other URL (no network fetch from templates).
- **Decision criteria** (all must hold for WeasyPrint, else switch `render_pdf` to fpdf2 + uharfbuzz with `set_text_shaping`, and record why):
  1. `render_pdf` works in the Docker image built with `docker build --build-context i18n=packages/i18n/messages apps/api` and locally.
  2. A sample in hi and mr (`स्वास्थ्य`, `क्षमता`, `ग्लूकोज़`, `रक्तातील साखर`, the `sugar.report.*` strings) renders with conjuncts and matras correctly. Check: render to PNG with `pdftoppm -r 110` and compare by eye against the same text in a browser; attach both images to the task report.
  3. Image size grows by at most 80 MB and a cold-start render of the sample takes under 3 s on the API's Cloud Run size [targets; measure and record the numbers].
- ADR 0027: the choice, the numbers measured, the fonts and their OFL licence, and the fallback path.

- [ ] **Step 1: Write the failing tests** (`test_pdf_engine.py`): `test_renders_en_hi_mr_sample` (bytes start with `%PDF`; `pypdf` reads one page), `test_fonts_embedded_are_noto` (every font in the PDF resources is a Noto subset), `test_font_covers_all_report_strings` (every `sugar.report.*` value in en, hi, mr: `font_covers(...) == []`), `test_no_network_fetch` (an `<img src="https://…">` in the HTML is refused, not fetched), `test_fonts_licence_present`.
- [ ] **Step 2: Run** `uv run pytest tests/unit/sugar/test_pdf_engine.py -q` → FAIL.
- [ ] **Step 3: Implement**; build the image; run criteria 1–3; write ADR 0027.
- [ ] **Step 4: Run** → PASS; `uv run pytest -q`.
- [ ] **Step 5: Commit** `feat(api): PDF engine with Noto fonts for en, hi and mr`.

---

### Task 30 (API): Report data, CSV writer, CSV goldens *(parallel with Task 29)*

Spec: 8.1, 8.3, 14.4 (CSV). Rulings H20, H23.

**Files:**
- Create: `apps/api/app/features/sugar/report/{data,csv_writer}.py`, `apps/api/tests/api/sugar/report/{test_data,test_csv}.py`, `apps/api/scripts/generate_sugar_report_expectations.py`, `packages/test-fixtures/sugar/report/{input.json, request_default.json, expected/en_mg_dl.csv, expected/en_mmol_l.csv, expected/hi_mg_dl.csv, expected/mr_mg_dl.csv}`
- Modify: `glucose.py` (`slot_carb_averages`), `glucose.yaml` (`report: {min_days: 7, max_days: 92}`), the stats fixtures (one `slot_carb_averages` case), `packages/test-fixtures/README.md` ("Doctor report")

**Interfaces:**
- Consumes: Task 4 readings, Task 14 `timeline.build_day` (per day), Task 19 `build_summary`, Task 25 labs; `core.i18n` for slot names.
- Produces:

```python
@dataclass(frozen=True, slots=True)
class SlotCarbAverage: meal_slot_id: UUID; days: int; average_g: Decimal | None; incomplete: bool   # known-total sum / days with entries
def slot_carb_averages(days: Sequence[Mapping[UUID, tuple[Decimal | None, bool]]]) -> list[SlotCarbAverage]
    # in glucose.py (pure): one mapping per day, slot id -> (known carbs total, incomplete); data.py builds it from SugarDayOut
@dataclass(frozen=True)
class ReportData:
    member_name: str | None; frm: date; to: date; timezone: str; unit: GlucoseUnit; language: Language
    generated_at: datetime; summary: SugarSummaryOut; days: list[SugarDayOut]; labs: list[LabOut]
    carb_averages: list[SlotCarbAverage]; carb_guide: dict[UUID, Decimal]; carbs_hidden: bool; include_notes: bool
async def build_report_data(session, member, frm, to, *, language, include_name, include_notes, today, settings) -> ReportData
    # 422 sugar_report_range (7-92 days), date_in_future, sugar_report_empty (no reading, meal or lab in range)
def write_csv(data: ReportData) -> bytes
    # UTF-8 BOM, RFC 4180, CRLF; columns exactly: record_type, local_date, local_time, timezone, value_mgdl_or_canonical,
    # display_value, display_unit, entered_value, entered_unit, context, after_meal_timing, linked_meal_slot, food_name,
    # carbs_g, carbs_incomplete, lab_test, note; rows ordered by local_date, local_time, record_type (glucose, meal_item, lab)
def neutralise(cell: str) -> str      # a user-text cell starting with = + - @ \t \r gets a leading apostrophe
```

  - CSV `note` is empty unless `include_notes`; no name column ever (H23); carbs columns empty under `hide_all`; slot names translated per `language`, custom labels as typed (through `neutralise`).
- `input.json`: one member, 14 days in `Asia/Kolkata`: readings in both units and all contexts, two meals a day (one with an unknown-carb quick add), a custom slot "Shaam ki chai", a range, a 45 g guide on lunch, two HbA1c results and a cholesterol result, one deleted reading and one deleted lab, a note `=HYPERLINK("http://x")`, and a reading on a 15th day outside the range. `request_default.json`: `{"format": "pdf", "language": "en", "include_name": false, "include_notes": false}` (clients send these defaults; dates are filled by the client).

- [ ] **Step 1: Write the failing tests.**
  - `test_data.py`: `test_range_7_92`, `test_empty_range_422`, `test_report_excludes_deleted`, `test_same_numbers_as_summary_and_day` (the report's summary equals `sugar_summary_get` and each day equals `sugar_day_get` for the fixture), `test_name_only_when_included`, `test_carbs_hidden_under_hide_all`, `test_other_member_never_included`.
  - `test_csv.py`: `test_csv_goldens_byte_exact` (the four files), `test_bom_and_crlf`, `test_formula_cells_neutralised`, `test_notes_only_when_included`, `test_no_name_column_even_with_include_name`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement**; generate the goldens with a pinned clock (`--write`). **Step 4: Run** → PASS; `--check` → no diff.
- [ ] **Step 5: Commit** `feat(api): doctor report data and CSV export`.

---

### Task 31 (API + shared): PDF renderer, `sugar_report_create`, snapshots, i18n, contract

Use the `api-endpoint` skill. Spec: 8.1, 8.2, 8.4 (rate limit), 12.4, 12.5 (Q13), 14.4, 14.6 (Q9, Q13). Rulings H14, H23, H29.

**Files:**
- Create: `apps/api/app/features/sugar/report/{pdf,router}.py`, `apps/api/app/features/sugar/report/templates/{report.html, report.css}`, `apps/api/tests/api/sugar/report/{test_pdf,test_route,test_consent,test_privacy}.py`, `packages/test-fixtures/sugar/report/expected/{en,hi,mr}.pdf.txt`
- Modify: `apps/api/app/main.py`, `apps/api/app/core/{config,ratelimit}.py` (`sugar_reports` 20/day), `scripts/generate_sugar_report_expectations.py` (PDF text), `packages/i18n/*`, `NATIVE_REVIEW.md` ("Plan 13 slice S5"), the contract

**Interfaces:**
- Consumes: Task 29 `render_pdf`, `font_covers`; Task 30 `build_report_data`, `write_csv`; `core.i18n` (every string by key; numbers via the report's unit).
- Produces:

```text
SugarReportIn {member_id?, from, to, format: "pdf"|"csv", language: "en"|"hi"|"mr", include_name = false, include_notes = false}
POST /v1/sugar/report   sugar_report_create
     dependencies, in order: report_gate (reads body.format: pdf -> terms + health_data; csv -> terms), limit("sugar_reports")
     200 application/pdf | text/csv; charset=utf-8, Content-Disposition attachment (H23), Cache-Control: no-store
     422 sugar_report_range, sugar_report_empty, date_in_future; 403 consent_required; 429 rate_limited
```

  - The member resolves with `check_minor = (format == "pdf")`. The PDF is rendered with `run_in_threadpool(render_pdf, html)`.
  - **PDF layout** (spec §8.2, without item 7): header (`sugar.report.title`, the date range, generated time and zone, the unit, the name only if `include_name`) and the subtitle line; summary (counts; the table by context with mean and SD; the within-range share only when `ready`, stating the range "as set by the user"; `labs_latest`); the time-of-day chart as inline SVG (median and quartile band, greyed insufficient windows, n per window); meals and carbs (per-slot averages with days, "at least" markers, the guide), or `sugar.report.carbs_hidden`; day tables (readings: time, value, context, timing, linked meal; meals: slot, items, carbs; notes only if `include_notes`); the lab table as entered with conversions; the footer on every page (`@page` margin box) with the page number.
  - Never in the PDF: an estimate, a score, a verdict, a colour on a reading, advice or LLM text.
- New keys (en drafts, H29): `sugar.report.title` "Glucose and food log"; `sugar.report.subtitle` "Information the user entered in SmartNutri. Not medical advice."; `sugar.report.footer` "Information, not medical advice. Values as entered by the user; meter and lab values are not checked by SmartNutri. Thresholds pending clinician review."; `sugar.report.{generated,period,unit,name,page}`; `sugar.report.section.{summary,pattern,meals,days,labs}`; `sugar.report.range_set_by_user` "Range set by the user: {low}–{high} {unit}"; `sugar.report.carbs_hidden` "Carbs are not shown because numbers are hidden in this account's settings."; `sugar.report.days_logged` "{count, plural, one {{count} day} other {{count} days}} with meals logged"; `sugar.report.{generate,format.pdf,format.csv,language,include_name,include_notes,csv_only_note,range.{14,30,90,custom},share,download,ready}`; errors `sugar_report_range`, `sugar_report_empty`.
- PDF snapshot: `expected/<lang>.pdf.txt` = `pypdf` text of the fixture report, NFC-normalised, whitespace collapsed, generated by the script and reviewed by hand once (the reviewer checks hi and mr read correctly).

- [ ] **Step 1: Write the failing tests.**
  - `test_pdf.py`: `test_pdf_text_snapshots_en_hi_mr`, `test_disclaimer_on_page_one_and_footer_every_page`, `test_font_coverage_no_tofu`, `test_no_estimate_score_or_colour_words` (extracted text has none of `estimat|score|verdict|red|green|danger|risk|control`), `test_name_absent_by_default`, `test_notes_absent_by_default`, `test_within_share_only_when_ready`.
  - `test_route.py`: `test_pdf_headers_no_store_attachment`, `test_csv_matches_golden`, `test_filename_has_no_name`, `test_rate_limited_20`, `test_nothing_stored` (row counts of every table and the storage listing unchanged after generating both formats).
  - `test_consent.py`: `test_csv_on_terms_after_withdrawal` (Q13), `test_pdf_refused_after_withdrawal_no_quota_used`, `test_screens_still_gated_after_withdrawal`, `test_minor_pdf_refused_csv_allowed`.
  - `test_privacy.py`: `test_other_account_never_in_report`, `test_report_body_not_in_logs`.
- [ ] **Step 2: Run** `uv run pytest tests/api/sugar/report -q` → FAIL.
- [ ] **Step 3: Implement**; keys in en, then hi and mr (NATIVE_REVIEW flags: the report reads as a record, not a diagnosis; Marathi digits stay Latin); regenerate i18n, ARB, the snapshots and the contract. If the generated Dart or TS client cannot return the binary body, the clients call the route through their authenticated HTTP layer with the generated `SugarReportIn` model; record the ruling.
- [ ] **Step 4: Run** the full checks as Task 5 Step 4, plus `generate_sugar_report_expectations --check` → PASS.
- [ ] **Step 5: Commit** `feat(api): doctor report PDF and CSV on demand, never stored`, `feat(i18n): sugar control slice S5`, `chore(contract): sugar report`.

---

### Task 32 (Android): Report screen, share *(parallel with Task 33)*

Use the `flutter-feature` skill. Spec: 8.4, 13.2 (screen 7), 14.5. Ruling H23.

**Files:**
- Create: `apps/app/lib/features/sugar/data/report_repository.dart`, `apps/app/lib/features/sugar/presentation/report_screen.dart`, `apps/app/test/features/sugar/report_screen_test.dart`
- Modify: `sugar_screen.dart` (entry), the router

**Interfaces:**
- Range chips 14, 30, 90 days and custom (7–92, ending at most `today`); format PDF / CSV; language (default the app language); toggles include name and include notes, **off by default**; Generate.
- The request body starts from `packages/test-fixtures/sugar/report/request_default.json` values.
- Without `health_data` (the consents state): only CSV is offered, with `sugar.report.csv_only_note`.
- On success: write the bytes to the app cache with the server's filename, open the system share sheet (`share_plus`), and delete the cached file after the share returns (also on cancel). Errors map to their messages; `consent_required` opens the consent flow.

- [ ] **Step 1: Write the failing tests:** `toggles default off and body equals request_default`, `only CSV offered after withdrawal`, `share hands the CSV golden bytes with the server filename and deletes the cache file`, `empty range error shown`, `custom range bounded 7 to 92`.
- [ ] **Step 2: Run them** to verify they fail. **Step 3: Implement.** **Step 4: Run** `dart format --set-exit-if-changed lib test && flutter analyze && flutter test` → PASS.
- [ ] **Step 5: Commit** `feat(app): doctor report with share`.

---

### Task 33 (Web): Report screen, download, e2e *(parallel with Task 32)*

Use the `web-feature` skill.

**Files:**
- Create: `apps/web/src/features/sugar/components/ReportView.tsx`, `apps/web/src/features/sugar/api/report.ts`, `apps/web/src/app/[locale]/(app)/sugar/report/page.tsx`, `apps/web/tests/features/sugar/ReportView.test.tsx`, `apps/web/e2e/sugar-report.spec.ts`
- Modify: `SugarView.tsx` (link), `stub-api.mjs` (serves the CSV golden and a small PDF)

**Interfaces:** the Task 32 behaviour; the file downloads through a `Blob` object URL that is revoked right after the click (nothing kept in storage).

- [ ] **Step 1: Write the failing tests:** the Task 32 cases (download instead of share). Plus `e2e/sugar-report.spec.ts`: generate a CSV → the download's filename is `smartnutri-glucose-<from>-<to>.csv` and its first bytes are the UTF-8 BOM; withdraw `health_data` in the stub → only CSV is offered, and the CSV still downloads.
- [ ] **Step 2: Run them** to verify they fail. **Step 3: Implement.** **Step 4: Run** `pnpm lint && npx tsc --noEmit && pnpm test && pnpm e2e` → PASS.
- [ ] **Step 5: Commit** `feat(web): doctor report download`.

---

### Task 34: Slice-S5 gate and final docs

**Files:**
- Modify: `docs/FEATURE_PARITY.md` (F31 → 🟡), `CONTEXT.md` (Plan 13 code complete; migrations 0014–0016; the API image now carries Pango and the Noto fonts; open USER items: clinician sign-off on `glucose.yaml`, native review of hi and mr, lawyer questions, S6–S8 next), this plan.

- [ ] **Step 1: Run everything** as Task 10 Step 1, plus every `generate_sugar_*_expectations --check`, and build the API image (`docker build --build-context i18n=packages/i18n/messages apps/api`).
- [ ] **Step 2: Dispatch** `nutrition-safety-reviewer`. Scope: the PDF and CSV content against spec §8 (no estimate, score, verdict, colour or advice); name and notes off by default; the CSV injection guard; never stored and `no-store`; Q13 consent by format with no quota spent on a refusal; hi and mr rendering (look at the PNGs from Task 29 and a fixture PDF); the footer and disclaimer; hide-numbers in the report; the whole DO-NOT-BUILD list across S1–S5.
- [ ] **Step 3: Fix** blocking findings with tests; re-run Step 1.
- [ ] **Step 4: Commit** `docs: Plan 13 slice S5 parity, context and review`.
