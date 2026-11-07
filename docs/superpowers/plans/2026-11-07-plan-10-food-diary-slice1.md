# Plan 10: Food Diary Slice 1: Goal Setup, Formula Targets, Safety Rails, Hide Numbers and the Protein Basis

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** An adult account holder sets up a daily guide (body data with an optional body-fat %, activity, goal direction and pace, pregnancy question, how to see numbers) and sees today's calories, protein, fat and carbs, computed only by the API, with every safety rail, a one-tap eye toggle that hides numbers, and the protein basis (lean mass, adjusted weight or actual weight). This ships on the API, Android and web.

**Architecture:**
- **API first.** A pure engine `app/scoring/targets.py` reads only `app/scoring/data/targets.yaml` (all PENDING CLINICIAN REVIEW). A new feature `app/features/targets/` stores one `diary_goal_settings` row per member (migration `0008`) and serves six routes gated by `health_data` (ADR 0022). `members.body_fat_pct` is a new health field. The protein g/kg moves from `thresholds.yaml` to `targets.yaml`, and `meals_summary` takes its protein target from the engine when the member has settings, and redacts hidden numbers.
- Then the shared step: golden target fixtures (generated, hand-checked), `layouts.json` home cards, i18n, `just contract`.
- **Clients** (Android ∥ web), in two paired tasks: (1) data layer, guide setup and the "Diary and daily guide" settings; (2) the `today_targets` Home card, the eye toggle, and hidden-number and protein-basis rendering on the existing summary cards and History.
- Targets are information, never verdicts: `analyze()` and every verdict module never import `targets.py`.

**Tech Stack:** as Plan 9. API: Python 3.13, FastAPI, SQLAlchemy 2 async + Alembic, pytest, `decimal`. Android: Flutter, Riverpod 3, go_router, the generated `smartnutri_api`. Web: Next.js 16, TanStack Query, next-intl, `@smartnutri/api-client`. Tests: pytest, flutter_test, Vitest, Playwright.

**Spec:** `docs/research/food-diary/FEATURE_SPEC.md` (binding; slice 1 is row 1 of section 10). Binding answers: `docs/research/food-diary/DECISIONS.md` (Q2, Q7, Q8, Q9, Q10, Q11, Q12, Q13, Q14, Q15 apply here). Executors read the spec sections each task cites.

## Rulings made while writing this plan

Existing names and shapes win over the spec where they already exist. Each ruling is also cited inline where it applies.

