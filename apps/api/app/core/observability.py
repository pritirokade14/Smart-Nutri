"""Sentry setup and scrubbing. No health data may reach Sentry or PostHog (Plan 8 Task 4).

PostHog events go only through `app.integrations.posthog.track` (allow-list).
"""

import hashlib
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import sentry_sdk

from app.core.config import Settings
from app.integrations.posthog import init_posthog, shutdown_posthog

REDACTED = "<redacted>"
# Headers that carry credentials or session state.
_SECRET_HEADERS = frozenset(
    {"authorization", "cookie", "set-cookie", "x-api-key", "apikey", "proxy-authorization"}
)
# Span data keys that can hold query strings or bound SQL parameters.
_SPAN_DATA_DROP = ("http.query", "http.fragment", "db.params", "db.parameters")
_HASHED = re.compile(r"^[0-9a-f]{64}$")


def _strip_query(url: Any) -> Any:
    if not isinstance(url, str):
        return url
    try:
        parts = urlsplit(url)
    except ValueError:
        return REDACTED
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _strip_query_in_text(text: Any) -> Any:
    """`GET https://host/path?x=1` -> `GET https://host/path` (span descriptions)."""
    if not isinstance(text, str):
        return text
    return re.sub(r"\?\S*", "", text)


def _hash_user_id(value: Any) -> str:
    raw = str(value)
    return raw if _HASHED.match(raw) else hashlib.sha256(raw.encode()).hexdigest()


def scrub_event(event: dict, hint: dict) -> dict | None:
    """Sentry before_send / before_send_transaction.

    Drops:
    - every request body (members, analyze, scans, products, voice...);
    - cookies, the query string (and any query part of URLs and span descriptions);
    - the request env (client IP);
    - credential headers;
    - user email, IP and username;
    - stack-frame local variables, `extra`, log messages and breadcrumbs;
    - exception messages, which can embed SQL parameters or input values.

    The user id becomes sha256(account_id).
    """
    event.pop("extra", None)
    # Exception text can embed SQL parameters, DB row contents or pydantic input values.
    for exc in (event.get("exception") or {}).get("values") or []:
        if "value" in exc:
            exc["value"] = REDACTED
    # Log messages are often pre-formatted with data, so drop them entirely.
    event.pop("logentry", None)
    event.pop("breadcrumbs", None)
    for exc in (event.get("exception") or {}).get("values") or []:
        for frame in (exc.get("stacktrace") or {}).get("frames") or []:
            frame.pop("vars", None)
    for thread in (event.get("threads") or {}).get("values") or []:
        for frame in (thread.get("stacktrace") or {}).get("frames") or []:
            frame.pop("vars", None)
    request = event.get("request")
    if isinstance(request, dict):
        for key in ("data", "cookies", "query_string", "env"):
            request.pop(key, None)
        if "url" in request:
            request["url"] = _strip_query(request["url"])
        headers = request.get("headers")
        if isinstance(headers, dict):
            for key in list(headers):
                if key.lower() in _SECRET_HEADERS:
                    del headers[key]
    user = event.get("user")
    if isinstance(user, dict):
        event["user"] = {"id": _hash_user_id(user["id"])} if user.get("id") else {}
    for span in event.get("spans") or []:
        if not isinstance(span, dict):
            continue
        span["description"] = _strip_query_in_text(span.get("description"))
        data = span.get("data")
        if isinstance(data, dict):
            for key in _SPAN_DATA_DROP:
                data.pop(key, None)
            if "url" in data:
                data["url"] = _strip_query(data["url"])
    return event


def init_observability(settings: Settings) -> None:
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            send_default_pii=False,
            traces_sample_rate=0.1 if settings.environment == "prod" else 0.0,
            include_local_variables=False,
            max_breadcrumbs=0,
            max_request_body_size="never",
            before_send=scrub_event,
            before_send_transaction=scrub_event,
        )
    init_posthog(settings)


def shutdown_observability() -> None:
    """Flush queued PostHog events (called on app shutdown)."""
    shutdown_posthog()
