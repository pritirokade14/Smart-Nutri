from datetime import UTC, date, datetime, time, timedelta

import pytest

from app.core.time import (
    is_valid_timezone,
    local_clock,
    local_date_of,
    local_day_bounds,
    local_today,
    zone,
)


def _utc(s: str) -> datetime:
    return datetime.fromisoformat(s)


def test_local_date_of_dst_and_midnight():
    # 23:59:59 IST and 00:00:00 IST either side of the date boundary.
    assert local_date_of(_utc("2026-11-07T18:29:59Z"), "Asia/Kolkata") == date(2026, 11, 7)
    assert local_date_of(_utc("2026-11-07T18:30:00Z"), "Asia/Kolkata") == date(2026, 11, 8)
    # 23:59 EST on 2026-03-07 is 04:59Z; DST starts at 2am local on the 8th.
    assert local_date_of(_utc("2026-03-08T04:59:00Z"), "America/New_York") == date(2026, 3, 7)
    assert local_date_of(_utc("2026-03-08T05:00:00Z"), "America/New_York") == date(2026, 3, 8)


def test_local_day_bounds_dst_day_is_23_hours():
    lo, hi = local_day_bounds(date(2026, 3, 8), date(2026, 3, 8), "America/New_York")
    assert hi.astimezone(UTC) - lo.astimezone(UTC) == timedelta(hours=23)
    lo2, hi2 = local_day_bounds(date(2026, 11, 7), date(2026, 11, 8), "Asia/Kolkata")
    assert hi2 - lo2 == timedelta(hours=48)


def test_is_valid_timezone():
    assert is_valid_timezone("Asia/Kolkata")
    assert is_valid_timezone("America/New_York")
    for bad in ("IST", "Mars/Base", "", "../etc/passwd"):
        assert not is_valid_timezone(bad)


def test_zone_unknown_raises_key_error():
    with pytest.raises(KeyError):
        zone("Mars/Base")
    with pytest.raises(KeyError):
        zone("")


def test_local_today_uses_zone():
    now = _utc("2026-11-08T03:00:00Z")
    assert local_today("Asia/Kolkata", now) == date(2026, 11, 8)
    assert local_today("America/New_York", now) == date(2026, 11, 7)


def test_local_clock_drops_seconds():
    assert local_clock(_utc("2026-11-07T18:29:59Z"), "Asia/Kolkata") == time(23, 59)
    assert local_clock(_utc("2026-11-08T02:00:00Z"), "America/New_York") == time(21, 0)
