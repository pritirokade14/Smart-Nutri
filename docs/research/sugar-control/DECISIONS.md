# Sugar Control: user decisions on FEATURE_SPEC open questions

Answered one at a time, starting 2026-11-07. These are binding for the build.

| # | Question | Decision |
|---|---|---|
| Q1 | Default glucose unit | (a) mg/dL by default; mmol/L available in settings and on the entry sheet. |
| Q2 | Meal-context tags | (a) Fasting, before a meal, after a meal (about 1 h, about 2 h, not sure), bedtime, any other time. |
| Q3 | Note for very low readings | (a) One static, neutral line below a clinician-set value ("If you feel unwell, follow the plan your doctor gave you, or get medical help"). No colour, no alert; ships only after clinician sign-off. (Re-asked at the user's request; the first answer was "no note".) |
| Q4 | Personal glucose range | (a) User-set only and empty by default. A general-reference information card in settings is never applied automatically. |
| Q5 | "Meals and your readings" | (a) Build it as slice S6, behind a flag that stays off until clinician review and about 4 weeks of tester data. Uses only the user own readings (10+ after-meal readings on 5+ days). |
| Q6 | Per-meal carb guide | (a) Optional and off by default. The user types their own grams per meal; no default number ships. |
| Q7 | GI and GL data source | (a) ICMR-NIN Dietary Guidelines 2024 Annexure III only, typed in by hand from the primary PDF with a page reference per row. Generic foods only; GL only where the source states it. |
| Q8 | PCOS scope | (a) The same tools as everyone else, with no PCOS-specific features and no cycle tracking. Revisit after launch. |
| Q9 | Doctor report format | (a) PDF in the app language (en, hi, mr) plus CSV, generated on demand and never stored. |
| Q10 | Reminders in the first release | (a) Not in the first release. Build them as the last slice (S8), after S1–S5 ship. |
| Q11 | Glucometer and CGM sync | (a) Deferred: manual entry only. Revisit with Health Connect in v2. |
| Q12 | Consent for reminders | (a) `health_data`. |
| Q13 | CSV export after `health_data` is withdrawn | (a) Allowed on `terms` alone as a data-access right; the PDF and all screens stay gated. |
| Q14 | Sugar Control chip without a saved condition | (a) Blood-sugar scan checks apply only once diabetes, prediabetes or PCOS is saved. Onboarding offers it optionally; no scoring change. |
| Q15 | How far back a reading can be entered | (a) 90 days. |
| Q16 | Deleted readings and labs | (a) An undo snackbar, plus "Recently deleted" for 30 days, then purged by the retention job. |
| Q17 | Analytics | (a) No Sugar Control events at all. |
| Q18 | Tab placement | (a) Sugar Control mode tabs: Home, Scan, Diary, Sugar, Profile. Family moves to More while it's deferred. |

Q6–Q18 were set to the recommended option at the user's request ("use all the recommended things", 2026-11-07).
| Q19 | Show SD in S3 patterns | Yes: show a plain descriptive SD ("readings vary by about ±X mg/dL") next to the average, with no CV, score or colours (user, 2026-11-08). |
