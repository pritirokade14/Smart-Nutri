# Sugar Control study: research log (Phase 1)

Date: 2026-11-07. Discovery only. Nothing cloned, downloaded or analysed. Free searches and public GitHub API metadata only. Format follows docs/research/food-diary.

## Sources

| Date | Source | What we took | Confidence |
|---|---|---|---|
| 2026-11-07 | GitHub repo nightscout/cgm-remote-monitor (metadata via the GitHub API) | AGPL-3.0, 2,858 stars, pushed 2026-11-07, JavaScript | High (API field; LICENSE file not opened) |
| 2026-11-07 | GitHub repo NightscoutFoundation/xDrip (metadata via the GitHub API) | GPL-3.0, 1,822 stars, pushed 2026-11-03, Java | High (API field) |
| 2026-11-07 | GitHub repo nightscout/AndroidAPS (metadata via the GitHub API) | AGPL-3.0, 1,249 stars, pushed 2026-11-07, Kotlin | High (API field) |
| 2026-11-07 | GitHub API topic search (diabetes, glucose) | Mostly CGM display tools (GlucoseTray MIT, FLwatch MIT, agp_tool MIT, libre-link-unofficial-api MIT). No maintained open meal-plus-glucose diary found | Medium |
| 2026-11-07 | GitHub repo Flutter (metadata via the GitHub API) diabetes diary search | zeletrik/diabetes-diary: no licence, 3 stars, last push 2019. Dead | High |
| 2026-11-07 | GitHub repo PCOS (metadata via the GitHub API) search | Only ML-prediction notebooks and OvaCare (React/Vite, no licence, 14 stars, 2026-10-04). No usable PCOS tracker | Medium |
| 2026-11-07 | alternativeto.net/software/xdrip- | xDrip+ GPL-3.0; GlucoDataHandler listed MIT; Glucosio listed open source but discontinued; Juggluco, Shuggah, Sugar Sense proprietary | Medium (aggregator) |
| 2026-11-07 | Web search: app-store results for diabetes meal and glucose logging | Blue Circle Diabetes app (Indian nonprofit, free, glucose log, food lookup with glycemic data, carb counting, insulin calculator); Nourishly Type 2; Glycemic Index Guide; GlucoSpike (iOS) | Low-Medium (store and foundation pages; not opened) |
| 2026-11-07 | cbinsights.com compare pages (BeatO, sugar.fit, mySugr) | BeatO: Delhi, 2015, own glucometer; sugar.fit: Bengaluru, 2021, type 2 and prediabetes; mySugr: logbook, insulin calculator, coach, doctor reports | Low-Medium |
| 2026-11-07 | medianama.com/2025/11/223-draft-guidelines-medical-device-software, nishithdesai.com, mondaq.com (CDSCO guidance) | CDSCO draft guidance on medical device software issued 2025-10-21 under MDR 2017 (SiMD vs SaMD, Class A-D). Mondaq piece dated 2026-08 says a final version exists | Medium; final text not read [unverified] |
| 2026-11-07 | apacmed.org SaMD guidance (2022) | Industry example: apps that calculate insulin dose from glucose are SaMD. Not a CDSCO decision | Medium |

## Not reached or weak

- Reddit (r/diabetes, r/diabetes_t2, r/PCOS, r/india): search tool returned no direct threads, only a mirror. User sentiment [unverified].
- Product Hunt and F-Droid: no direct hits; F-Droid listings not checked [unverified].
- Tidepool repo URL guessed wrong (404). Tidepool (BSD, non-profit) licence [unverified].
- Blue Circle: repo, licence and tech stack not found [unverified].
- Final CDSCO guidance text and any Indian classification of dose calculators: not read.

## Phase 4: feature spec (design only)

Date: 2026-11-07. Output: `FEATURE_SPEC.md` in this folder. No web sources were fetched in this phase; it synthesises the Phase 1 to 3 files and the repository. Nothing was built, migrated or committed.

| Date | Source | What we took | Confidence |
|---|---|---|---|
| 2026-11-07 | `SHORTLIST.md` (DO-NOT-BUILD list) | Carried into the spec as §1.4 "Never", restated in our words, plus two additions: no glucose prediction and no variability scores | High (our own binding list) |
| 2026-11-07 | `apps/nightscout.md`, `apps/xdrip.md` | Canonical mg/dL with the typed value kept; explicit unit on input; time-of-day pattern with wide windows and a minimum count; uuid idempotency; soft delete and restore; user-typed reminders with quiet hours. Excluded: estimated A1c, alarms, forecasts, insulin and dose maths | High (clean-room notes) |
| 2026-11-07 | `apps/closed-apps-public.md` | App comparison (§2 of the spec); meal-plus-reading idea (mySugr), GI on the food card (Blue Circle), user-entered HbA1c (BeatO), doctor PDF/CSV (mySugr, Glucose Buddy); guidance values used only as an information card or clinician questions | Medium (public pages, several secondary) |
| 2026-11-07 | `docs/research/food-diary/FEATURE_SPEC.md`, `DECISIONS.md` | Reused, not duplicated: meal slots, `meal_logs` entries with snapshots, local dates from `accounts.timezone`, the unknown-is-not-zero rule, hide-numbers, solo-with-family-ready keys, the ADR 0022 consent pattern | High |
| 2026-11-07 | `apps/api/app/scoring/conditions.py`, `data/thresholds.yaml`, `app/core/consent.py`, `app/integrations/posthog.py`, `app/features/me/service.py`, `packages/test-fixtures/modes/layouts.json` | Existing blood-sugar rules (sugar bands, misleading sugar claims, hidden/added sugars, 30 g carbs per serving, cardio caution) left unchanged; consent, analytics, delete-order and mode files the spec extends | High (read in the repo) |

Proposals made in the spec (all PENDING CLINICIAN REVIEW, all in a new `glucose.yaml`): conversion factor 18.016; hard limits 20–600 mg/dL; confirm band 40–400 mg/dL; very-low note below 54 mg/dL (Q3); 90-day back-entry; ±2 min duplicate window; after-meal link window 15–240 min; six 4-hour pattern windows with at least 5 readings each; insights gate 10 readings on 5 days, 3 meals on 3 days per food, +20 mg/dL difference; carb guide bounds 5–200 g with no default number; lab hard limits and conversion factors.

Still unverified (listed in spec §18): the conversion factor the clinician prefers (18.016 or 18); HbA1c IFCC/NGSP equation constants and lipid factors; home-meter display limits; ADA Standards of Care Section 6 primary text (2026); ICMR-NIN 2024 Annexure III GI list (primary PDF); Atkinson GI tables reuse terms; final CDSCO guidance text; FDA policy wording; WeasyPrint Devanagari shaping and image size; `flutter_local_notifications` licence; Supabase Postgres version for `ON DELETE SET NULL (column)`.

Open questions for the user: 18, in spec §16 (Q1–Q18), each multiple choice with the recommended option first.
