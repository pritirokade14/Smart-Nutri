# Food Diary and Targets: feature spec (Phase 4, design only)

**Changelog:** 2026-11-07: decisions Q1–Q16 applied.

- **Status:** DRAFT for user approval. The 16 decisions in `DECISIONS.md` are binding and are applied throughout (section 11 lists them). Nothing here is built. No code, migration or string has been changed.
- **Date:** 2026-11-07. Branch at the time of writing: `v1-rebuild` (alembic head `0007_plan9_supplement_category`).
- **Inputs:** the research files in this folder (`SHORTLIST.md`, `RESEARCH_LOG.md`, `apps/*.md`), AGENTS.md, CONTEXT.md, `docs/ARCHITECTURE.md`, `docs/PRODUCT.md`, `docs/FEATURE_PARITY.md`, ADRs 0017 to 0021, and the existing meals, summary, protein-guide and user-type code.
- **Clean room:** this spec is in our own words and our own notation. No code, text, strings, icons or data files were copied from any studied app.
  - OpenNutriTracker (GPL-3.0), NutriTrace (AGPL-3.0) and kcal (MPL-2.0) were used for ideas only.
  - FitBook is MIT, but its `LICENSE.md` names **"Copyright (c) 2024 Flexify"** as the holder, not FitBook. **Before any reuse of FitBook material, confirm the correct holder and keep the notice.** This spec reuses nothing from it.
  - SparkyFitness has a non-commercial licence and was not read for reuse.
- **Every number** in sections 4 and 5 is a proposal. Each one lives in YAML, is marked `PENDING CLINICIAN REVIEW`, and needs sign-off before launch.
- `[unverified]` marks anything not confirmed against a primary source. `[verify]` marks something we confirmed only partly.

---

## Contents

1. Summary and scope
2. How the studied apps do it
3. Ideas adopted and rejected
4. Target maths
5. Data model
6. API endpoints
7. Client design (Android and web)
8. i18n keys
9. Tests
10. Phased delivery plan
11. Decisions (resolved)
12. Risks and mitigations
13. Sources

---

## 1. Summary and scope

### 1.1 Headline design

SmartNutri adds a **single-user food diary with daily targets**, built by extending what already exists rather than beside it:

- **Diary entries extend `meal_logs`.** The scan-to-log table from Plan 6 gets a meal slot, a local date, a typed quantity and unit, more kinds of food, and a full food snapshot. There is no second entries table, and every existing log stays valid.
- **Targets come only from the API**, in a new pure module `app/scoring/targets.py`. Every constant is in a new `app/scoring/data/targets.yaml`, marked PENDING CLINICIAN REVIEW.
  - Energy: Mifflin-St Jeor BMR × an activity factor, plus a goal rate expressed as a **% of body weight per week**, then capped and floored.
  - Protein is set first, in g/kg per goal. The kilograms it applies to depend on what we know (Q10): lean mass when the user gives an optional body-fat %, an adjusted weight at BMI 30 or more, and otherwise actual weight. Fat comes next, as a share of energy with a floor. Carbs are the remainder.
- **Targets are information, never verdicts.** They never reach `analyze()`. No verdict, reason, score, allergen state or Nutri-Score reads them.
- **Each day's target is frozen.** A `diary_days` row stores the target that applied that day, so changing your goal never rewrites the past.
- **Unknown is never 0.** A missing nutrient keeps that day's total marked `incomplete`. "Remaining" is then `null`, because the eaten total is only a lower bound. This rule already holds in `meals/summary.py`, and the diary keeps it.
- **Indian household units.** Units are typed (katori, roti or chapati piece, cup, glass, tbsp, tsp, piece, serving, g, ml). One API function, `to_grams()`, converts them, and it refuses to guess.
- **Eating-disorder-aware safety rails** ship in the first slice, together with the first number:
  - calorie floors, a maximum rate of loss and a maximum deficit;
  - a target weight no lower than a BMI of 18.5;
  - no energy targets for anyone under 18, and none during pregnancy or breastfeeding;
  - neutral colours and copy, with no red, no "bad day" and no streaks;
  - a support signpost is deliberately left out for now (Q14, risk R20); the safety limits and the neutral cards stay;
  - one-tap **hide numbers**, which the API enforces by redacting the values.
- **Adaptive TDEE comes later, behind a readiness gate:**
  - a regression on calendar days, with local dates;
  - a smoothed weight trend that also rejects outliers;
  - a cap relative to the formula estimate, and a limit on how much it can change each week.
- **Family-ready, solo now.** Every row is keyed by `member_id`, and today the only member is the account holder (`relation = 'self'`, `is_primary`). A server flag (`DIARY_FAMILY_ENABLED=false`) rejects any other member until Family returns (Q9, confirmed).

### 1.2 In v1 of this feature

| Area | In |
|---|---|
| Goal setup | Body data (birth year, sex, height, weight, optional body-fat %), activity level, goal direction (lose, maintain, gain) from the goal chip, rate, optional target weight, pregnancy or breastfeeding question, hide-numbers choice |
| Targets | Daily kcal, protein, fat and carbs from the formula. A per-day snapshot. An explanation of how each number was reached. Safety rails |
| Diary | Today and any past day; meal slots (four defaults the user can rename, up to six); add, edit, move and delete entries; copy a meal or a whole day; mark a day "partly logged" |
| Add food | Search (generic Indian foods, my foods, my recipes, packaged products), recents, favourites, barcode (free), label scan (existing), quick add, custom food, recipe |
| Units | A household-unit table, per-food portion overrides, and one `to_grams()` |
| Progress | Week view, weight log, honest weight trend (raw points plus trend line, weekly rate, a projection only when it is meaningful), taper near the target weight |
| Settings | Show numbers, hide calories only, or hide all numbers; consumed or remaining view; change goal or rate; manage meals; reset targets |
| Modes | A Diary destination in the Build Muscle, Lose Weight and Eat Healthy modes (section 7.10) |

### 1.3 Out, for later

- **Adaptive TDEE.** It is designed here and built as slice 7 behind `ADAPTIVE_TDEE_ENABLED`, which stays off until the clinician signs off and testers have about 4 weeks of data (Q3). v1 uses the formula.
- Health Connect and wearables, step and exercise calories. Weight is manual only in v1 (Q4), and exercise is never added back (Q5).
- A support signpost of any kind (link or contact number). Deferred; to be revisited before launch (Q14, R20).
- Family diaries: logging for other members, and per-member targets for children (deferred, Q9).
- Per-weekday targets (training versus rest days), per-meal calorie budgets, micronutrient targets, water and fasting.
- Photo logging of home-cooked plates (needs an INDB licence, as PRODUCT.md already notes), and AI parsing of free text such as "2 roti and dal".
- Nested recipes (a recipe inside a recipe), recipe import, and sharing recipes between accounts.
- Export and import of the diary (DPDP access requests are served by support until then).
- Supplements dosing, meal plans, coaching. These are never in scope (PRODUCT.md "Not doing").

### 1.4 Family-ready design (deferred, hidden, not deleted)

- Every new table has `account_id` and `member_id`. A composite FK `(member_id, account_id) → members(id, account_id)` makes it impossible for one account's row to point at another account's member.
- Every endpoint takes an optional `member_id`, which defaults to the primary member. While `DIARY_FAMILY_ENABLED=false` (the default), any other member returns `422 diary_member_not_enabled`. Turning Family back on is a flag change plus a UI, with no migration.
- Custom foods, recipes and portion overrides belong to the **account** (a shared family kitchen). Diary entries, targets, weights and favourites belong to a **member**.
- The Family mode and tab stay registered, but are hidden while Family is deferred. That is a separate decision already made by the user, and it is unchanged here.

### 1.5 How the goal chips map to this feature

The goal chips being renamed (Eat Healthy, Lose Weight, Build Muscle, Sugar Control, Heart Health, Allergy Safe, My Diet) are a separate change. This spec depends only on the existing member `goal` codes:

| Chip | Existing member `goal` | Default diary direction | Served by this feature |
|---|---|---|---|
| Build Muscle | `build_muscle` | gain (lean, slow), or maintain if the user picks recomposition | **First** |
| Lose Weight | `weight_loss` | lose | **First** |
| Eat Healthy | `healthy_eating` | maintain | Yes, with maintenance targets (optional to set up) |
| Sugar Control, Heart Health, Allergy Safe, My Diet | conditions, allergens and diet fields (no `goal`) | maintain, if the user sets up targets | Diary is available from More; nothing here changes their verdict rules |
| (none) | `weight_gain` (exists in `GoalIn`, no chip) | gain | Kept working for existing data, with the Eat Healthy protein value. Not offered in new UI (Q15) |

The chip and the member `goal` remain presentation and verdict-side preferences as ADR 0019 defines them. The diary's `direction` is stored separately (section 5) because Build Muscle can mean a surplus or maintenance.

---

## 2. How the studied apps do it

Sources: `apps/opennutritracker.md` (ONT), `apps/nutritrace.md` (NT), `apps/kcal.md` (kcal), `apps/fitbook.md` (FB) and `apps/closed-apps-public.md` (MacroFactor MF, Cronometer CR, HealthifyMe HM, MyFitnessPal MFP). Section numbers refer to those files.

