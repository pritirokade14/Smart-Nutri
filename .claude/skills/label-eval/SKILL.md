---
name: label-eval
description: Use when building or running the nutrition-label extraction evaluation set, choosing or switching the CallMissed vision model, changing the extraction prompt, or checking extraction accuracy, cost or latency.
---

# Label extraction evaluation

Extraction turns a label photo into nutrition per 100 g, a serving size, ingredients, allergen and may-contain lines, claims and a veg mark. Wrong numbers lead to wrong health verdicts, so every model or prompt change is measured here first.

## Layout

```
apps/api/tests/evals/labels/
  images/            # GIT-IGNORED: real photos may show personal info
  expected/<id>.json # committed ground truth, one per image
  manifest.csv       # id, brand, category, language(s), photo conditions, source
  run_eval.py        # runner (written in Plan 2)
  results/           # committed summaries: <date>_<model>_<prompt>.md
```

## Building the set (target: at least 50 images in v1, 150+ later)

1. **Cover the real distribution:**
   - Biscuits, namkeen, beverages, dairy, cereals, sweets, instant noodles and ready-to-eat foods.
   - Hindi and bilingual labels.
   - Blurry, angled, curved-pack and glare photos.
   - Per-serving-only tables.
2. **Ground truth.** `expected/<id>.json` follows the same Pydantic schema as the extractor output (`NutritionExtraction`).
   - Enter it by hand from the pack, and double-check it.
   - Use `null` for values not printed. Never guess.
3. **Never commit the photos.** Store them in the team drive or a private bucket, and note the source in `manifest.csv`.

## Metrics (per model and prompt version)

| Metric | Definition | Gate |
|---|---|---|
| Numeric field accuracy | Within ±5% or ±0.5 g of truth, per field (kcal, protein, carbs, sugars, fat, sat fat, fibre, salt or sodium, serving) | ≥ 90% overall |
| Basis correctness | Per-100 g vs per-serving correctly identified | ≥ 98% |
| Ingredient F1 | Token-level, after `normalize()` | ≥ 0.9 |
| **Allergen recall** | Every allergen in the truth is detected by the engine on the extracted output | **100% (hard gate)** |
| Hallucination rate | A value returned where the truth is `null` | ≤ 2% |
| Latency | p50 and p95 seconds | p95 ≤ 8 s |
| Cost | Credits or ₹ per scan, from the CallMissed usage logs | Record it |

The allergen recall gate is absolute. A model that misses one allergen in the set cannot ship, whatever its other scores.

## Running

```bash
cd apps/api
uv run python tests/evals/labels/run_eval.py --model <model-id> --prompt extraction_v<N> [--limit 10]
```

- Run each candidate: `gpt-6-luna`, `glm-5.3-flash`, `gemma-4-31b`, `gemini-3.5-flash-lite`. Add new vision models from `GET /v1/models` (filter `supports_vision`).
- Use the same images, prompt and temperature (0) for every model.
- The runner calls the real API, which **spends credits**. Use `--limit` while iterating, and confirm the expected cost before a full run.

## Recording results

1. Write `results/<YYYY-MM-DD>_<model>_<prompt>.md` with the metrics table, the 5 worst images, and the failure types.
2. If the default changes, update `settings.models.extraction` and add an ADR in `docs/adr/`. Prefer India-processed models when quality is similar.
3. **Any prompt change** gets a new `app/prompts/extraction_v<N+1>.md`. Never edit the old version in place.

## Pitfalls

- Treating per-serving tables as per-100 g. Check the basis field first when numbers look off.
- Labels that list sodium in mg rather than salt in g.
- Comparing models on different image subsets.
- Leaking photos into git. `images/` is in `.gitignore`, so keep it that way.
