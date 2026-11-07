"""Day and week aggregation (Plan 11 Task 5; Rulings E13-E16). Pure."""

import json
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.features.diary.aggregate import build_day, build_week, progress, remaining
from app.features.meal_slots.models import MealSlot
from app.features.meals.models import MealLog
from app.features.meals.summary import _Acc
from app.features.targets.schemas import NumbersHidden
from app.scoring import DailyLimits
from app.scoring import targets as engine

DAY = date(2026, 11, 7)
MEMBER = uuid4()
LIMITS = DailyLimits(sugar_g=25, salt_g=5, protein_target_g=None, kcal=None)
G1 = engine.TargetResult(
    status="ready",
    energy_kcal=2760,
    protein_g=112,
    fat_g=77,
    carbs_g=405,
    direction="gain",
)
SHOW = NumbersHidden(energy=False, macros=False)
HIDE_ENERGY = NumbersHidden(energy=True, macros=False)
HIDE_ALL = NumbersHidden(energy=True, macros=True)
KEYS = (
    "energy_kcal",
    "sugars_g",
    "salt_g",
    "protein_g",
    "fat_g",
    "sat_fat_g",
    "carbs_g",
    "fibre_g",
)


def slot(position: int, key: str | None = "diary.slot.breakfast", label=None, archived=False):
    return MealSlot(
        id=uuid4(),
        account_id=uuid4(),
        member_id=MEMBER,
        position=position,
        label_key=key,
        custom_label=label,
        archived_at=datetime(2026, 10, 1, tzinfo=UTC) if archived else None,
    )


def entry(s: MealSlot, *, day: date = DAY, hour: int = 9, **nutrients) -> MealLog:
    values = dict.fromkeys(KEYS) | nutrients
    at = datetime(day.year, day.month, day.day, hour, 0, tzinfo=UTC)
    return MealLog(
        id=uuid4(),
        account_id=s.account_id,
        member_id=MEMBER,
        meal_slot_id=s.id,
        local_date=day,
        eaten_at=at,
        updated_at=at,
        source_kind="quick_add",
        product_name="x",
        grams=None,
        nutrients=values,
    )


def acc_of(*entries: MealLog) -> _Acc:
    a = _Acc()
    for e in entries:
        a.add(e.nutrients)
    return a


def day(slots, entries, result=G1, display="show", status="ready", **kw):
    return build_day(
        member_id=MEMBER,
        day=DAY,
        today=DAY,
        timezone="Asia/Kolkata",
        slots=slots,
        entries=entries,
        result=result,
        targets_status=status,
        limits=LIMITS,
        partial_logged=False,
        numbers_display=display,
        **kw,
    )


def test_unknown_never_zero():
    s = slot(0)
    a = entry(s, energy_kcal=400, protein_g=20.0)
    b = entry(s, energy_kcal=300)  # protein unknown
    d = day([s], [a, b])
    assert d.totals.protein_g == 20.0 and d.incomplete.protein_g is True
    assert d.remaining.protein_g is None and d.progress.protein_g is None
    assert d.totals.energy_kcal == 700.0 and d.incomplete.energy_kcal is False
    assert d.remaining.energy_kcal == 2060.0
    assert d.totals.fibre_g is None  # nobody knew it: null, not 0


def test_nothing_logged_is_null_not_zero():
    d = day([slot(0)], [])
    assert all(v is None for v in d.totals.model_dump().values())
    assert not any(d.incomplete.model_dump().values())
    assert d.remaining.model_dump() == {
        "energy_kcal": 2760.0,
        "protein_g": 112.0,
        "fat_g": 77.0,
        "carbs_g": 405.0,
    }
    assert d.progress.model_dump() == dict.fromkeys(
        ("energy_kcal", "protein_g", "fat_g", "carbs_g"), 0.0
    )


def test_negative_remaining_is_over():
    s = slot(0)
    d = day([s], [entry(s, energy_kcal=3010.4)])
    assert d.remaining.energy_kcal == -250.4
    assert d.progress.energy_kcal == 1.09


def test_remaining_rounds_half_up():
    s = slot(0)
    d = day([s], [entry(s, protein_g=50.25)])
    assert d.remaining.protein_g == 61.8  # 61.75 -> 61.8 (half-up)
    d2 = day([s], [entry(s, protein_g=50.35)])
    assert d2.remaining.protein_g == 61.7  # 61.65 -> 61.7


