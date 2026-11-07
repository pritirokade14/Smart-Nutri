"""Weight trend maths (Plan 12 Task 22). Hand-checked numbers; fixtures in packages/test-fixtures/weights."""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from datetime import date, timedelta
from decimal import Decimal

from app.scoring.config import load_config
from app.scoring.weight_trend import (
    WeighIn,
    compute_trend,
    max_change_kg_per_day,
    projection,
    rapid_loss,
    shape,
    weekly_rate,
    weight_for_targets,
)
from tests.fixtures.loader import FIXTURES

D = Decimal
D0 = date(2026, 1, 1)


def day(n: int) -> date:
    return D0 + timedelta(days=n)


def W(n: int, kg: str) -> WeighIn:
    return WeighIn(day(n), D(kg))


def daily(n_days: int, start: str, per_day: str) -> list[WeighIn]:
    return [WeighIn(day(i), D(start) + D(per_day) * i) for i in range(n_days)]


def test_ema_hand_example():
    # 80.0 (d0), 79.6 (d1): a1 = 0.25 -> T = 79.9; 79.2 (d3, gap 2): a2 = 1 - 0.75**2 = 0.4375
    # -> T = 79.9 + 0.4375 * (79.2 - 79.9) = 79.59375
    r = compute_trend([W(0, "80.0"), W(1, "79.6"), W(3, "79.2")])
    assert r.at(day(1)) == D("79.9")
    assert r.at(day(3)) == D("79.59375")
    assert r.at(day(-1)) is None
    assert r.at(day(10)) == D("79.59375")  # latest non-outlier on or before


def test_single_outlier_excluded():
    # 82.5 on d4: |82.5 - 79.59375| / 79.59375 = 3.65 % > 3 -> outlier, T unchanged
    r = compute_trend([W(0, "80.0"), W(1, "79.6"), W(3, "79.2"), W(4, "82.5")])
    assert [p.outlier for p in r.points] == [False, False, False, True]
    assert r.at(day(4)) == D("79.59375")
    assert len(r.trend) == 3
    # an in-band weigh-in afterwards keeps the outlier out; gap counts from d3 (2 days)
    r2 = compute_trend([*r_in(), W(5, "79.0")])
    assert r2.points[3].outlier is True and r2.points[4].outlier is False
    # a = 1 - 0.75**2 = 0.4375; T = 79.59375 + 0.4375 * (79.0 - 79.59375)
    assert r2.at(day(5)) == D("79.59375") + D("0.4375") * (D("79.0") - D("79.59375"))


def r_in() -> list[WeighIn]:
    return [W(0, "80.0"), W(1, "79.6"), W(3, "79.2"), W(4, "82.5")]


def test_exactly_on_the_band_is_not_an_outlier():
    r = compute_trend([W(0, "100"), W(1, "103")])  # exactly 3 %
    assert r.points[1].outlier is False


def test_step_change_two_in_a_row_accepted():
    # 80 x3, then 84 (5 % out, pending), then 84.2 (same side): both accepted.
    # 84: T = 80 + 0.25 * 4 = 81; 84.2: T = 81 + 0.25 * 3.2 = 81.8
    r = compute_trend([W(0, "80"), W(1, "80"), W(2, "80"), W(3, "84"), W(4, "84.2")])
    assert [p.outlier for p in r.points] == [False] * 5
    assert r.at(day(3)) == D("81")
    assert r.at(day(4)) == D("81.8")


def test_opposite_sides_are_two_outliers():
    r = compute_trend([W(0, "80"), W(1, "84"), W(2, "76")])
    assert [p.outlier for p in r.points] == [False, True, True]
    assert r.at(day(2)) == D("80")


def test_pending_cleared_by_an_in_band_weigh_in():
    # 84 out, 80.4 in band (pending cleared), 84.5 out again vs T: pending again, not a step
    r = compute_trend([W(0, "80"), W(1, "84"), W(2, "80.4"), W(3, "84.5")])
    assert [p.outlier for p in r.points] == [False, True, False, True]


def test_unsorted_and_empty_input():
    assert compute_trend([]).points == ()
    r = compute_trend([W(3, "79.2"), W(0, "80.0"), W(1, "79.6")])
    assert r.at(day(3)) == D("79.59375")


