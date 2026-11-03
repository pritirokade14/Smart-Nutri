# packages/i18n

**Every user-facing string for both clients lives here**, in English, Hindi and Marathi. One source means the Android app and the web app always say the same thing.

## Contents

```
messages/
  en.json   # source language, every key must exist here first
  hi.json   # हिंदी
  mr.json   # मराठी
scripts/    # build-arb.mjs (JSON → Flutter ARB), check-keys.mjs (consistency checks)
```

Keys are nested by feature, e.g. `scan.confirm.title`, `verdict.status.avoid`, `reason.sugar_high`.

- API **reason codes** map to `reason.<code>` (member verdicts) and `claim_reason.<code>` (front-of-pack claims). Every code the rules engine can emit must have a key in all three files.
- Placeholders use ICU syntax (`{name}`, `{count, plural, ...}`), which both next-intl and Flutter ARB understand.

## Rendering reasons (contract with the rules engine)

A reason arrives as `{code, severity, params}`. The engine is the source of truth for `params`; `apps/api/tests/unit/test_i18n_reason_params.py` runs the real engine and fails if a `reason.*`, `reason_variant.*` or `claim_reason.*` message uses an argument the engine does not send **on every emission** routed to it (next-intl throws `MissingValueError` and Flutter requires every argument).

**1. Pick the key.** Use `reason.<code>`, except for these variants:

| Code | Condition on `params` | Key to use instead |
|---|---|---|
| `nutrient_missing` | `reason == "low_confidence"` (only sent then) | `reason_variant.nutrient_missing_low_confidence` |
| `diet_violation` | `ingredients` is empty (brown non-veg mark, no listed non-veg ingredient) | `reason_variant.diet_violation_mark_only` |
| `custom_alert` | `ingredients` is empty (only the Open Food Facts sweetener flag matched; `alert` is `artificial_sweetener`). The variant says "sweeteners": the flag also covers stevia and polyols | `reason_variant.custom_alert_flag_only` |

Claim results use `claim_reason.<reason_code>`; the claim itself is shown next to it via `claim.<claim>`.

**2. Map code-valued params before interpolating.** These params are codes, not text:

| Param | Map through | Notes |
|---|---|---|
| `{diet}` | `diet.<code>` | |
| `{allergen}` | `allergen.<code>` | If no key exists, it is the member's own wording (an allergen we don't recognise): show it as-is. |
| `{condition}` | — | `condition_unrecognised` sends the member's own wording: show it as-is. Use `condition.<code>` wherever a canonical condition code is shown. |
| `{claim}` | `claim.<code>` | |
| `{nutrient}` | `nutrient.<code>` | Codes: `energy_kcal`, `protein_g`, `carbs_g`, `sugars_g`, `fat_g`, `sat_fat`, `salt`, `sodium_mg`, and `serving_size_g` (only in `claim_reason.nutrient_missing` for a per-serving protein claim). Labels are lower-case because they sit mid-sentence. |
| `{high_in}` | `nutrient.<code>` for each item, then join | A list of codes (`sat_fat`, `salt`). Not `high_in.*`, whose labels are whole phrases ("High in salt"). |
| `{alert}` | `alert.<code>` | A member ingredient alert: `palm_oil`, `maida`, `added_sugar`, `artificial_sweetener`, `msg`. Labels are lower-case because they sit mid-sentence. |
| `{alerts}` | `alert.<code>` for each item, then join | `custom_alert_unknown`: the enabled alerts that could not be checked, in that fixed order. |

**3. Lists.** `{ingredients}` (and `{high_in}` after mapping) is a list: join lists with ", " (comma + space) in every locale (no `Intl.ListFormat`, no locale conjunction) and pass the result as one string.

**4. Numbers.** Numeric params (`sugars_g`, `salt_g`, `carbs_g`, `energy_kcal`, `pct`, `limit_g`, `value`, `limit`, …) are formatted by the client for the locale and passed as strings (ARB type `String`). Only `plural` arguments are numeric (ARB type `num`).

**5. Basis.** Sugar, salt and energy values in `sugar_*`, `salt_*`, `energy_dense`, `child_salt_high`, `infant_*_high` and `claim_reason.exceeds_limit` are always per 100 g (food) or per 100 ml (drinks); the messages say "per 100 g/ml". Where the engine sends `basis`, it is `per_serving` or `per_100g`, used as an ICU `select` (`carbs_per_serving_high`, `child_sugar_*`, and `claim_reason.below_claimed`, where `value` and `claimed` are grams of protein). `claim_reason.below_minimum` is only emitted for protein claims (`value`/`limit` are protein's % of energy); the contract test fails if that changes.

**6. Params the messages don't use** (e.g. `rule`, `mark`, `protein_g_per_100kcal`) are for analytics and future copy; ignore them.

## Checks (`pnpm --filter @smartnutri/i18n check`)

`scripts/check-keys.mjs` fails on: missing or extra keys vs `en`; invalid ICU; empty translations; a `select`/`plural` without an `other` branch; a different set of ICU arguments, or a different kind (plain vs `select` vs `plural`) for the same argument, between locales; a different set of `select` cases (or plural `=N` cases) between locales; unknown plural keywords; and an apostrophe directly before `{`, `}`, `#` or `|` (quoting differs between next-intl and Flutter).

## Consuming

| Client | How |
|---|---|
| Web (`apps/web`) | next-intl imports `messages/<locale>.json` **directly**. No generation step. |
| Android (`apps/app`) | `just i18n` generates `apps/app/lib/core/l10n/app_{en,hi,mr}.arb` (nested keys flattened to camelCase, e.g. `scanConfirmTitle`). Flutter `gen-l10n` then builds the Dart accessors. |

## Rules

- **Add every key to all three files in the same change.** CI checks that the key sets match.
- Never edit the generated ARB files in `apps/app`. Edit here and run `just i18n`.
- Health wording ("Information, not medical advice", verdict labels) must be reviewed by a native speaker before release. Mark unreviewed translations in the PR. Open items are tracked in [NATIVE_REVIEW.md](NATIVE_REVIEW.md).
- Adding a reason code: add `reason.<code>` in all three files using only params the engine always sends for that code, then run the API contract test.
- No HTML in messages. Use rich-text tags supported by both clients only if needed.
