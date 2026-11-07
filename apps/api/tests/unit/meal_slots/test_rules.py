from datetime import time
from uuid import UUID, uuid4

import pytest

from app.features.meal_slots.defaults import DEFAULT_SLOTS
from app.features.meal_slots.rules import (
    SlotChoice,
    SlotWindow,
    pick_slot,
    window_contains,
)


def _defaults() -> tuple[list[SlotChoice], dict[str, UUID]]:
    ids = {d.label_key.rsplit(".", 1)[1]: uuid4() for d in DEFAULT_SLOTS}
    return (
        [
            SlotChoice(ids[d.label_key.rsplit(".", 1)[1]], d.position, SlotWindow(d.start, d.end))
            for d in DEFAULT_SLOTS
        ],
        ids,
    )


@pytest.mark.parametrize(
    ("at", "expected"),
    [
        (time(10, 59), "breakfast"),
        (time(11, 0), "lunch"),
        (time(15, 59), "lunch"),
        (time(16, 0), "snack"),
        (time(18, 59), "snack"),
        (time(19, 0), "dinner"),
        (time(23, 59), "dinner"),
        (time(0, 0), "dinner"),
        (time(3, 59), "dinner"),
        (time(4, 0), "breakfast"),
    ],
)
def test_default_boundaries(at, expected):
    active, ids = _defaults()
    assert pick_slot(active, at) == ids[expected]


def test_overlap_takes_lowest_position():
    a, b = uuid4(), uuid4()
    slots = [
        SlotChoice(b, 1, SlotWindow(time(9, 0), time(12, 0))),
        SlotChoice(a, 0, SlotWindow(time(8, 0), time(10, 0))),
    ]
    assert pick_slot(slots, time(9, 30)) == a


def test_no_window_contains_takes_latest_start_before():
    early, late = uuid4(), uuid4()
    slots = [
        SlotChoice(early, 0, SlotWindow(time(6, 0), time(7, 0))),
        SlotChoice(late, 1, SlotWindow(time(12, 0), time(13, 0))),
    ]
    assert pick_slot(slots, time(14, 0)) == late


def test_nothing_before_takes_lowest_position():
    early, late = uuid4(), uuid4()
    slots = [
        SlotChoice(late, 1, SlotWindow(time(12, 0), time(13, 0))),
        SlotChoice(early, 0, SlotWindow(time(6, 0), time(7, 0))),
    ]
    assert pick_slot(slots, time(5, 0)) == early


def test_slot_without_window_never_matched():
    plain, windowed = uuid4(), uuid4()
    slots = [
        SlotChoice(plain, 0, None),
        SlotChoice(windowed, 1, SlotWindow(time(12, 0), time(13, 0))),
    ]
    assert pick_slot(slots, time(12, 30)) == windowed
    # Nothing matches or starts before 05:00: the lowest position wins, windowless or not.
    assert pick_slot(slots, time(5, 0)) == plain
    # Windowless slots are not "latest start before": 14:00 picks the windowed slot.
    assert pick_slot(slots, time(14, 0)) == windowed


def test_wrap_window_contains():
    w = SlotWindow(time(22, 0), time(2, 0))
    assert window_contains(w, time(1, 30))
    assert not window_contains(w, time(2, 1))
    assert window_contains(w, time(22, 0))
    assert not window_contains(w, time(21, 59))


def test_empty_raises():
    with pytest.raises(ValueError):
        pick_slot([], time(9, 0))
