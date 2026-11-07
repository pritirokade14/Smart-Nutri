# Sugar Control: feature spec (Phase 4, design only)

Changelog: 2026-11-07: decisions Q1–Q18 applied.

- **Status:** DRAFT for build approval. Nothing here is built. No code, migration, YAML or string has been changed. The user's 18 binding decisions are in `DECISIONS.md` beside this file; section 16 lists them and the rest of the spec applies them.
- **Date:** 2026-11-07. Branch at the time of writing: `v1-rebuild`. Alembic head in the repo: `0008_diary_goal_settings`; the Food Diary spec reserves numbers up to `0014`.
- **Inputs:** `DECISIONS.md` (binding), `SHORTLIST.md` (including the DO-NOT-BUILD list, which is binding), `RESEARCH_LOG.md`, `apps/nightscout.md`, `apps/xdrip.md`, `apps/closed-apps-public.md` in this folder; `docs/research/food-diary/FEATURE_SPEC.md` and `DECISIONS.md`; AGENTS.md; CONTEXT.md; `docs/PRODUCT.md`; ADRs 0017, 0018, 0019, 0022; the existing blood-sugar rules in `apps/api/app/scoring/conditions.py` and `data/thresholds.yaml`; `app/core/consent.py`; `app/integrations/posthog.py`; `app/features/me/service.py`; `packages/test-fixtures/modes/layouts.json`.
- **Clean room:** everything here is in our own words and notation. Nightscout (AGPL-3.0) and xDrip+ (GPL-3.0) were read for ideas only; no code, strings, schemas or assets were copied. Closed apps were studied from public pages only (ADR 0006).
- **Every number** in this spec is a proposal. Each lives in YAML, is marked `PENDING CLINICIAN REVIEW`, and needs sign-off before launch.
- `[unverified]` marks anything not confirmed against a primary source.

---

## Contents

1. Summary and scope
2. How the studied apps do it
3. Ideas adopted and rejected
4. Glucose log
5. Meals and readings: one timeline, the meal link, and "meals and your readings"
6. Carbs, the per-meal carb guide, GI and GL
7. Lab values
8. Doctor report (PDF and CSV)
9. Reminders
10. PCOS
11. Onboarding
12. Data model, API, consent and DPDP
13. Client screens (Android and web) and i18n keys
14. Tests
15. Phased slices
16. Decisions (resolved)
17. Risks and mitigations
18. Sources

---

## 1. Summary and scope

### 1.1 Headline design

Sugar Control is a **logbook, not a medical device**. It lets one person (the account holder) record their own glucose readings and lab results beside the food they already log in the diary, see simple descriptive patterns, and hand a clean report to their doctor. It never tells anyone what to do with a medicine, never raises an alarm, and never estimates a value it was not given.

- **Built on the diary, not beside it.** Meals are diary meals: a meal slot on a local date (Food Diary spec §5.12), with entries in `meal_logs` that carry a food snapshot and nutrients (§5.1). Carbs per meal are the diary's slot totals. Local dates come from `accounts.timezone` (migration 0008). Hide-numbers (`numbers_display`) applies unchanged. Nothing in the diary is duplicated.
- **A glucose log** stored in canonical mg/dL, with the typed value and unit kept for audit, a closed set of meal-context tags, soft range notes against a range **the user sets** (no default range ever applied), idempotent create, soft delete with undo and a 30-day "Recently deleted" list, back-entry up to 90 days, and explicit time rules.
- **One timeline** per day that merges diary meals and glucose readings by time, with an optional link from a reading to a diary meal.
- **"Meals and your readings"** (the safe name for "foods that spike you"): a descriptive table computed only from the user's own linked readings, behind a minimum-data gate, worded as information, never advice, and behind a flag until a clinician has reviewed it (Q5).
- **Carbs per meal** from diary entries and label scans; an **optional, user-entered per-meal carb guide** shown as information (Q6); **GI and GL only from the ICMR-NIN 2024 Annexure III**, with a page reference per row, otherwise unknown (Q7).
- **A lab log** for HbA1c, fasting glucose and lipids, as the user typed them, with simple trends. **HbA1c is never estimated** from glucose readings, in any screen, response or report.
- **A doctor report**, generated server-side on demand as a PDF (in en, hi or mr) and a CSV, labelled "information, not medical advice", and never stored (Q9). The CSV stays available on `terms` alone after `health_data` is withdrawn (Q13).
- **Reminders** whose text is only what the user typed, with quiet hours and pause. No medicine names are suggested, and there are no dose fields. They are the last slice, S8, built after S1–S5 ship (Q10), and need `health_data` consent (Q12).
- **All numbers and statistics come from the API**, in a pure module `app/scoring/glucose.py` with its constants in `app/scoring/data/glucose.yaml`. Clients render. No verdict, reason, score or allergen state ever reads Sugar Control data; `analyze` is invariant to it (tested).
- **No LLM calls and no analytics events** carry Sugar Control data (Q17: no Sugar Control events exist at all). Nothing about a reading, a lab value, a meal link or a reminder leaves the API except to the user's own devices and the files they choose to export.
- **Solo now, family-ready.** Rows are keyed by `member_id` with the composite FK pattern; a server flag `SUGAR_FAMILY_ENABLED=false` rejects any member other than the primary one, exactly as the diary does (Food Diary Q9).

### 1.2 In scope (this feature)

| Area | In |
|---|---|
| Glucose log | Manual readings only (Q11): value, unit, time up to 90 days back (Q15), context tag, optional after-meal timing, optional meal link, optional note; edit; soft delete with undo and "Recently deleted" for 30 days (Q16); Android offline queue |
| Settings | Preferred unit (mg/dL or mmol/L); an optional personal range (low and high) the user types from their doctor's advice, empty by default (Q4); the optional carb guide, off by default (Q6); an optional low-reading note, shown only after clinician sign-off (Q3) |
| Timeline | A merged day view of diary meals (with carbs per meal) and readings; suggested meal links |
| Patterns | Summary by context tag and by time-of-day window over 7, 14, 30 or 90 days; share of readings within the user's own range when one is set; data-sufficiency notes |
| Meals and your readings | Slice S6: descriptive per-food table from the user's own linked after-meal readings, behind a data gate and a flag that stays off (Q5) |
| Carbs | Carbs per meal and per day from diary entries; the optional per-meal guide with no default number (Q6); GI and GL on generic foods from ICMR-NIN 2024 Annexure III only, with page references (Q7) |
| Labs | HbA1c, fasting glucose, total cholesterol, LDL, HDL, triglycerides; entered values with unit conversion for display; trends and "change since last" |
| Doctor report | PDF (en, hi, mr) and CSV over a chosen range of up to 92 days, on demand, never stored (Q9) |
| Reminders | User-typed text, times, weekdays, quiet hours, pause; last slice S8 (Q10); `health_data` consent (Q12) |
| Onboarding | The "Sugar Control" chip, with an optional condition question; no scoring change (Q14) |
| Navigation | Mode tabs Home, Scan, Diary, Sugar, Profile; Family moves to More (Q18) |

### 1.3 Later (designed for, not built now)

