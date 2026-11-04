# ADR 0019: User types and focused modes are presentation, never scoring input

- **Status:** Accepted
- **Date:** 2026-11-04

## Context

SmartNutri serves people with quite different jobs: people checking foods against diabetes, prediabetes, PCOS or BP; parents shopping for children and elderly parents; people losing weight; gym users; people with food allergies or a special diet; and people who just want to eat better. Plans 1–8 built everything as one app with one Home and one tab bar (Home · Scan · History · Family · Profile). New users have to find the parts that matter to them on their own.

On 2026-11-04 the user made eight binding decisions (Plan 9, `docs/superpowers/plans/2026-11-04-plan-9-personas.md`):
- six user types, up to 3 per account, stored on the account;
- asked right after the Terms screen, with one short follow-up per type and "Skip for now";
- a focused mode per type, with its own Home and tab bar;
- a gym protein guide with a `build_muscle` goal and a protein target;
- supplements not graded.

This is a health app. A user type that changed a verdict would make two people with identical health profiles see different answers, depending on which tile they tapped. Some types (a health condition, weight loss, an allergy) reveal health data, so they fall under DPDP and the `health_data` consent. Hiding screens per type risks an allergic child's information being out of sight.

## Decision

**A user type is a presentation preference. It never reaches the rules engine and never changes a verdict.** It decides the layout (tabs, Home cards, the More menu), the defaults offered for confirmation, and copy. Verdicts still come only from `app.scoring.analyze()` and each member's own fields (ADR 0005).

The specifics:

1. **Storage.**
   - A new account-owned table, `account_user_types` (migration `0005_plan9_user_types`), holds up to 3 types, the follow-up answers and the active mode, one row per account.
   - It has ENABLE + FORCE row-level security, an owner policy, SELECT-only for `authenticated`, and it is in `ACCOUNT_OWNED_TABLES`, so account deletion erases it.
   - Routes: `GET`/`PUT /v1/me/user-types` and `PATCH /v1/me/user-types/active`.
2. **Consent.**
   - Writing `health_condition`, `weight_loss` or `allergy_diet`, or a health follow-up (conditions, allergens, diet), needs an active `health_data` consent (`403 consent_required` otherwise).
   - Switching the active mode needs none.
   - Withdrawal keeps the stored types, and the layout still follows them. This mirrors ruling G1 in ADR 0018 (stored data keeps working; nothing is erased on withdrawal).
3. **Pre-fill is confirm-only.**
   - The API suggests changes to the account holder's own member fields (conditions, allergens, diet, goal, alerts) from the types and follow-ups.
   - Suggestions only add. They never remove a value and never relax a diet.
   - The client applies only what the user ticks, through the existing `PATCH /v1/members/{id}` and its `health_data` check.
   - Nothing health-related is set silently.
4. **Focused modes reorder and refocus; they never delete.**
   - Each of the 6 types has a 5-tab bar with Scan always second, and its own Home cards.
   - Every other destination is in a "More" menu, one tap from Home and at the top of Profile.
   - All routes stay registered.
   - When any member has an allergen, the allergy card is first on Home in every mode.
   - Scan, the result screen, verdicts and allergy checks are identical in every mode, and a client test proves it.
   - The mode table is one shared data file, `packages/test-fixtures/modes/layouts.json`, that both clients mirror and test against.
5. **Never in analytics or prompts.** No type, count, follow-up or "skipped" flag goes to PostHog or Sentry. No type goes into an LLM prompt.
6. **The gym protein guide goes through the rules engine, as data.**
   - `build_muscle` is a member goal. It adds at most an `ok`-level `good_protein_density` reason, never a caution or avoid.
   - Its protein target (1.6 g/kg, adults with a weight only) and the supplement statuses live in `thresholds.yaml`, PENDING CLINICIAN REVIEW.
   - Supplements are detected only from the user-confirmed category or Open Food Facts tags, never by the LLM. They get no Nutri-Score grade, and they are never suggested as alternatives.

## Consequences

**Easier:**
- New users see the features that fit them first.
- Gym users get protein-first information without a separate app.
- Android and web share one mode table, so they cannot drift apart.

**Harder:**
- There are six layouts to test on two clients. The shared layout fixture and the reachability and invariance tests keep this manageable.
- The account now stores a health-revealing preference next to the member fields. It is gated by `health_data`, erased with the account, and kept out of analytics. The lawyer review (ADR 0018) should cover it.
- The protein target, the claim tolerance and the supplement statuses need clinician sign-off before launch.

**Risks:**
- Users may read a mode as a medical programme. The copy says "information, not medical advice" and never "manage", "treat", "you need X g", a dose or a brand.
- Moving Family out of the tab bar in some modes could hide it. More and the mode-independent allergy card address this.

**Follow-up:**
- A higher protein target for weight loss.
- Kidney disease and pregnancy, which stay out (spec §2).
- Amino-spiking detection and price-per-protein from real prices (v2).
