---
name: scoring-rule
description: Use when adding or changing anything in apps/api/app/scoring — a verdict rule, a threshold, a condition or goal rule, a claim check, or allergen, diet, hidden-sugar or sodium-additive terms. Also use when a scoring test fails or a verdict looks wrong.
---

# Changing the rules engine

The rules engine is the only thing that decides a verdict (`ok` / `caution` / `unknown` / `avoid`). It is safety-critical. Work test-first and keep numbers in data files.

## Where things live

| What | File |
|---|---|
| Thresholds (high-in, claims, conditions, child and infant limits) | `app/scoring/data/thresholds.yaml` |
| Allergen terms (`contains` / `possible` / `exclude`) | `app/scoring/data/allergens.yaml` |
| Diet terms (non_veg, egg, dairy, animal_other, jain_exclusions) | `app/scoring/data/diet.yaml` |
| Ingredient lists (added and hidden sugars, sodium additives, caffeine, salt) | `app/scoring/data/ingredients.yaml` |
| Nutri-Score 2023 tables (the only numbers allowed in code) | `app/scoring/nutriscore.py` |
| Rule logic | `allergens.py`, `diet.py`, `warnings.py`, `claims.py`, `conditions.py`, `verdict.py` |

## Steps

1. **Find the source.** Every health number needs a citation: ICMR-NIN, FSSAI, WHO, NHS, UK FSA or a peer-reviewed paper. Put the URL in a YAML comment next to the value.
2. **Write the failing test first** in `tests/unit/scoring/test_<module>.py`.
   - Use the fixtures in `conftest.py`, or add a new named fixture there.
   - Assert exact codes and severities, e.g. `("salt_high", Status.AVOID)`, never "some reason exists".
3. Run it and watch it fail: `cd apps/api && uv run pytest tests/unit/scoring/test_<module>.py -v`
4. **Change the data first, and code only if the logic itself changes.**
   - New terms go in YAML, in lowercase. Add Hindi or Marathi (Devanagari) and common transliterations, e.g. `moongphali`, `मूंगफली`.
   - A new threshold key goes in `thresholds.yaml` under the right group, and the code reads it from `cfg.thresholds`.
5. Keep `# PENDING CLINICIAN REVIEW` at the top of `thresholds.yaml` unless a clinician has signed off. Record the sign-off in an ADR.
6. **Update the shared fixtures.** If any verdict or reason code changes, update `packages/test-fixtures/expected/*.json` in the same PR. CODEOWNERS requires a review there. The Android and web tests read these files too.
7. Run the **whole** suite and lint:
   `uv run pytest tests/unit/scoring tests/fixtures -v && uv run ruff check app tests`
   Or run `just test` to also check that both clients still render the fixtures.
8. **New reason codes** need keys `reason.<code>` in `packages/i18n/messages/{en,hi,mr}.json`. Then run `just i18n`.
9. Run the `nutrition-safety-reviewer` agent on the diff before you open the PR.
10. In the PR description, state the old value, the new value, the source, and the verdicts that change in the golden tests and `packages/test-fixtures`.

## Hard rules

- **Never turn `unknown` into `ok`.** Missing data, low extraction confidence (< `min_extraction_confidence`) or an empty ingredient list must stay `unknown` for any member the data matters to.
- **The LLM never changes a verdict.** Do not read model output inside `scoring/`.
- **Reasons are codes plus params, never prose.** Add new codes to `packages/i18n/messages/{en,hi,mr}.json` in the same PR. Never edit the generated Flutter ARB files.
- **Clients never compute verdicts.** If a rule seems to need client logic, it belongs here instead.
- **Inputs are per 100 g or 100 ml.** Convert per-serving values before they reach the engine. Never pass them as per-100 g values.
- **Status ranking is fixed:** `avoid` > `unknown` > `caution` > `ok`.
- **Allergen `possible` terms produce `may_contain`,** which defaults to `avoid`. Don't weaken this without clinician sign-off.

## Pitfalls

- **Substring false positives.** `egg` matches inside "eggplant" and `milk` inside "coconut milk". Add to `exclude`, and add a test.
- **Longest match first.** "onion powder" must not also report "onion". Check `find_terms` output order in tests.
- **INS/E-codes are normalised to `ins322`.** Write codes in YAML in that form.
- **Changing a shared term list** (e.g. `dairy`) affects the vegan and Jain diets and the claims. Re-run the full suite, not just one file.
- **Nutri-Score tables are official.** Change them only to match the Santé publique France / Open Food Facts 2023 implementation, and cite it.
