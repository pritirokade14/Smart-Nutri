# Plan 9: User Types, Focused Modes and the Gym Protein Guide

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Right after the Terms screen on first sign-in, the app asks "What brings you to SmartNutri?". The user picks up to 3 of 6 user types, answers at most one short follow-up per type, or taps "Skip for now". The types are stored on the account. Health and allergy types offer to pre-fill the account holder's own member fields, which are saved only after the user confirms. Each type has a focused mode: its own Home cards and its own 5-tab bar. Everything else stays reachable from "More", and nothing is deleted. Gym users get a "Build muscle" goal, a daily protein target, protein per serving, per 100 g and per 100 kcal on every scan, protein and whey claim checks, a "higher protein" sort, and protein columns in Compare. Supplements are never graded and never suggested. This ships on the API, Android and web.

**The type never changes a verdict.** Verdicts, allergen states and scores come only from `app.scoring.analyze()` and the members' own fields. A user type is presentation only: layout, defaults offered for confirmation, and copy.

**Architecture:**
- **API first.**
  - A new `account_user_types` table (migration `0005`, ENABLE + FORCE RLS) and three `/v1/me/user-types` routes.
  - A pure pre-fill function that turns types and follow-ups into suggested member-field changes. The client applies only the ones the user confirms, through the existing `PATCH /v1/members/{id}`, behind the existing `health_data` gate.
  - `app/scoring` gains the `build_muscle` goal, a protein target by goal, protein facts in the report, protein and whey claim checks, and a `supplement` category (migration `0006`). All numbers are in `thresholds.yaml`, marked PENDING CLINICIAN REVIEW.
  - The protein guide extends existing routes: `meals_summary`, `products_alternatives*`, `products_search` and `products_compare`.
- Then `just contract`, `just i18n` and the shared fixtures.
- **Clients** (Android ∥ web), in three paired tasks: onboarding, focused-mode shell, protein guide. The mode table (tabs, Home cards, More) is one shared data file, `packages/test-fixtures/modes/layouts.json`. Both clients mirror it as constants, and their tests fail on any difference.

**Tech Stack:** as Plan 6. API: Python 3.13, FastAPI, SQLAlchemy 2 async + Alembic, pytest. Android: Flutter, Riverpod 3, go_router, the generated `smartnutri_api`. Web: Next.js 16, TanStack Query, next-intl, `@smartnutri/api-client`. Tests: pytest, flutter_test, Vitest, Playwright.

**Inputs:**
- The user's 8 binding decisions (2026-11-04), restated in the next section.
- The research and draft in `.superpowers/sdd/plan-9-personas/persona-proposal.md` (git-ignored). The decisions override it where they differ: types get focused tab bars (decision 7) instead of "reorder only", and the follow-up is stored.
- ADR 0005 (rules decide), ADR 0018 (withdrawal stops processing), new ADR 0019 (user types and focused modes).

## The user's decisions (binding)

1. **Six user types:**
   - a health condition (diabetes, prediabetes, PCOS or BP; the follow-up asks which)
   - family
   - weight loss
   - gym and fitness
   - food allergy or special diet
   - just eating better
2. **Up to 3 types** per account.
3. **Stored on the account.** Health and allergy types offer to pre-fill the account holder's own member fields only after the user confirms, under the existing `health_data` consent. The type never changes a verdict and is never sent to analytics.
4. **Asked right after the Terms screen** on first sign-in: one screen, then at most one short follow-up per type, with "Skip for now". Editable in Profile.
5. **Gym:** a new "Build muscle" goal and a daily protein target of about 1.6 g/kg body weight, adults only, in YAML, PENDING CLINICIAN REVIEW. The target is tracked and never changes a verdict colour.
6. **Supplements and whey:** no Nutri-Score grade; allergen, diet and claim checks still run; children get a caution; never suggested as alternatives. This is its own task and can slip.
   - **6b. The protein guide (all 5 parts):**
     1. Daily protein progress on Home and the dashboard.
     2. Protein per serving, per 100 g and per 100 kcal on every scan.
     3. Protein and whey claim checks against the nutrition table, plus added sugar, sweeteners, caffeine in pre-workouts, milk/soy/egg allergens and the veg mark.
     4. A "higher protein" sort in alternatives and search, plus a "protein left today" card with suggestions, never `avoid` for the person.
     5. Compare: protein per serving, protein per 100 kcal, sugar, and price per scoop if the user types a price.
7. **Focused modes:** each type has its own Home and tab bar. Nothing is deleted: the rest lives in "More". There is a mode switcher at the top of Home and in Profile when the account has 2–3 types. Scan, verdicts and allergy checks are identical in every mode.
8. **Build now**, before the Play closed test, with parallel agents.

## Rulings made while writing this plan

Builders: these are settled. Existing code names win over this text if they differ (`.superpowers/sdd/RULES-FOR-AGENTS.md`).

- **P9-R1 Storage:** a new table `account_user_types` (one row per account), not columns on `accounts`. This keeps the health-revealing preference out of the row every request loads (`current_account_row`), gives it its own RLS test, and puts it in `ACCOUNT_OWNED_TABLES`.
- **P9-R2 Type keys:** `health_condition`, `family`, `weight_loss`, `gym`, `allergy_diet`, `eat_better`. Health-revealing: `health_condition`, `weight_loss`, `allergy_diet`.
- **P9-R3 Skip:** "Skip for now" stores `types = []`. The account is then in the `eat_better` mode, the default.
- **P9-R4 Active mode:** stored server-side (`active_type`) so Android and web agree. By default it is the chosen type with the highest safety-first priority: `allergy_diet` > `health_condition` > `family` > `weight_loss` > `gym` > `eat_better`.
- **P9-R5 The three tab sets the decisions left open:** Weight loss: Home · Scan · History · Protein · Profile. Allergy or diet: Home · Scan · Family · Search · Profile. Eating better: Home · Scan · Compare · History · Profile.
- **P9-R6 "More"** is one tap from Home (a "More" button next to the mode switcher in the Home header) and is also the first section of Profile. It lists every destination that is not in the current tab bar.
- **P9-R7 The allergy card is not mode-dependent.** When any member has an allergen, every mode's Home shows `allergy_check` first.
- **P9-R8 No analytics event** is added for user types: no type, no count, no "skipped". A test asserts this on all three platforms.
- **P9-R9 Pre-fill only adds.** It never removes a condition, allergen or alert, and it never relaxes a diet. It suggests `diet` only when the current diet is the default `non_veg`. Weight loss together with gym → build muscle is a goal conflict: the review screen asks the user to pick one.
- **P9-R10 Supplements:** detected only from the product category, which the user picks on the confirm screen (never preselected), or from Open Food Facts category tags. Never from the LLM: the extraction prompt is unchanged. Age bands:
  - under 2 → `avoid` (`supplement_infant`). This is stricter than decision 6 ("children get a caution"); it is the safest reading, flagged for the clinician.
  - 2 to 17 → `caution` (`supplement_child`).
  - unknown age → the existing `age_unknown` (`unknown`, Ruling R13).
- **P9-R11 Higher-protein sort:**
  - Candidates need a known protein per 100 kcal that is strictly higher than the source's, and a Nutri-Score grade no worse than the source's.
  - `avoid` for the member is dropped; the member defaults to the primary member.
  - Supplements are excluded.
  - A plain (relevance) search still returns supplements, ungraded.
- **P9-R12 Caffeine and sweeteners are information** in the product report for the protein guide. The existing `child_caffeine` / `infant_caffeine` avoid rules are unchanged. The new claim checks add no member reason.
- **P9-R13 `weight_loss` keeps 0.83 g/kg.** Only `build_muscle` gets 1.6 g/kg. A higher weight-loss target is a clinician question.
- **P9-R14 Two migrations:** `0005_plan9_user_types` (Task 1) and `0006_plan9_supplement_category` (Task 7), so the supplement task can slip on its own. The controller re-chains them at merge if needed.
- **P9-R15 Prompts get v2 files** (`explanation_v2.md`, `voice_v2.md`) that add the protein-guide "never" rules. Released v1 files are never edited.

## Global Constraints

Health-app rules (root `AGENTS.md`, non-negotiable):
1. **The rules engine decides; the LLM only explains.** Verdicts (`ok` / `caution` / `unknown` / `avoid`) come only from `apps/api/app/scoring`. Model output never changes a verdict, an allergen state or a score. Android and web never compute verdicts.
2. **Never invent nutrition data.** A missing value is `None`/`null` and leads to `unknown`. Protein per serving needs a serving size, and protein per 100 kcal needs protein and kcal; otherwise the value is `null`, never 0. Label extractions are confirmed by the user before saving.
3. **Unknown is not safe.** An allergic member never gets `ok` when ingredients are missing or confidence is below 0.7. `unknown` (and a protein band of `unknown`) is never green on any client.
4. **Thresholds live in data.** Every new number (protein target by goal, the `build_muscle` protein density, claim tolerances, supplement ages and statuses) is in `apps/api/app/scoring/data/*.yaml`, marked `PENDING CLINICIAN REVIEW`, with a source. Changes go through the `scoring-rule` skill, regenerated fixtures and a PR note.
5. **Secrets stay server-side.** Nothing new is public config.
6. **Health data residency.** LLM calls with member data keep `provider.data_residency = "in"` with names and IDs stripped. **User types never reach an LLM prompt.**
7. **No medical claims.** Copy is "information, not medical advice". Never "manage", "treat", "cure" or "reverse". Nutri-Score is "calculated by SmartNutri". The protein target is worded as a **guide**, never "you need X g".
8. **Open Food Facts data is ODbL.** Alternatives and search hits from OFF keep `attribution.off`.
9. **Strings only in `packages/i18n`** (en, hi, mr). The API returns codes. Machine-drafted hi/mr strings go in `packages/i18n/NATIVE_REVIEW.md`.
10. **Never hand-edit generated code** (contract clients, ARB/l10n, tokens). Run `just contract` / `just i18n` / `just tokens`.
11. **Feature parity.** Done only when API, Android and web ship it and the shared fixtures pass on all three.

