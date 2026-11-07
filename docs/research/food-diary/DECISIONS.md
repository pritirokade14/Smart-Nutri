# Food Diary: user decisions on FEATURE_SPEC open questions

Answered one at a time, starting 2026-11-07. These are binding for the build.

| # | Question | Decision |
|---|---|---|
| Q1 | Indian food data (IFCT 2017 licence) | (a) Write to ICMR-NIN for permission. Until then, use USDA FoodData Central ingredients plus Indian dishes built as documented recipes; switch to IFCT once approved. |
| Q2 | Energy equation | (a) Mifflin-St Jeor (1990) × activity factor |
| Q3 | Adaptive TDEE timing | (a) v1 uses the formula. Adaptive is built as slice 7, behind a flag that stays off until clinician sign-off and about 4 weeks of tester data. |
| Q4 | Weight source | (a) Manual weigh-ins only in v1, same on Android and web. Health Connect in v2. |
| Q5 | Exercise calories | (a) Ignore them; the activity level already covers typical exercise, so no add-back. |
| Q6 | Household-unit grams | (a) Our own reference set (katori 150 ml, cup 200 ml, glass 250 ml, tbsp 15 ml, tsp 5 ml, plus per-food grams), checked by a dietitian. Grams are always shown, and the user can edit them per food. |
| Q7 | Hide-numbers default | (a) Numbers shown by default. Onboarding offers show all, hide calories or hide all, and Today has a one-tap eye toggle. |
| Q8 | Protein g/kg per goal | (a) Build Muscle 1.6, Lose Weight 1.2, Eat Healthy 0.83. All PENDING CLINICIAN REVIEW. |
| Q9 | Family deferral | (a) Confirmed: solo only. Data is stored per member with "self" as the only member, the API rejects other members (`DIARY_FAMILY_ENABLED=false`), and there is no family UI. |
| Q10 | Protein reference weight | Lean mass if known, else adjusted weight (chosen after a competitor check). An optional body-fat % gives protein per kg of lean mass, as MacroFactor does. Without it, at BMI ≥ 30, use the clinical adjusted body weight (ideal weight + 25% of the excess). Otherwise use actual weight. The lean-mass g/kg factor and the IBW formula are PENDING CLINICIAN REVIEW. |
| Q11 | Sex "other" or not given | (a) Ask which estimate to use (female-type, male-type or in-between), defaulting to in-between (the mean of the two constants), and use the higher calorie floor. |
| Q12 | Age limits | (a) Targets from age 18, none under 18, and a "less certain" note over 78. |
| Q13 | Consent for targets | (a) Targets and the weight log need `health_data`. Withdrawing it stops the targets but keeps the stored data; food logging works on `terms`. Record this in ADR 0022. |
| Q14 | Support signpost | (c) No signpost for now; show only the safety limits (calorie floor, maximum loss rate). Can be revisited before launch. |
| Q15 | Existing `weight_gain` goal | (a) Keep it working for existing data (direction "gain", Eat Healthy protein), but do not offer it in new UI. A proper "Gain Weight" chip can come later. |
| Q16 | Meal slots | (b) Renamable slots, up to 6. The defaults are Breakfast, Lunch, Snacks and Dinner, picked from the time of day; the user can rename them or add more, for example pre-workout or evening chai. |
| Q11b | Calorie floor when sex is "other" or not given | Always the higher floor (1,500 kcal), whichever estimate is picked (user, 2026-11-07, after the safety review) |
| Q6b | Katori size | Follow ICMR-NIN 2024: default katori 200 ml, with small/medium/large options (115 / 155 / 360 ml) in the portion picker. Grams are always shown. This replaces the 150 ml in Q6 (user, 2026-11-07). |