- **D1 (scope): `diary_days` and `accounts.timezone` move to slice 2.** Slice 1 shows only today's target, computed live; nothing reads a past day. `GET /v1/targets` with a past date returns `status: "none"` (the spec's rule for a past day with no row, 5.3), a future date is `422 date_in_future`, and "today" is the existing `today_ist()`. The migration is therefore `0008_diary_goal_settings` (spec 5.11 name `0008_diary_goal_settings_targets`), and slice 2 adds `diary_days` and `accounts.timezone` in its own migration.
- **D2 (age): the engine's age is the existing `youngest_age(birth_year, today)`** (Plan 3 R19, `members/service.py`), not the spec's `target_year − birth_year`. One age rule everywhere; it is the protective one for the under-18 gate. Engine inputs carry `age` directly.
- **D3 (body fat on PATCH): `null` means "unchanged", and `clear_body_fat_pct: true` clears it.** The generated Dart client sends every unset field as `null` (`MemberPatch` docstring), so the spec's "null clears it" would wipe body fat on every unrelated member edit from Android. Reads are not withheld: the existing members API returns health fields regardless of consent and gates only writes (spec 6.1 says "withheld"; existing behaviour wins).
- **D4 (eye toggle): a new terms-only route `PUT /v1/targets/display` (`targets_display_put`)** changes only `numbers_display` and `summary_view`. Hiding numbers must never fail because stored settings stopped validating or because `health_data` was withdrawn.
- **D5 (TargetsOut additions):** `rate_options` (spec 7.1 says rate chips show kg/week "as computed by `targets_preview`", but the spec's `TargetsOut` has no field for them) and `unusual_fields` (the plausible-range confirmation, spec A14/7.1). `rate` and `rate_options` are unsigned magnitudes; `direction` carries the sign.
- **D6 (i18n): `targets.how` becomes `targets.how.title`**, because the spec also defines `targets.how.bmr` etc. and a JSON key can't be both a string and an object.
- **D7 (YAML): slice-1 `targets.yaml` holds only the keys slice-1 code reads**, so the guard test "every key is read" holds. `adaptive`, `trend`, `projection`, `safety` and `plausible.weight_change_kg_per_day` arrive with slices 6–7. The skeleton (4.14) wins over table 4.4: there is no `goal_rates.lose.max_pct_bw_per_week` (the options maximum is the cap). `protein.ibw.bmi_based` is not added until the clinician picks it; the engine raises on an unknown `protein.ibw.formula`.
- **D8 (settings that stopped validating):** `GET` can't answer 422. A stored `lose` with a current BMI below 18.5 is computed as maintenance with a new flag `underweight_maintenance` (copy = `targets.underweight`). A stored target weight below BMI 18.5 is raised to the lowest allowed weight before the taper.
- **D9 (floors):** when maintenance is below the floor, only `floor_limits_deficit` is set (not also `floor_applied`, whose copy "we don't suggest going below X" would be false there).
- **D10 (protein unification without `diary_days`):** `meals_summary` takes the protein target from today's engine result when the member has settings and an active `health_data` consent; a non-ready status gives no target and reports the status. Otherwise the legacy `daily_limits_for` rule applies, now reading g/kg from `targets.yaml` (so `weight_loss` becomes 1.2, Q8).
- **D11 (hidden numbers):** the API redacts `TargetsOut` and `meals_summary` (slice 1 has no diary responses; the summary is where eaten numbers show). `hide_energy` nulls every energy number; `hide_all` also nulls macros, sugar and salt totals, the protein target, `protein_left_g` and every explanation number. The pace (`rate`, `rate_options`) stays visible under `hide_all`, because the user has to choose a pace. Bands stay.
- **D12 (display rounding):** explanation kcal values are whole kcal, half-up; weights 1 dp; `rate` and `rate_options` 2 dp.
- **D13 (missing fields):** `missing_fields` uses member field names (`birth_year`, `sex`, `height_cm`, `weight_kg`). `sex = null` with no `sex_reference` is missing `sex`; `sex = "other"` with no reference uses `average` (G8).
- **D14 (home cards):** `today_targets` joins the gym, weight_loss and eat_better Home cards as spec 7.10 proposes; the **tabs don't change** (the `diary` destination is slice 2). Gym keeps `protein_claims_tip` (More holds destinations, not cards).
- **D15 (pregnancy):** the column stays boolean (spec 5.2). "Prefer not to say" is sent as `true`, as it pauses guides too.
- **D16 (consent keys):** `REQUIRED["targets"] = ("terms", "health_data")` and `REQUIRED["targets_prefs"] = ("terms",)` (delete and display).
- **D17 (Android e2e):** `apps/app` has no `integration_test` harness; the spec's Android integration flows are covered by widget flow tests. Web e2e runs in Playwright against `e2e/stub-api.mjs`.
- **D18 (G5):** slice 1 has no trend weight (slice 6), so the G5 fixture feeds the trend value (76.2 kg) as the body weight; the taper uses that weight.
- **D19 (error code):** new `goal_settings_not_found` (404) for `targets_display_put` without settings.
- **D20 (no rings yet):** spec slice 1 names "a minimal Today ring". A ring fill or an "X over" would be client arithmetic; slice 2's `remaining` and `progress` from the API drive rings. Slice 1's Today card shows rows: the API target and, for energy and protein, "{eaten} of {target}" from `meals_summary`.

## Global Constraints

Health-app rules (root `AGENTS.md`, non-negotiable):
1. **The rules engine decides; targets are information.** Clients never compute a target, a rate in kg, a remaining value or a flag. `app/scoring/verdict.py` and the verdict modules never import `targets.py`; `analyze` responses are byte-identical with and without goal settings.
2. **Never invent nutrition data.** Blank body fat is unknown, never 0. A summary total the user hid is `null` with `numbers_hidden`, not 0.
3. **Unknown is not safe.** `unknown` and incomplete are the grey "not enough data" style, never green. Targets never use verdict colours.
4. **Thresholds live in data.** Every number is in `targets.yaml`, first line `# PENDING CLINICIAN REVIEW`; changes need tests, regenerated fixtures and a PR note.
5. **Secrets stay server-side.** Nothing new is public config.
6. **No health data in analytics.** No new event in slice 1. Never send a target, weight, body fat, goal, direction, flag, pregnancy answer or the hidden-numbers state.
7. **No medical claims.** "Information, not medical advice" and "Pending clinician review" wherever a target number appears. Never "you need", "treat", "manage", "cure".
8. **Strings only in `packages/i18n`** (en, hi, mr); hi/mr machine drafts listed in `packages/i18n/NATIVE_REVIEW.md` under "Plan 10".
9. **Never hand-edit generated code.** `just` is not installed for agents: run the justfile recipe lines by hand (`.superpowers/sdd/RULES-FOR-AGENTS.md`).
10. **Feature parity.** Done only when API, Android and web ship it and the target fixtures pass on all three.

Slice-1 rules (spec sections in brackets):
- **Solo only (Q9).** Settings exist only for the primary member. Another account's member is `404 member_not_found`; a non-primary member is `422 diary_member_not_enabled` while `DIARY_FAMILY_ENABLED=false` (new setting, default false). [1.4, 6]
- **Safety rails ship with the first number** [1.1, 4.4–4.8]: floors 1,200 / 1,500 / 1,500 kcal and never below BMR; at most 1.0 kg/week, 25 % of maintenance and 1,000 kcal/day of deficit; no target under BMI 18.5; no targets under 18 or in pregnancy or breastfeeding; "less certain" over 78.
- **Neutral tone** [7]: progress uses the brand colour; over a target uses a neutral token, never the danger token; no streaks, ratings or celebration. **No support link or number anywhere (Q14).**
- **Hidden numbers mean no digits** for the hidden values on every slice-1 surface, including flag copy (`targets.flag.floor_applied_hidden`).
- **Contract:** `operation_id` = `<feature>_<action>`; errors use `ErrorEnvelope` and an `error.<code>` key in en, hi and mr; write routes depend on `current_account_row`; the consent gate runs before `limit()`.
- **Rounding** is half-up with `Decimal` everywhere in the engine; floats never decide a boundary.
- **Commits:** Conventional Commits with a scope, ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; `gitleaks protect --staged --no-banner` before each commit; never push.

## Review Focus

1. **Hidden numbers leaking.** With `hide_all`, a number still shows through flag copy (the floor value), the "How we got this" panel, the protein card, History or a rate chip label. Expected: no digit for energy or macros anywhere. Owned by Task 4 (`test_hidden_numbers_redact_every_number`), Task 5 (`test_summary_hide_all`), Tasks 8/10 (`eye toggle hides every number in one tap`).
2. **Settings that stop validating.** The user saved "lose", then edits weight below BMI 18.5, turns 17 by a birth-year correction, or answers pregnant. Expected: `GET` never 422s; it returns maintenance with `underweight_maintenance`, `not_available_minor` or `paused_pregnancy`. Owned by Task 1 (`test_underweight_at_read_becomes_maintenance`) and Task 4 (`test_targets_get_after_weight_drop_is_maintenance`).
3. **Exact boundaries.** BMI exactly 30.0 (160 cm, 76.8 kg), body fat exactly 3 and 70, and .5 roundings (G5 carbs 272.5 → 273). Expected: adjusted weight at 30.0, accepted at 3 and 70, half-up. Owned by Task 1 (`test_bmi_boundary_is_exact`, `test_half_up_rounding`).
4. **Body fat wiped by an unrelated edit.** Android renames a family member or saves the pre-fill review; the Dart client sends `body_fat_pct: null`. Expected: body fat unchanged. Owned by Task 3 (`test_null_body_fat_on_patch_leaves_value`) and Task 7 (`member save keeps body fat`).
5. **Consent redirect loop.** Without `health_data`, Home calls `targets_get`, gets 403, and the global consent handler pulls the user to a consent screen on every Home load. Expected: an inline card with a grant button; the rest of Home works. Owned by Task 8 (`consent_required shows the consent card, not a redirect`) and Task 10 (same name).

## Task overview: platform, order, parallelism

| Task | Platform | Depends on | Parallel group |
|---|---|---|---|
| 1. Targets YAML and pure engine | API (scoring) | — | **A** (alone) |
| 2. Protein unification, methodology, clinician sheet | API (scoring) | 1 | **B**: 2 ∥ 3 |
| 3. Migration 0008, settings model, `members.body_fat_pct` | API (db, members) | 1 | **B**: 2 ∥ 3 |
| 4. Targets routes, consent, rate limits, ADR 0022 | API | 1, 3 | — |
| 5. `meals_summary`: protein from targets, hidden numbers | API | 2, 4 | — |
| 6. Golden fixtures, home cards, i18n, contract | API + shared | 4, 5 | — (safety gate on fixtures) |
| 7. Data layer, guide setup, guide settings | Android | 6 | **C**: 7 ∥ 9 |
| 8. Today targets card, eye toggle, hidden and basis rendering | Android | 7 | **D**: 8 ∥ 10 |
| 9. Data layer, guide setup, guide settings | Web | 6 | **C**: 7 ∥ 9 |
| 10. Today targets card, eye toggle, hidden and basis rendering, e2e | Web | 9 | **D**: 8 ∥ 10 |
| 11. Slice gate: safety review, parity, docs | All | 1–10 | — |

Agents: Tasks 1–6 `api-builder` (sonnet); 7–8 `flutter-builder`; 9–10 `web-builder`; Task 11 `nutrition-safety-reviewer` (opus). Android and web files are disjoint. Tasks 2 and 3 touch disjoint files (2: `thresholds.yaml`, `daily_limits.py`, methodology, sheet; 3: alembic, models, members, db tests).

## File Map

```
apps/api/
  app/scoring/data/targets.yaml                              # T1 (new)
  app/scoring/{config,targets,__init__}.py                   # T1 (targets.py new)
  app/scoring/data/thresholds.yaml, app/scoring/{daily_limits,methodology}.py   # T2
  ../../scripts/clinician_review_sheet.py, ../../docs/launch/clinician-review.md # T2
  alembic/versions/0008_diary_goal_settings.py               # T3
  app/features/targets/{__init__,models}.py                  # T3
  app/features/members/{models,schemas,service}.py           # T3
  app/features/me/service.py (ACCOUNT_OWNED_TABLES)          # T3
  app/features/targets/{schemas,mapping,service,router}.py   # T4
  app/core/{consent,ratelimit,config}.py, app/main.py        # T4
  app/features/meals/{schemas,summary,service,router}.py     # T5
  scripts/generate_target_expectations.py                    # T6
  tests/unit/scoring/{test_targets,test_targets_yaml}.py     # T1
  tests/api/members/test_body_fat.py, tests/db/*             # T3
  tests/api/targets/*                                        # T4
  tests/api/meals/test_summary_targets.py                    # T5
  tests/fixtures/test_target_fixtures.py                     # T6
packages/test-fixtures/targets/{inputs,expected}/*.json, targets/direction_defaults.json   # T6
packages/test-fixtures/modes/layouts.json, meals/expected/*, responses/methodology.json     # T2, T6
packages/i18n/messages/{en,hi,mr}.json, packages/i18n/NATIVE_REVIEW.md                     # T6
packages/api-contract/**                                     # T6 (generated)
docs/adr/0022-daily-targets-health-data-gate.md              # T4
apps/app/lib/features/targets/**, test/features/targets/**   # T7, T8
apps/web/src/features/targets/**, src/app/[locale]/(app)/{guide/setup,profile/guide}/page.tsx, tests/features/targets/**, e2e/guide.spec.ts   # T9, T10
docs/FEATURE_PARITY.md (F21), CONTEXT.md                     # T11
```

---

### Task 1 (API, scoring): Targets YAML and the pure engine

Use the `scoring-rule` skill. Spec: 4.1–4.9, 4.12, 4.14, 9.1.

**Files:**
- Create: `apps/api/app/scoring/data/targets.yaml`, `apps/api/app/scoring/targets.py`, `apps/api/tests/unit/scoring/test_targets.py`, `apps/api/tests/unit/scoring/test_targets_yaml.py`
- Modify: `apps/api/app/scoring/config.py` (`ScoringConfig.targets`), `apps/api/app/scoring/__init__.py` (no re-export of `targets` from the package root, so verdict code can't reach it by accident)

**Interfaces:**
- Consumes: `load_config()` / `ScoringConfig` (`app/scoring/config.py`).
- Produces (all in `app/scoring/targets.py`; `Decimal` in, `Decimal`/`int` out):

```python
Direction = Literal["lose", "maintain", "gain"]
ActivityLevel = Literal["sedentary", "light", "moderate", "very"]
SexReference = Literal["male", "female", "average"]
TargetsStatus = Literal["ready", "needs_body_data", "not_available_minor", "paused_pregnancy"]
ProteinBasis = Literal["lean_mass", "adjusted_weight", "actual_weight"]
# Emitted in this order (deterministic fixtures):
FLAG_ORDER: tuple[str, ...] = ("underweight_maintenance", "rate_capped", "deficit_capped",
    "taper_active", "goal_weight_reached", "floor_applied", "floor_limits_deficit",
    "protein_capped", "carbs_below_reference", "average_sex_reference",
    "outside_equation_age_range")

@dataclass(frozen=True, slots=True)
class BodyData:  # age = youngest_age(...) (Ruling D2)
    age: int | None; sex: Literal["female", "male", "other"] | None
    height_cm: Decimal | None; weight_kg: Decimal | None
    body_fat_pct: Decimal | None; goal: str | None

@dataclass(frozen=True, slots=True)
class GoalSettings:
    direction: Direction; activity_level: ActivityLevel
    rate_pct_bw_per_week: Decimal | None = None      # None = YAML default for the direction
    target_weight_kg: Decimal | None = None
    sex_reference: SexReference | None = None
    pregnant_or_breastfeeding: bool = False
    fat_pct_energy: Decimal | None = None             # None = macros.fat_pct_energy.default

@dataclass(frozen=True, slots=True)
class RateOption:  # unsigned (Ruling D5), unrounded
    pct_bw_per_week: Decimal; kg_per_week: Decimal

@dataclass(frozen=True, slots=True)
class Explanation:  # unrounded; display rounding is the API's (Task 4)
    bmr_kcal: Decimal; activity_factor: Decimal; maintenance_kcal: Decimal
    adjustment_kcal: Decimal; weight_kg_used: Decimal; protein_basis: ProteinBasis
    protein_g_per_kg: Decimal; protein_reference_weight_kg: Decimal
    body_fat_pct_used: Decimal | None; ibw_kg: Decimal | None
    floor_kcal: Decimal | None   # lose only: max(floor_by_sex, BMR × min_bmr_multiple)

@dataclass(frozen=True, slots=True)
class TargetResult:
    status: TargetsStatus
    missing_fields: tuple[str, ...] = ()
    energy_kcal: int | None = None
    protein_g: int | None = None; fat_g: int | None = None; carbs_g: int | None = None
    direction: Direction | None = None
    rate: RateOption | None = None                    # after clamp and taper; None for maintain
    rate_options: tuple[RateOption, ...] = ()         # every YAML option for the direction at W
    explanation: Explanation | None = None
    flags: tuple[str, ...] = ()

class SettingsRuleError(Exception):
    def __init__(self, code: str, details: dict[str, Any] | None = None) -> None: ...

def compute(body: BodyData, settings: GoalSettings, cfg: ScoringConfig | None = None) -> TargetResult
def check_settings(body: BodyData, settings: GoalSettings, cfg: ScoringConfig | None = None) -> None
def check_body_fat(value: Decimal | None, cfg: ScoringConfig | None = None) -> None
def unusual_fields(body: BodyData, cfg: ScoringConfig | None = None) -> tuple[str, ...]
def protein_g_per_kg(goal: str | None, cfg: ScoringConfig | None = None) -> Decimal
def default_direction(goal: str | None) -> Direction
def sources(cfg: ScoringConfig | None = None) -> tuple[str, ...]   # section_sources.energy_targets (Task 2); () until then
```

Behaviour the signatures don't fix:
- **Status order** (first match): age known and `< minors.min_age_for_targets` → `not_available_minor`; `pregnant_or_breastfeeding` → `paused_pregnancy`; any missing field → `needs_body_data` with every missing field (Ruling D13); else `ready`. Non-ready results carry only `status`, `missing_fields`, and no numbers.
- **Sex resolution:** `male`/`female` use their constant and floor (reference ignored); `other` uses `sex_reference or "average"`; `None` uses `sex_reference` or is missing. `average` adds `average_sex_reference`.
- **Maths** exactly as spec 4.2–4.7.1, with Ruling D8 (underweight at read → maintain + `underweight_maintenance`; target weight raised to the BMI-18.5 weight) and Ruling D9 (one floor flag). Protein caps in every branch: `max_g_per_kg × W`, then `max_energy_pct × E_t / 4` (flag `protein_capped`). Carbs from the rounded P and F; `carbs_below_reference` when `C < 130`.
- `check_settings` raises, in this order: `fat_pct_out_of_range` {min, max}; `rate_not_allowed` {options} (a rate with `maintain`, or a rate not in the direction's options); `goal_not_allowed_minor` (age < 18 and direction ≠ maintain); `goal_not_allowed_underweight` (lose, BMI(W, H) < `goal_rates.lose_min_current_bmi`); `target_weight_too_low` {min_kg} (`min_kg` = 18.5 × h², rounded **up** to 0.1).
- `check_body_fat` raises `body_fat_out_of_range` {min: 3, max: 70} outside `body_fat.min_pct`–`max_pct`; `None` passes.
- `unusual_fields` returns `height_cm` / `weight_kg` outside `plausible.*`.
- `default_direction`: build_muscle → gain, weight_loss → lose, weight_gain → gain (Q15), healthy_eating or None → maintain.

`targets.yaml`: copy the spec 4.14 skeleton, minus `trend`, `adaptive`, `projection`, `safety` and `plausible.weight_change_kg_per_day` (Ruling D7). First line `# PENDING CLINICIAN REVIEW. Read only by app/scoring/targets.py. Never read by verdict rules.` Mark the Q10 keys `# [clinician]` as in the skeleton.

- [ ] **Step 1: Write the failing tests** in `tests/unit/scoring/test_targets.py` (profiles from spec 4.12; `D()` = `Decimal(str(x))`):

```python
@pytest.mark.parametrize("case, energy, p, f, c, basis, flags", [
    ("G1", 2760, 112, 77, 405, "actual_weight",  ()),
    ("G2", 1540,  71, 43, 217, "adjusted_weight", ()),
    ("G3", 1450,  46, 40, 227, "actual_weight",  ()),
    ("G4", 1200,  62, 33, 164, "actual_weight",  ("deficit_capped", "floor_applied")),
    ("G5", 1940,  91, 54, 273, "actual_weight",  ("taper_active",)),   # W = 76.2 (Ruling D18)
    ("G8", 2180,  50, 61, 358, "actual_weight",  ("average_sex_reference",)),
    ("G11", 2760, 119, 77, 398, "lean_mass",     ()),
    ("G12", 1540,  74, 43, 214, "lean_mass",     ()),
])
def test_golden_examples(case, energy, p, f, c, basis, flags): ...
    # also: r.status == "ready"; r.explanation.protein_basis == basis; r.flags == flags

def test_g1_explanation():  # bmr 1658.75, maintenance 2571.0625, adjustment 192.5, factor 1.55, floor None
def test_g2_adjusted_weight(): # ibw_kg ≈ 52.3819 (to 4 dp), reference ≈ 59.2864, protein_g_per_kg 1.2, floor 1439
def test_g4_floor_and_deficit_cap():  # adjustment -306.45, floor_kcal 1200
def test_g5_taper_rate(): # rate.kg_per_week == D("0.3"); adjustment == -330
def test_g6_minor_has_no_targets():   # age 16 → status not_available_minor, energy/macros None
def test_g7_underweight_lose_refused():  # 168 cm, 50 kg, lose → check_settings raises code goal_not_allowed_underweight
def test_macros_add_up_within_2_kcal():  # every G case: abs(4p + 9f + 4c - energy) <= 2
def test_bmi_boundary_is_exact():  # 160 cm: 76.5 kg → actual_weight; 76.8 kg (BMI 30.0) → adjusted_weight
def test_body_fat_wins_over_bmi():  # G12 basis lean_mass at BMI 31.25
def test_body_fat_bounds():  # check_body_fat: 2.9 and 70.1 raise body_fat_out_of_range {min 3, max 70}; 3, 70, None pass
def test_devine_ibw(sex, expected):  # 175 cm: male 70.46, female 65.96, average 68.21 (2 dp); 150 cm → base only
@pytest.mark.parametrize("goal, factor", [("build_muscle", "2.0"), ("weight_loss", "1.5"),
    ("healthy_eating", "1.0"), ("weight_gain", "1.0"), (None, "1.0")])
def test_lean_mass_factor_every_goal(goal, factor):
@pytest.mark.parametrize("goal, per_kg", [("build_muscle", "1.6"), ("weight_loss", "1.2"),
    ("healthy_eating", "0.83"), ("weight_gain", "0.83"), (None, "0.83")])
def test_protein_g_per_kg_by_goal(goal, per_kg):
def test_age_bounds():  # 17 → not_available_minor; 18 ready; 78 no age flag; 79 has outside_equation_age_range
@pytest.mark.parametrize("missing", ["birth_year", "sex", "height_cm", "weight_kg"])
def test_needs_body_data_each_field(missing):  # status needs_body_data, missing_fields == (missing,)
def test_pregnancy_pauses():  # status paused_pregnancy even with a missing height
def test_floor_binds_for_each_sex():  # male 70 y 160 cm 60 kg sedentary lose 1.0 → 1500 + floor_applied;
    # average 45 y 160 cm 65 kg light lose 1.0 → 1500 + floor_applied
def test_floor_limits_deficit_targets_maintenance():  # female 75 y 145 cm 48 kg sedentary lose 0.5 →
    # energy == 1020 (maintenance 1020.3), flags contain floor_limits_deficit and not floor_applied
def test_deficit_cap_at_1000():  # male 25 y 190 cm 130 kg very lose 1.0 → adjustment -1000, flags rate_capped, deficit_capped
def test_max_kg_per_week():  # 120 kg lose 1.0 → rate.kg_per_week == 1.0, rate_capped
def test_rate_clamped_to_options_range():  # compute with lose 1.5 → rate.pct_bw_per_week == 1.0, rate_capped
def test_taper_band_reaches_maintenance():  # lose, W 75.4, target 75 → adjustment 0, goal_weight_reached
def test_taper_past_target():  # lose, W 74, target 75 → adjustment 0, goal_weight_reached
def test_protein_capped_at_energy_share():  # male 70 y 160 cm 100 kg sedentary maintain, build_muscle, bf 3 →
    # energy 1990, protein_g == 174, protein_capped
def test_max_g_per_kg_caps_every_branch(tmp_cfg):  # YAML override max_g_per_kg 1.0 → P == W in all three branches
def test_custom_fat_share():  # G1 with fat_pct_energy 30 → fat_g == 92
def test_carbs_below_reference_flag():
def test_underweight_at_read_becomes_maintenance():  # stored lose, 168 cm 50 kg → direction maintain, flag underweight_maintenance
def test_low_target_weight_raised_to_minimum():  # 160 cm, target 40 kg → taper uses 47.36 kg
def test_sex_reference_ignored_for_male(); def test_sex_null_without_reference_is_missing()
@pytest.mark.parametrize("settings, code", [...])
def test_check_settings_codes(settings, code):  # lose 0.6 and maintain 0.5 → rate_not_allowed; fat 19 and 31 →
    # fat_pct_out_of_range; age 17 lose/gain → goal_not_allowed_minor (maintain passes);
    # 160 cm target 47.0 → target_weight_too_low with details {"min_kg": 47.4}
def test_rate_options_for_g2():  # lose at 80 kg → kg 0.2, 0.4, 0.6, 0.8 for 0.25/0.5/0.75/1.0 %
def test_unusual_fields():  # height 115 → ("height_cm",); weight 205 → ("weight_kg",)
def test_default_direction_every_goal():
def test_half_up_rounding():  # G5 carbs 272.5 → 273; G1 energy 2763.56 → 2760
```

`tests/unit/scoring/test_targets_yaml.py`:
- `test_header_is_pending_clinician_review` (first line starts with `# PENDING CLINICIAN REVIEW`).
- `test_every_key_is_read`: wrap `cfg.targets` in a recording mapping, run `compute`/`check_settings`/`unusual_fields` over all profiles above, assert every leaf path was read (except `version`, `energy.equation` and `protein.ibw.formula`, which are asserted at load).
- `test_min_age_matches_protein_min_age`: `minors.min_age_for_targets == thresholds daily_limits.protein_min_age == energy.mifflin.valid_age.min`.
- `test_verdict_does_not_import_targets`: walk the import graph of `app.scoring.verdict`, `app.scoring.conditions` and `app.features.analyze.service`; `app.scoring.targets` is never reached.

- [ ] **Step 2: Run them to verify they fail.** `cd apps/api && uv run pytest tests/unit/scoring/test_targets.py tests/unit/scoring/test_targets_yaml.py -q` → FAIL (module not found).
- [ ] **Step 3: Implement** `targets.yaml`, the `ScoringConfig.targets` loader, and `targets.py` with the interfaces above.
- [ ] **Step 4: Run them to verify they pass**, then `uv run pytest -q` and `uv run ruff check . && uv run ruff format --check .`.
- [ ] **Step 5: Commit** `feat(scoring): targets.yaml and the pure daily-targets engine`.

---

### Task 2 (API, scoring): Protein unification, methodology section, clinician sheet *(parallel with Task 3)*

Use the `scoring-rule` skill. Spec: 4.13, 4.14 sources, Q8, Q10.

**Files:**
- Modify: `apps/api/app/scoring/data/thresholds.yaml`, `apps/api/app/scoring/daily_limits.py`, `apps/api/app/scoring/methodology.py`, `scripts/clinician_review_sheet.py`, `docs/launch/clinician-review.md` (regenerated), `packages/test-fixtures/responses/methodology.json` and `packages/test-fixtures/meals/expected/*` (regenerated), `packages/test-fixtures/README.md` (protein moved)
- Tests: `apps/api/tests/unit/scoring/{test_daily_limits,test_methodology,test_build_muscle}.py`, `apps/api/tests/unit/test_clinician_review_sheet.py`, `apps/api/tests/api/meals/{test_meals_summary,test_protein_left}.py`

**Interfaces:**
- Consumes: `targets.protein_g_per_kg(goal, cfg)` (Task 1).
- Produces: `section_sources.energy_targets` in `thresholds.yaml` (read by `targets.sources()`); methodology section id `energy_targets` whose `thresholds` are `cfg.targets` minus `version`.
- `thresholds.yaml`: delete `daily_limits.protein_g_per_kg_by_goal` and `daily_limits.adult.protein_g_per_kg` (comment: "moved to targets.yaml protein.*"). Add `sources` entries `mifflin_1990`, `cdc_weight_loss`, `iom_2005_dri`, `morton_2018`, `icmr_nin_2024`, `devine_1974` (URLs from spec section 13, `url_verified: false`); `section_sources.energy_targets: {thresholds: [mifflin_1990, cdc_weight_loss, iom_2005_dri, issn_protein_2017, morton_2018, icmr_nin_2024, who_protein_2007, devine_1974, smartnutri_working_values], rationale: [issn_protein_2017, iom_2005_dri]}`.
- `daily_limits_for(member, weight_kg, cfg)`: `per_kg = float(targets.protein_g_per_kg(member.goal, cfg))`; the adult-age and weight guards are unchanged. `DailyLimits` is unchanged.
- Clinician sheet: one row per numeric leaf of `targets.yaml`, path prefixed `targets.`; the row-count assertion includes them; the Q10 keys (`protein.lean_mass_g_per_kg_by_goal.*`, `protein.ibw.*`, `protein.adjusted_weight.*`, `body_fat.*`) get the question "Q10: confirm or replace (lean-mass factor / IBW formula / BMI 30 threshold for Asian Indian adults / plausible body-fat range)"; the activity factors get "No primary source found: confirm or replace with ICMR-NIN 2020 PAL values".

- [ ] **Step 1: Write failing tests.**
  - `test_daily_limits.py::test_weight_loss_protein_is_1_2` → `daily_limits_for(member(goal="weight_loss", age=30), 70).protein_target_g == pytest.approx(84.0)` and `protein_g_per_kg == 1.2`.
  - `test_daily_limits.py::test_protein_g_per_kg_read_from_targets_yaml` → no `protein_g_per_kg` key under `thresholds["daily_limits"]`.
  - `test_methodology.py::test_energy_targets_section` → section `energy_targets` exists, its `threshold_sources` include `mifflin_1990`, and its thresholds contain `protein.lean_mass_g_per_kg_by_goal.build_muscle == 2.0`.
  - `test_clinician_review_sheet.py::test_targets_rows_present` → rows for `targets.protein.ibw.devine.kg_per_inch_over_60` and `targets.body_fat.min_pct`, each with a Q10 question; the generated file equals the committed `docs/launch/clinician-review.md`.
  - Update the weight-loss expectations in `test_meals_summary.py` / `test_protein_left.py` to 1.2 g/kg.
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement**, then regenerate: `uv run python ../../scripts/clinician_review_sheet.py > ../../docs/launch/clinician-review.md`, `uv run python scripts/export_fixture_responses.py`, `uv run python scripts/export_meal_fixtures.py`, `uv run python scripts/generate_fixture_expectations.py` (must report no verdict change).
- [ ] **Step 4: Run** `uv run pytest -q` and ruff → PASS.
- [ ] **Step 5: Commit** `feat(scoring): one protein source in targets.yaml (weight loss 1.2 g/kg) and the daily-guides methodology section`. PR note: Q8 changes the weight-loss protein guide.

---

### Task 3 (API, db): Migration 0008, the settings model and `members.body_fat_pct` *(parallel with Task 2)*

Use the `api-endpoint` skill. Spec: 5 (preamble), 5.1 `members`, 5.2, 4.7.1, 9.5 "Members and body fat".

**Files:**
- Create: `apps/api/alembic/versions/0008_diary_goal_settings.py`, `apps/api/app/features/targets/{__init__,models}.py`, `apps/api/tests/api/members/test_body_fat.py`
- Modify: `apps/api/app/features/members/{models,schemas,service}.py`, `apps/api/app/features/me/service.py`, `apps/api/tests/db/{conftest,test_rls,test_grants,test_migrations,test_constraints}.py`, `apps/api/tests/api/test_delete_me.py`

**Interfaces:**
- Consumes: `targets.check_body_fat(value, cfg)` (Task 1).
- Migration `0008_diary_goal_settings`, `down_revision = "0007_plan9_supplement_category"` (Ruling D1):
  - `members.body_fat_pct numeric NULL`, check `ck_members_body_fat_pct`: `body_fat_pct is null or (body_fat_pct >= 3 and body_fat_pct <= 70)`; unique `uq_members_id_account_id (id, account_id)`.
  - `diary_goal_settings`, columns and defaults exactly as spec 5.2 (`member_id` PK, `account_id`, `direction`, `rate_pct_bw_per_week`, `target_weight_kg` check 2–300, `activity_level`, `sex_reference`, `pregnant_or_breastfeeding` default false, `fat_pct_energy`, `energy_mode` default `'formula'`, `numbers_display` default `'show'`, `summary_view` default `'remaining'`, `created_at`, `updated_at`); closed-set checks on the five enum columns; FK `account_id → accounts(id) ON DELETE CASCADE`; composite FK `(member_id, account_id) → members(id, account_id) ON DELETE CASCADE`.
  - Privileges and RLS exactly as `0006_plan9_user_types` (REVOKE, GRANT SELECT to authenticated, ALL to service_role, ENABLE + FORCE, policy `diary_goal_settings_owner`).
  - Downgrade drops the table, the unique constraint and the column.
- `app/features/targets/models.py`: `class DiaryGoalSettings(Base)` mirroring the table (`Numeric(asdecimal=True)` for the numeric columns).
- Members:
  - `Member.body_fat_pct: Mapped[Decimal | None]`; `CheckConstraint(..., name="body_fat_pct")`.
  - `MemberIn.body_fat_pct: float | None = None`; `MemberPatch.body_fat_pct: float | None = None` (null = unchanged, **not** in `NULLABLE_ON_PATCH`) and `MemberPatch.clear_body_fat_pct: bool = False` (Ruling D3); `MemberOut.body_fat_pct: float | None`. No Pydantic bounds: the service returns the specific code.
  - `HEALTH_FIELDS` gains `"body_fat_pct"`.
  - `MemberPatch.changes()`: `clear_body_fat_pct=True` yields `{"body_fat_pct": None}`; sending both a value and the clear flag is `422 validation_error` with `fields: ["body.clear_body_fat_pct"]`.
  - `create_member` / `update_member`: after the goal-age check and before the consent check, `check_body_fat` → `ApiError("body_fat_out_of_range", 422, details={"min": 3, "max": 70})`. Clearing is never gated (existing rule).
- `ACCOUNT_OWNED_TABLES` gains `"diary_goal_settings"` before `"members"`.

- [ ] **Step 1: Write failing tests.**
  - `tests/api/members/test_body_fat.py`:
    - `test_body_fat_accepts_bounds` (3 and 70 stored and returned in `MemberOut`)
    - `test_body_fat_refuses_out_of_range` (2.9, 70.1 → 422 `body_fat_out_of_range`, `details == {"min": 3, "max": 70}`)
    - `test_null_body_fat_on_patch_leaves_value` (stored 15; PATCH `{"name": "A", "body_fat_pct": null}` → still 15)
    - `test_clear_body_fat_pct_clears_without_health_data` (consent withdrawn; clear → 200, value null)
    - `test_body_fat_write_needs_health_data` (403 `consent_required`, `details.purpose == "health_data"`)
    - `test_value_and_clear_together_is_422`
    - `test_body_fat_on_create`.
  - `tests/db/test_constraints.py`:
    - `test_members_body_fat_check` (2.9 → check violation)
    - `test_diary_goal_settings_composite_fk_rejects_foreign_member` (account A row pointing at account B's member → FK violation)
    - `test_diary_goal_settings_closed_sets` (direction `"cut"` → check violation)
  - `tests/db/test_rls.py`: add `diary_goal_settings` to `OWNED` (key `member_id`) and the insert-denied list. `test_grants.py`: add to the user tables. `conftest.TABLES` gains it.
  - `tests/db/test_migrations.py::test_diary_goal_settings_downgrades_cleanly`: head → `0007` removes the table, the column and `uq_members_id_account_id`; back to head restores forced RLS.
  - `tests/api/test_delete_me.py`: a settings row is erased.
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement** the migration, the model and the members changes.
- [ ] **Step 4: Run** `uv run pytest -q` (Docker up for `tests/db`) and ruff → PASS.
- [ ] **Step 5: Commit** `feat(api): migration 0008 diary goal settings and members.body_fat_pct`.

---

### Task 4 (API): Targets routes, consent, rate limits and ADR 0022

Use the `api-endpoint` skill. Spec: 6 (conventions), 6.1, 6.6, 6.7, 9.5.

**Files:**
- Create: `apps/api/app/features/targets/{schemas,mapping,service,router}.py`, `apps/api/tests/api/targets/{__init__,conftest,test_settings,test_targets_get,test_preview,test_display,test_consent,test_invariance}.py`, `docs/adr/0022-daily-targets-health-data-gate.md`
- Modify: `apps/api/app/main.py` (`ROUTERS`), `apps/api/app/core/consent.py`, `apps/api/app/core/ratelimit.py`, `apps/api/app/core/config.py`, `apps/api/tests/api/test_consent_gate.py` (`test_required_purposes_match_ruling_g1`)

**Interfaces:**
- Consumes: Task 1 engine; Task 3 `DiaryGoalSettings`, `Member.body_fat_pct`; `members.service.get_or_create_primary`, `youngest_age`; `consents_service.has_active_consent`; `today_ist`.
- Settings (`config.py`): `diary_family_enabled: bool = False`, `adaptive_tdee_enabled: bool = False`, `rate_limit_diary_settings_per_day: int = 30`, `rate_limit_targets_preview_per_hour: int = 120`. `BUCKETS` gains `diary_settings` (day) and `targets_preview` (hour).
- Consent (Ruling D16): `REQUIRED["targets"] = ("terms", "health_data")`, `REQUIRED["targets_prefs"] = ("terms",)`. The router is **not** in `CONSENT_GATES`; each route lists `Depends(gate_for(...))` first, then `Depends(limit(...))`, with `CONSENT_RESPONSES`.
- Schemas (`schemas.py`):

```python
NumbersDisplay = Literal["show", "hide_energy", "hide_all"]
class NumbersHidden(BaseModel): energy: bool; macros: bool         # also used by meals (Task 5)
class GoalSettingsIn(BaseModel):   # spec 6.1, member_id optional (primary)
    member_id: UUID | None = None; direction: Direction; activity_level: ActivityLevel
    rate_pct_bw_per_week: float | None = None; target_weight_kg: Annotated[float, Field(ge=2, le=300)] | None = None
    sex_reference: SexReference | None = None; pregnant_or_breastfeeding: bool
    fat_pct_energy: float | None = None; energy_mode: Literal["formula", "adaptive"] = "formula"
    numbers_display: NumbersDisplay = "show"; summary_view: Literal["remaining", "consumed"] = "remaining"
class GoalSettingsOut(GoalSettingsIn): member_id: UUID; updated_at: AwareDatetime
class BodyDataIn(BaseModel):  # unsaved preview overrides; a field SENT (even null) overrides the stored one
    birth_year: int | None = None; sex: Sex | None = None; height_cm: HeightCm | None = None
    weight_kg: WeightKg | None = None; body_fat_pct: float | None = None
class TargetsPreviewIn(GoalSettingsIn): body: BodyDataIn | None = None
class DisplayIn(BaseModel): member_id: UUID | None = None; numbers_display: NumbersDisplay | None = None; summary_view: Literal["remaining", "consumed"] | None = None
class RateOut(BaseModel): pct_bw_per_week: float; kg_per_week: float               # 2 dp, unsigned
class TargetsExplanation(BaseModel):   # Ruling D12; numbers null when hidden (Ruling D11)
    bmr_kcal: int | None; activity_factor: float | None; maintenance_kcal: int | None
    adjustment_kcal: int | None; weight_kg_used: float | None; protein_basis: ProteinBasis
    protein_g_per_kg: float | None; protein_reference_weight_kg: float | None
    body_fat_pct_used: float | None; ibw_kg: float | None; floor_kcal: int | None
class TargetsOut(BaseModel):   # spec 6.1 plus rate_options and unusual_fields (Ruling D5)
    member_id: UUID; date: date
    status: Literal["ready", "needs_body_data", "not_available_minor", "paused_pregnancy", "none"]
    missing_fields: list[str]; energy_kcal: int | None; protein_g: int | None; fat_g: int | None; carbs_g: int | None
    basis: Literal["formula", "adaptive"] | None; direction: Direction | None
    rate: RateOut | None; rate_options: list[RateOut]; explanation: TargetsExplanation | None
    flags: list[str]; unusual_fields: list[str]; numbers_hidden: NumbersHidden
    sources: list[str]; pending_clinician_review: Literal[True] = True
```

- `mapping.py` (pure; the fixture generator imports it): `def to_targets_out(member_id: UUID, day: date, result: TargetResult | None, numbers_display: NumbersDisplay, *, unusual: tuple[str, ...] = (), cfg: ScoringConfig | None = None) -> TargetsOut`. `result=None` → `status "none"`. `basis = "formula"` when ready. Applies Ruling D11 redaction and D12 rounding.
- `service.py`:

```python
async def resolve_member(session, account_id: UUID, member_id: UUID | None, settings: Settings) -> Member
    # None → primary (get_or_create_primary); foreign → 404 member_not_found; non-primary and flag off → 422 diary_member_not_enabled
def body_data(member: Member, today: date, overrides: BodyDataIn | None = None) -> targets.BodyData   # age via youngest_age (Ruling D2)
def goal_settings(row: DiaryGoalSettings | GoalSettingsIn) -> targets.GoalSettings
async def get_settings(session, member: Member) -> DiaryGoalSettings | None
async def put_settings(session, member: Member, body: GoalSettingsIn, settings: Settings) -> DiaryGoalSettings
    # adaptive while the flag is off → 422 adaptive_not_enabled; check_settings → ApiError(code, 422, details)
async def put_display(session, member: Member, body: DisplayIn) -> DiaryGoalSettings   # no row → 404 goal_settings_not_found (Ruling D19)
async def delete_settings(session, member: Member) -> None
async def targets_for_today(session, member: Member, cfg=None) -> tuple[TargetResult | None, DiaryGoalSettings | None]   # Task 5 uses it
```

- Routes (`router.py`, prefix `/v1/targets`, tag `targets`):

| Route | operation_id | Gate | Limit | Response |
|---|---|---|---|---|
| `GET /settings?member_id` | `targets_settings_get` | targets | — | `GoalSettingsOut \| None` |
| `PUT /settings` | `targets_settings_put` | targets | diary_settings | `TargetsOut` (today, recomputed) |
| `POST /preview` | `targets_preview` | targets | targets_preview | `TargetsOut` (not saved; `numbers_display` from the body) |
| `GET ?member_id&date` | `targets_get` | targets | — | `TargetsOut`; no settings or past date → `none` (Ruling D1); future → 422 `date_in_future` |
| `DELETE /settings?member_id` | `targets_settings_delete` | targets_prefs | — | 204 |
| `PUT /display` | `targets_display_put` | targets_prefs | diary_settings | `GoalSettingsOut` (Ruling D4) |

- ADR 0022 (copy `0000-template.md`): "Daily targets are information computed by the API; `health_data` gates them". Decision Q13: targets need `terms` + `health_data`; withdrawal stops processing and keeps stored settings (ADR 0018 option 1); delete and display need only `terms`; food logging stays on `terms`.

- [ ] **Step 1: Write failing tests** (a fixture patches `app.features.targets.service.today_ist` to `date(2026, 11, 7)`; the primary is seeded so that `youngest_age` gives the G-case age, e.g. birth_year 1997 → 28):
  - `test_settings.py`:
    - `test_put_then_get_roundtrip` (G1 profile: PUT returns `energy_kcal 2760`, `protein_g 112`, `fat_g 77`, `carbs_g 405`, `explanation.bmr_kcal 1659`, `maintenance_kcal 2571`, `adjustment_kcal 193`; GET settings returns the body)
    - `test_put_error_codes` (parametrized: `goal_not_allowed_minor`, `goal_not_allowed_underweight`, `target_weight_too_low` with `details.min_kg`, `rate_not_allowed`, `fat_pct_out_of_range`, `adaptive_not_enabled`; each 422 with that code)
    - `test_foreign_member_404`, `test_non_primary_422_until_flag_on`
    - `test_delete_then_get_is_none`
    - `test_settings_put_rate_limited` (31st → 429)
  - `test_targets_get.py`:
    - `test_no_settings_is_none`, `test_past_date_is_none`, `test_future_date_422`
    - `test_today_follows_settings_change`
    - `test_targets_get_after_weight_drop_is_maintenance` (stored lose; PATCH weight to BMI 17.7 → 200, `direction "maintain"`, flag `underweight_maintenance`)
    - `test_minor_and_pregnancy_statuses`
  - `test_preview.py`:
    - `test_preview_unsaved_body_fat_moves_basis` (G1 + `body.body_fat_pct 15` → `explanation.protein_basis "lean_mass"`, `protein_g 119`; the member row is unchanged)
    - `test_preview_body_fat_out_of_range` (2.9 → 422 `body_fat_out_of_range`)
    - `test_preview_needs_body_data_is_200` (no height → `status "needs_body_data"`, `missing_fields ["height_cm"]`)
    - `test_preview_unusual_height` (115 → `unusual_fields ["height_cm"]`)
    - `test_preview_rate_options_g2` (`[0.2, 0.4, 0.6, 0.8]` kg)
    - `test_hidden_numbers_redact_every_number` (walks the `TargetsOut` JSON: with `hide_energy`, every key containing `kcal` is null and the macros are not; with `hide_all`, `energy_kcal`, `protein_g`, `fat_g`, `carbs_g` and every `explanation` field except `protein_basis` are null, while `rate` and `rate_options` equal the unhidden response; `numbers_hidden` matches)
  - `test_display.py`:
    - `test_display_toggle` (`hide_all`, then `show`)
    - `test_display_without_settings_404` (`goal_settings_not_found`)
    - `test_display_works_without_health_data`
  - `test_consent.py`:
    - `test_targets_routes_need_health_data` (get, put, preview, settings_get → 403, `details.purposes == ["health_data"]`)
    - `test_delete_and_display_need_only_terms`
    - `test_gate_runs_before_the_rate_limit`
    - `test_withdrawal_keeps_stored_settings`
  - `test_invariance.py::test_targets_never_change_verdicts`: `POST /v1/analyze` for every fixture product is byte-identical before and after saving settings with body fat.
  - `test_consent_gate.py::test_required_purposes_match_ruling_g1` gains the two entries; `tests/api/test_openapi.py` passes after the contract export in Task 6 (run it then).
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement** schemas, mapping, service, router, wiring and ADR 0022.
- [ ] **Step 4: Run** `uv run pytest -q` (excluding `test_committed_openapi_matches_app`, fixed in Task 6) and ruff → PASS.
- [ ] **Step 5: Commit** `feat(api): targets routes with health_data gate, hide numbers and ADR 0022`.

---

### Task 5 (API): `meals_summary` takes protein from targets and redacts hidden numbers

Use the `api-endpoint` skill. Spec: 4.13, 1.1 (hide numbers), 9.3 last bullet. Rulings D10, D11.

**Files:**
- Modify: `apps/api/app/features/meals/{schemas,summary,service,router}.py`
- Create: `apps/api/tests/api/meals/test_summary_targets.py`
- Modify tests: `apps/api/tests/unit/meals/test_summary.py`

**Interfaces:**
- Consumes: `targets.service.targets_for_today`, `NumbersHidden`, `consents_service.has_active_consent`.
- Produces:
  - `Summary.numbers_hidden: NumbersHidden` (default both false).
  - `DailyLimitsOut.protein_basis: ProteinBasis | None` (`"actual_weight"` for the legacy rule when a target exists).
  - `DailyLimitsOut.protein_target_status: Literal["ready", "needs_body_data", "not_available_minor", "paused_pregnancy"] | None` (null = legacy rule).
  - Pure `def redact(summary: Summary, hidden: NumbersHidden) -> Summary` in `summary.py`: `energy` → `totals.energy_kcal` and every `days[].totals.energy_kcal` null; `macros` → every total (all four nutrients, period and days), `limits.protein_target_g` and `protein_left_g` null. Bands and `incomplete` are unchanged.
- Service order: load the member; if it has a settings row **and** `health_data` is active → the protein target is the engine's `protein_g` (with `protein_g_per_kg` and `basis` from its explanation) when ready, else null with `protein_target_status`; otherwise `daily_limits_for` as today. Apply `redact` with the row's `numbers_display` whether or not consent is active (hiding is less processing).

- [ ] **Step 1: Write failing tests.**
  - `test_summary_targets.py`:
    - `test_summary_protein_from_targets` (G11 profile with settings → `limits.protein_target_g == 119.0`, `protein_basis "lean_mass"`, `protein_g_per_kg 2.0`)
    - `test_summary_legacy_without_settings` (weight_loss, 70 kg → `84.0`, `protein_basis "actual_weight"`, `protein_target_status null`)
    - `test_summary_legacy_without_health_data` (settings present, consent withdrawn → legacy)
    - `test_summary_pregnancy_has_no_protein_target` (`protein_target_g null`, `protein_target_status "paused_pregnancy"`)
    - `test_summary_hide_energy` (`totals.energy_kcal null`, `days[*].totals.energy_kcal null`, `totals.sugars_g` present, `numbers_hidden == {energy: true, macros: false}`)
    - `test_summary_hide_all` (every total null; `limits.protein_target_g` and `protein_left_g` null; `bands` equal to the unhidden response)
    - `test_summary_other_member_unaffected`.
  - `test_summary.py::test_redact_is_pure` (the input is not mutated).
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `uv run pytest -q` and ruff → PASS (meal fixtures are regenerated in Task 6).
- [ ] **Step 5: Commit** `feat(meals): summary protein from daily targets and server-side hidden numbers`.

---

### Task 6 (API + shared): Golden target fixtures, home cards, i18n and the contract

Use the `api-contract` skill. Spec: 7.10, 8, 9.1.

**Files:**
- Create: `apps/api/scripts/generate_target_expectations.py`, `packages/test-fixtures/targets/inputs/*.json`, `packages/test-fixtures/targets/expected/*.json` (generated), `packages/test-fixtures/targets/direction_defaults.json`, `apps/api/tests/fixtures/test_target_fixtures.py`
- Modify: `packages/test-fixtures/modes/layouts.json`, `packages/test-fixtures/README.md` (a "Daily targets" section), `packages/test-fixtures/meals/expected/*` (regenerated), `packages/i18n/messages/{en,hi,mr}.json`, `packages/i18n/NATIVE_REVIEW.md`, `packages/api-contract/**` (generated), the mirrored mode tables `apps/app/lib/features/modes/mode_layouts.dart` and `apps/web/src/features/modes/layouts.ts` (with a `today_targets` stub that renders nothing until Tasks 8/10), minimal compile fixes in `apps/app` and `apps/web`

**Interfaces:**
- Input file: `{"as_of": "2026-11-07", "stored": false, "body": {"age", "sex", "height_cm", "weight_kg", "body_fat_pct", "goal"}, "settings": {GoalSettingsIn fields without member_id} | null}`. `settings: null` → `status "none"`. `stored: false` (default) is the preview/PUT path: `check_body_fat` and `check_settings` run first; `stored: true` is the GET path for settings saved earlier: only `compute` runs. Numbers are JSON numbers, read with `Decimal(str(x))`.
- Expected file: `to_targets_out(uuid5(NAMESPACE_URL, "https://smartnutri.app/test-fixtures/members/self"), as_of, ...)` dumped with `mode="json"`, sorted keys, 2-space indent and a trailing newline; or `{"error": {"code": ..., "details": {...}}}` when `check_settings` / `check_body_fat` raises. The script runs `--check` by default and `--write` to update.
- Cases (file stem → what it pins; profiles from spec 4.12 and the Task 1 tests):

| Stem | Pins |
|---|---|
| `g1_build_muscle`, `g2_lose_adjusted`, `g3_eat_healthy`, `g4_floor`, `g5_taper`, `g8_sex_other`, `g11_lean_mass`, `g12_lean_mass_bmi30` | the golden numbers (G4 is also the female floor, G5 the taper window) |
| `g6_minor` | `not_available_minor` |
| `g7_underweight_lose` | error `goal_not_allowed_underweight` |
| `activity_<level>_male`, `activity_<level>_female` (8) | each factor, G1 and G3 bodies, maintain |
| `floor_male`, `floor_average`, `floor_limits_deficit` | the floor flags |
| `rate_max_kg`, `deficit_1000` | `rate_capped`, `deficit_capped` |
| `taper_band`, `taper_past` | taper and `goal_weight_reached` |
| `protein_cap_energy` | `protein_capped` |
| `bmi_29_9`, `bmi_30_0` | basis `actual_weight` / `adjusted_weight` |
| `body_fat_3`, `body_fat_70`, `body_fat_2_9`, `body_fat_70_1`, `body_fat_blank` | accepted / error `body_fat_out_of_range` / unknown |
| `devine_male`, `devine_female`, `devine_average`, `devine_short` | `explanation.ibw_kg` (BMI ≥ 30 bodies; `short` = 150 cm) |
| `lean_factor_<goal>` (5, incl. `weight_gain` and none) | `protein_g_per_kg` 2.0 / 1.5 / 1.0 / 1.0 / 1.0 |
| `age_18`, `age_78`, `age_79` | ready; no flag; `outside_equation_age_range` |
| `needs_<field>` (4) | `missing_fields` |
| `pregnancy` | `paused_pregnancy` |
| `underweight_at_read` (`stored: true`) | maintenance + `underweight_maintenance` |
| `none` | `status "none"` |
| `g1_hide_energy`, `g1_hide_all`, `g4_hide_all` | redaction; G4 for the hidden floor copy |

- `direction_defaults.json`: `{"build_muscle": "gain", "weight_loss": "lose", "healthy_eating": "maintain", "weight_gain": "gain", "none": "maintain"}`.
- `layouts.json` home cards (Ruling D14; tabs unchanged): `gym: [today_targets, today_protein, protein_swaps, protein_claims_tip, recent_scans]`; `weight_loss: [today_targets, today_sugar_salt, recent_scans]`; `eat_better: [today_targets, custom_alerts_setup, claims_tip, recent_scans]`.
- i18n (en from spec 8; hi/mr machine drafts, listed in `NATIVE_REVIEW.md` under "Plan 10" with the flags below):
  - `targets.*`: every key in spec 8 "targets.*" except the adaptive, rapid-loss, low-intake and `mode.*` keys (later slices), with `targets.how` → `targets.how.title` (Ruling D6).
  - Plus these new keys:
    - `targets.how.floor` "Lowest we suggest: {value} kcal a day"
    - `targets.flag.protein_capped` "We've kept protein to a moderate share of your calories."
    - `targets.flag.underweight_maintenance` (same text as `targets.underweight`)
    - `targets.flag.floor_applied_hidden` "We don't suggest going lower than this. A doctor or dietitian can advise you."
    - `targets.pregnancy.yes` / `.no` / `.prefer_not`
    - `targets.intro.title` "Your daily guide" and `targets.intro.body` "An estimate to guide you, based on your details. Information, not medical advice."
    - `targets.step.about` / `.activity` / `.goal` / `.guide`
    - `targets.unusual_confirm` "Please check {fields}. Is this right?"
    - `targets.save`
    - `targets.rate_title` "Pace"
  - `diary.disclaimer`, `diary.targets_consent`, `diary.eye.hide` / `.show`, `diary.hidden_numbers`, `diary.of_target`, `diary.incomplete`.
  - `settings.diary.title`, `.numbers.title` / `.show` / `.hide_energy` / `.hide_all` / `.hide_note`, `.reset`, `.reset_confirm` "Reset your daily guide? Your food log stays.", `.body_fat`.
  - `home.cards.today_targets.title` "Today".
  - `protein.guide_lean` "Daily protein guide: {target} g, based on {per_kg} g per kg of lean mass. Information, not medical advice." and `protein.guide_adjusted` (same, "of an adjusted weight").
  - `methodology.section.energy_targets.title` "How we set daily guides" and `.description`.
  - `error.*` for `goal_not_allowed_minor`, `goal_not_allowed_underweight`, `target_weight_too_low`, `rate_not_allowed`, `fat_pct_out_of_range`, `adaptive_not_enabled`, `body_fat_out_of_range`, `diary_member_not_enabled`, `date_in_future`, `goal_settings_not_found`.
  - Copy rules: neutral; no "you need", "treat", "manage", "cure"; no support contact (Q14).
  - `NATIVE_REVIEW.md` flags: the `targets.flag.*` tone (never judging), `targets.pregnancy.paused`, and the plural or number formatting in `targets.rate_option`.

- [ ] **Step 1: Write failing tests** in `tests/fixtures/test_target_fixtures.py`:
  - `test_expectations_are_current` (`generate_target_expectations.py --check` exits 0)
  - `test_every_input_has_expected`
  - `test_hand_checked_goldens` (reads the expected files: `g1_build_muscle` 2760/112/77/405, `g2_lose_adjusted` 1540/71/43/217 with `explanation.protein_basis "adjusted_weight"` and `ibw_kg 52.4`, `g3_eat_healthy` 1450/46/40/227, `g4_floor` 1200/62/33/164 with flags `["deficit_capped", "floor_applied"]`, `g5_taper` 1940/91/54/273 with `rate.kg_per_week 0.3`, `g8_sex_other` 2180/50/61/358, `g11_lean_mass` 119/398 with `lean_mass`, `g12_lean_mass_bmi30` 74/214 with `lean_mass`)
  - `test_direction_defaults_match_api` (equals `default_direction`)
  - `test_every_flag_has_copy` (each `FLAG_ORDER` entry has `targets.flag.<flag>` in en, hi and mr)
  - `test_new_copy_has_no_medical_claims` (scan the new en/hi/mr keys with the existing banned-word list)

  `tests/fixtures/test_mode_layouts.py` keeps passing with the new cards; `tests/unit/test_error_codes_i18n.py` must pass.
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement.**
  1. Write the inputs and the script, then run `uv run python scripts/generate_target_expectations.py --write`.
  2. Edit `layouts.json` and the i18n files, then run `pnpm --filter @smartnutri/i18n build` and `cd apps/app && flutter gen-l10n`.
  3. Run `uv run python scripts/export_meal_fixtures.py`.
  4. Export the contract and regenerate both clients (the three justfile `contract` lines).
- [ ] **Step 4: Run** `uv run pytest -q` (including `test_committed_openapi_matches_app`), `dart analyze` in `packages/api-contract/dart`, and minimal compile fixes so `cd apps/app && flutter analyze && flutter test test/features/modes` and `cd apps/web && npx tsc --noEmit && pnpm test tests/features/modes` pass with the updated mirrors.
- [ ] **Step 5: Commit** `chore(contract): daily targets contract, golden target fixtures, home cards and i18n`.
- [ ] **Step 6: Safety gate.** `nutrition-safety-reviewer` hand-checks `targets/expected/g*.json` against spec 4.12, the flag copy, and the meal-fixture changes (CODEOWNERS: `packages/test-fixtures`).

---

### Task 7 (Android): Data layer, guide setup and guide settings *(parallel with Task 9)*

Use the `flutter-feature` skill. Spec: 7 (general rules), 7.1, 7.9 (slice-1 parts: numbers, goal, rate, target weight, activity, pregnancy, reset, body data). Rulings D3, D5, D13, D15.

**Files:**
- Create:
  - `apps/app/lib/features/targets/data/targets_repository.dart`
  - `apps/app/lib/features/targets/domain/direction_defaults.dart`
  - `apps/app/lib/features/targets/presentation/targets_providers.dart`, `guide_setup_screen.dart`, `about_you_step.dart`, `activity_step.dart`, `goal_step.dart`, `guide_result_step.dart`, `targets_explanation.dart`, `flag_notes.dart`, `numbers_choice.dart`, `guide_settings_screen.dart`
  - `apps/app/test/features/targets/{guide_setup_test.dart, direction_defaults_test.dart, flag_notes_test.dart}`, `apps/app/test/support/fake_targets.dart`
- Modify:
  - `apps/app/lib/core/router/app_router.dart` (`/guide/setup` full-screen, `/profile/guide` under Profile)
  - `apps/app/lib/features/settings/presentation/profile_screen.dart` (entry "Diary and daily guide")
  - `apps/app/lib/features/consent/data/consent_required_interceptor.dart` (`/v1/targets` handled in place)
  - `apps/app/lib/features/user_types/presentation/prefill_review_screen.dart` (after save or skip, go to `/guide/setup?from=welcome` when the types include `gym`, `weight_loss` or `eat_better`)
  - `apps/app/test/support/fixtures.dart` (`targetsJson(stem)`, `targetsFixture(stem)` → `TargetsOut`)

**Interfaces:**
- Consumes: the generated `targetsSettingsGet/Put`, `targetsPreview`, `targetsGet`, `targetsSettingsDelete`, `targetsDisplayPut`, `membersUpdate` (with `bodyFatPct`, `clearBodyFatPct`); `membersProvider`; `consent_sheet.dart`.
- Produces (used by Task 8):
  - `class TargetsFailure implements Exception { final String? code; final Map<String, Object?> details; }`
  - `TargetsRepository` with `get({String? memberId})`, `settings()`, `preview(TargetsPreviewIn)`, `save(GoalSettingsIn)`, `setDisplay(DisplayIn)`, `reset()`
  - `todayTargetsProvider` (`FutureProvider<TargetsOut>`, the primary member)
  - `goalSettingsProvider` (`FutureProvider<GoalSettingsOut?>`)
  - `String? flagMessage(AppLocalizations l10n, String flag, TargetsOut t)`: `floor_applied` uses `floor_applied_hidden` when `explanation.floorKcal` is null
  - `const kDirectionForGoal = {...}` (mirrors `direction_defaults.json`).
- Flow: steps 1–5 of spec 7.1. Step 1 = intro + `NumbersChoice` (show preselected) + "Skip, just log food" (→ `/home`). Step 2 saves nothing until Save. Step 4 rate chips render `preview.rateOptions` labels via `targets.rate_option`, and **never** compute kg. Step 5 calls `targetsPreview` with the unsaved body, shows numbers, the explanation, flag notes (neutral info style, never the danger token), the kidney note (`protein.kidney_note`) and `unusual_fields` confirmation. Save then:
  0. the screen shows `diary.disclaimer` and `targets.pending_review` under the numbers;
  1. `membersUpdate` on the primary (body data; body fat blank after a stored value → `clearBodyFatPct: true`, blank with none stored → omitted);
  2. `targetsSettingsPut`;
  3. invalidate `todayTargetsProvider` and the meal summary.

  Missing consent → the health-data consent sheet, then retry. `goal_not_allowed_underweight` → `targets.underweight` and `maintain` preselected. "Prefer not to say" on pregnancy sends `true` (Ruling D15).
- Guide settings (`/profile/guide`): the same steps as editable sections, plus "Numbers" (`targetsDisplayPut`) and "Reset daily guide" (confirm → `targetsSettingsDelete`).

- [ ] **Step 1: Write failing widget tests** (`guide_setup_test.dart`; fakes return golden files):
  - `onboarding preselects show numbers`
  - `body fat field shows the hint` (finds `targets.body_fat.hint` text under the field)
  - `blank body fat is saved as unknown` (captured `MemberPatch.bodyFatPct == null`, `clearBodyFatPct` false)
  - `clearing a stored body fat sends clear flag`
  - `member save keeps body fat` (an unrelated profile save sends no clear flag)
  - `out-of-range body fat shows the API message` ("Please enter a number between 3 and 70.")
  - `guide step renders g2_lose_adjusted` ("1,540", "71 g", "43 g", "217 g", and `targets.how.protein_adjusted` with "59.3")
  - `guide step shows lean basis for g11_lean_mass` (`targets.how.protein_lean`, "59.5")
  - `floor note renders for g4_floor in a neutral style` (text includes "1,200"; colour ≠ the danger token)
  - `hidden floor note for g4_hide_all has no digits`
  - `minor shows adults-only message` (`g6_minor`)
  - `pregnancy shows paused message`
  - `underweight lose offers maintenance`
  - `needs_height_cm highlights height`
  - `rate chips show kg from rate_options` (fake option 0.37 → chip text contains "0.37")
  - `g1_hide_all preview shows no digits for energy and macros`
  - `missing consent opens the health-data sheet before save`
  - `unusual height asks for confirmation`
  - `skip goes home without saving`

  `direction_defaults_test.dart`: `kDirectionForGoal` equals the fixture. `flag_notes_test.dart`: every flag in every golden file maps to a non-null message in en, hi and mr.
- [ ] **Step 2: Run** `cd apps/app && flutter test test/features/targets` → FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `flutter analyze && flutter test` → PASS.
- [ ] **Step 5: Commit** `feat(app): daily guide setup and settings`.

---

### Task 8 (Android): Today targets card, eye toggle, hidden numbers and protein basis *(parallel with Task 10)*

Use the `flutter-feature` skill. Spec: 7.2 (slice-1 subset: header eye, numbers, incomplete chip, neutral over, empty and consent states), 7.10, 9.6.

**Files:**
- Create:
  - `apps/app/lib/features/targets/presentation/{today_targets_card.dart, eye_toggle.dart}`
  - `apps/app/test/features/targets/{today_targets_card_test.dart, hidden_numbers_test.dart}`
- Modify:
  - `apps/app/lib/features/home/presentation/cards/{home_cards.dart, today_cards.dart}` (replace the Task 6 stub)
  - `apps/app/lib/features/protein/presentation/protein_progress.dart`
  - `apps/app/lib/features/meals/domain/meal_summary.dart` (`numbersHidden`, `proteinBasis`, `proteinTargetStatus`)
  - `apps/app/lib/features/history/presentation/*` (hidden note)
  - `apps/app/test/features/{home/home_cards_test.dart, modes/*, protein/protein_guide_test.dart, history/*}`

**Interfaces:**
- Consumes: Task 7 providers, `flagMessage`, `TargetsRepository.setDisplay`; `mealSummaryProvider`.
- `TodayTargetsCard` (`'today_targets'` in `HomeCards`):
  - `status none` → `targets.setup_cta` (→ `/guide/setup`) and `targets.skip` (dismisses for the session).
  - `ready` → four rows. Energy and protein show `diary.of_target` with the summary's eaten total. Fat and carbs show the target only (eaten arrives in slice 2). There is no "remaining" number (slice 2 brings it from the API).
  - An incomplete eaten total → the grey `diary.incomplete` chip.
  - Eaten above the target → the same `diary.of_target` line in the neutral token (no "X over": that subtraction is the API's `remaining` in slice 2; Ruling D20).
  - Other statuses → their message.
  - 403 `consent_required` → `diary.targets_consent` card with a grant button (the consent sheet), never a redirect.
  - Footer: `diary.disclaimer`.
  - The `EyeToggle` sits in the card header when settings exist. One tap: `show` → `hide_all`, otherwise → `show`, via `targetsDisplayPut`. Then invalidate the targets and summary providers.
- Hidden rendering: wherever `MealSummary` totals or `TargetsOut` numbers render (Today cards, protein progress, History day and week), `numbersHidden` shows `diary.hidden_numbers` instead of a value, never "not enough data".
- Protein progress copy: `proteinBasis` `lean_mass` → `protein.guide_lean`, `adjusted_weight` → `protein.guide_adjusted`, else `protein.guide`; `proteinTargetStatus == paused_pregnancy` → `targets.pregnancy.paused`.

- [ ] **Step 1: Write failing widget tests:**
  - `today_targets_card_test.dart`:
    - `renders golden g1_build_muscle targets` ("2,760", "112 g", "77 g", "405 g")
    - `status none shows setup CTA and skip`
    - `consent_required shows the consent card, not a redirect` (no navigation, the consent sheet opens on tap)
    - `eye toggle hides every number in one tap` (tap → the fake receives `hide_all`; reloaded with `g1_hide_all` → no `RegExp(r'\d')` text inside the card)
    - `hide_energy shows macros but no kcal`
    - `incomplete energy shows the grey chip`
    - `over target uses the neutral tone`
    - `disclaimer and pending review shown`
  - `hidden_numbers_test.dart`:
    - `history day hides totals when numbers_hidden`
    - `protein card lean basis copy`
    - `protein card paused for pregnancy`
  - `home_cards_test.dart`: `weight_loss mode shows today_targets first`.
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `flutter analyze && flutter test` → PASS.
- [ ] **Step 5: Commit** `feat(app): today daily-guide card, eye toggle and hidden numbers`.

---

### Task 9 (Web): Data layer, guide setup and guide settings *(parallel with Task 7)*

Use the `web-feature` skill. Same behaviour, states and rulings as Task 7. Desktop shows the five steps on one stepper page; mobile shows one step per screen (spec 7.1).

**Files:**
- Create:
  - `apps/web/src/features/targets/api/targets.ts`
  - `apps/web/src/features/targets/hooks/useTargets.ts`
  - `apps/web/src/features/targets/lib/{directionDefaults.ts, flagMessages.ts}`
  - `apps/web/src/features/targets/components/{GuideSetup,AboutYouStep,ActivityStep,GoalStep,GuideResult,TargetsExplanation,FlagNotes,NumbersChoice,GuideSettings}.tsx`
  - `apps/web/src/app/[locale]/(app)/guide/setup/page.tsx`, `apps/web/src/app/[locale]/(app)/profile/guide/page.tsx`
  - `apps/web/tests/features/targets/{GuideSetup.test.tsx, directionDefaults.test.ts, flagMessages.test.ts}`, `apps/web/tests/support/targets-fixtures.ts`
- Modify:
  - `apps/web/src/lib/api/client.ts` (no global consent handling for `/v1/targets` requests)
  - the profile page (entry)
  - the user-types review component (CTA to `/guide/setup?from=welcome` for gym, weight_loss and eat_better)
  - `apps/web/src/features/members/api/members.ts` (types)

**Interfaces:**
- Produces (used by Task 10):
  - `useTodayTargets(): UseQueryResult<TargetsOut, ApiError>`
  - `useGoalSettings()`
  - `usePreviewTargets()`, `useSaveGuide()` (members PATCH, then settings PUT)
  - `useSetDisplay()`, `useResetGuide()`
  - `flagMessage(t, flag, targets): string | null`
  - `DIRECTION_FOR_GOAL`
- Route segments carry no names or values (web AGENTS rule); query param `from=welcome` only.

- [ ] **Step 1: Write failing Vitest tests** with the same names and assertions as Task 7 Step 1 (`GuideSetup.test.tsx`), plus `directionDefaults.test.ts` and `flagMessages.test.ts`, rendering golden files from `packages/test-fixtures/targets/expected` in en, hi and mr where text is asserted.
- [ ] **Step 2: Run** `cd apps/web && pnpm test tests/features/targets` → FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `pnpm lint && npx tsc --noEmit && pnpm test` → PASS.
- [ ] **Step 5: Commit** `feat(web): daily guide setup and settings`.

---

### Task 10 (Web): Today targets card, eye toggle, hidden numbers, protein basis and e2e *(parallel with Task 8)*

Use the `web-feature` skill. Same behaviour as Task 8.

**Files:**
- Create:
  - `apps/web/src/features/targets/components/{TodayTargetsCard,EyeToggle}.tsx`
  - `apps/web/tests/features/targets/{TodayTargetsCard.test.tsx, hiddenNumbers.test.tsx}`
  - `apps/web/e2e/guide.spec.ts`
- Modify:
  - `apps/web/src/features/home/components/cards/{TodayCards,…}.tsx` (the `today_targets` case)
  - `apps/web/src/features/protein/components/ProteinProgress.tsx`
  - `apps/web/src/features/history/components/*` (hidden note)
  - `apps/web/src/features/meals/api/meals.ts` (types)
  - `apps/web/e2e/stub-api.mjs` (the six `/v1/targets` routes and the summary fields)
  - `apps/web/tests/features/{home/cards.test.tsx, modes/modes.test.tsx, protein/protein.test.tsx, history/*}`

**Interfaces:** consumes Task 9 hooks and `flagMessage`. The Today card, eye toggle and hidden rendering follow Task 8.

- [ ] **Step 1: Write failing tests:**
  - Vitest, with the same names and assertions as Task 8 Step 1.
  - Playwright `e2e/guide.spec.ts`:
    1. `set up lose weight and see the guide` (stub returns `g2_lose_adjusted` → "1,540" on Home)
    2. `hide all numbers leaves no digits on the Today card` (eye tap → card text has no digit)
    3. `without health_data the guide shows the consent card and Home still works`
    4. `body fat 15 moves protein to lean mass and clearing it moves it back` (stub `g1_build_muscle` then `g11_lean_mass`: the explanation line changes from `targets.how.protein` to `targets.how.protein_lean` and back)
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `pnpm lint && npx tsc --noEmit && pnpm test && pnpm e2e` → PASS.
- [ ] **Step 5: Commit** `feat(web): today daily-guide card, eye toggle, hidden numbers and e2e`.

---

### Task 11: Slice gate: safety review, parity and docs

**Files:**
- Modify: `docs/FEATURE_PARITY.md` (new row **F21 Food diary and daily guide**: slice 1 built, USER gates as F18–F20), `CONTEXT.md` (Plan 10 row, migration 0008, the clinician questions for Q10 and the activity factors, R20 "support signpost: revisit before launch" as a launch-gate open item), `docs/superpowers/plans/2026-11-07-plan-10-food-diary-slice1.md` (tick boxes)

- [ ] **Step 1:** Run everything:
  - `cd apps/api && uv run pytest -q && uv run ruff check . && uv run ruff format --check .`
  - `generate_target_expectations.py --check`
  - `dart analyze` in `packages/api-contract/dart`
  - `cd apps/app && flutter analyze && flutter test`
  - `cd apps/web && pnpm lint && npx tsc --noEmit && pnpm test && pnpm e2e`
  - Expected: all green, and the target fixtures pass on all three.
- [ ] **Step 2:** Dispatch `nutrition-safety-reviewer` on the whole slice diff. Scope:
  - `targets.yaml` values and their PENDING marks;
  - the engine against spec 4;
  - the golden fixtures;
  - the summary protein change (Q8, Ruling D10);
  - flag and onboarding copy in en, hi and mr (neutral, no claims, no support link);
  - hidden numbers on both clients;
  - the neutral over-target tone;
  - the verdict-invariance and import-graph tests;
  - ADR 0022.
- [ ] **Step 3:** Fix every blocking finding (each fix with its test), then re-run Step 1.
- [ ] **Step 4:** Update the parity and context docs, then commit `docs: Plan 10 slice 1 parity, context and review`.

**USER steps after this plan:**
- Clinician sheet: the Q10 keys, the activity factors, the floors and the weight-loss 1.2 g/kg.
- Native review of the new hi/mr strings.
- Decide on R20 (the support signpost) before launch.
