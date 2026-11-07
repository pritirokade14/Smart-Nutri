import dataclasses
import json
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.features.diary.frozen import from_row, to_row_values
from app.features.diary.models import DiaryDay
from app.scoring import targets
from scripts.generate_target_expectations import _body, _settings
from tests.fixtures.loader import FIXTURES

CASES = sorted((FIXTURES / "targets" / "inputs").glob("*.json"))


def _row(values: dict) -> DiaryDay:
    return DiaryDay(member_id=uuid4(), local_date=date(2026, 11, 7), account_id=uuid4(), **values)


def _result(path) -> targets.TargetResult | None:
    case = json.loads(path.read_text(encoding="utf-8"))
    if case["settings"] is None:
        return None
    return targets.compute(_body(case["body"]), _settings(case["settings"]))


@pytest.mark.parametrize("path", CASES, ids=[p.stem for p in CASES])
def test_round_trip_every_golden(path):
    result = _result(path)
    row = _row(to_row_values(result))
    if result is None:
        assert from_row(row) is None
    else:
        assert from_row(row) == dataclasses.replace(result, rate_options=())


def test_goldens_include_every_status():
    statuses = {r.status for r in (_result(p) for p in CASES) if r is not None}
    assert statuses == {
        "ready",
        "needs_body_data",
        "not_available_minor",
        "paused_pregnancy",
    }


def test_none_round_trip():
    values = to_row_values(None)
    assert values["status"] == "none"
    assert all(values[k] is None for k in ("energy_kcal", "protein_g", "fat_g", "carbs_g"))
    assert values["inputs"] == {} and values["flags"] == []
    assert from_row(_row(values)) is None


def test_inputs_keep_unrounded_decimals():
    g1 = next(p for p in CASES if p.stem == "g1_build_muscle")
    values = to_row_values(_result(g1))
    assert values["inputs"]["bmr_kcal"] == "1658.75"  # a string: a float would lose digits
    assert Decimal(values["inputs"]["bmr_kcal"]) == Decimal("1658.75")
    assert values["inputs"]["yaml_version"] == 1
    assert values["status"] == "ready" and values["basis"] == "formula"
    assert values["energy_kcal"] == Decimal(2760)
    assert values["inputs"]["rate_kg_per_week"] is not None