- Glucometer, CGM and Health Connect import: deferred (Q11); manual entry only. Revisit with Health Connect in v2 as a separate decision. The `source` column is a closed set holding only `manual` until then.
- Photo or OCR import of a lab report (would need the label-scan confirm pattern).
- Family logs (another member's readings), including children with type 1 diabetes. Needs the Family decision and a DPDP review for children's data.
- Other lab tests (post-meal plasma glucose, kidney function, thyroid, fasting insulin), each needing its own clinician row.
- PCOS-specific content or cycle tracking beyond the shared tools (Q8): revisit after launch.
- Insights over carbs (for example "readings after meals over N g carbs"), only after "meals and your readings" has been reviewed in use.

### 1.4 Never (the DO-NOT-BUILD list, binding)

Carried from `SHORTLIST.md` ("Regulatory: do NOT build"), restated in our words. These are refused even if asked for later, unless a regulatory opinion and a separate decision change them.

1. **No dose maths of any kind.** No insulin or tablet dose calculation, correction factor, insulin-to-carb ratio, bolus wizard, "insulin on board" or "carbs on board". No insulin or medicine fields on any record.
2. **No dose or timing advice.** Nothing like "take X units" or "skip your tablet". A reminder only repeats text the user typed, as information.
3. **No diagnosis or risk scoring.** No "you may have diabetes, prediabetes or PCOS", no risk score, no classification of a person from their readings or labs. (Ranges describe readings against the user's own numbers, never the person.)
4. **No treatment targets or medical alerts.** No hypo or hyper alarms, no push alerts on readings, no colour-coded "danger" states framed as clinical guidance. Ranges are user-set or shown as a cited general reference, always marked PENDING CLINICIAN REVIEW.
5. **No automation and no device claims.** No closed loop, pump or CGM-driven automation; no claim to replace a glucometer; no claim about reading accuracy. Importing from a meter or CGM is a later, separate decision.
6. **No model output changes a number.** The LLM explains only (AGENTS rule 1); Sugar Control makes no LLM calls at all in this design.
7. **No medical claims.** No "treats, manages or cures diabetes or PCOS". Copy says "information, not medical advice" (AGENTS rule 7).
8. **HbA1c is logged as entered and never estimated** from glucose readings (no "estimated A1c", no GMI, no average-to-A1c formula).

Two extra exclusions this spec adds for safety: no glucose **prediction or forecast** of any kind (Nightscout and xDrip+ both have one; `apps/nightscout.md` §4, `apps/xdrip.md` §3), and no **variability "scores"** presented as health scores (`apps/xdrip.md` §4).

---

## 2. How the studied apps do it

Sources: `apps/nightscout.md` (NS), `apps/xdrip.md` (XD), `apps/closed-apps-public.md` (closed). Section numbers refer to those files. Closed-app cells are from public pages; anything single-sourced is marked there and treated as [unverified] here.

| Topic | Nightscout (AGPL) | xDrip+ (GPL) | mySugr | Glucose Buddy | BeatO | sugar.fit | HealthifyMe | Blue Circle |
|---|---|---|---|---|---|---|---|---|
| **Glucose entry** | Manual finger-stick is a first-class entry type beside sensor values; no explicit manual range check found (NS §2) | Manual meter reading model with a unique timestamp and uuid, rejects zero or ancient times, clamps small future skew, 30 s duplicate window (XD §2) | Logbook with meter auto-sync; reviewers find entry slow (closed §1) | One entry for glucose, medicine and meal, with notes (closed §1) | Synced from its own meter, colour-coded history (closed §1) | CGM-led (closed §1) | CGM-led (closed §1) | Manual log (closed §1) |
| **Units** | mg/dL stored; display unit per site; thresholds read in display unit with a fragile magnitude heuristic (NS §1) | mg/dL stored; thresholds stored in display unit, which breaks on a unit switch (XD §1) | n/a | Both units (closed §1) | Not stated | n/a | n/a | mmol/L added on user demand (closed §1) |
| **Meal context** | No fasting or post-meal tag; free-text notes only (NS §2) | None on readings; free-text notes (XD §2) | Tags (more in Pro) (closed §1) | Custom tags in premium [unverified] | Not stated | n/a | n/a | Not stated |
| **Meals and carbs** | One "treatments" collection with carbs and notes, linked to glucose by time only (NS §3) | Carbs on the same record as insulin; markers on the glucose chart (XD §3) | Meal photo plus carbs; shows how glucose responded so the user can judge their carb estimate (closed §1) | Carbs from a food database, hourly view beside glucose (closed §1) | Diet plan by coaches | Coach-led "what drives spikes" (closed §1) | CGM plus food data "ranked by response" (closed §1) [unverified] | Carb counting help (closed §1) |
| **GI and GL** | None | None | None | None | None | None found | None found | GI (and possibly GL) on a food card; sources not stated (closed §1) |
| **Statistics** | Per-day counts low/in/high, mean, SD, quartiles, **estimated A1c**; time-of-day percentile chart (AGP idea); distribution vs user range (NS §4) | Time in range, mean, SD, variability indices, **estimated A1c**, data completeness (XD §4) | Daily, weekly, monthly reports; **estimated HbA1c** (closed §1) | Trends; automatic A1C "calculator" in premium (closed §1) | Trend graphs | n/a | n/a | n/a |
| **HbA1c and labs** | Estimate only | Estimate only | Estimate; lab entry unclear | Trend of A1C | User-entered HbA1c with reminders (closed §1) | n/a | Metabolic panel in a paid bundle | n/a |
| **Doctor report** | Printable HTML reports; CSV via the API (NS §5) | Database export, no PDF (XD §5) | PDF and Excel in Pro | Printable PDF and CSV | Email with graphs | n/a | n/a | n/a |
| **Reminders** | Alarms only (NS §9) | User-typed reminders with repeat buckets, weekday/weekend, "off at night", global disable (XD §9) | n/a | n/a | HbA1c reminders | n/a | n/a | n/a |
| **Regulated parts to avoid** | Bolus wizard, IOB/COB, alarms, prediction, estimated A1c (NS §10) | Insulin, dose adjust, alarms, forecast, calibration, estimated A1c (XD §10) | Bolus calculator in some countries | A1C estimate | A1C estimate (CGM bundle) | Hardware, coaching | Coaching | Insulin calculator |
| **Indian food** | None | None | None | None | Coaches | Coaches | 100k+ foods [unverified] | Yes (Indian nonprofit) |
| **Complaints** | Weak privacy defaults (readable by default) (NS §8) | Telemetry exists (XD §8) | Slow entry, tedious scrolling | Recurring charges [unverified] | Sales calls, meter failures, a timestamp bug | Undelivered CGM, sales calls | Not gathered | Not found |

**What nobody does publicly** (closed §2 item 5): gentle condition onboarding; a per-meal carb view built from packaged-food labels; any PCOS-specific tracking in the self-serve apps. These are our gap.

---

## 3. Ideas adopted and rejected

### 3.1 Adopted

| # | Idea | From | Why, and what we change |
|---|---|---|---|
| A1 | **Canonical mg/dL, convert at the edge** | NS §1, XD §1 | One stored unit keeps statistics simple. We add what both lack: the **typed value and unit are stored too**, the unit is always explicit on input (never inferred from size), and user ranges are stored in mg/dL so a unit switch cannot corrupt them. |
| A2 | **Closed set of meal-context tags** | Gap in NS §2 and XD §2 (free text is not queryable) | Patterns by context are the most useful thing for a fingerstick user and their doctor. Indian lab language (fasting, "PP", random) maps onto the set (Q2). |
| A3 | **Typo guard, not a clinical judgement** | XD §2 (sanity floor, future clamp, duplicate window) | Hard limits reject impossible input; a wider "unusual value" band asks the user to confirm what they typed. Neither is framed as a health warning. |
| A4 | **Client uuid for idempotent create; soft delete; restore** | XD §2 and §6 (uuid, "undone" state, undo), NS §6 (soft delete with `isValid`) | Android's offline queue already depends on `client_id`. Soft delete gives undo and a "Recently deleted" view for 30 days; the retention job purges rows after that (Q16). |
| A5 | **One time-ordered feed of meals and readings** | NS §3 (shared time axis), XD §3 (meal markers on the chart) | We merge diary meals (slot on a date) with readings on the server. The link from a reading to a meal is explicit and editable, not only time proximity. |
| A6 | **Time-of-day pattern** | NS §4 (percentile chart), XD §4 | Fingerstick data is sparse, so we use wide time windows (about 4 hours) instead of 30-minute bins, and refuse to draw a window with too few readings. |
| A7 | **Data-sufficiency notes** | XD §4 (expected readings) | We show "N readings on M days" next to every statistic, and a gate for anything comparative. |
| A8 | **Own-data meal response view** | mySugr meal photo plus response, HealthifyMe "ranked by response" (closed §1) | Only from the user's own typed readings, never CGM inference, descriptive wording, a minimum-data gate and a flag (Q5). |
| A9 | **GI, GL and portion on the food card** | Blue Circle (closed §1) | Only from ICMR-NIN 2024 Annexure III with a page per value; unknown otherwise; packaged products never get a GI (Q7). |
| A10 | **Doctor report: summary, pattern, day tables** | NS §5 (report set), mySugr and Glucose Buddy (PDF/CSV), BeatO (email share) | Generated server-side from the same functions as the screens, not stored, with "information, not medical advice" on every page. |
| A11 | **User-typed reminders with quiet hours and pause** | XD §9 | Content is only what the user typed; we add lock-screen privacy and refuse suggestions or dose fields. |
| A12 | **Default-deny privacy** | Lesson from NS §8 | RLS, owner-only access, no analytics events, no LLM, no stored report. |
| A13 | **Local time frozen per reading** | NS §6 (UTC offset kept) | Each reading stores its local date and minute-of-day at write time, so time zone changes never move past readings between windows. |
| A14 | **User-entered HbA1c with trend** | BeatO (closed §1) | Labs are typed values with their unit; HbA1c is shown in both % and mmol/mol by exact conversion of the entered value, never derived from glucose. |

### 3.2 Rejected

| Idea | Seen in | Why we reject it |
|---|---|---|
| Estimated A1c / GMI from average glucose | NS §4, XD §4, mySugr, Glucose Buddy, BeatO bundle | DO-NOT-BUILD item 8. A wrong estimate can delay a lab test or mislead a clinician. |
| Bolus wizard, IOB/COB, carb ratios, insulin records | NS §3 and §10, XD §3 and §10, mySugr, Blue Circle | DO-NOT-BUILD item 1: dose calculation is the standard SaMD example (`RESEARCH_LOG.md`, APACMed). |
| High/low alarms, missed-reading alerts, predicted lows | NS §9, XD §9 | DO-NOT-BUILD item 4. A reading outside the user's range gets a neutral note on screen only. |
| Glucose prediction or forecast | NS §4 (AR2), XD §3 (Forecast) | A forecast invites acting on it; out of scope entirely. |
| Thresholds stored in the display unit; unit guessed from magnitude | NS §1, XD §1 | Both break on a unit switch or a typo. Ranges are stored in mg/dL and the unit is always explicit. |
| Default clinical ranges painted on charts | NS §4 (report defaults) | Would read as a treatment target. No range is shown unless the user sets one (Q4). |
| Variability indices (GVI, PGS) and "success" scores | XD §4, NS §4 | Unproven as user-facing measures and easy to read as a grade of the person. |
| 30-minute AGP bins for fingersticks | NS §4 | Too few points per bin for manual logs; produces confident-looking noise. |
| Free-form query operators on the API | NS §7 (needed repeated hardening) | Fixed filters only. |
| Coach-led spike explanations, CGM hardware | sugar.fit, HealthifyMe | Paid, hardware-led, and advice-shaped; not our model. |
| Colour-coded "good/bad" readings in red and green | BeatO | Red/green reads as a verdict. Verdict colours are reserved for scan verdicts (Food Diary §7). |
| Calibration of sensor values from a meter reading | XD §2 | Device behaviour; out of scope. |

---

## 4. Glucose log

### 4.1 Units: canonical mg/dL, conversion for display

- **Stored:** `value_mgdl` (numeric, one decimal place) is the only value statistics use.
- **Also stored, for audit and exact round trip:** `entered_value` (numeric) and `entered_unit` (`mg_dl` or `mmol_l`).
- **Conversion constant:** `units.mgdl_per_mmoll` in `glucose.yaml`, proposed **18.016**, the factor both open-source apps use (`apps/nightscout.md` §1, `apps/xdrip.md` §1). It follows from the molar mass of glucose (about 180.16 g/mol). Some labs and textbooks use 18 [unverified which Indian labs use]. The clinician confirms.
- **Input precision:** mg/dL accepts whole numbers only; mmol/L accepts one decimal place. Anything finer is `422 glucose_precision`. The unit field is **required** on every write; the API never infers it from the size of the number.
- **Storing a mmol/L entry:** `value_mgdl = round_half_up(entered_value × 18.016, 1)`.
- **Display (computed by the API, never the client):**
  - In the reading's own entered unit: the entered value exactly (so a user who typed 6.2 always sees 6.2).
  - In mg/dL from mmol/L: `round_half_up(value_mgdl, 0)`.
  - In mmol/L from mg/dL: `round_half_up(value_mgdl ÷ 18.016, 1)`.
  - Statistics are computed on unrounded `value_mgdl` and rounded only for display.
- **Preferred unit** is a member setting (`sugar_settings.glucose_unit`), default **mg/dL**, with mmol/L in settings and on the entry sheet (Q1; Indian meters and lab reports mostly use mg/dL [unverified, no survey found]). Switching the unit changes display only. Every API response carries `display: {value, unit}` in the preferred unit plus `value_mgdl`.
- **User ranges are stored in mg/dL** (`range_low_mgdl`, `range_high_mgdl`) and displayed in the preferred unit.

### 4.2 Meal-context tags (closed set; Q2)

| Code | Meaning shown to the user | Notes |
|---|---|---|
| `fasting` | Fasting (on waking, before eating) | Indian lab "FBS" |
| `before_meal` | Before a meal | Can link to the meal that follows |
| `after_meal` | After a meal | Requires `after_meal_timing`: `about_1h`, `about_2h` or `not_sure`. "About 2 h" matches Indian "PP" testing |
| `bedtime` | At bedtime | |
| `random` | Any other time | Default when the user picks nothing; Indian "RBS" |

- The set is a DB check and an API enum; adding a value is a migration plus a fixture update.
- `after_meal_timing` is NULL unless the tag is `after_meal`, and required when it is.
- No tag implies anything medical; no tag triggers anything.

### 4.3 Hard limits, the "unusual value" confirm, and range notes

Three separate layers. None of them is an alarm, and none uses red.

1. **Hard limits (reject):** `value_mgdl` outside **20–600** returns `422 glucose_out_of_range` with the limits in the user's unit. Proposal based on the usual display range of home meters [unverified]. YAML `limits.hard_mgdl`.
2. **Unusual value (confirm):** outside **40–400** (YAML `limits.confirm_mgdl`) the API returns `422 glucose_needs_confirm` unless `confirm_unusual: true` is sent. The client shows the number in **both units** and asks "Is this the number you meant to type?". This catches mmol/mg mix-ups (typing 110 with mmol/L selected is outside the hard limit; typing 6 with mg/dL selected is outside the hard limit too). The wording is about typing, not health.
3. **Range note (display only):** if, and only if, the user has set a personal range, each reading gets `range_position`: `below`, `within`, `above`; otherwise `no_range`. The client shows a small neutral text label ("Below your range", "Within your range", "Above your range") with an icon, in a neutral token colour. There is **no default range** (Q4): the range is the one the user typed in settings, and nothing else is ever applied. There is no sound, vibration, push or banner.

**Very low readings (Q3, decided).** The saved-reading screen carries one static, neutral line for a reading below a clinician-set value: "If you feel unwell, follow the plan your doctor gave you, or get medical help." It is gated twice: the value lives in YAML (`info.very_low_note_below_mgdl`, **null until a clinician signs off a number**; 54 mg/dL, the level ADA guidance treats as clinically significant [unverified, secondary source in closed §3], is only the candidate put to the clinician) and the server flag `SUGAR_LOW_NOTE_ENABLED` (default false) must be on. With either missing, no note is returned and no space is reserved for it. The line is the same text for every user, in all three languages. It is not an alarm, not coloured, gives no dose or food advice, never changes with the reading, and does not depend on a range. There is no matching note for high readings.

**General reference values** (ADA before-meal 80–130 mg/dL and after-meal peak under 180 mg/dL, as summarised secondarily in closed §3 [unverified, 2025 edition; 2026 loosens goals for older adults]) appear only on an information card in Settings, worded "General reference values published for many non-pregnant adults. Your doctor may give you different numbers." They are never applied automatically (Q4), never drawn on a chart unless the user copies them into their own range, and are cited with `url_verified: false` until checked.

### 4.4 Time rules

- `measured_at` is a timezone-aware timestamp. Default: now.
- **Future:** more than 5 minutes ahead returns `422 measured_at_in_future`. Small skew up to 5 minutes is accepted as sent (not clamped, so the user's time is never altered silently).
- **Past:** older than **90 days** returns `422 measured_at_too_old` (YAML `time.max_back_days: 90`; Q15: exactly 90 days is accepted, 91 is refused). This allows copying a paper logbook in, which meals' 30-day rule does not.
- **Local values frozen at write:** the API stores `local_date` and `local_minute` (0–1439) from `measured_at` in `accounts.timezone`. Editing `measured_at` recomputes them; changing the account time zone does not (same rule as the diary, Food Diary §5.1).
- **Duplicates:** a second reading for the same member within ±2 minutes (YAML `time.duplicate_window_s: 120`) **and** with the same `value_mgdl` returns `409 glucose_possible_duplicate` with `details.existing_id`, unless `confirm_duplicate: true` is sent. Different values close together are allowed (people re-test).

### 4.5 Idempotency, edit, soft delete and undo

- **Create** takes an optional `client_id` (uuid). Unique `(account_id, client_id)`. A repeat returns **200 with the original row** (the existing `meal_logs` behaviour), even if the body differs; the client treats that as success.
- **Edit** (`PATCH`) can change value and unit together, context and timing, `measured_at`, the meal link and the note. The same validation runs. `updated_at` is set.
- **Delete** sets `deleted_at`; the row disappears from every list, statistic, insight and report at once. Response 200 `{id, deleted_at, restore_until}`.
- **Restore** (`POST .../restore`) clears `deleted_at` while within the restore window (Q16: 30 days, YAML `retention.restore_days: 30`). After that: `410 glucose_restore_expired`.
- **Undo in the UI:** a snackbar "Reading deleted. Undo" for about 8 seconds calls restore. A "Recently deleted" list in Settings shows rows (readings and labs) still inside the 30-day window, each with a Restore action.
- **Purge:** the existing retention job (`app/jobs/retention.py`) hard-deletes rows whose `deleted_at` is older than the window. Account deletion (`DELETE /v1/me`) hard-deletes everything at once regardless of the window.
- **Note** is optional user text, 0–200 characters, stored exactly as typed. It is never translated, never sent to analytics, logs or any model, and is excluded from the doctor report unless the user ticks "include notes".

### 4.6 What the glucose log never does

No insulin, medicine or dose field; no "corrected" value; no colour judgement; no alert; no push; no forecast; no estimate of anything; no LLM.

---

## 5. Meals and readings

### 5.1 One timeline (merged with the diary)

`GET /v1/sugar/day?date` returns a single list, sorted by local time, of:

- **meal items**, one per diary meal (a meal slot on that date with at least one entry): slot id and label, the time of its first and last entry, the entries (name, portion, carbs), carbs total for the meal with the diary's `incomplete` rule, the carb guide for that slot if set, and GI/GL notes where cited (§6.3);
- **reading items**: display value, unit, context, timing, range note, link, note flag.

The server builds the list from `meal_logs` (through the diary's own day function, so totals and the unknown rule are identical) and `glucose_readings`. Clients render it; they do not merge or sort.

### 5.2 Linking a reading to a diary meal

- A reading may carry a link to **one diary meal**: `linked_local_date` plus `linked_meal_slot_id`.
- **Suggestion (server-side):** when the client asks for one (`GET /v1/glucose/link-suggestion?measured_at&context`) or creates an `after_meal` or `before_meal` reading with no link:
  - `after_meal`: the meal on the reading's day (or the previous day just after midnight) whose **last** entry is between 15 and 240 minutes before `measured_at` (YAML `link.after_meal_min_minutes`, `link.after_meal_max_minutes`); the nearest wins.
  - `before_meal`: the meal whose **first** entry is between 0 and 60 minutes after `measured_at` (YAML `link.before_meal_max_minutes`).
  - No candidate means no link.
- On create, an automatic link is saved with `link_source = 'auto'` and shown with an "Linked to Lunch · change" control; a user-chosen link is `link_source = 'user'`. The user can unlink.
- A link to a meal that later loses all its entries is kept but shown as "meal has no items", and insights ignore it.
- Archived slots can still be linked targets for past days; new links to an archived slot on a day with no entries in it are refused (`422 meal_slot_archived`).
- `fasting`, `bedtime` and `random` readings cannot be linked (`422 glucose_link_not_allowed`).

### 5.3 "Meals and your readings" (Q5)

The product name for "foods that spike you". It describes the user's own logs. It never says "spike", "avoid", "bad", "safe", "cause" or "trigger".

**Inputs (all from the user's own rows, last 90 days, YAML `insights.window_days`):**
- Eligible readings: `after_meal`, linked to a meal with at least one entry, not deleted.
- **One timing bucket only:** the most common `after_meal_timing` among eligible readings (`about_2h` wins ties; `not_sure` is used only if it is the only bucket). Readings in other buckets are counted in `excluded_readings` and left out, so 1-hour and 2-hour values are never mixed.

**Gate (all must hold, else `ready: false` with progress numbers):**
- at least **10** eligible readings (`insights.min_readings`),
- on at least **5** distinct local dates (`insights.min_days`).

**Computation (pure, in `app/scoring/glucose.py`):**
1. `usual` = the median of all eligible readings' `value_mgdl`.
2. For each **food key** in the linked meals (product id, OFF barcode, generic food id, custom food id or recipe id; quick-add entries are excluded because they have no stable identity; a food appearing twice in one meal counts once): collect the after-meal reading of each meal that contains it.
3. Keep a food only if it appears in at least **3** linked meals on at least **3** distinct dates (`insights.min_meals_per_food`, `insights.min_days_per_food`).
4. For each kept food: `median_after` and `difference = median_after − usual`.
5. Output two lists, each sorted by difference then meal count then name, at most 5 items each (`insights.max_items`):
   - **"Readings after these meals were higher than your usual"**: `difference ≥ +20 mg/dL` (`insights.min_difference_mgdl`, PENDING CLINICIAN REVIEW).
   - **"Readings after these meals were close to or below your usual"**: `difference < +20`.
   - Each item shows the food name, the number of meals, its median after-meal reading and the user's usual value, in the preferred unit.

**Fixed caveats** (i18n keys, always shown): meals usually contain several foods, so this shows what was eaten alongside a reading, not what caused it; portion, activity, sleep, illness and medicines also change readings; information from your own logs, not medical advice; talk to your doctor or dietitian before changing what you eat.

**Never:** fed to verdicts, the scan screen, alternatives, voice, the LLM, analytics or the doctor report by default (the report includes it only if the user ticks it, Q9). Behind `SUGAR_INSIGHTS_ENABLED` (default false) until the clinician reviews the wording and gates.

### 5.4 Patterns (statistics)

`GET /v1/sugar/summary?from&to` (range 7–92 days) returns, from non-deleted readings:

- **Totals:** readings count, days with readings, first and last date.
- **By context tag:** for each tag (and each after-meal timing), `n`, median, lower and upper quartile, min, max, mean. Quartiles use the inclusive linear-interpolation method (Python `statistics.quantiles(method="inclusive")`, Hyndman and Fan type 7), named in the code and the fixtures so every implementation agrees.
- **By time-of-day window** (YAML `pattern.windows`, local time): late night 00:00–03:59, early morning 04:00–07:59, morning 08:00–11:59, afternoon 12:00–15:59, evening 16:00–19:59, night 20:00–23:59. A window with fewer than **5** readings (`pattern.min_readings_per_window`) returns `insufficient: true` and no statistics; the chart shows it greyed with "Not enough readings".
- **Within your range:** only when the user has set a range and the period has at least 10 readings: counts and shares below, within and above. Labelled "share of your readings", never "time in range" (that is a CGM measure).
- **No** SD, coefficient of variation, variability index, score, estimate or forecast.
- **Labs in the period:** the latest value of each test (from §7), with its date.

The same function feeds the screens and the report, so they can never disagree.

---

## 6. Carbs, the carb guide, GI and GL

### 6.1 Carbs per meal

- Carbs per meal are the diary slot totals of `carbs_g` (Food Diary §6.2 `DiaryDayOut.slots[].totals`), from entries logged by search, barcode, label scan, recipe or quick add. Label scans keep the existing rule: extracted values are confirmed by the user before anything is saved (AGENTS rule 2).
- **Unknown stays unknown:** if any entry in a meal has no carbs value, the meal total is marked incomplete ("at least 42 g; some items have no carb value"), exactly as the diary does. Quick-add entries with blank carbs count as unknown, never 0.
- Hide numbers: carbs follow `numbers_display`. With `hide_all`, carbs are hidden on Sugar Control screens too, and the screen offers a link to the setting. Glucose and lab values are never hidden by this setting (they are measurements the user typed, not intake numbers).
- The diary's daily carbs **target** (the remainder after protein and fat, Food Diary §4.7) is unchanged by this feature. A clinician question is raised in §17 (R10) about whether the remainder is suitable for blood-sugar users.

### 6.2 The optional per-meal carb guide (Q6)

- **Optional and off by default** (Q6). The user turns it on and types a number of grams per meal (one number for all meals, or per slot), "as advised by your doctor or dietitian".
- **No default number ships.** The research found no Indian (ICMR-NIN, RSSDI) per-meal carbohydrate figure; only shares of daily energy exist (closed §3 [unverified, secondary]). `glucose.yaml` holds only the bounds, no suggested value, and no code path pre-fills the field. Any default would be a new decision.
- Bounds: 5–200 g per meal (YAML `carb_guide.min_g`, `max_g`), so a typo is caught.
- **Display:** "38 g of your 45 g guide" or "52 g · your guide is 45 g", in neutral colours. Going over is described in plain words with no red and no warning icon. With an incomplete total: "at least 38 g of your 45 g guide".
- The guide never changes a verdict, a diary target or anything else.

### 6.3 GI and GL (Q7)

- **Only generic foods** from the diary's `foods` table can carry GI or GL. Packaged products, custom foods, recipes and quick adds never get one: a label does not state GI, and computing one from ingredients would be invention.
- Each value comes from a row in a reference table `glycaemic_reference` with a **source key** pointing to `glucose.yaml` `sources` (title, edition, Annexure and **page number**, `url_verified`). No source, no value.
- **The only source (Q7):** ICMR-NIN Dietary Guidelines for Indians 2024, Annexure III (GI list) [unverified: PDF blocked during research]. Rows are typed in by hand from the primary PDF, one row per food, each with its **page reference** (`source_locator`) and a named verifier. No other table (including the International Tables of GI and GL) is used; a food Annexure III lacks has no GI. GI and GL are unknown otherwise.
- **GL is shown only when the source states it for a stated serving.** We do not compute GL from GI and our own carb values, because sources use available carbohydrate and their own portions; mixing them would produce a number no source gives.
- **Bands** (display labels only): GI low ≤ 55, medium 56–69, high ≥ 70; GL low ≤ 10, medium 11–19, high ≥ 20 (closed §3; GI bands consistent across secondary sources, GL bands [unverified]). YAML `gi.bands`, `gl.bands`.
- **Display:** a row on the food card and in the timeline meal item: "GI 52 (low) · source: ICMR-NIN 2024", with an info sheet: GI depends on variety, cooking and what it is eaten with; it is a reference value, not a measurement of your meal. Unknown shows "GI not known for this food", never a guess.
- GI and GL never enter verdicts, the carb guide or insights.

---

## 7. Lab values

### 7.1 Tests (closed set)

| Code | Entered units | Canonical | Conversion (display only) | Hard limits (reject) |
|---|---|---|---|---|
| `hba1c` | `%` (NGSP) or `mmol_mol` (IFCC) | % | mmol/mol = (% − 2.15) × 10.929, and the inverse [verify constants against IFCC/NGSP] | 3–20 % |
| `fasting_glucose` | mg/dL or mmol/L | mg/dL | glucose factor (§4.1) | 20–600 mg/dL |
| `total_cholesterol` | mg/dL or mmol/L | mg/dL | × 38.67 [verify] | 50–600 mg/dL |
| `ldl` | mg/dL or mmol/L | mg/dL | × 38.67 [verify] | 10–500 mg/dL |
| `hdl` | mg/dL or mmol/L | mg/dL | × 38.67 [verify] | 5–200 mg/dL |
| `triglycerides` | mg/dL or mmol/L | mg/dL | × 88.57 [verify] | 10–5000 mg/dL |

All limits, plausible-confirm bands and factors live in `glucose.yaml` `labs.*`, PENDING CLINICIAN REVIEW. A plausible band (for example HbA1c 4–15 %) asks for confirmation as in §4.3.

### 7.2 Rules

- A lab result is `{test, entered_value, entered_unit, taken_on (date), note?}`. `taken_on` is a **date** (labs report a date), not in the future, at most 10 years back.
- The display shows the entered value in its unit, plus the other unit by exact conversion, labelled "converted".
- **No reference ranges, targets or bands** on lab values in v1: labs print their own ranges, which vary. No colour, no "high/normal".
- **No derived values:** no non-HDL, no ratios, no HOMA-IR, no risk score. Each would be a calculation a clinician should own.
- **Never estimate HbA1c.** No endpoint, field, chart, report line or i18n key computes or names an estimated A1c or GMI. A test asserts it (§14).
- **Trends:** per test, a points-only chart (no line implying values between tests), a table, and "change since your previous result: −0.4 % (on 12 Aug)". Same soft delete, restore, idempotency and Android queue as readings.

---

## 8. Doctor report (PDF and CSV)

### 8.1 Generation

- `POST /v1/sugar/report` with `{member_id?, from, to, format: "pdf" | "csv", language: "en" | "hi" | "mr", include_name: false, include_notes: false, include_meal_readings: false}`.
- Range: 7 to 92 days (`422 sugar_report_range`). If the range has no readings, meals or labs: `422 sugar_report_empty`.
- Generated **server-side, synchronously, on demand**, in Mumbai, and returned as the response body with `Content-Disposition: attachment`. **Never stored** anywhere (no bucket, no table, no cache; Q9), so nothing extra needs retention or erasure.
- **Consent (Q13):** the PDF needs `terms` and `health_data`. The CSV of the user's own stored data needs `terms` alone, so it stays available after `health_data` is withdrawn, as a data-access right. The CSV then contains stored data only and no computed insight section.
- Every string comes from `packages/i18n` through `app/core/i18n.py` (AGENTS rule 9), keys `sugar.report.*`. Numbers use the user's preferred unit, with the other unit in the CSV.
- PDF engine: **WeasyPrint** (BSD) is proposed because it shapes Devanagari through HarfBuzz; ReportLab may not shape Hindi and Marathi correctly [unverified]. Fonts: Noto Sans and Noto Sans Devanagari (OFL), bundled in the API image. Image size and cold start are measured in slice S5; the PDF ships in all three languages (Q9), so a problem there is fixed, not worked around by dropping a language.

### 8.2 PDF layout

1. **Header:** "Glucose and food log", the date range, generated date and time zone, the unit, and the member's name **only if** `include_name` is true. The first line under the title: "Information the user entered in SmartNutri. Not medical advice. SmartNutri does not diagnose or treat."
2. **Summary:** readings count and days with readings; the table by context tag (n, median, quartiles, min, max, mean); the share within the user's own range only if one is set (stating the range and that the user set it); the latest lab values with dates.
3. **Time-of-day pattern:** one chart of median and quartile band per window, greyed windows where data is insufficient, with the readings count per window.
4. **Meals and carbs:** carbs per meal slot per day (average over days with logged meals, with the number of days), incomplete markers, and the carb guide if set.
5. **Day tables:** one row block per day: each reading (time, value, context, timing, linked meal), each meal (slot, items, carbs), and notes only if `include_notes`.
6. **Lab table:** every lab result in the range, as entered, with conversion.
7. **Optional:** "meals and your readings" only if the flag is on, the gate is met and `include_meal_readings` is true, with its caveats in full.
8. **Footer on every page:** page number, "Information, not medical advice. Values as entered by the user; meter and lab values are not checked by SmartNutri. Thresholds pending clinician review."

Never in the report: estimated A1c, any score, verdicts, colours for readings, advice, or any LLM text.

### 8.3 CSV

- UTF-8 with BOM (so Excel shows Devanagari), RFC 4180 quoting, one row per record.
- Columns: `record_type` (`glucose`, `meal_item`, `lab`), `local_date`, `local_time`, `timezone`, `value_mgdl_or_canonical`, `display_value`, `display_unit`, `entered_value`, `entered_unit`, `context`, `after_meal_timing`, `linked_meal_slot`, `food_name`, `carbs_g`, `carbs_incomplete`, `lab_test`, `note` (empty unless `include_notes`).
- **Formula-injection guard:** any cell from user text (notes, custom slot names, custom food names) starting with `=`, `+`, `-`, `@`, tab or carriage return is prefixed with an apostrophe.
- Slot names: the translated default name, or the user's custom label as typed.

### 8.4 Delivery

- Android: the file is saved to the app's cache and handed to the system share sheet (email, WhatsApp, Drive are the user's choice); the cached file is deleted after sharing.
- Web: a browser download.
- Rate limit: `sugar_reports` 20 per day.

---

## 9. Reminders (last slice S8; Q10, Q12)

- **Content is only what the user typed:** a text of 1–60 characters. The field has a neutral placeholder ("Write your reminder") and **no suggestions, templates, autocomplete or examples that name a medicine**. There is no dose, strength, unit, pill count or "taken/skipped" field, and no adherence tracking.
- **Schedule:** up to 6 times a day (local `HH:MM`), weekdays as a 7-bit mask, enabled flag. At most 20 reminders per member.
- **Quiet hours** (account-level, optional start and end, may wrap past midnight): a reminder due inside them is **skipped**, not delayed.
- **Pause:** "pause all" with an optional end date; per-reminder enable switch.
- **Delivery:**
  - Android: local notifications scheduled on the device (`flutter_local_notifications` [verify licence]), inexact alarms (no exact-alarm permission). The schedule syncs from the API.
  - Web: browser notifications through a service worker and Web Push with server-side sending (VAPID keys server-side only). This needs a scheduler that wakes every few minutes; it is the costly part, which is why reminders are the last slice (Q10).
- **Lock-screen privacy:** the notification title is "SmartNutri reminder"; the user's text shows only when the device is unlocked (Android `VISIBILITY_PRIVATE` with a public version; web shows the text, so the setting "show text in notifications" defaults to off on web).
- **Copy:** "A reminder you set. SmartNutri does not give medicine advice."
- Reminders need `health_data` consent (Q12). Reminder text is user text: never sent to analytics, logs, any model or WhatsApp; stored server-side for sync, owner-only.
- Reminders are not linked to readings: no "you have not tested today" nudge, no reminder created automatically from data.

---

## 10. PCOS (Q8)

**Decided: the same tools as everyone else, with no PCOS-specific features and no cycle tracking in this release.**

- PCOS stays an optional condition on the member (`conditions` already accepts `pcos`, and it already maps to the blood-sugar verdict rules in `thresholds.yaml` `conditions.blood_sugar.applies_to`).
- A person with PCOS uses the same Sugar Control tools (glucose log, labs, carbs, report) if they want them. Nothing assumes they test glucose.
- **No cycle or period tracking.** It is reproductive health data with extra privacy weight, PCOS programmes that do this exist separately (GoodFlip, Fitterfly per search results [unverified]), and it adds nothing the rules engine can use safely.
- **No PCOS-specific lab tests** (fasting insulin, HOMA-IR, hormones) and no weight, fertility or symptom scoring. HOMA-IR would be a derived risk measure.
- Revisit after launch. Any later PCOS content (for example static education cards) is a new decision with a clinician and a claims review.
- Decided (Q8): the PCOS research rows are mostly empty (`apps/closed-apps-public.md` §4), so nothing PCOS-specific is built.

---

## 11. Onboarding

- **Entry:** the "Sugar Control" goal chip (the chip rename is a separate change; until it lands, the Plan 9 `health_condition` tile serves). No chip names a disease.
- **Step 1, a gentle optional question** (one screen): "Would you like to tell us more? This is optional." Choices: Diabetes, Prediabetes, PCOS, Prefer not to say, I just want to keep an eye on my sugar. Multi-select for the first three.
  - Picking a condition **pre-fills** `members.conditions` only after the user confirms and only with `health_data` consent (ADR 0019 pattern; the existing consent dialog opens if needed).
  - "Prefer not to say" and "keep an eye on my sugar" save nothing. A line explains: "Sugar checks on scanned foods use the conditions in your profile. You can add one any time." This is the decided rule (Q14): blood-sugar scan checks apply only once diabetes, prediabetes or PCOS is saved, and there is no scoring change or new condition.
- **Step 2, how you'd like to see things:** glucose unit (mg/dL preselected, Q1); "Do you have a range from your doctor?" (optional low and high; skip is prominent); carb guide (off; "Set a carb guide per meal" opens an empty input, no suggested number, Q6).
- **Step 3, what this is:** "Log readings and lab results next to your meals, see your own patterns, and share a report with your doctor. Information, not medical advice." A "Start with a reading" button and a "Just look around" link.
- Health-data consent is asked at the first save that needs it, not up front.
- Tone rules: no "patient", "diabetic", "control your disease", "risk" or "danger"; second person; short sentences.

---

## 12. Data model, API, consent and DPDP

### 12.1 Migrations

Alembic owns every table and policy (ADR 0009). The Food Diary uses 0008–0011 for its first slices and reserves 0012–0014 for later ones. **Each Sugar Control migration takes the next free number when its slice starts** (so `0012` or later, never a reserved number that has not landed yet). They are listed here by name.

| Migration (next free number) | Contents | Slice |
|---|---|---|
| `NNNN_sugar_settings_glucose` | `sugar_settings`, `glucose_readings` | S1 |
| `NNNN_sugar_carb_guides` | `carb_guides` | S2 |
| `NNNN_sugar_lab_results` | `lab_results` | S4 |
| `NNNN_sugar_glycaemic_reference` | `glycaemic_reference` (reference data, seeded) | S7 |
| `NNNN_sugar_reminders` | `reminders`, `reminder_settings` | S8 |

Every account-owned table follows the diary pattern (Food Diary §5): `REVOKE ALL` from `PUBLIC, anon, authenticated`; `GRANT SELECT` to `authenticated`; `GRANT ALL` to `service_role` (ADR 0013); `ENABLE` and `FORCE ROW LEVEL SECURITY`; policy `<t>_owner FOR ALL TO authenticated USING (account_id = (SELECT auth.uid())) WITH CHECK (same)`; composite FK `(member_id, account_id) → members(id, account_id) ON DELETE CASCADE`; added to `ACCOUNT_OWNED_TABLES`. Numbers are `numeric`. Each migration ships with an upgrade/downgrade test and the RLS test.

### 12.2 Tables

**`sugar_settings`** (one row per member)

| Column | Type | Null | Notes |
|---|---|---|---|
| `member_id` | uuid | PK | composite FK |
| `account_id` | uuid | NOT NULL | |
| `glucose_unit` | text | NOT NULL, default `'mg_dl'` | `mg_dl`, `mmol_l` |
| `range_low_mgdl`, `range_high_mgdl` | numeric | NULL | Both or neither; low < high; each within hard limits; user-set only |
| `carb_guide_enabled` | boolean | NOT NULL, default false | |
| `created_at`, `updated_at` | timestamptz | NOT NULL | |

**`glucose_readings`**

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | uuid | PK | |
| `account_id`, `member_id` | uuid | NOT NULL | composite FK |
| `measured_at` | timestamptz | NOT NULL | |
| `local_date` | date | NOT NULL | frozen at write (§4.4); index `(member_id, local_date)` |
| `local_minute` | smallint | NOT NULL | 0–1439 |
| `value_mgdl` | numeric(5,1) | NOT NULL | check 20–600 (backstop; the API reads YAML) |
| `entered_value` | numeric | NOT NULL | |
| `entered_unit` | text | NOT NULL | `mg_dl`, `mmol_l` |
| `context` | text | NOT NULL, default `'random'` | closed set §4.2 |
| `after_meal_timing` | text | NULL | `about_1h`, `about_2h`, `not_sure`; check: set iff `context = 'after_meal'` |
| `linked_local_date` | date | NULL | |
| `linked_meal_slot_id` | uuid | NULL | composite FK `(linked_meal_slot_id, member_id) → meal_slots(id, member_id) ON DELETE SET NULL (linked_meal_slot_id)` (Postgres 15+ column list, so `member_id` is untouched [verify Supabase PG version]); `num_nonnulls(linked_local_date, linked_meal_slot_id) in (0, 2)` |
| `link_source` | text | NULL | `auto`, `user`; set iff linked |
| `note` | text | NULL | 0–200 characters |
| `source` | text | NOT NULL, default `'manual'` | closed set: `manual` only (Q11) |
| `client_id` | uuid | NULL | unique `(account_id, client_id)` |
| `deleted_at` | timestamptz | NULL | soft delete; partial index on `(member_id, local_date) WHERE deleted_at IS NULL` |
| `created_at`, `updated_at` | timestamptz | NOT NULL | |

**`carb_guides`**: `(member_id, meal_slot_id)` PK, `account_id`, `grams` numeric (5–200), timestamps. Composite FK to `meal_slots ON DELETE CASCADE`. A row with `meal_slot_id` of every active slot is written when the user picks "same for all meals".

**`lab_results`**: `id`, `account_id`, `member_id`, `test` (closed set §7.1), `taken_on` date, `value_canonical` numeric, `entered_value`, `entered_unit` (closed set per test, checked by the API), `note` (0–200), `client_id` (unique per account), `deleted_at`, timestamps. Index `(member_id, test, taken_on)`.

**`glycaemic_reference`** (reference, not account-owned; `SELECT` to `authenticated` with `USING (true)`; writes service-role only): `id`, `food_id` FK `foods(id)`, `gi` numeric NULL, `gl` numeric NULL, `gl_serving_g` numeric NULL (required when `gl` is set), `reference_food` text (`glucose` or `white_bread`; the display converts nothing, it states which), `source_key` text NOT NULL (only the ICMR-NIN 2024 key exists), `source_locator` text NOT NULL (Annexure III and page number), `verified_by` text NOT NULL, `verified_on` date NOT NULL. Seeded from `app/scoring/data/glycaemic_reference.csv` only after hand verification against the primary PDF (Q7).

**`reminders`**: `id`, `account_id`, `member_id`, `text` (1–60), `times` (`text[]` of `HH:MM`, 1–6), `weekdays` smallint bitmask (1–127), `enabled`, `client_id`, timestamps. **`reminder_settings`** (per account): `quiet_start`, `quiet_end` (`time`, both or neither), `paused_until` (timestamptz NULL; far future = paused indefinitely), `show_text_on_web` boolean default false, timestamps.

**Delete order** in `ACCOUNT_OWNED_TABLES` (before the diary's `meal_slots` and `members`): `reminders`, `reminder_settings`, `lab_results`, `glucose_readings`, `carb_guides`, `sugar_settings`. `tests/api/test_delete_me.py` fails until they are added.

### 12.3 The pure module and YAML

- Server flags (default false): `SUGAR_LOW_NOTE_ENABLED` (Q3), `SUGAR_INSIGHTS_ENABLED` (Q5), `SUGAR_FAMILY_ENABLED`.
- `app/scoring/glucose.py` (pure, no I/O): `to_mgdl`, `display_value`, `range_position`, `link_candidate`, `summary_by_context`, `pattern_by_window`, `within_range_share`, `meal_readings` (insights), `lab_convert`. Each takes plain values and the loaded config.
- `app/scoring/data/glucose.yaml`, header `# PENDING CLINICIAN REVIEW. Read only by app/scoring/glucose.py. Never read by verdict rules.` Sections: `version`, `units`, `limits` (hard, confirm), `info` (very-low note), `time`, `link`, `pattern`, `within_range`, `insights`, `carb_guide`, `gi`, `gl`, `labs`, `retention`, `general_reference` (with source keys), `sources`. `info.very_low_note_below_mgdl` is `null` until clinician sign-off (Q3). `carb_guide` has bounds only, no default. `sources` holds the ICMR-NIN 2024 entry only for GI and GL (Q7).
- New `section_sources` entries in `thresholds.yaml` for the methodology page: `glucose_log` (smartnutri_working_values), `general_reference` (ADA Standards of Care Section 6, `url_verified: false`), `gi_bands`, `labs_units`.
- One clinician-sheet row per number (`docs/launch/clinician-review.md`).

### 12.4 API endpoints

Conventions as in the diary (Food Diary §6): feature folders; `ErrorEnvelope`; `operation_id` = `<feature>_<action>`; `member_id` optional, defaulting to the primary member; any other member returns `422 sugar_member_not_enabled` while `SUGAR_FAMILY_ENABLED=false`; another account's member returns `404 member_not_found`; cursor pagination `{items, next_cursor}`; local dates `YYYY-MM-DD`.

**`glucose`** (`app/features/glucose/`, prefix `/v1/glucose`)

| Method and path | operation_id | Request | Response | Errors | Consent | Rate limit |
|---|---|---|---|---|---|---|
| `POST /v1/glucose` | `glucose_create` | `GlucoseIn` | 201 `GlucoseOut`; 200 on a repeated `client_id` | `glucose_out_of_range`, `glucose_needs_confirm`, `glucose_precision`, `glucose_possible_duplicate` (409), `measured_at_in_future`, `measured_at_too_old`, `glucose_timing_required`, `glucose_link_not_allowed`, `meal_slot_not_found`, `meal_slot_archived`, `validation_error` | terms, health_data | `glucose_writes` 200/day |
| `GET /v1/glucose?from&to&context` | `glucose_list` | dates (max 92 days) | `{items: GlucoseOut[], next_cursor}` | `date_range_too_long` | terms, health_data | n/a |
| `GET /v1/glucose/{id}` | `glucose_get` | | `GlucoseOut` | `glucose_not_found` | terms, health_data | n/a |
| `PATCH /v1/glucose/{id}` | `glucose_update` | partial `GlucoseIn` | `GlucoseOut` | as create, plus `glucose_not_found` | terms, health_data | `glucose_writes` |
| `DELETE /v1/glucose/{id}` | `glucose_delete` | | 200 `{id, deleted_at, restore_until}` | `glucose_not_found` | **terms** (erasure is never gated) | n/a |
| `POST /v1/glucose/{id}/restore` | `glucose_restore` | | `GlucoseOut` | `glucose_not_found`, `glucose_restore_expired` (410) | terms, health_data | `glucose_writes` |
| `GET /v1/glucose/deleted` | `glucose_deleted_list` | | `{items: GlucoseOut[]}` (inside the window) | | terms, health_data | n/a |
| `GET /v1/glucose/link-suggestion?measured_at&context` | `glucose_link_suggest` | | `{linked_local_date, linked_meal_slot_id, slot_label} \| null` | | terms, health_data | n/a |

```text
GlucoseIn {
  member_id?: uuid
  value: number                       // as typed
  unit: "mg_dl" | "mmol_l"            // required, never inferred
  measured_at?: datetime              // default now
  context?: "fasting" | "before_meal" | "after_meal" | "bedtime" | "random"   // default random
  after_meal_timing?: "about_1h" | "about_2h" | "not_sure"                   // required iff after_meal
  link?: { local_date: date, meal_slot_id: uuid } | null                     // omitted = auto-suggest for before/after meal; null = no link
  note?: string(≤200)
  confirm_unusual?: boolean
  confirm_duplicate?: boolean
  client_id?: uuid
}

GlucoseOut {
  id, member_id, measured_at, local_date, local_time: "HH:MM",
  value_mgdl: number,                         // unrounded canonical
  entered: { value, unit },
  display: { value: number, unit },           // in the preferred unit, rounded per §4.1
  display_other: { value, unit },             // the other unit, for confirm screens and the CSV
  context, after_meal_timing,
  range_position: "below" | "within" | "above" | "no_range",
  very_low_note: boolean,                      // true only if SUGAR_LOW_NOTE_ENABLED, the YAML value is set (Q3) and the reading is below it
  link: { local_date, meal_slot_id, slot_label_key, slot_custom_label, source: "auto" | "user", meal_has_items: boolean } | null,
  note: string | null, source: "manual", created_at, updated_at, deleted_at: datetime | null
}
```

**`labs`** (`app/features/labs/`, prefix `/v1/labs`)

| Method and path | operation_id | Request | Response | Errors | Consent | Rate limit |
|---|---|---|---|---|---|---|
| `POST /v1/labs` | `labs_create` | `{member_id?, test, value, unit, taken_on, note?, confirm_unusual?, client_id?}` | 201 `LabOut` (200 on repeat) | `lab_unit_not_allowed`, `lab_out_of_range`, `lab_needs_confirm`, `taken_on_in_future`, `taken_on_too_old`, `validation_error` | terms, health_data | `lab_writes` 50/day |
| `GET /v1/labs?test` | `labs_list` | | `{items: LabOut[], next_cursor}` | | terms, health_data | n/a |
| `PATCH /v1/labs/{id}` | `labs_update` | partial | `LabOut` | as create, `lab_not_found` | terms, health_data | `lab_writes` |
| `DELETE /v1/labs/{id}` | `labs_delete` | | 200 `{id, deleted_at, restore_until}` | `lab_not_found` | terms | n/a |
| `POST /v1/labs/{id}/restore` | `labs_restore` | | `LabOut` | `lab_not_found`, `lab_restore_expired` | terms, health_data | `lab_writes` |
| `GET /v1/labs/trend?test` | `labs_trend_get` | | `{test, unit, points: [{taken_on, display, entered}], change_since_previous: {value, unit, previous_on} \| null}` | | terms, health_data | n/a |

`LabOut {id, test, taken_on, value_canonical, entered: {value, unit}, display: {value, unit}, converted: {value, unit} | null, note, deleted_at}`. There is no field for a range, a band or an estimate.

**`sugar`** (`app/features/sugar/`, prefix `/v1/sugar`)

| Method and path | operation_id | Request | Response | Errors | Consent | Rate limit |
|---|---|---|---|---|---|---|
| `GET /v1/sugar/settings` | `sugar_settings_get` | | `SugarSettingsOut` (defaults if no row) | | terms, health_data | n/a |
| `PUT /v1/sugar/settings` | `sugar_settings_put` | `{glucose_unit, range: {low, high, unit} \| null, carb_guide: {enabled, same_for_all_g?, per_slot?: [{meal_slot_id, grams}]}}` | `SugarSettingsOut` | `sugar_range_invalid`, `carb_guide_out_of_range`, `meal_slot_not_found` | terms, health_data | `sugar_settings` 30/day |
| `PUT /v1/sugar/settings/unit` | `sugar_unit_put` | `{glucose_unit}` | `SugarSettingsOut` | | **terms** (display only, like the diary eye toggle) | `sugar_settings` |
| `DELETE /v1/sugar/settings` | `sugar_settings_delete` | | 204 (clears range and guide) | | terms | n/a |
| `GET /v1/sugar/day?date` | `sugar_day_get` | | `SugarDayOut` (merged timeline, §5.1) | `date_in_future` | terms, health_data | n/a |
| `GET /v1/sugar/summary?from&to` | `sugar_summary_get` | 7–92 days | `SugarSummaryOut` (§5.4) | `date_range_too_long`, `date_range_too_short` | terms, health_data | n/a |
| `GET /v1/sugar/meal-readings` | `sugar_meal_readings_get` | | `MealReadingsOut {enabled, ready, progress: {readings, needed_readings, days, needed_days}, timing_bucket, usual: Display, excluded_readings, higher: Item[], similar_or_lower: Item[], caveat_keys}` | `sugar_insights_disabled` (when the flag is off, which is the shipped state; Q5) | terms, health_data | n/a |
| `POST /v1/sugar/report` | `sugar_report_create` | §8.1 | `application/pdf` or `text/csv` | `sugar_report_range`, `sugar_report_empty` | PDF: terms, health_data. CSV: **terms** only (Q13) | `sugar_reports` 20/day |

`SugarDayOut {date, timezone, items: (MealItem | ReadingItem)[], carbs_day: {total_g, incomplete}, numbers_hidden, pending_clinician_review: true}`, where `MealItem = {kind: "meal", meal_slot_id, label_key, custom_label, first_at, last_at, entries: [{name, portion_line, carbs_g, incomplete, gi: GiNote | null}], carbs: {total_g, incomplete}, carb_guide_g: number | null, readings_linked: uuid[]}` and `ReadingItem = {kind: "reading", reading: GlucoseOut}`.

**`foods_get` extension** (diary §6.3): `FoodDetailOut` gains `glycaemic: {gi, gi_band, gl, gl_band, gl_serving_g, reference_food, source: {key, title, locator}} | null`. Null means unknown.

**`reminders`** (`app/features/reminders/`, prefix `/v1/reminders`)

| Method and path | operation_id | Request | Response | Errors | Consent | Rate limit |
|---|---|---|---|---|---|---|
| `GET /v1/reminders` | `reminders_list` | | `{items: ReminderOut[], settings: ReminderSettingsOut}` | | terms, health_data (Q12) | n/a |
| `POST /v1/reminders` | `reminders_create` | `{member_id?, text, times, weekdays, enabled?, client_id?}` | 201 `ReminderOut` | `reminder_limit`, `reminder_text_invalid`, `reminder_times_invalid` | terms, health_data | `reminder_writes` 100/day |
| `PATCH /v1/reminders/{id}` | `reminders_update` | partial | `ReminderOut` | `reminder_not_found`, as above | terms, health_data | `reminder_writes` |
| `DELETE /v1/reminders/{id}` | `reminders_delete` | | 204 (hard delete; no history kept) | `reminder_not_found` | terms | n/a |
| `PUT /v1/reminders/settings` | `reminder_settings_put` | `{quiet_start?, quiet_end?, paused_until?, show_text_on_web?}` | `ReminderSettingsOut` | `quiet_hours_invalid` | terms | `reminder_writes` |
| `POST /v1/reminders/push-subscriptions` | `reminders_push_subscribe` | Web Push subscription (web only) | 204 | `validation_error` | terms | `reminder_writes` |

**New error codes** (each needs `error.<code>` in en, hi and mr): `glucose_out_of_range`, `glucose_needs_confirm`, `glucose_precision`, `glucose_possible_duplicate`, `glucose_timing_required`, `glucose_link_not_allowed`, `glucose_not_found`, `glucose_restore_expired`, `measured_at_in_future`, `measured_at_too_old`, `date_range_too_short`, `sugar_member_not_enabled`, `sugar_range_invalid`, `carb_guide_out_of_range`, `sugar_insights_disabled`, `sugar_report_range`, `sugar_report_empty`, `lab_unit_not_allowed`, `lab_out_of_range`, `lab_needs_confirm`, `lab_not_found`, `lab_restore_expired`, `taken_on_in_future`, `taken_on_too_old`, `reminder_limit`, `reminder_text_invalid`, `reminder_times_invalid`, `reminder_not_found`, `quiet_hours_invalid`. Reused: `date_in_future`, `date_range_too_long`, `meal_slot_not_found`, `meal_slot_archived`, `member_not_found`, `consent_required`, `rate_limited`, `validation_error`.

**Rate-limit buckets** (in `BUCKETS` and `Settings`): `glucose_writes` (day, 200), `lab_writes` (day, 50), `sugar_settings` (day, 30), `sugar_reports` (day, 20), `reminder_writes` (day, 100).

### 12.5 Consent (the Q13 pattern from the diary)

| Route group | Purposes | Why |
|---|---|---|
| `glucose_*`, `labs_*`, `sugar_settings_get/put`, `sugar_day_get`, `sugar_summary_get`, `sugar_meal_readings_get`, `sugar_report_create` | `terms` + `health_data` | Glucose readings, lab results and personal ranges are health data |
| `reminders_*` (except delete and settings) | `terms` + `health_data` (Q12) | The text is free-form and likely names a health matter |
| `glucose_delete`, `labs_delete`, `reminders_delete`, `sugar_settings_delete` | `terms` | Erasure is never gated |
| `sugar_unit_put`, `reminder_settings_put`, `reminders_push_subscribe` | `terms` | Display or delivery preferences only |
| `sugar_report_create` with `format: csv` | `terms` (Q13) | Data-access right to the user's own stored data after `health_data` is withdrawn |

- `REQUIRED` in `app/core/consent.py` gains `"sugar": ("terms", "health_data")` and `"sugar_prefs": ("terms",)` (the latter also used for the CSV path), gated per route first so a refused call costs no quota (as ADR 0022 does).
- **Withdrawal stops processing and keeps stored data** (ADR 0018 option 1, as for targets in ADR 0022). Screens show the inline "allow health details" card; stored readings, labs and reminders stay and reappear on re-consent. Delete stays available. Android cancels scheduled local reminders on withdrawal; the web stops sending pushes.
- **Q13 (decided):** the CSV export of the user's own data stays available after withdrawal on `terms` alone, as a data-access right. The PDF, the report options and every screen stay gated. In `sugar_report_create`, the consent check depends on `format`.
- **Consent text:** the `health_data` purpose text must name glucose readings, lab results and reminder text. That is a version bump, so existing users re-grant at first use (the existing `consent_required` with `details.purposes` handles it).
- **New ADR 0023:** "Sugar Control is information-only logging; health_data gates it; no estimation, dosing or alerts". It records the DO-NOT-BUILD list as an architectural constraint, the no-LLM and no-analytics decisions, and the invariance test.

### 12.6 DPDP and privacy notes

- **Residency:** all rows in Supabase Mumbai; reports generated on Cloud Run Mumbai and not stored; no third party receives Sugar Control data. No LLM call carries it (AGENTS rule 6 is met by not calling one).
- **Analytics:** **no Sugar Control events at all** (Q17). Even an event named `glucose_logged` would reveal that a person tracks glucose, which is health data in itself. The three allow-lists stay unchanged, and a test asserts that no event or property name contains `glucose`, `lab`, `sugar`, `reminder` or `a1c`. Sentry and logs carry counts and error codes only, never values or notes (the existing scrubber gets new field names: `value`, `entered_value`, `value_mgdl`, `note`, `text`).
- **Retention:** active data stays until the user deletes it or the account; soft-deleted readings and labs are purged by the retention job after 30 days (Q16); reports are never stored (Q9).
- **Erasure:** `DELETE /v1/me` removes all six account-owned tables.
- **Access:** the CSV doubles as "download my Sugar Control data".
- **Children:** single user for now, and the account holder is the only member. Whether an account holder under 18 may use Sugar Control without verifiable parental consent is a lawyer question (R8); until answered, the API refuses Sugar Control writes for a primary member whose birth year shows under 18 (`422 sugar_not_available_minor`, mirroring the diary's targets rule), and allows them when the age is unknown with a one-time "for adults" notice [proposal].
- **Lawyer questions** (added to the existing list): health_data text update; keeping data after withdrawal (as ADR 0018); CSV access after withdrawal (Q13, decided as allowed on `terms`; the lawyer confirms); minors.

---

## 13. Client screens (Android and web parity) and i18n keys

### 13.1 General rules

- Both clients render only API values: display values, range positions, statistics, link suggestions, carb totals, GI notes. The only client-side logic is input validation hints (the min and max for the selected unit, read from a shared fixture, so the form can disable Save before calling the API).
- **Colours:** no verdict colours anywhere in Sugar Control. Readings use neutral tokens; range notes are text plus an icon; insufficient data uses the grey "not enough data" style. New design tokens: `sugar.reading`, `sugar.reading-muted`, `sugar.meal`, `sugar.pattern-band`, `sugar.pattern-median`, all derived from brand and neutral palettes (`just tokens`).
- **Every screen with numbers** shows "Information, not medical advice" and, where a YAML number is involved, "pending clinician review".
- Android keeps an offline queue (drift) for readings and labs, keyed by `client_id`; a queued item shows "waiting to sync". The web is online-only and says so (existing copy).
- Accessibility: every chart has a table equivalent; range notes are never colour-only; large-text layouts tested at 200 %.

### 13.2 Screens

1. **Sugar tab (home of the feature):** latest reading card; "Add reading" primary button; today's merged timeline (preview); entries to Patterns, Labs, Report, Reminders, Settings. Empty state: "No readings yet. Add one when you next check."
2. **Add or edit reading (sheet):** large numeric input; the unit shown and switchable; context chips; after-meal timing chips when relevant; time (default now); suggested meal link with "change" and "no link"; note. States: unusual-value confirm (both units shown), duplicate confirm, the static low-reading note (Q3; absent unless the server returns `very_low_note`), consent card, offline queued (Android), API errors.
3. **Day timeline:** date switcher; meal cards (slot name, items, carbs, guide, GI notes) and reading chips in time order; tap a meal to see linked readings; tap a reading to edit. Delete gives an undo snackbar.
4. **Patterns:** range picker (7, 14, 30, 90 days); summary table by context; time-of-day chart with greyed insufficient windows; "share of your readings within your range" only when set; data-count line.
5. **Meals and your readings** (S6, flag off; the screen and its entry point are not shown while the flag is off, Q5): progress card until the gate is met ("7 of 10 after-meal readings linked, on 4 of 5 days"); then the two lists with the fixed caveats above them.
6. **Labs:** list grouped by test with the latest value and date; add/edit form (test, value, unit, date, note); per-test trend (points and table) with "change since previous".
7. **Doctor report:** range (14, 30, 90 days, custom), format (PDF, CSV), language (en, hi, mr), toggles (include my name, include notes, include meals and your readings only when the S6 flag is on and the gate is met), Generate; after `health_data` withdrawal only the CSV option is offered, with a line explaining why; then share (Android) or download (web).
8. **Reminders** (S8, last; Q10): list with switches; add/edit (text, times, weekdays); Pause all; Quiet hours; on Android a notification-permission prompt with an explanation; on web, the push permission and "show text in notifications" (off).
9. **Sugar settings:** unit; your range (optional, empty by default, with the general-reference information card that is never applied); carb guide (optional, off by default, empty input); recently deleted (readings and labs, 30 days); link to diary number settings.
10. **Onboarding** (§11) and the food-card GI row (§6.3).

### 13.3 Modes and tabs (`packages/test-fixtures/modes/layouts.json`)

- Add the destination `sugar`.
- For the mode that serves the Sugar Control chip (today `health_condition`, which also serves Heart Health until the chip rename splits them): tabs `home, scan, diary, sugar, profile` (Q18; family moves to More while Family is deferred). Home cards: `sugar_latest`, `meal_carbs`, `today_sugar_salt`, `claims_tip`, `recent_scans`. A Heart Health user without a blood-sugar condition sees the existing layout; the API's user-type and member data decide, and the clients read the mode from `layouts.json` as today.
- The reachability test (every destination reachable in every mode) and the invariance test (scan and verdicts identical in every mode) are extended to `sugar`.

### 13.4 i18n keys

All keys go into `packages/i18n/messages/en.json` first, then `hi.json` and `mr.json` in the same PR, and into `NATIVE_REVIEW.md`. ICU placeholders. English is our own draft copy.

| Key | en draft |
|---|---|
| `sugar.title` | Sugar |
| `sugar.chip` | Sugar Control |
| `sugar.disclaimer` | Information, not medical advice. SmartNutri does not diagnose or treat. |
| `sugar.pending_review` | Some numbers here are pending clinician review. |
| `sugar.add_reading` | Add reading |
| `sugar.reading.value` | Reading |
| `sugar.unit.mg_dl` / `sugar.unit.mmol_l` | mg/dL / mmol/L |
| `sugar.context.fasting` | Fasting |
| `sugar.context.before_meal` | Before a meal |
| `sugar.context.after_meal` | After a meal |
| `sugar.context.bedtime` | Bedtime |
| `sugar.context.random` | Any other time |
| `sugar.timing.about_1h` / `.about_2h` / `.not_sure` | About 1 hour after / About 2 hours after / Not sure |
| `sugar.range.below` / `.within` / `.above` | Below your range / Within your range / Above your range |
| `sugar.confirm_unusual` | Is this the number you meant to type? {value} {unit} ({other_value} {other_unit}) |
| `sugar.confirm_duplicate` | You saved {value} {unit} at {time} already. Save this one too? |
| `sugar.very_low_note` | If you feel unwell, follow the plan your doctor gave you, or get medical help. (Written in en, hi and mr now; never returned until clinician sign-off and the flag.) |
| `sugar.link.linked_to` | Linked to {meal} |
| `sugar.link.change` / `.none` | Change / No link |
| `sugar.link.meal_empty` | This meal has no items now. |
| `sugar.deleted` | Reading deleted. |
| `sugar.undo` | Undo |
| `sugar.recently_deleted` | Recently deleted |
| `sugar.recently_deleted.help` | Deleted items stay here for 30 days, then they are removed for good. |
| `sugar.restore` | Restore |
| `sugar.empty` | No readings yet. Add one when you next check. |
| `sugar.queued` | Waiting to sync |
| `sugar.consent_card` | To log readings and lab results, allow SmartNutri to use your health details. |
| `sugar.timeline.title` | Your day |
| `sugar.meal.carbs` | {grams} g carbs |
| `sugar.meal.carbs_incomplete` | At least {grams} g carbs. Some items have no carb value. |
| `sugar.meal.guide_of` | {grams} g of your {guide} g guide |
| `sugar.meal.guide_over` | {grams} g · your guide is {guide} g |
| `sugar.patterns.title` | Patterns |
| `sugar.patterns.readings_days` | {readings, plural, one {# reading} other {# readings}} on {days, plural, one {# day} other {# days}} |
| `sugar.patterns.not_enough` | Not enough readings |
| `sugar.patterns.median` / `.middle_half` / `.lowest` / `.highest` / `.average` | Middle value / Middle half of readings / Lowest / Highest / Average |
| `sugar.patterns.window.late_night` … `.night` | Late night / Early morning / Morning / Afternoon / Evening / Night |
| `sugar.patterns.within_share` | {within} of {total} readings were within the range you set ({low}–{high} {unit}). |
| `sugar.insights.title` | Meals and your readings |
| `sugar.insights.progress` | {readings} of {needed} after-meal readings linked to meals, on {days} of {needed_days} days. |
| `sugar.insights.higher` | Readings after these meals were higher than your usual |
| `sugar.insights.similar` | Readings after these meals were close to or below your usual |
| `sugar.insights.item` | {meals, plural, one {# meal} other {# meals}} · middle value {value} {unit} (your usual {usual} {unit}) |
| `sugar.insights.caveat_mixed` | Meals usually have several foods. This shows what you ate around a reading, not what caused it. |
| `sugar.insights.caveat_other` | Portion size, activity, sleep, illness and medicines also change readings. |
| `sugar.insights.caveat_advice` | Information from your own logs, not medical advice. Talk to your doctor or dietitian before changing what you eat. |
| `sugar.gi.value` | GI {gi} ({band}) · source: {source}, p. {page} |
| `sugar.gi.unknown` | GI not known for this food |
| `sugar.gi.band.low` / `.medium` / `.high` | low / medium / high |
| `sugar.gi.info` | GI depends on the variety, how the food is cooked and what it is eaten with. This is a reference value, not a measurement of your meal. |
| `sugar.labs.title` | Lab results |
| `sugar.labs.test.hba1c` / `.fasting_glucose` / `.total_cholesterol` / `.ldl` / `.hdl` / `.triglycerides` | HbA1c / Fasting glucose / Total cholesterol / LDL cholesterol / HDL cholesterol / Triglycerides |
| `sugar.labs.taken_on` | Test date |
| `sugar.labs.converted` | {value} {unit} (converted) |
| `sugar.labs.change` | Change since your previous result: {change} {unit} (on {date}) |
| `sugar.labs.as_entered` | As you entered it from your lab report |
| `sugar.report.title` | Glucose and food log |
| `sugar.report.subtitle` | Information the user entered in SmartNutri. Not medical advice. SmartNutri does not diagnose or treat. |
| `sugar.report.footer` | Information, not medical advice. Values as entered by the user; meter and lab values are not checked by SmartNutri. Thresholds pending clinician review. |
| `sugar.report.generate` | Create report |
| `sugar.report.format.pdf` / `.csv` | PDF / CSV |
| `sugar.report.language` | Report language |
| `sugar.report.csv_only_note` | Your health details are switched off, so only the CSV of your saved data can be downloaded. |
| `sugar.report.include_name` / `.include_notes` / `.include_meal_readings` | Include my name / Include my notes / Include "meals and your readings" |
| `sugar.report.section.summary` / `.pattern` / `.meals` / `.days` / `.labs` | Summary / Time of day / Meals and carbs / Day by day / Lab results |
| `sugar.reminders.title` | Reminders |
| `sugar.reminders.placeholder` | Write your reminder |
| `sugar.reminders.note` | A reminder you set. SmartNutri does not give medicine advice. |
| `sugar.reminders.pause_all` | Pause all reminders |
| `sugar.reminders.quiet_hours` | Quiet hours |
| `sugar.reminders.notification_title` | SmartNutri reminder |
| `sugar.settings.unit` | Glucose unit |
| `sugar.settings.range` | Your range (optional) |
| `sugar.settings.range_help` | If your doctor gave you a range, you can add it here. We use it only to label your readings. We never set one for you. |
| `sugar.settings.reference_card` | General reference values published for many non-pregnant adults: before meals {low}–{high} mg/dL; 1–2 hours after a meal, under {peak} mg/dL. Your doctor may give you different numbers. |
| `sugar.settings.carb_guide` | Carb guide per meal (optional) |
| `sugar.settings.carb_guide_help` | If your doctor or dietitian suggested an amount of carbs per meal, add it here. SmartNutri does not suggest a number. |
| `sugar.onboarding.more_q` | Would you like to tell us more? This is optional. |
| `sugar.onboarding.diabetes` / `.prediabetes` / `.pcos` / `.prefer_not` / `.just_watching` | Diabetes / Prediabetes / PCOS / Prefer not to say / I just want to keep an eye on my sugar |
| `sugar.onboarding.profile_note` | Sugar checks on scanned foods use the conditions in your profile. You can add one any time. |
| `sugar.onboarding.what` | Log readings and lab results next to your meals, see your own patterns, and share a report with your doctor. |
| `error.<code>` | One per new error code in §12.4 |

---

## 14. Tests

TDD for everything in `app/scoring/glucose.py`, the endpoints and the client data layers (AGENTS working conventions).

### 14.1 Unit conversion (property tests, Hypothesis)

- For every whole mg/dL in 20–600: storing then displaying in mg/dL returns the same integer.
- For every mmol/L with one decimal in the hard range: the display in the entered unit equals the entered value exactly; the converted mg/dL is within 0.5 of `value × 18.016`; converting the stored value back to mmol/L rounds to the entered value.
- Monotonic: a larger entered value never gives a smaller stored or displayed value, in either unit.
- Boundaries: 19, 20, 600, 601 mg/dL and their mmol/L equivalents hit the right error; precision errors for 110.5 mg/dL and 6.25 mmol/L.
- The API rejects a write with no unit; no code path infers a unit from magnitude (a test feeds 6.0 and 110 with each unit and checks the result follows the stated unit).
- Range thresholds survive a unit switch unchanged (stored mg/dL).
- Lab conversions: HbA1c % ↔ mmol/mol round trip; cholesterol and triglyceride factors; per-test allowed units.
- **Shared fixture** `packages/test-fixtures/sugar/units.json` (input, unit, expected stored, expected display in both units, expected error). The API runs all of it; Android and web run the display-format and input-hint rows.

### 14.2 Statistics golden fixtures (`packages/test-fixtures/sugar/stats/*.json`)

- Summary by context: odd and even counts; ties; a single reading; the quartile method pinned; mean; min and max.
- Time-of-day windows: readings on window edges (03:59, 04:00, 23:59, 00:00); a window below the minimum returns `insufficient`.
- Local time: a reading saved in `Asia/Kolkata`, then the account time zone changed to `Europe/London`: the reading keeps its local date and window; a DST-zone case to prove frozen local minutes.
- Within-range share: absent when no range; absent below 10 readings; correct counts at the exact low and high boundary (boundary values count as within).
- Insights: gate not met (9 readings; 10 readings on 4 days); gate met; mixed timing buckets (the minority bucket is excluded and counted); a food in 2 meals is dropped; a food twice in one meal counts once; quick add excluded; a deleted reading excluded; a meal whose items were deleted excluded; sorting and the 5-item cap; the +20 boundary.
- Link suggestion: 14, 15, 240 and 241 minutes; nearest wins; just after midnight links to the previous day's dinner; archived slot handling.
- **No estimate:** a test walks every response schema in `openapi.json` and every `sugar.*` i18n key, and fails if a field or key contains `estimated`, `ea1c`, `gmi` or `a1c_estimate`; another asserts that no function in `glucose.py` takes glucose readings and returns an HbA1c-shaped value (a name and signature check backed by review).

### 14.3 API, RLS, consent and invariance

- RLS: another account cannot read, update, delete or restore any row (direct SQL as `authenticated` and through the API).
- Consent: each route returns `403 consent_required` without `health_data` except delete and the preference routes; withdrawal keeps rows; re-consent shows them again.
- Idempotency: repeated `client_id` returns 200 and the original row; parallel duplicate creates produce one row.
- Soft delete: hidden from list, summary, day, insights and report at once; restore inside and outside the window; the retention job purges only expired rows (dry-run counts only).
- `DELETE /v1/me` erases all Sugar Control tables (`test_delete_me.py`).
- `SUGAR_FAMILY_ENABLED=false` rejects other members; under-18 primary member refused.
- **Invariance:** `analyze` responses for the full verdict fixture set are byte-identical with and without Sugar Control data, settings, ranges and carb guides on the member (as `tests/api/targets/test_invariance.py` does for targets).
- Analytics: the three `ALLOWED_EVENTS` lists are unchanged, and no name or property contains the banned words (§12.6). Log capture during the whole suite contains no reading value, note or reminder text.

### 14.4 Report snapshot and privacy

- **CSV golden files** (byte-exact) for a fixture member in en, hi and mr, mg/dL and mmol/L.
- **PDF snapshot:** text extracted from the generated PDF (for example with `pypdf`) compared against a golden text file per language; page count; the disclaimer line on page 1 and the footer on every page; Devanagari glyphs present (no tofu: a font-coverage check).
- **Privacy:** no name unless `include_name`; no notes unless `include_notes`; no insights unless the flag, the gate and the toggle are all on; a note containing `=HYPERLINK(...)` is neutralised in the CSV; another member's or account's data never appears; nothing is written to storage or the DB during generation (storage listing and row counts unchanged); response headers forbid caching (`Cache-Control: no-store`).
- No "estimated", score, verdict or colour words in the extracted text.

### 14.5 Client tests (Android widget, web component, Playwright e2e)

- Add reading: unit switch, context and timing chips, unusual and duplicate confirms, offline queue (Android), undo after delete.
- Timeline renders API order unchanged; meal carbs incomplete state; guide text; GI unknown text.
- Patterns: greyed windows, table equivalent, no range share without a range.
- Insights: progress state; caveats always visible above the lists.
- Labs: add, converted display, trend points without connecting lines, change line.
- Report: toggles default off; download (web) and share (Android) flows.
- Reminders: no suggestion UI exists; quiet-hours and pause; lock-screen visibility set to private (Android).
- Mode reachability for `sugar`; scan and verdict screens unchanged in every mode.
- No verdict colour token used anywhere under the Sugar Control feature folders (a lint-style test on both clients).

### 14.6 Tests that pin the decisions

- **Q3:** with the flag off or `very_low_note_below_mgdl` null, no response carries `very_low_note` for any value; with both on, the note appears only below the value and is the same static key; no colour token, sound or push is attached; there is no high-reading note.
- **Q4:** a new member has no range; no code path writes `range_low_mgdl` or `range_high_mgdl` except the user's own settings call; `range_position` is `no_range` for every reading until then.
- **Q5:** `sugar_meal_readings_get` returns `sugar_insights_disabled` with the flag off (the default); the report ignores `include_meal_readings` while it is off.
- **Q6:** the carb guide is disabled for a new member; YAML has no suggested grams; no response or fixture pre-fills a value.
- **Q7:** every `glycaemic_reference` seed row has the ICMR-NIN 2024 source key, an Annexure III page locator and a verifier; packaged, custom, recipe and quick-add foods return `glycaemic: null`; GL is never computed.
- **Q8:** no endpoint, field or `sugar.*` key is PCOS-specific, and nothing records a cycle (the onboarding condition choice is the only mention).
- **Q9 and Q13:** the PDF renders in en, hi and mr and nothing is stored; the CSV succeeds with only `terms` after `health_data` is withdrawn, while the PDF, the screens and other routes return `consent_required`.
- **Q12:** every reminder route except delete and settings returns `consent_required` without `health_data`.
- **Q14:** `analyze` output is identical for the same member with and without Sugar Control onboarding (covered by the invariance test).
- **Q15:** a reading exactly 90 days back is accepted and 91 days back returns `measured_at_too_old`.
- **Q16:** a deleted reading or lab is restorable on day 30 and returns `410` after that; the retention job purges only rows past 30 days.
- **Q17:** see §14.3: no analytics event or property relates to Sugar Control.
- **Q18:** `layouts.json` for the Sugar Control mode lists `home, scan, diary, sugar, profile`, with family reachable through More.

---

## 15. Phased slices

Each slice runs **API (`api-builder`) → `just contract` → Android (`flutter-builder`) ∥ web (`web-builder`) → `nutrition-safety-reviewer`**, and is done only when `just test` passes and the shared fixtures pass on all three (CLAUDE.md, AGENTS rule 11). Every slice touches health data or health-adjacent UI, so every slice gets the safety review. Each slice updates `docs/FEATURE_PARITY.md` under a new row **F22 Sugar Control**.

| # | Slice | API | Clients | Ready when | Depends on |
|---|---|---|---|---|---|
| S1 | **Glucose log core** | Migration `sugar_settings_glucose`; `glucose.yaml` (units, limits, 90-day back-entry, 30-day retention, the null low-note value); `SUGAR_LOW_NOTE_ENABLED` flag (default off); `glucose.py` conversion and range position; `glucose_*` CRUD, delete, restore, deleted list; `sugar_settings_*`, `sugar_unit_put`; consent entries; rate limits; retention-job purge; ADR 0023; unit fixtures | Sugar tab with readings list by day, add/edit sheet, undo, recently deleted (30 days), settings (unit, user-set range, reference card), onboarding (§11), `sugar` destination and the Home, Scan, Diary, Sugar, Profile tabs in `layouts.json` (Q18) | Unit fixtures and RLS green on all three; invariance test green | Diary slice 1 (accounts.timezone, 0008) |
| S2 | **Timeline, meal link, carbs per meal, carb guide** | Migration `sugar_carb_guides`; link suggestion; `sugar_day_get` built on the diary day function; carb guide in settings | Day timeline, link control, meal cards with carbs and guide, home cards `sugar_latest` and `meal_carbs` | Link-window fixtures green; carbs identical to `diary_day_get` on the fixture week | S1; diary slices 2 and 2b (meal slots) |
| S3 | **Patterns** | `sugar_summary_get`; stats fixtures | Patterns screen with chart and table | Stats golden fixtures green on the API; display rows on clients | S1 |
| S4 | **Lab log** | Migration `sugar_lab_results`; `labs_*`, `labs_trend_get`; lab fixtures | Labs list, form, trends | Lab conversion fixtures green; no-estimate test green | S1 |
| S5 | **Doctor report** | `sugar_report_create` (PDF in en, hi, mr and CSV, never stored; CSV on `terms` after withdrawal); WeasyPrint and Noto fonts in the API image; report strings from i18n | Report screen, share and download | CSV golden and PDF text snapshots green in en, hi, mr; privacy and Q13 consent tests green; image size and cold start measured | S2, S3, S4 |
| S6 | **Meals and your readings** (flag `SUGAR_INSIGHTS_ENABLED`, **stays off**) | `sugar_meal_readings_get`; insight fixtures | Insights screen, report toggle | Insight fixtures green; the flag stays off until the clinician signs off the wording, gates and the +20 value and testers have logged for about 4 weeks (10+ after-meal readings on 5+ days each); turning it on is a separate decision | S2 (Q5) |
| S7 | **GI and GL** | Migration `sugar_glycaemic_reference`; seed typed by hand from ICMR-NIN 2024 Annexure III only, one source row with a page reference per value; `foods_get` extension | GI row on the food card and in meal items | Every seeded row has an Annexure III page locator and a verifier; unknown shown everywhere else | Diary slice 3 (foods); Q7 |
| S8 | **Reminders** (last slice) | Migration `sugar_reminders`; `reminders_*` behind `health_data`; web push sender job | Reminders screens; Android local notifications; web service worker | Delivery tested on a device and in Chrome; lock-screen privacy verified; the Q12 consent test green | S1–S5 shipped (Q10); Q12 |

After S1, slices S3 and S4 can run in parallel with S2; S5 follows S2–S4. S6 and S7 are independent of each other. S8 is built last, only after S1–S5 have shipped (Q10). S6 ships dark: its flag stays off.

---

## 16. Decisions (resolved)

All 18 questions are answered in `DECISIONS.md` (binding for the build; Q1–Q5 one at a time, Q6–Q18 at the recommended option at the user's request on 2026-11-07). This table says what each decision is and where the spec applies it. The options that were not chosen have been removed from this document.

| # | Topic | Decision (summary) | Applied in |
|---|---|---|---|
| Q1 | Default glucose unit | mg/dL by default; mmol/L in settings and on the entry sheet | §4.1, §12.2, §13.2 |
| Q2 | Meal-context tags | Fasting, before a meal, after a meal (about 1 h, about 2 h, not sure), bedtime, any other time | §4.2, §12.2 |
| Q3 | Low-reading note | One static neutral line below a clinician-set value; no colour, no alert; gated by YAML (null until sign-off) and the flag `SUGAR_LOW_NOTE_ENABLED`; ships only after sign-off | §4.3, §12.3, §12.4, §13.4, §14.6, S1, R4 |
| Q4 | Personal range | User-set only, empty by default; the general-reference card is information and never applied | §4.3, §12.2, §13.2, §14.6 |
| Q5 | Meals and your readings | Slice S6 behind a flag that stays off until clinician review and about 4 weeks of tester data; the user's own readings only (10+ after-meal readings on 5+ days) | §5.3, §15 (S6), §14.6, R3 |
| Q6 | Per-meal carb guide | Optional and off by default; the user types their own grams; no default number ships | §6.2, §11, §14.6, R10 |
| Q7 | GI and GL source | ICMR-NIN 2024 Annexure III only, typed by hand with a page reference per row; generic foods only; GL only where the source states it; unknown otherwise | §6.3, §12.2, §15 (S7), §14.6, R11 |
| Q8 | PCOS scope | Same tools as everyone; no PCOS-specific features, no cycle tracking; revisit after launch | §1.3, §10, §14.6 |
| Q9 | Doctor report | PDF in en, hi or mr plus CSV; on demand; never stored | §8, §15 (S5), R14 |
| Q10 | Reminders | Not in the first release; the last slice, S8, after S1–S5 ship | §9, §15 (S8), R16 |
| Q11 | Glucometer and CGM | Deferred; manual entry only; revisit with Health Connect in v2 | §1.3, §12.2 |
| Q12 | Reminder consent | `health_data` | §9, §12.5, §14.6 |
| Q13 | CSV after withdrawal | CSV allowed on `terms` alone as a data-access right; the PDF and all screens stay gated | §8.1, §12.4, §12.5, §14.6 |
| Q14 | Chip without a condition | Blood-sugar scan checks apply only once diabetes, prediabetes or PCOS is saved; onboarding offers it optionally; no scoring change | §11, §14.6 |
| Q15 | Back-entry window | 90 days | §4.4, §14.6 |
| Q16 | Deleted readings and labs | Undo snackbar, plus "Recently deleted" for 30 days, then purged by the retention job | §4.5, §12.6, §14.6 |
| Q17 | Analytics | No Sugar Control events at all | §12.6, §14.3 |
| Q18 | Tabs | Home, Scan, Diary, Sugar, Profile; Family moves to More while deferred | §13.3, §14.6, S1 |

---

## 17. Risks and mitigations

| # | Risk | Kind | Mitigation |
|---|---|---|---|
| R1 | **Classified as software as a medical device in India.** CDSCO's medical-device-software guidance under MDR 2017 (draft 2025-10-21; a final version is reported [unverified]) could treat glucose software as SaMD. | Regulatory (CDSCO) | Stay on the information side: the DO-NOT-BUILD list (§1.4) is enforced in ADR 0023, tests (no estimate, no alerts, no dose fields) and the safety review. Logging and display of user-entered data only; no diagnosis, prediction, dosing or alarms. **USER:** get a short regulatory opinion before launch, and keep store listing and marketing copy free of treatment claims. |
| R2 | **US FDA view** if the app is ever offered in the US. FDA treats apps that help people log and track their own health data as low risk under its mobile-app and device-software policy [unverified exact policy text]; dose calculators are devices. | Regulatory (FDA SaMD) | Same boundary as R1. No US launch is planned; recheck before any. |
| R3 | **"Meals and your readings" read as advice** ("stop eating rice"), or confounded by other foods, portions or medicines. | Clinical | Descriptive wording, banned-word list, fixed caveats above the lists, data gate, one timing bucket, flag off until clinician review, never in verdicts or the LLM. |
| R4 | **A low reading and a user who relies on the app.** No alarm by design, so a dangerous low is not flagged. | Clinical | The app never claims to monitor; the copy says information only. Q3's static note (shown only after clinician sign-off and with its flag on) is the only response; until then there is none. Onboarding and settings say SmartNutri does not alert. |
| R5 | **Unit mix-up** (6.1 typed with mg/dL selected, or 110 with mmol/L). | Clinical, data quality | Unit required on every write, never inferred; hard limits catch most mix-ups; the confirm shows both units; ranges stored in mg/dL; property tests. |
| R6 | **Wrong or duplicate entries** skew patterns and the report. | Data quality | Duplicate check, confirm band, edit and restore, data counts beside every statistic, "values as entered" on the report. |
| R7 | **Time-zone and midnight errors** move readings between days or windows. | Data quality | Local date and minute frozen at write; explicit edge fixtures; link window crosses midnight deliberately. |
| R8 | **Children's data** (an under-18 account holder, or a parent logging a child with type 1 diabetes later). DPDP requires verifiable parental consent for children. | Privacy (DPDP) | Single user now; under-18 primary member refused; family logging deferred; lawyer question added. |
| R9 | **Health-data exposure** through analytics, logs, notifications, a shared report or a breach. | Privacy | No analytics events; scrubber field names; RLS with FORCE; Mumbai residency; report not stored and `no-store`; name and notes excluded by default; lock-screen privacy for reminders; CSV injection guard. |
| R10 | **Carb numbers read as prescriptions**, and the diary's carb remainder may be high for blood-sugar users. | Clinical | Carb guide is user-entered and off by default; neutral display; no default number until a clinician supplies one. Clinician question: is the diary's carbs-as-remainder suitable when a blood-sugar condition is set? (No change in this spec.) |
| R11 | **Invented or misattributed GI values.** | Clinical, legal | Generic foods only, a source row per value with locator and verifier, GL only as stated by the source, unknown everywhere else; only the ICMR-NIN 2024 Annexure III is used (Q7), so there is no second source to reconcile. |
| R12 | **Lab unit confusion** (HbA1c % vs mmol/mol; cholesterol mg/dL vs mmol/L) and misread trends. | Clinical | Unit picked from a per-test closed list; plausible-confirm; both units shown; points-only chart; no ranges or bands. |
| R13 | **Medical claims creep into copy** (store text, reminders, education). | Regulatory, legal | Copy review in every safety review; banned phrases list in tests for `sugar.*` keys ("manage your diabetes", "control", "treat", "cure", "spike"). |
| R14 | **PDF rendering of Hindi and Marathi** fails or bloats the API image. | Technical | WeasyPrint with Noto fonts, measured in S5. The PDF ships in en, hi and mr (Q9), so a rendering problem is fixed before S5 is done. |
| R15 | **Consent text change** forces re-consent and confuses existing users. | Product, privacy | Inline consent card at first use of Sugar Control only; the change is explained in plain words. |
| R16 | **Web push reminders** add infrastructure and a new failure mode. | Technical | Reminders are the last slice, S8 (Q10); the sender job logs counts only. |

---

## 18. Sources

- `docs/research/sugar-control/SHORTLIST.md`: ranked candidates, closed leaders, the DO-NOT-BUILD list and the safe zone.
- `docs/research/sugar-control/RESEARCH_LOG.md`: licences (Nightscout AGPL-3.0, xDrip+ GPL-3.0, AndroidAPS AGPL-3.0), CDSCO draft guidance (2025-10-21) and APACMed's SaMD example, unreached sources.
- `docs/research/sugar-control/apps/nightscout.md`: units (§1), manual entry and context (§2), treatments timeline (§3), statistics and AGP idea (§4), reports and CSV (§5), data model and soft delete (§6), API lessons (§7), privacy defaults (§8), exclusions (§10).
- `docs/research/sugar-control/apps/xdrip.md`: units and display (§1), manual reading guards (§2), treatments (§3), statistics and completeness (§4), export (§5), uuid idempotency (§6), privacy (§8), user-typed reminders (§9), exclusions (§10).
- `docs/research/sugar-control/apps/closed-apps-public.md`: per-app findings for sugar.fit, BeatO, mySugr, Glucose Buddy, HealthifyMe and Blue Circle (§1), cross-app patterns (§2), citable guidance on GI bands, ICMR-NIN 2024, ICMR-INDIAB, RSSDI, the plate method and ADA reference ranges, all secondary and PENDING CLINICIAN REVIEW (§3).
- `docs/research/food-diary/FEATURE_SPEC.md` (§1.4, §5, §5.12, §6, §6.6, §7, §10) and `DECISIONS.md` (Q7, Q9, Q13, Q16): meal slots, entries and snapshots, local dates, hide-numbers, family deferral, consent pattern.
- Repository: `apps/api/app/scoring/conditions.py` (blood-sugar group: sugar bands, misleading sugar claims, hidden and added sugars, 30 g carbs per serving, cardio caution); `apps/api/app/scoring/data/thresholds.yaml` (`conditions.blood_sugar`, `condition_aliases`, `sources`, `section_sources`); `apps/api/app/core/consent.py` (`REQUIRED`); `apps/api/app/integrations/posthog.py` (`ALLOWED_EVENTS`); `apps/api/app/features/me/service.py` (`ACCOUNT_OWNED_TABLES`); `apps/api/app/jobs/retention.py`; `packages/test-fixtures/modes/layouts.json`; ADRs 0006, 0009, 0013, 0017, 0018, 0019, 0022.
- Not verified and needed before build: the glucose conversion factor the clinician prefers (18.016 or 18); the HbA1c IFCC/NGSP equation constants and the lipid factors; home-meter display limits; ADA Standards of Care Section 6 primary text (2026 edition); ICMR-NIN 2024 Annexure III (GI list) primary PDF; the final CDSCO guidance text; FDA policy wording; WeasyPrint Devanagari shaping and image size; `flutter_local_notifications` licence; Supabase Postgres version for `ON DELETE SET NULL (column)`.
