"""Check or regenerate packages/test-fixtures/weights/expected/*.json from the real trend maths.

Run from apps/api:
  uv run python scripts/generate_weight_expectations.py          # --check (default): diff, exit 1 if stale
  uv run python scripts/generate_weight_expectations.py --write  # write only the files that differ

Input (hand-written): weights/inputs/<stem>.json
  {"weigh_ins": [{"date": "2026-01-01", "weight_kg": 80.0}, ...],
   "target_kg": 75 | null, "numbers_display": "show" | "hide_energy" | "hide_all"}
  Numbers are JSON numbers, read as Decimal(str(x)). Always the full history (the route slices
  to its window afterwards).

Output (generated, never edited by hand): weights/expected/<stem>.json, the `WeightTrendOut`
body without the request envelope (`member_id`, `days`, `from`, `to`, which the route adds):
  points[{date, weight_kg|null, outlier, y}], trend[{date, trend_kg|null, y}],
  weekly_rate {kg, pct_bw}|null, projection {target_kg|null, date}|null, projection_reason,
  flags ["rapid_loss"], rapid_loss_pct (the safety line, for the card text; null under hide_all), numbers_hidden, pending_clinician_review.
kg and pct are rounded to 2 dp half-up and written as JSON numbers. `y` is `shape()` over the
weigh-ins and the trend values together, so the dots and the line share one scale. Under
`hide_all` every kg, the rate and the target are null; `y` is kept; the projection date is null too, so no digits show (spec e2e 7), while
`projection_reason` stays.
Dumped with sorted keys, 2-space indent and a trailing newline.

Review every change with nutrition-safety-reviewer before committing: never hand-edit an
expectation to match code.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.scoring import weight_trend as wt
from app.scoring.config import load_config
from tests.fixtures.loader import FIXTURES

TWO_DP = Decimal("0.01")


def _dec(value: object) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _kg(x: Decimal | None, hidden: bool) -> float | None:
    if x is None or hidden:
        return None
    return float(x.quantize(TWO_DP, rounding=ROUND_HALF_UP))


def _y(x: Decimal | None) -> float | None:
    return None if x is None else float(x)


def expected_for(case: dict) -> dict:
    hidden = case.get("numbers_display", "show") == "hide_all"
    ins = [
        wt.WeighIn(date.fromisoformat(w["date"]), Decimal(str(w["weight_kg"])))
        for w in case["weigh_ins"]
    ]
    result = wt.compute_trend(ins)
    ys = wt.shape([*(p.kg for p in result.points), *(t for _, t in result.trend)])
    n = len(result.points)
    target = _dec(case.get("target_kg"))

    rate = wt.weekly_rate(result)
    reason, when = wt.projection(result, target)
    return {
        "points": [
            {
                "date": p.day.isoformat(),
                "weight_kg": _kg(p.kg, hidden),
                "outlier": p.outlier,
                "y": _y(ys[i]),
            }
            for i, p in enumerate(result.points)
        ],
        "trend": [
            {"date": d.isoformat(), "trend_kg": _kg(t, hidden), "y": _y(ys[n + i])}
            for i, (d, t) in enumerate(result.trend)
        ],
        "weekly_rate": None
        if rate is None or hidden
        else {
            "kg": _kg(rate[0], False),
            "pct_bw": float(rate[1].quantize(TWO_DP, rounding=ROUND_HALF_UP)),
        },
        "projection": None
        if reason != "ready"
        else {"target_kg": _kg(target, hidden), "date": None if hidden else when.isoformat()},
        "projection_reason": reason,
        "flags": ["rapid_loss"] if wt.rapid_loss(result) else [],
        "rapid_loss_pct": None
        if hidden
        else float(load_config().targets["safety"]["rapid_loss_pct_bw_per_week"]),
        "numbers_hidden": hidden,
        "pending_clinician_review": True,
    }


def compute(fixtures: Path = FIXTURES) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted((fixtures / "weights" / "inputs").glob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        out[path.name] = json.dumps(expected_for(case), indent=2, sort_keys=True) + "\n"
    return out


def changes(fixtures: Path = FIXTURES) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Return (new contents by file, old contents by file, {file: ADDED|CHANGED|REMOVED})."""
    exp = fixtures / "weights" / "expected"
    new = compute(fixtures)
    old = (
        {p.name: p.read_text(encoding="utf-8") for p in exp.glob("*.json")} if exp.is_dir() else {}
    )
    tags = {}
    for name in sorted(set(new) | set(old)):
        if new.get(name) == old.get(name):
            continue
        tags[name] = "ADDED" if name not in old else "REMOVED" if name not in new else "CHANGED"
    return new, old, tags


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true", help="write the files that differ")
    parser.add_argument("--check", action="store_true", help="exit 1 if stale (the default)")
    args = parser.parse_args(argv)
    new, old, tags = changes()
    if not tags:
        print("weights/expected/ matches the engine")
        return 0
    for name, tag in tags.items():
        print(f"{tag}: {name}")
        if tag == "CHANGED":
            diff = difflib.unified_diff(
                old[name].splitlines(), new[name].splitlines(), "expected", "engine", lineterm=""
            )
            print("\n".join(diff))
    if not args.write:
        print("stale: run with --write, then review with nutrition-safety-reviewer")
        return 1
    exp = FIXTURES / "weights" / "expected"
    exp.mkdir(parents=True, exist_ok=True)
    for name, tag in tags.items():
        if tag == "REMOVED":
            (exp / name).unlink()
        else:
            (exp / name).write_text(new[name], encoding="utf-8")
    print(f"wrote {len(tags)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
