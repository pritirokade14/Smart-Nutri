"""Diary analytics events (Plan 11 Task 8; spec 6.8): names and a closed `method` only, never a
nutrient, a target, a hidden state, a slot label or a quick-add name."""

import logging

import pytest

from app.integrations import posthog as ph
from app.integrations.posthog import ALLOWED_EVENTS, track

DIARY_METHODS = {
    "barcode",
    "label",
    "manual",
    "search",
    "recent",
    "favourite",
    "quick_add",
    "custom",
    "recipe",
    "copy",
}


class Recorder:
    def __init__(self):
        self.events: list[tuple[str, dict]] = []

    def capture(self, event, *, distinct_id, properties):
        self.events.append((event, dict(properties)))


@pytest.fixture
def recorder(monkeypatch):
    rec = Recorder()
    monkeypatch.setattr(ph, "_client", rec)
    return rec


def test_diary_events_allowed(recorder):
    from uuid import uuid4

    account = uuid4()
    track(account, "diary_entry_added", {"method": "quick_add"})
    track(account, "diary_day_viewed")
    assert recorder.events == [
        ("diary_entry_added", {"method": "quick_add"}),
        ("diary_day_viewed", {}),
    ]
    assert ALLOWED_EVENTS["diary_entry_added"] == {"method"}
    assert ALLOWED_EVENTS["diary_day_viewed"] == set()


def test_diary_event_drops_user_text_and_extra_keys(recorder, caplog):
    from uuid import uuid4

    caplog.set_level(logging.WARNING)
    track(uuid4(), "diary_entry_added", {"method": "Evening chai", "label": "Pre-gym"})
    # A name is not a method: the property is dropped, the event still carries no text.
    assert recorder.events == [("diary_entry_added", {})]
    assert "Evening chai" not in caplog.text and "Pre-gym" not in caplog.text
    track(uuid4(), "diary_day_viewed", {"energy_kcal": 1800})
    assert recorder.events[-1] == ("diary_day_viewed", {})


@pytest.mark.parametrize("method", sorted(DIARY_METHODS))
def test_every_diary_method_is_allowed(recorder, method):
    from uuid import uuid4

    track(uuid4(), "diary_entry_added", {"method": method})
    assert recorder.events == [("diary_entry_added", {"method": method})]


def test_method_enum_is_exactly_the_diary_set():
    assert ph._ENUMS["method"] == DIARY_METHODS
    # scan_started shares the enum (the scan methods are a subset).
    assert {"barcode", "label", "manual", "search"} <= ph._ENUMS["method"]