Plan 9 rules:
- **The user type never changes a verdict.** `app/scoring`, `analyze`, `meals/summary`, alternatives, search, compare and the explanation and voice prompts never read `account_user_types`. Two accounts with identical members and different types get byte-identical `analyze` and `meals_summary` responses (Task 1 test).
- **Nothing health-related is set silently.** Pre-fill is a list of suggestions with every item unticked by default except where the user's own follow-up answer says so. The user confirms on a review screen. Only confirmed items go to `PATCH /v1/members/{id}`, and that route keeps its `health_data` check.
- **Consent:** writing a health-revealing type (`health_condition`, `weight_loss`, `allergy_diet`) or a health follow-up (`conditions`, `allergens`, `diet`) needs an active `health_data` consent, otherwise `403 consent_required` with `details.purposes = ["health_data"]`. Switching the active mode needs no new consent. After withdrawal, stored types still drive the layout (it is presentation, like verdicts using stored allergies under ruling G1), and nothing is erased (ADR 0018).
- **Changing types never clears member data.** Removing a type leaves conditions, allergens, diet, goal and alerts untouched.
- **Nothing is deleted from the app.** Every destination (Home, Scan, History, Family, Protein, Compare, Search, Profile, How we score) is reachable in every mode, from the tab bar or from More. Every route stays registered and deep links keep working.
- **Scan is identical in every mode.** The scan entry is always tab 2. The result screen, verdicts, allergy checks, disclaimer and Report a problem are the same widgets and components with the same data. The mode never reaches the result screen.
- **Analytics:** no user type, type count, follow-up, goal, protein value or price ever goes to PostHog or Sentry. `ALLOWED_EVENTS` (API `posthog.py`, web `src/lib/analytics.ts`, Android `lib/core/observability/analytics.dart`) gains nothing.
- **Price per scoop is client-only.** It is typed by the user, computed on the device, shown in Compare, and never stored, logged, sent to the API, put in a URL or tracked.
- **Contract:** every route has an explicit `operation_id` = `<feature>_<action>`. Errors use the `ErrorEnvelope` plus an `error.<code>` i18n key. Every query is scoped by account; another account's id returns 404. Write routes depend on `current_account_row`.
- **Colours** come only from design tokens.
- **Commands:** `just` is not installed for agents. Run the root justfile recipe lines by hand (`.superpowers/sdd/RULES-FOR-AGENTS.md`).

**NOT doing (out of scope, and forbidden in copy, prompts and code):**
- No doses: no "take 1 scoop twice a day", no timing or pre/post-workout advice.
- No brand or supplement recommendations. Supplements are never offered as alternatives or swaps.
- No creatine, steroid, pre-workout stimulant or "fat burner" advice.
- No "you need X g of protein" medical claims. The target is shown as a guide with its basis (g per kg) and the disclaimer.
- No personal kcal target, no carb budget, no medication logic.
- No additive "risk" grades. No amino-spiking detection or protein per rupee from price data (v2).

## Review Focus

1. **Type isolation:** analyze and summary are byte-identical across types. Owned by Task 1 (`test_user_types_never_change_verdicts`) and Tasks 10/13 (`result screen identical in every mode`).
2. **Consent gate:** a health-revealing type without `health_data` → 403; switching mode after withdrawal still works. Task 1.
3. **Pre-fill:** never saved without confirmation, never removes, never relaxes a diet, primary member only. Task 2 (API), Tasks 9/12 (clients).
4. **Protein target:** 1.6 g/kg for `build_muscle` adults only. None under 18, with an unknown age or without a weight. Never changes a status. Task 3.
5. **`build_muscle` never cautions:** the goal adds at most an `ok`-level `good_protein_density`. Task 3.
6. **Supplements:** no grade; a milk-allergic member still gets the milk allergen; children caution, infants avoid; never an alternative or protein swap. Task 7.
7. **Higher protein never suggests `avoid`** or a supplement, and never a worse grade. Task 6.
8. **Price per scoop never leaves the device.** Tasks 11/14.
9. **Reachability:** every destination is reachable in every mode, and scan is tab 2 in all 6. Tasks 10/13.
10. **Copy and prompts:** no medical claims, doses, brands, creatine or steroids, or "you need X g" in en/hi/mr; the "not covered yet" list exists. Tasks 5, 8 and the gate.
11. **Analytics:** nothing about types. Tasks 1, 9, 12.

## Task overview: platform, order, parallelism

| Task | Platform | Depends on | Runs in parallel with |
|---|---|---|---|
| 1. User types: table, routes, consent gate | API | — | 3 |
| 2. Pre-fill suggestions | API | 1 | 3, 4, 5 |
| 3. `build_muscle` goal and protein target | API (scoring) | — | 1, 2 |
| 4. Protein facts and protein/whey claim checks | API (scoring) | 3 | 2, 5 |
| 5. Prompt v2: protein-guide guard rules | API (prompts) | — | 2, 4 |
| 6. Protein guide routes: summary, sorts, compare | API | 4 | 2 |
| 7. Supplements (can slip) | API (scoring) | 6 | — |
| 8. Contract, i18n, mode table, shared fixtures | API + shared | 1–6 (and 7 if landed) | — |
| 9. Onboarding: picker, follow-up, pre-fill, Profile | Android | 8 | **12** |
| 10. Focused-mode shell, Home cards, More, switcher | Android | 9 | **13** |
| 11. Protein guide screens | Android | 10 | **14** |
| 12. Onboarding | Web | 8 | **9** |
| 13. Focused-mode shell | Web | 12 | **10** |
| 14. Protein guide screens | Web | 13 | **11** |
| 15. Slice gate: safety review and parity | All | 9–14 | — |

The scoring tasks (3 → 4 → 6 → 7) all touch `thresholds.yaml` and the fixtures, so they run in that order. Android and web files are disjoint, so 9 ∥ 12, 10 ∥ 13 and 11 ∥ 14. If Task 7 slips, Task 8 runs without the supplement strings and fixtures, and Task 7 later regenerates the contract, strings and fixtures itself.

## Interfaces consumed from earlier plans

Verify these names before Task 1. On a mismatch, the code wins.

- **Plan 2/8 (`me`):** `app/features/me/{models,schemas,router,service}.py`; `MeOut`; `current_account_row` → `CurrentAccount`; `ACCOUNT_OWNED_TABLES` and `erase_account_rows` in `me/service.py`; `tests/api/test_delete_me.py` (fails until a new account table is listed).
- **Plan 5 (members):** `HEALTH_FIELDS = ("allergens", "conditions", "goal", "height_cm", "weight_kg")`; `GoalIn`, `ConditionIn`, `DietIn`, `CustomAlert`, `MemberPatch`, `MemberOut.is_primary`; `members_update` (`PATCH /v1/members/{id}`) with the `health_data` check; `to_scoring_member(record, today=)`; the primary member is ensured by `members/service.py`.
- **Plan 5/8 (consents):** `consents_service.has_active_consent(session, account_id, purpose)`; `CURRENT_VERSIONS` in `consents/policy.py`; `403 consent_required` with `details.purposes`. Android `consent_sheet.dart` and `ConsentScreen`; web `ConsentGate`, `ConsentPrompt`, `ConsentDialog`.
- **Plan 1/6 (scoring):** `analyze`, `ProductReport`, `Product.per_serving()`, `Category`, `Member.goal`, `conditions.weight_loss.good_protein_g_per_100kcal` and the `good_protein_density` reason; `daily_limits_for(member, weight_kg, cfg)` → `DailyLimits.protein_target_g`; `daily_limits.protein_min_age: 18`; `check_claims` with `high_protein` / `source_of_protein`; `ingredients.yaml` `caffeine` and `custom_alerts.artificial_sweetener.terms`; `added_sugar_terms`.
- **Plan 6 (protein data and discovery):** `Summary` with `totals.protein_g`, `limits.protein_target_g`, `bands.protein_g`, `incomplete.protein_g`; `rank_alternatives(source_grade, candidates, member)`, `AlternativesOut.reason`; `search_products(...)` → `SearchHit`; `compare(...)`, `CompareSide`, `CompareBetter`.
- **Plan 8:** `ALLOWED_EVENTS` (posthog.py) mirrored by `analytics.ts` and `analytics.dart`; `scripts/clinician_review_sheet.py` and `docs/launch/clinician-review.md` (a unit test keeps the sheet current).
- **Clients:** Android `lib/core/router/app_router.dart` (`termsStatusProvider` redirect, `StatefulShellRoute` branches `/home`, `/history`, `/family`, `/profile`; `/scan`, `/search`, `/compare` are full-screen routes) and `lib/shared/widgets/app_shell.dart` (bar: Home · Scan · History · Family · Profile; Scan pushes `/scan`). Web `src/app/[locale]/(app)/layout.tsx` (`AppShell` → `ConsentGate`), `src/components/shell/AppNav.tsx` (`TABS`, bar and rail variants).

## File Map

