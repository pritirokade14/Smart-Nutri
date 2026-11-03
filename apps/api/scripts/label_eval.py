"""Label-extraction eval CLI. SPENDS REAL CALLMISSED CREDITS. Never run in CI or tests.

    cd apps/api
    uv run python -m scripts.label_eval --models kimi-k2.5,gemma-4-31b --limit 10
    uv run python -m scripts.label_eval --models kimi-k2.5 --limit 10 --yes-spend

Without `--yes-spend` it only prints how many paid calls it would make and an estimated
cost, then exits (status 2). Reports (metrics only, commit-safe) go to
tests/evals/labels/reports/; raw model output (label text) goes to the git-ignored
tests/evals/labels/raw/.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import mimetypes
import os
import re
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

from app.features.scans.cells import extraction_schema, to_extraction
from app.integrations.providers import ExtractionFailed, LLMProvider, ProviderUnavailable
from app.prompts import load_prompt
from scripts.label_eval_core import aggregate, load_manifest, render_markdown, score_photo

LABELS_DIR = Path(__file__).resolve().parent.parent / "tests" / "evals" / "labels"
EST_TOKENS_IN = 2500  # rough: prompt + one phone photo
EST_TOKENS_OUT = 700
_TOKENS = re.compile(r"tokens_in=(\S+) tokens_out=(\S+)")


class _TokenCapture(logging.Handler):
    """Reads token counts from CallMissedClient's per-call log line (it does not return them)."""

    def __init__(self) -> None:
        super().__init__()
        self.last: tuple[int | None, int | None] = (None, None)

    def emit(self, record: logging.LogRecord) -> None:
        m = _TOKENS.search(record.getMessage())
        if m:
            self.last = tuple(None if v == "None" else int(v) for v in m.groups())  # type: ignore[assignment]


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)


def load_pricing(path: Path, model: str) -> dict[str, float] | None:
    """`pricing.json`: {"<model>": {"in_per_1m": x, "out_per_1m": y}} in any one currency."""
    if not path.is_file():
        return None
    entry = json.loads(path.read_text(encoding="utf-8")).get(model)
    return entry if entry and "in_per_1m" in entry and "out_per_1m" in entry else None


def estimate(calls: int, pricing: dict[str, float] | None) -> str:
    if not pricing:
        return f"{calls} calls; cost unknown (no entry in pricing.json for this model)"
    per = (EST_TOKENS_IN * pricing["in_per_1m"] + EST_TOKENS_OUT * pricing["out_per_1m"]) / 1e6
    return f"{calls} calls, about {per * calls:.4f} (pricing.json units), {per:.5f} per call"


async def run_model(
    provider: LLMProvider,
    photos: list[dict[str, Any]],
    model: str,
    prompt_name: str,
    raw_dir: Path | None = None,
    capture: _TokenCapture | None = None,
) -> list[dict[str, Any]]:
    """Run every photo sequentially (same prompt and temperature for all models).

    The model answers in the prompt version's schema (extraction_v2: raw cells). `pred` is
    always the parsed `NutritionExtraction` the API normalises, so v1 and v2 are scored the
    same way; `raw_dir` keeps the raw model output."""
    prompt, version = load_prompt(prompt_name)
    schema = extraction_schema(version)
    rows: list[dict[str, Any]] = []
    for photo in photos:
        image = Path(photo["path"]).read_bytes()
        mime = mimetypes.guess_type(photo["path"])[0] or "image/jpeg"
        if capture:
            capture.last = (None, None)
        start = time.monotonic()
        pred: dict[str, Any] | None = None
        raw: dict[str, Any] | None = None
        error: str | None = None
        try:
            result = await provider.extract_label(
                image=image, mime=mime, prompt=prompt, prompt_version=version,
                schema=schema, model=model,
            )  # fmt: skip
            raw = result.model_dump()
            pred = to_extraction(result).model_dump()
        except (ExtractionFailed, ProviderUnavailable) as exc:
            error = getattr(exc, "reason", None) or type(exc).__name__
            if isinstance(exc, ProviderUnavailable):  # e.g. out of credits: stop spending
                rows.append(_row(photo, None, error, start, capture))
                break
        rows.append(_row(photo, pred, error, start, capture))
        if raw_dir is not None and raw is not None:
            raw_dir.mkdir(parents=True, exist_ok=True)
            (raw_dir / f"{_safe(photo['id'])}.json").write_text(
                json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8"
            )
    return rows