| Topic | OpenNutriTracker (GPL) | NutriTrace (AGPL) | kcal (MPL) | FitBook (MIT*) | Closed apps (public pages only) |
|---|---|---|---|---|---|
| **Targets** | IOM 2005 total-energy equations (no BMR step), 4 activity bands, goal ±500 kcal or rate × 1,100 kcal/kg/day; macros as fixed 60/25/15 % of energy; no protein per kg (ONT §3) | Mifflin-shaped BMR in the wizard only, 5 activity factors, flat ±20 % for lose or gain, stored once as a fixed goal; macros typed by hand (NT §3.1, §3.4) | No formula at all: named goals typed by hand, per weekday by bitmask (kcal §5) | Opt-in "auto-calc" from body weight alone: 27.5 kcal/kg, 1.6 g/kg protein, 0.8 g/kg fat, 5 g/kg carbs. The macros do not add up to the calories, and each weigh-in overwrites manual targets (FB §5) | MF: rate as % body weight per week; protein first by training type, then fat and carbs. CR: Mifflin-St Jeor; ratio or gram modes [partly unverified]. HM: age, sex, height, weight → budget [formula unverified]. MFP: about 500 kcal/day per lb/week [unverified] |
| **Adaptive TDEE** | None | 35-day OLS of weight on the **index of valid days**; 21-day gate; 7,700 kcal/kg; no smoothing, no caps; UTC dates for the window (NT §3.3, §8) | None | None | MF: weekly check-in, weighted weight trend, deliberately damped changes (about 40–60 % of the raw shift); needs intake on 4 of 7 days and at least 1 weigh-in a week (closed §1) |
| **Diary** | 4 fixed slots; snapshot of the food on every entry; per-day goal stored on the day; cached running totals with read-modify-write, which led to locks, rollback and repair code (ONT §2, §6) | One row per day holding a JSON array of items; uuid merge with tombstones; renamable meals; consumed or remaining toggle (NT §2, §6) | Entries store their own totals (snapshot) and cannot be edited, only deleted and re-added (kcal §1, §6) | One row per entry referencing a food or a meal **with no snapshot**, so editing a food rewrites history; summary mode used/target, remaining, both or none (FB §2, §6) | MFP Premium: per-meal and per-weekday goals [unverified]; MF: customisable toolbar [unverified] |
| **Units** | Closed set: g, ml, oz, fl oz, serving; ml = g everywhere; "1 serving" with no grams logs 1 g (ONT §4, §8) | Typed catalogue (mass, volume, count, custom); per-food `alt_units` with grams; density field; randomised 5,000-case test after a bug (NT §4) | Units carry a type (weight, volume, division); a food lists the units it supports; fractions accepted (kcal §3) | Fixed factors (cup 250 g, tbsp 15 g); volume treated as water; household measures from CORGIS stored but apparently unused (FB §3) | HM: katori and chapati as servings (official blog snippet); katori size varies, 120 or 200 ml quoted by third parties [unverified] |
| **Food DB** | OFF plus its own Supabase backend (USDA, BLS); own foods first; cache first, then live (ONT §5) | Own foods, OFF (or a local mirror), USDA with a key; OFF re-ranking (NT §5) | None, on purpose (kcal intro) | CORGIS 7,000 US foods plus OFF import (FB §3) | HM: Indian dishes built with NIN (press) [unverified]; MFP: huge crowd DB with duplicates; CR: verified government data [unverified] |
| **Recipes** | Sum of ingredients in grams ÷ total grams; a nutrient unknown on every ingredient stays unknown; servings (ONT §4) | Recipes share a table with meals; "split recipe" into ingredients (NT §4) | Polymorphic lines (food or recipe), per serving = total ÷ servings, grams only when a cooked weight exists (kcal §4) | "Meals" as saved combinations with no yield (FB §4) | n/a |
| **Progress** | Weight per local day; raw dots plus a 7-day moving average; least-squares projection only when heading toward the target; optional taper 1–5 kg (ONT §7, §3) | Weight series with a straight regression; fasting streaks (NT §7) | None | Weight list, goal line, trend line; a random "well done" toast near the target (FB §7) | MF: trend weight and expenditure trend |
| **Safety rails** | Soft warning below 1,500 / 1,200 kcal; plausible-range confirm on height and weight; notice for under-19s; "no streak guilt" (ONT §3, §7) | None: no floor, no rate cap (NT §3.1, §11) | n/a (no maths) | None | MF: protects fat first, then protein, at very low targets (closed §1) |
| **Known bugs** | Activity coefficient applied to weight only, understating energy by 109–489 kcal/day (fixed, #987); day-offset bugs (#586); time-zone shift on weight delete (#1418); concurrent totals lost (ONT §3, §8) | Index-based x-axis inflates the slope when days are skipped; UTC versus local dates; goal resolver showed the weekly peak (#203); kJ drift (#146); no tests for any target maths (NT §8, §10, §11) | Decimal overflow (widened columns); possible divide by zero; missing values stored as 0 (kcal §8) | Migration corrupted nutrients and needed an inverse; lb uses 2.2; preview and stored totals may disagree (FB §8) | MFP: barcode scanning moved behind Premium in 2022 (Slashdot); reported data-entry bugs in 2026 [unverified] |

\* FitBook: MIT, with the copyright line naming "Flexify" (FB header).

**A correction to our own research.** `apps/nutritrace.md` §3.1 calls NutriTrace's BMR coefficients (9.99, 6.25, 4.92) "not the standard constants". The primary abstract of Mifflin et al. 1990 (Europe PMC, read 2026-11-07) gives exactly these as the **full-precision combined equation**, `9.99·W + 6.25·H − 4.92·A + 166·sex − 161`, and gives `10/6.25/5/+5/−161` as the simplified sex-specific form. Both are published. NutriTrace's real weak points are the flat ±20 %, the missing floor and the untested maths, not the constants.

---

## 3. Ideas adopted and rejected

### 3.1 Adopted

| # | Idea | From | Why (and what we change) |
|---|---|---|---|
| A1 | **Food snapshot per entry** | ONT §2, kcal §6 (FB is the counter-example) | History must not change when a food, the OFF cache or a recipe changes. `meal_logs` already snapshots the portion nutrients (ADR 0017). We add `food_snapshot` (per 100 g values, name, units with grams), so an entry can be edited without its source. |
| A2 | **Goal frozen per day** | ONT §2 (goal on the tracked day), kcal §5 (`journal_dates` link) | A past day is judged against the target it had. We store the **numbers** in `diary_days` (kcal froze only a link). A day before the feature existed has no target, and we never back-fill it with today's settings. |
| A3 | **Typed units with one to-grams function** | kcal §3 (unit types, supported units), FB §10 (one resolver), NT §4 (randomised test) | One server function, `to_grams(quantity, unit, food)`, returns grams or `None`. The UI offers only units the food supports, so a conversion never fails in normal use. Clients never convert for saving. |
| A4 | **Household-unit table plus per-food portions** | Gap in all four open apps (SHORTLIST "Gap"); HM's katori and chapati (closed §3) | India-first. Volume units have a fixed ml. Count units (roti, piece) have **no** global grams and need a per-food value. Volume units need a per-food grams value or a known density. Nothing is ever ml = g by default. |
| A5 | **Unknown ≠ 0** | Rejected behaviour in ONT §6, NT §6, kcal §8, FB §6; our own `meals/summary.py` | Already a project rule. Totals sum only known values, mark `incomplete`, and set "remaining" to `null` when incomplete. A day with unknown energy is excluded from adaptive TDEE. |
| A6 | **Readiness-gated adaptive TDEE** | NT §3.3 (gate and fallback), MF (closed §1: data sufficiency, damping) | Shows "learning, n of 14 days" until ready and falls back to the formula. We fix NT's bugs: regression on **calendar days** (not valid-day index), **local dates** in the account's time zone, a **smoothed trend** with outlier rejection, a **band cap** around the formula, a **weekly step limit**, a minimum number of real weigh-ins, and a per-day plausibility check. |
| A7 | **Protein first per kg, then a fat floor, carbs as the remainder** | MF (closed §1); our existing `protein_g_per_kg_by_goal` (Plan 9); FB's g/kg idea without its inconsistency | Fits Build Muscle and Lose Weight far better than fixed percentages (ONT's 60/25/15). Fat is a share of energy, between a floor and the ICMR-NIN 30 % ceiling. Carbs fill the rest, and the macros always add up to the kcal target (FB's did not). |
| A8 | **Weekly rate as % of body weight** | MF (closed §1) | The kg/week shrinks as weight falls. It is easy to cap, and it is fairer across body sizes than a fixed −500 kcal. It is shown to the user as kg/week as well. |
| A9 | **Taper near the target** | ONT §3 (taper), our own formula | The last kilograms ease into maintenance. Our version: the rate becomes `distance ÷ taper_weeks` once the full rate would overshoot within the taper window. It is smooth, has no fixed 1–5 kg band, and reaches maintenance inside a small band. |
| A10 | **Quick add, recents, copy a meal or day, favourites** | ONT §1, NT §1, FB §1, kcal §3 | Logging speed decides whether people keep a diary. Recents are a **query** over `meal_logs`, not a table. Quick add stores kcal (required) and macros (optional, never 0 when blank). |
| A11 | **Free barcode** | MFP paywalled barcode scanning in 2022 (closed §4) | We already have barcode, label scan and OFF resolution free (F3, F4). The diary reuses them. This gap is ours to win. |
| A12 | **Honest weight trend** | ONT §7 (projection only toward the target), MF (trend weight) | Raw dots plus a smoothed trend. A weekly rate from a calendar-day fit. A projection only with enough data, the trend heading toward the target, and a horizon under 2 years. Otherwise we say there is no projection. |
| A13 | **Consumed or remaining toggle** | NT §1, FB §6 | Some users find "remaining" motivating and others find it stressful. It is a setting, and hide numbers goes further. |
| A14 | **Plausible-range confirm on body data** | ONT §1 | Values outside a plausible range are accepted only after a confirmation. Hard limits come from the existing members API (height 30–250 cm, weight 2–300 kg). |
| A15 | **Idempotent create with `client_id`** | NT §4; our own `meal_logs` | Android's offline queue (drift) already relies on it. We extend it to custom foods, weights and favourites. |
| A16 | **Totals computed from entries in one place** | ONT §6 and NT §6 show what goes wrong | No cached running totals. The API sums the entries on read (the `_Acc` approach in `summary.py`). Clients render. |
| A17 | **Recipe maths: sum in grams, keep unknown unknown, cooked weight** | ONT §4, kcal §4 | Per 100 g = Σ nutrients ÷ cooked weight (or raw total). A nutrient missing on any ingredient marks the recipe incomplete for that nutrient. |
| A18 | **Fractions in quantity input** (½, 1½) | kcal §3 | Natural for "half a roti" or "one and a half katori". |

### 3.2 Rejected

| Idea | Seen in | Why we reject it |
|---|---|---|
| Fixed macro percentages (60/25/15) | ONT §3 | Ignores body weight and goal; poor for Build Muscle; a high carb share is a poor default for our blood-sugar users. |
| Flat ±20 % or fixed ±500 kcal goal | NT §3.1, ONT §3 | Not proportional to body size. Can push a small person under a safe intake. |
| Rules of thumb from body weight only (27.5 kcal/kg) | FB §5 | No sex, age, height or activity. Macros inconsistent with kcal. Overwrites the user's targets on every weigh-in. |
| Missing nutrient counted as 0 | ONT, NT, kcal, FB | Breaks AGENTS rule 2 and rule 3. |
| No snapshot (live join to the current food) | FB §2 | Editing a food silently rewrites history. |
| One row per day holding a JSON array | NT §2 | Hard to index, aggregate and protect with RLS. Real rows in Postgres are better. |
| Cached running totals | ONT §6 | Lost updates, locks and repair code. |
| Index-based regression x-axis, UTC dates | NT §8 | Inflates the slope when days are skipped; off-by-one dates near midnight. |
| Unbounded adaptive TDEE | NT §3.3 | One stretch of partial logging lowers the target, a risky feedback loop for a health app. |
| Exercise "eat-back" added to the goal by default | ONT §6, NT §3.2, MFP | Over-credits exercise and double-counts with the activity factor. We do not add exercise back at all (Q5). |
| Volume = water density, "1 serving" → 1 g | FB §3, ONT §8 | Wrong for oil, atta, rice and dal. We never default silently. |
| "Good" and "poor" day ratings, streaks, random praise toasts | ONT §6, FB §7 | Arbitrary, not goal-aware, and a risk for people with disordered eating. No streaks and no day ratings. |
| Profile and goals as unversioned settings | NT §11 | Changing a goal rewrites the past. We store dated snapshots. |
| Clients computing targets | ONT, FB | Android and web could disagree. AGENTS rule 1. |
| Wiring tests that match strings in source files | NT §10 | Brittle; they test nothing. We use behaviour and golden tests. |
| Entries that cannot be edited | kcal §1 | Too much friction. Edits re-derive from the snapshot. |
| Per-weekday goals, per-meal budgets (for now) | kcal, MFP | Useful later. Not needed for the first users, and each adds a frozen-day edge case. |

---

## 4. Target maths

All maths runs in `app/scoring/targets.py` (pure functions, no I/O, `Decimal` where rounding matters). Every constant is read from `app/scoring/data/targets.yaml`. The **YAML key** for each constant is given in `code` style. The file's first line is `# PENDING CLINICIAN REVIEW`, as in `thresholds.yaml`.

### 4.1 Notation

| Symbol | Meaning | Unit |
|---|---|---|
| `W` | body weight used for energy (section 4.9) | kg |
| `H` | height | cm |
| `A` | age in whole years on the target date: `target_year − birth_year` (we store a birth year only, so this can be one year high; the effect on BMR is 5 kcal) | years |
| `S` | sex reference: `male`, `female` or `average` | |
| `BMR` | basal metabolic rate (strictly, resting energy expenditure) | kcal/day |
| `f_act` | activity factor | |
| `E_m` | maintenance energy (TDEE) | kcal/day |
| `r` | goal rate, signed: negative to lose, positive to gain | % of body weight per week |
| `ΔE` | daily energy adjustment for the goal | kcal/day |
| `E_t` | energy target | kcal/day |
| `P`, `F`, `C` | protein, fat and carbohydrate targets | g/day |
| `BF` | optional body-fat percentage entered by the user | % |
| `LBM` | lean mass, `W × (1 − BF/100)`, used only when `BF` is given | kg |
| `IBW` | ideal body weight from the named formula (section 4.7.1) | kg |
| `W_ref` | the weight that protein g/kg is applied to (lean mass, adjusted weight or actual weight) | kg |

### 4.2 BMR: Mifflin-St Jeor (1990)

```
BMR = k_W · W + k_H · H − k_A · A + c_S
```

| Constant | Value | YAML key |
|---|---|---|
| `k_W` | 10 | `energy.mifflin.weight_kcal_per_kg` |
| `k_H` | 6.25 | `energy.mifflin.height_kcal_per_cm` |
| `k_A` | 5 | `energy.mifflin.age_kcal_per_year` |
| `c_S` male | +5 | `energy.mifflin.sex_constant.male` |
| `c_S` female | −161 | `energy.mifflin.sex_constant.female` |
| `c_S` average | −78 (the mean of +5 and −161; our own working value) | `energy.mifflin.sex_constant.average` |
| Valid age range | 18 to 78 (the paper's sample was 19 to 78; 18 matches our adult age, see Q12) | `energy.mifflin.valid_age` |

- **Source:** Mifflin MD, St Jeor ST, Hill LA, Scott BJ, Daugherty SA, Koh YO. *A new predictive equation for resting energy expenditure in healthy individuals.* Am J Clin Nutr 1990;51(2):241–247. doi:10.1093/ajcn/51.2.241, PMID 2305711.
- **Verification [verify]:** we read the **abstract** through Europe PMC on 2026-11-07. It states that the sample was 498 healthy adults aged 19 to 78, and it gives both the simplified male (`+5`) and female (`−161`) forms above and the combined form `9.99·W + 6.25·H − 4.92·A + 166·sex − 161`. The full text was not read. A person should check the published table once before launch.
- When the member's sex is `other` or not given, the user is asked which estimate to use: female, male or in-between. In-between (`average`) is preselected, and the higher calorie floor applies to it (Q11). `average` is not in the paper.
- **Ages over 78:** the formula still runs, the response carries the flag `outside_equation_age_range`, and the explanation says the estimate is less certain.

### 4.3 Activity factor and maintenance energy

```
E_m = BMR × f_act
```

| Level (UI label from i18n) | `f_act` | YAML key |
|---|---|---|
| `sedentary`: mostly sitting (desk work, little walking) | 1.2 | `energy.activity_factor.sedentary` |
| `light`: on your feet part of the day, or light exercise 1–3 days a week | 1.375 | `energy.activity_factor.light` |
| `moderate`: active job or exercise 3–5 days a week | 1.55 | `energy.activity_factor.moderate` |
| `very`: hard physical work or hard training 6–7 days a week | 1.725 | `energy.activity_factor.very` |

- **Source: [unverified].** These multipliers are used very widely (calculator sites and textbooks), but we found no primary source (closed §5). They are attributed in different places to FAO/WHO/UNU (1985) PAL work and to exercise-physiology textbooks. The clinician must confirm them, or replace them with ICMR-NIN 2020 PAL values. The choice of Mifflin-St Jeor as the equation is settled (Q2).
- We **leave out the 1.9 "extra active" level** on purpose. Self-rated activity is usually over-estimated, and a high factor pushes the target up for everyone who picks it.
- **No exercise add-back (Q5).** The activity level already covers typical exercise, so logged or synced exercise never raises the target.

### 4.4 Goal rate and energy adjustment

```
r_kg = r / 100 × W                          (kg per week; negative = loss)
ΔE   = r_kg × ρ / 7                         (kcal per day)
```

| Constant | Value | YAML key | Source |
|---|---|---|---|
| `ρ`, energy per kg of body-weight change | 7,700 kcal/kg | `energy.kcal_per_kg_body_weight` | A long-used approximation (about 3,500 kcal per lb). Hall (2008) shows the true value varies with body composition and time [unverified detail]; we use it for a weekly rate, never for short-term predictions |
| Lose: rate options | 0.25, 0.5, 0.75, 1.0 % per week | `goal_rates.lose.options_pct_bw_per_week` | MacroFactor's %-of-body-weight approach (closed §1); values are our working values |
| Lose: default | 0.5 % per week | `goal_rates.lose.default_pct_bw_per_week` | Working value. For 80 kg that is 0.4 kg/week, inside the CDC's "about 1 to 2 pounds a week" (0.45–0.9 kg) for gradual loss (CDC, fetched 2026-11-07) |
| Lose: maximum | 1.0 % per week **and** 1.0 kg per week, whichever is lower | `goal_rates.lose.max_pct_bw_per_week`, `goal_rates.lose.max_kg_per_week` | Working value, within the CDC range |
| Gain: options | 0.1, 0.25, 0.5 % per week | `goal_rates.gain.options_pct_bw_per_week` | Working value. MF recommends modest bulking surpluses (closed §1) [numbers unverified] |
| Gain: default | 0.25 % per week | `goal_rates.gain.default_pct_bw_per_week` | Working value |
| Maximum deficit as a share of maintenance | 25 % of `E_m` | `goal_rates.max_deficit_pct_of_maintenance` | Working value |
| Maximum deficit, absolute | 1,000 kcal/day | `goal_rates.max_deficit_kcal_per_day` | Working value (the top of the CDC range at 7,700 kcal/kg) |
| Maintain | `ΔE = 0` | n/a | |

Rate clamping, in order (each step that bites adds a flag to the response):
1. Clamp `r` to the options range for the direction (`rate_capped`).
2. Clamp `|r_kg|` to `max_kg_per_week` (`rate_capped`).
3. For a loss: `ΔE = −min(|ΔE|, max_deficit_pct_of_maintenance × E_m, max_deficit_kcal_per_day)` (`deficit_capped`).

### 4.5 Taper near the target weight

The taper applies only when a target weight `W*` is set. Let `d = |W_trend − W*|` (kg), where `W_trend` is the trend weight (section 4.9), and let `T` be `goal_rates.taper.weeks` (4).

```
if the direction is lose and W_trend ≤ W* + band, or the direction is gain and W_trend ≥ W* − band:
    ΔE = 0, flag goal_weight_reached           (band = goal_rates.taper.maintenance_band_kg = 0.5)
elif |r_kg| × T > d:
    r_kg ← sign(r_kg) × d / T, flag taper_active     (recompute ΔE from the new r_kg)
```

This is our own formulation. The full rate would overshoot the target within `T` weeks, so the rate becomes "close the remaining gap over `T` weeks". The steps get smaller as the gap shrinks, and inside the band the target is maintenance. When the goal weight is reached, the response says so in neutral copy (no celebration; see section 4.11).

### 4.6 Energy target, floors and rounding

```
E_raw   = E_m + ΔE
E_floor = max( floor_by_sex[S],  BMR × min_bmr_multiple )
E_t     = if direction = lose: max(E_raw, min(E_floor, E_m))
          else:                E_raw
E_t     = round_half_up(E_t / step) × step
```

| Constant | Value | YAML key | Source |
|---|---|---|---|
| `floor_by_sex.female` | 1,200 kcal | `floors.kcal_by_sex.female` | Widely quoted "do not go below without medical supervision" figure; original source not confirmed [unverified] |
| `floor_by_sex.male` | 1,500 kcal | `floors.kcal_by_sex.male` | Same [unverified] |
| `floor_by_sex.average` | 1,500 kcal (the higher, more protective value) | `floors.kcal_by_sex.average` | Working value |
| `min_bmr_multiple` | 1.0 (never plan below the estimated BMR) | `floors.min_bmr_multiple` | Working value |
| `step` | 10 kcal | `rounding.kcal_step` | Display precision; the estimate is nowhere near ±10 kcal accurate |

- `min(E_floor, E_m)` means **a floor never turns a loss goal into a surplus.** If maintenance is below the floor, the target is maintenance, with the flag `floor_limits_deficit` and copy saying the chosen rate is not possible safely.
- A floor that binds sets the flag `floor_applied`. The UI then explains, in neutral words, that SmartNutri does not suggest less than this amount and that a doctor or dietitian can advise.
- Floors apply to loss only. Gain and maintain are naturally above them, and a gain target below the floor would be a data error (flag `check_body_data`).

### 4.7 Macros: protein first, then fat, carbs as the remainder

```
(W_ref, basis) = protein_reference(W, H, BF, sex)     which weight protein applies to: section 4.7.1
P   = round(factor[goal, basis] × W_ref)              capped at max_g_per_kg × W (total body weight)
F   = round(max(fat_pct × E_t, fat_floor_pct × E_t) / 9)
C   = round((E_t − 4·P − 9·F) / 4)          computed from the ROUNDED P and F, so 4P + 9F + 4C is within ±2 kcal of E_t
```

| Constant | Value | YAML key | Source |
|---|---|---|---|
| Protein, Build Muscle | 1.6 g/kg | `protein.g_per_kg_by_goal.build_muscle` | ISSN position stand: 1.4–2.0 g/kg (Jäger et al. 2017, doi:10.1186/s12970-017-0177-8, PMID 28642676). Morton et al. 2018 meta-analysis: the benefit plateaus around 1.62 g/kg (Br J Sports Med 52:376, PMID 28698222). ICMR-NIN Dietary Guidelines 2024: above about 1.6 g/kg adds no further resistance-training muscle gain (news coverage; primary PDF not read) [verify]. **Already in `thresholds.yaml` (Plan 9); moved here, see 4.12** |
| Protein, Lose Weight | 1.2 g/kg | `protein.g_per_kg_by_goal.weight_loss` | Working value. ISSN notes higher intakes help keep lean mass in a deficit (Jäger 2017). Today `thresholds.yaml` uses 0.83 for weight loss (ruling P9-R13); CONTEXT §9 already asks the clinician about 1.2. **Decided in Q8** |
| Protein, Eat Healthy | 0.83 g/kg | `protein.g_per_kg_by_goal.healthy_eating` | WHO/FAO/UNU 2007 safe level (already in `thresholds.yaml`); ICMR-NIN RDA 0.83 g/kg (secondary sources) [verify] |
| Protein, other goals or none (including the hidden `weight_gain` goal, Q15) | 0.83 g/kg | `protein.default_g_per_kg` | As above |
| Protein maximum | 2.2 g/kg of total body weight | `protein.max_g_per_kg` | Working value, a ceiling in every branch of 4.7.1. ISSN's upper range; ICMR-NIN advises against high protein, so the default stays 1.6 |
| Lean-mass factor, Build Muscle | 2.0 g per kg of lean mass | `protein.lean_mass_g_per_kg_by_goal.build_muscle` | Working value [clinician], PENDING CLINICIAN REVIEW. Chosen so a person at about 20 % body fat lands near the Q8 figure per kg of total weight (1.6 ÷ 0.8). **Q10** |
| Lean-mass factor, Lose Weight | 1.5 g per kg of lean mass | `protein.lean_mass_g_per_kg_by_goal.weight_loss` | Same reasoning (1.2 ÷ 0.8) [clinician] |
| Lean-mass factor, Eat Healthy, other goals, hidden `weight_gain` | 1.0 g per kg of lean mass | `protein.lean_mass_g_per_kg_by_goal.healthy_eating`, `.weight_gain`, `.default` | Same reasoning (0.83 ÷ 0.8, rounded) [clinician] |
| Body-fat range | 3 to 70 % | `body_fat.min_pct`, `body_fat.max_pct` | Plausibility limits for a self-entered value [clinician] |
| Adjusted-weight threshold | BMI ≥ 30 | `protein.adjusted_weight.min_bmi` | WHO adult obesity cut-off. Adjusted body weight is common clinical practice for people with obesity [unverified]. Lower BMI cut-offs are used for Asian Indian adults, so the clinician should confirm 30 [clinician]. **Q10** |
| Adjusted-weight excess fraction | 0.25 | `protein.adjusted_weight.excess_fraction` | 25 % of the excess over ideal weight [unverified] |
| IBW formula | `devine` (alternative: `bmi_based`) | `protein.ibw.formula` | Our proposed choice, marked [clinician], PENDING CLINICIAN REVIEW. The clinician may switch it to a BMI-based ideal weight (key `protein.ibw.bmi_based.bmi`, unused unless chosen) |
| Devine constants | base 50 kg (male), 45.5 kg (female), 47.75 kg (`average`, the mean); plus 2.3 kg per inch of height over 60 inches, never below the base | `protein.ibw.devine.base_kg.{male,female,average}`, `protein.ibw.devine.kg_per_inch_over_60` | Devine 1974, widely published [unverified: original not read] |
| `fat_pct` default | 25 % of energy | `macros.fat_pct_energy.default` | Working value, inside IOM's 20–35 % range and under ICMR-NIN's ≤ 30 % |
| `fat_floor_pct` | 20 % of energy | `macros.fat_pct_energy.min` | IOM 2005 AMDR lower bound (doi:10.17226/10490) |
| Fat maximum (user choice) | 30 % of energy | `macros.fat_pct_energy.max` | ICMR-NIN 2024 (news coverage) [verify] |
| Carb reference minimum | 130 g/day | `macros.carbs_reference_min_g` | IOM 2005 carbohydrate RDA. Not enforced; when `C` is below it, the flag `carbs_below_reference` shows a note |
| Energy densities | protein 4, carbs 4, fat 9 kcal/g | `macros.kcal_per_g` | Atwater general factors |
| Rounding | whole grams | `rounding.macro_g_step` | |

- If protein would take more than `protein.max_energy_pct` (35 %, a working value) of `E_t`, `P` is reduced to that share and the response carries `protein_capped`. This only happens at very low targets.
- **No fibre, sugar or salt targets in this feature.** Sugar and salt keep their existing **limits** in `thresholds.yaml` (`daily_limits`), shown by the existing summary bands.

#### 4.7.1 Protein reference weight (Q10)

The branch is chosen in this order, and the first one that applies wins. The response says which one was used (`explanation.protein_basis`).

| # | When | `W_ref` | g/kg factor used | `basis` |
|---|---|---|---|---|
| 1 | The member has a `body_fat_pct` (3–70) | `LBM = W × (1 − BF/100)` | `protein.lean_mass_g_per_kg_by_goal[goal]` | `lean_mass` |
| 2 | No body fat, and BMI(`W`, `H`) ≥ `protein.adjusted_weight.min_bmi` (30) | Adjusted body weight `IBW + 0.25 × (W − IBW)`, with `IBW` from the formula named in `protein.ibw.formula` (Devine, [clinician]) | `protein.g_per_kg_by_goal[goal]` | `adjusted_weight` |
| 3 | Otherwise | `W` (actual weight) | `protein.g_per_kg_by_goal[goal]` | `actual_weight` |

- BMI and lean mass use the same `W` as the energy maths (section 4.9).
- Body fat wins over BMI because it measures what we want. A person at BMI 30 or more who gives body fat uses lean mass.
- Body fat is optional. Blank means unknown and is never treated as 0. A value outside 3–70 is refused with `422 body_fat_out_of_range`, never clamped silently.
- `body_fat_pct` is health data, stored on the member and gated by `health_data` (section 5.1). It is entered by the user and not changed by weigh-ins, so it can go stale; the client lets the user update or clear it.
- The same two protection caps apply in every branch: `max_g_per_kg` against total body weight, and `max_energy_pct` against `E_t`.
- The earlier idea of capping the reference weight at a healthy-BMI weight is removed, in the maths, the YAML and the tests.
- Clinician questions raised here: the three lean-mass factors, the IBW formula, the adjusted-weight threshold and fraction, and the body-fat range.

### 4.8 Who gets targets

| Case | Result (`targets.status`) | Rule (YAML key) |
|---|---|---|
| Age unknown, height unknown, weight unknown, or sex unknown with no reference chosen | `needs_body_data`, with `details.fields` | |
| Age under 18 | `not_available_minor`: no energy or macro targets, intake only. Lose Weight and Build Muscle can't be chosen (Build Muscle is already adult-only: `ADULT_ONLY_GOALS`) | `minors.min_age_for_targets: 18` (the same age as `daily_limits.protein_min_age`) |
| Pregnant or breastfeeding = yes | `paused_pregnancy`: no targets, intake only, a note to ask a doctor | |
| Current BMI below 18.5 and direction = lose | Lose Weight not allowed: `422 goal_not_allowed_underweight`; maintenance is offered | `goal_rates.lose_min_current_bmi: 18.5` (WHO adult cut-off) |
| Target weight with BMI below 18.5 | `422 target_weight_too_low` (with the lowest allowed kg in `details`) | `goal_rates.target_weight_min_bmi: 18.5` |
| `body_fat_pct` given but outside the range | `422 body_fat_out_of_range` on the member or preview request; it is never used in a calculation | `body_fat.min_pct`, `body_fat.max_pct` |
| `health_data` consent withdrawn | `403 consent_required` on the targets routes (processing stops, ADR 0018); the diary keeps working without targets | Q13 |
| Otherwise | `ready` | |

### 4.9 Which body weight the maths uses

- With fewer than `trend.min_weigh_ins_for_trend` (3) weigh-ins, `W` is the latest weigh-in (`members.weight_kg`).
- From 3 weigh-ins on, `W` is the **trend weight** on the target date (section 4.10, step 2). Daily water swings then don't move the target.
- The protein reference weight (lean mass, adjusted weight or actual weight, section 4.7.1) is derived from the same `W`.
- The target is computed **at most once a day per member** and frozen in `diary_days`.

### 4.10 Adaptive TDEE (slice 7, behind a flag; Q3)

It runs once a week per member, on the account's local check-in day (`adaptive.check_in_weekday`, Monday), and writes one row to `energy_estimates`. All dates are **local dates** in the account's time zone (`accounts.timezone`, IANA name, default `Asia/Kolkata`), never UTC.

**Inputs**, over the window of `N = adaptive.window_days` (28) local days ending **yesterday** (today is never complete):

1. **Daily intake `I_d`.** The sum of the entries' `energy_kcal` on local day `d`. Day `d` is **eligible** only if all of these hold:
   - it has at least one entry;
   - no entry on it has unknown energy;
   - the user has not marked it "partly logged" (`diary_days.partial_logged`);
   - `I_d ≥ adaptive.min_day_fraction_of_formula × E_m_formula` (0.5). This filters forgotten days that the user did not mark.
2. **Trend weight `T_d`.** A time-aware exponential smoothing over **calendar days**:
   - `T_first = first weigh-in`.
   - For each later weigh-in `w` after a gap of `g` days: `α_g = 1 − (1 − α)^g`, then `T ← T + α_g (w − T)`, with `α = adaptive.trend_alpha_per_day` (0.1).
   - A weigh-in more than `adaptive.outlier_pct_from_trend` (3 %) away from the current trend is **kept for display but excluded** from the trend and the fit (flag `outlier_excluded`).
3. **Slope `b`** (kg/day). Ordinary least squares of the **raw, non-outlier weigh-ins** on `x = (local date − window start)` in **days**. Gaps are real gaps: skipping days does not compress time.

**Readiness gate.** Every one of these must hold, otherwise `ready = false` and the formula is used:

| Condition | Value | YAML key |
|---|---|---|
| Eligible intake days | ≥ 14 of 28 | `adaptive.min_intake_days` |
| Non-outlier weigh-ins | ≥ 6 | `adaptive.min_weigh_ins` |
| Span from first to last weigh-in in the window | ≥ 14 days | `adaptive.min_weigh_span_days` |
| A weigh-in in each of the last 2 weeks | yes | `adaptive.require_weigh_in_last_weeks: 2` |

The response gives the progress ("intake days 9 of 14, weigh-ins 4 of 6") so the UI can show a learning card.

**Estimate.**

```
Ī        = mean(I_d over eligible days)
E_raw_ad = Ī − b × ρ                                   (b < 0 when losing: maintenance is above intake)
E_band   = clamp(E_raw_ad, (1 − β) × E_m_formula, (1 + β) × E_m_formula)        β = adaptive.band_pct_of_formula / 100 = 0.25
E_prev   = last week's used value (the formula value the first time)
E_used   = E_prev + clamp(λ × (E_band − E_prev), −Δmax, +Δmax)                  λ = adaptive.step_fraction = 0.5
                                                                                  Δmax = adaptive.max_weekly_change_kcal = 150
```

- `E_used` replaces `E_m` in sections 4.4 to 4.6. **The floors, caps and rails all apply unchanged**, so adaptive mode can never plan below the floor.
- **The result is stored, not recomputed on each request.** `energy_estimates` keeps `E_m_formula`, `E_raw_ad`, `E_used`, the counts and the flags.
- **Why this shape:**
  - The band stops runaway values, and under-logging is a known bias that would otherwise lower targets.
  - The step fraction and the weekly cap damp noise, as MacroFactor does (closed §1).
  - Calendar-day x values and local dates fix NutriTrace's two bugs (NT §8).
- If the band clamps for 3 check-ins in a row, the response carries `adaptive_disagrees_with_formula`. The UI then suggests checking logging completeness. It does not suggest eating less.
- Every adaptive constant is a working value, PENDING CLINICIAN REVIEW.

### 4.11 Rapid-loss and low-intake checks (information cards, never a change of target downward)

| Check | Rule | YAML key | Effect |
|---|---|---|---|
| Rapid loss | Trend loss faster than 1.5 % of body weight per week, sustained over 3 weekly check-ins | `safety.rapid_loss_pct_bw_per_week`, `safety.rapid_loss_weeks` | Flag `rapid_loss`. The target is not lowered further: adaptive may raise it but not lower it. A neutral card suggests a slower rate |
| Low intake | 7 consecutive eligible days with intake below `E_floor` | `safety.low_intake_days` | Flag `low_intake_pattern`. A neutral, non-judging card that says what we saw and reminds the user that a day can be marked partly logged. No support link for now (Q14, R20). Shown once a week at most |

### 4.12 Worked examples (these become the golden fixtures)

Rounding is half-up. Macros are computed from the rounded `E_t`.

| # | Profile | BMR | `E_m` | `ΔE` | `E_t` | P / F / C (g) | Flags |
|---|---|---|---|---|---|---|---|
| G1 | Build Muscle; male, 28 y, 175 cm, 70 kg, moderate; gain 0.25 %/wk | 10·70 + 6.25·175 − 5·28 + 5 = **1,658.75** | × 1.55 = 2,571.06 | +0.175 kg/wk × 7,700 / 7 = **+192.5** | 2,763.56 → **2,760** | actual weight (no body fat, BMI 22.9): P = 1.6 × 70 = **112**; F = 2,760 × 0.25 / 9 = 76.67 → **77**; C = (2,760 − 448 − 693) / 4 = 404.75 → **405** | none |
| G2 | Lose Weight; female, 40 y, 160 cm, 80 kg, light; lose 0.5 %/wk | 800 + 1,000 − 200 − 161 = **1,439** | × 1.375 = 1,978.63 | −0.4 kg/wk → **−440** (25 % cap 494.7, 1,000 cap: not binding) | 1,538.63 → **1,540** (floor = max(1,200, 1,439) = 1,439: not binding) | no body fat and BMI 31.25 (≥ 30), so adjusted weight: IBW (Devine, female) = 45.5 + 2.3 × (62.99 − 60) = 52.38 kg; adjusted = 52.38 + 0.25 × (80 − 52.38) = 59.29 kg; P = 1.2 × 59.29 = 71.1 → **71**; F = 385 / 9 = 42.78 → **43**; C = (1,540 − 284 − 387) / 4 = 217.25 → **217** | none |
| G3 | Eat Healthy; female, 30 y, 155 cm, 55 kg, sedentary; maintain | 550 + 968.75 − 150 − 161 = **1,207.75** | × 1.2 = 1,449.3 | 0 | **1,450** | actual weight: P = 0.83 × 55 = 45.65 → **46**; F = 362.5 / 9 = 40.28 → **40**; C = (1,450 − 184 − 360) / 4 = 226.5 → **227** | none |
| G4 | Lose Weight; female, 55 y, 150 cm, 52 kg, sedentary; asks 1.0 %/wk | 520 + 937.5 − 275 − 161 = **1,021.5** | × 1.2 = 1,225.8 | −0.52 kg/wk → −572 → capped to 25 % of `E_m` = **−306.45** | E_raw = 919.35; floor = max(1,200, 1,021.5) = 1,200 ≤ E_m → **1,200** | BMI 23.1 (below 30), so actual weight 52; P = 1.2 × 52 = 62.4 → **62**; F = 300 / 9 = 33.33 → **33**; C = (1,200 − 248 − 297) / 4 = 163.75 → **164** | `deficit_capped`, `floor_applied` |
| G5 | Lose Weight; male, 35 y, 170 cm, 90 kg, light; 0.75 %/wk; target 75 kg; trend 76.2 kg | with W = 76.2: 762 + 1,062.5 − 175 + 5 = **1,654.5** | × 1.375 = 2,274.94 | full r_kg = 0.5715; d = 1.2; 0.5715 × 4 = 2.29 > 1.2, so r_kg = 0.3 → **−330** | 1,944.94 → **1,940** | BMI(76.2) = 26.4 (below 30), so actual weight 76.2; P = 1.2 × 76.2 = 91.44 → **91**; F = 485 / 9 = 53.89 → **54**; C = (1,940 − 364 − 486) / 4 = 272.5 → **273** | `taper_active` |
| G6 | Any goal; 16 y | n/a | n/a | n/a | **null** | null | status `not_available_minor` |
| G7 | Lose Weight; 168 cm, 50 kg (BMI 17.7) | n/a | n/a | n/a | n/a | n/a | `422 goal_not_allowed_underweight` |
| G8 | Sex `other`, no reference picked; 30 y, 165 cm, 60 kg, moderate; maintain | 600 + 1,031.25 − 150 − 78 = **1,403.25** | × 1.55 = 2,175.04 | 0 | **2,180** | P = 0.83 × 60 = 49.8 → **50**; F = 545 / 9 = 60.56 → **61**; C = (2,180 − 200 − 549) / 4 = 357.75 → **358** | `average_sex_reference` |
| G9 | Adaptive: formula `E_m` 2,000; 20 eligible days, Ī = 1,800; slope −0.05 kg/day; last week 2,000 | n/a | E_raw_ad = 1,800 + 385 = 2,185; band 1,500–2,500, not binding; step 0.5 → 2,092.5; Δ 92.5 < 150 | | `E_used` = 2,092.5 (target maths then as above) | | `adaptive_ready` |
| G10 | Adaptive with gaps: 13 eligible days | | **not ready**, formula used | | | | progress `13/14` |
| G11 | G1 profile plus body fat 15 % (Build Muscle) | 1,658.75 | 2,571.06 | +192.5 | **2,760** | lean mass = 70 × 0.85 = 59.5 kg; P = 2.0 × 59.5 = **119**; F = **77**; C = (2,760 − 476 − 693) / 4 = 397.75 → **398** | none (basis `lean_mass`) |
| G12 | G2 profile plus body fat 38 % (Lose Weight, BMI 31.25) | 1,439 | 1,978.63 | **−440** | **1,540** | body fat wins over BMI: lean mass = 80 × 0.62 = 49.6 kg; P = 1.5 × 49.6 = 74.4 → **74**; F = **43**; C = (1,540 − 296 − 387) / 4 = 214.25 → **214** | none (basis `lean_mass`) |

Protein branch coverage: actual weight (G1, G3, G4, G5, G8), adjusted weight (G2), lean mass (G11, G12). The BMI 29.9 / 30.0 and body-fat 2.9 / 3 / 70 / 70.1 boundaries are separate cases (section 9.1).

### 4.13 What changes in the existing YAML

- `thresholds.yaml` `daily_limits.protein_g_per_kg_by_goal` and `daily_limits.adult.protein_g_per_kg` **move** to `targets.yaml` `protein.*`, so there is one protein source. `daily_limits_for()` then reads them through `targets.protein_g_per_kg(goal)`.
- The **existing summary's protein target becomes the day's frozen `diary_days.protein_g` when one exists.** Otherwise it falls back to the old rule (g/kg × weight, adults only). The Home protein card and the diary then never show two different protein numbers.
- Q8 sets Lose Weight to 1.2 g/kg, so the expected outputs in `packages/test-fixtures/meals/expected` change for weight-loss members. That needs the safety reviewer and a PR note (AGENTS rule 4).
- `section_sources` gains `energy_targets` (sources: `mifflin_1990`, `cdc_weight_loss`, `iom_2005_dri`, `issn_protein_2017`, `morton_2018`, `icmr_nin_2024`, `smartnutri_working_values`). Each new source starts with `url_verified: false`.
- The "How we score" methodology page gets a "How we set daily guides" section. It is generated from the same YAML, as today.

### 4.14 `targets.yaml` skeleton (all values PENDING CLINICIAN REVIEW)

```yaml
# PENDING CLINICIAN REVIEW. Read only by app/scoring/targets.py. Never read by verdict rules.
version: 1
energy:
  equation: mifflin_st_jeor_1990
  mifflin:
    weight_kcal_per_kg: 10
    height_kcal_per_cm: 6.25
    age_kcal_per_year: 5
    sex_constant: {male: 5, female: -161, average: -78}
    valid_age: {min: 18, max: 78}
  activity_factor: {sedentary: 1.2, light: 1.375, moderate: 1.55, very: 1.725}
  kcal_per_kg_body_weight: 7700
goal_rates:
  lose: {options_pct_bw_per_week: [0.25, 0.5, 0.75, 1.0], default_pct_bw_per_week: 0.5, max_kg_per_week: 1.0}
  gain: {options_pct_bw_per_week: [0.1, 0.25, 0.5], default_pct_bw_per_week: 0.25}
  max_deficit_pct_of_maintenance: 25
  max_deficit_kcal_per_day: 1000
  taper: {weeks: 4, maintenance_band_kg: 0.5}
  target_weight_min_bmi: 18.5
  lose_min_current_bmi: 18.5
floors:
  kcal_by_sex: {female: 1200, male: 1500, average: 1500}
  min_bmr_multiple: 1.0
protein:
  g_per_kg_by_goal: {build_muscle: 1.6, weight_loss: 1.2, healthy_eating: 0.83, weight_gain: 0.83}   # weight_gain is the hidden goal: Eat Healthy value (Q15)
  default_g_per_kg: 0.83
  lean_mass_g_per_kg_by_goal: {build_muscle: 2.0, weight_loss: 1.5, healthy_eating: 1.0, weight_gain: 1.0, default: 1.0}   # used when body fat is given (Q10)
  max_g_per_kg: 2.2            # per kg of total body weight, every branch
  max_energy_pct: 35
  adjusted_weight: {min_bmi: 30, excess_fraction: 0.25}
  ibw:
    formula: devine            # [clinician] devine | bmi_based
    devine: {base_kg: {male: 50, female: 45.5, average: 47.75}, kg_per_inch_over_60: 2.3}
body_fat: {min_pct: 3, max_pct: 70}   # [clinician]
macros:
  fat_pct_energy: {default: 25, min: 20, max: 30}
  carbs_reference_min_g: 130
  kcal_per_g: {protein: 4, carbs: 4, fat: 9}
minors: {min_age_for_targets: 18}
trend: {min_weigh_ins_for_trend: 3}
adaptive:
  window_days: 28
  min_intake_days: 14
  min_weigh_ins: 6
  min_weigh_span_days: 14
  require_weigh_in_last_weeks: 2
  min_day_fraction_of_formula: 0.5
  trend_alpha_per_day: 0.1
  outlier_pct_from_trend: 3.0
  band_pct_of_formula: 25
  step_fraction: 0.5
  max_weekly_change_kcal: 150
  check_in_weekday: 1          # ISO weekday, account-local
projection: {min_weigh_ins: 6, min_span_days: 14, max_horizon_days: 730}
safety:
  rapid_loss_pct_bw_per_week: 1.5
  rapid_loss_weeks: 3
  low_intake_days: 7
rounding: {kcal_step: 10, macro_g_step: 1}
plausible:        # confirm-before-save ranges for body data (hard limits stay in the members API)
  height_cm: {min: 120, max: 210}
  weight_kg: {min: 30, max: 200}
  weight_change_kg_per_day: 2.0
```

`household_units.yaml` (section 5.6) holds the unit table. It is not a health threshold, but it is a data value and stays reviewable. `meal_slots.yaml` (section 5.12) holds the default slots, their time windows and the limit of 6.

---

## 5. Data model

All tables are created by Alembic, which owns the schema and RLS (ADR 0009). The pattern for every new account-owned table copies `0006_plan9_user_types`:

- `REVOKE ALL ... FROM PUBLIC, anon, authenticated`; `GRANT SELECT ... TO authenticated`; `GRANT ALL ... TO service_role` (ADR 0013: no direct data-API writes).
- `ENABLE` and `FORCE ROW LEVEL SECURITY`.
- `CREATE POLICY <t>_owner ... FOR ALL TO authenticated USING (account_id = (SELECT auth.uid())) WITH CHECK (same)`.
- Added to `ACCOUNT_OWNED_TABLES` (in delete order), so `DELETE /v1/me` erases it. `tests/api/test_delete_me.py` already fails until we do.

Member-scoped tables also get a **composite FK** `(member_id, account_id) → members(id, account_id) ON DELETE CASCADE`. Migration 0008 adds the needed `uq_members_id_account_id` unique constraint to `members`.

Numeric columns use `numeric` (exact), so there is no float drift (lesson from kcal §2).

### 5.1 Changes to existing tables

**`accounts`** (0008)

| Column | Type | Null | Notes |
|---|---|---|---|
| `timezone` | text | NOT NULL, default `'Asia/Kolkata'` | IANA name, validated against `zoneinfo` by the API. Used for local dates. Changing it does not move past entries |

**`members`** (0008). Body data stays where it is: `birth_year`, `sex`, `height_cm`, `weight_kg`, `goal`, all already gated by `health_data` (`HEALTH_FIELDS`).
- One new health column (Q10): `body_fat_pct`, numeric, NULL, with a check that it is NULL or between 3 and 70 [clinician]. The API validates against the YAML limits (`body_fat.min_pct`, `body_fat.max_pct`) and returns `422 body_fat_out_of_range`; the DB check is a backstop. NULL means unknown and is never treated as 0. It joins `HEALTH_FIELDS`, so reading or writing it needs `health_data`.
- New constraint `uq_members_id_account_id (id, account_id)` for the composite FKs.
- `weight_kg` becomes "the latest weigh-in". The weights API writes it in the same transaction as a `weight_logs` row, so verdict-side rules that read it are unchanged.

**`meal_logs`** becomes the diary entry table (0009). Existing rows stay valid.

| Column | Change | Type | Null | Notes |
|---|---|---|---|---|
| `local_date` | add | date | NOT NULL | Back-filled as `(eaten_at AT TIME ZONE 'Asia/Kolkata')::date`. Set by the API from `eaten_at` and `accounts.timezone`. Index `ix_meal_logs_member_id_local_date` |
| `meal_slot_id` | add | uuid | NOT NULL | Composite FK `(meal_slot_id, member_id) → meal_slots(id, member_id) ON DELETE RESTRICT`, so an entry can only use its own member's slot, and a slot with entries can never be deleted (it is archived, section 5.12). Back-filled by creating each member's default slots in the migration and giving each legacy row the slot for its IST hour (before 11:00 Breakfast, 11:00–15:59 Lunch, 16:00–18:59 Snacks, from 19:00 Dinner). When a client omits it, the API picks the slot from the local time windows (5.12). Index `(member_id, local_date, meal_slot_id)` |
| `source_kind` | add | text | NOT NULL, default `'product'` | `product`, `off`, `food`, `custom_food`, `recipe`, `quick_add`. Back-filled from `product_id` / `off_barcode` |
| `food_id` | add | uuid | NULL | FK `foods(id)` |
| `custom_food_id` | add | uuid | NULL | FK `custom_foods(id) ON DELETE SET NULL` (the snapshot keeps the history) |
| `recipe_id` | add | uuid | NULL | FK `recipes(id) ON DELETE SET NULL` |
| `quantity` | add | numeric | NULL | > 0, ≤ 1000. NULL on legacy rows (grams only) |
| `unit` | add | text | NULL | A unit code (section 5.6). `num_nonnulls(quantity, unit) in (0, 2)` |
| `grams` | **alter** | numeric | **NULL** (was NOT NULL) | NULL only for `quick_add`. The check `grams > 0 and grams <= 5000` is unchanged, plus `grams is not null or source_kind = 'quick_add'` |
| `food_snapshot` | add | jsonb | NULL | `{name, brand, basis: "g"|"ml", per_100: {nutrient: number|null}, units: {code: grams}, attribution}` at log time. NULL on legacy rows: an edit then derives per 100 g as `nutrients × 100 / grams`, the exact inverse |
| `nutrients` | extend keys | jsonb | NOT NULL | Adds `fibre_g` to the existing seven keys. Values are unrounded; null means unknown. Quick add: kcal required, macros optional, blanks are null |
| `updated_at` | add | timestamptz | NOT NULL, default now() | |
| `ck_meal_logs_product_ref` | **replace** | check | | With `ck_meal_logs_ref`: `num_nonnulls(product_id, off_barcode, food_id, custom_food_id, recipe_id) <= 1 AND (source_kind IN ('custom_food','recipe','quick_add') OR num_nonnulls(...) = 1)` plus a `source_kind` ↔ column match |
| `ck_meal_logs_source_kind`, `ck_meal_logs_unit` | add | check | | Closed sets. There is no slot check: slots are rows, not a closed set |

RLS: the existing `meal_logs_owner` policy (via the member's account) is unchanged. The downgrade deletes rows with `grams IS NULL` or a non-legacy `source_kind`, as 0003 did for OFF-only rows, and documents that. It also drops `meal_logs.meal_slot_id` and the `meal_slots` table, so custom slot names and assignments are lost on a downgrade, and the migration notes say so.

### 5.2 Goal settings: `diary_goal_settings` (0008)

One row per member. Every write needs `health_data`.

| Column | Type | Null | Notes |
|---|---|---|---|
| `member_id` | uuid | NOT NULL, PK | composite FK with `account_id` |
| `account_id` | uuid | NOT NULL | FK `accounts`, cascade |
| `direction` | text | NOT NULL | `lose`, `maintain`, `gain`. Default from the member's goal (section 1.5); an existing `weight_gain` member starts as `gain` (Q15) |
| `rate_pct_bw_per_week` | numeric | NULL | NULL for maintain. Must be one of the YAML options for the direction (checked by the API, not the DB, because options live in YAML) |
| `target_weight_kg` | numeric | NULL | 2–300. BMI rule checked by the API |
| `activity_level` | text | NOT NULL | `sedentary`, `light`, `moderate`, `very` |
| `sex_reference` | text | NULL | `male`, `female`, `average`; used only when `members.sex` is `other` or NULL |
| `pregnant_or_breastfeeding` | boolean | NOT NULL, default false | Health data. Pauses targets |
| `fat_pct_energy` | numeric | NULL | NULL = YAML default; else within the YAML min–max |
| `energy_mode` | text | NOT NULL, default `'formula'` | `formula`, `adaptive` (adaptive is accepted only when the server flag is on) |
| `numbers_display` | text | NOT NULL, default `'show'` (Q7) | `show`, `hide_energy`, `hide_all` |
| `summary_view` | text | NOT NULL, default `'remaining'` | `remaining`, `consumed` |
| `created_at`, `updated_at` | timestamptz | NOT NULL | |

### 5.3 Frozen daily targets and day status: `diary_days` (0008)

| Column | Type | Null | Notes |
|---|---|---|---|
| `member_id` | uuid | NOT NULL | PK part 1; composite FK |
| `local_date` | date | NOT NULL | PK part 2 |
| `account_id` | uuid | NOT NULL | |
| `status` | text | NOT NULL | `ready`, `needs_body_data`, `not_available_minor`, `paused_pregnancy`, `none` (no settings) |
| `energy_kcal` | numeric | NULL | NULL unless `ready` |
| `protein_g`, `fat_g`, `carbs_g` | numeric | NULL | |
| `basis` | text | NULL | `formula`, `adaptive` |
| `direction` | text | NULL | Frozen copy |
| `rate_pct_bw_per_week` | numeric | NULL | After clamping and taper |
| `inputs` | jsonb | NOT NULL, default `{}` | `{bmr, activity_factor, maintenance_kcal, adjustment_kcal, weight_kg_used, protein_basis, protein_g_per_kg, protein_reference_weight_kg, body_fat_pct_used, ibw_kg, floor_kcal, yaml_version}`, for the "how we got this" view and audits |
| `flags` | text[] | NOT NULL, default `{}` | e.g. `floor_applied`, `taper_active` |
| `partial_logged` | boolean | NOT NULL, default false | The user marked the day as not fully logged |
| `computed_at` | timestamptz | NOT NULL | |

Rules:
- A row is created the first time a day is read or logged.
- **Today's** row is recomputed when settings, weight or the time zone change. **Past rows are never recomputed.**
- A past day with no row gets `status = 'none'` and no target. It is never back-filled.

### 5.4 Weight log: `weight_logs` (0013)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | uuid | NOT NULL, PK | |
| `account_id`, `member_id` | uuid | NOT NULL | composite FK |
| `local_date` | date | NOT NULL | unique `(member_id, local_date)`: one per day, and a second save replaces it |
| `weight_kg` | numeric | NOT NULL | check 2–300 (same as members) |
| `measured_at` | timestamptz | NOT NULL | |
| `source` | text | NOT NULL, default `'manual'` | `manual` only in v1 (Q4), the same on both clients; `health_connect` is v2 |
| `client_id` | uuid | NULL | unique `(account_id, client_id)` |
| `created_at`, `updated_at` | timestamptz | NOT NULL | |

Stored kg only. lb display is not offered in v1 (India uses kg). If it is ever added, 1 lb = 0.45359237 kg exactly (FB's 2.2 was a bug).

### 5.5 Adaptive estimates: `energy_estimates` (0014)

| Column | Type | Null | Notes |
|---|---|---|---|
| `member_id` | uuid | NOT NULL | PK part 1 |
| `week_start` | date | NOT NULL | PK part 2 (the local check-in date) |
| `account_id` | uuid | NOT NULL | |
| `ready` | boolean | NOT NULL | |
| `formula_kcal` | numeric | NOT NULL | |
| `raw_kcal` | numeric | NULL | NULL when not ready |
| `used_kcal` | numeric | NOT NULL | Equals `formula_kcal` when not ready |
| `intake_days`, `weigh_ins`, `weigh_span_days` | integer | NOT NULL | |
| `slope_kg_per_day` | numeric | NULL | |
| `trend_weight_kg` | numeric | NULL | |
| `flags` | text[] | NOT NULL, default `{}` | |
| `computed_at` | timestamptz | NOT NULL | |

### 5.6 Units: `household_units` (reference, 0010) and `food_portions` (0010)

**`household_units`** is a reference table seeded from `household_units.yaml`. It is not account-owned. `SELECT` is granted to `authenticated` with policy `USING (true)`, and writes are service-role only.

| Column | Type | Null | Notes |
|---|---|---|---|
| `code` | text | NOT NULL, PK | |
| `kind` | text | NOT NULL | `mass`, `volume`, `count` |
| `ml` | numeric | NULL | Volume units only |
| `grams` | numeric | NULL | Mass units only (`g` = 1) |
| `sort` | integer | NOT NULL | |

The label is always the i18n key `unit.<code>`, never stored text.

Seed (Q6): our own reference set, checked by a dietitian before launch, with grams always shown and editable per food by the user. **Every volume is a working value until that check.**

| Code | Kind | Fixed size | Notes |
|---|---|---|---|
| `g` | mass | 1 g | |
| `ml` | volume | 1 ml | |
| `serving` | count | none (the food's own serving grams) | Offered only when the food has a serving weight |
| `katori` | volume | 150 ml [unverified] | Sizes vary from about 100 to 200 ml (third parties quote 120 and 200, closed §3). The UI always shows grams next to it |
| `cup` | volume | 200 ml [unverified] | Indian tea and steel cups, smaller than the US 240 ml |
| `glass` | volume | 250 ml [unverified] | |
| `tbsp` | volume | 15 ml | Metric tablespoon |
| `tsp` | volume | 5 ml | Metric teaspoon |
| `roti` | count | none | "One roti, chapati, phulka or paratha piece". Needs a per-food weight |
| `piece` | count | none | idli, dosa, egg, biscuit, ladoo… Needs a per-food weight |

**`food_portions`** holds per-food grams for a unit. A row is global (`account_id` NULL, curated by us) or a user override.

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | uuid | NOT NULL, PK | |
| `account_id` | uuid | NULL | NULL = global |
| `food_id` | uuid | NULL | exactly one of `food_id`, `custom_food_id`, `product_id`, `off_barcode` |
| `custom_food_id` | uuid | NULL | cascade |
| `product_id` | uuid | NULL | |
| `off_barcode` | text | NULL | Only grams per unit we derive ourselves; no OFF data is copied |
| `unit` | text | NOT NULL | FK `household_units(code)` |
| `grams_per_unit` | numeric | NOT NULL | > 0, ≤ 2000 |
| `source` | text | NOT NULL | `smartnutri_measured`, `reference_table`, `user`, `label` |
| `note` | text | NULL | internal (never shown) |
| `created_at` | timestamptz | NOT NULL | |

Unique on `(coalesce(account_id, nil), ref, unit)`. RLS for SELECT: `account_id IS NULL OR account_id = (SELECT auth.uid())`. Writes go through the API; global rows are service-role only.

**`to_grams(quantity, unit, food) → grams | None`** (API only, `app/features/foods/units.py`). It tries these in order:
1. `mass` unit: `quantity × unit.grams`.
2. `serving`: `quantity × food.serving_g`, else `None`.
3. A portion row for this food and unit, preferring the user override over the global row: `quantity × grams_per_unit`.
4. `volume` unit and the food has `density_g_per_ml`: `quantity × unit.ml × density`.
5. `volume` unit and the food is `ml`-based (`basis = 'ml'`): `quantity × unit.ml`, and the per 100 values are per 100 ml.
6. Otherwise `None`. The API never assumes ml = g, and returns `422 unit_grams_unknown`.

`foods_get` returns `units: [{code, grams_per_unit}]`, with only the units that resolve, so the picker never offers a unit that fails.

### 5.7 Generic foods: `foods` (reference, 0010; content per Q1)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | uuid | NOT NULL, PK | |
| `source` | text | NOT NULL | e.g. `ifct2017`, `usda_fdc`, `smartnutri_recipe` |
| `source_code` | text | NOT NULL | unique `(source, source_code)` |
| `name_en` | text | NOT NULL | Food names are **data**, not UI strings |
| `name_hi`, `name_mr` | text | NULL | Same; native-reviewed |
| `aliases` | text[] | NOT NULL, default `{}` | "chapati", "phulka", "रोटी" for search |
| `basis` | text | NOT NULL | `g`, `ml` |
| `per_100` | jsonb | NOT NULL | Same keys as product `per_100g`, null = unknown |
| `density_g_per_ml` | numeric | NULL | Only when the source gives it |
| `serving_g` | numeric | NULL | |
| `is_cooked` | boolean | NOT NULL | |
| `licence` | text | NOT NULL | e.g. `CC0` or `NIN permission <ref>`. Shown by the attribution component |
| `data_version` | text | NOT NULL | |

**Launch content (Q1).** We write to ICMR-NIN now to ask for written permission to use IFCT 2017 in a commercial app. Until it arrives, the table holds USDA FoodData Central ingredients (`usda_fdc`) and Indian dishes built as documented recipes from those ingredients (`smartnutri_recipe`, each listing its ingredients and grams, with no invented values). When NIN approves, `ifct2017` rows are added and the seed switches over, with the permission reference stored in `licence`. The USDA licence is re-verified before use.

Search index: `pg_trgm` GIN on `name_en || aliases`. RLS: SELECT for `authenticated USING (true)`; writes service-role only.

### 5.8 Custom foods: `custom_foods` (0011)

Account-owned (the family kitchen).

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | uuid | NOT NULL, PK | |
| `account_id` | uuid | NOT NULL | |
| `name` | text | NOT NULL | 1–80 |
| `brand` | text | NULL | |
| `basis` | text | NOT NULL | `g`, `ml` |
| `per_100` | jsonb | NOT NULL | At least energy **or** one macro must be known (`422 custom_food_nutrients_empty`). The rest is null; nothing is defaulted to 0 |
| `entered_per` | jsonb | NULL | `{amount, unit}` if the user typed values per serving; the API converts to per 100 and keeps this for editing |
| `serving_g` | numeric | NULL | |
| `density_g_per_ml` | numeric | NULL | |
| `barcode` | text | NULL | unique `(account_id, barcode)`. A scan of this barcode finds the user's own food first |
| `client_id` | uuid | NULL | unique `(account_id, client_id)` |
| `created_at`, `updated_at` | timestamptz | NOT NULL | |

Not shared to the public catalogue, and never fed to verdicts. A custom food that should get a verdict goes through the existing label-scan or `products_create` path instead.

### 5.9 Recipes: `recipes` and `recipe_ingredients` (0011)

**`recipes`** (account-owned)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | uuid | NOT NULL, PK | |
| `account_id` | uuid | NOT NULL | |
| `name` | text | NOT NULL | |
| `servings` | numeric | NULL | > 0; NULL means grams only |
| `cooked_weight_g` | numeric | NULL | > 0; NULL means the raw total weight is used |
| `per_100g` | jsonb | NOT NULL | Computed by the API on every save: `Σ(ingredient nutrients) / basis_weight × 100`. A nutrient unknown on any ingredient is still summed from the known ones, but is listed in `incomplete_nutrients` |
| `incomplete_nutrients` | text[] | NOT NULL, default `{}` | |
| `total_raw_g` | numeric | NOT NULL | |
| `client_id` | uuid | NULL | |
| `created_at`, `updated_at` | timestamptz | NOT NULL | |

**`recipe_ingredients`** (account-owned, cascade with the recipe; at most 50 per recipe)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | uuid | NOT NULL, PK | |
| `recipe_id` | uuid | NOT NULL | FK cascade |
| `account_id` | uuid | NOT NULL | |
| `position` | integer | NOT NULL | |
| `source_kind` | text | NOT NULL | `product`, `off`, `food`, `custom_food` (no nested recipes in v1) |
| `product_id`, `off_barcode`, `food_id`, `custom_food_id` | | NULL | Exactly one, by `source_kind`; `custom_food_id` SET NULL on delete |
| `name` | text | NOT NULL | Snapshot |
| `quantity`, `unit` | numeric, text | NOT NULL | |
| `grams` | numeric | NOT NULL | From `to_grams` |
| `per_100` | jsonb | NOT NULL | Snapshot |
| `attribution` | text | NULL | `attribution.off` for OFF ingredients |

A diary entry from a recipe stores the recipe's `per_100g` at that moment in `food_snapshot`, so later recipe edits don't change history.

### 5.10 Favourites: `favourites` (0012). Recents are a query.

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | uuid | NOT NULL, PK | |
| `account_id`, `member_id` | uuid | NOT NULL | composite FK |
| `source_kind` | text | NOT NULL | as in `meal_logs` minus `quick_add` |
| `product_id`, `off_barcode`, `food_id`, `custom_food_id`, `recipe_id` | | NULL | exactly one; cascade on custom food or recipe delete |
| `name` | text | NOT NULL | snapshot for display |
| `default_quantity`, `default_unit` | numeric, text | NULL | |
| `created_at` | timestamptz | NOT NULL | |

Unique on `(member_id, source_kind, ref)`. Maximum 200 per member.

**Recents** are not a table. `diary_recents` runs `SELECT DISTINCT ON (ref) ... FROM meal_logs WHERE member_id = ? ORDER BY ref, eaten_at DESC` over the last 60 days, optionally for one slot (by slot id), with the last used quantity and unit. Quick adds are excluded.

### 5.11 Migration list

| Migration | Contents | Slice |
|---|---|---|
| `0008_diary_goal_settings_targets` | `accounts.timezone`; `uq_members_id_account_id`; `members.body_fat_pct`; `diary_goal_settings`; `diary_days` | 1 |
| `0009_diary_meal_logs_extend` | `meal_slots` (5.12) with the default slots created for every existing member; the `meal_logs` changes in 5.1 (including `meal_slot_id`), with back-fills | 2 |
| `0010_diary_foods_units` | `household_units` (seeded), `foods`, `food_portions`, `pg_trgm` index | 3 |
| `0011_diary_custom_foods_recipes` | `custom_foods`, `recipes`, `recipe_ingredients`; `meal_logs` FKs to them | 4 |
| `0012_diary_favourites` | `favourites` | 5 |
| `0013_diary_weight_logs` | `weight_logs`; back-fill one row per member that has `weight_kg`, dated the member's `updated_at` local date | 6 |
| `0014_diary_energy_estimates` | `energy_estimates` | 7 |

Each migration ships with an upgrade and downgrade test, the RLS test (section 9.5), and an update to `ACCOUNT_OWNED_TABLES`.

Final delete order: `recipe_ingredients`, `favourites`, `meal_logs`, `meal_slots`, `recipes`, `food_portions` (user rows), `custom_foods`, `energy_estimates`, `weight_logs`, `diary_days`, `diary_goal_settings`, then the existing `members`, `scans`, … `consents`.

### 5.12 Meal slots: `meal_slots` (0009, Q16)

Member-scoped, with the composite FK and the RLS pattern at the top of section 5. The defaults are rows too, so every diary entry points at a slot id. Unique `(id, member_id)` supports the entry FK.

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | uuid | NOT NULL, PK | |
| `account_id`, `member_id` | uuid | NOT NULL | composite FK |
| `position` | integer | NOT NULL | Display order from 0. A reorder rewrites positions 0..n-1 in one transaction |
| `label_key` | text | NULL | i18n key for a default slot (`diary.slot.breakfast`, `.lunch`, `.snack`, `.dinner`) |
| `custom_label` | text | NULL | User text, 1–30 characters after trimming. Overrides `label_key` when set. Check: at least one of `label_key` and `custom_label` is set |
| `default_time_window` | jsonb | NULL | `{start: "HH:MM", end: "HH:MM"}` in the account's local time; may wrap past midnight; NULL when the user gave none |
| `is_default` | boolean | NOT NULL, default false | True for the four seeded slots, so the UI can offer "use the original name" |
| `archived_at` | timestamptz | NULL | Set when the slot is archived |
| `created_at`, `updated_at` | timestamptz | NOT NULL | |

Rules:
- **Defaults** come from `meal_slots.yaml`: Breakfast 04:00–10:59, Lunch 11:00–15:59, Snacks 16:00–18:59, Dinner 19:00–03:59 (the same bands the back-fill uses). They are created for existing members by migration 0009 and for new members the first time slots are read (idempotent). They show their i18n names until the user renames them.
- **Limit of 6** active (non-archived) slots per member, enforced by the API under a row lock on the member (`422 meal_slot_limit`). Archived slots do not count. At least one active slot must remain (`422 meal_slot_last_active`).
- **Display label** is `custom_label` when set, else the translated `label_key`. Custom labels are user text: stored exactly as typed, never translated, never sent to analytics, logs or any model prompt, and visible only to the owner. A rename never touches entries, because they point at the id. Clearing the custom label on a default slot restores its default name.
- **Default slot for a new entry** (the client sends no slot): take `eaten_at` in the account's local time. Use the active slot whose time window contains it (lowest position if windows overlap). If none does, use the active slot whose window starts latest before that time. If there is still none, use the lowest-position active slot. `meal_slots_list` also returns `suggested_slot_id` for the current moment, so clients preselect without their own logic.
- **Delete means archive when there is history.** Deleting a slot that has entries sets `archived_at` and nothing else. Its entries stay in the diary, visible on their days with the slot marked archived, and can be moved to an active slot. An archived slot is not offered for new entries. Deleting a slot that never had an entry removes the row. History is never deleted (`ON DELETE RESTRICT` on the entry FK backs this up).
- While `DIARY_FAMILY_ENABLED=false`, slots exist only for the `self` member.

---

## 6. API endpoints

Conventions, as in the existing API:
- Feature folders `app/features/<feature>/` (router, schemas, service, models).
- Errors are always `ErrorEnvelope` `{error: {code, message_key: "error.<code>", details}}`.
- `operation_id` is `<feature>_<action>`.
- Every route needs `terms` (the core service). Routes that **write or derive from body data** also need `health_data` (section 6.6).
- A request that names a member of another account returns `404 member_not_found`. A non-primary member returns `422 diary_member_not_enabled` while Family is off.
- `member_id` is optional everywhere and defaults to the primary member.
- Dates are **local dates** (`YYYY-MM-DD`) in the account's time zone. Timestamps are timezone-aware.
- Pagination is cursor-based: `?limit=` (1–100, default 50) and `?cursor=` (opaque). The response is `{items, next_cursor}`.
- All numbers are returned unrounded where the client needs to compute a preview, and rounded (1 dp, or the YAML step) where they are display values. Each field says which.

### 6.1 `targets` (`app/features/targets/`, prefix `/v1/targets`)

| Method and path | operation_id | Request | Response | Errors | Consent | Rate limit |
|---|---|---|---|---|---|---|
| `GET /v1/targets/settings?member_id` | `targets_settings_get` | n/a | `GoalSettingsOut` or `null` | 404, 422 | terms, health_data | n/a |
| `PUT /v1/targets/settings` | `targets_settings_put` | `GoalSettingsIn` | `TargetsOut` (today, recomputed) | `goal_not_allowed_minor`, `goal_not_allowed_underweight`, `target_weight_too_low`, `rate_not_allowed`, `fat_pct_out_of_range`, `adaptive_not_enabled`, `validation_error` | terms, health_data | `diary_settings` 30/day |
| `POST /v1/targets/preview` | `targets_preview` | `GoalSettingsIn` plus optional unsaved body data `{birth_year, sex, height_cm, weight_kg, body_fat_pct?}` | `TargetsOut` (not saved; `date` = today) | as above, plus `body_fat_out_of_range`, and `needs_body_data` returned as a status, not an error | terms, health_data | `targets_preview` 120/hour |
| `GET /v1/targets?member_id&date` | `targets_get` | n/a | `TargetsOut` (creates today's frozen row if missing; a past date with no row returns `status: none`) | `date_in_future` | terms, health_data | n/a |
| `GET /v1/targets/estimate?member_id` | `targets_estimate_get` | n/a | `EnergyEstimateOut` (readiness progress and the latest estimate) | `adaptive_not_enabled` | terms, health_data | n/a |
| `DELETE /v1/targets/settings?member_id` | `targets_settings_delete` | n/a | 204. Removes settings; today's day row becomes `none`; past days keep their frozen targets | | terms (erasure is never gated by health_data) | n/a |

```text
GoalSettingsIn {
  member_id?: uuid
  direction: "lose" | "maintain" | "gain"
  rate_pct_bw_per_week?: number          // must be one of the YAML options; omitted = the default
  target_weight_kg?: number | null
  activity_level: "sedentary" | "light" | "moderate" | "very"
  sex_reference?: "male" | "female" | "average" | null
  pregnant_or_breastfeeding: boolean
  fat_pct_energy?: number | null
  energy_mode?: "formula" | "adaptive"
  numbers_display?: "show" | "hide_energy" | "hide_all"
  summary_view?: "remaining" | "consumed"
}

TargetsOut {
  member_id: uuid
  date: date
  status: "ready" | "needs_body_data" | "not_available_minor" | "paused_pregnancy" | "none"
  missing_fields: string[]               // for needs_body_data, e.g. ["height_cm"]
  energy_kcal: number | null             // rounded to the kcal step; null when hidden (numbers_hidden) or not ready
  protein_g, fat_g, carbs_g: number | null
  basis: "formula" | "adaptive" | null
  direction: "lose" | "maintain" | "gain" | null
  rate: { pct_bw_per_week: number, kg_per_week: number } | null      // after clamping and taper
  explanation: {                          // "how we got this"; numbers null when hidden
    bmr_kcal, activity_factor, maintenance_kcal, adjustment_kcal,
    weight_kg_used, protein_basis: "lean_mass" | "adjusted_weight" | "actual_weight",
    protein_g_per_kg, protein_reference_weight_kg, body_fat_pct_used, ibw_kg, floor_kcal
  } | null
  flags: string[]                          // floor_applied, floor_limits_deficit, rate_capped, deficit_capped,
                                           // taper_active, goal_weight_reached, protein_capped, carbs_below_reference,
                                           // average_sex_reference, outside_equation_age_range, rapid_loss,
                                           // low_intake_pattern, adaptive_ready, adaptive_disagrees_with_formula
  numbers_hidden: { energy: boolean, macros: boolean }
  sources: string[]                        // keys of thresholds/targets sources, for the methodology link
  pending_clinician_review: true
}
```

**Body fat on the member (Q10).** `body_fat_pct` is added as an optional, nullable number to the existing members create, update and read schemas (3–70; anything else is `422 body_fat_out_of_range`; null clears it). It is a health field: it needs `health_data` like height and weight, and is withheld without that consent as the other health fields are. `GoalSettingsIn` does not carry it, because body data stays on the member; `targets_preview` accepts it as unsaved input.

### 6.2 `diary` (`app/features/diary/`, prefix `/v1/diary`) and the extended `meals` routes

Entry CRUD stays under `/v1/meals`, so Android's offline queue and the existing clients keep working. The day, week and recents views are new under `/v1/diary`.

| Method and path | operation_id | Request | Response | Errors | Consent | Rate limit |
|---|---|---|---|---|---|---|
| `POST /v1/meals` (extended) | `meals_log` | `MealIn` v2 (below) | 201 `MealOut` v2; 200 for a repeated `client_id` | `invalid_food_ref`, `portion_required`, `unit_not_supported`, `unit_grams_unknown`, `quantity_out_of_range`, `serving_size_unknown`, `eaten_at_out_of_range`, `quick_add_energy_required`, `food_not_found`, `custom_food_not_found`, `recipe_not_found`, `meal_slot_not_found`, `meal_slot_archived`, 503 OFF unavailable | terms | `meal_logs` 300/day (existing) |
| `PATCH /v1/meals/{id}` | `meals_update` | `{quantity?, unit?, grams?, meal_slot_id?, eaten_at?}` | `MealOut` v2 (recomputed from `food_snapshot`) | `meal_not_found`, and the portion errors above | terms | `meal_logs` |
| `DELETE /v1/meals/{id}` | `meals_delete` (existing) | n/a | 204 | `meal_not_found` | terms | n/a |
| `POST /v1/meals/copy` | `meals_copy` | `{member_id?, from_date, from_slot_id?, to_date, to_slot_id?, client_id}` (no `from_slot_id` copies the whole day; an entry whose slot is archived needs an explicit `to_slot_id`) | 201 `{created: MealOut[]}` | `copy_source_empty`, `date_in_future`, `date_too_old`, `copy_too_many` (more than 50 entries), `meal_slot_not_found`, `meal_slot_archived` | terms | `meal_logs` (counts each created entry) |
| `GET /v1/meals` (existing) | `meals_list` | adds `?local_date=` | `MealOut[]` v2 | | terms | n/a |
| `GET /v1/meals/summary` (existing) | `meals_summary` | unchanged | `Summary` (protein target now from `diary_days` when present; totals add `fat_g`, `carbs_g`, `fibre_g`) | | terms | n/a |
| `GET /v1/diary/day?member_id&date` | `diary_day_get` | n/a | `DiaryDayOut` | `date_in_future` | terms (+ health_data for the `targets` part: without it, `targets` is null with `targets_status: consent_required`) | n/a |
| `GET /v1/diary/week?member_id&end` | `diary_week_get` | n/a | `DiaryWeekOut` (7 days, oldest first) | | as above | n/a |
| `PUT /v1/diary/days/{date}/status` | `diary_day_status_put` | `{member_id?, partial_logged: bool}` | `DiaryDayStatusOut` | `date_in_future` | terms | `diary_settings` |
| `GET /v1/diary/recents?member_id&slot_id&limit` | `diary_recents_list` | n/a | `{items: RecentItem[]}` (at most 30; no cursor) | | terms | n/a |

```text
MealIn v2 {
  member_id?: uuid
  // exactly one food reference, or `quick`:
  product_id?: uuid; barcode?: string; food_id?: uuid; custom_food_id?: uuid; recipe_id?: uuid
  quick?: { name?: string(≤60), energy_kcal: number(>0, ≤5000), protein_g?, fat_g?, carbs_g?, fibre_g? }   // blanks stay null
  // exactly one portion form (not for quick):
  grams?: number | servings?: number | { quantity: number, unit: UnitCode }
  meal_slot_id?: uuid                                          // an active slot of this member; default picked from the local time windows (5.12)
  eaten_at?: datetime                                          // default now; ≤ 5 min ahead, ≤ 30 days ago (existing rule)
  client_id?: uuid
}

MealOut v2 = MealOut (existing fields; `grams` becomes nullable for quick add) + {
  source_kind, food_id, custom_food_id, recipe_id, quantity, unit, meal_slot_id, local_date,
  nutrients: NutrientSnapshot (+ fibre_g),            // 1 dp display values; null = unknown
  incomplete: string[],                               // nutrient keys that are null on this entry
  attribution                                          // existing: "attribution.off" for OFF products and OFF recipe ingredients
}

DiaryDayOut {
  member_id, date, timezone
  slots: [{ slot_id, label_key | null, custom_label | null, position, archived, entries: MealOut[], totals: Totals }]
       // the member's active slots in position order, plus an archived slot only on a day that has entries in it
  totals: Totals { energy_kcal, protein_g, fat_g, carbs_g, fibre_g, sugars_g, salt_g }   // sums of KNOWN values, null if none known
  incomplete: { <nutrient>: bool }
  targets: TargetsOut | null
  targets_status: "ready" | "none" | "needs_body_data" | "not_available_minor" | "paused_pregnancy" | "consent_required"
  remaining: { energy_kcal, protein_g, fat_g, carbs_g } | null
       // target − eaten, may be negative (= over); null per nutrient when that total is incomplete,
       // when there is no target, or when hidden. Never computed on the client.
  progress: { energy_kcal, protein_g, fat_g, carbs_g }     // eaten ÷ target, 0..n, for the ring; null under the same rules
  limits_bands: NutrientBands                             // existing sugar/salt bands (from meals_summary rules)
  partial_logged: bool
  numbers_hidden: { energy: bool, macros: bool }
  pending_clinician_review: true
}
```

**Hiding numbers is enforced on the server.** With `hide_energy`, every energy field in `TargetsOut`, `DiaryDayOut`, `DiaryWeekOut` and `MealOut.nutrients.energy_kcal` comes back `null`, with `numbers_hidden.energy = true`. With `hide_all`, the macro fields are null as well. The entries, the portions and the ring "shape" (`progress`, rounded to 0.25 steps) still come back, so the diary stays usable. A client bug therefore cannot show hidden numbers.

`DiaryWeekOut` has 7 `DayTile`s (`date, totals, incomplete, targets: {energy_kcal, protein_g} | null, progress, partial_logged, items`) and `averages`. The averages are taken **over days with logged items that are not partial**, and the count of those days is returned beside them, so empty days never pull the average down (FB §6) and are never shown as "0".

### 6.2.1 Meal slots (`app/features/meal_slots/`, prefix `/v1/meal-slots`, Q16)

| Method and path | operation_id | Request | Response | Errors | Consent | Rate limit |
|---|---|---|---|---|---|---|
| `GET /v1/meal-slots?member_id&include_archived` | `meal_slots_list` | n/a | `{items: MealSlotOut[], suggested_slot_id}`. Creates the four defaults on the first call | 404, 422 | terms | n/a |
| `POST /v1/meal-slots` | `meal_slots_create` | `{member_id?, custom_label (1–30), default_time_window?, client_id?}` | 201 `MealSlotOut`, added at the end (200 for a repeated `client_id`) | `meal_slot_limit`, `meal_slot_label_duplicate`, `validation_error` | terms | `diary_writes` |
| `PATCH /v1/meal-slots/{id}` | `meal_slots_rename` | `{custom_label?, default_time_window?}`. A null `custom_label` on a default slot restores its original name | `MealSlotOut` | `meal_slot_not_found`, `meal_slot_archived`, `meal_slot_label_duplicate`, `validation_error` | terms | `diary_writes` |
| `PUT /v1/meal-slots/order` | `meal_slots_reorder` | `{member_id?, ids: uuid[]}` (every active slot exactly once) | `{items: MealSlotOut[]}` | `meal_slot_not_found`, `validation_error` | terms | `diary_writes` |
| `DELETE /v1/meal-slots/{id}` | `meal_slots_archive` | n/a | 200 `{result: "archived" \| "deleted"}`. Archives when the slot has entries; removes the row only when it never had any | `meal_slot_not_found`, `meal_slot_last_active` | terms | `diary_writes` |

```text
MealSlotOut { id, member_id, position, label_key | null, custom_label | null,
              default_time_window | null, is_default, archived }
```

- The label rules, the limit of 6 and the default-slot choice are in section 5.12. Names are unique among a member's active slots, ignoring case.
- Slots hold no health data, so they need only `terms`. Their labels are never sent to analytics (section 6.8).

### 6.3 `foods` (`app/features/foods/`, prefix `/v1/foods`), `custom_foods` and `recipes`

| Method and path | operation_id | Request | Response | Errors | Consent | Rate limit |
|---|---|---|---|---|---|---|
| `GET /v1/foods/search?q&kinds&limit&cursor` | `foods_search` | `q` 2–80 characters; `kinds` ⊆ `food, custom_food, recipe, product` | `{items: FoodHit[], next_cursor}`. Order: my custom foods and recipes, then recents that match, then generic foods (trigram rank), then own-catalogue and OFF products via the existing products search service | `query_too_short`, 503 for OFF only (other kinds still return, with `partial: true` and `failed_sources`) | terms | `search` 60/min (existing) |
| `GET /v1/foods/{kind}/{id}` | `foods_get` | `kind` ∈ `food, custom_food, recipe, product, off` (`id` = barcode for off) | `FoodDetailOut {kind, id, name, brand, basis, per_100 (unrounded, null = unknown), units: [{code, grams_per_unit}], serving_g, attribution, licence}` | `food_not_found` | terms | `product_lookups` 300/hour (existing) |
| `GET /v1/foods/units` | `foods_units_list` | n/a | `UnitOut[] {code, kind, ml, grams}` | | terms | n/a |
| `PUT /v1/foods/{kind}/{id}/portions/{unit}` | `foods_portion_put` | `{grams_per_unit}` (the user's own override) | `FoodDetailOut` | `unit_not_supported`, `validation_error` | terms | `diary_writes` 200/day |
| `DELETE /v1/foods/{kind}/{id}/portions/{unit}` | `foods_portion_delete` | n/a | 204 | | terms | n/a |
| `GET /v1/custom-foods` | `custom_foods_list` | paginated | `{items: CustomFoodOut[], next_cursor}` | | terms | n/a |
| `POST /v1/custom-foods` | `custom_foods_create` | `CustomFoodIn {name, brand?, basis, values_per: {amount, unit}, nutrients: {...}, serving_g?, density_g_per_ml?, barcode?, client_id?}` | 201 `CustomFoodOut` (200 on a repeated `client_id`) | `custom_food_nutrients_empty`, `barcode_already_used`, `validation_error` | terms | `diary_writes` |
| `PATCH /v1/custom-foods/{id}` | `custom_foods_update` | partial `CustomFoodIn` | `CustomFoodOut` | `custom_food_not_found` | terms | `diary_writes` |
| `DELETE /v1/custom-foods/{id}` | `custom_foods_delete` | n/a | 204 (diary history stays, through the snapshot) | `custom_food_not_found` | terms | n/a |
| `GET /v1/recipes` | `recipes_list` | paginated | `{items: RecipeSummaryOut[], next_cursor}` | | terms | n/a |
| `GET /v1/recipes/{id}` | `recipes_get` | n/a | `RecipeOut {..., ingredients[], per_100g, per_serving, incomplete_nutrients}` | `recipe_not_found` | terms | n/a |
| `POST /v1/recipes` | `recipes_create` | `RecipeIn {name, servings?, cooked_weight_g?, ingredients: [{ref, quantity, unit}] (1–50), client_id?}` | 201 `RecipeOut` | `recipe_ingredient_limit`, `recipe_weight_invalid` (cooked weight above 3 × raw or below 0.2 × raw), `unit_grams_unknown` (with `details.position`), `invalid_food_ref` | terms | `diary_writes` |
| `PUT /v1/recipes/{id}` | `recipes_update` | `RecipeIn` | `RecipeOut` | as above | terms | `diary_writes` |
| `DELETE /v1/recipes/{id}` | `recipes_delete` | n/a | 204 | `recipe_not_found` | terms | n/a |

The existing barcode lookup first checks the user's own `custom_foods.barcode`, then follows the existing order (own catalogue, OFF cache, OFF), as ONT §5 does. That is a change to `products_get_by_barcode` and `resolve_ref` for the logging path only. **Verdicts never use custom foods.**

### 6.4 `favourites` (`/v1/favourites`)

| Method and path | operation_id | Request | Response | Errors | Consent | Rate limit |
|---|---|---|---|---|---|---|
| `GET /v1/favourites?member_id` | `favourites_list` | paginated | `{items: FavouriteOut[], next_cursor}` | | terms | n/a |
| `POST /v1/favourites` | `favourites_add` | `{member_id?, ref, default_quantity?, default_unit?}` | 201 `FavouriteOut` (200 if it already exists) | `favourite_limit`, `invalid_food_ref` | terms | `diary_writes` |
| `DELETE /v1/favourites/{id}` | `favourites_delete` | n/a | 204 | `favourite_not_found` | terms | n/a |

### 6.5 `weights` (`/v1/weights`)

| Method and path | operation_id | Request | Response | Errors | Consent | Rate limit |
|---|---|---|---|---|---|---|
| `GET /v1/weights?member_id&from&to` | `weights_list` | dates; default the last 90 days; max 400 days | `{items: WeightOut[]}` (one per day, so bounded; no cursor) | `date_range_too_long` | terms, health_data | n/a |
| `PUT /v1/weights/{date}` | `weights_put` | `{member_id?, weight_kg, confirm_unusual?: bool, client_id?}` | `WeightOut` (also sets `members.weight_kg` when it is the latest date, and recomputes today's targets) | `weight_out_of_range` (outside 2–300), `weight_needs_confirm` (outside the plausible range, or more than 2 kg/day from the previous weigh-in, with `details.previous`), `date_in_future`, `date_too_old` (more than 400 days) | terms, health_data | `weights` 30/day |
| `DELETE /v1/weights/{date}?member_id` | `weights_delete` | n/a | 204 (`members.weight_kg` falls back to the latest remaining row, or stays unchanged if none remain) | `weight_not_found` | terms (erasure never needs health_data) | n/a |
| `GET /v1/weights/trend?member_id&days` | `weights_trend_get` | `days` ∈ 30, 90, 365 | `WeightTrendOut {points: [{date, weight_kg, outlier}], trend: [{date, trend_kg}], weekly_rate: {kg, pct_bw} \| null, projection: {target_kg, date} \| null, projection_reason: "ready" \| "too_few_weigh_ins" \| "moving_away" \| "no_target" \| "too_far", numbers_hidden}` | | terms, health_data | n/a |

With `numbers_display = hide_all`, `weights_trend_get` still returns the shape of the chart, but the kg values are null. The user has to choose "show" in settings to see them.

### 6.6 Consent mapping (extends ADR 0017 and 0018)

| Route group | Purposes | Why |
|---|---|---|
| `meals_*`, `diary_*` (entries, day and week views, recents), `meal_slots_*`, `foods_*`, `custom_foods_*`, `recipes_*`, `favourites_*` | `terms` | Food logging is the core service, as ruled for meal logs in ADR 0017. The lawyer's DPDP question there still applies |
| `targets_*` (except delete), `weights_*` (except delete) | `terms` + `health_data` | They write or process body data (height, weight, sex, pregnancy, target weight, body fat) |
| The `targets` part of `diary_day_get` and `diary_week_get` | `health_data` checked inside the handler | Without it, the day still loads, with `targets: null` and `targets_status: consent_required` |
| `targets_settings_delete`, `weights_delete` | `terms` only | Erasure must always be possible |

- **Withdrawing `health_data` stops target processing** (ADR 0018 option 1: stop, don't erase).
  - Unlike verdicts, targets are not a safety function, so there is no reason to keep processing.
  - Stored settings, weights and frozen days are kept, and processing resumes on re-consent.
  - This needs a short ADR, **0022**: "Daily targets are information computed by the API; health_data gates them" (Q13).
- `REQUIRED` in `app/core/consent.py` gains `"targets": ("terms", "health_data")` and `"weights": ("terms", "health_data")`.
- New rate-limit buckets go in `BUCKETS` and `Settings`: `diary_settings` (day, 30), `targets_preview` (hour, 120), `diary_writes` (day, 200), `weights` (day, 30).

### 6.7 New error codes (each needs an `error.<code>` key in en, hi and mr)

`invalid_food_ref`, `unit_not_supported`, `unit_grams_unknown`, `quantity_out_of_range`, `quick_add_energy_required`, `food_not_found`, `custom_food_not_found`, `recipe_not_found`, `favourite_not_found`, `weight_not_found`, `copy_source_empty`, `copy_too_many`, `date_in_future`, `date_too_old`, `date_range_too_long`, `query_too_short`, `custom_food_nutrients_empty`, `barcode_already_used`, `recipe_ingredient_limit`, `recipe_weight_invalid`, `favourite_limit`, `goal_not_allowed_minor`, `goal_not_allowed_underweight`, `target_weight_too_low`, `rate_not_allowed`, `fat_pct_out_of_range`, `adaptive_not_enabled`, `weight_out_of_range`, `weight_needs_confirm`, `diary_member_not_enabled`, `body_fat_out_of_range`, `meal_slot_not_found`, `meal_slot_archived`, `meal_slot_limit`, `meal_slot_last_active`, `meal_slot_label_duplicate`.

Existing codes reused: `portion_required`, `serving_size_unknown`, `eaten_at_out_of_range`, `meal_not_found`, `member_not_found`, `consent_required`, `rate_limited`, `validation_error`.

### 6.8 Analytics (no health data)

- Add to `ALLOWED_EVENTS` (API, Android and web together): `diary_entry_added {method}`, with `method` ∈ `search, barcode, label, recent, favourite, quick_add, custom, recipe, copy`; and `diary_day_viewed {}`.
- **Never** sent: any target, weight, rate, goal, direction, nutrient, flag, "hidden numbers" state, pregnancy answer, body-fat value, custom meal-slot label (it is user text) or slot count, or onboarding answer.
- The existing tests that compare the three allow-lists are extended to cover the new events.

---

## 7. Client design (Android and web, full parity)

General rules (from AGENTS, ADR 0019 and the existing apps):
- Both clients render only what the API returns.
- The portion preview is the one exception. The client shows `quantity × grams_per_unit × per_100 / 100` from `foods_get` as a **preview**. The saved value is the API's own result, and a shared fixture proves the client preview equals the API result for every unit case (section 9.2).
- Colours come from design tokens. Progress uses the **brand** colour, unknown or incomplete uses the grey "not enough data" style, and going over a target uses a **neutral** tone, never red. Verdict colours (`ok` green and so on) are never used for targets.
- Every screen shows "Information, not medical advice" and "pending clinician review" where numbers appear.
- Android keeps its offline queue (drift) for entries and weights, using `client_id`. The web stays online-only and says so (existing copy).

### 7.1 Goal setup (onboarding for body data and goal)

Entered from:
- the follow-up step of the Build Muscle, Lose Weight or Eat Healthy chip (Plan 9's user-type follow-ups);
- the Today empty state ("Set up your daily guide");
- Settings.

Steps (one per screen on mobile, a single stepper page on desktop web):

1. **Intro.** What the guide is: an estimate, information, not advice. A three-way choice of how to see numbers: "Show numbers" (preselected), "Hide calories", "Hide all numbers" (Q7). A one-tap eye toggle on Today changes it later. A "Skip, just log food" link.
2. **About you.** Birth year, sex (female, male, other or prefer not to say; for the last two, a choice of which estimate to use: female, male or in-between, preselected, see Q11). Height. Weight. Body fat %, optional. All pre-filled from the member.
   - **Body-fat explanation (Q10).** Shown under the field: "Optional. If you know it, for example from a body-composition scale, we base your protein guide on lean mass. If you leave it blank, we use your weight." Blank is saved as unknown, never 0. A value outside 3–70 shows the API's message. The user can update or clear it at any time.
   - Values outside the plausible range ask for confirmation.
   - Missing `health_data` consent opens the existing consent dialog before saving.
3. **Activity.** Four cards with everyday Indian examples (desk job and little walking; on your feet part of the day; active job or exercise most days; hard physical work or daily hard training).
4. **Goal.** The direction comes from the chip and can be changed. Rate options appear as chips showing kg/week **as computed by `targets_preview`**, never by the client. Optional target weight. The question "Are you pregnant or breastfeeding?" (yes, no, prefer not to say; the last pauses targets, as yes does).
5. **Your daily guide.** The `targets_preview` result: kcal, protein, fat, carbs, and an expandable "How we got this" (BMR, activity, adjustment, floor, protein g/kg and which weight it was based on: lean mass, adjusted weight or actual weight, with sources). Flags shown as neutral notes (for example, a floor). Save calls `targets_settings_put`.

States:
- loading;
- API error, with retry;
- `needs_body_data` (the missing fields are highlighted);
- `not_available_minor`: a friendly "daily guides are for adults; you can still log food";
- `paused_pregnancy`;
- `goal_not_allowed_underweight`: maintenance is offered, with neutral copy and no figures about "too low".

### 7.2 Today (the Diary day screen)

- **Header:** a date switcher (previous, today, next, and a calendar). A future date is not selectable. An eye icon hides or shows numbers in one tap (Q7).
- **Rings:** one large energy ring and three smaller rings (or bars on narrow screens) for protein, carbs and fat.
  - Each shows **remaining** or **consumed** (`summary_view`), with a toggle chip.
  - The values come from `remaining` and `progress`.
  - An incomplete nutrient shows a grey "Some items don't show this value, so the total may be higher" chip instead of a number.
  - Over target shows "X over" in the neutral tone.
  - With `numbers_hidden`, the rings show only fill shapes, with no numbers.
- **Meal slots:** one section per active slot from `meal_slots_list`, in the user's order (four defaults, up to six). The title is the user's custom name, or the translated default name. A slot the user removed appears only on days that have entries in it, marked as removed. Each section has:
  - entries showing name, portion ("2 roti · 80 g") and kcal (unless hidden), plus an incomplete marker and OFF attribution where needed;
  - an "Add" button;
  - a menu: copy this meal to another day or slot, or move entries.
- **Day menu:** "Copy yesterday", "Copy a day…", "Mark as partly logged" (explains that this keeps the day out of averages and learning), "Manage meals" (section 7.11).
- **Sugar and salt bands** (from the existing summary) are a small row under the rings. These are existing limits, not targets.
- **Empty states:** no goal set up ("Set up your daily guide, or just log food"); nothing logged ("Nothing logged yet").
- **Errors:** offline (Android shows queued entries with a "waiting to sync" badge; web shows the online-only note); `consent_required` for targets (a card to grant `health_data`, while the diary still works).

### 7.3 Add food

A bottom sheet on Android and a dialog or side panel on web. Segments:

1. **Search:** one box. Results are grouped (My foods and recipes, Indian foods, Packaged products), each with a kind badge and attribution. A partial-failure note when OFF is unreachable, which says so instead of claiming "no results" (ONT §1 lesson).
2. **Recent:** for this slot first, then all; each with its last quantity and unit (one tap logs again).
3. **Favourites.**
4. **Barcode:** opens the existing scanner (F3) with "for the diary" context. A found product goes to the portion picker. Not found leads to the label flow (F4/F15) and then the portion picker. The verdict screen stays available ("See if it suits you"), and the verdict is unchanged.
5. **Label scan:** the existing flow, with confirmation required (AGENTS rule 2).
6. **Quick add:** an optional name, kcal (required), and optional protein, carbs, fat and fibre. Blank fields stay unknown, with a note that blanks are treated as unknown, not 0.
7. **Create:** "New food" (section 7.6) or "New recipe" (section 7.7).

### 7.4 Portion picker

- Unit chips for the units the API returned, for example `katori · roti · g`.
- A quantity stepper with fraction chips (¼, ½, 1, 1½, 2) and free input. Grams are always shown ("1 katori ≈ 150 g · edit").
- "Edit grams for this unit" saves the user's own portion override (`foods_portion_put`).
- A live preview of kcal and macros (preview only, section 7). Unknown nutrients show "not on the label".
- Slot and time. Save, with an "Add to favourites" toggle.
- Errors: `unit_grams_unknown` offers grams; `quantity_out_of_range`.

### 7.5 Day, week and progress views

- **Week:** seven bars of energy against the frozen target line for each day (each day has its own line, because targets are frozen), plus protein on how many days the target was met (`n of 7 logged days`). Averages are over complete logged days, with the count shown. Incomplete and partial markers. **No good or poor day labels, no streaks.**
- **Progress:**
  - A weight chart with raw dots (outliers drawn hollow) and the trend line.
  - The weekly rate as "about 0.3 kg per week (0.4 % of body weight)".
  - A projection sentence only when `projection_reason = ready`. Otherwise a neutral reason ("Not enough weigh-ins yet").
  - The adaptive card (slice 7): "Learning your energy use: 9 of 14 days, 4 of 6 weigh-ins", then "This week's estimate: 2,090 kcal (formula 2,000)" with an explanation.
  - Rapid-loss and low-intake cards (section 4.11), worded neutrally, with no support link for now (Q14, R20).

### 7.6 Custom food

Name, brand, values per 100 g, per 100 ml or per serving (the user picks; the API converts), the nutrient fields (energy, protein, carbs, sugars, fat, saturated fat, fibre, salt or sodium), serving size, optional barcode, and optional household-unit grams. Blank fields stay unknown. Validation errors come from the API.

### 7.7 Recipe builder

A name; ingredients added through the same search and portion picker; servings; and an optional cooked weight, with a tip: "Weigh the pot after cooking for the best accuracy".

The live per-serving and per-100 g figures come from the API on save. Before saving, the client shows the ingredient list only. The editor marks nutrients that are incomplete.

### 7.8 Weight log

- Add a weigh-in (date, kg) with the tip "Same time of day, e.g. after waking". Unusual values ask for confirmation.
- A list, with edit and delete.
- No reminders by default. An optional weekly reminder, off by default.

### 7.9 Settings ("Diary and daily guide")

- Goal, rate and target weight; activity; fat share (a 20–30 % slider); targets mode (formula, or adaptive when the flag is on).
- **Numbers:** show, hide calories, or hide all. Also reachable in one tap from the Today header (an eye icon) and offered in onboarding.
- Remaining or consumed.
- Pregnancy and breastfeeding.
- Reset the daily guide (`targets_settings_delete`). Delete all diary data goes through the existing account deletion; a per-feature wipe is Q-later.
- **Meals:** manage meal slots (section 7.11).
- Body data, including the optional body-fat % with its explanation (Q10).
- There is no support entry in v1 (Q14, R20).

### 7.10 Mode and tab placement (`packages/test-fixtures/modes/layouts.json`)

- Add the destination `diary`.
- **The existing `history` destination becomes `diary`.** The Diary day and week views replace the History day list and weekly dashboard, which they extend. The old `/history` route redirects to `/diary` on both clients, so links and tests keep working. Scan stays second in every mode.

| Mode (chip) | Tabs today | Proposed tabs | Home cards (proposed) |
|---|---|---|---|
| `gym` (Build Muscle) | home, scan, protein, compare, profile | home, scan, **diary**, protein, profile (compare moves to More) | **today_targets**, today_protein, protein_swaps, recent_scans (protein_claims_tip moves to More) |
| `weight_loss` (Lose Weight) | home, scan, history, protein, profile | home, scan, **diary**, protein, profile | **today_targets**, today_sugar_salt, recent_scans (today_protein merges into today_targets) |
| `eat_better` (Eat Healthy) | home, scan, compare, history, profile | home, scan, compare, **diary**, profile | **today_targets** (shows "Set up" when there are no settings), custom_alerts_setup, claims_tip, recent_scans |
| `health_condition` (Sugar Control, Heart Health) | home, scan, history, family, profile | home, scan, **diary**, family*, profile | unchanged |
| `allergy_diet` (Allergy Safe, My Diet) | home, scan, family, search, profile | unchanged (diary in More) | unchanged |
| `family` | home, scan, family, history, profile | hidden while Family is deferred; `history` → `diary` | unchanged |

\* The Family tab handling while Family is deferred follows the separate Family decision, not this spec.

- The allergy card stays first when any member has an allergen (ADR 0019 rule, unchanged).
- The **reachability test** (every destination reachable in every mode) and the **invariance test** (scan and verdicts identical in every mode) are extended to `diary`.

### 7.11 Meals screen (manage meal slots, Q16)

Reached from Settings, and from "Manage meals" in the Today day menu. Online-only on both clients.

- A list of the active meals in the user's order, with a reorder control (drag handle on Android, drag or up and down buttons on web).
- **Rename** inline. A default meal also offers "Use the original name". A hint under the field: "Names you type are kept exactly as you type them" (they are never translated).
- **Add a meal** (for example pre-workout or evening chai), with an optional usual time. At 6 meals the button is disabled and the limit message shows.
- **Remove** a meal. If it has entries, the dialog says the food already logged stays in the diary, and the API archives it. The last remaining meal cannot be removed.
- An optional usual time per meal, explained as the way we suggest a meal when food is added.
- States: loading; error with retry; limit reached; duplicate name; last meal.
- On Android, a queued offline entry whose meal was removed in the meantime comes back as `meal_slot_archived`. The app then asks the user to pick another meal for that entry.

---

## 8. i18n keys

All keys go into `packages/i18n/messages/en.json` first, then `hi.json` and `mr.json` in the same PR. Hindi and Marathi copy is written for the PR and goes into `NATIVE_REVIEW.md` for the native-speaker review that is already a USER gate. Placeholders use ICU syntax. The English below is our own draft copy, kept neutral and free of medical claims.

**`diary.*`**

| Key | en draft |
|---|---|
| `diary.title` | Diary |
| `diary.today` | Today |
| `diary.slot.breakfast` / `.lunch` / `.snack` / `.dinner` | Breakfast / Lunch / Snacks / Dinner. These are the default names only: `meal_slots.label_key` points here until the user renames a slot. Custom names are user text and never pass through i18n |
| `diary.add` | Add food |
| `diary.add_to_slot` | Add to {slot} |
| `diary.empty_day` | Nothing logged yet. |
| `diary.copy_yesterday` | Copy yesterday |
| `diary.copy_meal` | Copy this meal |
| `diary.copy_day` | Copy a day |
| `diary.copied` | {count, plural, one {# item copied} other {# items copied}} |
| `diary.move` | Move to another meal |
| `diary.mark_partial` | Mark as partly logged |
| `diary.partial_note` | Partly logged days are left out of weekly averages and of learning your energy use. |
| `diary.partial_badge` | Partly logged |
| `diary.remaining` / `diary.consumed` | Remaining / Eaten |
| `diary.left` | {value} left |
| `diary.over` | {value} over |
| `diary.of_target` | {eaten} of {target} |
| `diary.incomplete` | Some items don't show this value, so the real total may be higher. |
| `diary.hidden_numbers` | Numbers are hidden. You can change this in settings. |
| `diary.portion_line` | {quantity} {unit} · {grams} g |
| `diary.quick_add_name` | Quick add |
| `diary.week.title` | This week |
| `diary.week.average` | Average over {days, plural, one {# logged day} other {# logged days}} |
| `diary.week.protein_days` | Protein guide reached on {met} of {days} logged days |
| `diary.disclaimer` | Information, not medical advice. Daily guides are estimates and are pending clinician review. |
| `diary.targets_consent` | To see your daily guide, allow SmartNutri to use your health details. |
| `diary.eye.hide` / `diary.eye.show` | Hide numbers / Show numbers |
| `diary.slots.manage` | Manage meals |
| `diary.slots.add` | Add a meal |
| `diary.slots.rename` | Rename |
| `diary.slots.reset_name` | Use the original name |
| `diary.slots.name_hint` | Names you type are kept exactly as you type them. |
| `diary.slots.time_window` | Usual time (optional) |
| `diary.slots.time_window_hint` | We use this to suggest a meal when you add food. |
| `diary.slots.reorder` | Change order |
| `diary.slots.remove` | Remove this meal |
| `diary.slots.remove_note` | Food you already logged here stays in your diary. |
| `diary.slots.removed_badge` | Removed meal |
| `diary.slots.limit` | You can have up to {max} meals. |
| `diary.slots.last_active` | Keep at least one meal. |
| `diary.slots.duplicate` | You already have a meal with this name. |
| `diary.slots.pick_again` | That meal was removed. Please pick another meal for this item. |

**`targets.*`**

| Key | en draft |
|---|---|
| `targets.title` | Your daily guide |
| `targets.setup_cta` | Set up your daily guide |
| `targets.skip` | Skip, just log food |
| `targets.energy` / `.protein` / `.fat` / `.carbs` | Calories / Protein / Fat / Carbs |
| `targets.kcal_value` | {value} kcal |
| `targets.g_value` | {value} g |
| `targets.how` | How we got this |
| `targets.how.bmr` | Estimated energy at rest: {value} kcal |
| `targets.how.activity` | Activity factor: {value} |
| `targets.how.maintenance` | Estimated energy to stay the same: {value} kcal |
| `targets.how.adjustment` | Change for your goal: {value} kcal a day |
| `targets.how.protein` | Protein: {per_kg} g per kg of your weight ({weight} kg) |
| `targets.how.protein_adjusted` | Protein: {per_kg} g per kg of an adjusted weight ({weight} kg) |
| `targets.how.protein_lean` | Protein: {per_kg} g per kg of lean mass ({weight} kg) |
| `targets.body_fat.label` | Body fat % (optional) |
| `targets.body_fat.hint` | If you know it, for example from a body-composition scale, we base your protein guide on lean mass. If you leave it blank, we use your weight. |
| `targets.body_fat.out_of_range` | Please enter a number between {min} and {max}. |
| `targets.how.sources` | Sources and method |
| `targets.direction.lose` / `.maintain` / `.gain` | Lose weight slowly / Stay the same / Gain slowly |
| `targets.rate_option` | About {kg} kg a week ({pct}% of body weight) |
| `targets.target_weight` | Target weight (optional) |
| `targets.activity.sedentary` / `.light` / `.moderate` / `.very` | (titles) Mostly sitting / Lightly active / Active / Very active |
| `targets.activity.sedentary_hint` … `.very_hint` | Everyday examples for each level |
| `targets.sex_reference.title` | Which estimate should we use? |
| `targets.sex_reference.female` / `.male` / `.average` | Female estimate / Male estimate / In between |
| `targets.pregnancy.question` | Are you pregnant or breastfeeding? |
| `targets.pregnancy.paused` | Daily guides are paused during pregnancy and breastfeeding. Please ask your doctor about your needs. You can still log food. |
| `targets.minor` | Daily guides are for adults. You can still log food. |
| `targets.needs_body_data` | Add {fields} to see a daily guide. |
| `targets.flag.floor_applied` | We don't suggest going below {value} kcal a day. A doctor or dietitian can advise you. |
| `targets.flag.floor_limits_deficit` | Your chosen pace isn't possible within a safe minimum, so this guide is for staying the same. |
| `targets.flag.rate_capped` | We've set the pace to the safest option we offer. |
| `targets.flag.deficit_capped` | We've kept the daily change to a gentle amount. |
| `targets.flag.taper_active` | You're close to your target, so the pace is easing off. |
| `targets.flag.goal_weight_reached` | You're at your target weight. The guide is now for staying the same. |
| `targets.flag.carbs_below_reference` | Carbs are below the usual minimum of 130 g a day. A dietitian can help you adjust. |
| `targets.flag.outside_equation_age_range` | This estimate is less certain at your age. |
| `targets.flag.average_sex_reference` | This guide uses an in-between estimate. |
| `targets.underweight` | We can help you keep a steady weight instead. |
| `targets.target_weight_too_low` | Please choose {min} kg or more. |
| `targets.mode.formula` / `.adaptive` | Estimate from your details / Learn from my log and weight |
| `targets.adaptive.learning` | Learning your energy use: {days} of {need_days} days, {weighins} of {need_weighins} weigh-ins |
| `targets.adaptive.ready` | This week's estimate: {value} kcal (estimate from your details: {formula} kcal) |
| `targets.adaptive.disagrees` | Your log and your weight don't match our estimate. Check whether some days were partly logged. |
| `targets.rapid_loss` | Your weight is going down faster than the pace you chose. A slower pace is usually easier to keep up. |
| `targets.low_intake` | You've logged less than {value} kcal a day for a week. That may be days you didn't log everything. You can mark a day as partly logged. |
| `targets.pending_review` | Pending clinician review |

**`units.*`**: `unit.g`, `unit.ml`, `unit.serving`, `unit.katori`, `unit.cup`, `unit.glass`, `unit.tbsp`, `unit.tsp`, `unit.roti`, `unit.piece`, each with an ICU plural form (for example `{count, plural, one {katori} other {katoris}}`; Hindi and Marathi need native plural forms). Also `unit.grams_hint` "1 {unit} ≈ {grams} g" and `unit.edit_grams` "Edit grams for this unit".

**`foods.*`**: `foods.search_placeholder` "Search foods, dishes or brands", `foods.group.mine` "My foods and recipes", `foods.group.indian` "Indian foods", `foods.group.packaged` "Packaged products", `foods.partial_results` "Some results couldn't load. Try again.", `foods.recent`, `foods.favourites`, `foods.quick_add`, `foods.new_food`, `foods.new_recipe`, `foods.not_on_label` (reuse `protein.not_on_label`), `foods.blank_is_unknown` "Leave blank if you don't know. Blank is never counted as 0.", `foods.values_per.100g` / `.100ml` / `.serving`, `foods.kind.food` / `.custom_food` / `.recipe` / `.product`, `foods.source_credit` "Nutrition data: {source}".

**`recipes.*`**: `recipes.title`, `recipes.ingredients`, `recipes.add_ingredient`, `recipes.servings`, `recipes.cooked_weight`, `recipes.cooked_weight_tip`, `recipes.per_serving`, `recipes.per_100g`, `recipes.incomplete`.

**`weight.*`**: `weight.title` "Weight", `weight.add`, `weight.kg_value`, `weight.tip_same_time`, `weight.confirm_unusual` "This is quite different from your last weigh-in ({previous} kg). Save anyway?", `weight.trend`, `weight.weekly_rate` "About {kg} kg a week ({pct}% of body weight)", `weight.projection` "At this pace you'd reach {target} kg around {date}.", `weight.no_projection.too_few_weigh_ins` / `.moving_away` / `.no_target` / `.too_far`, `weight.outlier` "Left out of the trend", `weight.reminder` "Weekly weigh-in reminder".

**`settings.diary.*`**: `settings.diary.title` "Diary and daily guide", `settings.diary.numbers.title` "Numbers", `.show` "Show numbers", `.hide_energy` "Hide calories", `.hide_all` "Hide all numbers", `.hide_note` "You can still log food. Your guide keeps working in the background.", `settings.diary.view` "Show remaining or eaten", `settings.diary.fat_share` "Share of calories from fat: {pct}%", `settings.diary.reset` "Reset daily guide", `settings.diary.meals` "Meals", `settings.diary.body_fat` "Body fat %". There are no support keys in v1 (Q14).

**`modes.*` and `nav.*`**: `nav.diary` "Diary"; the home card titles `home.card.today_targets` "Today".

**`error.*`**: one key per new code in section 6.7.

**`analytics`**: none (events carry no text).

`check-keys.mjs` already enforces parity across the three files. `tests/unit/test_error_codes_i18n.py` will fail until every new error code has its key.

---

## 9. Tests

TDD for everything in `scoring/`, the API endpoints and the client data layers (AGENTS).

### 9.1 Golden formula tests (shared fixtures)

- `packages/test-fixtures/targets/inputs/<case>.json` holds the profile, settings and date. `packages/test-fixtures/targets/expected/<case>.json` holds `TargetsOut`. They are **generated** by `scripts/generate_target_expectations.py` (`--check` and `--write`, like the verdict fixtures) and hand-checked by the safety reviewer.
- Cases: G1 to G12 from section 4.12, plus:
  - every activity level for one male and one female profile;
  - each floor binding (female, male, average);
  - rate clamp, `max_kg_per_week` clamp, deficit clamp at 25 % and at 1,000 kcal;
  - taper inside the window, at the band and past the target;
  - protein cap at `max_energy_pct`;
  - the three protein branches (Q10), one golden case each: lean mass with body fat (G11, G12), adjusted weight at BMI 30 or more without body fat (G2), and actual weight (G1, G3 to G5, G8);
  - the BMI boundary: 29.9 uses actual weight, 30.0 uses adjusted weight;
  - precedence: a person at BMI 30 or more who gives body fat uses lean mass;
  - body-fat bounds: 2.9 and 70.1 are refused, 3 and 70 are accepted, blank is unknown and never 0;
  - the Devine ideal weight for male, female and `average`, and for a height under 60 inches (no negative offset);
  - the lean-mass factor for every goal, including the hidden `weight_gain` goal (Eat Healthy value, Q15);
  - age 18, 78 and 79;
  - `needs_body_data` for each missing field;
  - minor, pregnancy, and underweight lose.
- API: `tests/unit/scoring/test_targets.py` compares `targets.compute()` with every fixture, plus a hand-written check of G1 to G5, G11 and G12 (one per protein branch), so a fixture regenerated with a wrong formula can't pass by itself.
- Android and web render-test the `expected` responses: the ring values, the hidden-number states and the flag copy keys.
- A YAML guard test: every key in `targets.yaml` is read by code, and every number has a `section_sources` entry. The `PENDING CLINICIAN REVIEW` header must be present.

### 9.2 Unit conversion (property tests, Hypothesis)

`tests/unit/foods/test_units.py`:
- **Linearity:** `to_grams(k·q, u, f) = k · to_grams(q, u, f)` for k > 0 (Decimal-exact).
- **Monotonic:** larger q gives larger grams.
- **Mass units** ignore the food: `to_grams(q, "g", f) = q`.
- **Refusal:** a count unit without a portion returns `None`; a volume unit with no density, no portion and a `g` basis returns `None`. Never `q` itself.
- **Override precedence:** user override, then global portion, then density.
- **Bounds:** the result is always > 0, and the API rejects any result over 5,000 g.
- **Round trip:** a log, then a PATCH with the same quantity and unit, gives an identical snapshot.
- Shared fixture `packages/test-fixtures/units/conversions.json` (food, quantity, unit → grams, kcal). The API asserts its `to_grams` against it. Android and web assert their **preview** against the same file.

### 9.3 Aggregation and the unknown rule

- An unknown nutrient on any entry gives `incomplete`, `remaining = null` and a total that is a lower bound, never 0. A day with nothing logged has null totals.
- Quick add with kcal only leaves protein, fat and carbs unknown and the day incomplete for them.
- Recipe: an ingredient lacking fibre makes the recipe `incomplete_nutrients` contain fibre, and an entry from it is incomplete too.
- Hidden numbers: with `hide_energy`, every energy field in every diary and targets response is null (one parametrised test walks the response schemas).

### 9.4 Adaptive TDEE scenarios (`tests/unit/scoring/test_adaptive.py`)

- Gate: 13 eligible days, 5 weigh-ins, a 13-day span, or no weigh-in last week: each is not ready, with correct progress counts.
- **Gaps:** the same weights with 10 skipped days give the slope from calendar days. A test proves the index-based slope would differ (the NutriTrace bug) and ours does not.
- **Time zone:**
  - Entries at 23:30 and 00:30 IST fall on different local days.
  - An account in `America/New_York` uses its own local days.
  - A time-zone change mid-window does not move earlier entries (their `local_date` is stored).
  - The window ends **yesterday** in local time.
- **Too little data**, all-partial days, an all-unknown-energy day: excluded.
- **Outliers:** a single +4 % weigh-in is kept for display and excluded from the trend and the fit.
- **Caps:** raw estimate 40 % above the formula is clamped to the band; a 600 kcal swing moves at most 150 kcal in a week; 3 clamped weeks set `adaptive_disagrees_with_formula`.
- **Floors still apply:** a low adaptive estimate never yields a target below the floor.
- `rapid_loss` stops further decreases.
- **Determinism:** the same inputs give the same stored row (idempotent weekly job).

### 9.5 API, RLS and consent

- Per endpoint: success, every listed error code, foreign member (404), non-primary member while the flag is off (422), and pagination (cursor stability, limit bounds).
- `client_id` idempotency for entries, custom foods, recipes and weights, including the concurrent race (as in `meals_log`).
- **Frozen day:** change settings today; yesterday's `diary_days` is unchanged and today's is recomputed. A past date with no row returns `none`.
- `meal_logs` back-fill migration test: legacy rows get `local_date`, `meal_slot_id` (pointing at the member's default slot for the old hour band) and `source_kind`; the summary's results are identical before and after (an existing fixture week).
- **RLS** (the existing pattern with two accounts and `SET ROLE authenticated`): every new table is invisible to the other account, `authenticated` cannot INSERT, UPDATE or DELETE, `anon` sees nothing, and global `foods`, `household_units` and `food_portions` rows are readable.
- **Account deletion** erases every new table (`test_delete_me.py`).
- **Consent:**
  - targets and weights refuse without `health_data`, with `details.purposes`;
  - diary day without `health_data` returns entries and `targets_status = consent_required`;
  - delete routes work without `health_data`;
  - the gate runs before the rate limiter.
- **Verdict invariance:** with and without goal settings, targets and weights, `analyze()` returns byte-identical results for every product and member fixture. `scoring/verdict.py` must not import `targets.py` (an import-graph test).
- **Members and body fat:** `body_fat_pct` accepts null and 3–70 and refuses anything else with `body_fat_out_of_range`; reading or writing it needs `health_data`; account deletion erases it; `targets_preview` accepts it unsaved.
- **Meal slots (Q16):**
  - Defaults are created once per member: reading the list twice makes no duplicates.
  - The seventh active slot is refused (`meal_slot_limit`); archived slots do not count; the last active slot cannot be removed.
  - A rename changes the label and no entry; clearing the custom label on a default restores its name; a duplicate name is refused.
  - Reorder rewrites positions and rejects a partial list.
  - **Delete with entries archives:** the entries still appear on their days, marked removed, and a hard delete of a used slot fails at the database (`RESTRICT`). Delete of a never-used slot removes it.
  - A log or copy into an archived or foreign slot is refused.
  - **Default slot from local time:** at 10:59 and 11:00, 15:59 and 16:00, 18:59 and 19:00, across midnight, in two time zones, with a renamed or removed slot, with custom windows, and with overlapping windows.
  - The back-fill maps legacy rows by the same bands, and the summary is identical before and after.
  - Foreign member 404; non-primary member 422 while the flag is off; RLS and account deletion cover `meal_slots`.
- **Custom labels do not leak:** a custom meal label never appears in any analytics event or in any model prompt (a payload test), and comes back byte for byte as stored, with no translation.
- Analytics: the three allow-lists match; no new event carries a value.
- Contract: `just contract` with no drift.

### 9.6 Client tests (Android widget, web component, Playwright e2e)

Widget and component tests, against the shared golden responses:
- Today renders the rings from `remaining` and `progress`; incomplete renders the grey chip; over renders neutral (a colour-token assertion that it is not the danger token); hidden numbers render no digits.
- The portion picker offers only the API's units and its preview matches `units/conversions.json`.
- Onboarding shows the floor, minor, pregnancy and underweight states.
- The week view shows no rating text and no streak.
- Mode layouts: the `layouts.json` tests (reachability and invariance) include `diary`, and `/history` redirects.
- Onboarding shows the optional body-fat field with its explanation; blank saves as unknown; an out-of-range value shows the API's message; the guide shows which protein basis was used.
- The Meals screen: rename, reset name, reorder, add up to six, the limit message at six, the removal note, the last meal blocked. Today shows a removed slot only on days that have entries in it. A custom label renders exactly as typed in en, hi and mr.
- The eye toggle hides every number in one tap, and onboarding preselects "show".

E2E (web Playwright; Android integration test for the same flows):
1. Set up Lose Weight → see the guide → log "2 roti" plus "1 katori dal" from search → the ring updates → edit to 3 roti → delete.
2. Scan a barcode → log a product from OFF → attribution is shown in the diary.
3. Quick add with kcal only → the day shows incomplete macros.
4. Copy yesterday's breakfast to today.
5. Create a recipe → log one serving.
6. Add weigh-ins → see the trend, and no projection with too few points.
7. Hide all numbers → no digits on Today, Week or Progress.
8. Withdraw `health_data` → the diary still works and the guide shows the consent card.
9. Rename Snacks to "Evening chai", add a fifth meal, log into it, remove it, and see the entry still on its day; a seventh meal is refused.
10. Enter body fat 15 % and see the protein guide move to a lean-mass basis; clear it and see it go back.

Android only: queue an entry offline and sync it (existing harness).

---

## 10. Phased delivery plan

Each slice runs **API (`api-builder`) → `just contract` → Android (`flutter-builder`) ∥ web (`web-builder`) → `nutrition-safety-reviewer`**, and is done only when `just test` passes and the shared fixtures pass on all three (CLAUDE.md, AGENTS rule 11). Every slice touches health maths, a fixture or a verdict-adjacent UI, so every slice gets the safety review.

| # | Slice | API | Clients | Ready when | Depends on |
|---|---|---|---|---|---|
| 1 | **Goal setup and formula targets, with every safety rail, hide numbers and the protein basis** | `targets.yaml`; `scoring/targets.py` (lean-mass, adjusted-weight and actual-weight branches); migration 0008 (with `members.body_fat_pct`); `body_fat_pct` on the members schemas; `targets_*`; consent and rate-limit entries; the protein unification (4.13); target fixtures G1–G8, G11, G12; methodology section; ADR 0022 | Onboarding (7.1) with the optional body-fat % and its explanation, a minimal Today ring using the existing `meals_summary` and the new `targets_get`, numbers settings and the eye toggle, the `today_targets` home card | Golden fixtures pass on all three; the clinician sheet lists the lean-mass factors, the IBW formula, the adjusted-weight threshold and the 3–70 range | Decisions Q2, Q7, Q8, Q10, Q11, Q12, Q13 (applied) |
| 2 | **Diary day: default meal slots, local dates, edit, copy, quick add, partial days** | Migration 0009 (`meal_slots` with the four defaults for every member, and `meal_logs.meal_slot_id`); `meal_slots_list` (read-only, with the suggested slot); `meals_log` v2 (product, OFF, quick); `meals_update`, `meals_copy`; `diary_day_get`, `diary_week_get`, `diary_day_status_put`, `diary_recents_list`; analytics events | Full Today (7.2), the Add-food sheet with recents, barcode, label and quick add, week view; the `history` → `diary` destination and redirect; layouts.json | Back-fill test green; the summary is identical on the fixture week; default-slot choice from local time tested | 1 |
| 2b | **Meal slot management: rename, add, reorder, archive (up to 6)** | `meal_slots_create`, `meal_slots_rename`, `meal_slots_reorder`, `meal_slots_archive`; the limit of 6; archive instead of delete; new error codes; tests in 9.5 | Meals screen (7.11); entries move between slots; removed-slot display; i18n keys | Slot tests green on all three; custom labels proven absent from analytics | 2 |
| 3 | **Household units and Indian foods** | Migration 0010; `household_units.yaml`; the generic-food seed (USDA FoodData Central ingredients plus documented Indian-dish recipes, Q1; the NIN request goes out in parallel, and IFCT replaces them only after written permission); `to_grams`; `foods_search`, `foods_get`, `foods_units_list`, `foods_portion_*`; unit fixtures | Portion picker (7.4); search groups | Property tests and conversion fixtures pass on all three; the unit seed is dietitian-checked before launch (Q6) | 2 (Q1 and Q6 applied) |
| 4 | **Custom foods and recipes** | Migration 0011; `custom_foods_*`, `recipes_*`; barcode lookup checks custom foods first for logging | Custom food form, recipe builder | | 3 |
| 5 | **Favourites** | Migration 0012; `favourites_*` | Favourites segment, the star in the picker | | 2 |
| 6 | **Weight log, honest trend, taper** | Migration 0013 (with back-fill); `weights_*`; trend and projection; taper and the trend weight in targets | Weight log, Progress (7.5, without adaptive) | | 1, 2 |
| 7 | **Adaptive TDEE (behind `ADAPTIVE_TDEE_ENABLED`, default off)** | Migration 0014; weekly job (`app/jobs/adaptive_energy.py`, run by the existing scheduler pattern); `targets_estimate_get`; `energy_mode = adaptive`; fixtures G9, G10 and the scenario suite | Learning and ready cards, mode switch in settings | Scenario suite green; clinician sign-off on the `adaptive.*` keys and about 4 weeks of tester data before the flag is turned on | 6 (Q3 applied: the flag stays off) |

Once slice 2 is merged, slices 2b, 3, 5 and 6 can run in parallel (slice 6 also needs slice 1), and slice 4 follows slice 3.

Each slice updates `docs/FEATURE_PARITY.md`. The diary becomes a new row, **F21 Food diary and daily guide**, with the same USER gates as the others.

---

## 11. Decisions (resolved)

The user answered all 16 questions on 2026-11-07. The answers are binding and are recorded in `DECISIONS.md`; the options that were not chosen are not repeated here. The last column shows where each decision lands in this spec.

| Q | Topic | Decision | Applied in |
|---|---|---|---|
| Q1 | Indian food data | Write to ICMR-NIN for permission to use IFCT 2017. Until then, USDA FoodData Central ingredients plus Indian dishes built as documented recipes. Switch to IFCT once approved | 5.7, slice 3, R6 |
| Q2 | Energy equation | Mifflin-St Jeor (1990) × an activity factor | 4.2, 4.3 |
| Q3 | Adaptive TDEE | v1 uses the formula. Adaptive is slice 7, behind a flag that stays off until clinician sign-off and about 4 weeks of tester data | 4.10, slice 7 |
| Q4 | Weight source | Manual weigh-ins only, the same on Android and web. Health Connect in v2 | 5.4, 6.5, 7.8 |
| Q5 | Exercise calories | Ignored. The activity level already covers typical exercise, so there is no add-back | 3.2, 4.3 |
| Q6 | Household-unit grams | Our own reference set (katori 150 ml, cup 200 ml, glass 250 ml, tbsp 15 ml, tsp 5 ml, plus per-food grams), checked by a dietitian. Grams always shown, editable per food | 5.6, 7.4, slice 3 |
| Q7 | Hide-numbers default | Numbers shown by default. Onboarding offers show all, hide calories or hide all, and Today has a one-tap eye toggle | 5.2, 6.2, 7.1, 7.2 |
| Q8 | Protein g/kg per goal | Build Muscle 1.6, Lose Weight 1.2, Eat Healthy 0.83, all pending clinician review | 4.7, 4.13 |
| Q9 | Family deferral | Solo only. Stored per member with "self" as the only member; the API rejects others (`DIARY_FAMILY_ENABLED=false`); no family UI | 1.4, 6 |
| Q10 | Protein reference weight | Lean mass if body fat is known (optional input, 3–70 %), else adjusted body weight at BMI 30 or more (ideal weight + 25 % of the excess), else actual weight. Lean-mass factors and the IBW formula are pending clinician review. The old capped-reference-weight rule is gone | 4.7.1, 5.1, 6.1, 7.1, 9.1, slice 1 |
| Q11 | Sex "other" or not given | Ask which estimate to use. In-between (the mean of the two constants) is preselected, and the higher calorie floor applies | 4.2, 4.6, 7.1 |
| Q12 | Age limits | Targets from 18, none under 18, and a "less certain" note over 78 | 4.2, 4.8 |
| Q13 | Consent for targets | `health_data` gates targets and the weight log. Withdrawing it stops the targets and keeps stored data. Food logging works on `terms`. Recorded in ADR 0022 | 6.6, slice 1 |
| Q14 | Support signpost | None for now. Only the safety limits (calorie floor, maximum loss rate) and neutral cards. To be revisited before launch | 4.11, 7.9, R20 |
| Q15 | Existing `weight_gain` goal | Keeps working for existing data (direction gain, Eat Healthy protein) but is not offered in new UI. A "Gain Weight" chip can come later | 1.5, 4.14, 5.2 |
| Q16 | Meal slots | Renamable slots, up to 6. Defaults Breakfast, Lunch, Snacks and Dinner, picked from the time of day. The user can rename them or add more, for example pre-workout or evening chai | 5.1, 5.12, 6.2.1, 7.11, slices 2 and 2b |

---

## 12. Risks and mitigations

| # | Kind | Risk | Mitigation |
|---|---|---|---|
| R1 | Clinical | A formula estimate can be off by several hundred kcal for an individual | Shown as a guide with "how we got this"; rounded to 10 kcal; floors and caps; adaptive (later) learns from real data; every constant pending clinician sign-off |
| R2 | Clinical | Encouraging restriction in someone with, or at risk of, disordered eating | Floors, a maximum rate and deficit, a BMI 18.5 target limit, no deficit under 18 or in pregnancy, neutral colours and copy, no streaks or day ratings, server-enforced hide numbers, the rapid-loss and low-intake cards; safety review of all copy. No support signpost for now (R20) |
| R3 | Clinical | High protein for people with kidney disease (no kidney field) | The existing `protein.kidney_note` copy on every protein guide; the default stays at ICMR-NIN's 1.6 ceiling; lean mass or an adjusted weight, never raw weight, is the reference at high body weight (4.7.1); kidney disease is out of scope (PRODUCT.md) |
| R4 | Clinical | Users read targets as medical advice, or a "programme" | "Information, not medical advice" on every guide; no "treat" or "manage" wording; targets never alter verdicts (import-graph and invariance tests); the methodology page explains it |
| R5 | Clinical | Adaptive TDEE lowers targets because of under-logging | Day eligibility rules, partial-day marking, the band around the formula, the weekly step limit, floors still apply, no decrease while `rapid_loss`, the disagreement flag; off until sign-off |
| R6 | Legal | IFCT or NIN data used without permission | Q1 decided: the written request goes to NIN now; launch data is USDA FoodData Central plus documented recipes; every food row stores its `licence`; IFCT rows are added only after written permission; the USDA licence is re-verified before use |
| R7 | Legal | OFF ODbL attribution lost inside diaries and recipes | `attribution` kept on entries and recipe ingredients; one attribution component on every diary surface (ADR 0017); only grams-per-unit that we derive ourselves is stored, never copied OFF data |
| R8 | Legal | DPDP: diaries and weights are health-related personal data | Body data gated by `health_data`; the diary on `terms` follows ADR 0017's pending lawyer review; erasure through account deletion covers every new table; no analytics; India region |
| R9 | Legal | Copying from GPL, AGPL or MPL apps, or a FitBook licence misunderstanding | Clean-room spec in our own words; no code or strings copied; FitBook's "Flexify" holder flagged before any reuse |
| R10 | Data quality | Household units vary widely (a katori can be 100 to 200 ml) | Grams always shown next to the unit; per-food values; user overrides; a dietitian-checked reference set (Q6) |
| R11 | Data quality | Crowd-sourced OFF values are wrong or incomplete | The existing sanitiser drops implausible values; unknown stays unknown and marks totals incomplete; Report a problem (F14) |
| R12 | Data quality | Volume converted with water density for oil, flour or rice | `to_grams` never assumes ml = g; volume needs a portion row, a density or an ml basis |
| R13 | Data quality | Time-zone and midnight errors | `local_date` stored at write time from the account's time zone; tests at 23:30 and 00:30 and across zones |
| R14 | UX | Logging Indian home food is slow, so people stop | Recents per slot, favourites, copy meal or day, quick add, fractions, Indian dish search; analytics only on the method used |
| R15 | UX | Two protein numbers (summary and diary) confuse users | One source: the frozen day's protein feeds both (4.13) |
| R16 | UX | Replacing History with Diary breaks muscle memory and links | The redirect from `/history`; the same tab slot; the existing summaries kept inside Diary |
| R17 | Engineering | Changing `meal_logs` breaks Android's offline queue or the existing clients | Additive columns with back-fills; `meals_log` stays backward-compatible (grams or servings still accepted); `grams` nullable only for quick add; the contract is regenerated in the same PR; migration tests |
| R18 | Engineering | Client preview and API results drift | The shared `units/conversions.json` fixture on all three; the API value is authoritative on save |
| R19 | Clinical | Pregnancy or breastfeeding not disclosed | The question in onboarding; "prefer not to say" also pauses guides; the copy points to a doctor |
| R20 | Clinical | **Deferred (Q14):** there is no support signpost in v1, so someone struggling with food or weight finds no contact in the app | The safety limits (calorie floors, maximum loss rate, BMI limits), neutral cards, no streaks and hide numbers all stay. **Revisit before launch:** decide with the user and the clinician whether to add a verified support contact. It is a launch-gate item, tracked in CONTEXT.md open items |
| R21 | Clinical | A self-entered body-fat % is wrong or stale (scales vary, and the value drifts as weight changes), so protein is too high or too low | Optional; range 3–70; `max_g_per_kg` and `max_energy_pct` cap every branch; the explanation shows the basis used; the user can update or clear it; the factors and range are [clinician] and pending review |
| R22 | Clinical | The IBW formula (Devine) uses height only, and BMI 30 may be a high threshold for Asian Indian adults | Both the formula and `adjusted_weight.min_bmi` are YAML keys marked [clinician]; the BMI-based alternative is already named; golden cases pin the current choice |
| R23 | Privacy | Custom meal names are free user text and could hold personal details | Stored as typed, 30-character limit, owner-only RLS, never translated, never in analytics, logs or prompts, erased with the account (5.12, 6.8) |
| R24 | Data integrity | Deleting a slot could orphan or erase diary history | Entries reference a slot id with `ON DELETE RESTRICT`; delete means archive when there are entries; archived slots still show on their days; tests in 9.5 |

---

## 13. Sources

**Research files (this folder):** `DECISIONS.md`, `SHORTLIST.md`, `RESEARCH_LOG.md`, `apps/opennutritracker.md`, `apps/nutritrace.md`, `apps/kcal.md`, `apps/fitbook.md`, `apps/closed-apps-public.md`.

**Repo:** `AGENTS.md`, `CONTEXT.md`, `docs/ARCHITECTURE.md`, `docs/PRODUCT.md`, `docs/FEATURE_PARITY.md`, ADR 0017, 0018, 0019, 0020, 0021, `apps/api/app/features/meals/{models,schemas,service,summary,router}.py`, `apps/api/app/scoring/daily_limits.py`, `apps/api/app/scoring/data/thresholds.yaml`, `apps/api/app/core/{consent,ratelimit,errors,time}.py`, `apps/api/app/features/members/{models,schemas}.py`, `apps/api/app/features/me/service.py` (`ACCOUNT_OWNED_TABLES`), `apps/api/alembic/versions/0001_baseline.py`, `0003_plan6_meal_logs_off.py`, `0006_plan9_user_types.py`, `packages/test-fixtures/modes/layouts.json`, `packages/i18n/messages/en.json`, `apps/web/src/lib/analytics.ts`, and the Android and web meals, protein and history features.

**External** (read 2026-11-07 unless noted):
- Mifflin MD, St Jeor ST, et al. Am J Clin Nutr 1990;51(2):241–247. doi:10.1093/ajcn/51.2.241, PMID 2305711. Abstract read via Europe PMC REST (`https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:2305711%20AND%20SRC:MED&resultType=core&format=json`). PubMed itself needed cookies. The constants were cross-checked against secondary sources (e.g. https://www.guidelinecentral.com/calculator/479/, https://en.wikipedia.org/wiki/Harris%E2%80%93Benedict_equation). [verify: full text]
- CDC, "Losing Weight": "about 1 to 2 pounds a week". https://www.cdc.gov/healthy-weight-growth/losing-weight/index.html
- Jäger R, et al. ISSN position stand: protein and exercise. J Int Soc Sports Nutr 2017;14:20. doi:10.1186/s12970-017-0177-8, PMID 28642676 (via `closed-apps-public.md`; abstract only).
- Morton RW, et al. Br J Sports Med 2018;52(6):376–384. PMID 28698222 (via `closed-apps-public.md`).
- ICMR-NIN Dietary Guidelines for Indians 2024: protein above about 1.6 g/kg/day adds no further resistance-training gains; protein supplements discouraged; 0.83 g/kg recommendation. **Via news coverage only** (e.g. https://thesouthfirst.com/news/icmr-releases-dietary-guidelines-for-indians-after-13-years-says-no-to-protein-supplements, https://theprint.in/india/icmr-calls-for-avoiding-protein-supplements-issues-dietary-guidelines-for-indians/2077477, https://telanganatoday.com/why-do-icmr-nins-new-dietary-guidelines-advise-against-protein-supplements). [verify against the NIN PDF]
- WHO/FAO/UNU 2007, TRS 935, protein safe level 0.83 g/kg (already cited in `thresholds.yaml`).
- Institute of Medicine 2005, Dietary Reference Intakes for Energy, Carbohydrate, Fiber, Fat, Fatty Acids, Cholesterol, Protein, and Amino Acids. doi:10.17226/10490 (AMDR fat 20–35 %, carbohydrate RDA 130 g) [verify page numbers].
- Hall KD. What is the required energy deficit per unit weight loss? Int J Obes 2008 [unverified: not read].
- MacroFactor help and method pages (rate as % of body weight, damping, data sufficiency), via `closed-apps-public.md` §1.
- Calorie floors of 1,200 and 1,500 kcal: widely quoted, original source not confirmed [unverified].
- Activity factors 1.2 to 1.725: widely used, primary source not found [unverified].
- Devine BJ. Gentamicin therapy. Drug Intell Clin Pharm 1974;8:650–655 (ideal body weight) [unverified: original not read]. Adjusted body weight with a 25 % excess fraction: common clinical practice [unverified]. Both are on the clinician sheet (Q10).
- Lean-mass-based protein in a competitor (MacroFactor): from the competitor check recorded in `DECISIONS.md` (Q10), public pages only [unverified].
- USDA FoodData Central licence (CC0, public domain) [verify before use].
