"""Check or regenerate packages/test-fixtures/expected/*.json from the real rules engine.

Run from apps/api:
  uv run python scripts/generate_fixture_expectations.py          # --check (default): diff, exit 1 if different
  uv run python scripts/generate_fixture_expectations.py --write  # write only the files that differ

Review every change with nutrition-safety-reviewer before committing: never hand-edit an
expectation to match code.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.scoring import analyze
from tests.fixtures.loader import FIXTURES, load_member, load_product


def compute(fixtures: Path = FIXTURES) -> dict[str, str]:
    products = sorted(p.stem for p in (fixtures / "products").glob("*.json"))
    members = sorted(m.stem for m in (fixtures / "members").glob("*.json"))
    out: dict[str, str] = {}
    for p in products:
        for m in members:
            v = analyze(load_product(p, fixtures), [load_member(m, fixtures)]).verdicts[0]
            data = {
                "status": v.status.value,
                "reasons": [{"code": r.code, "severity": r.severity.value} for r in v.reasons],
            }
            out[f"{p}.{m}.json"] = json.dumps(data, indent=2) + "\n"
    return out


def changes(fixtures: Path = FIXTURES) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Return (new contents by file, old contents by file, {file: ADDED|CHANGED|REMOVED})."""
    exp = fixtures / "expected"
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


def report(new: dict[str, str], old: dict[str, str], tags: dict[str, str]) -> list[str]:
    lines: list[str] = []
    for name, tag in tags.items():
        lines.append(f"{tag}: {name}")
        lines.extend(
            difflib.unified_diff(
                old.get(name, "").splitlines(),
                new.get(name, "").splitlines(),
                f"committed/{name}",
                f"engine/{name}",
                lineterm="",
            )
        )
    return lines


def write(fixtures: Path = FIXTURES) -> dict[str, str]:
    exp = fixtures / "expected"
    exp.mkdir(exist_ok=True)
    new, _old, tags = changes(fixtures)
    for name, tag in tags.items():
        if tag == "REMOVED":
            (exp / name).unlink()
        else:
            (exp / name).write_text(new[name], encoding="utf-8")
    return tags


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument(
        "--check", action="store_true", help="default: report differences, exit 1 if any"
    )
    mode.add_argument("--write", action="store_true", help="write only the files that differ")
    args = ap.parse_args(argv)
    if args.write:
        tags = write()
        print("\n".join(f"{t}: {n}" for n, t in tags.items()) or "expected/ already up to date")
        return 0
    new, old, tags = changes()
    if tags:
        print("\n".join(report(new, old, tags)))
        return 1
    print("expected/ matches the rules engine")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
