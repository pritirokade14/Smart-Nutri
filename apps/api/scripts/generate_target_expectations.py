"""Check or regenerate packages/test-fixtures/targets/expected/*.json from the real engine.

Run from apps/api:
  uv run python scripts/generate_target_expectations.py          # --check (default): diff, exit 1 if stale
  uv run python scripts/generate_target_expectations.py --write  # write only the files that differ

Input (hand-written): targets/inputs/<stem>.json
  {"as_of": "2026-11-07", "stored": false,
   "body": {"age", "sex", "height_cm", "weight_kg", "body_fat_pct", "goal"},
   "settings": {GoalSettingsIn fields without member_id} | null}
  `settings: null` -> status "none". `stored: false` (the default) is the preview and PUT path:
  `check_body_fat` and `check_settings` run first and a failed rule is the expected
  `{"error": {"code", "details"}}`. `stored: true` is the GET path for settings saved earlier:
  only `compute` runs (a stored setting that stopped validating never errors, Ruling D8).
  Numbers are JSON numbers, read as Decimal(str(x)).

Output (generated, never edited by hand): targets/expected/<stem>.json, the `TargetsOut` the API
returns (built by the API's own `to_targets_out`, member id fixed), dumped with sorted keys,
2-space indent and a trailing newline.

Review every change with nutrition-safety-reviewer before committing: never hand-edit an
expectation to match code.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.features.targets.mapping import to_targets_out
from app.scoring import targets, weight_trend
from tests.fixtures.loader import FIXTURES

MEMBER_ID = uuid5(NAMESPACE_URL, "https://smartnutri.app/test-fixtures/members/self")
NUMBER_FIELDS = {"height_cm", "weight_kg", "body_fat_pct"}
SETTING_NUMBERS = ("rate_pct_bw_per_week", "target_weight_kg", "fat_pct_energy")


def _dec(value: object) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _body(raw: dict) -> targets.BodyData:
    return targets.BodyData(
        age=raw["age"],
        sex=raw["sex"],
        height_cm=_dec(raw["height_cm"]),
        weight_kg=_dec(raw["weight_kg"]),
        body_fat_pct=_dec(raw["body_fat_pct"]),
        goal=raw["goal"],
    )


def _settings(raw: dict) -> targets.GoalSettings:
    return targets.GoalSettings(
        direction=raw["direction"],
        activity_level=raw["activity_level"],
        rate_pct_bw_per_week=_dec(raw.get("rate_pct_bw_per_week")),
        target_weight_kg=_dec(raw.get("target_weight_kg")),
        sex_reference=raw.get("sex_reference"),
        pregnant_or_breastfeeding=bool(raw.get("pregnant_or_breastfeeding", False)),
        fat_pct_energy=_dec(raw.get("fat_pct_energy")),
    )


def _dump(out, keep_weight_source: bool = False) -> dict:
    """The response as JSON. `explanation.weight_source` (slice 6) is only written for a case
    with weigh-ins; for the others it is left out, so the older goldens stay byte-identical."""
    body = out.model_dump(mode="json")
    if body.get("explanation") is not None and not keep_weight_source:
        body["explanation"].pop("weight_source", None)
    return body


def expected_for(case: dict) -> dict:
    day = date.fromisoformat(case["as_of"])
    body = _body(case["body"])
    raw_settings = case["settings"]
    if raw_settings is None:
        return _dump(to_targets_out(MEMBER_ID, day, None, "show"))
    settings = _settings(raw_settings)
    display = raw_settings.get("numbers_display", "show")
    if not case.get("stored", False):
        try:
            targets.check_body_fat(body.body_fat_pct)
            targets.check_settings(body, settings)
        except targets.SettingsRuleError as exc:
            return {"error": {"code": exc.code, "details": exc.details}}
    weigh_ins = case.get("weigh_ins")
    source = None
    if weigh_ins:  # optional: the trend weight replaces the profile weight (G25)
        trend = weight_trend.weight_for_targets(
            [
                weight_trend.WeighIn(date.fromisoformat(w["date"]), _dec(w["weight_kg"]))
                for w in weigh_ins
            ],
            day,
        )
        source = "latest" if trend is None else "trend"
        if trend is not None:
            body = replace(body, weight_kg=trend)
    result = targets.compute(body, settings)
    if weigh_ins and result.explanation is not None:
        result = replace(result, explanation=replace(result.explanation, weight_source=source))
    out = to_targets_out(MEMBER_ID, day, result, display, unusual=targets.unusual_fields(body))
    return _dump(out, keep_weight_source=bool(weigh_ins))


def compute(fixtures: Path = FIXTURES) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted((fixtures / "targets" / "inputs").glob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        out[path.name] = json.dumps(expected_for(case), indent=2, sort_keys=True) + "\n"
    return out


def changes(fixtures: Path = FIXTURES) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Return (new contents by file, old contents by file, {file: ADDED|CHANGED|REMOVED})."""
    exp = fixtures / "targets" / "expected"
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
        print("targets/expected/ matches the engine")
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
    exp = FIXTURES / "targets" / "expected"
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