def test_weight_for_targets_needs_three():
    assert weight_for_targets([W(0, "76.2"), W(1, "76.2")], day(1)) is None
    assert weight_for_targets([W(0, "76.2"), W(1, "76.2"), W(2, "76.2")], day(2)) == D("76.2")
    # an outlier does not count towards the three
    ins = [W(0, "76.2"), W(1, "76.2"), W(2, "80.0")]
    assert weight_for_targets(ins, day(2)) is None
    # weigh-ins after the target date are ignored
    assert weight_for_targets([*ins[:2], W(5, "76.2")], day(1)) is None


def test_weekly_rate_and_pct():
    # 80 x3 (d0-d2), then 79 on d9 (gap 7): a = 1 - 0.75**7 = 0.86651611328125
    # T(d9) = 80 - 0.86651611328125 = 79.13348388671875; T(d2) = 80
    r = compute_trend([W(0, "80"), W(1, "80"), W(2, "80"), W(9, "79")])
    kg, pct = weekly_rate(r)
    assert kg == D("-0.86651611328125")
    assert pct == kg / D("79.13348388671875") * 100
    assert round(pct, 4) == D("-1.0950")


def test_weekly_rate_none_cases():
    assert weekly_rate(compute_trend([])) is None
    two = compute_trend([W(0, "80"), W(8, "79")])
    assert weekly_rate(two) is None  # fewer than 3
    nothing_before = compute_trend([W(0, "80"), W(1, "80"), W(2, "80")])
    assert weekly_rate(nothing_before) is None  # none on or before last - 7


def test_rapid_loss_needs_three_windows():
    # 0.2 kg/day fall: steady state about 1.4 kg/week, about 1.8 % of body weight
    assert rapid_loss(compute_trend(daily(28, "80", "-0.2"))) is True
    # only 21 days: the third window (ending d6) has no weigh-in a week before it
    assert rapid_loss(compute_trend(daily(21, "80", "-0.2"))) is False
    # 0.1 kg/day is 0.7 kg/week, below 1.5 %
    assert rapid_loss(compute_trend(daily(28, "80", "-0.1"))) is False
    assert rapid_loss(compute_trend([])) is False


def test_projection_reasons():
    falling = compute_trend(daily(20, "80", "-0.1"))
    assert projection(falling, None) == ("no_target", None)
    # reached beats too_few: 3 weigh-ins within the 0.5 kg band
    assert projection(compute_trend(daily(3, "80", "0")), D("80.3")) == ("reached", None)
    assert projection(compute_trend(daily(3, "80", "0")), D("85")) == ("too_few_weigh_ins", None)
    # six weigh-ins but a span under 14 days
    assert projection(compute_trend(daily(6, "80", "-0.1")), D("70"))[0] == "too_few_weigh_ins"
    assert projection(compute_trend([]), D("70")) == ("too_few_weigh_ins", None)
    reason, when = projection(falling, D("75"))
    assert reason == "ready" and when is not None and when > day(19)
    assert projection(falling, D("85")) == ("moving_away", None)
    assert projection(compute_trend(daily(20, "80", "0")), D("75")) == ("moving_away", None)
    slow = compute_trend(daily(20, "80", "-0.02"))  # about 0.14 kg a week: 1000 days to 60 kg
    assert projection(slow, D("60")) == ("too_far", None)


def test_projection_date_is_ceiling_of_days():
    # constant fall 0.5 kg/day: the trend follows at the same slope after the start-up,
    # so use a hand case instead: 80 on d0,d1,d2 (T=80), 79 on d9 -> kg rate -0.86651611328125
    r = compute_trend([W(i, "80") for i in range(3)] + [W(9, "79"), W(12, "79"), W(16, "79")])
    last = day(16)
    t_last = r.at(last)
    kg, _ = weekly_rate(r)
    expected = math.ceil((D("70") - t_last) / (kg / 7))
    assert projection(r, D("70")) == ("ready", last + timedelta(days=expected))


def test_shape_constant_is_half():
    assert shape([D("80"), D("80")]) == [D("0.5"), D("0.5")]
    assert shape([]) == []
    assert shape([None, None]) == [None, None]


