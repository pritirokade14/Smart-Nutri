"""Calendar dates in India Standard Time (P5-R11).

IST is a fixed UTC+05:30 with no daylight saving, so a fixed offset is exact and does not
depend on the container having tz data installed.
"""

from datetime import UTC, date, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30), "IST")


def today_ist(now: datetime | None = None) -> date:
    """Today's date in India. `now` (timezone-aware) is for tests."""
    return (now or datetime.now(UTC)).astimezone(IST).date()