```
apps/api/
  alembic/versions/0005_plan9_user_types.py                 # T1
  alembic/versions/0006_plan9_supplement_category.py        # T7
  app/features/me/{models,schemas,router,service}.py        # T1 (+ user_types section)
  app/features/me/prefill.py                                # T2 (pure)
  app/features/members/schemas.py                           # T3 (GoalIn += build_muscle)
  app/scoring/data/thresholds.yaml                          # T3, T4, T7
  app/scoring/data/ingredients.yaml                         # T4 (whey / other-protein terms)
  app/scoring/{daily_limits,conditions,claims,verdict,models,nutriscore,methodology}.py  # T3, T4, T7
  app/prompts/{explanation_v2,voice_v2}.md, app/prompts/__init__.py   # T5
  app/features/analyze/explain.py, app/features/voice/answer.py       # T5 (banned-word lists)
  app/features/meals/{schemas,summary}.py                   # T6
  app/features/products/{alternatives,search,compare,schemas,router,off_mapping}.py  # T6, T7
  app/features/scans/normalize.py                           # T7 (never proposes supplement)
  scripts/clinician_review_sheet.py                         # T3, T7 (units)
  tests/api/test_user_types.py, tests/unit/me/test_prefill.py
  tests/unit/scoring/{test_build_muscle,test_protein_facts,test_protein_claims,test_supplements}.py
  tests/api/products/test_protein_sort.py, tests/api/meals/test_protein_left.py
  tests/db/{test_rls,test_grants,test_migrations,conftest}.py   # T1, T7
packages/test-fixtures/modes/layouts.json                   # T8 (source of truth for tabs, cards, More)
packages/test-fixtures/protein/price_per_scoop.json         # T8 (client-only arithmetic cases)
packages/test-fixtures/{members,products,expected,responses}/   # T8 (regenerated)
packages/i18n/messages/{en,hi,mr}.json, packages/i18n/NATIVE_REVIEW.md   # T8
packages/api-contract/                                      # T8 (generated)
docs/launch/clinician-review.md                             # T3, T7 (regenerated)
apps/app/lib/features/user_types/…, lib/features/modes/…, lib/features/protein/…   # T9–T11
apps/app/lib/core/router/app_router.dart, lib/shared/widgets/app_shell.dart        # T9, T10
apps/app/lib/features/{home,settings,product,analysis,members,scan}/…             # T10, T11
apps/web/src/features/{user-types,modes,protein,home}/…                            # T12–T14
apps/web/src/app/[locale]/(app)/{welcome,protein}/page.tsx                         # T12, T13
apps/web/src/components/shell/{AppNav,AppShell}.tsx, src/features/consent/components/ConsentGate.tsx
apps/web/src/features/{product,analysis,members,scan}/…                           # T14
docs/FEATURE_PARITY.md (F18–F20), CONTEXT.md                                      # T15
```

---

### Task 1 (API): Account user types: table, routes and consent gate

**Files:**
- Create: `apps/api/alembic/versions/0005_plan9_user_types.py`, `apps/api/tests/api/test_user_types.py`
- Modify: `apps/api/app/features/me/{models,schemas,router,service}.py`, `apps/api/tests/db/{conftest,test_rls,test_grants,test_migrations}.py`, `apps/api/tests/api/test_delete_me.py` (only if it lists tables explicitly)

**Interfaces:**

Table `account_user_types` (one row per account):
- `account_id uuid primary key references accounts(id) on delete cascade`
- `types text[] not null default '{}'`, with check constraint `user_types`: `cardinality(types) <= 3 and types <@ array['health_condition','family','weight_loss','gym','allergy_diet','eat_better']::text[]`
- `follow_ups jsonb not null default '{}'`
- `active_type text null`, with check constraint `active_type`: `active_type is null or active_type = any(types)`
- `answered_at timestamptz not null default now()`, `updated_at timestamptz not null default now()`
- Privileges and RLS exactly like `members`: `REVOKE ALL … FROM PUBLIC, anon, authenticated`; `GRANT SELECT … TO authenticated`; `GRANT ALL … TO service_role`; `ENABLE` + `FORCE ROW LEVEL SECURITY`; policy `account_user_types_owner FOR ALL TO authenticated USING (account_id = auth.uid()) WITH CHECK (account_id = auth.uid())`.
- `revision = "0005_plan9_user_types"`, `down_revision = "0004_plan8_deleted_accounts"`.

```python
# app/features/me/schemas.py
UserType = Literal["health_condition", "family", "weight_loss", "gym", "allergy_diet", "eat_better"]
USER_TYPE_PRIORITY: tuple[UserType, ...] = (
    "allergy_diet", "health_condition", "family", "weight_loss", "gym", "eat_better")
HEALTH_REVEALING_TYPES = frozenset({"health_condition", "weight_loss", "allergy_diet"})
HEALTH_FOLLOW_UPS = frozenset({"conditions", "allergens", "diet"})
DEFAULT_TYPE: UserType = "eat_better"
GymGoal = Literal["build_muscle", "lose_fat", "stay_fit"]
FamilyWith = Literal["children", "parents", "partner", "others"]
AllergenKey = Literal["milk", "peanut", "gluten", "soy", "egg", "tree_nut", "sesame",
                      "fish", "crustacean", "mustard", "sulphite"]   # allergens.yaml keys; check at build time

class FollowUps(BaseModel):            # model_config = ConfigDict(extra="forbid")
    conditions: list[ConditionIn] | None = Field(default=None, min_length=1, max_length=4)  # health_condition
    family_with: list[FamilyWith] | None = Field(default=None, max_length=4)               # family
    gym_goal: GymGoal | None = None                                                         # gym
    allergens: list[AllergenKey] | None = Field(default=None, max_length=11)                # allergy_diet
    diet: DietIn | None = None                                                              # allergy_diet
    alerts: list[CustomAlert] | None = None                                                 # eat_better
    # weight_loss has no follow-up. Lists are unique.

class UserTypesIn(BaseModel):
    types: list[UserType] = Field(max_length=3)   # unique; [] = "Skip for now"
    follow_ups: FollowUps = FollowUps()

class ActiveTypeIn(BaseModel):
    active_type: UserType

class UserTypesOut(BaseModel):
    types: list[UserType]                 # stored order = the user's tap order
    follow_ups: FollowUps
    active_type: UserType                 # resolved: stored value if in types, else the
                                          # highest-priority chosen type, else "eat_better"
    answered: bool                        # false until the first PUT: clients show the picker
    answered_at: datetime | None
    prefill: PrefillSuggestion | None     # Task 2; None in this task
```

Routes (prefix `/v1/me`, tag `me`, all depend on `current_account_row`):
- `GET /v1/me/user-types`, `operation_id="me_user_types_get"` → `UserTypesOut`. With no row: `types=[]`, `answered=false`, `active_type="eat_better"`.
- `PUT /v1/me/user-types`, `operation_id="me_user_types_put"`, body `UserTypesIn` → `UserTypesOut`. An upsert. It keeps `active_type` if it is still in the new `types`, else sets it to null (resolved on read).
  - `403 consent_required` (`details.purposes = ["health_data"]`) when the body has a health-revealing type or a health follow-up and `has_active_consent(session, account_id, "health_data")` is false. Nothing is written.
  - `422 validation_error`: more than 3 types, duplicates, or duplicate list items.
  - `422 follow_up_without_type`: a follow-up whose type is not in `types` (for example `gym_goal` without `gym`).
- `PATCH /v1/me/user-types/active`, `operation_id="me_user_types_set_active"`, body `ActiveTypeIn` → `UserTypesOut`. Needs no consent.
  - `422 user_type_not_selected` unless `active_type` is in the stored `types`, or `types == []` and `active_type == "eat_better"`.
  - `404 user_types_not_found` when there is no row.
- `ACCOUNT_OWNED_TABLES` gains `"account_user_types"` (before `"consents"`; the list is erased in order).
- No `track(...)` call and no log line with types or follow-ups. Log only `user_types status=saved count=<n>`.

