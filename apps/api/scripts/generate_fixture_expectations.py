"""Regenerate packages/test-fixtures/expected/*.json by running the real rules engine.

Run from apps/api:  uv run python scripts/generate_fixture_expectations.py

Writes one file per (product, member) pair. Review the diff for safety plausibility
(nutrition-safety-reviewer) before committing: never hand-edit an expectation to match code.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.scoring import analyze
from tests.fixtures.loader import FIXTURES, load_member, load_product


def main() -> None:
    out = FIXTURES / "expected"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.json"):
        old.unlink()
    products = sorted(p.stem for p in (FIXTURES / "products").glob("*.json"))
    members = sorted(m.stem for m in (FIXTURES / "members").glob("*.json"))
    for p in products:
        for m in members:
            v = analyze(load_product(p), [load_member(m)]).verdicts[0]
            data = {"status": v.status.value, "reason_codes": [r.code for r in v.reasons]}
            (out / f"{p}.{m}.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            print(f"{p:15} {m:20} {data['status']:8} {data['reason_codes']}")


if __name__ == "__main__":
    main()
