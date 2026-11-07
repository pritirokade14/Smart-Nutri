"""Check or regenerate packages/test-fixtures/diary/expected/*.json from the real aggregation.

Run from apps/api:
  uv run python scripts/generate_diary_expectations.py          # --check (default): diff, exit 1 if stale
  uv run python scripts/generate_diary_expectations.py --write  # write only the files that differ

Input (hand-written): diary/inputs/<stem>.json
  {"as_of": "2026-11-07", "date": "2026-11-07", "timezone": "Asia/Kolkata",
   "targets_case": "g1_build_muscle" | null, "targets_status": null | "consent_required",
   "numbers_display": "show" | "hide_energy" | "hide_all", "partial_logged": false,
   "slots": [{"key", "label_key", "custom_label", "position", "archived"}]   (default: the 4 defaults),
   "entries": [{"slot", "local_time", "source_kind", "name", "grams", "nutrients": {8 keys}}]}
  `targets_case` names a targets/inputs stem, computed with `stored: true` (only `compute` runs).
  `null` means no target; `targets_status: "consent_required"` forces that status and no target.
  A week input has `"kind": "week"` and `days: [{date, targets_case, partial_logged, entries}]`;
  `date` is the last day, and a day that is not listed is empty with no frozen row.

Output (generated, never edited by hand): diary/expected/<stem>.json, the `DiaryDayOut` or
`DiaryWeekOut` the API returns (built by the API's own `build_day` / `build_week`), with ids from
uuid5(NAMESPACE_URL, "https://smartnutri.app/test-fixtures/diary/<stem>/<key>"), dumped with sorted
keys, 2-space indent and a trailing newline.

Review every change with nutrition-safety-reviewer before committing: never hand-edit an
expectation to match code.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from datetime import date, datetime, time
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.core.time import zone
from app.features.diary.aggregate import build_day, build_week
from app.features.meal_slots.defaults import DEFAULT_SLOTS
from app.features.meal_slots.models import MealSlot
from app.features.meals.models import MealLog
from app.scoring import DailyLimits
from app.scoring import targets as engine
from scripts.generate_target_expectations import _body, _settings
from tests.fixtures.loader import FIXTURES

INPUTS = FIXTURES / "diary" / "inputs"
EXPECTED = FIXTURES / "diary" / "expected"
# Fixed adult limits for the sugar and salt bands (the shared fixtures have no member).
LIMITS = DailyLimits(sugar_g=25, salt_g=5, protein_target_g=None, kcal=None)
OFF_BARCODE = "8900000000000"
BASE = "https://smartnutri.app/test-fixtures/diary"


def _id(stem: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"{BASE}/{stem}/{key}")


def _targets(case_name: str | None) -> engine.TargetResult | None:
    """The result for a targets/inputs stem, computed as a stored guide (no validation)."""
    if case_name is None:
        return None
    case = json.loads(
        (FIXTURES / "targets" / "inputs" / f"{case_name}.json").read_text(encoding="utf-8")
    )
    if case["settings"] is None:
        return None
    return engine.compute(_body(case["body"]), _settings(case["settings"]))


def _slots(stem: str, spec: list[dict] | None, account: UUID, member: UUID) -> dict[str, MealSlot]:
    if spec is None:
        spec = [
            {
                "key": d.label_key.rsplit(".", 1)[1],
                "label_key": d.label_key,
                "custom_label": None,
                "position": d.position,
                "archived": False,
            }
            for d in DEFAULT_SLOTS
        ]
    return {
        s["key"]: MealSlot(
            id=_id(stem, f"slot/{s['key']}"),
            account_id=account,
            member_id=member,
            position=s["position"],
            label_key=s["label_key"],
            custom_label=s["custom_label"],
            is_default=s["label_key"] is not None,
            archived_at=datetime(2026, 10, 1, tzinfo=zone("UTC")) if s["archived"] else None,
        )
        for s in spec
    }


def _entries(
    stem: str,
    prefix: str,
    day: date,
    items: list[dict],
    slots: dict[str, MealSlot],
    tz: str,
    account: UUID,
    member: UUID,
) -> list[MealLog]:
    out = []
    for i, item in enumerate(items):
        hh, mm = item["local_time"].split(":")
        at = datetime.combine(day, time(int(hh), int(mm)), tzinfo=zone(tz))
        kind = item["source_kind"]
        out.append(
            MealLog(
                id=_id(stem, f"{prefix}entry/{i}"),
                account_id=account,
                member_id=member,
                meal_slot_id=slots[item["slot"]].id,
                local_date=day,
                eaten_at=at,
                updated_at=at,
                source_kind=kind,
                product_id=_id(stem, f"{prefix}product/{i}") if kind == "product" else None,
                off_barcode=OFF_BARCODE if kind == "off" else None,
                product_name=item["name"],
                grade=None,
                grams=item["grams"],
                nutrients=dict(item["nutrients"]),
                client_id=None,
            )
        )
    return out


def expected_for(stem: str, case: dict) -> dict:
    account, member = _id(stem, "account"), _id(stem, "member")
    tz = case["timezone"]
    as_of = date.fromisoformat(case["as_of"])
    end = date.fromisoformat(case["date"])
    slots = _slots(stem, case.get("slots"), account, member)
    display = case["numbers_display"]
    if case.get("kind") == "week":
        entries: list[MealLog] = []
        results: dict[date, engine.TargetResult | None] = {}
        partial: dict[date, bool] = {}
        for d in case["days"]:
            day = date.fromisoformat(d["date"])
            entries += _entries(
                stem, f"{d['date']}/", day, d["entries"], slots, tz, account, member
            )
            results[day] = _targets(d["targets_case"])
            partial[day] = d["partial_logged"]
        out = build_week(
            member_id=member,
            end=end,
            today=as_of,
            entries=entries,
            results=results,
            partial=partial,
            limits=LIMITS,
            numbers_display=display,
        )
        return out.model_dump(mode="json")
    result = _targets(case["targets_case"])
    forced = case.get("targets_status")
    status = forced or (result.status if result is not None else "none")
    out_day = build_day(
        member_id=member,
        day=end,
        today=as_of,
        timezone=tz,
        slots=list(slots.values()),
        entries=_entries(stem, "", end, case["entries"], slots, tz, account, member),
        result=result,
        targets_status=status,
        limits=LIMITS,
        partial_logged=case["partial_logged"],
        numbers_display=display,
    )
    return out_day.model_dump(mode="json")


def compute(fixtures: Path = FIXTURES) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted((fixtures / "diary" / "inputs").glob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        out[path.name] = json.dumps(expected_for(path.stem, case), indent=2, sort_keys=True) + "\n"
    return out


def changes(fixtures: Path = FIXTURES) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Return (new contents by file, old contents by file, {file: ADDED|CHANGED|REMOVED})."""
    exp = fixtures / "diary" / "expected"
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
        print("diary/expected/ matches the aggregation")
        return 0
    for name, tag in tags.items():
        print(f"{tag}: {name}")
        if tag == "CHANGED":
            diff = difflib.unified_diff(
                old[name].splitlines(), new[name].splitlines(), "expected", "code", lineterm=""
            )
            print("\n".join(diff))
    if not args.write:
        print("stale: run with --write, then review with nutrition-safety-reviewer")
        return 1
    EXPECTED.mkdir(parents=True, exist_ok=True)
    for name, tag in tags.items():
        if tag == "REMOVED":
            (EXPECTED / name).unlink()
        else:
            (EXPECTED / name).write_text(new[name], encoding="utf-8")
    print(f"wrote {len(tags)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