def test_shape_scales_and_rounds_half_up():
    # (v - 70) / 6: 70 -> 0, 71 -> 0.1666 -> 0.17, 72.25 -> 0.375 -> 0.38, 76 -> 1
    out = shape([D("70"), None, D("71"), D("72.25"), D("76")])
    assert out == [D("0"), None, D("0.17"), D("0.38"), D("1")]


def test_max_change_key():
    assert max_change_kg_per_day() == D("2.0")


def _generator():
    path = FIXTURES.parents[1] / "apps" / "api" / "scripts" / "generate_weight_expectations.py"
    spec = importlib.util.spec_from_file_location("generate_weight_expectations", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_matches_fixtures():
    gen = _generator()
    new, _old, tags = gen.changes()
    assert not tags, (
        f"stale weight fixtures: {tags}; run scripts/generate_weight_expectations.py --write"
    )
    assert set(new) == {p.name for p in (FIXTURES / "weights" / "inputs").glob("*.json")}


EXPECTED_CASES = {
    "three_constant", "gap_calendar_days", "single_outlier", "step_change_two_in_a_row",
    "too_few_for_rate", "weekly_rate_loss", "rapid_loss_three_weeks", "projection_ready",
    "projection_too_few", "projection_moving_away", "projection_too_far", "projection_reached",
    "no_target", "hide_all",
}  # fmt: skip


def _expected(name: str) -> dict:
    return json.loads((FIXTURES / "weights" / "expected" / f"{name}.json").read_text("utf-8"))


def test_fixture_cases_exist():
    names = {p.stem for p in (FIXTURES / "weights" / "expected").glob("*.json")}
    assert names == EXPECTED_CASES


def test_fixture_hand_checked_goldens():
    # gap_calendar_days is the ema hand example: 79.59375 -> 79.59
    gap = _expected("gap_calendar_days")
    assert [t["trend_kg"] for t in gap["trend"]] == [80.0, 79.9, 79.59]
    # single_outlier: the 82.5 point is hollow and the trend does not move
    out = _expected("single_outlier")
    assert [p["outlier"] for p in out["points"]] == [False, False, False, True]
    assert out["trend"][-1]["trend_kg"] == 79.59
    # step change: both accepted, trend 81.0 then 81.8
    step = _expected("step_change_two_in_a_row")
    assert not any(p["outlier"] for p in step["points"])
    assert [t["trend_kg"] for t in step["trend"]][-2:] == [81.0, 81.8]
    # hide_all: no digits, y kept
    hidden = _expected("hide_all")
    assert hidden["numbers_hidden"] is True
    assert all(p["weight_kg"] is None and p["y"] is not None for p in hidden["points"])
    assert all(t["trend_kg"] is None and t["y"] is not None for t in hidden["trend"])
    assert hidden["weekly_rate"] is None
    assert hidden["projection"]["target_kg"] is None
    assert _expected("too_few_for_rate")["weekly_rate"] is None
    assert _expected("rapid_loss_three_weeks")["flags"] == ["rapid_loss"]
    assert _expected("three_constant")["flags"] == []
    for name, reason in {
        "projection_ready": "ready", "projection_too_few": "too_few_weigh_ins",
        "projection_moving_away": "moving_away", "projection_too_far": "too_far",
        "projection_reached": "reached", "no_target": "no_target",
    }.items():  # fmt: skip
        assert _expected(name)["projection_reason"] == reason, name


def test_yaml_trend_keys_present_and_sourced():
    cfg = load_config()
    assert {"trend", "projection", "safety"} <= set(cfg.targets)
    assert (
        "smartnutri_working_values"
        in cfg.thresholds["section_sources"]["energy_targets"]["thresholds"]
    )


def test_module_is_pure():
    import ast
    from pathlib import Path

    src = Path(__file__).resolve().parents[3] / "app" / "scoring" / "weight_trend.py"
    mods = {
        n.module if isinstance(n, ast.ImportFrom) else a.name
        for n in ast.walk(ast.parse(src.read_text("utf-8")))
        if isinstance(n, ast.Import | ast.ImportFrom)
        for a in (n.names if isinstance(n, ast.Import) else [None])
        if (n.module if isinstance(n, ast.ImportFrom) else a.name)
    }
    assert not {m for m in mods if m.split(".")[0] in {"sqlalchemy", "fastapi", "httpx", "os"}}