def _row(photo, pred, error, start, capture) -> dict[str, Any]:
    tin, tout = capture.last if capture else (None, None)
    return {
        "id": photo["id"], "ok": pred is not None, "pred": pred, "error": error,
        "latency_s": time.monotonic() - start, "tokens_in": tin, "tokens_out": tout,
    }  # fmt: skip


def write_report(
    model: str, prompt: str, photos: list[dict[str, Any]], results: list[dict[str, Any]],
    pricing: dict[str, float] | None, out_dir: Path, today: str,
) -> dict[str, Any]:  # fmt: skip
    by_id = {p["id"]: p for p in photos}
    scored = [score_photo(by_id[r["id"]], r) for r in results]
    agg = aggregate(scored, pricing)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{today}_{_safe(model)}_{prompt}"
    (out_dir / f"{stem}.md").write_text(
        render_markdown(model, prompt, today, agg, scored), encoding="utf-8"
    )
    # Per-photo detail has ids and problem codes only, never label text.
    (out_dir / f"{stem}.json").write_text(
        json.dumps({"model": model, "prompt": prompt, "date": today, **agg, "photos": scored},
                   indent=2, default=list),
        encoding="utf-8",
    )  # fmt: skip
    return agg


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--models", required=True, help="comma-separated CallMissed model ids")
    ap.add_argument("--prompt", default="extraction_v1")
    ap.add_argument("--limit", type=int, default=None, help="first N photos (same for every model)")
    ap.add_argument("--manifest", type=Path, default=LABELS_DIR / "manifest.json")
    ap.add_argument("--pricing", type=Path, default=LABELS_DIR / "pricing.json")
    ap.add_argument("--yes-spend", action="store_true", help="actually call the paid API")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    photos = [p for p in load_manifest(args.manifest) if p["image_exists"]]
    missing = [p["id"] for p in load_manifest(args.manifest) if not p["image_exists"]]
    if args.limit is not None:
        photos = photos[: args.limit]
    if missing:
        print(f"skipping {len(missing)} manifest entries with no image file in images/")
    if not photos or not models:
        print(
            "0 photos to run (add photos to images/ and entries to manifest.json). No calls made."
        )
        return 1

    total = 0
    for model in models:
        pricing = load_pricing(args.pricing, model)
        total += len(photos)
        print(f"{model}: {estimate(len(photos), pricing)}")
    print(f"TOTAL {total} paid CallMissed calls, prompt {args.prompt}, temperature 0")
    if not args.yes_spend:
        print("Not running: pass --yes-spend to spend credits.")
        return 2
    if os.environ.get("CI"):
        print("Refusing to run paid evals in CI.")
        return 2

    from app.core.config import get_settings
    from app.integrations.callmissed import CallMissedClient

    settings = get_settings()
    capture = _TokenCapture()
    logging.getLogger("app.integrations.callmissed").addHandler(capture)
    logging.getLogger("app.integrations.callmissed").setLevel(logging.INFO)

    async def go() -> None:
        client = CallMissedClient(
            api_key=settings.callmissed_api_key, base_url=settings.callmissed_base_url
        )
        try:
            today = date.today().isoformat()
            for model in models:
                raw = LABELS_DIR / "raw" / _safe(model)
                rows = await run_model(client, photos, model, args.prompt, raw, capture)
                pricing = load_pricing(args.pricing, model)
                agg = write_report(
                    model, args.prompt, photos, rows, pricing, LABELS_DIR / "reports", today
                )
                bad = [k for k, v in agg["gates"].items() if v is False]
                print(f"{model}: gates failed: {bad or 'none'}")
        finally:
            await client.aclose()

    asyncio.run(go())
    return 0


if __name__ == "__main__":
    sys.exit(main())