@pytest.mark.parametrize(
    ("eaten", "shape"), [(0.37, 0.25), (0.38, 0.5), (0.125, 0.25), (0.875, 1.0)]
)
def test_progress_quarter_steps_when_hidden(eaten, shape):
    acc = acc_of(entry(slot(0), energy_kcal=eaten * 2760))
    shown = progress(G1, acc, SHOW).energy_kcal
    hidden = progress(G1, acc, HIDE_ENERGY)
    assert shown == pytest.approx(eaten, abs=0.006)
    assert hidden.energy_kcal == shape
    assert hidden.protein_g is None  # protein was never entered: unknown, not 0


def test_progress_hidden_keeps_other_nutrients_exact():
    acc = acc_of(entry(slot(0), energy_kcal=1000, protein_g=56.0, fat_g=10, carbs_g=100))
    p = progress(G1, acc, HIDE_ENERGY)
    assert p.energy_kcal == 0.25 and p.protein_g == 0.5
    r = remaining(G1, acc, HIDE_ENERGY)
    assert r.energy_kcal is None and r.protein_g == 56.0
    r_all = remaining(G1, acc, HIDE_ALL)
    assert all(v is None for v in r_all.model_dump().values())
    p_all = progress(G1, acc, HIDE_ALL)
    assert p_all.energy_kcal == 0.25 and p_all.protein_g == 0.5  # shape stays


def test_no_ready_target_has_no_remaining_or_progress():
    s = slot(0)
    for result, status in (
        (None, "none"),
        (engine.TargetResult(status="paused_pregnancy"), "paused_pregnancy"),
        (
            engine.TargetResult(status="needs_body_data", missing_fields=("height_cm",)),
            "needs_body_data",
        ),
        (G1, "consent_required"),
    ):
        d = day([s], [entry(s, energy_kcal=100)], result=result, status=status)
        assert d.remaining is None and d.progress is None, status
        assert d.targets_status == status
    d = day([s], [], result=G1, status="consent_required")
    assert d.targets is None  # consent withdrawn: no target is shown


def test_slot_totals_per_slot():
    b, lunch = slot(0), slot(1, "diary.slot.lunch")
    d = day(
        [lunch, b],  # given out of order
        [
            entry(lunch, hour=13, energy_kcal=500, protein_g=20.0),
            entry(b, hour=8, energy_kcal=300, protein_g=10.0),
            entry(b, hour=7, energy_kcal=200),
        ],
    )
    assert [s.slot_id for s in d.slots] == [b.id, lunch.id]
    assert d.slots[0].totals.energy_kcal == 500.0 and d.slots[0].incomplete.protein_g is True
    assert d.slots[1].totals.energy_kcal == 500.0 and d.slots[1].incomplete.protein_g is False
    assert [e.nutrients.energy_kcal for e in d.slots[0].entries] == [200.0, 300.0]  # by time


def test_archived_slot_only_with_entries():
    keep, with_entries, without = (
        slot(0),
        slot(1, None, "Old", archived=True),
        slot(2, None, "Gone", archived=True),
    )
    d = day([keep, with_entries, without], [entry(with_entries, energy_kcal=100)])
    assert [(s.slot_id, s.archived) for s in d.slots] == [(keep.id, False), (with_entries.id, True)]


def _week(days: dict[date, list[MealLog]], results=None, partial=None, display="show"):
    entries = [e for es in days.values() for e in es]
    return build_week(
        member_id=MEMBER,
        end=DAY,
        today=DAY,
        entries=entries,
        results=results or {},
        partial=partial or {},
        limits=LIMITS,
        numbers_display=display,
    )


def test_week_average_excludes_partial_and_empty():
    s = slot(0)
    d = [DAY - timedelta(days=i) for i in range(7)]
    week = _week(
        {
            d[0]: [entry(s, day=d[0], energy_kcal=2000, protein_g=100.0)],
            d[1]: [entry(s, day=d[1], energy_kcal=1000, protein_g=50.0)],
            d[2]: [entry(s, day=d[2], energy_kcal=100)],  # partial: left out
            # d[3] empty: left out
        },
        partial={d[2]: True},
    )
    assert [t.date for t in week.days] == sorted(d)  # oldest first, 7 days
    assert week.averaged_days == 2
    assert week.averages.energy_kcal == 1500.0 and week.averages.protein_g == 75.0
    assert week.averages.fat_g is None  # nobody knew it
    tile = {t.date: t for t in week.days}
    assert tile[d[2]].partial_logged is True and tile[d[3]].items == 0
    assert tile[d[3]].totals.energy_kcal is None  # an empty day is null, never 0


