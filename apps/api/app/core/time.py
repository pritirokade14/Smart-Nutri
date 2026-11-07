"""Calendar dates and wall-clock times in an IANA time zone (Plan 11 Task 1; ADR 0023).

`today_ist` stays for the callers that are India-only (P5-R11). Diary days use the account's
zone (`accounts.timezone`, default Asia/Kolkata). The `tzdata` package is a dependency, because
a slim container may lack the system zone files.
"""

from datetime import UTC, date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, available_timezones

IST = timezone(timedelta(hours=5, minutes=30), "IST")
DEFAULT_TIMEZONE = "Asia/Kolkata"


def today_ist(now: datetime | None = None) -> date:
    """Today's date in India. `now` (timezone-aware) is for tests."""
    return (now or datetime.now(UTC)).astimezone(IST).date()


def now_utc() -> datetime:
    """The current instant. Routes and services call it as `core_time.now_utc()` (module
    attribute), so tests pin the clock by patching `app.core.time.now_utc`."""
    return datetime.now(UTC)


def zone(name: str) -> ZoneInfo:
    """The zone for an IANA name. Raises KeyError for an unknown name."""
    try:
        return ZoneInfo(name)
    except (ValueError, OSError) as exc:  # ZoneInfoNotFoundError is a KeyError; "" and ".." are not
        raise KeyError(name) from exc


def is_valid_timezone(name: str) -> bool:
    return bool(name) and name in available_timezones()


def local_today(tz_name: str, now: datetime | None = None) -> date:
    return (now or now_utc()).astimezone(zone(tz_name)).date()


def local_date_of(at: datetime, tz_name: str) -> date:
    """The calendar date of an aware instant in the zone."""
    return at.astimezone(zone(tz_name)).date()


def local_clock(at: datetime, tz_name: str) -> time:
    """The wall-clock time of an aware instant in the zone, seconds dropped."""
    local = at.astimezone(zone(tz_name))
    return time(local.hour, local.minute)


def local_day_bounds(start: date, end: date, tz_name: str) -> tuple[datetime, datetime]:
    """[start 00:00, end + 1 day 00:00) in the zone, as aware datetimes. DST-safe."""
    tz = zone(tz_name)
    lo = datetime(start.year, start.month, start.day, tzinfo=tz)
    nxt = end + timedelta(days=1)
    hi = datetime(nxt.year, nxt.month, nxt.day, tzinfo=tz)
    return lo, hi
