"""PostHog server events through an allow-list: no health data, ever (Plan 8 Task 4).

`track()` is the only way the API sends an analytics event.
- **Events.** Only events in `ALLOWED_EVENTS` are sent. Any other event is dropped with a
  warning that names the event, never its properties.
- **Properties.** Only the listed keys are kept, and only with safe values: a short
  lowercase token, an int (not a bool) or a bool. Some keys accept a closed set of values.
  Dropped keys are named in a warning. Their values are never logged.
- **Identity.** The distinct id is `sha256(account_id)` hex, never the raw id.

Never send conditions, allergens, diet, verdict reasons, per-member statuses, nutrients,
member names, emails or raw IDs. The Android (`analytics.dart`) and web (`analytics.ts`)
clients must mirror `ALLOWED_EVENTS` exactly.
"""

from __future__ import annotations

import hashlib
import logging
import re
from collections.abc import Mapping
from types import MappingProxyType
from uuid import UUID

from posthog import Posthog

from app.core.config import Settings

logger = logging.getLogger(__name__)

# Hard-coded ingest host (US cloud); no env var by design. Only allow-listed, health-free
# events go there.
POSTHOG_HOST = "https://us.i.posthog.com"

ALLOWED_EVENTS: Mapping[str, set[str]] = MappingProxyType(
    {
        "app_opened": set(),
        "scan_started": {"method"},
        "scan_completed": {"method", "found"},
        "verdicts_shown": {"member_count"},
        "meal_logged": set(),
        "voice_asked": {"language"},
        "report_submitted": {"reason"},
        "share_clicked": {"kind"},
        "account_deleted": set(),
        # F6: events the clients send; names only, never properties.
        "meal_queued": set(),
        "meal_log_undone": set(),
        "meal_removed": set(),
        "share_result": set(),
        "share_weekly": set(),
        "compare_opened": set(),
        "compare_viewed": set(),
        "product_search": set(),  # never the query text
        # Plan 11 (spec 6.8): the Diary. A closed `method`, nothing else: never a nutrient, a
        # target, a remaining value, a hidden state, a slot label, a slot count or a quick-add name.
        "diary_entry_added": {"method"},
        "diary_day_viewed": set(),
    }
)

# Keys whose values come from a closed set. Other string values must be a short token.
_ENUMS: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "method": frozenset(
            {
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
        ),
        "language": frozenset({"en", "hi", "mr"}),
        "reason": frozenset({"wrong_values", "wrong_ingredients", "wrong_product", "other"}),
        "kind": frozenset({"link", "image", "whatsapp"}),
    }
)
_BOOLS = frozenset({"found"})
_COUNTS = frozenset({"member_count"})
_TOKEN = re.compile(r"^[a-z0-9_]{1,40}$")

_client: Posthog | None = None


def hashed_id(account_id: UUID) -> str:
    return hashlib.sha256(str(account_id).encode()).hexdigest()


def _safe(key: str, value: object) -> bool:
    if key in _BOOLS:
        return isinstance(value, bool)
    if key in _COUNTS:
        return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 1000
    if not isinstance(value, str) or not _TOKEN.match(value):
        return False
    return key not in _ENUMS or value in _ENUMS[key]


def track(
    distinct_id: UUID, event: str, props: Mapping[str, str | int | bool] | None = None
) -> None:
    """Send one allow-listed event. Never raises; a no-op without POSTHOG_API_KEY."""
    allowed = ALLOWED_EVENTS.get(event)
    if allowed is None:
        logger.warning("analytics_event_dropped event=%s", event if _TOKEN.match(event) else "?")
        return
    props = props or {}
    kept = {k: v for k, v in props.items() if k in allowed and _safe(k, v)}
    dropped = sorted(k for k in props if k not in kept)
    if dropped:
        names = [k if _TOKEN.match(k) else "?" for k in dropped]
        logger.warning("analytics_props_dropped event=%s keys=%s", event, ",".join(names))
    if _client is None:
        return
    try:
        _client.capture(event, distinct_id=hashed_id(distinct_id), properties=kept)
    except Exception as exc:  # noqa: BLE001 - analytics must never break a request
        logger.warning("analytics_capture_failed error=%s", type(exc).__name__)


def init_posthog(settings: Settings) -> None:
    global _client
    if settings.posthog_api_key and _client is None:
        _client = Posthog(settings.posthog_api_key, host=POSTHOG_HOST, disable_geoip=True)


def shutdown_posthog() -> None:
    """Flush queued events (called on app shutdown)."""
    global _client
    if _client is not None:
        _client.shutdown()
        _client = None