def test_week_average_flags_incomplete_and_never_counts_unknown_as_zero():
    s = slot(0)
    d0, d1 = DAY, DAY - timedelta(days=1)
    week = _week(
        {
            d0: [entry(s, day=d0, energy_kcal=2000, protein_g=100.0)],
            d1: [entry(s, day=d1, energy_kcal=1000)],  # protein unknown
        }
    )
    assert (
        week.averages_incomplete.protein_g is True and week.averages_incomplete.energy_kcal is False
    )
    assert week.averages.protein_g == 50.0  # a lower bound over 2 days (100 / 2), flagged
    assert week.averages.energy_kcal == 1500.0


def test_protein_met_days_uses_frozen_target_per_day():
    s = slot(0)
    d = [DAY - timedelta(days=i) for i in range(4)]
    g2 = engine.TargetResult(status="ready", energy_kcal=1540, protein_g=71, fat_g=43, carbs_g=217)
    week = _week(
        {
            d[0]: [entry(s, day=d[0], protein_g=112.0)],  # G1 112: met
            d[1]: [entry(s, day=d[1], protein_g=80.0)],  # G2 71: met (G1's 112 would not be)
            d[2]: [entry(s, day=d[2], protein_g=60.0)],  # G2 71: not met
            d[3]: [entry(s, day=d[3], protein_g=500.0)],  # no row: no target, not counted
        },
        results={d[0]: G1, d[1]: g2, d[2]: g2},
    )
    assert week.protein_met_days == 2
    tile = {t.date: t for t in week.days}
    assert tile[d[1]].targets.protein_g == 71 and tile[d[0]].targets.protein_g == 112
    assert tile[d[3]].targets is None and tile[d[3]].progress is None


def _numbers(node, path=""):
    """Every (path, value) for a float or int under `node`."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _numbers(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _numbers(v, f"{path}[{i}]")
    elif isinstance(node, (int, float)) and not isinstance(node, bool):
        yield path, node


def test_redaction_hide_all_walks_every_number():
    s = slot(0)
    d = day(
        [s],
        [
            entry(
                s,
                energy_kcal=400,
                protein_g=20.0,
                fat_g=5,
                carbs_g=60,
                fibre_g=3,
                sugars_g=4,
                salt_g=0.5,
                sat_fat_g=1,
            )
        ],
        display="hide_all",
    )
    dumped = json.loads(d.model_dump_json())
    nutrient_keys = (
        "energy_kcal",
        "protein_g",
        "fat_g",
        "carbs_g",
        "fibre_g",
        "sugars_g",
        "salt_g",
        "sat_fat_g",
    )
    for top in ("totals", "remaining", "targets"):
        node = dumped[top]
        for path, value in _numbers(node):
            if path.rsplit(".", 1)[-1] in nutrient_keys or top == "targets":
                if top == "targets" and path.rsplit(".", 1)[-1] in (
                    "activity_factor",
                    "protein_g_per_kg",
                    "pct_bw_per_week",
                ):
                    continue
                assert False, f"{top}{path} = {value} is not null"
    for slot_out in dumped["slots"]:
        for path, _ in _numbers(slot_out["totals"]):
            raise AssertionError(path)
        for e in slot_out["entries"]:
            assert all(v is None for v in e["nutrients"].values())
    # Portions, positions and progress (quarter steps) are present.
    assert dumped["slots"][0]["position"] == 0
    assert dumped["progress"]["energy_kcal"] in (0.0, 0.25, 0.5, 0.75, 1.0)
    assert dumped["progress"]["protein_g"] is not None
    assert dumped["numbers_hidden"] == {"energy": True, "macros": True}
    # The incompleteness (which nutrients are unknown) stays: it is not a number.
    assert dumped["incomplete"]["salt_g"] is False


def test_week_hide_all_has_no_numbers():
    s = slot(0)
    week = _week(
        {DAY: [entry(s, energy_kcal=400, protein_g=20.0)]}, results={DAY: G1}, display="hide_all"
    )
    dumped = json.loads(week.model_dump_json())
    assert all(v is None for v in dumped["averages"].values())
    for tile in dumped["days"]:
        assert all(v is None for v in tile["totals"].values())
        if tile["targets"] is not None:
            assert all(v is None for v in tile["targets"].values())
    assert dumped["averaged_days"] == 1  # counts are not nutrient numbers


def test_decimal_sums_are_exact():
    s = slot(0)
    d = day([s], [entry(s, energy_kcal=0.1), entry(s, energy_kcal=0.2)])
    assert d.totals.energy_kcal == 0.3 and d.remaining.energy_kcal == 2759.7
    assert Decimal(str(d.remaining.energy_kcal)) == Decimal("2759.7")
