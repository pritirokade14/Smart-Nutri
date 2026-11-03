---
name: label-eval
description: Use when building or running the nutrition-label extraction evaluation set, choosing or switching the CallMissed vision model, changing the extraction prompt, or checking extraction accuracy, cost or latency.
---

# Label extraction evaluation

Extraction turns a label photo into nutrition per 100 g, a serving size, ingredients, allergen and may-contain lines, claims and a veg mark. Wrong numbers lead to wrong health verdicts, so every model or prompt change is measured here first.

## Layout

```
apps/api/tests/evals/labels/
  manifest.json      # committed: one entry per photo, with the values a human transcribed
  images/            # GIT-IGNORED: real photos may show personal info
  raw/               # GIT-IGNORED: raw model output (contains label text)
  reports/           # committed, metrics only: <date>_<model>_<prompt>.md and .json
  pricing.json       # optional, committed: {"<model>": {"in_per_1m": x, "out_per_1m": y}}
apps/api/scripts/label_eval.py       # CLI
apps/api/scripts/label_eval_core.py  # manifest loader, scorer and the GATES table (pure)
```

The photo checklist, the manifest entry format and the transcription rules are in `apps/api/tests/evals/labels/README.md`. Read it before adding photos.

## Building the set (target: 40 to 60 real packs in v1, 150+ later)

1. **Cover the real distribution:**
   - Biscuits, namkeen, beverages, dairy, cereals, sweets, instant noodles and ready-to-eat foods.
   - Hindi and bilingual labels.
   - Blurry, angled, curved-pack and glare photos.
   - Per-serving-only tables.
2. **Ground truth.** Each `manifest.json` entry has an `expected` block.
   - Transcribe it by hand from the pack, and double-check it.
   - Use `null` for values not printed. Never guess. A key you leave out is not scored.
3. **Never commit the photos.** Store them in the team drive or a private bucket, and note the source in the entry's `source` field.

## Metrics (per model and prompt version)

The gates are the `GATES` table in `apps/api/scripts/label_eval_core.py`. If they change, change the code and this table together.

| Metric | Gate |
|---|---|
| `numeric_accuracy` (within 5% or 0.5 of the transcription) | >= 0.90 |
| `unit_basis` (units and per-100 vs per-serving) | >= 0.98 |
| `null_precision` (a value returned where the pack prints none) | <= 0.02 |
| `pct_in_gram` (a %RDA number put in a gram field) | <= 0 |
| `may_contain_recall` (critical) | >= 1.0 |
| `allergen_statement_recall` | >= 1.0 |
| `allergen_engine_recall` (hard) | >= 1.0 |
| `ingredient_f1` (after `normalize()`) | >= 0.90 |
| `devanagari` | >= 0.95 |
| `injection` (planted instructions leaking into output) | <= 0 |
| `failure_rate` | <= 0.05 |
| `latency_p95` (seconds) | <= 8.0 |

Also reported, with no gate: upper-bound recall, confidence on degraded and clean photos, and cost per call (from token counts and `pricing.json`).

The allergen and may-contain gates are absolute. A model that misses one allergen in the set cannot ship, whatever its other scores.

## Running

```bash
cd apps/api
# Prints the call count and estimated cost, makes no calls, exits with status 2:
uv run python -m scripts.label_eval --models <a>,<b> --limit N
# After the product owner OKs the cost:
uv run python -m scripts.label_eval --models <a>,<b> --limit N --yes-spend
```

- It refuses to run in CI. Never run it from tests.
- Candidates include `gpt-6-luna`, `glm-5.3-flash`, `gemma-4-31b` and `gemini-3.5-flash-lite`. Add new vision models from `GET /v1/models` (filter `supports_vision`).
- Every model sees the same photos, the same prompt (`--prompt`, default `extraction_v1`) and temperature 0.
- It **spends credits**. Start with `--limit 10`, then run the full set.

## Recording results

1. The run writes `reports/<YYYY-MM-DD>_<model>_<prompt>.md` and `.json` (metrics and problem codes only). Commit them. Raw output stays in the git-ignored `raw/`.
2. If the default changes, update `settings.models.extraction` and add an ADR in `docs/adr/`. Prefer India-processed models when quality is similar.
3. **Any prompt change** gets a new `app/prompts/extraction_v<N+1>.md`. Never edit the old version in place.

## Pitfalls

- Treating per-serving tables as per-100 g. Check the basis field first when numbers look off.
- Labels that list sodium in mg rather than salt in g.
- Comparing models on different image subsets.
- Leaking photos into git. `images/` is in `.gitignore`, so keep it that way.