- [ ] **Step 1: Write failing tests.**
  - `tests/api/test_user_types.py`:
    - `test_get_without_row_is_unanswered_eat_better`
    - `test_put_roundtrip_and_resolved_active_type` (`["gym", "allergy_diet"]` → `active_type == "allergy_diet"`)
    - `test_skip_stores_empty_and_answered`
    - `test_more_than_three_or_duplicates_422`
    - `test_follow_up_without_type_422`
    - `test_health_type_without_consent_403_writes_nothing` (each of the 3 health types, and `follow_ups.conditions` under `family`)
    - `test_gym_and_family_need_no_health_consent`
    - `test_set_active_must_be_selected_422` and `test_set_active_after_withdrawal_ok`
    - `test_removing_types_keeps_member_fields` (seed the primary member with allergens and conditions, PUT `[]`, member unchanged)
    - `test_user_types_never_change_verdicts`: two accounts with identical seeded families, one with `["gym"]` and one with `["health_condition", "allergy_diet", "family"]`. `POST /v1/analyze` for a fixture product and `GET /v1/meals/summary` give byte-identical bodies, apart from ids that come from the account. Compare after mapping member ids.
    - `test_other_accounts_row_is_invisible` (account B's GET is unanswered)
    - `test_no_analytics_for_user_types`: patch `app.integrations.posthog.track` and assert it is never called by the three routes, and that no `ALLOWED_EVENTS` key or property name contains `type`, `goal` or `focus`.
  - `tests/db/test_rls.py`: add `account_user_types` to `OWNED` and to `test_policies_are_exactly_as_designed` (`("account_user_types", "ALL")`), and add it to `TABLES` in `tests/db/conftest.py` with a seed row per account. The existing parametrised cases then cover isolation, denied writes and anon.
  - `tests/db/test_grants.py`: `authenticated` is SELECT-only on it.
  - `tests/db/test_migrations.py`: `test_user_types_downgrades_cleanly` (0005 down, then up).
  - `tests/api/test_delete_me.py` (existing): passes only once the table is in `ACCOUNT_OWNED_TABLES`. Add `test_delete_me_erases_user_types`.
- [ ] **Step 2: Run them to verify they fail.** `cd apps/api && uv run pytest tests/api/test_user_types.py tests/db -q`.
- [ ] **Step 3: Implement** the migration, the `AccountUserTypes` model (`app/features/me/models.py`), the schemas, the service (`get_user_types`, `put_user_types`, `set_active_type`, `resolve_active_type`) and the routes. Check `uv run alembic downgrade -1 && uv run alembic upgrade head`.
- [ ] **Step 4: Run them to verify they pass**, then the full suite: `uv run pytest -q && uv run ruff check . && uv run ruff format --check .`.
- [ ] **Step 5: Commit** with message `feat(api): account user types with health-data consent gate (migration 0005)`.
- USER: apply migration 0005 to dev (`just db-migrate`) before the next deploy.

---

### Task 2 (API): Pre-fill suggestions for the account holder

**Files:**
- Create: `apps/api/app/features/me/prefill.py`, `apps/api/tests/unit/me/test_prefill.py`
- Modify: `apps/api/app/features/me/{schemas,service,router}.py`, `apps/api/tests/api/test_user_types.py`

**Interfaces:**

```python
PrefillField = Literal["conditions", "allergens", "diet", "goal", "custom_alerts"]

class PrefillChange(BaseModel):
    field: PrefillField
    current: list[str] | str | None   # the primary member's value now
    value: list[str] | str            # the FULL new value to send in MemberPatch if confirmed
    added: list[str]                  # list fields: what is new (for display); [] for diet/goal
    reason: UserType                  # which type suggested it (display only)

class PrefillSuggestion(BaseModel):
    member_id: UUID                   # always the primary member (relation self)
    changes: list[PrefillChange]      # [] = nothing to confirm; the client skips the review screen
    goal_choice: list[GoalIn] | None  # ["weight_loss", "build_muscle"] on a goal conflict: no goal
                                      # change is in `changes`; the user picks one or neither
    needs_health_consent: bool        # any change touches HEALTH_FIELDS and health_data is not active

def suggest_prefill(types: Sequence[UserType], follow_ups: FollowUps,
                    primary: MemberSnapshot) -> tuple[list[PrefillChange], list[GoalIn] | None]  # pure
```

Rules (pure, tested exhaustively):

| Type and follow-up | Suggested change |
|---|---|
| `health_condition` + `conditions` | `conditions` = current ∪ chosen (only if something is new) |
| `weight_loss` | `goal = weight_loss` if different |
| `gym` + `build_muscle` / `lose_fat` / `stay_fit` | `goal = build_muscle` / `weight_loss` / `healthy_eating`, if different |
| `weight_loss` and `gym` + `build_muscle` | no goal change; `goal_choice = ["weight_loss", "build_muscle"]` |
| `allergy_diet` + `allergens` | `allergens` = current ∪ chosen |
| `allergy_diet` + `diet` | `diet` = chosen, **only if the current diet is `non_veg`** (never relax a stricter diet) |
| `eat_better` + `alerts` | `custom_alerts` = current ∪ chosen; `goal = healthy_eating` only if the goal is null |
| `family` | none (its follow-up opens "Add a family member") |

Never a removal. Never a field outside the table. Never a non-primary member. `UserTypesOut.prefill` is filled on both `PUT` and `GET`, and it is recomputed from the current member each time, so it is empty once the user has confirmed.

- [ ] **Step 1: Write failing tests.**
  - `tests/unit/me/test_prefill.py`, one per table row, plus:
    - `test_never_removes` (current allergens `[peanut]`, chosen `[milk]` → value `[peanut, milk]`)
    - `test_never_relaxes_diet` (current `vegan`, chosen `veg` → no change)
    - `test_nothing_new_means_no_change`
    - `test_goal_conflict_offers_choice`
    - `test_family_and_skip_suggest_nothing`
  - `tests/api/test_user_types.py`:
    - `test_put_returns_prefill_for_primary_only`
    - `test_prefill_is_not_applied` (the member is unchanged after PUT)
    - `test_prefill_empty_after_confirm` (PATCH the member with `value`s, then GET → `changes == []`)
    - `test_needs_health_consent_flag`
- [ ] **Step 2: Run them to verify they fail.** `uv run pytest tests/unit/me tests/api/test_user_types.py -q`.
- [ ] **Step 3: Implement** `prefill.py` and wire it into the service and routes.
- [ ] **Step 4: Run them to verify they pass**, plus the full API suite and ruff.
- [ ] **Step 5: Commit** with message `feat(api): pre-fill suggestions from user types (confirm-only, never removes)`.

---

### Task 3 (API, scoring): `build_muscle` goal and protein target by goal

Use the `scoring-rule` skill.

**Files:**
- Modify: `apps/api/app/scoring/data/thresholds.yaml`, `apps/api/app/scoring/{daily_limits,conditions,methodology}.py`, `apps/api/app/features/members/schemas.py`, `scripts/clinician_review_sheet.py`, `docs/launch/clinician-review.md` (regenerated), `apps/api/tests/unit/test_clinician_review_sheet.py`
- Create: `apps/api/tests/unit/scoring/test_build_muscle.py`

**Interfaces:**

```yaml
conditions:
  build_muscle:            # PENDING CLINICIAN REVIEW. A goal is a preference (Ruling R34):
    applies_to: [build_muscle]   # it may add an OK-level reason only, never a caution or avoid.
    good_protein_g_per_100kcal: 5   # same SmartNutri working value as weight_loss
daily_limits:
  # Protein TARGET by goal (g per kg body weight per day), adults (protein_min_age) with a
  # weight only. build_muscle 1.6: ISSN position stand 2017 (Jäger et al., PMID 28642676),
  # range 1.4-2.0 for exercising people. PENDING CLINICIAN REVIEW. Other goals use adult.protein_g_per_kg.
  protein_g_per_kg_by_goal: {build_muscle: 1.6}
sources:
  issn_protein_2017: {title: "ISSN position stand: protein and exercise (2017)", url: "https://pubmed.ncbi.nlm.nih.gov/28642676/", url_verified: false}
```

- `section_sources.daily_limits` gains `issn_protein_2017`; a new `section_sources.build_muscle: {thresholds: [smartnutri_working_values], rationale: [issn_protein_2017]}`.
- `GoalIn = Literal["healthy_eating", "weight_loss", "weight_gain", "build_muscle"]`. `weight_gain` is unchanged.
- `daily_limits_for(member, weight_kg, cfg)`: `per_kg = protein_g_per_kg_by_goal.get(member.goal, adult.protein_g_per_kg)`. The adult-age and weight guards are unchanged.
- `condition_reasons`: the `build_muscle` group adds `good_protein_density` (`Status.OK`) exactly as `weight_loss` does, and nothing else.
- `scripts/clinician_review_sheet.py`: unit `"g per kg body weight per day"` for `("daily_limits", "protein_g_per_kg_by_goal", "build_muscle")`. Add questions:
  - Is 1.6 g/kg right?
  - Should members with diabetes or hypertension keep it?
  - There is no kidney field. The copy says "If you have kidney disease, ask your doctor before eating more protein." Is that enough?
  - Should weight loss get 1.2 g/kg?

- [ ] **Step 1: Write failing tests** (`tests/unit/scoring/test_build_muscle.py`):

```python
def test_protein_target_by_goal(cfg):
    m = Member(id="g", name="G", age=25, goal="build_muscle")
    assert daily_limits_for(m, 70.0, cfg).protein_target_g == pytest.approx(112.0)

@pytest.mark.parametrize("age", [17, None])
def test_no_target_under_18_or_unknown_age(cfg, age):
    m = Member(id="g", name="G", age=age, goal="build_muscle")
    assert daily_limits_for(m, 70.0, cfg).protein_target_g is None

def test_no_target_without_weight(cfg):
    assert daily_limits_for(Member(id="g", name="G", age=30, goal="build_muscle"), None, cfg).protein_target_g is None

def test_other_goals_keep_adult_value(cfg):
    m = Member(id="w", name="W", age=30, goal="weight_loss")
    assert daily_limits_for(m, 70.0, cfg).protein_target_g == pytest.approx(58.1)

def test_good_protein_density_is_ok_reason(cfg, high_protein_product): ...

def test_build_muscle_never_changes_status(cfg, all_fixture_products):
    # For every fixture product: status(goal=build_muscle) == status(goal=None), and the
    # reasons differ by at most one ("good_protein_density", ok).
```

  Also extend `test_clinician_review_sheet.py` with the new unit, and the methodology test with the `build_muscle` section.
- [ ] **Step 2: Run them to verify they fail.** `uv run pytest tests/unit/scoring/test_build_muscle.py -v`.
- [ ] **Step 3: Implement** the data first, then the code. Regenerate the sheet: `uv run python ../../scripts/clinician_review_sheet.py > ../../docs/launch/clinician-review.md` (check the script's own usage line).
- [ ] **Step 4: Run them to verify they pass**, plus `uv run pytest tests/unit/scoring tests/fixtures -q` and `uv run python scripts/generate_fixture_expectations.py` (`--check`: no fixture member has `build_muscle` yet, so expect no diff).
- [ ] **Step 5: Commit** with message `feat(scoring): build_muscle goal and protein target by goal (pending clinician review)`.
- [ ] **Step 6: Safety gate.** Run `nutrition-safety-reviewer` on the diff.

---

### Task 4 (API, scoring): Protein facts in the report and protein/whey claim checks

Use the `scoring-rule` skill.

**Files:**
- Modify: `apps/api/app/scoring/{verdict,claims,models,__init__}.py`, `apps/api/app/scoring/data/{thresholds,ingredients}.yaml`
- Create: `apps/api/tests/unit/scoring/{test_protein_facts,test_protein_claims}.py`

**Interfaces:**

```python
@dataclass(frozen=True, slots=True)
class ProteinFacts:
    per_100g: float | None
    per_serving: float | None    # None without serving_size_g (Product.per_serving)
    per_100kcal: float | None    # protein_g / energy_kcal * 100; None if either is None or kcal == 0
    serving_size_g: float | None
# All rounded to 1 dp, from the SANITISED product (implausible values were already dropped).

ProductReport += protein: ProteinFacts
ProductReport += sweeteners: tuple[str, ...]   # custom_alerts.artificial_sweetener terms found, plus
                                               # "contains_sweeteners" when only the OFF flag says so
ProductReport += caffeine: tuple[str, ...]     # ingredients.yaml `caffeine` terms found
```

They serialise into `AnalyzeOut.report` and `PublicProductOut.report` as `report.protein`, `report.sweeteners` and `report.caffeine`. Existing `hidden_sugars`, `allergens`, `diet_violations` and `veg_mark_mismatch` already cover added sugar, milk/soy/egg and the veg mark.

New claim keys in `claims.py` (matched **before** `high_protein` and `source_of_protein`):

| Key | Matches | Check |
|---|---|---|
| `protein_amount` | a number + `g` + `protein` (e.g. "24g protein per scoop", "24 g protein") | per serving when the claim says serving/scoop/serve and `serving_size_g` is known, else per 100 g. `contradicted` / `below_claimed` when the table value is more than `claims.protein_amount_shortfall_pct` % below the claim; `unverifiable` / `nutrient_missing` without the value or the serving size |
| `whey_only` | "100% whey", "pure whey" | `contradicted` / `other_protein_source` when `claims.other_protein_terms` are found in the ingredients; `unverifiable` / `ingredients_unknown` when ingredients are unknown |
| `whey_protein` | "whey", "whey protein" | `contradicted` / `whey_not_listed` when no `claims.whey_terms` are found in known ingredients; `unverifiable` when ingredients are unknown |

```yaml
claims:
  # Protein claims vs the nutrition table. PENDING CLINICIAN REVIEW; SmartNutri working value
  # (verify against the FSSAI Labelling and Display Regulations 2020 tolerance).
  protein_amount_shortfall_pct: 10
  whey_terms: [whey, whey protein, whey protein concentrate, whey protein isolate, hydrolysed whey, hydrolyzed whey, wpc, wpi, व्हे]
  other_protein_terms: [soy protein, soya protein, soy protein isolate, pea protein, rice protein, wheat protein, wheat gluten, collagen, gelatin, casein, caseinate, milk protein concentrate]
```

- New claim checks add **no member reason** (P9-R12). The `test_new_claims_never_change_status` test pins this.

- [ ] **Step 1: Write failing tests.**
  - `test_protein_facts.py`:
    - `test_per_serving_and_per_100kcal` (25 g/100 g, 400 kcal, 30 g serving → 7.5, 6.3)
    - `test_none_stays_none` (no kcal → `per_100kcal is None`; no serving → `per_serving is None`)
    - `test_zero_kcal_is_none`
    - `test_sweeteners_and_caffeine_listed`
    - `test_off_sweetener_flag_listed`
  - `test_protein_claims.py`:
    - `test_protein_amount_supported_per_scoop`
    - `test_protein_amount_below_claimed`
    - `test_protein_amount_without_serving_unverifiable`
    - `test_whey_only_with_soy_protein_contradicted`
    - `test_whey_not_listed`
    - `test_whey_ingredients_unknown_unverifiable`
    - `test_plain_protein_word_still_source_of_protein`
    - `test_new_claims_never_change_status` (over all fixture products and members)
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement** the data first, then `ProteinFacts` in `verdict._build`, the report fields and the claim keys.
- [ ] **Step 4: Run them to verify they pass**, plus `uv run pytest tests/unit/scoring tests/fixtures -q`. The report shape changed, so regenerate the goldens: `uv run python scripts/export_fixture_responses.py`, and check that `tests/api/analyze/test_shared_fixtures.py` passes. Verdicts in `expected/` must not change (`generate_fixture_expectations.py` reports no diff).
- [ ] **Step 5: Commit** with message `feat(scoring): protein per serving and per 100 kcal, and protein and whey claim checks`.
- [ ] **Step 6: Safety gate.** Run `nutrition-safety-reviewer` on the diff.

---

### Task 5 (API, prompts): Protein-guide guard rules in the explanation and voice prompts

**Files:**
- Create: `apps/api/app/prompts/explanation_v2.md`, `apps/api/app/prompts/voice_v2.md`
- Modify: `apps/api/app/prompts/__init__.py` (versions → v2), `apps/api/app/features/analyze/explain.py`, `apps/api/app/features/voice/answer.py` (banned-word lists), their tests

**Interfaces:**
- v2 = v1 plus one rule: "Never recommend a supplement, a brand or a product to buy. Never mention creatine, steroids, pre-workouts or fat burners. Never say how much protein, or how many scoops or servings, someone needs or should eat. You may repeat protein numbers that are in the input."
- The output filters that throw away a reply gain `creatine`, `steroid`, `steroids`, `fat burner` and their hi/mr forms ("क्रिएटिन", "स्टेरॉयड").
- The prompt input never contains user types. A test asserts that the serialised context has no key named `user_type`, `types` or `active_type`.
- `prompt_version` in responses becomes `explanation_v2` / `voice_v2`. The goldens are regenerated in Task 8.

- [ ] **Step 1: Write failing tests:**
  - `test_explanation_uses_v2`
  - `test_reply_with_creatine_is_discarded` (fake LLM)
  - `test_reply_with_dose_language_is_discarded` ("2 scoops a day")
  - `test_context_has_no_user_types`
  - the same set for voice.
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement.** No live LLM calls: use the existing fakes.
- [ ] **Step 4: Run them to verify they pass**, plus the full API suite.
- [ ] **Step 5: Commit** with message `feat(prompts): v2 explanation and voice prompts forbid supplement, dose and creatine advice`.
- [ ] **Step 6: Safety gate.** Run `nutrition-safety-reviewer` (prompts are CODEOWNERS-reviewed).

---

### Task 6 (API): Protein guide routes: daily protein left, higher-protein sort, compare columns

**Files:**
- Modify: `apps/api/app/features/meals/{schemas,summary,router}.py`, `apps/api/app/features/products/{alternatives,search,compare,schemas,router}.py`
- Create: `apps/api/tests/api/meals/test_protein_left.py`, `apps/api/tests/api/products/test_protein_sort.py`, `apps/api/tests/unit/products/test_protein_rank.py`

**Interfaces:**

```python
# meals: Summary gains
protein_left_g: float | None = Field(description=(
    "period=day only: max(0, limits.protein_target_g - totals.protein_g), 1 dp. Null when there "
    "is no target, when protein is incomplete for the day, or for period=week. A guide, not a need."))

# products: both alternatives routes gain
sort: Annotated[Literal["grade", "protein"], Query()] = "grade"
AlternativeOut += protein_g: float | None, protein_per_100kcal: float | None
AlternativesOut.reason += "source_protein_unknown"   # sort=protein and the source has no protein per 100 kcal

# products_search gains
sort: Annotated[Literal["relevance", "protein"], Query()] = "relevance"
member_id: Annotated[UUID | None, Query()] = None
SearchHit += protein_g: float | None, protein_per_100kcal: float | None, member_status: MemberStatus | None
# products_search moves from current_account to current_account_row (it now resolves a member).

# compare: CompareSide gains
serving_size_g: float | None
protein_per_serving_g: float | None
sugars_per_serving_g: float | None
protein_per_100kcal: float | None
# CompareBetter gains (same "a" | "b" | "same" | "unknown" rule; missing is unknown, never a win)
protein_per_serving_g (higher), protein_per_100kcal (higher), sugars_per_serving_g (lower)
```

Every protein number comes from `report.protein` (Task 4). There is no second calculation.

`rank_alternatives_by_protein(source, candidates, member)` (pure, P9-R11):
1. The source needs `protein.per_100kcal` (else `reason="source_protein_unknown"`) and a grade (else `source_ungraded`, as today).
2. Keep candidates with a known `per_100kcal` **strictly greater** than the source's, and a grade that is known and **not worse** than the source's.
3. Analyse each candidate for the member. **Drop `avoid`.** The member is `member_id`, or the primary member when it is absent.
4. Order: ok > caution > unknown, then `per_100kcal` descending, then grade, then name. At most 5. `reason="no_better_found"` when empty.

Search with `sort=protein`:
- Same member rule: drop `avoid` and fill `member_status`.
- Order by `protein_per_100kcal` descending, with unknown values last.
- `sort=relevance` is unchanged, with `member_status` null unless `member_id` is given.

- [ ] **Step 1: Write failing tests.**
  - `test_protein_left.py`:
    - `test_protein_left_day` (target 112, eaten 40 → 72.0)
    - `test_protein_left_never_negative`
    - `test_protein_left_null_without_target_or_incomplete`
    - `test_protein_left_null_for_week`
  - `test_protein_rank.py`:
    - `test_never_avoid_for_member` (a milk-allergic member never gets a milk product)
    - `test_never_worse_grade`
    - `test_strictly_more_protein_per_100kcal`
    - `test_unknown_protein_excluded`
    - `test_order_status_then_protein`
    - `test_defaults_to_primary_member`
  - `test_protein_sort.py`:
    - `test_alternatives_sort_protein_route`
    - `test_search_sort_protein_drops_avoid`
    - `test_search_relevance_unchanged`
    - `test_compare_protein_columns_and_better`
    - `test_compare_missing_serving_is_unknown`
    - `test_other_accounts_member_404`
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them to verify they pass**, plus the full API suite and ruff.
- [ ] **Step 5: Commit** with message `feat(api): protein left today, higher-protein sort and protein compare columns`.

---

### Task 7 (API, scoring): Supplements *(can slip)*

Use the `scoring-rule` skill.

**Files:**
- Create: `apps/api/alembic/versions/0006_plan9_supplement_category.py`, `apps/api/tests/unit/scoring/test_supplements.py`, `apps/api/tests/api/products/test_supplement_alternatives.py`
- Modify: `apps/api/app/scoring/{models,nutriscore,conditions}.py`, `apps/api/app/scoring/data/thresholds.yaml`, `apps/api/app/features/products/{models,schemas,off_mapping,alternatives,search}.py`, `apps/api/app/features/scans/normalize.py` (tests only, if it already never proposes the value), `scripts/clinician_review_sheet.py`, `docs/launch/clinician-review.md`, `apps/api/tests/db/test_migrations.py`

**Interfaces:**
- `Category.SUPPLEMENT = "supplement"`. Products check constraint `ck_products_category` gains `'supplement'` (migration `0006`, `down_revision = "0005_plan9_user_types"`; the downgrade maps `supplement` rows to `general` first). `ProductCreate.category` Literal gains `"supplement"`.
- **Detection (never the LLM):**
  - The user picks "Supplement (protein powder, whey, health supplement)" on the confirm screen. The normaliser never proposes or preselects it.
  - Or Open Food Facts tags: `off_mapping.SUPPLEMENT_TAGS = ("en:dietary-supplements", "en:protein-powders", "en:bodybuilding-supplements", "en:whey-proteins", "en:sports-nutrition-supplements")`, checked before every other category. Add the comment "verify each tag against the OFF taxonomy" and a test per tag.
- `compute_nutriscore`: a supplement → `NutriScoreResult(None, None, False, False, "not_scored_supplement")`.
- Everything else still runs: allergens, diet, veg mark, high-in, hidden sugars, claims, custom alerts, condition rules, and protein facts.
- New member reasons:

```yaml
supplements:   # PENDING CLINICIAN REVIEW (P9-R10). ICMR-NIN Dietary Guidelines 2024 discourage
               # protein supplements; a child caution and an infant avoid are SmartNutri working values.
  child_max_age: 18          # infant.max_age <= age < 18 -> child_status
  child_status: caution      # reason supplement_child
  infant_status: avoid       # age < conditions.infant.max_age -> reason supplement_infant
```

  Unknown age → the existing `age_unknown` (`unknown`): the supplement rule always flags at the most protective age.
- **Never suggested:**
  - A supplement source → `AlternativesOut(items=[], reason="source_supplement")` (new reason literal).
  - Supplement candidates are dropped in `rank_alternatives` and `rank_alternatives_by_protein`.
  - `sort=protein` search drops supplements.
  - Relevance search still shows them, with no grade.

- [ ] **Step 1: Write failing tests** (`test_supplements.py`):
  - `test_supplement_has_no_grade_reason_not_scored`
  - `test_whey_flags_milk_for_milk_allergic_member` (avoid)
  - `test_supplement_child_caution` (age 9) and `test_supplement_teen_caution` (age 16)
  - `test_supplement_infant_avoid`
  - `test_supplement_age_unknown_is_unknown`
  - `test_adult_supplement_not_ok_on_grade_alone` (a status comes from the other rules only)
  - `test_weight_loss_member_no_nutriscore_low_for_supplement`
  - `test_off_supplement_tags_map_to_supplement` (parametrised)
  - `test_normalizer_never_proposes_supplement`
  - `test_claims_still_checked_on_supplement`
  - `test_supplement_alternatives.py`: `test_supplement_source_returns_source_supplement`, `test_supplement_never_a_candidate` (both sorts), `test_protein_search_excludes_supplements`
  - `test_migrations.py`: `test_supplement_category_downgrades_cleanly`
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement** the data first, then the code. Check the migration down and up. Regenerate the clinician sheet with the new `supplements` units ("years (maximum age, exclusive)") and the questions:
  - Is caution right for 2–17?
  - Is avoid right under 2?
  - Should adults with conditions get a caution?
- [ ] **Step 4: Run them to verify they pass**, plus `uv run pytest -q`, then `uv run python scripts/generate_fixture_expectations.py` (no existing fixture is a supplement: no diff).
- [ ] **Step 5: Commit** with message `feat(scoring): supplements are not graded, still checked, caution for children, never suggested (migration 0006)`.
- [ ] **Step 6: Safety gate.** Run `nutrition-safety-reviewer` on the diff.
- USER: apply migration 0006 to dev.

---

### Task 8 (API + shared): Contract, i18n, the mode table and shared fixtures

**Files:**
- Generated: `packages/api-contract/openapi.json`, `packages/api-contract/dart/**`, `packages/api-contract/ts/**`
- Create: `packages/test-fixtures/modes/layouts.json`, `packages/test-fixtures/protein/price_per_scoop.json`, `packages/test-fixtures/members/build_muscle_adult.json`, `packages/test-fixtures/products/whey_powder.json`, `apps/api/tests/fixtures/test_mode_layouts.py`
- Modify: `packages/i18n/messages/{en,hi,mr}.json`, `packages/i18n/NATIVE_REVIEW.md`, `packages/test-fixtures/README.md`, regenerated `packages/test-fixtures/{expected,responses,drafts}/`

**Interfaces:**

`packages/test-fixtures/modes/layouts.json` is **hand-written and reviewed, and it is the single source of truth** for tabs, Home cards and More. Both clients mirror it as constants, and their tests compare the constants with the file. The API test checks that `priority` equals `USER_TYPE_PRIORITY` and that `default_type` equals `DEFAULT_TYPE`.

```json
{
  "priority": ["allergy_diet", "health_condition", "family", "weight_loss", "gym", "eat_better"],
  "default_type": "eat_better",
  "destinations": ["home", "scan", "history", "family", "protein", "compare", "search", "profile", "how_we_score"],
  "always_first_card_when_any_member_has_allergens": "allergy_check",
  "modes": {
    "health_condition": {"tabs": ["home", "scan", "history", "family", "profile"],
                         "home_cards": ["today_sugar_salt", "claims_tip", "not_covered", "recent_scans"]},
    "family":           {"tabs": ["home", "scan", "family", "history", "profile"],
                         "home_cards": ["family_strip", "weekly_family", "recent_scans"]},
    "weight_loss":      {"tabs": ["home", "scan", "history", "protein", "profile"],
                         "home_cards": ["today_protein", "today_sugar_salt", "recent_scans"]},
    "gym":              {"tabs": ["home", "scan", "protein", "compare", "profile"],
                         "home_cards": ["today_protein", "protein_swaps", "protein_claims_tip", "recent_scans"]},
    "allergy_diet":     {"tabs": ["home", "scan", "family", "search", "profile"],
                         "home_cards": ["allergy_check", "unknown_explainer", "recent_scans"]},
    "eat_better":       {"tabs": ["home", "scan", "compare", "history", "profile"],
                         "home_cards": ["custom_alerts_setup", "claims_tip", "recent_scans"]}
  }
}
```

- **More** = `destinations` minus the mode's `tabs` (in `destinations` order). For example, gym's More is History · Family · Search · How we score.
- Every mode has `scan` at index 1 and `profile` last. The scan CTAs (barcode, label photo, manual) always sit above the cards and are not cards.
- **Home cards** (all data from existing routes; clients never compute verdicts or limits):

| Card | Data | Notes |
|---|---|---|
| `allergy_check` | `members_list` | who has which allergy; "Unknown means we couldn't check, so it is never marked safe"; a CTA to add allergies when none are set (allergy mode only) |
| `today_sugar_salt` | `meals_summary` (primary member, day) | bands from tokens; `unknown` is grey |
| `today_protein` | `meals_summary` (primary, day) | total vs `limits.protein_target_g`, `protein_left_g`; "no target" note (adults with weight and birth year); kcal shown without a target |
| `protein_swaps` | link | "Find higher-protein options" → Protein screen |
| `protein_claims_tip`, `claims_tip` | static copy | "We check protein claims against the nutrition table" / "Sugar-free? We check claims" |
| `not_covered` | static copy | "Not covered yet: thyroid, cholesterol, kidney disease, pregnancy" |
| `family_strip` | `members_list` | members + "Add member" |
| `weekly_family` | `meals_week_counts` | counts only |
| `unknown_explainer` | static copy | why `unknown` is not safe |
| `custom_alerts_setup` | `members_list` | CTA to switch on alerts |
| `recent_scans` | existing recent list | always last |

`packages/test-fixtures/protein/price_per_scoop.json` holds hand-written cases for the client-only arithmetic `price_per_scoop = price × serving_size_g / pack_size_g`, rounded to 2 dp. The result is `null` when any input is missing or ≤ 0, or when `serving_size_g` is null. For example `{"price": 2499, "pack_size_g": 1000, "serving_size_g": 33, "expected": 82.47}`.

Fixtures:
- `members/build_muscle_adult.json`: age 25, goal `build_muscle`.
- `products/whey_powder.json`: synthetic. Category `supplement` if Task 7 landed, else `general` (Task 7 then flips it). Ingredients whey protein concentrate, cocoa, soy lecithin, sucralose. Claims "24g protein per scoop", "100% whey". Serving 33 g.
- Regenerate: `uv run python scripts/generate_fixture_expectations.py --write`, `scripts/export_fixture_responses.py`, `scripts/export_draft_fixtures.py`, `scripts/export_meal_fixtures.py`.

i18n (en, hi, mr; hi/mr machine drafts listed in `NATIVE_REVIEW.md` under "Plan 9"):
- `user_types.*`:
  - the title "What brings you to SmartNutri?"
  - the 6 tile titles and subtitles (the health tile names diabetes, prediabetes, PCOS and BP)
  - "Pick up to 3", "Skip for now"
  - the follow-up questions and options
  - the "not covered yet" list
  - "You can change this in Profile"
  - the consent note
  - the pre-fill review screen ("Add these to your profile?", per-field lines, goal choice)
- `modes.*`: the 6 mode names, the switcher, "More".
- `nav.protein`, `nav.compare`, `nav.search`, `nav.more`, `nav.how_we_score`.
- `home.cards.*` for every card above.
- `protein.*`:
  - progress, guide wording ("Daily protein guide: {target} g, based on {per_kg} g per kg. Information, not medical advice.")
  - left today, no-target note, kidney note
  - swaps, "higher protein" sort, per serving / per 100 g / per 100 kcal
  - price per scoop and its "never saved" note
- `goal.build_muscle`.
- Reasons and labels:
  - `reason.supplement_child`, `reason.supplement_infant`
  - `nutriscore.not_scored_supplement`
  - `claim.protein_amount`, `claim.whey_only`, `claim.whey_protein` and their reason codes (`below_claimed`, `other_protein_source`, `whey_not_listed`)
  - `report.sweeteners`, `report.caffeine`
  - `alternatives.reason.source_supplement`, `alternatives.reason.source_protein_unknown`
  - `category.supplement`
- `error.user_type_not_selected`, `error.follow_up_without_type`, `error.user_types_not_found`.
- Copy rules: no "manage", "treat", "cure", "reverse", "you need", doses or brands.
- `tests/unit/test_error_codes_i18n.py` and `test_i18n_reason_params.py` must pass.

- [ ] **Step 1: Write failing tests.**
  - `tests/fixtures/test_mode_layouts.py`:
    - `test_priority_matches_api`
    - `test_every_mode_has_five_tabs_scan_second_profile_last`
    - `test_every_destination_reachable_in_every_mode` (tabs ∪ More == destinations)
    - `test_recent_scans_last`
  - Plus `test_copy_has_no_medical_claims_or_doses`: scan the new en/hi/mr strings for the banned words of the explanation filter and the NOT-doing list.
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement.**
  - Export `openapi.json` (`cd apps/api && uv run python -m scripts.export_openapi > ../../packages/api-contract/openapi.json`) and regenerate both clients (the justfile `contract` lines).
  - Add the strings, then `pnpm --filter @smartnutri/i18n build` and `cd apps/app && flutter gen-l10n`.
  - Write the fixtures and run the regeneration scripts.
- [ ] **Step 4: Run them to verify they pass**, then `uv run pytest -q`, `dart analyze` in `packages/api-contract/dart`, and the minimal compile fixes in both clients so that `flutter analyze` and `npx tsc --noEmit` pass.
- [ ] **Step 5: Commit** with message `chore(contract): user types, protein guide, mode table, i18n and fixtures`.
- [ ] **Step 6: Safety gate.** `nutrition-safety-reviewer` reviews the new expected verdicts, copy and the mode table (CODEOWNERS: `packages/test-fixtures`).

---

### Task 9 (Android): Onboarding: type picker, follow-up, pre-fill review, Profile *(parallel with Task 12)*

Use the `flutter-feature` skill.

**Files:**
- Create: `apps/app/lib/features/user_types/{data/user_types_repository.dart, domain/user_types.dart, presentation/{type_picker_screen.dart, follow_up_screen.dart, prefill_review_screen.dart, user_types_providers.dart}}`, `apps/app/test/features/user_types/*_test.dart`, `apps/app/test/support/fake_user_types.dart`
- Modify: `apps/app/lib/core/router/app_router.dart`, `apps/app/lib/features/settings/presentation/profile_screen.dart`, `apps/app/test/core/router_test.dart`

**Interfaces:**
- `userTypesProvider` (`AsyncNotifier<UserTypesOut>`) over `me_user_types_get` / `_put` / `_set_active`. `userTypesStatusProvider`: `unknown | unanswered | answered`.
- Redirect, after the terms check:
  - signed in + terms OK + `unanswered` → `/welcome`.
  - `/welcome` (and its children) is reachable only while unanswered or with `?edit=1`.
  - While loading or on error, the app goes on (like the terms check). `/profile`, `/terms`, `/consent` and `/goodbye` are exempt.
- Routes:
  - `/welcome`: picker. 6 tiles, multi-select, at most 3 (a 4th tap shows `user_types.max_three`). "Continue" and "Skip for now".
  - `/welcome/follow-up`: at most one screen per chosen type, in priority order:
    - health → condition chips
    - family → who (children, parents, partner, others), then an optional "Add a family member" → `/family/new`
    - gym → build muscle / lose fat / stay fit
    - allergy → allergen chips (the 11 canonical) + diet
    - eating better → alert toggles
    - weight loss → none
  - `/welcome/review`: shown only when `prefill.changes` is non-empty or `goal_choice` is set.
- **Consent:** if a health tile or health follow-up is chosen and `health_data` is not active, open the existing `consent_sheet.dart` **in context** before the PUT. If the user declines, those tiles are deselected with the note `user_types.consent_declined_note`, and the rest is saved.
- **Review:** every change is a checkbox showing current → new (allergens and conditions show only what is added).
  - Ticked by default only when the user's own follow-up chose it. A goal conflict is a radio list (weight loss / build muscle / neither, default neither).
  - "Save to my profile" sends **one** `members_update` with the confirmed `value`s. "Not now" sends nothing.
  - A 403 from the members PATCH goes through the existing consent flow.
- **Profile:** a row "What brings you here" (types) → `/welcome?edit=1` (the same screens, prefilled). The mode switcher row is added in Task 10.
- **No analytics** call anywhere in this feature.

- [ ] **Step 1: Write failing widget and router tests:**
  - `max three selections`
  - `skip stores empty types and lands on home`
  - `terms then picker redirect` (and no picker once answered)
  - `health tile without consent opens consent sheet; declined drops it with note`
  - `defaults are not saved until confirmed` (no members PATCH before "Save")
  - `only ticked changes are sent` (the fake repo records the body)
  - `goal conflict defaults to neither`
  - `editing types in profile never sends a members PATCH by itself`
  - `no analytics events` (the fake analytics records nothing)
  - `all copy from l10n` (no hard-coded strings; existing lint/test pattern)
- [ ] **Step 2: Run them to verify they fail.** `cd apps/app && flutter test test/features/user_types test/core/router_test.dart`.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them to verify they pass**, plus `flutter analyze && flutter test`.
- [ ] **Step 5: Commit** with message `feat(app): user-type picker after terms, follow-up and confirm-only pre-fill`.

---

### Task 10 (Android): Focused-mode shell, Home cards, More and the mode switcher *(parallel with Task 13)*

Use the `flutter-feature` skill.

**Files:**
- Create: `apps/app/lib/features/modes/{mode_layouts.dart, mode_providers.dart, presentation/{mode_switcher.dart, more_menu.dart}}`, `apps/app/lib/features/home/presentation/cards/*.dart`, `apps/app/lib/features/protein/presentation/protein_screen.dart` (progress only; Task 11 adds swaps), `apps/app/test/features/modes/*_test.dart`, `apps/app/test/features/home/home_cards_test.dart`
- Modify: `apps/app/lib/shared/widgets/app_shell.dart`, `apps/app/lib/core/router/app_router.dart`, `apps/app/lib/features/home/presentation/home_screen.dart`, `apps/app/lib/features/settings/presentation/profile_screen.dart`, `apps/app/test/core/shell_navigation_test.dart`

**Interfaces:**
- `mode_layouts.dart`: `const kModeLayouts`, `kDestinations` and `kTypePriority`, mirroring `packages/test-fixtures/modes/layouts.json`. A test loads the JSON and compares.
- `activeModeProvider` = `userTypesProvider.active_type`, falling back to `eat_better` while loading, on error or offline (the last value is cached in memory).
- **Shell:**
  - Shell branches become `/home`, `/history`, `/family`, `/protein` (new) and `/profile`.
  - `scan`, `compare` and `search` stay full-screen routes. Their tabs **push** them, as Scan does today. `/compare` with no `a`/`b` shows its "pick two products" empty state (add one if missing).
  - `AppShell` builds its 5 destinations from `kModeLayouts[mode].tabs`. Index 1 is always the brand-coloured Scan.
  - A branch that is not in the current bar (for example `/family` in gym mode, opened from More) shows the bar with no tab selected; if the Flutter version needs an index, Home is shown as selected.
- **More** (`more_menu.dart`): a bottom sheet from a "More" button in the Home header, and the first section of Profile. It lists `destinations − tabs` with icons and l10n labels, plus How we score.
- **Mode switcher** (`mode_switcher.dart`): a segmented control at the top of Home and a row in Profile, shown only when `types.length >= 2`. It calls `me_user_types_set_active` and switches optimistically, rolling back on error.
- **Home:** the scan CTAs (unchanged), then `allergy_check` if any member has an allergen and the mode is not `allergy_diet` (P9-R7), then the mode's `home_cards` in order. Card widgets read existing providers (`membersProvider`, the meals summary provider for the primary member). They render API values only. Bands use tokens; `unknown` is grey, never green.
- **Protein screen (progress part):** a member picker (primary by default).
  - Today's protein vs target, and `protein_left_g`, using the guide wording.
  - The no-target note (needs weight and birth year, 18+) with a link to the member form.
  - The kidney note and the disclaimer.

- [ ] **Step 1: Write failing tests:**
  - `layouts match shared fixture`
  - `each mode shows its five tabs with scan second` (6 cases)
  - `more lists every destination not in the bar` (6 cases)
  - `every destination reachable in every mode` (tap through bar or More → the route renders)
  - `switcher hidden with one type, shown with two, calls set_active`
  - `home cards follow layout order`
  - `allergy_check first in every mode when a member has allergens`
  - `unknown protein band is never green`
  - `result screen identical in every mode`: pump `ResultScreen` from `responses/analyze/cola.json` and `responses/analyze/sf_biscuit.json` under each of the 6 modes and compare the verdict section's semantics tree (statuses, reasons, allergen rows, disclaimer). They must be equal.
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them to verify they pass**, plus `flutter analyze && flutter test`.
- [ ] **Step 5: Commit** with message `feat(app): focused modes with per-type tabs, home cards, More and mode switcher`.

---

### Task 11 (Android): Protein guide screens *(parallel with Task 14)*

Use the `flutter-feature` skill.

**Files:**
- Modify: `apps/app/lib/features/protein/presentation/protein_screen.dart`, `apps/app/lib/features/product/presentation/{alternatives_section.dart, compare_screen.dart, search_screen.dart, product_discovery_providers.dart}`, `apps/app/lib/features/analysis/presentation/result_screen.dart` (+ a `protein_facts.dart` widget), `apps/app/lib/shared/widgets/nutri_score_chip.dart`, `apps/app/lib/features/members/presentation/member_form_screen.dart` (goal "Build muscle"), `apps/app/lib/features/scan/presentation/confirm_screen.dart` (category "Supplement", never preselected; only if Task 7 landed)
- Create: `apps/app/lib/features/protein/domain/price_per_scoop.dart`, `apps/app/test/features/protein/*_test.dart`

**Interfaces:**
- **Result screen:** a protein facts row from `report.protein` (per serving, per 100 g, per 100 kcal; null shows "—", never 0), "Contains sweeteners: …" and "Contains caffeine: …" from the report, and the new claim results in the existing claims section. A supplement shows `nutriscore.not_scored_supplement` instead of a grade. The verdict section is untouched.
- **Protein screen (swaps part):**
  - Today's logged items for the member (`meals_list`).
  - Each item has "Higher-protein options" → `products_alternatives[_by_barcode]?sort=protein&member_id=…`.
  - A search box that calls `products_search?sort=protein&member_id=…`.
  - Lists show the member status badge from the API. `avoid` never appears (the API drops it; the client does not filter).
- **Alternatives section:** a "Higher protein" toggle (sort=protein) next to the default.
- **Search screen:** a sort toggle (relevance / higher protein).
- **Compare:**
  - New rows: protein per serving, protein per 100 kcal, sugars per serving, each with the better-side marker from `better`.
  - **Price per scoop:** per side, two optional number fields (pack price in ₹, pack size in g). It shows `price_per_scoop(price, packSizeG, servingSizeG)` (pure, in `domain/`) with the note "Only on this phone. Never saved." State lives in the widget only: no provider persistence, no drift, no shared prefs, no request body, no route param, no analytics.

- [ ] **Step 1: Write failing tests:**
  - `protein facts row shows dash for null`
  - `supplement shows not graded label`
  - `price per scoop matches shared fixture` (all cases in `protein/price_per_scoop.json`)
  - `price is never persisted or sent` (after typing a price, the fake API client and storage have recorded nothing new; rebuilding the screen clears it)
  - `higher protein toggle requests sort=protein with member`
  - `search protein sort`
  - `protein screen lists swaps for logged items`
  - `compare shows protein rows and markers`
  - `member form offers build muscle`
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them to verify they pass**, plus `flutter analyze && flutter test` and a debug APK build.
- [ ] **Step 5: Commit** with message `feat(app): protein guide: facts on scan, swaps, higher-protein sort, compare and price per scoop`.

---

### Task 12 (Web): Onboarding: type picker, follow-up, pre-fill review, Profile *(parallel with Task 9)*

Use the `web-feature` skill.

**Files:**
- Create: `apps/web/src/features/user-types/{api/userTypes.ts, hooks/useUserTypes.ts, components/{TypePicker.tsx, FollowUp.tsx, PrefillReview.tsx, UserTypesGate.tsx}}`, `apps/web/src/app/[locale]/(app)/welcome/page.tsx`, `apps/web/tests/features/user-types/*.test.tsx`, `apps/web/e2e/user-types.spec.ts`
- Modify: `apps/web/src/app/[locale]/(app)/layout.tsx` (`ConsentGate` → `UserTypesGate` → children), `apps/web/src/app/[locale]/(app)/profile/page.tsx`

**Interfaces:** the same behaviour as Task 9.
- `UserTypesGate` renders after the terms step. While `answered === false` it redirects to `/[locale]/welcome`. It exempts `profile` and `welcome`, and it lets the page render while loading or on error.
- The consent step uses the existing `ConsentDialog`.
- Pre-fill sends one `members_update` with the confirmed `value`s.
- No `track()` calls.

- [ ] **Step 1: Write failing Vitest tests:** the same ten cases as Task 9, named identically.
  - Playwright `user-types.spec.ts`: sign in → accept terms → pick "Gym and fitness" + "Food allergy or special diet" → follow-ups (build muscle; milk) → review shows goal and allergen unticked/ticked as specified → Save → Home is in the `allergy_diet` mode (priority), and the switcher shows both.
- [ ] **Step 2: Run them to verify they fail.** `pnpm --filter @smartnutri/web test user-types`.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them to verify they pass**, plus `pnpm lint && npx tsc --noEmit && pnpm test` and the e2e spec.
- [ ] **Step 5: Commit** with message `feat(web): user-type picker after terms, follow-up and confirm-only pre-fill`.

---

### Task 13 (Web): Focused-mode shell, Home cards, More and the mode switcher *(parallel with Task 10)*

Use the `web-feature` skill.

**Files:**
- Create: `apps/web/src/features/modes/{layouts.ts, useActiveMode.ts, components/{ModeSwitcher.tsx, MoreMenu.tsx}}`, `apps/web/src/features/home/components/cards/*.tsx`, `apps/web/src/app/[locale]/(app)/protein/page.tsx`, `apps/web/src/features/protein/components/ProteinProgress.tsx`, `apps/web/tests/features/modes/*.test.tsx`, `apps/web/tests/features/home/cards.test.tsx`
- Modify: `apps/web/src/components/shell/{AppNav.tsx, AppShell.tsx}`, `apps/web/src/app/[locale]/(app)/home/page.tsx`, `apps/web/src/app/[locale]/(app)/profile/page.tsx`, `apps/web/tests/shell.test.tsx`, `apps/web/tests/home.test.tsx`

**Interfaces:** the same behaviour as Task 10.
- `layouts.ts` mirrors `layouts.json`; a test imports the JSON and compares.
- `AppNav` builds `TABS` from the active mode:
  - The "bar" variant shows the 5 tabs.
  - The "rail" variant (desktop) shows the 5 tabs, then a "More" group with the rest, so nothing is hidden on wide screens either.
  - Active-tab matching prefers an exact tab (in gym mode `/compare` lights Compare). Otherwise it falls back to the existing `also` rules (result/product → Scan).
- `/[locale]/protein`: the progress part, as on Android.
- All existing routes stay.

- [ ] **Step 1: Write failing Vitest tests:** the same nine cases as Task 10, named identically. The invariance test renders the result view from `responses/analyze/{cola,sf_biscuit}.json` under each mode and compares the verdict region's accessible tree.
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them to verify they pass**, plus lint, typecheck and the full web suite.
- [ ] **Step 5: Commit** with message `feat(web): focused modes with per-type tabs, home cards, More and mode switcher`.

---

### Task 14 (Web): Protein guide screens *(parallel with Task 11)*

Use the `web-feature` skill.

**Files:**
- Create: `apps/web/src/features/protein/{lib/pricePerScoop.ts, components/{ProteinSwaps.tsx, ProteinFacts.tsx}}`, `apps/web/tests/features/protein/*.test.tsx`
- Modify: `apps/web/src/features/product/components/{Alternatives.tsx, SearchBox.tsx, CompareTable.tsx}` (or the existing names), `apps/web/src/features/analysis/components/*` (protein facts, sweeteners, caffeine, not-graded supplement), `apps/web/src/components/ui/NutriScoreChip.tsx`, `apps/web/src/features/members/components/*` (goal "Build muscle"), `apps/web/src/features/scan/components/*` (confirm category "Supplement", only if Task 7 landed), `apps/web/src/app/[locale]/(app)/protein/page.tsx`

**Interfaces:** the same behaviour as Task 11.
- Price per scoop lives only in React component state. It is never in `localStorage`, the URL, a query key, a request or `track()`.
- The public product page `/p/[barcode]` also shows protein facts and the not-graded label (generic facts only, never personal).

- [ ] **Step 1: Write failing Vitest tests:** the same nine cases as Task 11, named identically, plus `public page shows protein facts without member data`.
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them to verify they pass**, plus lint, typecheck, the full suite and `pnpm build`.
- [ ] **Step 5: Commit** with message `feat(web): protein guide: facts on scan, swaps, higher-protein sort, compare and price per scoop`.

---

### Task 15: Slice gate: safety review and parity

**Files:**
- Modify: `docs/FEATURE_PARITY.md` (F18 user types, F19 focused modes, F20 protein guide), `CONTEXT.md` (status)

- [ ] **Step 1: Run everything.** API `uv run pytest -q`, ruff check + format; `dart analyze` (contract); `flutter analyze && flutter test`; web `pnpm lint && npx tsc --noEmit && pnpm test` and `pnpm e2e`; `gitleaks protect --staged --no-banner` before each commit. Expected: all green.
- [ ] **Step 2: Run the `nutrition-safety-reviewer`** over the whole slice. Check every Review Focus item, plus:
  - en/hi/mr copy for medical claims, doses, brands, creatine or steroids, and "you need X g"
  - the protein-target wording
  - the supplement statuses
  - the regenerated `expected/` and `responses/`
  - unknown never green on the new cards and screens

  Fix blocking issues in the owning task's files and re-run their tests.
- [ ] **Step 3: Check parity.** The shared fixtures (`modes/layouts.json`, `protein/price_per_scoop.json`, `expected/`, `responses/`) pass on API, Android and web.
  - Mark F18–F20 🟡 (code complete, waiting on USER: the dev deploy with migrations 0005/0006, the clinician review of the new thresholds, the native review of the new strings).
  - Mark ✅ only after those.
- [ ] **Step 4: Commit** with message `docs: plan 9 parity status`.

**USER steps after this plan:**
- Apply migrations 0005 and 0006 on dev.
- Clinician review of `build_muscle` 1.6 g/kg, the protein claim tolerance and the supplement statuses (`docs/launch/clinician-review.md`).
- Native hi/mr review of the Plan 9 strings.
- A manual check on a phone and in a browser: the picker after terms, each of the 6 modes, and one whey label scan.
