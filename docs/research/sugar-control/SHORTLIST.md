# Sugar Control study: shortlist (Phase 1)

Date: 2026-11-07. Discovery only; nothing cloned or analysed. GPL/AGPL: learn from, never copy code. Licences are GitHub API fields; LICENSE files not yet opened.

Finding: there is no maintained open-source "meal plus glucose plus carbs" diary. Open source is CGM and pump tooling. The meal-to-glucose idea has to be studied from closed apps' public docs.

## Ranked candidates

| # | App | Platform | Open source / licence | Activity | Stack | Official source | Covers | Indian food | Regulatory note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Nightscout (cgm-remote-monitor) | Web, self-host | Yes, AGPL-3.0. github.com/nightscout/cgm-remote-monitor | 2,858 stars, pushed 2026-11-07 | Node.js, MongoDB | GitHub, Nightscout docs | Glucose and treatments (carbs, notes) timeline, AGP and daily reports, doctor-shareable views, API | None found | Community tool, not a regulated product; carries a "not for treatment decisions" stance [unverified wording] |
| 2 | xDrip+ | Android | Yes, GPL-3.0. github.com/NightscoutFoundation/xDrip | 1,822 stars, pushed 2026-11-03 | Java, Android | GitHub releases | Manual and CGM glucose, carb and insulin treatment entries, graphs, stats, Nightscout sync | None found | Not approved for dosing; dosing-adjacent features exist, so avoid |
| 3 | AndroidAPS | Android | Yes, AGPL-3.0. github.com/nightscout/AndroidAPS | 1,249 stars, pushed 2026-11-07 | Kotlin | GitHub | Automated insulin delivery with pump. Reference only for data model of treatments | None | Closed-loop insulin dosing: regulated territory. Never study for features |
| 4 | GlucoDataHandler | Android, watch | MIT per AlternativeTo [unverified: repo not checked] | [unverified] | Kotlin [unverified] | GitHub [unverified] | Glucose display, widgets | None | Display only |
| 5 | Blue Circle Diabetes app | Android, iOS | Unknown [unverified] | [unverified] | [unverified] | bluecircle.foundation, stores | Free, glucose log, food lookup with glycemic data, carb counting, insulin calculator (per store text) | Yes, Indian nonprofit (depth [unverified]) | Has insulin calculator: regulated pattern, avoid copying it |
| 6 | Nourishly Diabetes Type 2 | iOS (Android [unverified]) | No | [unverified] | n/a | App Store | Logs glucose, carbs, meds, meals, activity, stress | Unlikely | Information logging |
| 7 | Glycemic Index Guide: Diabetes | iOS | No | [unverified] | n/a | App Store | GI and GL lookup, glucose log, custom foods | Not stated | Information only |
| 8 | Glucosio | Android | Listed open source, discontinued | Dead | n/a | n/a | Early glucose diary | None | Not worth reading |

Dead ends: zeletrik/diabetes-diary (no licence, 2019). OvaCare (PCOS, React/Vite, no licence: cannot reuse).

## Closed leaders (public docs and store pages only)

| App | Why study | Notes |
|---|---|---|
| mySugr (Roche) | Logbook, meal photos, doctor reports, HbA1c estimate | Its insulin bolus calculator is a regulated device feature; do not mirror |
| sugar.fit | India, type 2 and prediabetes, CGM-led coaching | Paid, coach-driven; Indian meal logic is the benchmark |
| BeatO | India, ties to own glucometer, reading log, teleconsults | Hardware-led |
| Glucose Buddy | Simple manual logs of glucose, carbs, meds, A1c | Display and trends |
| HealthifyMe diabetes | India, CGM "BIOS" meal-response insights, Indian foods | Public docs only [unverified detail] |

## Top picks (for Phase 3, with approval)

1. **Nightscout**: how to model glucose entries plus meal and carb "treatments" on one timeline, and its AGP/daily report layout for a doctor export. AGPL: ideas only.
2. **xDrip+**: manual glucose entry UX, units (mg/dL and mmol/L) handling and stats, treatment logging. GPL: ideas only. Skip all dosing parts.
3. **Blue Circle** (docs and screenshots only, plus whichever closed leader is most Indian, sugar.fit): Indian diabetic food content, GI/GL display, plate guidance. Licence unknown so no code reading.

## Regulatory: do NOT build (CDSCO MDR 2017, FDA SaMD)

CDSCO issued software-as-medical-device guidance under MDR 2017 (draft 2025-10-21; a final version reportedly exists, [unverified]). Insulin dose calculators are the standard SaMD example. Stay on the information side:

- No insulin or medicine dose calculation, correction factors, insulin-to-carb ratios, bolus or "insulin on board".
- No dose or timing advice ("take X units", "skip your tablet"). Medicine and insulin reminders only repeat what the user typed, as information.
- No diagnosis or risk scoring for diabetes, prediabetes or PCOS; no "you may have" outputs from readings.
- No treatment targets or alerts that tell users to act medically (for example hypo or hyper alarms framed as clinical guidance). Show reading ranges only as user-set or label-sourced, marked PENDING CLINICIAN REVIEW.
- No closed-loop, pump or CGM-driven automation; no claim of replacing a glucometer; no reading accuracy claims. Importing from a glucometer or CGM is a later, separate decision.
- No LLM or model output that changes a verdict or number (existing rule 1). LLM explains only.
- No "treats, manages or cures diabetes or PCOS" copy (existing rule 7). Use "information, not medical advice".
- HbA1c: log what the user enters; do not estimate it from glucose readings.

Safe zone: carb and sugar budgets against label data, GI/GL as reference data in YAML, manual glucose notes tied to meals, simple trends, doctor-share export of user-entered data, plate-method education content.
